# 第2研究：主解析完了後の研究方針・主張・着地点

作成日：2026-10-05  
基準repository：`HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae`  
基準commit：`bfe715fc1c04325535a3c4d63ea4584e691dc322`  
対象branch：`pf-second-study-v2-budget-safety-mechanism-20261005`

本書は、完了済みbudget-safety mechanism解析を受けた研究方針の提案である。旧研究方針・実験protocol・prediction・truth・formal decisionを変更するものではない。保存結果、そこからの代数的帰結、研究上の判断、外部文献との比較を区別する。新しい分子計算、PF/H作用、Arnoldi、truth取得、再fit、再採点は実行していない。本書をリポジトリへcommit/pushしたことも意味しない。

## 1. 結論

Direction Cを維持する。ただし「校正情報の価値は条件依存だった」という事例整理でも、「safeの不等式を変形した」という代数だけの研究でもなく、次を主題にする。

> 有限時間PF校正に基づくQPE予算の信頼性と、追加校正による資源削減の余地を、凍結済み判断の数値検証から明らかにする。

中心成果は、(1) cheap推定の過小評価と予算余裕による失敗・成功の識別、(2) 強いcheap対照に対する完全情報の改善余地と実M1の幅・採用制約の分離、(3) PF/H-referenceの誤差相殺を含む点精度の解釈、の三つとする。

主解析は既に完了している。次は主解析の再実行や追加pilotではなく、contribution・図表・技術的説明の統合へ進む。新しいgateやq=1成功例を完成条件にしない。

## 2. RQと第一研究との境界

### Primary RQ

> 固定した有限時間PF-QPEの問題設定において、近似校正から凍結した予算の安全性と資源効率は、どの誤差要因・安全余裕・候補時刻に左右され、追加spectral校正は何を改善し、何を改善できなかったか。

「どんな未知分子でもsafeと認定できる条件を得た」という問いへの回答ではない。対象は既存の固定問題設定における数値的信頼性評価である。

### Secondary RQ

1. 符号付き点誤差、誤差絶対値の過小評価、candidate/gamma/signの内部安定性は、凍結予算のsafe/unsafeとどのように異なるか。
2. 同じ時刻または固定候補集合で、完全なPF誤差を無償で知った場合の最小安全予算はどこにあり、実M1のpoint・width・rank・eligibilityはそこからどれだけ隔たるか。
3. PF固有値とHamiltonian参照値の差を推定する場合、両方の誤差の相殺・非相殺は、shift推定精度の解釈をどう変えるか。

情報取得費用は、測定範囲を明示した付随評価として残す。q=1 combined costやcold standalone費用が未測定であるため、「量子・古典総費用で割に合う」を主RQの達成済み部分にしない。[R1–R3]

第一研究は校正、予算余裕、時刻域、PF選択等の損失を診断した研究として保持する。第二研究はその後段で、有限時間校正を予算判断へ変換した際の信頼性と改善余地を評価する。第一研究への追加計算、旧結果の再命名、二重の独立標本扱いは行わない。

## 3. 保存結果から採用する中核claim

### C1：内部安定性・符号付き精度は、予算安全性の代用にならない

保存量を

\[
e=|\delta_{\rm direct}|,\quad c=|\widehat\delta_C|,\quad a=\beta K
\]

と置く。現行の安全性判定と固定cheap予算は

\[
e+\frac{a}{tB}\le\epsilon_E,
\qquad
B_\gamma=\gamma\frac{a}{t(\epsilon_E-c)}.
\]

これより

\[
e-c\le M_\gamma,
\qquad
M_\gamma=\left(1-\frac1\gamma\right)(\epsilon_E-c)
\]

となる。基本評価量は

\[
S_B=\epsilon_E-e-\frac{a}{tB}
\]

