# Data and Feature Methodology

## Data flow and artifact roles

Polymarket WebSocket raw captures preserve received messages and completion markers before any interpretation. The normalized event ledger is a derived, manifest-bound, create-only projection with source order, local receipt timestamps, canonical observations, sparse trades, inferred idle intervals, and raw-to-row provenance. Research artifacts and the older Chainlink outcome labels are separate products; Chainlink-labeled 5m artifacts were useful for Polymarket contract analysis, but their outcome is not the current BTC forward-return target. Ledger validation established 10,874 certified development sessions across five horizons, with zero quarantined.

The current V1 uses certified whole-session ledgers to construct a causal PM projection at `T=S+0.4*(E-S)`, with as-of views at `T-10s` and `T`. Source rows are eligible only when locally received by the cutoff. The latest eligible quote is carried as state; quote age records staleness. No freshness threshold or zero fill is applied. Missing PM views exclude the row from paired comparisons. Source file hashes, session IDs, market/window identity, builder version, and output hashes are bound in immutable feature manifests.

## Binance reference and BTC features

The BTC reference is the Binance spot `BTCUSDT` public one-second kline archive. Archive timestamps in 2026 are microseconds. `C(t)` is the close of the unique bar covering `[t-1s,t)`; raw close time is `t_us-1`, while semantic bar end is `t_us`. Exact bars are required: no nearest match, interpolation, timestamp tolerance, or fill. The 5m development manifest is `research/feature_tables/btc_5m_v1/20260923_T074240Z__btc5m-v1__b1d01e6/manifest.json` under the private external data root, SHA-256 `c1df8755141929cd396401152fe3cbe59f500a35abbfe9af601a88271b0291ea`. It binds 7,548 selected sessions, the cohort identity, source-ledger hashes, **28 exact Binance daily archive paths and SHA-256 hashes** under `research/reference_data/binance/spot/BTCUSDT/1s/`, builder commit `b1d01e6e734e6f9cd23959ed3778869e8a610780`, model columns, and three hashed output tables. The original 5m materializer is available at `RUNTIME/runtime/research/feature_table_v1.py` in that Git commit; the current checkout uses a later cross-horizon builder.

`B0` has 13 BTC columns: 1/10/60-second log returns, open-to-cutoff log displacement, two 60-second realized-volatility measures, absolute and squared displacement, absolute and squared 10-second return, their interaction, and `g(T)` plus its 10-second change. `g` is a zero-drift diffusion-style BTC basis function using certified expiry and time remaining. Exact formulas, zero-volatility behavior, and required bars are in the internal feature contract and the selected public code. `B` adds PM spread and quote age at both views. `L` adds `q=2*midpoint(T)-1`; `A` adds `dq10=2*(midpoint(T)-midpoint(T-10s))`. The target columns `y1/y2/y5` are separate from predictors:

```text
y1 = C(T+61)/C(T+1)-1
y2 = C(T+62)/C(T+2)-1
y5 = C(T+65)/C(T+5)-1
```

The PM feature cutoff is local Dell receipt time. The Binance endpoint `U_event=T` is an exchange-event-time convention. Historical archives do not prove that the finalized `C(T)` bar was locally available at T. This prevents a claim of live causal availability or executable edge.

## Reproduction guide

Obtain the private certified development ledger cohort and exact Binance `BTCUSDT` one-second archives. Check the 5m feature manifest hash and its source/output hashes; use the manifest's session inventory, builder identity, schema, and selected column lists. Run the selected pure PM projector and BTC reference/control/target builders against validated sessions, then compare output hashes and row counts. The full private data and generated feature tables are omitted from the public snapshot because they include large raw and derived captures and host-specific lineage. The public code documents the transformations; the manifest identities and methodology document the controlled experiment.
