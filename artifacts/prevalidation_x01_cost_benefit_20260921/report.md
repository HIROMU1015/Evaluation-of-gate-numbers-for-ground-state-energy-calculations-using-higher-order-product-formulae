# X01 A07: cost-benefit and calibration amortization

Status: complete

This audit equalizes frozen-budget success on the same 17 saved development conditions using the A05 empirical uniform margins. It performs no new PF or molecular calculation. The safety margins are post-hoc diagnostics, not unseen-system guarantees.

## Strategy comparison

| PF | model | four-metric pass | frozen pass before margin | after empirical margin | calibration points over 17 | per-condition range | saved calibration seconds | median safe quantum ratio vs current two-term | basket ratio |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|
| current_m3 | original_one_term | 3/17 | 17/17 | 17/17 | 137 | 8--9 | 211.535 | 1.015194 | 1.012951 |
| current_m3 | refit_one_term | 3/17 | 17/17 | 17/17 | 137 | 8--9 | 211.535 | 1.014560 | 1.012453 |
| current_m3 | two_term | 16/17 | 17/17 | 17/17 | 137 | 8--9 | 211.535 | 1.000000 | 1.000000 |
| two_term_center | original_one_term | 11/17 | 17/17 | 17/17 | 136 | 8--8 | 212.61 | 1.159259 | 1.156721 |
| two_term_center | refit_one_term | 12/17 | 17/17 | 17/17 | 136 | 8--8 | 212.61 | 1.158773 | 1.156457 |
| two_term_center | two_term | 17/17 | 9/17 | 17/17 | 136 | 8--8 | 212.61 | 1.150189 | 1.149805 |

Both PFs use a selected five-point short-time window and three direct fit points. `current_m3` requires one extra evaluated short-time point for `LiH_CAS2e4o`, so its total is 137 points versus 136 for `two_term_center`. This is one saved proxy evaluation over 17 conditions, not a reduction in direct calibration points.

## Paired two-term comparison

After applying the empirical A05 margin to `two_term_center`, its continuous quantum cost relative to `current_m3` ranges from 1.144246 to 1.175105, with median 1.150189. The equal-one-run 17-condition basket ratio is 1.149805.

Using oracle direct required costs instead gives a range of 1.144428 to 1.210110, with median 1.151258. These oracle ratios are diagnostic and are not available to a deployment-time selector.

Saved PF-specific calibration time totals 211.534924 s for `current_m3` and 212.609919 s for `two_term_center` (ratio 1.005082). The paired per-condition timing ratio has median 0.973936 and range 0.817960--1.019914. These small differences are wall-time measurements, not evidence of a different asymptotic calibration cost.

## Amortization

Calibration is paid once while the quantum premium repeats for every QPE run. In the aggregate 17-condition basket, `two_term_center` has both higher saved calibration time and higher quantum cost. Consequently there is no positive reuse count at which it breaks even in these two separate resource coordinates. Quantum cost units and classical seconds are not added without an external conversion rule.

| QPE runs/condition | new/current quantum ratio | current calibration s/run | new calibration s/run | dominance |
|---:|---:|---:|---:|---|
| 1 | 1.149805 | 211.535 | 212.61 | current_m3 lower quantum cost and lower saved calibration time |
| 2 | 1.149805 | 105.767 | 106.305 | current_m3 lower quantum cost and lower saved calibration time |
| 5 | 1.149805 | 42.307 | 42.522 | current_m3 lower quantum cost and lower saved calibration time |
| 10 | 1.149805 | 21.1535 | 21.261 | current_m3 lower quantum cost and lower saved calibration time |
| 50 | 1.149805 | 4.2307 | 4.2522 | current_m3 lower quantum cost and lower saved calibration time |
| 100 | 1.149805 | 2.11535 | 2.1261 | current_m3 lower quantum cost and lower saved calibration time |
| 1000 | 1.149805 | 0.211535 | 0.21261 | current_m3 lower quantum cost and lower saved calibration time |

## A07 conclusion

Under the saved additive cost model, `current_m3` plus the two-term model is the preferred operational strategy among these six cells: it already meets the frozen budget on all 17 saved conditions and has lower margin-adjusted quantum cost on every condition. The new PF saves one short-time proxy evaluation across all 17 conditions, but not a direct fit point or aggregate saved calibration time. The new PF's remaining benefit is a wider symmetric prediction margin and the LiH four-metric pass, but A05 shows that this does not translate into a saved precision failure for the baseline. The current evidence therefore does not justify paying the new PF's quantum premium for operational reliability.

This conclusion is limited to correlated development conditions and the continuous proxy. Unseen-family transfer, calibration without exact states, integer QPE rounds, and hardware-level depth remain untested.

## Files

- `calibration_rows.csv`: saved point counts and PF-specific timings.
- `strategy_rows.csv`: condition-level margin-adjusted strategies.
- `strategy_summary.csv`: six PF/model cells.
- `paired_two_term.csv`: direct paired PF comparison.
- `amortization.csv`: reuse-count analysis with separated units.
- `raw_sources.csv`: hashes of the 17 raw calibration sources.
- `cost_benefit.png`: quantum and calibration ratios.
- `analysis.json` and `manifest.json`: machine-readable summary and provenance.
