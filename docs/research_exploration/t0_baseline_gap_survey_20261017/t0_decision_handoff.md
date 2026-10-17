# T0判断用handoff：baselineと保証gap

2026-10-17 JST。Repository：`HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae`。
branch：`qc-t0-baseline-gap-survey-20261017`。
固定起点：[`a80596c29e0eaaf7483f8981ed0e61c918335054`](https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/commit/a80596c29e0eaaf7483f8981ed0e61c918335054)。
この文書自身を含む公開commitのidentityは、循環参照を避けてGit履歴と最終チャットで報告する。

**結果：保証問題R1を1件だけ条件付き保持。新アルゴリズム、新操作原理、総資源優位、正式採択はいずれも0件。**
R1は「外挿PFの相殺次数を、低energyの有限step保証でも保てるか」という既知open questionの限定した数学的検証課題。
係数・演算子を新しく生成するアルゴリズムを作った成果ではない。

読む順序：本書 → [task](t0_task_definition.md) → [baseline cards](t0_baseline_comparison.md) →
[総費用](t0_total_cost_decomposition.md) → [gap台帳](t0_gap_analysis.md) →
[R1の目標命題・反証条件](t0_research_problem_candidates.md) →
[SOURCE](source_registry.json)／[静的監査](static_audit.json)／[provenance](provenance.json)。

## 1. 最終質問への回答

### Q1：同一条件で最も強いbaselineは何か

普遍的な一法は未確定。小overlap・gap未認証・測定型accessでは、標準PF＋Lin–Tong CDFを単純対照とし、
2026年のcommutator-scaling外挿PF＋CDFも強い既知対照に含める。
大overlap・long-tail分割では部分乱択RTE＋RPEが有力だが、RMS／confidenceとoverlap条件を揃える必要がある。
低energy情報を使うなら、通常高次PFの既知低energy保証とsector上界も全対照へ与える。

既存PFの連続rotation proxy、PRのP=0信号RZ価格、SPRINTのXAS Toffoli推定、QET-Uの呼出し数は同一task／価格ではない。
固定分子・全準備費・全protocolの共通データがない以上、新しい総費用順位は作れない。

### Q2：絶対E0までの何が制約するか

単一shot価格ではなく、\(\sum_jN_j(P_j+C_j)\)、controlled simulationの全時刻・精度、overlap／信号半径、
全roundのbranch・confidence、モデル／係数誤差、情報取得費が制約する。
instanceを固定していないため、これらの実測支配順位は未取得。
第一・第二研究の保存安全性やPRのvisibility改善から、全E0成功保証・総費用改善は導けない。

### Q3：文献に根拠のあるgapは残るか

**残る。ただし範囲付きである。**
[2026年8月の一次文献L08 §1.7](https://arxiv.org/html/2608.13862v1) は、通常PFの低energy／average-case改善が
外挿PFにも引き継がれるかを明示的に未解決とする。今回は低energyの側だけを扱う。
通常PFの低energy改善そのものは [L09](https://arxiv.org/pdf/2504.20746v1) の到達点であり、新発見にしない。

[L07](https://arxiv.org/pdf/2304.09827v2) にも浅いGSEE認証費用・runtime下界の明示的な問題があるが、
QET-U／block-encoding構成を今回の中心へ移さない。
小overlap改善、乱択signal→energy接続、compact BCHは既知の強い構成があり、一般的な未解決問題とは認定しない。

### Q4：何を数学的研究問題として残したか

R1-Pは、固定した既知のRichardson combinationに対して、低energy射影後も \(r^{-4}\) の相殺と
cutoff依存の有限r剰余を両立できるか、という反証可能なnorm上界。
必要なのは中間のhigh-energy leakageを払うrestricted係数・積・剰余の補題であり、
全normに低energyを代入しただけの主張ではない。

**独立性は未確立**。L08/L09等の既存証明から直ちに従うなら新課題から外す。
成立しても、既知作用の新しい保証にとどまり、新操作原理ではない。
通常4次PFより高価、PSD shift後のcutoffがextensive、state／tail証拠が高価なら、E0資源候補としては保留／棄却する。

### Q5：次に何を選び、最初に何を確かめるか

第一の判断は、**新操作の発見だけでなく、既知作用への新保証を検証する小課題R1を次段階に選ぶか**。
選ぶ場合の最初の作業は、L08の外挿series／sector証明とL09のlowenergy証明との直接還元確認。
続いて、別契約の紙上範囲で4 modes・2 electronsの非可換layersを用い、相殺・残る高次項・leakageを確認し、
同じ情報を使う通常4次PF／sector対照が既に十分なら打ち切る。
この最小検証はまだ実施していない。数値・科学用記号計算・compileの承認を含まない。

## 2. 次の担当と承認境界

| 担当 | 判断・作業 | 現時点の権限 |
| --- | --- | --- |
| GPT／ユーザー | R1を限定紙上検証へ進めるか、価値軸を新保証まで含めるか判断 | 今回のhandoffを読むための判断。採択を代行しない |
| ユーザー | 進める場合、対象class、比較baseline、紙上計算の範囲と停止点を明示承認 | 追加作業は未承認 |
| Codex | 承認された場合のみ、既知証明への還元確認→最小反例／費用gateを実施 | 今回は提案のみ。科学計算・実装は別承認 |

推薦はR1の**限定された紙上判別**だけで、一般Lへの拡張、別ansatz、別gap調査、新アルゴリズムの構成探索を連続開始しない。
R1を選ばない場合、本調査後の追加作業は不要。新アルゴリズム研究全体の不可能性・終了は宣言しない。

## 3. 実際に確認したことと未確認事項

確認したのは固定資料の内容・scope、21件のrepository SOURCE identity、9件の版固定一次論文、
既知の費用式・保証の入力条件、S1/S5の不足欄である。読取り範囲はregistryに個別記載し、歴史上の全sourceを再読したとはしない。
検索は2026-10-17の限定調査。arXiv未出版稿も含み、網羅的なpriority／最適性の証明ではない。
公開実装は本repoのcost/PF sourceを静的に確認したのみで、import・実行していない。

未確認：R1-Pの正しさ、既知証明への完全還元、新規性、非自明な電子classでの準備／eta／tail証拠、
固定bitの定数、FT価格、全E0資源差。小例や数式を科学プログラムで検証した結果はない。

保全：J1 `PAUSED_PENDING_NEW_MECHANISM`、Q1 `PAUSED_PENDING_NEW_LEVEL_INSERTION_RULE`、
第一・第二研究、PR Track A/B、P1～P8、T1-D、SOS-PFとA2、SOURCE・raw・grant・科学契約・承認・STOPは不変。
今回の新資料だけを独立branchへ公開する。過去の「push未実施」等の履歴は更新しない。

## 4. 公開照合と停止

今回の成果物は指定6 Markdown、source registry、static audit、provenanceの9件。
provenanceは自身をmanifestから除外し、将来の公開commit／自己hashを埋め込まない。
normal push後、remote SHA、独立した空bare repoへのfetch、Git blob・bytes・SHA-256、commit固定rawを照合する。
その観測結果と40文字commitは最終チャットで報告し、凍結済みの入力記録へ遡及書込みしない。

**Mandatory STOP：公開・照合完了後に停止。正式採択、追加探索、詳細科学レビュー、新規科学計算・実装は自動開始しない。**
