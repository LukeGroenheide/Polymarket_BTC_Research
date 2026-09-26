#!/usr/bin/env python3
"""One entirely synthetic session-to-paired-Ridge path; no private data."""

from __future__ import annotations

import copy
import datetime as dt
import json
import math
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "CODE"))

from polymarket_research import btc_reference, btc_timing, causal_features, paired_ridge


SESSION_PATH = Path(__file__).with_name("synthetic_session.json")


def load_session(path: Path = SESSION_PATH) -> dict:
    with path.open(encoding="utf-8") as source:
        return json.load(source)


def make_variant(template: dict, index: int) -> dict:
    """Move an invented session to a later 5m window for a tiny model example."""
    session = copy.deepcopy(template)
    shift = dt.timedelta(minutes=5 * index)
    manifest = session["session_manifest"]
    manifest["session_id"] = f"synthetic-session-{index:03d}"
    manifest["market_id"] = f"synthetic-market-{index:03d}"
    manifest["window_start_ms"] += int(shift.total_seconds() * 1000)
    manifest["window_end_ms"] += int(shift.total_seconds() * 1000)
    for row in session["canonical_records"]:
        row["session_id"] = manifest["session_id"]
        row["market_id"] = manifest["market_id"]
        received = dt.datetime.fromisoformat(row["local_receive_timestamp_utc"])
        row["local_receive_timestamp_utc"] = (received + shift).isoformat()
        if row["source_index"] < 2:
            row["best_bid"] += index * (0.001 + row["source_index"] * 0.001)
            row["best_ask"] += index * (0.001 + row["source_index"] * 0.001)
    session["synthetic_btc"]["variant"] = index
    return session


def synthetic_binance_rows(session: dict, timing: btc_timing.BTCTiming) -> list[list[str]]:
    """Generate invented 12-column one-second rows, including C(S) and targets."""
    spec = session["synthetic_btc"]
    variant = spec.get("variant", 0)
    start_us = timing.window_start_ms * 1000
    rows = []
    for second in range(timing.decision_offset_seconds + 66):
        boundary_us = start_us + second * 1_000_000
        close = (spec["base_close"] + (spec["slope_per_second"] + 0.04 * variant) * second
                 + spec["wave_amplitude"] * math.sin((second + 3 * variant) / 9))
        # Only open time, close price, and raw close time are read by the parser.
        rows.append([str(boundary_us - 1_000_000), "0", "0", "0",
                     f"{close:.8f}", "0", str(boundary_us - 1),
                     "0", "0", "0", "0", "0"])
    return rows


