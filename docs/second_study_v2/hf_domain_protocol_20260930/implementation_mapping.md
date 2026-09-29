# Static implementation mapping（コード実装なし）

| Pilot concern | Existing source | Reuse / adapter decision |
|---|---|---|
| Arnoldi chain | `pf_spectral_recoverability_d2.build_arnoldi_chain` | scienceを変更せず再利用 |
| prefix analysis | `analyze_prefix`, `analyze_coordinate` | m=1/2/4/8と既存gateを維持 |
| absolute energy lift | `unwrap_energy` | predictor ruleとして維持 |
| HF PF action | D2-A predictorの`CoordinateActions` pattern | HF cache adapterが必要。未実装 |
| rotation count | practical calibration `_rotation_count` | same H/current_m3 identityの確認が必要 |
| local proxy | practical calibrationのproxy acquisition/model | 同一candidateだけを取得するwrapperが必要。34点fit再実行は禁止 |
| domain selector | 新規thin wrapper | allowance→gate→eligible→min budget→tie→fallbackのみ |
| freeze | D2-A prediction artifact/commit verification pattern | 7件固定をそのまま仮定せず新schemaで明示stage |
| branch scorer | D2-A scoring audit definition | old integer-equality scorerは再利用禁止 |
| truth | S0 exact-time cap 2点 + future cap-exterior 4点 | 後者は別承認。nearest snap禁止 |

必要な新コードはHF sanitized cache adapter、budget-targeted selector wrapper、representation-independent scorer、artifact schema、testsに限定する。D2-A coreのstate/PF/width/threshold/mを変える必要が生じた場合はdesign discrepancyとしてP1前に停止する。
