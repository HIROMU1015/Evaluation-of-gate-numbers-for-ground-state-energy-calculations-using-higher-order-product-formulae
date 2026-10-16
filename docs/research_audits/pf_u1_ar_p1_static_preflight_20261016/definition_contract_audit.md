# U1-AR P1-S3：定義・単位の静的照合

2026-10-16。source定義の確認と、Claude原文との照合結果を分ける。Claude `レビューoutter(5).md` は今回検索したアクセス可能範囲では取得できず、§5.6の具体的な式・代入・符号・命題A1〜A4の原文は未確認。したがってClaudeが実際にどの誤りを犯したかという断定はしない。以下の不一致は、既存source間の実在する相違、または明示した同一視に対する条件付き判定である。推論の再計算・数値補正は0件。

分類は `DEFINITION_CONFIRMED`（指定したsourceで確認）、`DEFINITION_MISMATCH`（指定した二定義が異なる）、`INSUFFICIENT_SOURCE`（必要原文/identity/field不足）、`NOT_APPLICABLE`（そのsourceの定義対象外）とする。

## S3-1：時間・単位

| 対象 | 判定 | 確認した定義・Claude推論への制約 |
|---|---|---|
| F05/X02のτ | DEFINITION_CONFIRMED | `time_hartree_inverse` は外側PF一stepの時間、Ha⁻¹。合成S2の各内部stageは係数×τ。QPE全体のcontrolled evolutionの総時間・query数とは異なる。 |
| F03 `t_ana` | DEFINITION_CONFIRMED | [F03コード](https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/e820f653a5916f27233ab4674a89d288cf969e37/review_response/audit_f03_a4_operator_cancellation.py) のprotocolは `(epsilon/(5*abs(a4)))^(1/4)`。one-termのenergy-error modelに基づく時間で、AR時刻・branch warningの測定時刻ではない。式を読んだだけで値は再計算していない。 |
| warning time = t_ana = QPE総時間という同一視 | DEFINITION_MISMATCH | warningは有限grid上の判定、t_anaはモデル式、QPE総時間はunitary呼出しを含む。相互に置換する定義は原本にない。Claudeがこの同一視をしたかはINSUFFICIENT_SOURCE。 |
| 後続HF/NH3/N2/COの時間 | DEFINITION_CONFIRMED | 当該コードのHはatomic-unitで、PFへ渡す外側の時間。HFのCSVは列名 `time` だがprotocol/実装で同じ規約。内部fragment時間・F03のformal coefficient由来t_ana・他runのfit-derived時間を混ぜない。 |
| R1/R6とのraw値比較 | DEFINITION_MISMATCH | R1のsはdimensionlessで一stepはs×total time。R6はeV/eV⁻¹。repositoryのτ/Ha⁻¹と記号・raw数値を無変換で同一視できない。変換や再計算は行わない。 |
| Claude §5.6の使用規約 | INSUFFICIENT_SOURCE | 原文未取得のため逐語照合不能。 |

## S3-2：円周phase gap

根拠は [X02 code](https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/2ba6174b6f9617d51766579c775a77132f3c7f57/review_response/audit_x02_curve_model_integrity.py) 169–174行付近と183–274行付近、[F05 code](https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/e820f653a5916f27233ab4674a89d288cf969e37/review_response/audit_f05_energy_phase_gap.py)、[HF code](https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/6eb1aa02f1d28904741b2cee4f70347e1203198f/review_response/run_f_hf_mechanism_bridge.py) 343–350行付近。

