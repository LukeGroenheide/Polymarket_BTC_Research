# Public inspection build. The private runtime uses its full ledger-v2 validator.
# This adapter accepts already certified ledger-v2 session inputs and preserves
# the selected PM projection calculations; it grants no publication authority.
"""Pure one-session Polymarket feature projection for the BTC 5m V1.

The projector consumes an already validated immutable ledger-v2 session
manifest and canonical rows.  It performs no discovery, filesystem access,
network access, target construction, BTC-reference work, or publication.
"""

from __future__ import annotations

from dataclasses import dataclass
import datetime as dt
import math
from typing import Any, Dict, Iterable, Mapping, Optional

from . import ledger_contract as event_ledger


PM_CAUSAL_FEATURE_PROJECTION_SCHEMA = "btc_5m_pm_causal_projection_v1"
PM_V1_BUCKET = "5m"
PM_V1_DECISION_OFFSET_SECONDS = 120
PM_V1_LAG_SECONDS = 10
PM_QUOTE_EVENT_TYPES = frozenset({"book", "price_change", "best_bid_ask"})
MARKET_WINDOW_MEMBERSHIPS = frozenset(
    {
        "before_window",
        "in_window",
        "at_or_after_window_end",
        "unknown_event_time",
    }
)

_EPOCH_UTC = dt.datetime(1970, 1, 1, tzinfo=dt.timezone.utc)
_FORBIDDEN_INPUT_FIELDS = frozenset(
    {
        "brier_score",
        "is_resolved",
        "outcome_y",
        "raw_change",
        "raw_event",
        "resolution_timestamp_ms",
        "resolved_outcome",
        "target",
        "winning_asset_id",
        "winning_outcome",
        "y1",
        "y2",
        "y5",
    }
)


@dataclass(frozen=True)
class _CanonicalRecord:
    row: Mapping[str, Any]
    receive_time: dt.datetime


def _iso_utc(value: dt.datetime) -> str:
    return value.astimezone(dt.timezone.utc).isoformat(timespec="microseconds")


def _timestamp_from_ms(value: int) -> dt.datetime:
    return _EPOCH_UTC + dt.timedelta(milliseconds=value)


def _parse_receive_timestamp(value: Any, *, source_index: int) -> dt.datetime:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(
            "Canonical record local_receive_timestamp_utc must be nonempty text "
            f"at source_index {source_index}"
        )
    timestamp_text = value.strip()
    if timestamp_text.endswith("Z"):
        timestamp_text = f"{timestamp_text[:-1]}+00:00"
    try:
        parsed = dt.datetime.fromisoformat(timestamp_text)
    except ValueError as exc:
        raise ValueError(
            "Canonical record local_receive_timestamp_utc is invalid at "
            f"source_index {source_index}"
        ) from exc
    if parsed.tzinfo is None:
        raise ValueError(
            "Canonical record local_receive_timestamp_utc must include a timezone "
            f"at source_index {source_index}"
        )
    return parsed.astimezone(dt.timezone.utc)


def _is_forbidden_field(field: Any) -> bool:
    if not isinstance(field, str):
        return False
    normalized = field.strip().lower()
    return (
        normalized in _FORBIDDEN_INPUT_FIELDS
        or normalized.startswith("target_")
        or normalized.startswith("future_")
        or normalized.startswith("btc_control_")
        or normalized.endswith("_target")
        or normalized.endswith("_label")
    )


def _reject_forbidden_fields(payload: Mapping[str, Any], *, context: str) -> None:
    forbidden = sorted(str(field) for field in payload if _is_forbidden_field(field))
    if forbidden:
        raise ValueError(f"{context} contains forbidden predictor fields: {forbidden}")


