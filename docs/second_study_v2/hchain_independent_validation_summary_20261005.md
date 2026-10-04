# H chain calibration と resource decision の検証結果

文書整理日：2026-10-05。実験系列：2026-10-04。
証拠を確認したsnapshot：`971dc7a9b1b138fbbbb95fc684aa52af657e81b1`。

H2からH8までの固定H-chain検証を、研究目的、共通protocol、system coverage、結果、限定、provenanceの順でまとめる。これは保存済み成果物の文書統合であり、新しい科学計算、再fit、再採点、policy変更を行った結果ではない。

Reference protocolが成立したH2/H4/H5/H6/H7/H8では、すべてcheap-onlyで`r=0.8`を選び、安全にbenchmark B0から約33%のcontinuous budget削減を達成した。ただしfixed cheap `gamma=1.01`も同じdecisionとbudgetで安全だった。したがって、この系列ではadaptive cheapまたはselective spectralの追加利益を確認していない。H3はreference-scale protocolの適用不能として分離する。

## 研究目的と位置付け

第2研究v2の問いは、誤差推定器の点精度だけではなく、追加校正情報が時刻・QPE予算の判断を変える価値と、その情報取得費用である。H-chain検証はgeneral-molecule側から継承したcheap/spectral calibrationとresource-decision structureを、H-chain family内の固定contractで別に評価するcontrolled size-series diagnosticである。

ここでの「independent」はH-chain固有のreference、benchmark、入力、座標を定義した評価を指し、完全未使用のindependent holdoutを意味しない。HF/HClのcandidate contractやdomain-lossをH-chainへ移植した評価でもない。研究質問とこの区別は[元protocol](hchain_independent_validation_20261004/hchain_independent_validation_protocol.json)、[採点contract](hchain_independent_validation_20261004/truth_and_branch_scoring_contract.md)に固定されている。

## 共通の固定protocol

線形、中心配置、原子間隔1 Angstrom、STO-3G、canonical `current_m3`の4次PFを用いた。Even chainsはneutral singlet、odd chainsはcation tripletである。Hamiltonian、population sector、RHF referenceからsingles/doublesを含むCISD state、ordered PF components、係数bytesを入力段階で固定した。古いH6の200次元Z2 groundは今回の400次元sectorのtruthに流用していない。

Odd chainsでは保存されたPySCFの非zero-spin dispatchによりROHF referenceを用いる。H2/H3のCISD subspaceはpopulation sector全体と同じ次元で、そのinput-subspace solveは会計に明記されている。H2のM1 projected solveもprimary 4がsector dimension 4に等しい有限サイズ例であり、外部exact-state入力や一般的な小subspace回収の証明とは扱わない。[Odd-chain protocol](hchain_odd_extension_20261004/protocol.md)と[rank-aware M1規則](hchain_independent_validation_20261004/rank_aware_M1_amendment.json)を参照。

Cheap observableは`delta_C(t) = Im(<exp(+iHt) psi_CISD, U_P(t) psi_CISD>)/t`であり、`arg(echo)/t`やexact-state proxyではない。Truth-free referenceは固定34点`geomspace(0.02,1.8,34)`、5点window、4次からの許容差0.2、R2下限0.999、noise floor `5e-13 Ha`に対し最初の適格windowを選ぶ。そこで得た`alpha_C`から`t_ref = (epsilon_E/(5*alpha_C))**0.25`を定める。H4は同一規則による保存referenceをidentity確認後に再利用した。失敗時にgrid、window、noise floorを救済変更しない。

各適格systemの候補は`r = 0.5, 0.65, 0.8`、`t = r*t_ref`の3点だけで、absolute timeとbinary64 hexを取得前にfreezeした。`epsilon_E = 0.00015936001019904 Ha`、`beta = 1.2`、`eta = 0.10`を固定した。

Benchmarkは`T0 = 0.5*t_ref`、`B0 = 1.01*C_C(T0)`、`C_C(t) = beta*K/[t*(epsilon_E-abs(delta_C(t)))]`である。T0はH-chainのbenchmark anchorであり、物理的なnatural domain capやHFのreproduction controlではない。KはPF一stepのPauli rotation数で、古典matvec数とは異なる。

