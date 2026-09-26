# Experiments and Results

## A. Historical sidecar-based edge_finder_v1

The older `edge_finder_v1` paired BTC 5m Polymarket second-grid observations with local BTC reference sidecars. Its named `pm_ge_010` slice was `p_mid_change_10s >= 0.10`, conditional on a flat prior BTC move. Eleven-date forward returns were directionally positive, but directional reliability was mixed and a crude 1 bp return haircut failed. This was hypothesis and alignment research; it used different artifacts, targets, and selection logic from current ledger-based V1. The earlier Chainlink-labeled research artifacts concern contract outcomes and are also distinct.

## B. Ledger and pipeline validation

The normalized-ledger v2 development cohort certified 10,874 selected sessions with zero quarantined. A July 20 five-bucket date validated 415 canonical ledger families, 19,533,883 rows, and 683,577 trades. These establish data-plane and readback behavior, not predictive performance. Historical prototypes and validation fixtures had limitations in side semantics, quote authority, and unsupported labels; the current modeling uses certified ledger-v2 sessions.

## C. Current ledger-based BTC V1 development study — finalized

All numbers below are **development validation**, using the frozen July 5 boundary and paired populations. The 5m feature identity is `20260923_T074240Z__btc5m-v1__b1d01e6`; exact manifest/result hashes and the 15m/1h/4h/1d identities are in the internal frozen record. Horizons use lifecycle40 at 5m/15m/1h/4h/1d; the earlier 15m fixed120 artifact answers a separate question. The validation set spans seven ET dates except daily, which has four paired validation observations. Lower MSE is better. `A−B` is a signed absolute MSE difference; negative favors A.

| Horizon | Paired train / validation | y1 naive MSE | y1 B MSE | y1 A MSE | A−B MSE | Relative A improvement vs B | A y1 R² | Reading |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| 5m | 5716 / 1801 | 3.06981e-07 | 3.09967e-07 | 3.08563e-07 | -1.40404e-09 | 0.452963% | -0.00525606 | A slightly better than B; both worse than naive |
| 15m | 1904 / 600 | 3.17218e-07 | 3.38334e-07 | 3.44139e-07 | 5.80455e-09 | -1.71563% | -0.0853958 | A worse than B |
| 1h | 473 / 150 | 2.7058e-07 | 2.95825e-07 | 3.00206e-07 | 4.38066e-09 | -1.48083% | -0.124756 | A worse than B and naive |
| 4h | 113 / 36 | 1.17078e-06 | 2.83711e-05 | 3.14229e-05 | 3.05178e-06 | -10.7566% | -28.6967 | stale valid quote dominates error |
| 1d | 12 / 4 | 3.96728e-06 | 4.94245e-06 | 3.58337e-06 | -1.35908e-06 | 27.4982% | -0.141587 | four rows; descriptive only |

The 5m y1 Ridge A improvement over B is small. Fixed-prediction daily stability favored A on six of seven validation ET dates and survived leave-one-date-out; A and B still lost to the training-mean naive predictor. The 15m and 1h A variants were worse than B on y1. The valid 4h July 14 quote was about 44 minutes old and contributed about 96.4% of A's y1 squared validation error; it remains included under the frozen rule. Daily has 12 paired training rows, four validation rows, and 19 A predictors; its four dates favored A, but generalization is unestablished. Fixed boosting and learning curves were completed under the frozen development battery without tuning and did not establish a predictive edge.

### Development sensitivity targets

| Horizon | y2 B MSE | y2 A MSE | y5 B MSE | y5 A MSE |
| --- | ---: | ---: | ---: | ---: |
| 5m | 3.19561e-07 | 3.18599e-07 | 3.21906e-07 | 3.21746e-07 |
| 15m | 3.19474e-07 | 3.22551e-07 | 3.31857e-07 | 3.30717e-07 |
| 1h | 2.74841e-07 | 2.77649e-07 | 2.63315e-07 | 2.64335e-07 |
| 4h | 4.87714e-05 | 5.13747e-05 | 7.0753e-05 | 6.59346e-05 |
| 1d | 4.75061e-06 | 3.523e-06 | 5.56187e-06 | 4.48987e-06 |

### Additional finalized development metrics

All rows below use the development validation split, never the reserved OOS block. The complete machine-readable results retain all models, targets, metrics, coefficients, and preprocessing parameters under the immutable identities below. Pearson r for a constant naive prediction is undefined.