という安全性slackである。gamma=1ではM=0なので比率を作らずslackを用いる。e-c<0は過大評価であり、絶対値を取って危険な過小評価へ変換しない。c>=epsilonならcheap式は不適格、e>=epsilonなら同じuncorrected taskの有限安全予算は存在しない。[R2]

この同値変形は定義したモデル内の恒等的な整理で、新しいPF誤差boundではない。また、64件の保存判定と一致したことは算術・実装照合であり、64件の独立予測成功ではない。[R7]

実証上の内容は、同じcheap stability gateが同じq=0を返しても、HF equilibriumとstretchで安全性が異なったことである。

| 条件・選択点 | 過小評価e-c [Ha] | M_1.01 [Ha] | slack [Ha] | 解釈 |
|---|---:|---:|---:|---|
| HF equilibrium, 1.6T0 | 1.28300068e-5 | 1.46426427e-6 | -1.13657425e-5 | margin超過、unsafe |
| HF stretch150, 1.6T0 | 5.63018839e-7 | 1.50672428e-6 | +9.43705442e-7 | margin内、safe |

stretchはcheapとtruthの符号が逆で、signed point errorは約1.49247e-5 Haだがsafeだった。H-chainの選択点ではH2/H5の小さい過小評価をmarginが吸収し、H4/H6/H7/H8はcheap magnitudeが過大評価だった。[R1]

同じeligible集合上で費用すべてを共通の正のgammaで掛けてもargminは変わらない。このためgamma間の選択不変性は、独立した推定法の一致とは違う。eligible集合・fallbackが変わる場合は別だが、選択が不変だったことだけから未観測のbiasを上界化することはできない。[R2]

この結果は現B2/H1 gateに対する具体的な反例である。すべてのcheap diagnosticの不可能性定理ではない。G2は既知HFデータを使うpost-hoc replayであり、新しいholdoutではない。

### C2：追加情報の価値は、cheap対照が残す改善余地と分けて評価する

同時刻の完全truthによる最小予算を

\[
B_{\rm truth}(t)=\frac{a}{t(\epsilon_E-e(t))}
\]

とする。これは固定モデル内のcost-free oracleであり、取得可能な校正法ではない。

安全な比較予算B_Cに対する残余headroomは

\[
h(t;B_C)=1-\frac{B_{\rm truth}(t)}{B_C}.
\]

同一t・task・cost modelを保つ限り、これを越えて安全予算を削減することはできない。この限定を外し、時刻変更、新PF、補正付きQPE、異なる費用モデルまで否定してはならない。

既存tableの同時刻比較は次の通り。[R4]

| 対象 | 参照予算 | 有効比較数 | 完全truthへの残余削減率 |
|---|---|---:|---:|
| HF | 同時刻fixed cheap gamma=1.01 | 5/6 | 約0.1506–2.2428% |
| H-chain | 同時刻fixed cheap gamma=1.01 | 18/18 | 約0.9766–2.7290% |
| HCl | main同時刻gamma=1.02 | 6/6 | 約0.3280–2.2865% |

HF equilibriumの1.6T0・gamma1.01はunsafeなので、safeな対照としての改善率は未定義のままにする。29比較は独立29標本ではない。

したがって、この名指しした安全な同時刻対照に対して、10%削減は完全情報でも届かない。これは方法非依存の固定モデル内oracle比較であり、「M1のwidthをゼロにしても10%窓が負」という固定pointの比較より広い。ただしgamma1.10対照、別時刻、候補域拡大を一緒に含めた一般的no-benefit定理ではない。

H-chainでは保存3候補のoracle最良も全6系でr=0.8だった。現在のfixed1.01/B2/H1は同じ候補を選んでおり、選択済み予算からnative-grid oracleまでの残りは約0.9766–2.7290%である。[R4,R5]

この結果は「M1が不利だった」より強い限定的解釈を可能にする。対象H-chainの固定候補では、cheap判断が既にoracleに近く、情報を高精度化して回復できる余地自体が小さい。ただしr=0.8は候補端であり、より長い時刻が有利かどうかは示していない。

