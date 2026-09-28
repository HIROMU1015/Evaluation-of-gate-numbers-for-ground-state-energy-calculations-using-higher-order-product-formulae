# D2R R0 failure ledger

- Source commit: `05649f1a7b6e405eadc2dbbdc0897836e0fa2f02`
- Protocol SHA-256: `a6290b107ebbf93f7c0ee3bc383208862c51e37603a670625091e15472d4584b`
- Strategy-condition rows: 16
- Deduplicated selected coordinates: 10
- Saved selected-time CISD proxies: 5
- Missing selected-time CISD proxies: 5
- Unsafe strategy-condition rows: 6

## Unsafe rows

| Condition | Strategy | Required/frozen | Underestimate/allowance |
|---|---|---:|---:|
| LiF_active_eq_sto3g | current_fallback | 1.804420287 | 45.580539 |
| LiF_active_eq_sto3g | equal_information_pooled_fit | 1.804420287 | 45.580539 |
| LiF_active_eq_sto3g | multiple_window_rule | 1.804420287 | 45.580539 |
| LiF_active_eq_sto3g | uncapped_counterfactual | 1.568569785 | 37.247656 |
| HCl_full_eq_sto3g | current_fallback | 1.005912420 | 1.587767 |
| HCl_full_stretch150_sto3g | equal_information_pooled_fit | 1.006621197 | 1.657764 |

All quantities in this report are read-only derivations from the closed second study. They are post-hoc development diagnostics and do not change its `complete_no_benefit` decision.
