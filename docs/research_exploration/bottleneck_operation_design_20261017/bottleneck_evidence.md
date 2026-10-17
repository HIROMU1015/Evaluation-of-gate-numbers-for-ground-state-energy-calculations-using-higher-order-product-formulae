# 具体的ボトルネックから操作仕様へ

2026-10-17 JST。紙上検討、固定資料の静的確認、限定一次文献調査。
**具体的な操作仕様を1件まで展開したが、明示的な既知法還元により最終保持は0件。**
一般的な「depth／shotsが多い」を課題とせず、入力から目的作用へ進むどの段階が不足するかを区別した。

## 1. 旧研究の障害と今回の取扱い

固定SOURCEの原文・commit・bytesは[source_registry.json](source_registry.json)に対応する。
保存された科学数値は再計算・再集計していない。下記の結論を新しい一般no-goへ拡張しない。

| 障害 | なぜ生じるか／既存操作だけで不足する点 | 根拠と境界 | 今回の扱い |
|---|---|---|---|
| PF校正のstate proxyを良くしても、選択する時刻・予算が良くなるとは限らない | proxyの期待値、PF固有枝、finite-time model、安全margin、取得費は異なる。診断がbaselineと同じ選択を返せば、その診断の増分価値は出ない | 第一研究S4は固定範囲で`complete_no_benefit`。第二研究はpoint精度とdecision window／budgetを区別する。[S07–S09] | 新selector、threshold、rank、truthの取得は行わず、独立操作課題に移さない |
| coherentな乱択平均の保証を、そのまま一般DF・絶対E0の全費用へ移せない | 平均channel、平均複素信号、trajectory、位相、visibilityは違う。先導係数の改善はnative gateとshotsの利益を自動で与えない | PR Track Bの後続限定受理とNOT ADOPTED草稿を分ける。Track Aの取得済み点優位と母平均・最終energy費用も別。[R01, R04, R05] | 既存law・共有±・gate価格・一般DF移送の再設計はしない |
| 相互作用の表現を変えても、coherent操作を構成したことにならない | arbitraryな非可換二次式は単一scalar phaseで生成できない。未知振幅の対数やchart変換も固定量子gateにはならない | 直近NA/NBの保持0件、P1～P8の還元記録。[S01, S02, S04] | NA/NBの修正案を探索せず、今回の新課題の入力契約を明示する |
| energyを正しく測ることと、固有state上の追加測定noiseを消すことは異なる | 個別observableの測定は、H全体に存在する非可換なcross項・共分散を保存する測定器とは限らない | O5、X2およびP6。joint POVM、Bell測定、制御変量自体は既知。[S04–S06] | 二つ目の候補にはしない。具体的な新instrument生成規則を今回作れていないため |
| 少粒子係数を符号化したcopiesと、N電子Hamiltonianを符号化したcopiesは異なる | 二電子係数は\(\mathcal P_2\)上、targetは\(\mathcal F_N\)上。普通のSWAPは両空間の意味をそのまま交換できない | DMEの入力、既存PRのcopy-access境界。[L02, R02] | **操作仕様Aへ展開し、CG/Paldusへの具体還元後に不保持** |

J1の保留理由は、共同閉路の試行が既知loop／echoに還元されるか、低次bus残差を消せなかったことである。[S03]
今回の操作設計はbus、pulse word、CARによる共同閉路の探索を使わず、J1の再開条件の審査にもしていない。

## 2. 操作仕様へ展開した障害を正確に書く

二電子係数行列Vと、その多電子作用\(\Gamma_N(V)\)の定義は[操作仕様](operation_design_task.md) §1。
通常のDMEへ多電子状態

\[
\rho_N=\Gamma_N(V)/\operatorname{Tr}_{\mathcal F_N}\Gamma_N(V)
\]

を与えればよい、とする案は、\(\rho_N\)の準備を新しい入力問題として残す。
さらに標準pair basisで

\[
\operatorname{Tr}_{\mathcal F_N}\Gamma_N(V)
=\binom{M-2}{N-2}\operatorname{Tr}_{\mathcal P_2}V
\tag{B1}
\]

である。各対角pairが\(\binom{M-2}{N-2}\)個のdeterminantに含まれることによる。
このtrace正規化は、二電子係数のtraceとは異なり、NとMによって大きくなり得る。
式(B1)は今回の短い紙上の数え上げであり、新しい数値評価や一般下界ではない。
\(\rho_N\)の実際の準備法や特殊クラスを排除せず、trace因子だけで全方式の不利も結論しない。