M1の幅とpointについては

\[
B_M(t)=\frac{a}{t(\epsilon_E-|\widehat\delta_M|-w_M)}
\]

を使い、同じ比較予算をetaだけ削減できるwidth条件

\[
w_M\le w_{\rm win}
=\epsilon_E-|\widehat\delta_M|-\frac{a}{t(1-\eta)B_C}
\]

を保つ。[R2] w_win<0は、その固定M1 pointを保持してwidthだけを非負範囲で縮めても目標へ届かないという意味である。width coverageは経験的であり、必要なrankやbranch gateを無効化しない。

現結果は、HF6点で点精度改善6、abstain0、H-chain18点で改善11、abstain12、HCl6点で改善6、abstain1である。[R1] 改善余地、point、width、rank、eligibility、fallbackを別々に示す。

### C3：shift推定精度と、PF固有値回収精度は同じではない

同じH、sector、origin、physical branchを確認できたH-chain18点では

\[
\widehat\delta_M-\delta
=(\widehat E_{\rm PF}-E_{\rm PF})-(\widehat E_H-E_0)
=A-R
\]

を評価できた。[R6]

| 選択点r=0.8 | PF側誤差A [Ha] | H-reference誤差R [Ha] | shift誤差A-R [Ha] |
|---|---:|---:|---:|
| H4 | 6.67348e-11 | 3.80583e-9 | -3.73909e-9 |
| H5 | 1.62667e-10 | 4.57483e-8 | -4.55856e-8 |
| H6 | 2.42817e-6 | 3.36122e-6 | -9.33044e-7 |
| H7 | 5.12632e-6 | 8.53820e-6 | -3.41188e-6 |
| H8 | 2.79934e-5 | 6.39472e-5 | -3.59538e-5 |

H4/H5ではreference側の誤差が大きく、H6/H7/H8では正の誤差同士が部分的に相殺している。差に共通誤差が相殺されること自体は新原理ではない。貢献は、本比較のM1点精度を実際に分解し、PF回収・reference・shiftを混同しない形で解釈したことにある。

H2の機械丸め域を物理現象としない。HF/HClの12点は限定source registry内ではidentity条件を閉じられず、分解を未評価のままにする。H-reference基準にtruth shiftを足した量を独立PF truthとして循環利用しない。state qualityやrankが原因という因果的主張も行わない。

## 4. H-chain約33%の位置付け

leading model c=alpha*t^4とreference定義の下では、r=.5から.8の費用比は

\[
\frac{.5(1-.5^4/5)}{.8(1-.8^4/5)}=0.6722589534681074
\]

で、32.77410465%削減になる。保存結果は32.8304–33.0940%、差は約0.0563–0.3199 percentage pointsである。[R1]

この結果は補助的な解釈統制として重要だが、「新adaptive方式が33%削減した」という中心貢献にはしない。大部分の比率が時刻・leading-model設計に近いことと、その凍結予算がtruth上で安全だったことを分離する。

H-chainは7系を試行し6系がreference適格、H3は適用不能で未採点。evenはneutral singlet、oddはcation tripletであり純粋なparity試験ではない。H2ではCISD/有限次元の飽和がある。6系すべてq=0で、fixed gamma1.01とB2/H1が同じである。[R1,R3]

## 5. 研究の着地点

### 推奨

限定された数値方法論・信頼性研究として、独立論文を狙う。主題は新しいselectorやKrylov法の提案ではなく、有限時間の推定値を凍結予算へ変換する際の誤差・保守性・改善余地の分析である。

仮題：

> 有限時間積公式校正の信頼性と資源削減余地：QPE予算の数値的評価

英題候補：

> Reliability and Resource Headroom of Finite-Time Trotter-Error Calibration for Quantum Phase Estimation

