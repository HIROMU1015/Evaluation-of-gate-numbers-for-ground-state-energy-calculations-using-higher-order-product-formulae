# U1-AR P1-S2：保存データの所在・取得可能性

2026-10-16。固定commitをGitHubから独立bare repositoryへfetchし、対象blobをローカルGit objectとbyte比較した。CSVはヘッダのみを意味的に確認し、数値行の集計・ranking・再解析はしていない。コードは実行せず定義・保存処理を読んだ。各sourceのpath、40文字のorigin/result commit、verified snapshot commit、Git blob、SHA-256、byte数、読解範囲は [provenance.json](provenance.json) に記録する。path導入commitと元runのdirty HEADは別のidentityである。

## 固定sourceと分類

| ID | 固定commit・取得先 | 取得可能性と限界 |
|---|---|---|
| F02 | `e820f653a5916f27233ab4674a89d288cf969e37`、[励起状態CSV](https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/e820f653a5916f27233ab4674a89d288cf969e37/artifacts/prevalidation_f02_tau8_state_mixing_20260921_retry3/excited_state_contributions.csv)、[縮退群CSV](https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/e820f653a5916f27233ab4674a89d288cf969e37/artifacts/prevalidation_f02_tau8_state_mixing_20260921_retry3/degenerate_group_contributions.csv)、[生成コード](https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/e820f653a5916f27233ab4674a89d288cf969e37/review_response/audit_f02_tau8_state_mixing.py) | 公開scalarあり。物理励起gap・D4結合・混合係数あり。有限τのPF全スペクトル/ベクトルと相手IDはこの表にない。 |
| F05 | `e820f653a5916f27233ab4674a89d288cf969e37`、[phase-gap CSV](https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/e820f653a5916f27233ab4674a89d288cf969e37/artifacts/prevalidation_f05_energy_phase_gap_20260922/phase_gap_points.csv)、[summaryヘッダ](https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/e820f653a5916f27233ab4674a89d288cf969e37/artifacts/prevalidation_f05_energy_phase_gap_20260922/condition_summary.csv)、[結合コード](https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/e820f653a5916f27233ab4674a89d288cf969e37/review_response/audit_f05_energy_phase_gap.py) | 公開scalarあり。X02の選択枝・phase gapとF02をsystem/PFで結合。最近接相手のID・全位相・全ベクトル・巻数kを保存しない。 |
| X02 | `e820f653a5916f27233ab4674a89d288cf969e37`、[曲線CSV](https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/e820f653a5916f27233ab4674a89d288cf969e37/artifacts/prevalidation_x02_curve_model_integrity_20260921_retry3/truth_points.csv)、[曲線JSON](https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/e820f653a5916f27233ab4674a89d288cf969e37/artifacts/prevalidation_x02_curve_model_integrity_20260921_retry3/truth_curves.json)、[branch summary](https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/e820f653a5916f27233ab4674a89d288cf969e37/artifacts/prevalidation_x02_curve_model_integrity_20260921_retry3/branch_summary.csv) | 公開scalar曲線。selected raw phase・unwrap integer・effective energy・overlap・residualあり。JSONも各点のscalarで、全Schur系はない。 |
| X02 code補完 | [元コード](https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/2ba6174b6f9617d51766579c775a77132f3c7f57/review_response/audit_x02_curve_model_integrity.py)（snapshot `2ba6174b6f9617d51766579c775a77132f3c7f57`） | e820 snapshotにはこのpathがない。公開済み別commitから取得し、X02 auditの実行時source hash `2fa1ba73481aeda511c706acc8f7f106ca216f4d005e8783786ee2e5122c661f` と一致確認。dirty rootのコードを代用していない。 |
| HF bridge | `6eb1aa02f1d28904741b2cee4f70347e1203198f`、[phase-gap CSV](https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/6eb1aa02f1d28904741b2cee4f70347e1203198f/artifacts/server_f_hf_mechanism_bridge_retry1_20260923_221c7c3/phase_gap_points.csv)、[励起状態CSV](https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/6eb1aa02f1d28904741b2cee4f70347e1203198f/artifacts/server_f_hf_mechanism_bridge_retry1_20260923_221c7c3/excited_state_contributions.csv)、[元report](https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/6eb1aa02f1d28904741b2cee4f70347e1203198f/artifacts/server_f_hf_mechanism_bridge_retry1_20260923_221c7c3/report.md)、[コード](https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/6eb1aa02f1d28904741b2cee4f70347e1203198f/review_response/run_f_hf_mechanism_bridge.py) | 公開scalarあり。元reportの36 diagnostic eigendecompositionは計算の会計値であり、36組の全固有値/固有ベクトル保存の意味ではない。保存処理はscalar CSV/JSON・図・manifest。全Schur系は公開artifactに保存されない。 |
| NH3 | `e820f653a5916f27233ab4674a89d288cf969e37`、[raw schema](https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/e820f653a5916f27233ab4674a89d288cf969e37/artifacts/server_existing_pf_unified_nh3_20260920_233516_e692360/raw/full_equilibrium__current_m3.json)、[fine schema](https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/e820f653a5916f27233ab4674a89d288cf969e37/artifacts/server_existing_pf_unified_nh3_20260920_233516_e692360/fine/raw/full_equilibrium__current_m3.json)、[準備・点計算コード](https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/e820f653a5916f27233ab4674a89d288cf969e37/review_response/run_full_electron_nh3_higher_term_diagnosis.py)、[stage2コード](https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/e820f653a5916f27233ab4674a89d288cf969e37/review_response/run_existing_pf_unified_nh3_stage2.py) | 選択PF固有値・shift・overlapは公開。確認したschemaに全H励起スペクトル/全PF系なし。準備コードはHの基底状態のみを抽出。fragmentの `component_spectra` は全Hの励起スペクトルではない。 |
| N2 / CO | `6eb1aa02f1d28904741b2cee4f70347e1203198f`、[N2 metadata](https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/6eb1aa02f1d28904741b2cee4f70347e1203198f/artifacts/server_h01_approximate_state_calibration_20260922_011228_e0692a8/cache/N2_active_eq_sto3g.metadata.json)、[CO metadata](https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/6eb1aa02f1d28904741b2cee4f70347e1203198f/artifacts/server_h01_approximate_state_calibration_20260922_011228_e0692a8/cache/CO_active_eq_sto3g.metadata.json)、[H01準備コード](https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/e820f653a5916f27233ab4674a89d288cf969e37/review_response/run_h01_approximate_state_calibration.py)。後続scalarは [S0 branch audit](https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/cd81018932b9557b7a55e2e1cd8c5e3988245409/artifacts/server_pf_first_study_s0_exact_time_v1_1_20260925_3279201/branch_audit.csv) | H identity/sectorと選択枝のscalarは公開。H01 cache schemaにはsparse H/state/fragment spectra等があるが、完全H励起系は保存項目ではない。全PF位相・相手との対応も公開表にない。historical cacheは今回検索した外部cache範囲で所在未確認。後続R0の別sourceで置換しない。 |
| 後続H6の例 | `19362c23ccdc16b6ad0ff547cc363e138a3930d2`、[A3ヘッダ](https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/19362c23ccdc16b6ad0ff547cc363e138a3930d2/artifacts/validation_expansion_20261007/A3_spectral_components.csv) | `time,eigencomponent_index,tracked,weight,relative_phase,contribution` を持つ別条件の公開scalar。NH3/N2/COやF05の相手状態対応が保存された証拠にはならない。 |