代わりに\(\rho_2=V/\operatorname{Tr}V\)を入力する場合、目標のfirst-order generatorは
\(\Gamma_N(\rho_2)/\binom N2\)。
HMEはこのような線形写像の出力をHamiltonianにする一般機能を既に持つ。[L03]
従って、不足操作の候補を「新しいHME定理」や「二電子状態を用いるという発想」として提示しなかった。
具体化したのは、HMEのjoint generatorとして明示できる\(J_N\)を、係数非依存の具体的操作へ落とす規則である。
この規則も、§4で述べる既知法還元により新設計課題としては残らなかった。

## 3. 普通SWAPの失敗と、達成可能性の区別

二電子を抽出するisometry \(S_N\)と、そのimage上に圧縮したSWAPは数式で書ける。
しかし、SWAPはそのimageを保存しない。
M=5・N=3の手で追える例ではimage外成分が生じ、extract–SWAP–unextractをそのままdeterministicな衝突と呼べない。
具体式は操作仕様 §4。これはtargetのfermion反対称性に由来する、明示的な合成障害である。

一方、\(e^{-i\theta J_N}\)自体は有限次元の正しいunitaryであり、一般の回路合成や既知Schur/CGなどの経路を排除していない。
first-quantizedな個々のlabelled pairを順次処理する方式も、途中の非不変性を誤差へ戻して全体を近似する可能性があり、
「途中でimage外へ出るから全アルゴリズムが不可能」とはしない。
今回要求するのは、**一回の衝突の完了時に物理空間へ閉じ、coherent controlを保つ専用生成規則**である。

## 4. 不足操作の候補から、既知の生成規則へ

\(J_N\)は電子係数Vには依存せず、targetと二電子補助の全占有数wを保存する。
固定wでは必要なlabel空間の状態数が最大\(\binom{N+2}{2}\)となる。
これにより、不足操作の候補を「任意の多電子exp」から、**占有数blockを混合する係数非依存recoupling**へ限定した。
小blockであること自体では生成の完成を認定しない。
そのgeneratorを二speciesのCARで整理すると、全spinの二次多項式に還元される。
既知CG/Paldusのtotal-spin labelに応じた3種類のphaseと逆変換で、目的作用を生成する規則まで記述できた。
詳細は操作仕様 §6。したがって、ここに新しい操作が必要という課題は残さない。

P2と既存componentコードは小成分の列挙・対角化を既に扱っている。[S04, S10]
今回はVの配置graphを新たにclusteringするのではなく、補助衝突の運動学的blockを扱う。
今回の結果はCG/Paldus＋phaseへの特殊化であり、独立新原理としての差分は残らなかった。
同じ不足操作を別の名称や性能要求で救済する追加探索は開始しない。

## 5. 不保持とした残りの方向

- **momentを保存するenergy測定器**：\(\sum_z zM_z=H\)、\(\sum_z z^2M_z=H^2+D\)という要求までは書ける。
  しかし、\(D\)を制御する新しい測定生成規則を今回定義できていない。単なる「全Hのよい測定器を作る」という要求を二つ目の設計課題にはしない。
- **有限orbital空間へのcoordinate phaseの圧縮**：\(Pe^{-itV}P\)と\(e^{-itPVP}\)の違いは実際の障害だが、
  そのexpを供給する新規則を今回得ていない。反射・Zeno・block-encodingを中核に移す再設計は開始しない。
- **PFのphase補正・共分散推定・新selector**：既存の停止系列・Track A/B・第一／第二研究のscopeと重なる。
  今回の新操作課題の数を増やすために再命名しない。

これらの不保持は今回の具体化の不足を示すだけで、周辺原理の不可能性を意味しない。
NA/NB・J1や旧系列の正式状態は変更しない。

**最終保持0件。** これは上の操作仕様に対する限定結果であり、新しい操作が今後不要という一般結論ではない。
具体化した対象、既知還元、最小の確認例、失敗条件は[操作仕様](operation_design_task.md)へ集約した。

[S01]: ../independent_construction_principles_20261017/research_hypothesis_handoff.md
[S02]: ../independent_construction_principles_20261017/prior_art_and_not_retained.md
[S03]: ../p1star_j1_pause_decision_20261017/research_decision_record.md
[S04]: ../cross_domain_mechanism_ideation_20261016/principle_ideation_map.md
[S04–S06]: source_registry.json
[S01, S02, S04]: source_registry.json
[S04, S10]: source_registry.json
[S07–S09]: source_registry.json
[S10]: ../../../src/trotterlib/component_sector_pf.py
[R01, R04, R05]: source_registry.json
[L02]: https://arxiv.org/html/1608.00281v1
[L02, R02]: source_registry.json
[L03]: https://arxiv.org/html/2308.07956v1
[R02]: https://github.com/HIROMU1015/Partially-Randomized-Trotter/blob/56f1cc55c59ab7bc42c6b24e0953675de9b29b1d/docs/research/qc_new_algorithm_research_scope_20261016/open_problem_landscape.md