"safe"は数値truthと指定連続費用モデル内の判定と定義する。厳密certificate、実機成功確率、離散回路総費用、未知条件への安全性保証は含めない。

### 論文の概要案

近似状態を用いた有限時間Trotter誤差校正について、固定した四次積公式とQPE連続費用モデルの下で、凍結予算の安全性と資源削減余地を調べる。10条件30座標の保存結果を用い、誤差過小評価と予算余裕、完全情報による候補内最小予算、spectral推定のpoint・width・採用制約を分離した。対象H-chainでは固定cheap方式が安全な判断を与えた一方、HFでは候補・eligibility・符号が安定したcheap gateにfalse negativeがあった。安全な同時刻cheap対照の多くはcost-free oracleに近く、追加精度の量子予算利益は限定された。またH-chainのPF/H-reference誤差分解から、shiftの高精度をPF側回収の高精度と同一視できない例を確認した。これらは固定問題設定における数値的限界であり、普遍的な安全policyやspectral不要性を示すものではない。

### 完成見通しの評価

修士研究の独立した発展章として、既存結果は十分に一貫した内容を持つ。独立査読論文としても候補になるが、新規性・掲載可能性を保証しない。数式の同値変形、弱い自作gateの失敗、固定rankの比較だけを押し出すと弱い。C1–C3の限定的だが具体的な観測結果を組み合わせ、最も近い先行研究との違いを示す必要がある。

第一研究を自動的に統合し直すことは推奨しない。原稿化後に貢献の独立性が弱いと判断された場合だけ、論文としての切り分けを別途検討する。第一研究への新規計算は不要。

## 6. 新規性の外部照合

2026-10-05時点の一次資料を検索・確認した。以下は対象を絞った比較であり、網羅的な不存在証明ではない。外部論文の手法を本repositoryで再現・比較実行したわけではない。

### 6.1 Mehendaleほか：最も近いclassical-estimator比較

[L1]のarXiv v3だけでなく、2025年10月のDigital Discovery出版版を確認した。近似CISDからの摂動推定、Hamiltonian partitioning、T-gate評価を扱い、高相関でも資源順位が異なると明記している。出版版にはN2伸長に対する状態品質の検討もある。

従って、近似状態を使う誤差推定、精度と資源の不一致、状態品質依存、Trotter誤差とQPE誤差配分一般を新規性に数えない。

本研究の差分候補は、有限時間に固定した予算をtruthで採点し、過小評価の片側性、固定cheap対照、oracle headroom、width/rank/採用、reference誤差を併せて評価する点である。主張はこの具体的比較に限定する。

### 6.2 Simon–Love：今回追加して照合すべき重要文献

[L2]はphase-error測定を量子回路で行い、QPEの誤差予算・最適時刻・資源見積りと結び付ける研究である。Appendix BはTrotter誤差とQPE誤差の総制約を用いた資源最適化、Appendix Dはphase proxyの近似性と非上界性、非固有状態の扱いを論じる。

「校正のための情報取得を将来QPEの資源削減へ使う」という着想自体は新規ではない。本研究は量子誤差測定アルゴリズムを提案せず、比較基準を保守的commutator boundからsafe fixed-cheap対照まで引き上げた場合に残る改善余地と、実際の凍結判断の失敗・保守性を分析する。

今回の結果でSimon–Love法が失敗するとは言わない。同法を同一条件で実装した比較ではない。

### 6.3 Maxwellほか：実用規模・BCH推定との境界

[L3]は2026年のpractical Trotter error estimation、compact BCH、sampling、tensor-network等への適用を扱う。高精度・低古典費用の誤差推定それ自体は既に明確な研究分野である。

本研究は同法より精度・規模・古典計算量で優れると主張しない。有限時間の凍結予算へ推定を投入した後の信頼性と改善余地を対象にする。

### 6.4 Yi–Crosson / Hejaziほか

