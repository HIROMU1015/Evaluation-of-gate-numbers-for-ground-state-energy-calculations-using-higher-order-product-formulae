# D2R R1 selected-coordinate cause decomposition

The closed second-study decision remains `complete_no_benefit`. All exact-state and direct-shift use below is post-hoc development diagnosis.

## Fixed calculation counts

- system_cache_reused: 0
- proxy_cache_reused: 0
- system_regeneration_count: 0
- phase_a_system_cache_reuse_count: 4
- exact_ground_regeneration_count: 4
- saved_cisd_proxy_reuse_count: 5
- new_cisd_proxy_count: 5
- new_exact_proxy_count: 10
- environment_bridge_cisd_proxy_count: 0
- hamiltonian_byte_identity_mismatch_count: 0
- computed_this_invocation: 15
- new_direct_truth_coordinate_count: 0
- full_pf_unitary_build_count: 0
- gpu_operation_count: 0

## Strategy-level decomposition

| Condition | Strategy | Safe | Attribution | model/a | state/a | proxy/a | CISD-local safe | exact-local safe |
|---|---|---:|---|---:|---:|---:|---:|---:|
| LiF_active_eq_sto3g | current_fallback | False | model_component | 40.142 | 5.524 | 0.086 | False | True |
| LiF_active_eq_sto3g | equal_information_pooled_fit | False | model_component | 40.142 | 5.524 | 0.086 | False | True |
| LiF_active_eq_sto3g | multiple_window_rule | False | model_component | 40.142 | 5.524 | 0.086 | False | True |
| LiF_active_eq_sto3g | uncapped_counterfactual | False | model_component | 33.326 | 3.969 | 0.047 | False | True |
| LiF_active_stretch150_sto3g | current_fallback | True | state_component | 1.433 | 4.977 | 0.013 | True | True |
| LiF_active_stretch150_sto3g | equal_information_pooled_fit | True | state_component | 1.433 | 4.977 | 0.013 | True | True |
| LiF_active_stretch150_sto3g | multiple_window_rule | True | state_component | 1.433 | 4.977 | 0.013 | True | True |
| LiF_active_stretch150_sto3g | uncapped_counterfactual | True | state_component | 1.723 | 5.378 | 0.015 | True | True |
| HCl_full_eq_sto3g | current_fallback | False | mixed_or_none | 0.945 | 0.000 | 0.643 | True | True |
| HCl_full_eq_sto3g | equal_information_pooled_fit | True | proxy_eigenvalue_component | 0.122 | 0.000 | 2.322 | True | True |
| HCl_full_eq_sto3g | multiple_window_rule | True | mixed_or_none | 0.000 | 0.000 | 0.310 | True | True |
| HCl_full_eq_sto3g | uncapped_counterfactual | True | model_component | 13.121 | 0.000 | 2.560 | True | True |
| HCl_full_stretch150_sto3g | current_fallback | True | mixed_or_none | 0.576 | 0.000 | 0.074 | True | True |
| HCl_full_stretch150_sto3g | equal_information_pooled_fit | False | proxy_eigenvalue_component | 0.003 | 0.000 | 4.774 | False | False |
| HCl_full_stretch150_sto3g | multiple_window_rule | True | mixed_or_none | 0.576 | 0.000 | 0.074 | True | True |
| HCl_full_stretch150_sto3g | uncapped_counterfactual | True | model_component | 25.455 | 0.000 | 0.092 | True | True |

## Coordinate-level state controls

| Condition | t | CISD source | CISD residual | exact overlap | exact residual |
|---|---:|---|---:|---:|---:|
| LiF_active_eq_sto3g | 0.90401845416 | new_r1_cisd_proxy | 1.770e-01 | 0.99110939959 | 7.760e-15 |
| LiF_active_eq_sto3g | 0.932979331066 | new_r1_cisd_proxy | 1.770e-01 | 0.99110939959 | 7.760e-15 |
| LiF_active_stretch150_sto3g | 0.703783641376 | new_r1_cisd_proxy | 1.166e-01 | 0.966620002943 | 1.363e-14 |
| LiF_active_stretch150_sto3g | 0.718579853821 | new_r1_cisd_proxy | 1.166e-01 | 0.966620002943 | 1.363e-14 |
| HCl_full_eq_sto3g | 0.121182035223 | saved_phase_a_proxy | 9.967e-08 | 1 | 1.088e-13 |
| HCl_full_eq_sto3g | 0.15753664579 | saved_phase_a_proxy | 9.967e-08 | 1 | 1.088e-13 |
| HCl_full_eq_sto3g | 0.193891256357 | saved_phase_a_proxy | 9.967e-08 | 1 | 1.088e-13 |
| HCl_full_stretch150_sto3g | 0.155106715353 | saved_phase_a_proxy | 2.457e-06 | 1 | 8.388e-14 |
| HCl_full_stretch150_sto3g | 0.201638729958 | saved_phase_a_proxy | 2.457e-06 | 1 | 8.388e-14 |
| HCl_full_stretch150_sto3g | 0.248170744564 | new_r1_cisd_proxy | 2.457e-06 | 1 | 8.388e-14 |

R2 is not authorized. Stop here for research-direction review.