| Arm | 固定された役割 |
|---|---|
| B1 | 同じcheap情報に対しgamma `1.01,1.02,1.05,1.10`を独立armとして評価。Budgetは`gamma*C_C(t)`で、gammaはproxy-error倍率ではない。 |
| B2 | Cheapだけのno-fit rule。Gamma間のcandidate・eligibility・fallback不一致とproxy符号不安定性を判定し、stableなら1.01、それ以外は1.10を選ぶ。 |
| H1取得判断 | B2と同じcheap policyを起点とし、cheap instabilityまたはB2 fallbackがある場合だけ`q=1`でM1を取得。取得判断にM1やtruthを入れない。 |
| H1採用判断 | `q=0`ならB2と同じaction。`q=1`なら固定したspectral consistency・adoption ruleを適用し、利用不能なM1で小さいwidthへ救済しない。 |
| M1 | 元CISDからexplicit-vector unitary Arnoldiを各座標1 chain。Sectorに応じたprimaryはH2で4、H4/H5/H6/H7/H8で8。Prefix間でPF/H actionsを共有し、`e_use = abs(delta_M)+w_M`を予算に使用。 |
| Always M1 | H1のconditional取得と区別したcomparator。H1 freeze後に`q=0`systemのM1を補完する。 |

各armは適格候補の最小frozen budgetを選び、適格候補がなければ`(T0,B0)`へfallbackする。M1のprimary rank不足、数値・branch gate不合格、positive QPE allowance不足は元のabstentionとして残す。候補適格性、tie-break、H1 consistencyの詳細は[policy contract](hchain_independent_validation_20261004/B1_B2_M1_H1_policy_contract.json)、[rank-aware M1規則](hchain_independent_validation_20261004/rank_aware_M1_amendment.json)を参照。

Truth barrierの順序は、入力/reference/座標freeze → cheap取得 → B0/B1/B2/q commit → q=1 M1 → H1 commit → q=0 comparator補完 → prediction commitとbyte gate → same-H ground freeze → direct truth/gap freeze → immutable scoringである。Full PF、exact ground、direct truth、truth gapはpredictorへ渡していない。

Scorerは同じHamiltonian/sector/PF/時刻のPFを構築し、complex Schurで最初の固定時刻のground-overlap枝を選び、残りは直前枝とのcontinuationを行った。追加の小時刻anchorはない。保存したsigned shiftとabsolute errorを区別し、安全性は`abs(delta_direct)+beta*K/(t*B_frozen) <= epsilon_E`、targetはさらに`t>T0`かつ`B_frozen<=0.90*B0`で判定した。Truthからdecision、budget、widthを修正していない。

正式resource metricは`continuous_rotation_cost_proxy`であり、離散QPE query countでも、量子・古典のend-to-end総費用でもない。[Truth method](hchain_input_reference_preparation_20261004/truth_scoring_method.json)と[採点contract](hchain_independent_validation_20261004/truth_and_branch_scoring_contract.md)が詳細の根拠である。

## H2からH8のsystem coverage

表の数値は[H2–H7保存統合表](../../artifacts/hchain_h3_h5_h7_extension_20261004/h2_h7_integrated_summary.csv)、[H2–H8保存統合表](../../artifacts/hchain_h8_memory_safe_extension_20261004/h2_h8_integrated_summary.csv)、[H8 report](../../artifacts/hchain_h8_memory_safe_extension_20261004/report.md)に基づく。表示のB/B0のみ丸め、予算や判定は変更していない。