[L4,L5]はspectral/eigenvalue/QPE特化のPF解析を扱う。固有値誤差が演算子norm誤差と異なること、gapやstateの役割、高次PFのtask特化は新規でない。本研究は新しい全次数定理やgap certificateを主張しない。

### 6.5 phase2、orbital transformations、tapered QPE

[L6]は保守的boundと経験的誤差の資源差を扱う。[L7]はorbital変換と単純descriptorの限界を検討する。[L8]はTrotter誤差、位相register離散化、初期overlapなどを回路レベルで比較する。

本研究はbound-versus-observation一般、簡単なdescriptorの不完全性一般、回路QPEの実用成功確率を初めて扱う研究ではない。[L8]はabstract範囲の確認で、全文の詳細評価を行ったとはしない。

### 6.6 新規性の最終判断

- 単独では弱い：slackの代数、accuracy≠utility、Arnoldi、freeze手順、自作gate1件の失敗、H-chain約33%。
- 現時点で採用する差分候補：固定有限時間PF-QPEの安全なcheap対照に対する、実予算失敗・oracle近接・幅/採用・reference誤差を結び付けた数値的信頼性評価。
- 未確立：汎用的なregime識別器、未知系の必要margin、calibrationの多項式スケーリング、net cost advantage、厳密certificate。

確認した近接資料の範囲で、この具体的な組合せと同一の実証は確認していない。しかし、それは世界初の証明でも掲載可能性の保証でもない。投稿用のcontributionは対象・metric・evidence classを明記して書く。

## 7. 方式の役割

| 対象 | 今後の役割 |
|---|---|
| B1 fixed cheap frontier | 主要対照。各固定gammaを保存通り報告 |
| cheap-first | 情報取得順序の候補。gamma1.01の普遍安全性ではない |
| 現B2/H1 | G2反例を持つ固定historical diagnostic。主運用方式として非採用 |
| M1 | 指定rank/reference/width/adoptionを持つ対照。spectral情報一般を代表しない |
| condition-wise最小safe gamma | 事後oracle診断。未知条件で選べる方式ではない |
| cost-free truth oracle | 固定候補/同時刻の改善余地。実装可能介入ではない |
| C0 | 幅と必要な分離情報の設計資料。厳密certificate成果ではない |

情報が増えても、十分賢いpolicyはそれを無視して元判断を維持できる。したがってM1の不利益は「情報が多いほど必ず悪くなる」ことではなく、取得情報・推定器・width・採用規則の具体的な組の性能である。

HFでは共通safe gamma1.10とM1の比較で小さいaggregate差が残るが、これを消さない。一方、condition-wise oracle gammaへ全方式が勝つことを要求するのも不公平である。固定運用arm、実際のpolicy、事後oracleを三つに分ける。

## 8. 必要な図表と原稿構成

作業履歴のD1→D2→C0→G2をそのまま本文構成にしない。

| 主図 | 内容 | 根拠 |
|---|---|---|
| Figure 1 | selected frozen budgetの過小評価と吸収可能余裕。HF eqを失敗、stretchをsafeな符号反転例として示す | budget_safety_capacity.csv / selected_frozen_budget_safety.csv |
| Figure 2 | named safe cheap対照→同時刻/native-grid oracleまでのheadroomと、実M1のbudget/abstainを対比 | same_time_oracle_headroom.csv / oracle_headroom_by_contract.csv / M1 table |
| Figure 3 | H-chainでPF側・H-reference側・differenceの誤差を同じ物理energy originで並べる | m1_reference_error_decomposition.csv |
| Table 1 | conditions、native contract、reference適格性、sampleの単位、正式status | 保存protocolとsummary |

H-chain leadingモデルと約33%の表、全gamma/全座標表、細かいstage会計、old stop/provenance、software caveatは付録へ。H3の適用不能とH2の有限次元特性は本文tableにも残す。

本文構成は、問題設定→安全性とoracle/widthの基本関係→cheap反例と安全事例→改善余地とspectral実結果→reference誤差→実務的含意と限界、を推奨する。