| 対象 | 判定 | 定義・制約 |
|---|---|---|
| `selected_phase_gap_radians` | DEFINITION_CONFIRMED | rad。X02は選択phaseと同一sector内の他の全PF phaseの差をmod 2πの円周距離へ写し、自己を除いた最小値。HFもeigval比のangleで同じ円周距離。full Hilbert空間全体の最小値ではない。 |
| sector | DEFINITION_CONFIRMED | X02 H2はspin population [1,1]/次元4、H4は[2,2]/次元36。HF bridgeは原本metadataのrestricted次元20。NH3/N2/COは別のpopulation/Z2 sector。 |
| 最近接相手の固定性 | DEFINITION_CONFIRMED | 各点で全候補からminを取るので相手は変化し得る。F02で支配的なD4混合励起群を選ぶ演算ではない。 |
| `phase_gap/τ` と物理励起gapの恒等的対応 | DEFINITION_MISMATCH | 前者は有限τのdressed PF円周gap。F05 normalized分母はbare Hの最小gap。固定のn・支配混合群・巻数kは保存されない。短時間の対応から有限τの特定相手を自動決定できない。 |
| 相手のID、H励起状態対応、kの復元 | INSUFFICIENT_SOURCE | 全位相/ベクトル・相手ID・対応表なし。選択枝のunwrap integerだけでは相手との巻数差や物理励起状態を同定できない。 |
| minimum phase gap = principal-log branch-cut margin | DEFINITION_MISMATCH | pairwise円周距離と、log cutまでの距離は別定義。HF finite-logのreference-relative marginも別項目。 |
| Claudeのτ(Ẽ_n−Ẽ_0)≈2πkとの対応 | INSUFFICIENT_SOURCE | nがbare HかPF branchか、energy liftの選択、kの意味、どの時刻・sectorでの式か原文確認が必要。近接だけでmixing・誤差モデル破綻を確定しない。 |

## S3-3：overlap・選択規則・warning

| 対象 | 判定 | 確認した定義 |
|---|---|---|
| X02 ground / previous overlap | DEFINITION_CONFIRMED | いずれも内積の絶対値二乗の確率。first pointはground最大、次点以後はprevious selected vectorとのoverlap最大。maximum-ground候補との一致を別に記録。 |
| X02 warning | DEFINITION_CONFIRMED | 選択index不一致 OR previous確率<0.9 OR ground確率<0.9 OR 円周gap<1e-6 rad。閾値の所在はX02 `direct_curve` のwarning式（237–242行付近）。F05はこれをinputから継承する。 |
| F05 first warning / reliable prefix | DEFINITION_CONFIRMED | F05の時間順の保存点で最初のwarning。prefixはその前まで。`PHASE_COMPRESSION_RATIO=0.1` は別のcompression分類であり、X02の1e-6 rad gateの代替ではない。 |
| X02縮退projector | NOT_APPLICABLE | このlegacy trackerにprojector方式は実装されず、個別Schur vectorのargmaxを使う。厳密縮退時の一意性を保証する定義ではない。 |
| HF bridgeの選択 | DEFINITION_CONFIRMED | `_f05_point`（572–631行付近）は各点でground overlap最大を選び、previous overlapは診断値。unwrapも各点でexact E0に最も近いliftを使う。|
| X02 = HFの同一継続枝規則 | DEFINITION_MISMATCH | X02はprevious最大・previous effective energyをunwrap参照にする。HFはground最大・E0参照。時間・円周gap・確率の単位が一致しても枝契約は同一ではない。 |
| NH3の選択 | DEFINITION_CONFIRMED | `_schur_point` は各点ground最大、relative principal phase/τでshift。全PF系/unwrap integerを保存するX02方式ではない。 |
| 後続FS-R0.1のprojector規則 | DEFINITION_CONFIRMED | [固定branch contract](https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/b4a7a8204b8d7fa0a2a1bc79bfbdd7cf63177ca1/artifacts/pf_first_study_fs_r01_branch_extension_20261007/branch_contract.md) はgap<1e-8 radでcluster projector、非clusterの一致/previous確率>=0.9等を明記。X02の1e-6 warningとは別契約。今回は未実行。 |
| 後続projector規則をlegacy F05へ適用済みとみなす | DEFINITION_MISMATCH | 原本の選択・thresholdは異なる。legacy値を新契約で再分類・救済していない。 |
| `ground_state_survival_probability` | DEFINITION_CONFIRMED | X02では `abs(ground† U ground)^2`。選択PF固有ベクトルとのground overlap確率とは別。 |
| warning時刻をAR onsetと呼ぶ | DEFINITION_MISMATCH | warningは上記OR。[元report](https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/e820f653a5916f27233ab4674a89d288cf969e37/artifacts/prevalidation_f05_energy_phase_gap_20260922/report.md) も最初のwarningはground-overlap低下を含み、phase-gap絶対gate単独ではないと報告する。ARの原因/発生時刻という認証はない。 |

