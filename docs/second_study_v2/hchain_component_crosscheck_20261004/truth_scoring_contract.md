# Truth scoring contract — planning only

Direct truthを開く科学scorerは未承認。現在はsourceのtime/identity/field metadataだけを監査し、shift/error magnitudeをtime選択やpolicy設計に使用していない。

## Quantities

- Signed shift: delta_direct [Ha]。PF signは U_P~exp(+iHt)。QPEに入る絶対PF errorは abs(delta_direct) だが、今回はbudget性能を評価しない。
- Cheap error: E_C=abs(cheap_signed_shift-delta_direct)。M1 error: E_M=abs(M1_signed_shift-delta_direct)。
- Width coverage: E_M<=w_M。E_C/epsilon_E、E_M/epsilon_E、w_M/epsilon_Eを別fieldで保存する。epsilon_E=0.00015936001019904 Haは継承値。
- R_C=abs(cheap)/abs(direct)はcheap_proxy_contract.jsonの継承sign floorを超える場合だけ。near-zeroはnull＋absolute error。

## Branch comparison

HF source hf_domain_intervention_pilot.py:physical_branch_correct の表現非依存の規則を維持する。g_phaseはpositive principal target circular phase gap [rad]、g_E=g_phase/t [Ha]と区別し、abs(M1_shift-direct_shift)<g_E/2をcompatibility diagnosticとする。absolute/reference energyが保存されている場合は別fieldで比較する。exact ground certificateを主張しない。

絶対PF energy unwrap整数とground-relative shift unwrap整数を直接比較しない。cheapにbranch-correct labelは付けない。target phase gapが欠ける場合はbranch_indeterminateであり、小さいshift誤差だけでbranch passを認定しない。

## Saved-source limitations

H4のfirst-study branch_audit.csv、H2/H4のF01 holdout、H6 canonical holdoutの対象rowには継承scorerが要求するtarget phase gapが保存されていない。branch-reliable flagやprincipal-log branch-cut marginはtarget gapの代わりではない。既存scalar truthがあることと今回の全scoring fieldが揃うことを分ける。

H6追加direct資料はHamiltonian coefficient hashが元sourceと不一致。numerically_equivalent=trueでもexact-match truthとしてreuseしない。H6のexact-state用200次元restrictionをCISDへ転用しない。

## Future procedural gates

別承認後に限り、prediction freeze commit/blob identity、同一PF/H/state source、absolute timeのbinary64 hex一致、numerical/branch validityを検証してscoreする。nearest、interpolation、new anchorは使用しない。新exact ground stateや新gap計算が必要なら追加の明示承認を要する。現在はscorerを実装・実行していない。