| Horizon | y1 B MAE | y1 A MAE | y1 B R² | y1 A R² | y1 B Pearson r | y1 A Pearson r | y1 paired B0 MSE | y1 paired L MSE |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 5m | 0.000379201 | 0.00037763 | -0.00983021 | -0.00525606 | -0.00763573 | 0.0233093 | 3.10089e-07 | 3.09305e-07 |
| 15m | 0.000383634 | 0.000385051 | -0.0670886 | -0.0853958 | 0.0102904 | 0.004902 | 3.36119e-07 | 3.38017e-07 |
| 1h | 0.000389997 | 0.000392855 | -0.108344 | -0.124756 | -0.0832977 | -0.0427305 | 2.921e-07 | 2.95894e-07 |
| 4h | 0.00150646 | 0.00155452 | -25.8125 | -28.6967 | 0.0395089 | 0.0405096 | 1.12906e-06 | 3.17396e-05 |
| 1d | 0.00180042 | 0.00134352 | -0.574563 | -0.141587 | -0.417997 | 0.27472 | 3.61524e-06 | 5.01444e-06 |

The fixed boosting battery was a development diagnostic, using 100 depth-three trees at learning rate 0.1. The table shows paired validation MSE; the corresponding immutable results contain MAE, R², Pearson r and the full B0/L battery as well. Lower MSE is better.

| Horizon | Target | Naive MSE | Boosting B MSE | Boosting A MSE | A−B MSE |
| --- | --- | ---: | ---: | ---: | ---: |
| 5m | y1 | 3.06981e-07 | 3.20319e-07 | 3.22935e-07 | 2.61631e-09 |
| 5m | y2 | 3.13502e-07 | 3.1943e-07 | 3.24491e-07 | 5.06079e-09 |
| 5m | y5 | 3.16172e-07 | 3.21391e-07 | 3.22858e-07 | 1.46726e-09 |
| 15m | y1 | 3.17218e-07 | 3.2782e-07 | 3.35274e-07 | 7.45451e-09 |
| 15m | y2 | 3.07561e-07 | 3.21622e-07 | 3.28587e-07 | 6.9644e-09 |
| 15m | y5 | 3.24921e-07 | 3.40917e-07 | 3.4858e-07 | 7.66272e-09 |
| 1h | y1 | 2.7058e-07 | 3.41929e-07 | 3.24312e-07 | -1.76174e-08 |
| 1h | y2 | 2.63548e-07 | 3.14813e-07 | 3.23715e-07 | 8.90176e-09 |
| 1h | y5 | 2.51646e-07 | 3.43784e-07 | 3.2067e-07 | -2.31138e-08 |
| 4h | y1 | 1.17078e-06 | 1.21362e-06 | 1.32439e-06 | 1.1077e-07 |
| 4h | y2 | 1.06177e-06 | 1.06591e-06 | 1.07079e-06 | 4.88054e-09 |
| 4h | y5 | 1.02305e-06 | 9.87457e-07 | 1.00643e-06 | 1.89685e-08 |
| 1d | y1 | 3.96728e-06 | 3.73131e-06 | 3.73131e-06 | 0 |
| 1d | y2 | 3.88097e-06 | 3.56415e-06 | 3.56415e-06 | 0 |
| 1d | y5 | 4.48589e-06 | 4.08986e-06 | 4.08986e-06 | 0 |

The frozen Ridge A y1 learning curve used one fixed validation set and chronological 25/50/75/100% training prefixes. Its endpoint comparison is descriptive; it does not select a new training fraction.

| Horizon | 25% training rows | 25% A y1 MSE | Full training rows | Full A y1 MSE | Conditional fixed-prediction daily check |
| --- | ---: | ---: | ---: | ---: | --- |
| 5m | 1423 | 3.16489e-07 | 5716 | 3.08563e-07 | A won 6/7 ET dates; leave-one-date-out retained A |
| 15m | 473 | 3.30205e-07 | 1904 | 3.44139e-07 | skipped: A did not beat B |
| 1h | 119 | 3.4712e-07 | 473 | 3.00206e-07 | skipped: A did not beat B |
| 4h | 28 | 0.000128769 | 113 | 3.14229e-05 | skipped: A did not beat B |
| 1d | 2 | 4.38878e-06 | 12 | 3.58337e-06 | A won 4/4 singleton dates; descriptive only |

### Immutable development provenance

Paths are relative to the private external `research/` root. SHA-256 values bind the exact feature manifest and development Ridge result; the 5m fixed-boosting result hash is `30c539ac9e58fd3c10abd4469f9c441633ff69727ab4fe62ef02dd8b65732039`. The completed development code and results were frozen at Git commit `74d01c15f8f801a4b29c26060fc288771ba416a9`.

