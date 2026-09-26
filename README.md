# Polymarket BTC Market Research

This project asks whether Polymarket BTC market state at 40% of a market's lifetime adds predictive association for subsequent BTC spot returns beyond BTC-only and quote-quality controls. The current result is an **archival event-time study**, not a live trading system. Final frozen out-of-sample (OOS) metrics and the V1 conclusion are **PENDING_FINAL_OOS**.

## What is studied

The Dell collector records Polymarket BTC binary-market WebSocket messages for 5m, 15m, 1h, 4h, and 1d markets. Immutable raw captures feed a normalized event ledger with source order, receipt timestamps, and provenance. Certified whole-session ledgers feed a causal Polymarket feature projection. Binance spot `BTCUSDT` one-second archives supply event-time BTC controls and forward-return targets. The evaluation compares BTC-only `B0`, BTC plus PM quote quality `B`, PM level `L`, and PM level plus 10-second repricing `A` on paired rows.

```text
Polymarket raw capture → normalized ledger → causal PM feature table
Binance BTCUSDT 1s archive ────────────────→ BTC controls and y1/y2/y5
                                          → chronological validation → frozen OOS
```

The earlier sidecar-based `edge_finder_v1` tested a thresholded 5m repricing slice with local BTC sidecars. Its eleven-date direction was positive, but a rough 1 bp cost haircut failed. That study and the older Chainlink-labeled contract-outcome artifacts are distinct from the current ledger-based archival BTC V1.

## Development evidence

The certified development cohort has 10,874 selected ledger sessions across five horizons. The canonical 5m feature artifact has 7,548 rows. Development validation begins July 5, 2026 ET; the 5m paired train/validation counts are 5,716/1,801. Ridge uses alpha 1, an unpenalized intercept, and training-only population-variance standardization. Fixed boosting uses 100 depth-three trees and learning rate 0.1. No model or threshold tuning used OOS.

For 5m y1 development validation, Ridge B MSE was `3.099668659e-7` and A MSE was `3.085628304e-7`; the training-mean naive MSE was `3.069806683e-7`. A slightly improved on B yet both were worse than naive. Other horizon findings and sensitivity targets are in the [result summary](RESULTS/summary.md). These are development results, not the final OOS conclusion.

## Final frozen OOS

Run status: `PENDING_FINAL_OOS`. Paired coverage: `PENDING_FINAL_OOS`. Final y1/y2/y5 metrics: `PENDING_FINAL_OOS`. Development-versus-OOS interpretation: `PENDING_FINAL_OOS`. Final V1 conclusion: `PENDING_FINAL_OOS`.

The source cohort and scoring procedure were frozen before OOS access. After completion, the final results table will report paired coverage, MSE, MAE, R², Pearson r where defined, A-versus-B deltas, per-date behavior, and the V1 interpretation without changing the model or protocol.

## Navigate and reproduce

- [Data and feature methodology](DOCUMENTATION/data_and_feature_methodology.md) explains raw, ledger, Binance bars, as-of features, lineage, and the private data boundary.
- [Evaluation methodology](DOCUMENTATION/evaluation_methodology.md) specifies chronological splitting, comparators, metrics, leakage prevention, and the one-shot OOS procedure.
- [Experiments and results](RESULTS/summary.md) separates historical sidecar research, pipeline validation, finalized development evidence, and prepared OOS tables.
- [Limitations and next steps](DOCUMENTATION/limitations_and_next_steps.md) covers time, cost, latency, and regime limits.
- [Selected code](CODE/README.md) contains the pure Binance reference builder and a public inspection build of the PM projector.

The public snapshot excludes raw captures, ledger payloads, Binance archive copies, feature tables, model output files, host control evidence, and private operational history. These are large, host-specific, or contain detailed collection provenance. The methodology records stable cohort, manifest, code, and result identities so an authorized reviewer with the canonical data can check lineage and reproduce the development study. The Dell and external drive explain the scale and retention design; this repository is for research and engineering review, not one-command deployment.

Historical Binance bars do not prove that finalized one-second bars were available locally at the decision instant. Neither the historical sidecar results nor development validation support a live-executable or profitable edge claim.