## 9. 次の作業と停止点

### 次の作業：完成済み解析から研究成果版を作る

Codex側は、既存CSV/JSONから上記図表、claim-evidence台帳、論文概要、先行研究差分表を作成する。数値の再fit、新しいpolicy評価、新しいoracle-grid、再採点、HCl/LiF補完は行わない。表示の丸めや単位変換は保存値へ照合する。

追加文献[L2]と出版版[L1]をrole mapへ加え、単なる一般論に依存した新規性表現を修正する。研究現状ページへの反映と詳細な原稿化は、今回方針のユーザー承認に基づいて行う。

成果物は原則、(1) result synthesis、(2) claim-evidence ledger、(3) figure/captionとsource対応、(4) updated related-work delta、(5) outstanding-claims表、にまとめる。新しい主解析CSVを量産せず、既存tableをauthoritative resultとして利用する。

`AGENTS.md`に従い、許可repository内で必要成果物だけをcommit・non-force pushし、40文字commitと読む順序をhandoffへ記載する。private runtimeや元science artifactは変更・公開しない。[R8]

### 追加科学検証を検討する場合

| 未達の主張 | 必要になるもの | 現在の判断 |
|---|---|---|
| 新gateが未知条件で安全 | 新規則を固定した後の未使用評価 | 今回の完成条件にしない |
| M1/reference悪化の因果原因 | state/rank等を独立に変える実験 | 観測分解に限定すれば不要 |
| spectral法一般の優劣 | 外部代表法等の同条件実装比較 | 現M1に限定すれば不要 |
| HF/HClにも同じreference相殺機構 | same-H独立energy identityの補完 | H-chain限定なら不要 |
| 量子・古典end-to-end利益 | q=1 combined/cold cost、回路・実装会計 | 現在は主張しない |
| 別PF/basis/geometryへの一般化 | 別scopeの事前固定評価 | 現在の結果から一般化しない |

追加実験を永続的に禁じる意味ではない。まず成果版を読んで、どの特定claimが欠けるために何を計算するかを決める。より強い主張を要求しない限り、追加分子・rank・q=1探索を一律の条件にしない。

### 完成条件

中心C1–C3に根拠図表と比較対象が対応し、代数とempirical evidenceの境界、post-hoc/未使用評価の境界、condition/coordinateの分母、oracle/operationalの境界が明記されていること。新手法の勝利は必要ない。

既存主解析の同一性確認33,434件は算術監査であり、科学的発見の件数ではない。旧full test suiteの未解決事項はH8原report通り保存し、今回の主解析testでrepository全体greenになったとはしない。[R7]

## 10. 第3方針と将来方法開発

現結果だけでは新PF設計へ進むtriggerはない。主に校正bias、幅、reference、固定候補余地を見ており、他PFを公平に比較して固有の不足を示した結果ではない。

将来、新PFが必要となるのは、既存PFのtruth-freeに利用可能な校正・時刻戦略では資源目標が満たせず、かつPF自体を変えることで改善できる具体的な領域と比較設計が特定された場合である。現B2/H1 gateの失敗だけをその理由にしない。

新gate設計も、既知HFをdevelopmentとして使うこと自体は許されるが、新規則の独立評価には使い戻せない。現研究のまとめと、将来の方法開発を混同しない。

## 11. 主要内部資料

以下はすべて基準commit `bfe715fc1c04325535a3c4d63ea4584e691dc322` で参照した。