## F02：保存列・状態識別

`excited_state_contributions.csv`：

```text
system_id,formula_id,excited_state_index,excited_energy_hartree,excitation_gap_hartree,d4_coupling_real,d4_coupling_imaginary,d4_coupling_absolute,mixing_contribution_hartree
```

`degenerate_group_contributions.csv`：

```text
system_id,formula_id,degenerate_group_index,excited_energy_hartree,excitation_gap_hartree,state_count,first_state_index,last_state_index,squared_d4_coupling,mixing_contribution_hartree,absolute_mixing_share
```

生成コードの `state_mixing_contributions`（81–170行付近）は保存Hをeighし、referenceと最大overlapのtargetが基底であることを検査する。`excited_state_index` はこのHの固有値順のindexでtargetを除いたもの。gapは `E_n−E_0`、結合は `⟨n|D4|0⟩`、mixingは `|結合|²/(E_0−E_n)`。縮退群はエネルギー差 `1e-10 Ha` 以内でgroup化し、群index・先頭/末尾index・個数・結合絶対値二乗の和を保存する。縮退内の個別固有ベクトルやindexは基底選択依存。群への和と、有限τのPF最近接相手のidentityを混同しない。

`mixing_contribution_hartree` はa8の係数寄与で、τ⁸を掛けた有限時間energy shiftそのものではない。D4/D8等の `_hartree` suffixはatomic-unitでの係数値の名称でもあり、物理energy列と同一の次元扱いにはできない（[定義監査](definition_contract_audit.md)）。数値補正はしていない。