def build_model_row(session: dict) -> tuple[dict, dict, btc_timing.BTCTiming]:
    """Assemble the same named PM, BTC, and target fields on one session ID."""
    manifest = session["session_manifest"]
    timing = btc_timing.lifecycle40(
        manifest["bucket"], manifest["window_start_ms"], manifest["window_end_ms"]
    )
    projector = {
        "5m": causal_features.project_btc_5m_polymarket_features,
        "15m": causal_features.project_btc_15m_polymarket_features,
        "1h": causal_features.project_btc_1h_polymarket_features,
        "4h": causal_features.project_btc_4h_polymarket_features,
        "1d": causal_features.project_btc_1d_polymarket_features,
    }[manifest["bucket"]]
    pm = projector(session_manifest=manifest,
                   canonical_records=session["canonical_records"])

    # The real materializer keeps pre-T controls and post-T targets separate.
    bars = btc_reference.parse_binance_btcusdt_1s_archive_rows(
        synthetic_binance_rows(session, timing)
    )
    cutoff_us = timing.decision_cutoff_ms * 1000
    start_us = timing.window_start_ms * 1000
    pre_t = [bar for bar in bars if bar.semantic_bar_end_us <= cutoff_us]
    post_t = [bar for bar in bars if bar.semantic_bar_end_us > cutoff_us]
    kwargs = {"market_start_us": start_us,
              "market_duration_seconds": timing.duration_seconds,
              "decision_offset_seconds": timing.decision_offset_seconds}
    btc = btc_reference.build_btc_v1_event_time_controls(
        reference_bars=pre_t, **kwargs
    )
    targets = btc_reference.build_btc_v1_targets(reference_bars=post_t, **kwargs)
    if (pm["session_id"] != manifest["session_id"] or
            pm["decision_offset_seconds"] != timing.decision_offset_seconds or
            dt.datetime.fromisoformat(pm["decision_cutoff_utc"].replace("Z", "+00:00")) !=
            dt.datetime.fromtimestamp(cutoff_us / 1_000_000, dt.timezone.utc) or
            btc["timing"]["u_event_us"] != cutoff_us or
            targets["timing"]["decision_cutoff_us"] != cutoff_us):
        raise ValueError("PM/BTC/target session timing differs")

    current, lag = pm["as_of_t"], pm["as_of_t_minus_10s"]
    pm_fields = {
        "pm_spread_t": current["spread"],
        "pm_quote_age_seconds_t": current["quote_age_seconds"],
        "pm_spread_t_minus_10s": lag["spread"],
        "pm_quote_age_seconds_t_minus_10s": lag["quote_age_seconds"],
        "q": pm["q"], "dq10": pm["dq10"],
    }
    controls = btc["controls"] or {
        name: None for name in btc_reference.BTC_V1_CONTROL_COLUMNS
    }
    start = dt.datetime.fromtimestamp(timing.window_start_ms / 1000, dt.timezone.utc)
    row = {
        "session_id": manifest["session_id"],
        "start": start,
        "target_end": dt.datetime.fromtimestamp(timing.final_target_ms / 1000,
                                                 dt.timezone.utc),
        "features": {**controls, **pm_fields},
        "targets": {name: targets["targets"][name]["value"]
                    for name in btc_reference.BTC_V1_TARGET_FIELDS},
        "target_status": {name: targets["targets"][name]["status"]
                          for name in btc_reference.BTC_V1_TARGET_FIELDS},
        "pm_status": pm["feature_row_status"],
        "causal_status": pm["causal_status"],
        "btc_status": btc["status"],
    }
    return row, pm, timing


