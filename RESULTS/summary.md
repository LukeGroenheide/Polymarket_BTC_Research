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

## D. Final frozen OOS — completed

The one-shot evaluation scored all 2,075 selected sessions from July 15–19, 2026 ET. All selected sessions were eligible for the paired comparison. The model, features, split, and scoring protocol were unchanged after the freeze.

- Execution commit: `40adfac2187eeb350833d5e491c20667cb5d7551`; run ID: `btc-v1-final-oos__40adfac`.
- Frozen protocol SHA-256: `c302cbc17cd9b81e5b0c87a2bbd86f76f551a0a6de8192e2313f57f41fca40d9`.
- Final result record: internal Git commit `34a964ea162e194a4cc16ea3ffef072082dda2ef`, `SOURCE_OF_TRUTH/BTC_V1_OOS_RESULTS.md`. The private result artifacts remain under the external research data root.

### Paired coverage

| Horizon | Selected and paired OOS rows | ET dates |
| --- | ---: | --- |
| 5m | 1,440 | July 15–19, 2026 |
| 15m | 480 | July 15–19, 2026 |
| 1h | 120 | July 15–19, 2026 |
| 4h | 30 | July 15–19, 2026 |
| 1d | 5 | July 15–19, 2026 |

### Primary y1 comparison

These are Ridge results on identical paired rows. B uses BTC and quote-quality controls; A adds Polymarket level and recent price movement. Lower MSE is better. A positive relative improvement means A beat B. B0 is the paired BTC-only comparator.

| Horizon | B MSE | A MSE | A−B MSE | A improvement vs B | Naive MSE | Paired B0 MSE | B / A MAE | B / A R² | B / A Pearson r |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 5m | 1.801451e-07 | 1.796818e-07 | -4.632557e-10 | +0.257% | 1.800388e-07 | 1.800781e-07 | 0.0002715487 / 0.0002717392 | -0.000810629 / 0.001763026 | 0.02816976 / 0.05873852 |
| 15m | 1.975804e-07 | 1.984374e-07 | 8.570397e-10 | -0.434% | 1.950144e-07 | 1.964373e-07 | 0.0002882006 / 0.0002909796 | -0.01467647 / -0.01907781 | 0.02956018 / 0.03066166 |
| 1h | 1.464771e-07 | 1.502189e-07 | 3.741787e-09 | -2.555% | 1.395259e-07 | 1.465694e-07 | 0.0002748906 / 0.000277103 | -0.05972973 / -0.08680073 | -0.01385461 / -0.02438201 |
| 4h | 2.252915e-07 | 2.403527e-07 | 1.506117e-08 | -6.685% | 1.862208e-07 | 2.21277e-07 | 0.0003734654 / 0.000396282 | -0.3841963 / -0.4767324 | 0.03955253 / 0.1744264 |
| 1d | 1.900202e+22 | 1.917011e+22 | 1.680829e+20 | -0.885% | 2.62087e-07 | 3.54377e-06 | 6.164742e+10 / 6.191948e+10 | -1.745668e+30 / -1.76111e+30 | 0.1864615 / 0.1864615 |

At 5m, A had 0.257% lower y1 MSE than B and also narrowly beat naive. The same small A-over-B direction appeared in development validation, where both models lost to naive. At 15m, 1h, 4h, and 1d, A did not beat B. The five-row 1d Ridge result is dominated by an extreme July 16 error; the row remains included under the frozen rule.

### Prespecified y2 and y5 checks

| Horizon | y2 B MSE | y2 A MSE | y5 B MSE | y5 A MSE |
| --- | ---: | ---: | ---: | ---: |
| 5m | 1.800819e-07 | 1.79755e-07 | 1.736079e-07 | 1.734408e-07 |
| 15m | 1.941551e-07 | 1.957799e-07 | 1.860405e-07 | 1.879522e-07 |
| 1h | 1.78046e-07 | 1.82233e-07 | 1.840656e-07 | 1.893523e-07 |
| 4h | 2.239936e-07 | 2.362164e-07 | 1.732362e-07 | 1.979205e-07 |
| 1d | 1.823392e+22 | 1.840234e+22 | 2.242329e+22 | 2.264458e+22 |

### Behavior by ET date

The date check uses the same fixed predictions; there was no refit by date. A beat B on all five 5m dates. At 15m and 1h it beat B on one of five dates, at 4h on three, and at 1d on one. Longer-horizon date counts are small, especially the one-row daily dates.

| 5m ET date | Paired rows | B y1 MSE | A y1 MSE |
| --- | ---: | ---: | ---: |
| 2026-07-15 | 288 | 2.621164e-07 | 2.611074e-07 |
| 2026-07-16 | 288 | 2.013813e-07 | 2.012869e-07 |
| 2026-07-17 | 288 | 2.32564e-07 | 2.322134e-07 |
| 2026-07-18 | 288 | 5.707277e-08 | 5.68985e-08 |
| 2026-07-19 | 288 | 1.475908e-07 | 1.469028e-07 |

### Development compared with OOS

The direction is based on the same A-versus-B y1 MSE comparison. Development was used to choose and freeze V1; the reserved dates were scored once afterward.

| Horizon | Development A−B MSE | OOS A−B MSE | OOS date wins for A |
| --- | ---: | ---: | ---: |
| 5m | -1.40404e-09 | -4.632557e-10 | 5/5 |
| 15m | 5.80455e-09 | 8.570397e-10 | 1/5 |
| 1h | 4.38066e-09 | 3.741787e-09 | 1/5 |
| 4h | 3.05178e-06 | 1.506117e-08 | 3/5 |
| 1d | -1.35908e-06 | 1.680829e+20 | 1/5 |

### Final V1 conclusion

The 5-minute result suggests that the added Polymarket features may contain a small amount of incremental predictive information beyond the BTC and market-quality controls used here. But the effect is small, the slower horizons did not reproduce it, and the study does not establish a profitable trading edge or live execution performance.

This is an archival event-time association study. Historical Binance bars do not prove that finalized one-second bars were locally available at the decision moment. Five OOS dates and overlapping short-horizon markets provide limited independent regime coverage. Any changed model or protocol would require a new version and a future untouched evaluation block.