## F05 / X02：必要fieldと欠落

F05 `phase_gap_points.csv`：

```text
system_id,formula_id,point_index,time_hartree_inverse,physical_minimum_gap_hartree,selected_phase_gap_radians,phase_gap_over_time_hartree,normalized_phase_gap_over_physical_gap,selected_ground_overlap_probability,previous_branch_overlap_probability,selection_rules_agree,branch_warning,inside_reliable_prefix
```

最初のwarningは時間順の保存点で `branch_warning` が初めてtrueになる点。根の探索・連続的な発火時刻ではない。reliable prefixはその点より前。X02から受け取るwarningは選択規則不一致、ground確率<0.9、previous確率<0.9、円周gap<1e-6 radのOR。最初のwarningをAR発生時刻とする定義ではない。

円周gapは選択PF位相から同一restricted sectorの他の全PF位相への `abs(angle(exp(i Δphase)))` の最小値。相手は時間ごとに変化し得る。`phase_gap_over_time_hartree` はこの値/τ、normalized値の分母はF02の物理最小gap。特定励起状態のgapや支配的D4混合群gapを分母にしていない。

X02には `continuous_branch_index` と `maximum_ground_overlap_branch_index`、`raw_eigenphase_radians`、`phase_unwrap_integer`、`selected_effective_energy_hartree` がある。ただし前者は各点のSchur列indexであり永続的なH励起状態IDではない。相手のPF index、相手のunwrap、相手とH励起状態とのoverlap対応、全PF固有ベクトルは保存されない。公開scalarだけからその対応の一意な復元を保証できない。

[F05元report](https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/e820f653a5916f27233ab4674a89d288cf969e37/artifacts/prevalidation_f05_energy_phase_gap_20260922/report.md) は最初のwarning全条件にground-overlap低下を含むと報告している。ここでは元reportの記述を確認しただけで、CSV行から再集計していない。

## H / PF / sector / energy originのidentity

F02とF03は同じF01 `effective_operators.npz` のSHA-256をinputに記録している。F01コードの保存schemaはH/reference state、fragment groups、D4/D6/D8等。[PF registry](https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/e820f653a5916f27233ab4674a89d288cf969e37/artifacts/prevalidation_f01_effective_hamiltonian_multipf_20260921_retry1/formula_registry.csv) は `weights_json,s2_sequence_json,s2_block_count,expanded_step_count,normalization` を保持する。[F01コード](https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/e820f653a5916f27233ab4674a89d288cf969e37/review_response/audit_f01_effective_hamiltonian_multipf.py) のregistry、[PF展開](https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/e820f653a5916f27233ab4674a89d288cf969e37/src/trotterlib/pf_decomposition.py)、[PF実装](https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/e820f653a5916f27233ab4674a89d288cf969e37/src/trotterlib/product_formula.py) が順序・fragment展開の固定source。係数の再加算・新しいW_S算出は行わない。

[H-chain準備コード](https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/e820f653a5916f27233ab4674a89d288cf969e37/review_response/validate_hchain_perturbative_estimator.py) の `_prepare_sector_system` は各groupのidentity項を除き、非定数group和とその基底energyを使用する。X02 JSONのH2 sectorはfixed interleaved spin populations [1,1]・次元4、H4はfixed half populations [2,2]・次元36。F01も同じ準備コードを使う。F05はH2/H4の `yoshida4,current_m3,two_term_center` を結合し、F03にある `m5_best` を含まない。

名目上のsystem/PF/sectorと共通コードは確認でき、F02/F03間は同一NPZのhashで結ばれる。一方、再生成されたX02 HとF01 Hについて、共通の行列byte hash・basis順序hashによる厳密な同一性までは原本に保存されていない。F05のlabel joinだけでそのidentityを証明したとは言えない。これは不一致の実証ではなく、厳密な対応のsource不足。

