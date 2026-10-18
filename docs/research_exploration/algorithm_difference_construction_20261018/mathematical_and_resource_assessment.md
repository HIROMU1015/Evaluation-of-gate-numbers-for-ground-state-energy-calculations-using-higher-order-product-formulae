# 数学的判別・資源会計と残る問い

2026-10-18 JST。手計算による仕様照合。[生成式](generation_rule_construction.md)・[識別例](discriminating_examples.md)の数学を数値solverやsymbolic checkerで検査したとはしない。

## 1. 成立・独立性・有用性を分ける

| 層 | 到達点 |
| --- | --- |
| 操作成立 | G2の条件付き二準位対角化とG4のPOVM／momentが成立。finite precisionはG6で別会計 |
| 既知対照との差 | 固定一軸／別pool ablationとの差は成立。公表済みL01を公平に用いる対照との差は残らない |
| 差による性能・保証 | D2のF測定標本分散差は成立するが、B_fairにも同じ分布と保証がある |
| 元Hの絶対E0への有用性 | state品質、R、native/noise、全費用、E0精度保証は未確立 |

技術分類は**既知手順への還元**。付随して、固定active一軸の同時対角化不能と、F recordからcross-context Rを復元できない限定的障害を得た。これらは全手法の不可能性ではない。独立した具体差分候補を成立認定しておらず、正式研究状態は変更しない。

## 2. 実際のcopies・分散・confidence

Fの一標本値は|y_F|≤B_F=|ν|+r_max。固定m_Fの独立準備から平均を作るとVar(Fhat)=Var_ρ(F)/m_F。state-independentな一つの十分shot条件は

\[
m_F\ge\frac{2B_F^2}{\epsilon_F^2}\log\frac2{\alpha_F}
\tag{M1}
\]

で、|Fhat−TrρF|≤ε_Fを確率≥1−α_Fで保証する（bounded IID sampleの通常のconcentration）。B_fairにも**同じ**M1が成り立つ。D2のvariance0を観測一回から全未知stateへ保証したことにはならず、varianceに基づくshot allocationには推定費・confidenceを入れる。原seedを選び直して安いvarianceを無料化しない。

Rは二つのhopping測定等で別に取得し、ε_R、α_Rを計上する。G6の系統幅をδ_F、その他のreadout等の幅をδ_deviceとすれば、単純なunion会計では

\[
|\widehat E-E_\rho|\le\epsilon_F+\epsilon_R+\delta_F+\delta_{device},
\quad\Pr(\text{statistical event})\ge1-\alpha_F-\alpha_R.
\tag{M2}
\]

ηやcを落とさず、E_ρ−E0という近似stateの誤差を別に加える必要がある。その有用な上界は今回ない。M2を絶対E0 certificateと呼ばない。

## 3. 何を節約し、何を追加するか

同一の加算可能な量子gate座標gについて、Fの別pool測定をm_X,m_D、条件付き測定をm_F、Rの同じ測定をC_R^(g)とする。各測定のstate準備以外の費用をc_X,c_D,c_condと分けると

\[
\begin{split}
C_{sep}^{(g)}&=(m_X+m_D)C_A^{(g)}+m_Xc_X^{(g)}+m_Dc_D^{(g)}+C_R^{(g)},\\
C_{cond}^{(g)}&=m_F(C_A^{(g)}+c_{cond}^{(g)})+C_R^{(g)}\\
&=C_{sep}^{(g)}
-(m_X+m_D-m_F)C_A^{(g)}-m_Xc_X^{(g)}-m_Dc_D^{(g)}
+m_Fc_{cond}^{(g)}.
\end{split}\tag{M3}
\]

c_condには二spectatorとactiveのreadout、一active Givens、feedforward実装に伴う当該資源を含める。latencyはgate数へ換算せず時間座標で別会計する。単にpoolが一つ減ったことだけで総gate費が下がるとはしない。C_Rを省けない理由はD5–D6である。B_fairとの比較ではm_F、c_cond、C_A、C_Rが全て同じなので、**同じ実装を選ぶ限り同じ費用の構成が存在する**。全装置に対する最適実費の等価定理ではない。

| 資源 | 明示した会計・限界 |
| --- | --- |
| state copies | F-shotにA一回、R-shotにもfresh A。A†・controlled-Aなし。D2用Aの条件付き準備も全対照に課金 |
| 量子操作／depth | Fではoccupation readoutと隣接pair Givens。coherent版Uのcontrol全branchは不要。native分解・compile/depth実測は未実施 |
| shots | Var_ρ(F)、range、confidenceに従う。B_fairは同じjoint law、平均、分散。無関係なshadow lawを同shotとしない |
| 古典前処理 | 元係数の読取・canonical化・pattern検査＋三つのsqrt/atan2、要求bit精度。一般Hの最適pattern分割器は未構成 |
| shot後処理 | sとx1−x2の計算、三値table照合とscore加算。B_fairも同じ |
| 記憶量 | 三つの角度／r tableと係数、積算値。全recordを残すならO(m_F)個の定数長record。一般kの2^k tableが無料とはしない |
| 証拠／pilot | variance・state品質・noise calibrationを実際に認証するなら取得費が追加。今回はいずれも実施・無料仮定していない |

shot数、CX/T/depth、CPU時間、memory、待機時間を換算規則なく足さない。M3は記号会計であり、数値速度向上や改善率は作っていない。

## 4. なぜ数値実験へ進まないか

今回のRは公表生成手順へ閉形式で代入でき、全未知ρのrecord lawまで一致した。数値toyでこの一致を再確認しても、独立核心の有無という判断は変わらない。D2の分散差も既知対照で再現でき、D3は別pool費を必須にする。従って**本構成のための新規simulation・科学契約・grantは提案しない**。

残るのは一般電子Hでの有用性、native装置費、網羅的priority等だが、現仮説を維持する具体差ではない。これを埋めるために別pattern、非可換context、別angle heuristicを無制限探索しない。今回得た限定的障害の外に新機構があるかは未判定であり、その探索は今回の後続承認ではない。

次の最小の判断は、ユーザー／GPTがこの還元結果を確認し、この一件を技術記録として扱うかを決めることである。独立新規性・論文化・次方向の採否をCodexが決めない。別の具体核心を将来検討する場合は、同じ合法accessで公表L01を越えて変える量と識別条件を示す別依頼が必要となる。今回その別核心を作ったとはしない。