def _validated_records(
    records: Iterable[Mapping[str, Any]],
    *,
    manifest: event_ledger.EventLedgerSessionManifest,
) -> list[_CanonicalRecord]:
    rows: list[Dict[str, Any]] = []
    for position, record in enumerate(records):
        if not isinstance(record, Mapping):
            raise ValueError(
                f"Canonical record at physical position {position} must be a mapping"
            )
        row = dict(record)
        _reject_forbidden_fields(row, context=f"Canonical record {position}")
        rows.append(row)

    raw_ndjson_artifact = next(
        artifact
        for artifact in manifest.source_artifacts
        if artifact.role == "raw_ndjson"
    )
    if raw_ndjson_artifact.row_count != len(rows):
        raise ValueError(
            "Canonical record count conflicts with session manifest raw_ndjson "
            "row_count"
        )

    event_ledger.validate_event_ledger_rows(
        rows,
        bucket=manifest.bucket,
        expected_schema=event_ledger.EVENT_LEDGER_SCHEMA_V2_NAME,
    )

    manifest_outcomes = dict(manifest.asset_outcomes)
    validated: list[_CanonicalRecord] = []
    required_projector_fields = (
        "market_slug",
        "asset_id",
        "outcome",
        "market_window_membership",
        "best_bid",
        "best_ask",
    )
    for position, row in enumerate(rows):
        if row.get("row_kind") != event_ledger.CANONICAL_OBSERVATION_ROW_KIND:
            raise ValueError("PM projector accepts canonical observation records only")
        source_index = row.get("source_index")
        if type(source_index) is not int or source_index != position:
            raise ValueError(
                "Canonical records must be supplied in ascending physical "
                "source_index order starting at zero"
            )
        missing_fields = [
            field for field in required_projector_fields if field not in row
        ]
        if missing_fields:
            raise ValueError(
                f"Canonical record {source_index} is missing projector fields: "
                f"{missing_fields}"
            )
        if row.get("session_id") != manifest.session_id:
            raise ValueError(
                "Canonical record session_id conflicts with session manifest"
            )
        if row.get("bucket") != manifest.bucket:
            raise ValueError("Canonical record bucket conflicts with session manifest")
        if row.get("market_id") != manifest.market_id:
            raise ValueError(
                "Canonical record market_id conflicts with session manifest"
            )
        if row.get("market_slug") != manifest.market_slug:
            raise ValueError(
                "Canonical record market_slug conflicts with session manifest"
            )

        asset_id = row.get("asset_id")
        if asset_id not in manifest_outcomes:
            raise ValueError(
                "Canonical record asset_id is not owned by session manifest"
            )
        if row.get("outcome") != manifest_outcomes[asset_id]:
            raise ValueError("Canonical record outcome conflicts with session manifest")

        event_type = row.get("event_type")
        if not isinstance(event_type, str) or not event_type.strip():
            raise ValueError("Canonical record event_type must be nonempty text")
        membership = row.get("market_window_membership")
        if membership not in MARKET_WINDOW_MEMBERSHIPS:
            raise ValueError("Canonical record market_window_membership is invalid")

        validated.append(
            _CanonicalRecord(
                row=row,
                receive_time=_parse_receive_timestamp(
                    row.get("local_receive_timestamp_utc"),
                    source_index=source_index,
                ),
            )
        )
    return validated


def _quote_projection(record: Optional[_CanonicalRecord]) -> Dict[str, Any]:
    if record is None:
        return {
            "quote_status": "unavailable",
            "quote_issues": ["no_qualifying_quote_snapshot"],
            "best_bid": None,
            "best_ask": None,
            "midpoint": None,
            "spread": None,
        }

    issues: list[str] = []
    prices: Dict[str, Optional[float]] = {}
    for field in ("best_bid", "best_ask"):
        value = record.row.get(field)
        if value is None:
            issues.append(f"missing_{field}")
            prices[field] = None
        elif isinstance(value, bool) or not isinstance(value, (int, float)):
            issues.append(f"non_numeric_{field}")
            prices[field] = None
        else:
            try:
                price = float(value)
            except OverflowError:
                price = math.inf
            if not math.isfinite(price):
                issues.append(f"nonfinite_{field}")
                prices[field] = None
            else:
                prices[field] = price
            if prices[field] is not None and not 0.0 <= prices[field] <= 1.0:
                issues.append(f"out_of_range_{field}")

    best_bid = prices["best_bid"]
    best_ask = prices["best_ask"]
    if (
        best_bid is not None
        and best_ask is not None
        and 0.0 <= best_bid <= 1.0
        and 0.0 <= best_ask <= 1.0
        and best_bid > best_ask
    ):
        issues.append("crossed_quote")

    if issues:
        invalid = any(not issue.startswith("missing_") for issue in issues)
        return {
            "quote_status": "invalid" if invalid else "missing",
            "quote_issues": issues,
            "best_bid": None,
            "best_ask": None,
            "midpoint": None,
            "spread": None,
        }

    assert best_bid is not None and best_ask is not None
    return {
        "quote_status": "valid",
        "quote_issues": [],
        "best_bid": best_bid,
        "best_ask": best_ask,
        "midpoint": (best_bid + best_ask) / 2.0,
        "spread": best_ask - best_bid,
    }