| System | Reference | Sector/CISD | t_ref | q | Selected r | B2/H1 B/B0 | Safe/target | Fixed gamma 1.01 safe | Always M1 |
|---|---|---|---:|---:|---:|---:|---|---|---|
| H2 | 適用可 | 4/4 | 1.8470023167315772 | 0 | 0.8 | 0.6705717434 | PASS/PASS | PASS | B0 fallback |
| H3 | 適用不能 | 3/3 | 未取得 | — | — | — | 未採点 | 未採点 | 未実行 |
| H4 | 適用可 保存reference再利用 | 36/27 | 1.237648718781152 | 0 | 0.8 | 0.6716956053 | PASS/PASS | PASS | B0 fallback |
| H5 | 適用可 | 50/38 | 1.4108552969899706 | 0 | 0.8 | 0.6699509060 | PASS/PASS | PASS | B0 fallback |
| H6 | 適用可 | 400/118 | 1.0864029909482193 | 0 | 0.8 | 0.6703472188 | PASS/PASS | PASS | B0 fallback |
| H7 | 適用可 | 735/171 | 1.1581877773296543 | 0 | 0.8 | 0.6712914474 | PASS/PASS | PASS | B0 fallback |
| H8 | 適用可 | 4900/361 | 0.9909332903963247 | 0 | 0.8 | 0.6690596263 | PASS/PASS | PASS | B0 fallback |

分母はattempted 7系、reference適格・採点済み6系、reference適用不能1系である。H3の欠損は0ではなく未採点であり、成功例の分母に入れない。各適格systemの3座標はsystem内診断で、18 independent samplesではない。Fixed gamma 1.01は全6系でB2/H1と同じselected timeとbudgetだった。

## Cheap-only decisionと資源結果

全6適格systemでB2/H1はbenchmark B0から約33%のcontinuous budget削減を安全に達成した。全系のqが0なので、今回実現したH1はB2そのものであり、conditional spectral取得は不要と判定された。

ただしfixed cheap gamma 1.01でも同じ結果が得られた。保存したfour-gamma frontierでは全armが全適格systemでsafeだった。従って確認されたのは、固定したH-chain条件でのcheap-only decisionの有用性であり、B2のadaptive効果やH1のselective spectral追加価値ではない。B0とalways-M1のB0 fallbackも安全だが、10%削減targetは達成していない。

この削減はbenchmark anchorとの比較である。HFで同定したnatural domain-lossの回復率、未知条件で達成可能な最大削減率、discrete query-count削減、量子・古典総費用の削減としては解釈しない。

## M1の点精度とwidthと採用判断

各reportは`E_C = abs(delta_C-delta_direct)`、`E_M = abs(delta_M-delta_direct)`、経験的coverage `E_M<=w_M`、physical branch診断 `E_M<g_phase/(2*t)`を別に保存している。絶対位相とground-relative位相のunwrap整数は直接比較していない。Abstainした座標の点診断を、採用されたresource actionと混同しない。

| System | Physical branch診断 | 経験的width coverage | 元のpolicy abstention | M1がcheapより点誤差を改善した座標 |
|---|---|---|---|---|
| H2 | 3/3一致 | 3/3 | 2/3 primary rank不足 | 3/3 |
| H3 | 未実行 | 未実行 | 未実行 | 未実行 |
| H4 | 3/3一致 | 3/3 | 0/3 | 3/3 |
| H5 | 3/3一致 | 3/3 | 1/3 allowance不足 | 2/3 |
| H6 | 3/3一致 | 3/3 | 3/3 allowance不足 | 3/3 |
| H7 | 3/3一致 | 3/3 | 3/3 allowance不足 | 0/3 |
| H8 | 3/3一致 | 3/3 | 3/3 allowance不足 | 0/3 |

点精度改善のcountは既存H2–H7統合表とH8 reportの記録に従う。個々の値は[H2/H4/H6座標採点](../../artifacts/hchain_truth_scoring_20261004/result/coordinate_scoring.csv)、[H5/H7座標採点](../../artifacts/hchain_h3_h5_h7_extension_20261004/coordinate_scoring.csv)、[H8座標採点](../../artifacts/hchain_h8_memory_safe_extension_20261004/coordinate_scoring.csv)へ追跡できる。