| Horizon | Feature manifest | Manifest SHA-256 | Development result | Result SHA-256 |
| --- | --- | --- | --- | --- |
| 5m | `feature_tables/btc_5m_v1/20260923_T074240Z__btc5m-v1__b1d01e6/manifest.json` | `c1df8755141929cd396401152fe3cbe59f500a35abbfe9af601a88271b0291ea` | `results/btc_5m_v1/ridge_baseline/results.json` | `7348bfcb1466409cc7740ff2a9d80a1d6fe63f70581ac84b4556bf78a45171d3` |
| 15m | `feature_tables/btc_15m_v1/20260925_T193300Z__btc15m-lifecycle40-v1__398d997/manifest.json` | `d9b521b062c59462842fba2431f3f12df9c8d54d4f853fba2a543e0cb7743d11` | `results/btc_15m_v1/20260925_T193300Z__btc15m-lifecycle40-v1__398d997/results.json` | `2378adc8c7d02a120ecbcb2340470de3f6bf12a6169d2d86b0664b92f795a583` |
| 1h | `feature_tables/btc_1h_v1/20260925_T195450Z__btc1h-lifecycle40-v1__ed33385/manifest.json` | `d009fb1aff6bd93c3e2089923bf522083eb27991f178b22a0c9267e8eae2b9de` | `results/btc_1h_v1/20260925_T195450Z__btc1h-lifecycle40-v1__ed33385/results.json` | `11832f867c512093f5c193bda942e66e8d140eece9d299e4fc0c9a1bb3429ef2` |
| 4h | `feature_tables/btc_4h_v1/20260925_T201358Z__btc4h-lifecycle40-v1__af1c0f8/manifest.json` | `634e5eb5afcf657c93bfe214f73d7d05219da24770c321e2fcc37d0e46a1dad3` | `results/btc_4h_v1/20260925_T201358Z__btc4h-lifecycle40-v1__af1c0f8/results.json` | `23162dbda3cad4107436536b04620024ca4b754462b227013683a1a009bb5e61` |
| 1d | `feature_tables/btc_1d_v1/20260925_T202925Z__btc1d-lifecycle40-v1__1b9c97b/manifest.json` | `7f86cf393fa299aa706a512025b75a597e261eeb9dc56977b30512236e32e3cc` | `results/btc_1d_v1/20260925_T202925Z__btc1d-lifecycle40-v1__1b9c97b/results.json` | `bc912dbdc90edcc5c8445354928df8ced569721820d6ab79a3d5059316bdac3b` |

## FINAL FROZEN OOS — PENDING COMPLETION

Every cell marked `PENDING_FINAL_OOS` is withheld until the one-shot frozen run has completed and its identities and paired coverage have been verified. No result or conclusion is inferred from partial output. The final OOS runner reports the full frozen battery for all horizons and targets; the publication table below highlights the prespecified PM increment.

- Completion status: `PENDING_FINAL_OOS`
- OOS run/result artifact identities and hashes by horizon: `PENDING_FINAL_OOS`
- Freeze identity and source fingerprint verification: `PENDING_FINAL_OOS`
- Development fit counts verified against immutable artifacts: `PENDING_FINAL_OOS`

### Paired coverage

| Horizon | Frozen selected sessions | OOS paired rows | ET-date coverage |
| --- | ---: | ---: | --- |
| 5m | 1440 | PENDING_FINAL_OOS | PENDING_FINAL_OOS |
| 15m | 480 | PENDING_FINAL_OOS | PENDING_FINAL_OOS |
| 1h | 120 | PENDING_FINAL_OOS | PENDING_FINAL_OOS |
| 4h | 30 | PENDING_FINAL_OOS | PENDING_FINAL_OOS |
| 1d | 5 | PENDING_FINAL_OOS | PENDING_FINAL_OOS |

### Primary y1: paired Ridge comparison

`A−B` is `MSE(A)−MSE(B)`; relative improvement is `(MSE(B)−MSE(A))/MSE(B) × 100%`. Negative A−B and positive relative improvement favor A. MAE and R² use the same paired rows; Pearson r is reported when defined.

