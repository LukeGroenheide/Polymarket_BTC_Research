"""Focused checks for the selected public BTC V1 code path."""

from __future__ import annotations

import copy
import datetime as dt
from pathlib import Path
import subprocess
import sys
import unittest
import xml.etree.ElementTree as ET


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "CODE"))
sys.path.insert(0, str(ROOT / "examples"))

from polymarket_research import btc_reference, btc_timing, paired_ridge
import run_synthetic


class PublicExampleTests(unittest.TestCase):
    def setUp(self) -> None:
        self.template = run_synthetic.load_session()

    def test_lifecycle40_offsets_and_window_validation(self) -> None:
        start = self.template["session_manifest"]["window_start_ms"]
        for bucket, seconds, offset in (
            ("5m", 300, 120), ("15m", 900, 360), ("1h", 3600, 1440),
            ("4h", 14400, 5760), ("1d", 86400, 34560),
        ):
            with self.subTest(bucket=bucket):
                timing = btc_timing.lifecycle40(bucket, start, start + seconds * 1000)
                self.assertEqual(timing.decision_offset_seconds, offset)
                self.assertEqual(timing.decision_cutoff_ms, start + offset * 1000)
                self.assertEqual(timing.final_target_ms, start + (offset + 65) * 1000)
        with self.assertRaises(ValueError):
            btc_timing.lifecycle40("5m", start, start + 299_000)

    def test_post_cutoff_quote_is_excluded(self) -> None:
        row, pm, timing = run_synthetic.build_model_row(self.template)
        self.assertEqual(pm["as_of_t"]["contributing_source_index"], 1)
        self.assertEqual(pm["as_of_t"]["prefix_barrier_source_index"], 2)
        self.assertEqual(pm["decision_offset_seconds"], timing.decision_offset_seconds)
        self.assertAlmostEqual(row["features"]["q"], 0.08)
        self.assertAlmostEqual(row["features"]["dq10"], 0.12)

    def test_missing_pm_stays_missing_and_excludes_paired_row(self) -> None:
        session = copy.deepcopy(self.template)
        session["canonical_records"][0]["event_type"] = "trade"
        row, pm, _timing = run_synthetic.build_model_row(session)
        self.assertEqual(pm["feature_row_status"], "missing_lag_snapshot")
        self.assertIsNone(row["features"]["dq10"])
        self.assertIsNone(row["features"]["pm_spread_t_minus_10s"])
        self.assertFalse(paired_ridge.eligible(row, "y1"))
        self.assertTrue(paired_ridge.eligible(row, "y1", paired=False))

    def test_exact_binance_bar_and_unavailable_inputs(self) -> None:
        manifest = self.template["session_manifest"]
        timing = btc_timing.lifecycle40("5m", manifest["window_start_ms"],
                                        manifest["window_end_ms"])
        raw = run_synthetic.synthetic_binance_rows(self.template, timing)
        bars = btc_reference.parse_binance_btcusdt_1s_archive_rows(raw)
        self.assertEqual(bars[0].semantic_bar_end_us, timing.window_start_ms * 1000)
        self.assertEqual(bars[0].raw_close_time_us + 1,
                         bars[0].semantic_bar_end_us)
        self.assertEqual(bars[0].raw_open_time_us + 1_000_000,
                         bars[0].semantic_bar_end_us)
        malformed = raw[0].copy()
        malformed[6] = str(int(malformed[6]) - 1)
        with self.assertRaises(ValueError):
            btc_reference.parse_binance_btcusdt_1s_archive_row(malformed)
        with self.assertRaises(ValueError):
            btc_reference.parse_binance_btcusdt_1s_archive_rows(raw + [raw[0]])

        kwargs = {"market_start_us": timing.window_start_ms * 1000,
                  "market_duration_seconds": timing.duration_seconds,
                  "decision_offset_seconds": timing.decision_offset_seconds}
        cutoff = timing.decision_cutoff_ms * 1000
        post_t = [bar for bar in bars if bar.semantic_bar_end_us > cutoff]
        targets = btc_reference.build_btc_v1_targets(
            reference_bars=post_t, **kwargs
        )
        y1 = targets["targets"]["y1"]
        closes = {bar.semantic_bar_end_us: bar.close for bar in bars}
        self.assertEqual(y1["entry_semantic_bar_end_us"], cutoff + 1_000_000)
        self.assertEqual(y1["exit_semantic_bar_end_us"], cutoff + 61_000_000)
        self.assertAlmostEqual(y1["value"],
                               closes[cutoff + 61_000_000] /
                               closes[cutoff + 1_000_000] - 1)
        controls = [bar for bar in bars if bar.semantic_bar_end_us <= cutoff]
        missing = btc_reference.build_btc_v1_event_time_controls(
            reference_bars=controls[:-1], **kwargs
        )
        self.assertEqual(missing["status"], "unavailable")
        self.assertIn("missing_required_bar",
                      {reason["code"] for reason in missing["unavailable_reasons"]})
        duplicate = btc_reference.build_btc_v1_event_time_controls(
            reference_bars=controls + [controls[-1]], **kwargs
        )
        self.assertEqual(duplicate["status"], "unavailable")
        self.assertIn("duplicate_required_bar",
                      {reason["code"] for reason in duplicate["unavailable_reasons"]})

    def test_paired_population_split_and_train_only_scaling(self) -> None:
        rows = [run_synthetic.build_model_row(run_synthetic.make_variant(self.template, i))[0]
                for i in range(8)]
        boundary = rows[5]["start"]
        report = paired_ridge.evaluate_paired(rows, boundary)
        self.assertEqual((report["paired_train_rows"], report["paired_validation_rows"]),
                         (5, 3))
        self.assertEqual(set(report["ridge"]), {"B0", "B", "L", "A"})
        self.assertTrue(all(result["train_rows"] == 5 and
                            result["validation_rows"] == 3
                            for result in report["ridge"].values()))
        self.assertEqual(report["naive"]["train_rows"], 5)
        self.assertEqual(paired_ridge.FEATURES["A"],
                         btc_reference.BTC_V1_COMPARATOR_COLUMNS["A"])

        changed_validation = copy.deepcopy(rows)
        changed_validation[5]["features"]["q"] = 1000.0
        altered = paired_ridge.evaluate_paired(changed_validation, boundary)
        self.assertEqual(report["ridge"]["A"]["training_feature_means"],
                         altered["ridge"]["A"]["training_feature_means"])
        self.assertEqual(report["ridge"]["A"]["training_feature_scales"],
                         altered["ridge"]["A"]["training_feature_scales"])
        self.assertEqual(report["ridge"]["A"]["coefficients_standardized"],
                         altered["ridge"]["A"]["coefficients_standardized"])

        incomplete = copy.deepcopy(rows)
        incomplete[5]["pm_status"] = "missing_current_snapshot"
        paired = paired_ridge.evaluate_paired(incomplete, boundary)
        self.assertEqual(paired["paired_validation_rows"], 2)
        self.assertNotIn(incomplete[5]["session_id"], paired["paired_validation_sessions"])
        self.assertTrue(paired_ridge.eligible(incomplete[5], "y1", paired=False))

        crossing = copy.deepcopy(rows)
        crossing[4]["target_end"] = boundary + dt.timedelta(seconds=1)
        purged = paired_ridge.evaluate_paired(crossing, boundary)
        self.assertEqual(purged["purged_train_rows"], 1)
        self.assertEqual(purged["paired_train_rows"], 4)

    def test_example_runs(self) -> None:
        completed = subprocess.run(
            [sys.executable, "-B", str(ROOT / "examples" / "run_synthetic.py")],
            cwd=ROOT, check=True, capture_output=True, text=True,
        )
        self.assertIn("Synthetic illustration only", completed.stdout)
        self.assertIn("post-cutoff source 2 excluded", completed.stdout)
        self.assertIn("5 train, 3 validation", completed.stdout)
        self.assertIn("Synthetic figure: examples/output/synthetic_predictions.svg",
                      completed.stdout)
        figure = ROOT / "examples" / "output" / "synthetic_predictions.svg"
        self.assertTrue(figure.is_file())
        parsed = ET.parse(figure)
        self.assertEqual(parsed.getroot().tag, "{http://www.w3.org/2000/svg}svg")
        labels = " ".join(element.text or "" for element in parsed.iter())
        for label in ("Synthetic demonstration — not published research results",
                      "Actual synthetic y1", "Ridge A", "Ridge B",
                      "Training-mean naive"):
            self.assertIn(label, labels)


if __name__ == "__main__":
    unittest.main()