## S3-4：energy origin・unwrap・対象枝identity

[H-chain準備](https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/e820f653a5916f27233ab4674a89d288cf969e37/review_response/validate_hchain_perturbative_estimator.py)（148–185行付近）はidentity項を除いたgroup和Hと `E_without_constant` を使用する。F01/F02/F03とX02/F05のenergyはこのsourceでの非定数energyであり、核反発等を含む絶対分子全energyと同義ではない（DEFINITION_CONFIRMED）。これを「定数項込みの絶対energy」と読む場合はDEFINITION_MISMATCH。

X02の符号は `U_PF(τ)=exp(+iτH_eff)`。raw phaseはprincipal angle、初点のunwrap参照はE0、以後はprevious effective energyで、`round((reference_energy*τ−raw_phase)/(2π))` を選ぶ。selected energyは `(raw_phase+2π*integer)/τ`。これは離散的なlift選択（DEFINITION_CONFIRMED）であり、実軸全体の解析的・一意な固有枝の証明ではない。個々のintegerやSchur列indexを物理的なstate IDと同一視する場合はDEFINITION_MISMATCH。

global scalar shiftは全位相を共通回転し、pairwise円周gapやoverlapを変えない。一方、絶対位相・整数lift・principal cutやノルム条件の記述はgaugeの指定が必要。HF finite-logのexact-H reference unwrapとfragment midpoint処理、NH3/N2/CO metadataのremoved constantは各sourceの定義を保つ。gaugeを合わせる数値処理は行わない。

F02/F03は同一F01 NPZ hashをinputに持つ（DEFINITION_CONFIRMED）。F05はX02/F02をsystem/PFで結び、名目H2/H4・3PF・同じ準備コードを確認できる。ただしX02で生成したH/basisとF01の保存H/basisの共通byte identityはinput manifestにないため、完全な共通基底の証明はINSUFFICIENT_SOURCE。m5_bestはF03にあるがF05にはなく、F03全PFをF05でも比較済みとする場合はDEFINITION_MISMATCH。

F02の `excitation_gap_hartree` はenergy差。一方、展開 `H_eff=H+τ⁴D4+τ⁶D6+τ⁸D8+…` では、次元を戻すとD4はHa⁵、a8寄与はHa⁹になる。これはsourceの展開式とτ単位の静的な次元確認であり、新しい科学係数の計算ではない。`mixing_contribution_hartree` を有限τ energy shiftの列と読む場合はDEFINITION_MISMATCH。原本の列名や値を変更していない。

## Claude §5.6を科学的に採用する前の不足

原文の式・前提・使用列・時刻を取得し、上記の定義と逐語照合する必要がある（INSUFFICIENT_SOURCE）。とくに、warning時刻を共鳴時刻としたか、最小gapを固定相手のgapに置換したか、overlapを振幅で読んだか、unwrap integerとbranch identityを混ぜたか、F03のt_anaをF05/HFへそのまま移したかを確認する。

命題A/B/M/R/Nは [文献対応](literature_correspondence.md) の仮定・未証明部分を残す。今回の監査はARの否定も実証も行わず、不一致を数値補正して仮説を救済しない。P1実行・数学的詳細レビュー・研究採択は未承認。Mandatory STOP。