M1が点精度を改善した場合でも、固定widthやrank/eligibilityの規則を経たalways-M1 decisionは全6系でB0 fallbackだった。一方、H5のr=0.8、H7/H8の全点ではM1の点誤差自体もcheapより大きい。系列全体を「点精度は常に高いがwidthだけが問題」とはまとめない。

経験的coverageはcertificateではなく、H Ritz referenceもcertified ground stateではない。`g_phase`、`g_E`、unit-circle chord gapは別fieldであり、未取得の`g_rho_others`をtarget gapで代用して新widthを作っていない。

## H3のreference適用不能

H3の正式な個別statusは`H3_reference_scale_unavailable_under_frozen_protocol`である。固定34点grid、noise floor、次数・R2・window規則で適格windowがなく、t_refを定義できなかった。Noise floorやfit規則を変更せず、代替referenceによる救済もしていない。

H3 inputとreference acquisitionは行ったが、candidate、B0、M1、same-H ground truth、direct truthは生成していない。この結果はfrozen reference-scale protocolのapplicability failureであり、未実行のM1やresource decisionの性能失敗ではない。詳細は[H3/H5/H7 report](../../artifacts/hchain_h3_h5_h7_extension_20261004/report.md)に保存されている。

## H8のmemory-safe拡張とsoftware caveat

H8はscience contractを変更せず、group処理のmemory lifetimeを短縮する実装で実行した。保存H7の1座標で旧実装とのPF vector、cheap、M1点推定・width・residualの差が0であることを先に確認し、H8入力とresource gateをfreezeしてから進めた。[実装差分設計](hchain_h8_memory_safe_20261004/memory_design.md)、[同値性記録](hchain_h8_memory_safe_20261004/implementation_equivalence.json)が根拠である。

H8はq=0、B2/H1 budget比0.669059626334297、約33.0940%削減でsafe/targetを満たした。Fixed gamma 1.01も同じ結果だった。M1は3/3 abstainで全点の点誤差もcheapより大きい。Peak RSSは2,507,060 KiB、約2.39 GiBで4 GiB以内、CPU process/BLAS threadは1/1、GPU query/allocation/kernel/CuPy importは0だった。

保存済みfocused test gateは6回すべて各118 passed、fail/skip 0だった。一方、repository-wide legacy suiteはgreenではない。未除外のfull runはoptional python-flint不足でcollection error、flint依存moduleだけを除いた診断partitionは484 passed、7 failed、1 skippedだった。7件は旧H2/H4/H6 private runtime依存2件とhistorical commit内のartifact path不在5件で、legacy sources/testsはbaseから変更されていない。

これを「full suite合格」や「H8変更による7 regression failures」とは記さない。科学stageのgate通過とrepository全体のrelease readinessを分離し、後者は未解決として残す。この文書化でpackage追加、runtime移送、historical artifact修復、test再実行はしていない。[H8 test gate summary](../../artifacts/hchain_h8_memory_safe_extension_20261004/test_gate_summary.json)と[H8 report](../../artifacts/hchain_h8_memory_safe_extension_20261004/report.md)を参照。

## 研究上の解釈と限界

保存結果が支持する範囲は「この固定H-chain familyでは、cheap-onlyの時刻・budget decisionがbenchmarkより低予算で安全だった」である。Selective acquisitionのpositive incremental valueは未確認で、q=1 conditional H1 pathの実測性能はない。この結果だけから研究routeの自動継続・閉鎖を決めず、次の方針はgovernance reviewとして扱う。

- 18座標を18 independent samplesと数えず、H3をscored systemに含めない。
- Oddはcation triplet、evenはneutral singletなので、純粋なparity効果を分離した実験ではない。
- 完全未使用holdout、general-molecule generalization、scaling exponentや統計的有意性を主張しない。
- Universal cheap sufficiency、B2/H1の一般的policy validation、厳密なwidth/branch/ground certificateを主張しない。
- 古典wall time、memory、PF/H actions、shared/cache費用は量子budgetと別会計。異なる単位を合算してend-to-end savingを作らない。Warm shared-path H1 timingはcold standalone always-M1測定ではない。
- q=0 comparator補完のM1費用はH1費用へ入れない。保存M1が全座標に存在することと、H1がその情報へアクセスしたことは区別する。