- [R1] `artifacts/budget_safety_mechanism_20261005/report.md`
- [R2] `docs/second_study_v2/budget_safety_mechanism_20261005/quantity_dictionary_and_analysis_spec.md`
- [R3] `docs/second_study_v2/budget_safety_mechanism_20261005/final_direction_and_claim_scope.md`
- [R4] `artifacts/budget_safety_mechanism_20261005/same_time_oracle_headroom.csv`
- [R5] `artifacts/budget_safety_mechanism_20261005/oracle_headroom_by_contract.csv`
- [R6] `artifacts/budget_safety_mechanism_20261005/m1_reference_error_decomposition.csv`
- [R7] `artifacts/budget_safety_mechanism_20261005/independent_validation_audit.json`
- [R8] `AGENTS.md`
- [R9] `docs/second_study_v2/research_direction_review_after_hchain_20261005/novelty_assessment.md`

本レビューは原本の全source/manifestを再hashした監査ではない。主要資料・解析仕様・代表数表を読み直し、保存監査の範囲も確認した研究判断である。

## 12. 外部一次資料・確認範囲

- [L1] S. G. Mehendale, L. A. Martínez-Martínez, P. D. Kamath, A. F. Izmaylov, “Estimating Trotter approximation errors to optimize Hamiltonian partitioning for lower eigenvalue errors,” Digital Discovery 4, 3540–3551 (2025), DOI `10.1039/D5DD00185D`; arXiv `2312.13282v3`. 出版版のIntroduction、Results、Resource efficiency、Conclusionsとv3本文を照合。N2伸長の追加を含む。
- [L2] W. A. Simon, P. J. Love, “Quantum Advantage in Resource Estimation,” arXiv `2512.02131v1` (2025). Main text、Appendix B resource estimation、Appendix D phase errorを確認。
- [L3] W. Maxwell et al., “Practical Estimation of Trotter Error for Hamiltonian Simulation,” arXiv `2606.30738v1` (2026). Abstract、Introduction、asymptotic結果・compact BCHのscopeを確認。全定理の再証明はしていない。
- [L4] C. Yi, E. Crosson, “Spectral Analysis of Product Formulas for Quantum Simulation,” arXiv `2102.12655`. Abstract/scope確認。
- [L5] K. Hejazi et al., “Better product formulas for quantum phase estimation,” arXiv `2412.16811v1`. Abstract、spectral perturbation/gap assumptions確認。
- [L6] M. Miller et al., “phase2: Full-State Vector Simulation of Quantum Time Evolution at Scale,” arXiv `2504.17881v2` (2026改訂). Abstract、empirical-versus-bound/resource discussion、版情報確認。
- [L7] M. Kronenberger, M. Erakovic, M. Reiher, “Trotter error and orbital transformations in quantum phase estimation,” DOI `10.1080/00268976.2026.2681062`; arXiv `2602.18913v1`. Publisher abstract/本文のdescriptor・conclusionを確認。
- [L8] E. Pelofske, S. Eidenbenz, “Effects of Trotter Error, Digitization Error, and Initial State Overlap on Tapered Quantum Phase Estimation for Minimum Eigenvalue Computation,” arXiv `2609.06249` (2026). Abstract確認のみ。
- [L9] E. N. Epperly, L. Lin, Y. Nakatsukasa, “A theory of quantum subspace diagonalization,” arXiv `2110.07492v2`, SIAM J. Matrix Anal. Appl. 43(3), 1263–1290 (2022). Abstract/書誌確認。M1 empirical widthへ定理を無条件に適用しない。
- [L10] G. Rendon, J. Watkins, N. Wiebe, “Improved Accuracy for Trotter Simulations Using Chebyshev Interpolation,” arXiv `2212.14144v4`, Quantum 8, 1266 (2024). Abstract/書誌確認。補正・外挿は現在のuncorrected fixed-budget taskとは区別する。

## 最終判断

既存主解析は、研究の中心を具体化するのに十分な判断材料を与えた。今は新pilotを挟んで再度方針を考える段階ではなく、限定された信頼性・headroom研究としてcontributionと図表を完成させる段階である。新規性は一般理論や単なる代数に置かず、凍結済み実判断の反例、安全なcheap対照から残る僅かな改善余地、spectral/reference誤差の分離という実証内容に置く。