def _project_as_of(
    records: Iterable[_CanonicalRecord],
    *,
    manifest: event_ledger.EventLedgerSessionManifest,
    market_start: dt.datetime,
    cutoff: dt.datetime,
    decision_offset_seconds: int,
) -> Dict[str, Any]:
    prefix_last_source_index: Optional[int] = None
    barrier: Optional[_CanonicalRecord] = None
    previous_receive: Optional[dt.datetime] = None
    regression_source_indexes: list[int] = []
    first_quote: Optional[_CanonicalRecord] = None
    latest_quote: Optional[_CanonicalRecord] = None

    for record in records:
        source_index = int(record.row["source_index"])
        if record.receive_time > cutoff:
            barrier = record
            break

        prefix_last_source_index = source_index
        if previous_receive is not None and record.receive_time < previous_receive:
            regression_source_indexes.append(source_index)
        previous_receive = record.receive_time

        if record.row["market_window_membership"] != "in_window":
            continue
        if record.row["asset_id"] != manifest.yes_asset_id:
            continue
        if record.row["event_type"] not in PM_QUOTE_EVENT_TYPES:
            continue
        if first_quote is None:
            first_quote = record
        latest_quote = record

    projected_quote = _quote_projection(latest_quote)
    first_quote_receive = first_quote.receive_time if first_quote is not None else None
    latest_quote_receive = (
        latest_quote.receive_time if latest_quote is not None else None
    )
    projected_quote.update(
        {
            "cutoff_utc": _iso_utc(cutoff),
            "decision_offset_seconds": decision_offset_seconds,
            "eligible_prefix_last_source_index": prefix_last_source_index,
            "prefix_barrier_source_index": (
                int(barrier.row["source_index"]) if barrier is not None else None
            ),
            "prefix_barrier_receive_timestamp_utc": (
                _iso_utc(barrier.receive_time) if barrier is not None else None
            ),
            "causal_status": (
                "receipt_time_regression_within_prefix"
                if regression_source_indexes
                else "ok"
            ),
            "receipt_time_regression_count": len(regression_source_indexes),
            "receipt_time_regression_source_indexes": regression_source_indexes,
            "first_qualifying_quote_source_index": (
                int(first_quote.row["source_index"])
                if first_quote is not None
                else None
            ),
            "first_qualifying_quote_receive_timestamp_utc": (
                _iso_utc(first_quote_receive)
                if first_quote_receive is not None
                else None
            ),
            "leading_availability_gap_seconds": (
                max(0.0, (first_quote_receive - market_start).total_seconds())
                if first_quote_receive is not None
                else None
            ),
            "contributing_source_index": (
                int(latest_quote.row["source_index"])
                if latest_quote is not None
                else None
            ),
            "contributing_event_type": (
                latest_quote.row["event_type"] if latest_quote is not None else None
            ),
            "quote_receive_timestamp_utc": (
                _iso_utc(latest_quote_receive)
                if latest_quote_receive is not None
                else None
            ),
            "quote_age_seconds": (
                (cutoff - latest_quote_receive).total_seconds()
                if latest_quote_receive is not None
                else None
            ),
        }
    )
    return projected_quote