def plot_validation_predictions(rows: list[dict], boundary: dt.datetime,
                                evaluation: dict,
                                output_path: Path = ROOT / "examples" / "output" /
                                "synthetic_predictions.svg") -> Path:
    """Plot only the invented paired validation rows scored above."""
    import matplotlib
    matplotlib.use("Agg")
    from matplotlib import pyplot as plt

    _train, validation, _purged = paired_ridge.chronological_split(
        rows, boundary, "y1"
    )
    if [row["session_id"] for row in validation] != evaluation["paired_validation_sessions"]:
        raise ValueError("Plotted validation population differs from paired evaluation")
    observations = list(range(1, len(validation) + 1))
    to_bp = lambda values: [value * 10_000 for value in values]
    actual = to_bp([row["targets"]["y1"] for row in validation])
    a = to_bp(paired_ridge.predict(
        evaluation["ridge"]["A"], validation, paired_ridge.FEATURES["A"]
    ))
    b = to_bp(paired_ridge.predict(
        evaluation["ridge"]["B"], validation, paired_ridge.FEATURES["B"]
    ))
    naive = to_bp([evaluation["naive"]["train_target_mean"]] * len(validation))

    plt.rcParams["svg.fonttype"] = "none"
    plt.rcParams["svg.hashsalt"] = "polymarket-synthetic-v1"
    figure, (top, lower) = plt.subplots(
        2, 1, figsize=(8.2, 5.9), sharex=True,
        gridspec_kw={"height_ratios": [2.2, 1], "hspace": 0.12},
    )
    figure.suptitle("Synthetic demonstration — not published research results",
                     fontsize=13, fontweight="bold", y=0.985)
    top.plot(observations, actual, color="#202A35", marker="o", linewidth=2,
             label="Actual synthetic y1")
    top.plot(observations, a, color="#1768AC", marker="s", linewidth=1.8,
             label="Ridge A")
    top.plot(observations, b, color="#D97706", marker="D", linewidth=1.6,
             label="Ridge B")
    top.plot(observations, naive, color="#667085", linestyle="--", linewidth=1.4,
             label="Training-mean naive")
    top.set_ylabel("Synthetic y1 BTC return (bp)")
    top.legend(loc="upper left", frameon=False, ncol=2, fontsize=9)
    top.grid(axis="y", color="#D8DEE6", linewidth=0.7)
    top.spines[["top", "right"]].set_visible(False)

    lower.axhline(0, color="#606975", linewidth=0.9)
    lower.plot(observations, [p - y for p, y in zip(a, actual)],
               color="#1768AC", marker="s", linewidth=1.7, label="Ridge A error")
    lower.plot(observations, [p - y for p, y in zip(b, actual)],
               color="#D97706", marker="D", linewidth=1.7, label="Ridge B error")
    lower.set_ylabel("Prediction − target (bp)")
    lower.set_xlabel("Synthetic validation observation")
    lower.set_xticks(observations)
    lower.grid(axis="y", color="#D8DEE6", linewidth=0.7)
    lower.spines[["top", "right"]].set_visible(False)
    figure.text(0.5, 0.008, "Invented inputs; plotted values have no research significance.",
                ha="center", fontsize=8.5, color="#526071")
    figure.subplots_adjust(top=0.88, bottom=0.16, left=0.13, right=0.98)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    figure.savefig(output_path, format="svg", metadata={
        "Date": None,
        "Title": "Synthetic demonstration — not published research results",
        "Description": "Invented validation targets and fixed paired Ridge A, Ridge B, and naive predictions.",
    })
    plt.close(figure)
    # Matplotlib emits whitespace after some SVG tags; keep the generated file
    # clean for Git without changing its shapes, values, or labels.
    svg = output_path.read_text(encoding="utf-8")
    output_path.write_text(
        "\n".join(line.rstrip(" \t") for line in svg.splitlines()) + "\n",
        encoding="utf-8",
    )
    return output_path


def main() -> None:
    template = load_session()
    rows = []
    for index in range(8):
        row, pm, timing = build_model_row(make_variant(template, index))
        rows.append(row)
        if index == 0:
            first_pm = pm
            first_timing = timing
    boundary = rows[5]["start"]
    evaluation = paired_ridge.evaluate_paired(rows, boundary, "y1")
    figure_path = plot_validation_predictions(rows, boundary, evaluation)
    print("Synthetic illustration only; these are not research results.")
    print(f"Cutoff: {dt.datetime.fromtimestamp(first_timing.decision_cutoff_ms / 1000, dt.timezone.utc).isoformat()}")
    print(f"PM source at T: {first_pm['as_of_t']['contributing_source_index']} "
          f"(post-cutoff source 2 excluded); q={first_pm['q']:.4f}; "
          f"dq10={first_pm['dq10']:.4f}")
    print(f"BTC controls: {rows[0]['btc_status']}; y1: {rows[0]['target_status']['y1']}; "
          f"paired eligible: {paired_ridge.eligible(rows[0], 'y1')}")
    print(f"Paired Ridge y1: {evaluation['paired_train_rows']} train, "
          f"{evaluation['paired_validation_rows']} validation, "
          f"{evaluation['purged_train_rows']} purged")
    print(f"Synthetic A vs B MSE: {evaluation['A_vs_B']['a_mse']:.3e} vs "
          f"{evaluation['A_vs_B']['comparator_mse']:.3e}; "
          f"winner={evaluation['A_vs_B']['winner']}")
    print(f"Synthetic figure: {figure_path.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