## 正式statusと証拠の追跡

以下のoriginal statusは変更していない。

| 系列 | 正式status | Result publication origin commit |
|---|---|---|
| H2/H4/H6 | `hchain_independent_validation_complete_review_required` | `5a9226a94fad0b578df1a53edd1a29e3571ad8c3` |
| H3/H5/H7 | `hchain_h3_h5_h7_extension_complete_review_required` | `ff949e6aa942475f20f0623bcffb617e1e750f24` |
| H8 | `hchain_h8_extension_complete_review_required` | `cc3c49dac8630f6a18a3a6d6edc21b0c18bd6fb6` |

この文書が内容を確認したsnapshotは全系列について`971dc7a9b1b138fbbbb95fc684aa52af657e81b1`であり、origin/result publication commitとは別である。H3/H5/H7 provenance先端は`50b73a363fa581f8534c399f087b35cb38a4cb70`、H8 provenance先端は上記971dc7aである。H3のreference結果そのもののoriginは`6c063dd2578109b204c0a1346581b2016c724957`で、後のpublicationと統合しない。

| 系列 | Prediction freeze | Truth freeze | 採点結果 |
|---|---|---|---|
| H2/H4/H6 | `858265dacd` | `ae585e2c1a` | `5a9226a94f` result publication |
| H3/H5/H7 | `747868eb35` | `db504bf8b9` | `2065a4b2d5` scoring freeze |
| H8 | `b0a67843d3` | `944291272c` | `12052e9ec3` scoring freeze |

上表の省略commitの完全identity、ground freeze、hash、元technical stopとcontinuationの履歴は次のauthorityへ追跡できる。

- [H2/H4/H6 result report](../../artifacts/hchain_truth_scoring_20261004/result/report.md)、[COMPLETE](../../artifacts/hchain_truth_scoring_20261004/result/COMPLETE.json)、[execution audit](../../artifacts/hchain_truth_scoring_20261004/result/execution_audit.json)。
- [H3/H5/H7 report](../../artifacts/hchain_h3_h5_h7_extension_20261004/report.md)、[publication provenance](../../artifacts/hchain_h3_h5_h7_extension_20261004/publication_provenance.json)、[integrated source registry](../../artifacts/hchain_h3_h5_h7_extension_20261004/integrated_source_registry.json)、[COMPLETE](../../artifacts/hchain_h3_h5_h7_extension_20261004/COMPLETE.json)。
- [H8 report](../../artifacts/hchain_h8_memory_safe_extension_20261004/report.md)、[publication source registry](../../artifacts/hchain_h8_memory_safe_extension_20261004/publication_source_registry.json)、[publication provenance](hchain_h8_memory_safe_20261004/publication_provenance.json)、[COMPLETE](../../artifacts/hchain_h8_memory_safe_extension_20261004/COMPLETE.json)。
- [H2–H7統合表](../../artifacts/hchain_h3_h5_h7_extension_20261004/h2_h7_integrated_summary.csv)はreference・gamma・点精度比較の補完元、[H2–H8統合表](../../artifacts/hchain_h8_memory_safe_extension_20261004/h2_h8_integrated_summary.csv)は全7系の最新保存decision coverageである。

古いprotocolの`blocked`、H8 preflightの`H8_extension_contract_blocked`、作成時の`no push`記録は、その時点の履歴として保存されている。現在の完了範囲は上記3つのCOMPLETE/resultで確認する。H8 remote branchの公開済み先端971dc7aは2026-10-05のread-only監査で確認した事実であり、保存publication provenanceの`push_performed=false`を書き換えたものではない。

この総括は新しいscientific taxonomyや実行authorizationではない。次は研究方針レビューで停止する。追加H-chain・分子・PF・時刻、fit、threshold/width/rank/q変更、C1/D2-B、runtime移送、科学計算再実行には別承認が必要である。