def _project_btc_polymarket_features(
    *,
    session_manifest: event_ledger.EventLedgerSessionManifest | Mapping[str, Any],
    canonical_records: Iterable[Mapping[str, Any]],
    bucket: str,
    schema: str,
    decision_offset_seconds: int = PM_V1_DECISION_OFFSET_SECONDS,
) -> Dict[str, Any]:
    """Project one pure predictor row using the frozen early-session cutoffs.

    Each as-of view is the physical-source prefix ending immediately before the
    first record whose local receipt time is later than that view's inclusive
    cutoff.  Later records can never re-enter, even when their receipt timestamp
    regresses.  Receipt regressions wholly inside the retained prefix preserve
    physical order and are surfaced as an explicit causal status.
    """

    if isinstance(session_manifest, Mapping):
        _reject_forbidden_fields(session_manifest, context="Session manifest")
    manifest = event_ledger.event_ledger_session_manifest_from_mapping(
        session_manifest
    )
    if manifest.bucket != bucket:
        if bucket == "5m":
            raise ValueError("PM V1 causal projector supports BTC 5m sessions only")
        raise ValueError(f"PM V1 causal projector expected BTC {bucket} session")
    expected_duration_ms = {"5m": 300_000, "15m": 900_000,
                            "1h": 3_600_000, "4h": 14_400_000,
                            "1d": 86_400_000}[bucket]
    if manifest.window_end_ms != manifest.window_start_ms + expected_duration_ms:
        raise ValueError(f"BTC {bucket} session has an unexpected market window")

    records = _validated_records(canonical_records, manifest=manifest)
    return _project_btc_polymarket_features_from_records(
        manifest=manifest, records=records, schema=schema,
        decision_offset_seconds=decision_offset_seconds,
    )


def _project_btc_polymarket_features_from_records(
    *,
    manifest: event_ledger.EventLedgerSessionManifest,
    records: Iterable[_CanonicalRecord],
    schema: str,
    decision_offset_seconds: int = PM_V1_DECISION_OFFSET_SECONDS,
) -> Dict[str, Any]:
    """Apply the same as-of arithmetic to an already certified source prefix."""
    market_start = _timestamp_from_ms(manifest.window_start_ms)
    market_end = _timestamp_from_ms(manifest.window_end_ms)
    if (type(decision_offset_seconds) is not int or
            not PM_V1_LAG_SECONDS < decision_offset_seconds <
            (market_end - market_start).total_seconds()):
        raise ValueError("Invalid PM V1 decision offset")
    cutoff_t = market_start + dt.timedelta(seconds=decision_offset_seconds)
    cutoff_lag = cutoff_t - dt.timedelta(seconds=PM_V1_LAG_SECONDS)

    lag_view = _project_as_of(
        records,
        manifest=manifest,
        market_start=market_start,
        cutoff=cutoff_lag,
        decision_offset_seconds=(
            decision_offset_seconds - PM_V1_LAG_SECONDS
        ),
    )
    current_view = _project_as_of(
        records,
        manifest=manifest,
        market_start=market_start,
        cutoff=cutoff_t,
        decision_offset_seconds=decision_offset_seconds,
    )

    current_midpoint = current_view["midpoint"]
    lag_midpoint = lag_view["midpoint"]
    q = 2.0 * current_midpoint - 1.0 if current_midpoint is not None else None
    dq10 = (
        2.0 * (current_midpoint - lag_midpoint)
        if current_midpoint is not None and lag_midpoint is not None
        else None
    )
    regression_boundaries = [
        boundary
        for boundary, view in (("T-10s", lag_view), ("T", current_view))
        if view["causal_status"] != "ok"
    ]
    unusable_dq10_inputs = [
        boundary
        for boundary, view in (("T-10s", lag_view), ("T", current_view))
        if view["quote_status"] != "valid"
    ]

    if current_view["quote_status"] == "invalid":
        feature_row_status = "invalid_current_snapshot"
    elif current_view["quote_status"] != "valid":
        feature_row_status = "missing_current_snapshot"
    elif lag_view["quote_status"] == "invalid":
        feature_row_status = "invalid_lag_snapshot"
    elif lag_view["quote_status"] != "valid":
        feature_row_status = "missing_lag_snapshot"
    else:
        feature_row_status = "complete"

    return {
        "schema": schema,
        "source_ledger_schema": event_ledger.EVENT_LEDGER_SCHEMA_V2_NAME,
        "session_manifest_schema": manifest.manifest_schema,
        "session_id": manifest.session_id,
        "market_id": manifest.market_id,
        "market_slug": manifest.market_slug,
        "bucket": manifest.bucket,
        "yes_asset_id": manifest.yes_asset_id,
        "market_window_start_utc": _iso_utc(market_start),
        "market_window_end_utc": _iso_utc(market_end),
        "decision_cutoff_utc": _iso_utc(cutoff_t),
        "decision_offset_seconds": decision_offset_seconds,
        "lag_cutoff_utc": _iso_utc(cutoff_lag),
        "lag_seconds": PM_V1_LAG_SECONDS,
        "feature_row_status": feature_row_status,
        "causal_status": (
            "receipt_time_regression_within_used_prefix"
            if regression_boundaries
            else "ok"
        ),
        "causal_warning_boundaries": regression_boundaries,
        "as_of_t_minus_10s": lag_view,
        "as_of_t": current_view,
        "q": q,
        "q_status": (
            "available"
            if current_view["quote_status"] == "valid"
            else current_view["quote_status"]
        ),
        "dq10": dq10,
        "dq10_status": "available" if dq10 is not None else "unavailable",
        "dq10_unusable_inputs": unusable_dq10_inputs,
    }


