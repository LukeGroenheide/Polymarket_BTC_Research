# Selected research code

`polymarket_research/btc_reference.py` is the private runtime's pure Binance one-second parser and frozen V1 BTC control/target builder. `polymarket_research/causal_features.py` carries the selected PM projection calculation; its import is adapted to the small public `ledger_contract.py` input adapter so this code can be inspected and imported without private production ledger and recovery modules. The private production path uses a fuller ledger-v2 validator and only certified immutable session inputs. This public subset does not validate raw captures, publish artifacts, authorize ledger operation, or replicate the full private build pipeline.

From `CODE/`, import with `python3 -c 'from polymarket_research import btc_reference, causal_features'`. All modules use the Python standard library.