| Horizon | B MSE | A MSE | A−B absolute | A relative improvement | B MAE | A MAE | B R² | A R² | B Pearson r | A Pearson r | Naive MSE | B0 MSE |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 5m | PENDING_FINAL_OOS | PENDING_FINAL_OOS | PENDING_FINAL_OOS | PENDING_FINAL_OOS | PENDING_FINAL_OOS | PENDING_FINAL_OOS | PENDING_FINAL_OOS | PENDING_FINAL_OOS | PENDING_FINAL_OOS | PENDING_FINAL_OOS | PENDING_FINAL_OOS | PENDING_FINAL_OOS |
| 15m | PENDING_FINAL_OOS | PENDING_FINAL_OOS | PENDING_FINAL_OOS | PENDING_FINAL_OOS | PENDING_FINAL_OOS | PENDING_FINAL_OOS | PENDING_FINAL_OOS | PENDING_FINAL_OOS | PENDING_FINAL_OOS | PENDING_FINAL_OOS | PENDING_FINAL_OOS | PENDING_FINAL_OOS |
| 1h | PENDING_FINAL_OOS | PENDING_FINAL_OOS | PENDING_FINAL_OOS | PENDING_FINAL_OOS | PENDING_FINAL_OOS | PENDING_FINAL_OOS | PENDING_FINAL_OOS | PENDING_FINAL_OOS | PENDING_FINAL_OOS | PENDING_FINAL_OOS | PENDING_FINAL_OOS | PENDING_FINAL_OOS |
| 4h | PENDING_FINAL_OOS | PENDING_FINAL_OOS | PENDING_FINAL_OOS | PENDING_FINAL_OOS | PENDING_FINAL_OOS | PENDING_FINAL_OOS | PENDING_FINAL_OOS | PENDING_FINAL_OOS | PENDING_FINAL_OOS | PENDING_FINAL_OOS | PENDING_FINAL_OOS | PENDING_FINAL_OOS |
| 1d | PENDING_FINAL_OOS | PENDING_FINAL_OOS | PENDING_FINAL_OOS | PENDING_FINAL_OOS | PENDING_FINAL_OOS | PENDING_FINAL_OOS | PENDING_FINAL_OOS | PENDING_FINAL_OOS | PENDING_FINAL_OOS | PENDING_FINAL_OOS | PENDING_FINAL_OOS | PENDING_FINAL_OOS |

### Prespecified y2 and y5 sensitivity

| Horizon | y2 B MSE | y2 A MSE | y2 A−B | y5 B MSE | y5 A MSE | y5 A−B |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| 5m | PENDING_FINAL_OOS | PENDING_FINAL_OOS | PENDING_FINAL_OOS | PENDING_FINAL_OOS | PENDING_FINAL_OOS | PENDING_FINAL_OOS |
| 15m | PENDING_FINAL_OOS | PENDING_FINAL_OOS | PENDING_FINAL_OOS | PENDING_FINAL_OOS | PENDING_FINAL_OOS | PENDING_FINAL_OOS |
| 1h | PENDING_FINAL_OOS | PENDING_FINAL_OOS | PENDING_FINAL_OOS | PENDING_FINAL_OOS | PENDING_FINAL_OOS | PENDING_FINAL_OOS |
| 4h | PENDING_FINAL_OOS | PENDING_FINAL_OOS | PENDING_FINAL_OOS | PENDING_FINAL_OOS | PENDING_FINAL_OOS | PENDING_FINAL_OOS |
| 1d | PENDING_FINAL_OOS | PENDING_FINAL_OOS | PENDING_FINAL_OOS | PENDING_FINAL_OOS | PENDING_FINAL_OOS | PENDING_FINAL_OOS |

Full y1/y2/y5 naive, B0, B, L, A Ridge and fixed boosting MSE/MAE/R²/Pearson r remain in the immutable result artifacts: `PENDING_FINAL_OOS`.

### Fixed-prediction y1 behavior by ET date

For each horizon and eligible date, insert row count, B MSE, A MSE, winner, and signed `sum((y-B)^2−(y-A)^2)` from the frozen runner. Singleton daily dates may use raw squared errors. No date-specific refit or post-hoc exclusion.

| Horizon | ET date | Paired rows | B MSE | A MSE | Winner | Signed SSE improvement |
| --- | --- | ---: | ---: | ---: | --- | ---: |
| PENDING_FINAL_OOS | PENDING_FINAL_OOS | PENDING_FINAL_OOS | PENDING_FINAL_OOS | PENDING_FINAL_OOS | PENDING_FINAL_OOS | PENDING_FINAL_OOS |

### Development versus OOS and conclusion

| Horizon | Development y1 A−B MSE | Final OOS y1 A−B MSE | Stability across dates | Interpretation |
| --- | ---: | ---: | --- | --- |
| 5m | -1.40404e-09 | PENDING_FINAL_OOS | PENDING_FINAL_OOS | PENDING_FINAL_OOS |
| 15m | 5.80455e-09 | PENDING_FINAL_OOS | PENDING_FINAL_OOS | PENDING_FINAL_OOS |
| 1h | 4.38066e-09 | PENDING_FINAL_OOS | PENDING_FINAL_OOS | PENDING_FINAL_OOS |
| 4h | 3.05178e-06 | PENDING_FINAL_OOS | PENDING_FINAL_OOS | PENDING_FINAL_OOS |
| 1d | -1.35908e-06 | PENDING_FINAL_OOS | PENDING_FINAL_OOS | PENDING_FINAL_OOS |

Final interpretation: `PENDING_FINAL_OOS`.

Final V1 conclusion: `PENDING_FINAL_OOS`.
