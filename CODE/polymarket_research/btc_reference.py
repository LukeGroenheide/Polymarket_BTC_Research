"""Pure Binance BTCUSDT 1-second parsing and frozen V1 BTC builders.

The functions in this module operate only on in-memory archive rows or their
parsed representations.  They perform no retrieval, filesystem access,
network access, publication, or model-column discovery.
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass
import datetime as dt
import math
import re
from types import MappingProxyType
from typing import Any, Optional


BINANCE_BTCUSDT_SYMBOL = "BTCUSDT"
BINANCE_ONE_SECOND_INTERVAL = "1s"
BINANCE_BTCUSDT_1S_REFERENCE_BAR_SCHEMA = (
    "binance_btcusdt_1s_reference_bar_v1"
)
BTC_V1_EVENT_TIME_CONTROL_SCHEMA = "btc_v1_event_time_controls_v1"
BTC_V1_TARGET_SCHEMA = "btc_v1_targets_v1"

BTC_V1_DECISION_OFFSET_SECONDS = 120
BTC_V1_MARKET_DURATION_SECONDS = 300
BTC_V1_REQUIRED_CONTROL_BAR_COUNT = 72

BTC_V1_CONTROL_COLUMNS = (
    "btc_logret_1s_u",
    "btc_logret_10s_u",
    "btc_logret_60s_u",
    "btc_logdisp_s_u",
    "btc_sigma60_u",
    "btc_sigma60_u_minus_10s",
    "btc_abs_logdisp_s_u",
    "btc_sq_logdisp_s_u",
    "btc_abs_logret_10s_u",
    "btc_sq_logret_10s_u",
    "btc_logdisp_x_logret_10s_u",
    "btc_g_u",
    "btc_g_delta_10s",
)
BTC_V1_TARGET_FIELDS = ("y1", "y2", "y5")
BTC_V1_QUOTE_QUALITY_COLUMNS = (
    "pm_spread_t",
    "pm_quote_age_seconds_t",
    "pm_spread_t_minus_10s",
    "pm_quote_age_seconds_t_minus_10s",
)
BTC_V1_COMPARATOR_COLUMNS = MappingProxyType(
    {
        "B0": BTC_V1_CONTROL_COLUMNS,
        "B": BTC_V1_CONTROL_COLUMNS + BTC_V1_QUOTE_QUALITY_COLUMNS,
        "L": BTC_V1_CONTROL_COLUMNS + BTC_V1_QUOTE_QUALITY_COLUMNS + ("q",),
        "A": (
            BTC_V1_CONTROL_COLUMNS
            + BTC_V1_QUOTE_QUALITY_COLUMNS
            + ("q", "dq10")
        ),
    }
)

_BINANCE_KLINE_COLUMN_COUNT = 12
_OPEN_TIME_COLUMN = 0
_CLOSE_COLUMN = 4
_CLOSE_TIME_COLUMN = 6
_ONE_SECOND_US = 1_000_000
_TIMESTAMP_TEXT = re.compile(r"(?:0|[1-9][0-9]*)\Z")
_EPOCH_UTC = dt.datetime(1970, 1, 1, tzinfo=dt.timezone.utc)


def _epoch_microseconds(value: dt.datetime) -> int:
    delta = value - _EPOCH_UTC
    return (
        (delta.days * 86_400 + delta.seconds) * _ONE_SECOND_US
        + delta.microseconds
    )


_START_2026_US = _epoch_microseconds(
    dt.datetime(2026, 1, 1, tzinfo=dt.timezone.utc)
)
_START_2027_US = _epoch_microseconds(
    dt.datetime(2027, 1, 1, tzinfo=dt.timezone.utc)
)


class _ReferenceRowError(ValueError):
    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code


@dataclass(frozen=True)
class BinanceBTCUSDTOneSecondBar:
    """Minimal parsed bar with distinct raw and semantic timestamps."""

    raw_open_time_us: int
    raw_close_time_us: int
    semantic_bar_end_us: int
    close: float

    @property
    def semantic_bar_end_ms(self) -> int:
        return self.semantic_bar_end_us // 1_000

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema": BINANCE_BTCUSDT_1S_REFERENCE_BAR_SCHEMA,
            "symbol": BINANCE_BTCUSDT_SYMBOL,
            "interval": BINANCE_ONE_SECOND_INTERVAL,
            "raw_open_time_us": self.raw_open_time_us,
            "raw_close_time_us": self.raw_close_time_us,
            "semantic_bar_end_us": self.semantic_bar_end_us,
            "semantic_bar_end_ms": self.semantic_bar_end_ms,
            "close": self.close,
        }


@dataclass(frozen=True)
class _InvalidReferenceRow:
    source_index: int
    code: str


@dataclass(frozen=True)
class _ReferenceCatalog:
    valid: Mapping[int, tuple[tuple[int, BinanceBTCUSDTOneSecondBar], ...]]
    invalid: Mapping[int, tuple[_InvalidReferenceRow, ...]]


ReferenceBarInput = BinanceBTCUSDTOneSecondBar | Sequence[Any]


def _parse_timestamp_us(value: Any, *, field: str) -> int:
    if type(value) is int:
        parsed = value
    elif isinstance(value, str) and _TIMESTAMP_TEXT.fullmatch(value):
        parsed = int(value)
    else:
        raise _ReferenceRowError(
            "invalid_timestamp_grammar",
            f"Binance {field} must be a canonical integer microsecond timestamp",
        )
    if not _START_2026_US <= parsed < _START_2027_US:
        raise _ReferenceRowError(
            "invalid_2026_microsecond_timestamp",
            f"Binance {field} must be a 2026 microsecond Unix timestamp",
        )
    return parsed


def _parse_close_price(value: Any) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float, str)):
        raise _ReferenceRowError(
            "invalid_close_price",
            "Binance close price must be numeric, finite, and greater than zero",
        )
    if isinstance(value, str) and (not value or value != value.strip()):
        raise _ReferenceRowError(
            "invalid_close_price",
            "Binance close price must be numeric, finite, and greater than zero",
        )
    try:
        parsed = float(value)
    except (OverflowError, ValueError) as exc:
        raise _ReferenceRowError(
            "invalid_close_price",
            "Binance close price must be numeric, finite, and greater than zero",
        ) from exc
    if not math.isfinite(parsed) or parsed <= 0.0:
        raise _ReferenceRowError(
            "invalid_close_price",
            "Binance close price must be numeric, finite, and greater than zero",
        )
    return parsed


def _validated_bar(
    *,
    raw_open_time: Any,
    raw_close_time: Any,
    semantic_bar_end: Any = None,
    close: Any,
) -> BinanceBTCUSDTOneSecondBar:
    open_time_us = _parse_timestamp_us(raw_open_time, field="openTime")
    close_time_us = _parse_timestamp_us(raw_close_time, field="closeTime")
    if (
        open_time_us % _ONE_SECOND_US != 0
        or close_time_us != open_time_us + _ONE_SECOND_US - 1
    ):
        raise _ReferenceRowError(
            "invalid_one_second_interval",
            "Binance timestamps must identify exactly one [t-1s, t) interval",
        )
    computed_semantic_end_us = close_time_us + 1
    if computed_semantic_end_us % _ONE_SECOND_US != 0:
        raise _ReferenceRowError(
            "invalid_semantic_boundary",
            "Binance timestamps must normalize to an exact whole-second boundary",
        )
    if semantic_bar_end is not None and (
        type(semantic_bar_end) is not int
        or semantic_bar_end != computed_semantic_end_us
    ):
        raise _ReferenceRowError(
            "invalid_semantic_boundary",
            "Stored semantic bar end conflicts with raw Binance timestamps",
        )
    return BinanceBTCUSDTOneSecondBar(
        raw_open_time_us=open_time_us,
        raw_close_time_us=close_time_us,
        semantic_bar_end_us=computed_semantic_end_us,
        close=_parse_close_price(close),
    )


def parse_binance_btcusdt_1s_archive_row(
    row: Sequence[Any],
) -> BinanceBTCUSDTOneSecondBar:
    """Parse one exact 12-column Binance BTCUSDT 1-second archive row."""

    if isinstance(row, (str, bytes, bytearray)) or not isinstance(row, Sequence):
        raise _ReferenceRowError(
            "invalid_row_shape",
            "Binance archive row must be a 12-column sequence",
        )
    if len(row) != _BINANCE_KLINE_COLUMN_COUNT:
        raise _ReferenceRowError(
            "invalid_row_shape",
            "Binance archive row must contain exactly 12 columns",
        )
    return _validated_bar(
        raw_open_time=row[_OPEN_TIME_COLUMN],
        raw_close_time=row[_CLOSE_TIME_COLUMN],
        close=row[_CLOSE_COLUMN],
    )


def parse_binance_btcusdt_1s_archive_rows(
    rows: Iterable[Sequence[Any]],
) -> tuple[BinanceBTCUSDTOneSecondBar, ...]:
    """Parse rows in input order and reject duplicate semantic boundaries."""

    parsed: list[BinanceBTCUSDTOneSecondBar] = []
    first_index_by_boundary: dict[int, int] = {}
    for source_index, row in enumerate(rows):
        bar = parse_binance_btcusdt_1s_archive_row(row)
        boundary = bar.semantic_bar_end_us
        if boundary in first_index_by_boundary:
            raise _ReferenceRowError(
                "duplicate_semantic_boundary",
                "Duplicate Binance semantic bar boundary at source indexes "
                f"{first_index_by_boundary[boundary]} and {source_index}: "
                f"{boundary}",
            )
        first_index_by_boundary[boundary] = source_index
        parsed.append(bar)
    return tuple(parsed)


def _candidate_boundaries(value: ReferenceBarInput) -> tuple[int, ...]:
    if isinstance(value, BinanceBTCUSDTOneSecondBar):
        timestamp_values = (
            (value.raw_open_time_us, _ONE_SECOND_US),
            (value.raw_close_time_us, 1),
            (value.semantic_bar_end_us, 0),
        )
    elif (
        isinstance(value, Sequence)
        and not isinstance(value, (str, bytes, bytearray))
        and len(value) == _BINANCE_KLINE_COLUMN_COUNT
    ):
        timestamp_values = (
            (value[_OPEN_TIME_COLUMN], _ONE_SECOND_US),
            (value[_CLOSE_TIME_COLUMN], 1),
        )
    else:
        return ()

    candidates: set[int] = set()
    for raw_value, increment in timestamp_values:
        try:
            timestamp_us = _parse_timestamp_us(raw_value, field="candidate")
        except _ReferenceRowError:
            continue
        boundary = timestamp_us + increment
        if boundary % _ONE_SECOND_US == 0:
            candidates.add(boundary)
    return tuple(sorted(candidates))


def _validate_reference_input(value: ReferenceBarInput) -> BinanceBTCUSDTOneSecondBar:
    if isinstance(value, BinanceBTCUSDTOneSecondBar):
        return _validated_bar(
            raw_open_time=value.raw_open_time_us,
            raw_close_time=value.raw_close_time_us,
            semantic_bar_end=value.semantic_bar_end_us,
            close=value.close,
        )
    return parse_binance_btcusdt_1s_archive_row(value)


def _catalog_reference_inputs(
    reference_bars: Iterable[ReferenceBarInput],
    *,
    relevant_boundaries: set[int],
) -> _ReferenceCatalog:
    valid_lists: dict[
        int, list[tuple[int, BinanceBTCUSDTOneSecondBar]]
    ] = {}
    invalid_lists: dict[int, list[_InvalidReferenceRow]] = {}
    for source_index, value in enumerate(reference_bars):
        try:
            bar = _validate_reference_input(value)
        except _ReferenceRowError as exc:
            for boundary in _candidate_boundaries(value):
                if boundary in relevant_boundaries:
                    invalid_lists.setdefault(boundary, []).append(
                        _InvalidReferenceRow(source_index=source_index, code=exc.code)
                    )
            continue
        boundary = bar.semantic_bar_end_us
        if boundary in relevant_boundaries:
            valid_lists.setdefault(boundary, []).append((source_index, bar))
    return _ReferenceCatalog(
        valid={key: tuple(value) for key, value in valid_lists.items()},
        invalid={key: tuple(value) for key, value in invalid_lists.items()},
    )


def _resolve_required_bars(
    catalog: _ReferenceCatalog,
    required_boundaries: Sequence[int],
) -> tuple[dict[int, BinanceBTCUSDTOneSecondBar], list[dict[str, Any]]]:
    selected: dict[int, BinanceBTCUSDTOneSecondBar] = {}
    reasons: list[dict[str, Any]] = []
    for boundary in required_boundaries:
        valid = catalog.valid.get(boundary, ())
        invalid = catalog.invalid.get(boundary, ())
        source_indexes = sorted(
            {source_index for source_index, _bar in valid}
            | {issue.source_index for issue in invalid}
        )
        if len(source_indexes) > 1:
            reasons.append(
                {
                    "code": "duplicate_required_bar",
                    "semantic_bar_end_us": boundary,
                    "source_indexes": source_indexes,
                }
            )
        if invalid:
            reasons.append(
                {
                    "code": "invalid_required_bar",
                    "semantic_bar_end_us": boundary,
                    "source_indexes": sorted(
                        {issue.source_index for issue in invalid}
                    ),
                    "issue_codes": sorted({issue.code for issue in invalid}),
                }
            )
        if not valid and not invalid:
            reasons.append(
                {
                    "code": "missing_required_bar",
                    "semantic_bar_end_us": boundary,
                }
            )
        if len(valid) == 1 and not invalid and len(source_indexes) == 1:
            selected[boundary] = valid[0][1]
    return selected, reasons


def _validate_market_start_us(market_start_us: Any) -> int:
    if type(market_start_us) is not int:
        raise ValueError("market_start_us must be an integer microsecond timestamp")
    if not _START_2026_US <= market_start_us < _START_2027_US:
        raise ValueError("market_start_us must be a 2026 microsecond timestamp")
    if market_start_us % _ONE_SECOND_US != 0:
        raise ValueError("market_start_us must be an exact whole-second boundary")
    return market_start_us


def _timing(market_start_us: int, *, market_duration_seconds: int = BTC_V1_MARKET_DURATION_SECONDS,
            decision_offset_seconds: int = BTC_V1_DECISION_OFFSET_SECONDS) -> dict[str, int]:
    if market_duration_seconds not in (BTC_V1_MARKET_DURATION_SECONDS, 900, 3600, 14400, 86400):
        raise ValueError("Only the frozen BTC 5m, 15m, 1h, 4h and 1d V1 market durations are supported")
    if (type(decision_offset_seconds) is not int or
            not 70 <= decision_offset_seconds < market_duration_seconds - 65):
        raise ValueError("BTC V1 decision offset cannot support the frozen bars and targets")
    decision_cutoff_us = (
        market_start_us + decision_offset_seconds * _ONE_SECOND_US
    )
    return {
        "market_start_us": market_start_us,
        "decision_cutoff_us": decision_cutoff_us,
        "u_event_us": decision_cutoff_us,
        "market_end_us": (
            market_start_us + market_duration_seconds * _ONE_SECOND_US
        ),
    }


def btc_v1_required_control_bar_ends_us(
    market_start_us: int, *,
    decision_offset_seconds: int = BTC_V1_DECISION_OFFSET_SECONDS,
) -> tuple[int, ...]:
    """Return C(S) and the frozen 71 trailing semantic boundaries."""

    start = _validate_market_start_us(market_start_us)
    u_event_us = start + decision_offset_seconds * _ONE_SECOND_US
    trailing = tuple(
        u_event_us + offset_seconds * _ONE_SECOND_US
        for offset_seconds in range(-70, 1)
    )
    required = (start,) + trailing
    assert len(required) == BTC_V1_REQUIRED_CONTROL_BAR_COUNT
    return required


def _log_return(
    closes: Mapping[int, float], numerator_boundary: int, denominator_boundary: int
) -> float:
    return math.log(closes[numerator_boundary]) - math.log(
        closes[denominator_boundary]
    )


def _sigma60(closes: Mapping[int, float], *, boundary: int) -> float:
    squared_returns = [
        _log_return(
            closes,
            boundary - j * _ONE_SECOND_US,
            boundary - (j + 1) * _ONE_SECOND_US,
        )
        ** 2
        for j in range(60)
    ]
    return math.sqrt(math.fsum(squared_returns) / 60.0)


def _g(displacement: float, sigma60: float, *, tau_seconds: int) -> Optional[float]:
    if tau_seconds <= 0 or not (
        math.isfinite(displacement) and math.isfinite(sigma60)
    ):
        return None
    if sigma60 == 0.0:
        if displacement > 0.0:
            return 1.0
        if displacement < 0.0:
            return -1.0
        return 0.0
    z = displacement / (sigma60 * math.sqrt(tau_seconds))
    return math.erf(z / math.sqrt(2.0))


def build_btc_v1_event_time_controls(
    *,
    market_start_us: int,
    reference_bars: Iterable[ReferenceBarInput],
    market_duration_seconds: int = BTC_V1_MARKET_DURATION_SECONDS,
    decision_offset_seconds: int = BTC_V1_DECISION_OFFSET_SECONDS,
) -> dict[str, Any]:
    """Build the atomic frozen 13-column BTC event-time control vector."""

    start = _validate_market_start_us(market_start_us)
    timing = _timing(start, market_duration_seconds=market_duration_seconds,
                     decision_offset_seconds=decision_offset_seconds)
    required = btc_v1_required_control_bar_ends_us(
        start, decision_offset_seconds=decision_offset_seconds)
    catalog = _catalog_reference_inputs(
        reference_bars, relevant_boundaries=set(required)
    )
    selected, reasons = _resolve_required_bars(catalog, required)
    result: dict[str, Any] = {
        "schema": BTC_V1_EVENT_TIME_CONTROL_SCHEMA,
        "status": "unavailable" if reasons else "available",
        "unavailable_reasons": reasons,
        "timing": timing,
        "required_bar_count": BTC_V1_REQUIRED_CONTROL_BAR_COUNT,
        "control_columns": list(BTC_V1_CONTROL_COLUMNS),
        "controls": None,
    }
    if reasons:
        return result

    closes = {boundary: bar.close for boundary, bar in selected.items()}
    u_event_us = timing["u_event_us"]
    market_end_us = timing["market_end_us"]
    logret_1s = _log_return(closes, u_event_us, u_event_us - _ONE_SECOND_US)
    logret_10s = _log_return(
        closes, u_event_us, u_event_us - 10 * _ONE_SECOND_US
    )
    logret_60s = _log_return(
        closes, u_event_us, u_event_us - 60 * _ONE_SECOND_US
    )
    displacement_u = _log_return(closes, u_event_us, start)
    sigma_u = _sigma60(closes, boundary=u_event_us)
    u_minus_10s = u_event_us - 10 * _ONE_SECOND_US
    sigma_u_minus_10s = _sigma60(closes, boundary=u_minus_10s)
    displacement_u_minus_10s = _log_return(closes, u_minus_10s, start)
    g_u = _g(
        displacement_u,
        sigma_u,
        tau_seconds=(market_end_us - u_event_us) // _ONE_SECOND_US,
    )
    g_u_minus_10s = _g(
        displacement_u_minus_10s,
        sigma_u_minus_10s,
        tau_seconds=(market_end_us - u_minus_10s) // _ONE_SECOND_US,
    )
    if g_u is None or g_u_minus_10s is None:
        result["status"] = "unavailable"
        result["unavailable_reasons"] = [{"code": "invalid_g_input"}]
        return result

    controls = {
        "btc_logret_1s_u": logret_1s,
        "btc_logret_10s_u": logret_10s,
        "btc_logret_60s_u": logret_60s,
        "btc_logdisp_s_u": displacement_u,
        "btc_sigma60_u": sigma_u,
        "btc_sigma60_u_minus_10s": sigma_u_minus_10s,
        "btc_abs_logdisp_s_u": abs(displacement_u),
        "btc_sq_logdisp_s_u": displacement_u**2,
        "btc_abs_logret_10s_u": abs(logret_10s),
        "btc_sq_logret_10s_u": logret_10s**2,
        "btc_logdisp_x_logret_10s_u": displacement_u * logret_10s,
        "btc_g_u": g_u,
        "btc_g_delta_10s": g_u - g_u_minus_10s,
    }
    if tuple(controls) != BTC_V1_CONTROL_COLUMNS:
        raise AssertionError("BTC V1 control implementation violated its allowlist")
    result["controls"] = controls
    return result


_TARGET_OFFSETS_SECONDS = MappingProxyType(
    {
        "y1": (1, 61),
        "y2": (2, 62),
        "y5": (5, 65),
    }
)


def build_btc_v1_targets(
    *,
    market_start_us: int,
    reference_bars: Iterable[ReferenceBarInput],
    market_duration_seconds: int = BTC_V1_MARKET_DURATION_SECONDS,
    decision_offset_seconds: int = BTC_V1_DECISION_OFFSET_SECONDS,
) -> dict[str, Any]:
    """Build only the independently available frozen y1/y2/y5 targets."""

    start = _validate_market_start_us(market_start_us)
    timing = _timing(start, market_duration_seconds=market_duration_seconds,
                     decision_offset_seconds=decision_offset_seconds)
    cutoff = timing["decision_cutoff_us"]
    target_boundaries = {
        name: (
            cutoff + entry_offset * _ONE_SECOND_US,
            cutoff + exit_offset * _ONE_SECOND_US,
        )
        for name, (entry_offset, exit_offset) in _TARGET_OFFSETS_SECONDS.items()
    }
    all_required = tuple(
        boundary
        for name in BTC_V1_TARGET_FIELDS
        for boundary in target_boundaries[name]
    )
    catalog = _catalog_reference_inputs(
        reference_bars, relevant_boundaries=set(all_required)
    )
    targets: dict[str, dict[str, Any]] = {}
    for name in BTC_V1_TARGET_FIELDS:
        entry_boundary, exit_boundary = target_boundaries[name]
        selected, reasons = _resolve_required_bars(
            catalog, (entry_boundary, exit_boundary)
        )
        value = None
        if not reasons:
            value = (
                selected[exit_boundary].close / selected[entry_boundary].close
                - 1.0
            )
        targets[name] = {
            "status": "unavailable" if reasons else "available",
            "unavailable_reasons": reasons,
            "entry_semantic_bar_end_us": entry_boundary,
            "exit_semantic_bar_end_us": exit_boundary,
            "value": value,
        }

    if tuple(targets) != BTC_V1_TARGET_FIELDS:
        raise AssertionError("BTC V1 target implementation violated its allowlist")
    return {
        "schema": BTC_V1_TARGET_SCHEMA,
        "target_fields": list(BTC_V1_TARGET_FIELDS),
        "timing": timing,
        "targets": targets,
    }