HF bridgeでは各fragmentのspectral midpointを引き、scalar和をH0へ戻すgaugeを明記。[元manifest](https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/6eb1aa02f1d28904741b2cee4f70347e1203198f/artifacts/server_f_hf_mechanism_bridge_retry1_20260923_221c7c3/manifest.json) はH hash・sector次元20・49 groups等を保持する。HFの枝選択は各点のmaximum-ground方式で、X02のprevious-vector継続とは異なる。finite-logで使うH/PF overlap assignmentは一時的で、全対応表の公開保存はない。

NH3の準備metadataにはgeometry/basis/charge/multiplicity、population/Z2 sectorと `removed_constant_hartree` 等がある。N2/CO H01 metadataはactive CAS(10e,8o)、nα=nβ=5、population次元3136、restricted次元1568、Z2 mask/targetとH hashを持つ。これらを異なる全電子HF/H-chain sectorに横断移植しない。

## private保存、所在未確認、追加計算の区別

| 分類 | 静的確認結果 | 次に必要となり得るもの（今回は実施しない） |
|---|---|---|
| private保存あり・identity確認済み・数値未decode | rootのF01 `effective_operators.npz`：148005 bytes、SHA-256 `a4a6ddc5572faaadd73e6853c32bfd7110c1f838abd4f1946376f64d8db070fc`。HF external cacheの2 pickleも存在し元manifestのhashと一致。private内容は公開しない。 | 利用承認・対象範囲を先に確認。ファイル存在とhash一致は全PF系の保存証明ではない。 |
| 必要fieldが保存されていない | 確認したF05/X02/HF公開出力に最近接相手ID・全PF eigensystem・H励起状態対応なし。HFの36 diagnostic eigendecompositionもこの保存処理でscalar化される。 | 別checkpointの有無とidentityを先に探索・確認する必要がある。36という会計だけから再利用可能な固有ベクトルを仮定しない。 |
| 保存を示す過去の記録はあるが現在の所在未確認 | historical N2/CO cacheは公開sidecarと準備schemaがあるが、今回の外部cache filename検索で実体を特定できなかった。NH3 full-spectrum checkpointも特定できない。 | 所有者・実行環境・保存範囲の確認。権限拒否による取得不能とは今回確認できていない。不存在の全域証明でもない。 |
| 元データの厳密なidentityが未完結 | F01/F02/F03とX02/F05の共通basis/H byte identity。追加のcheckpointがあってもsourceとの一致は別確認。 | source registry、basis order、H/PF/state/gaugeの同一性を先に閉じる。別sourceによるhistorical救済はしない。 |
| 別の科学計算が必要となる可能性 | 既存の完全checkpointが見つからなければ、PF相手やH励起状態への対応を得るには新しい対角化/overlap診断等が必要になり得る。 | 対象座標・PF・state・truth access・回数・停止点を承認した別契約が必要。今回の依頼は承認に含まれない。 |

HF pickleの位置は元manifest記載の `pf_external_cache/h01_hf_mechanism_transfer_20260922_VY56wx/cache/`。eqのfile SHAは `1da32d7e96eddaebfd3039f4576e1b4f86098c1acffb207d59779cf6f3c3b07a`、stretch150は `89e7cff9a70d481fcc15b11908686a47d55b23a2b7206062d8b9a1ea9fe1d173`。確認はstreamでbyte hashを取ったのみで、pickleをdeserializeしていない。

## W_S・ω_n・結合への対応

| 必要量 | 既存fieldと限界 |
|---|---|
| ω_nがbare HのE_n−E_0を意味する場合 | F02/HFの `excitation_gap_hartree` が候補。ただし同じH/sector/state/gaugeが前提。有限τのdressed PF gapではない。 |
| ⟨n\|D4\|0⟩ | F02/HF excited-state表にreal/imag/absoluteと混合寄与あり。有限τの共鳴を生む正確な結合をそのまま与えるとは限らない。 |
| PF係数・fragment順序 | F01 registryと固定PFコード、X02 formula schema、HF protocol/実装、NH3 formula schemaに所在あり。係数値は再集計しない。 |
| W_S・ω_c^max・τ_1・r | 読んだschemaに、Claudeの定義で確定した同名fieldはない。H04/H05のoperator/norm上界やfragment spectraを定義確認なしで同一視できない。ω_nから最大値等を算出していない。 |

現存データで定義と欠落は確認できるが、AR相手の同定・P1-A1〜A4の判定が完結可能とは確認できない。Mandatory STOP。