def project_btc_5m_polymarket_features(
    *,
    session_manifest: event_ledger.EventLedgerSessionManifest | Mapping[str, Any],
    canonical_records: Iterable[Mapping[str, Any]],
) -> Dict[str, Any]:
    return _project_btc_polymarket_features(
        session_manifest=session_manifest,
        canonical_records=canonical_records,
        bucket="5m",
        schema=PM_CAUSAL_FEATURE_PROJECTION_SCHEMA,
    )


def project_btc_15m_polymarket_features(
    *,
    session_manifest: event_ledger.EventLedgerSessionManifest | Mapping[str, Any],
    canonical_records: Iterable[Mapping[str, Any]],
) -> Dict[str, Any]:
    return _project_btc_polymarket_features(
        session_manifest=session_manifest,
        canonical_records=canonical_records,
        bucket="15m",
        schema="btc_15m_pm_causal_projection_lifecycle40_v1",
        decision_offset_seconds=360,
    )


def project_btc_1h_polymarket_features(
    *,
    session_manifest: event_ledger.EventLedgerSessionManifest | Mapping[str, Any],
    canonical_records: Iterable[Mapping[str, Any]],
) -> Dict[str, Any]:
    return _project_btc_polymarket_features(
        session_manifest=session_manifest,
        canonical_records=canonical_records,
        bucket="1h",
        schema="btc_1h_pm_causal_projection_lifecycle40_v1",
        decision_offset_seconds=1440,
    )


def project_btc_4h_polymarket_features(
    *,
    session_manifest: event_ledger.EventLedgerSessionManifest | Mapping[str, Any],
    canonical_records: Iterable[Mapping[str, Any]],
) -> Dict[str, Any]:
    return _project_btc_polymarket_features(
        session_manifest=session_manifest,
        canonical_records=canonical_records,
        bucket="4h",
        schema="btc_4h_pm_causal_projection_lifecycle40_v1",
        decision_offset_seconds=5760,
    )


def project_btc_1d_polymarket_features(
    *,
    session_manifest: event_ledger.EventLedgerSessionManifest | Mapping[str, Any],
    canonical_records: Iterable[Mapping[str, Any]],
) -> Dict[str, Any]:
    return _project_btc_polymarket_features(
        session_manifest=session_manifest,
        canonical_records=canonical_records,
        bucket="1d",
        schema="btc_1d_pm_causal_projection_lifecycle40_v1",
        decision_offset_seconds=34560,
    )
