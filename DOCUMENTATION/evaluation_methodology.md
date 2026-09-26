# Evaluation Methodology

## Frozen development design

The certified development cohort is `btc_intraday_dev_20260615_20260714_v1`, June 15–July 14 ET. July 10–12 are excluded due to a collection outage. Validation starts July 5 00:00 ET: training uses June 15–July 4; validation uses July 5–9 and July 13–14. The 5m artifact has 5,744 training and 1,804 validation rows for standalone BTC `B0`; 5,716 and 1,801 have complete paired `B/L/A` features. A training row is purged if its latest target boundary crosses validation start; zero 5m rows were purged. No PM imputation or extra embargo was used.

The naive reference predicts the training target mean. Ridge fits `B0`, `B`, `L`, and `A` separately for each `y1/y2/y5`, with alpha 1, unpenalized intercept, training-only population-variance standardization, constant-column scale 1, and no tuning. The fixed squared-error gradient booster uses 100 depth-three trees, learning rate 0.1, and no early stopping. Validation reports MSE, MAE, R², and Pearson r where defined. For a fair PM increment, comparator metrics use identical paired rows; standalone `B0` can also use its larger population. The Ridge A y1 learning curve uses fixed chronological training prefixes. Conditional daily stability uses fixed predictions, with no retraining by date, only where development A beats B.

## Leakage and interpretation

PM features use only messages locally received by their cutoff; BTC controls stop at event-time T; targets begin after T. Feature selection, splits, models, and OOS eligibility are fixed before final OOS access. Validation is development evidence, not unbiased final evidence. Adjacent 5m sessions and seven validation ET dates are highly correlated and provide limited regime coverage. Negative R² or underperformance of naive cannot support a predictive-edge claim.

## Final frozen OOS procedure

The immutable source freeze is `btc_intraday_shared_20260715_20260719_v1`, SHA-256 `ab22cf0df339f97449c6eb0bf4d580517ee4cb68e261d26eee785c29cfa61979`, selecting exactly 1440/480/120/30/5 sessions for 5m/15m/1h/4h/1d. Short-horizon windows cover July 15 00:00 ET to July 20 00:00 ET. Daily uses the frozen whole noon-to-noon ET directory-date exception. Each OOS row requires complete BTC controls and its target, two causal PM views, and finite B/q/dq10 features. Identical paired rows support model comparisons. The frozen runner verifies provenance and development fit counts, refits the fixed models once on all eligible pre-OOS development rows, fits preprocessing there, and scores OOS once. It reports paired counts and ET-date coverage; MSE, MAE, R², and Pearson r for y1/y2/y5; y1 comparisons against B0 and naive; and fixed-prediction per-date y1 A/B behavior. The block is spent after scoring. No threshold, feature, cohort, model, or protocol change is permitted based on OOS.
