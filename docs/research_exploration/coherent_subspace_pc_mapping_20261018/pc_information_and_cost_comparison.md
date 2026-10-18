# 同じaccessでの標本分布・分散・費用の比較

2026-10-18 JST。手計算による仕様照合。**期待値が一致するだけの対応から一段進め、理想モデルではVQNHEの2種の配置対測定からGの意思決定統計を同じshot数で再現できる。** 以下は解析式であり、標本生成・solver・symbolic checker・回路build/compileを行っていない。

## 1. 非対角Pauliの配置対

固定term lでP|y〉=ω(y)|y⊕d〉、d≠0。dの立った一bitをstarとし、star=0のbitstring uを各pairの代表、v=u⊕d、θ=〈u|P|v〉=ω(v)とする。PはHermitianなのでω(u)=θ*。解析用記号として

\[
p_u=|\psi_u|^2,\quad p_v=|\psi_v|^2,\quad
S_o=p_u+p_v,\quad t_o=\psi_u^*\theta\psi_v
\tag{I1}
\]

と書く。ψの振幅をoracleに与えるのではない。u,v,d,θと以下のrecord変換は既知Pauliとbitstringから計算できる。

[VQNHE本文式(5)–(9)、complex supplement式(S13)–(S15)](https://arxiv.org/html/2106.05105v1)の2種の配置対basisを、符号labelを揃えて次のように表す。

\[
|R,\sigma,o\rangle=(|u\rangle+\sigma\theta^*|v\rangle)/\sqrt2,
\quad
|I,\sigma,o\rangle=(|u\rangle+i\sigma\theta^*|v\rangle)/\sqrt2.
\]

従ってその測定記録(β,o,σ)の確率は

\[
\Pr_V(\sigma,o|R)=\tfrac12(S_o+2\sigma\operatorname{Re}t_o),
\quad
\Pr_V(\sigma,o|I)=\tfrac12(S_o+2\sigma\operatorname{Im}t_o).
\tag{I2}
\]

原論文のstar出力の符号が異なる場合は既知の符号relabelで揃える。これは新しい測定法の構成ではなく、同論文の2つのpair quadratureの数学的表現である。

一方、Gのancilla測定記録(s,x)は

\[
\begin{array}{ll}
\Pr_G(s,u|X)=\tfrac14(S_o+2s\operatorname{Re}t_o),&
\Pr_G(s,v|X)=\tfrac14(S_o+2s\operatorname{Re}t_o),\\
\Pr_G(s,u|Y)=\tfrac14(S_o+2s\operatorname{Im}t_o),&
\Pr_G(s,v|Y)=\tfrac14(S_o-2s\operatorname{Im}t_o).
\end{array}
\tag{I3}
\]

Gの(|0〉ψ+|1〉Pψ)/√2について、固定xのancillaのX/Y Born確率を展開すると得られる。複素位相はθに含まれ、後からωを再度掛けない。

## 2. recordの相互変換と意思決定統計の一致

I2→I3の変換は、VQNHEのrecordに独立な公平bit o_dirを加えるだけである。

| quadrature | o_dir=0 | o_dir=1 |
| --- | --- | --- |
| R→GのX | x=u、s=σ | x=v、s=σ |
| I→GのY | x=u、s=σ | x=v、s=−σ |

逆方向はpairを特定し、Xならσ=s、Yならx=uでσ=s／x=vでσ=−sとしてorientationを捨てればよい。いずれもψを要求しない。lを同じabs(j_l)/Λで、βを同じ1/2で選べば、termとaxisも含むjoint lawの対応になる。

さらに、Gは各標本をHermitian化してから足したものと、平均後Hermitian化したものが数学的に同じである。E_aa′をlabel matrixの一entryとし、a=f(u)、a′=f(v)、κ_l=Λ sgn(j_l)とすると、GのHermitian一標本matrixは

\[
\mathcal M_R^f=\kappa_l\sigma(E_{aa'}+E_{a'a}),
\quad
\mathcal M_I^f=i\kappa_l\sigma(E_{aa'}-E_{a'a}).
\tag{I4}
\]

a=a′もこの式で扱える。Rは2κσE_aa、Iは0となる。I4はorientationに依存しない。従ってVQNHE recordからorientation用coinすら生成せず、**同じHermitian Jhat^fを全fについて同時に**作れる。単なる各entryの平均の一致ではなく、一標本matrix族{M^f}_fのjoint distributionが同じであり、全cross-covarianceとmatrix推定値の分布も同じである。未Hermitian化のraw一entry標本を比べる場合は上のfair-bit変換を含める。

population poolは同じψのZ samplesをm_S回取得する。Shatも同じ分布、同じ共通recordの比較なら同じ値である。Gのe_H/e_S、全Fの同時confidence、u_fはそのまま使用できる。VQNHEの別の効率定理やSSEのnoise式をGへ流用していない。

加えてC_addのH-record部分は

\[
W_{f'}(x)+W_{f'}(x\oplus d)=W_{f'}(u)+W_{f'}(v)
\tag{I5}
\]

でorientation非依存である。残りは同じpopulation記録とK等の固定値だけ。従って**Jhat、Shat、confidence、g_L、C_add、その比とtie判定まで同時に再現**できる。前文書の帰納法により全tree更新とSTOPも再現する。

同じcouplingの下でpathwiseに一致するという意味である。独立に採った二つの有限shot実runが必ず同じtreeを返す、という意味ではない。有限精度のbit単位一致を要求する場合は、fair-bitで同じraw形式を作り、同じ集計順・算術・solver規約を使う必要がある。

## 3. 対角termとscalar

d=0ならP|x〉=ω(x)|x〉、ω(x)=±1。GのX outcomeはs=ω(x)に確定し、Y outcomeは±1等確率。VQNHEの通常のZ測定xに、同じaxisのcoinとY用の独立符号coinを加えればGのrecord lawを再現できる。GのHermitian contributionはXで2Λ sgn(j_l)ω(x)E_aa、Yで0。意思決定統計はZ recordとaxisだけから作れる。

従って対角termも同じm_Hのseed準備で対応する。既知法が対角項にYを使わない効率化を許されることはあるが、その利得をGの原lawの結果と混同しない。scalar cは双方c Shatとして一回だけ戻す。Λ=0なら双方E0=cで終了する。

## 4. 状態準備と回路費

| 項目 | 固定G | VQNHE配置対＋同じ後処理 | literalなlocal-shadow SSE |
| --- | --- | --- | --- |
| H用seed | m_H回のA | 同じm_H回のA。1配置対標本にA一回 | 選んだshadow budget分のA |
| population | 別m_S回のAとZ測定 | 同じpoolを使用可能 | 既存shadowから推定する場合は別の分散。公平比較では同じZ poolも許す |
| A†／controlled-A | 不要 | 不要 | 標準local shadowsでも不要 |
| 追加ancilla | G仕様では一個 | starをsystem内に取る原測定では不要 | local単一qubit測定では不要 |
| logical操作 | controlled-P。素朴な分解では非I支持w_lへのcontrol | 論文記載のX/Y支持m_lに対するstar control、最大m_l−1個の2qubit操作。Z phaseは古典処理できる | local basis回転で測定。必要なprojector momentsの分散・処理費は別 |
| readout | system n bit＋ancilla符号 | system n bitにpairとσを符号化 | basis情報とn bit |
| 実費 | m_H(C_A+C_cP)+m_S C_Aとreadout | m_H(C_A+C_pair)+m_S C_Aとreadout | shadow norm、必要copies、対象observable評価費を含めて別計上 |

これは既存のlogical構成の比較であり、実装・compile結果やhardwareのgate下界ではない。connectivity、制御のnative価格、noise、最適化で定数は変わり得る。**Gに同shotの情報上の優位はなく、VQNHEとのnative実時間差は未測定**。後者の未測定は、前者の理想access下の再現証明を未判定へ戻す理由にはしない。

Z-controlを省略するVQNHE実装では、対応するZ-bit parityの符号をrecordへ戻す古典費も取得会計へ足す。省略せず既知の全control構成を用いれば、非I支持w_lに対しstar以外のw_l−1 controlとなり、そのparity補正を回路に含められる。前者の少ないgateと後者の少ない補正費を同時に無料で取らない。pairからu,vを復元するbit操作、term／axisの乱択、readout処理も両者へ計上する。**同一なのは比較用に正規化したrecordのlawとC_addであり、異なる取得実装の全instruction数が同一という意味ではない。**

## 5. SSEを同予算と扱ってはいけない範囲

SSE原法はlocal Pauli poolとlocal Clifford shadowsを用い、小space energy gainでfilterしGramをregularizeする。[§II.2、III.1–3](https://arxiv.org/html/2406.11533v1) 任意のΠ_aをpoolへ追加すると、Pauli演算子の(反)交換だけで済むfilter式が失われる。Π_aのPauli展開、shadow norm、実際の統計保証と評価bit費を数える必要がある。一般のpredicateについてpolytime・同shotのtrace評価を仮定しない。

同じDに含まれ得るq_{C,0}=1[N_C=0]だけでも差が分かる。サイズwのCについて

\[
\Pi_{C,0}=\prod_{i\in C}(I+Z_i)/2.
\]

一様local X/Y/Z shadowsでの通常のunbiased estimatorは

\[
T=\prod_{i\in C}(1+3b_i1_{B_i=Z})/2.
\]

C上が|0…0〉のseedでは、各factorは確率1/3で2、確率2/3で1/2。従ってE[T]=1、E[T²]=(3/2)^w、Var(T)=(3/2)^w−1となる。通常のZ人口測定なら同じprojectorの標本は常に1で分散0である。必要ならC外の占有spectatorで固定Nを保てる。

これは測定分布の紙上診断であり、新しいHamiltonian family／P-d近似保証の構成ではない。Gが全SSE変種に勝つという意味もない。biased shadows、Z人口pool、VQNHE配置対等を同じ情報で許した強対照には、この差をG固有の利点として保持できない。**標準SSEとGのrecordは異なるが、既知配置対対照でGを再現できる**という二つの事実を分ける。

## 6. 古典費・統計保証の会計

graphの実処理も明記する。支持のclique加算はO(Σ_μサイズ(I_μ)²)、E本のedge整列はO(E log E)、その後のunion-findはO(E α(n))。中間clusterを明示保存するなら、その総member数だけ書込・記憶費を足す。Cからのthreshold列もQ個分を作る。edge、cluster、predicateの表現を共有する対照は全く同じ処理であり、Gだけgraph生成を無料としない。これらはoperation-count上の上界で、係数加算・比較のbit費は別途双方に入る。測定後は各H recordについて同じ二つのendpointを分類し、同じ二つのmatrix位置へ集計する。全Fを実際に列挙する費用を仮定せず、各stepの実候補≤KQだけを数える。

| 費用／保証 | 同じD・同じrecordを使う対照での結果 |
| --- | --- |
| graphと辞書 | 同じterm集計、edge整列、forest、threshold列。Q=O(n(L+n))を双方へ計上 |
| storage | O((m_H+m_S)(n+log M))のG記録。VQNHE pair記録も同じorder。raw Gへ展開するならO(m_H)のclassical coin処理。意思決定には不要 |
| 候補評価 | stepごとに≤KQ候補。同じpredicate path、同じmatrix集計とK³ solve。全候補のscreening費を足す |
| C_add | I5と同じZ poolにより値が一致。比を選ぶ前に全候補をscreenした費用は既に支払い済み。比の最大化から総実費の最小性は出ない |
| confidence | 固定Fの同時eventと同じp_min依存幅。選択後の一候補だけのintervalで代用しない。record law／統計が一致する対照にも同じ保証 |
| 停止 | certificate不足・候補なし・K上限で同じ。E0精度達成の証明ではない |
| coherent出力state | F_zψを実際に準備する場合のpredicate/table/rotation/uncomputeとpostselection費は双方へ計上。energy後処理だけで準備済みとしない |

finite-bit係数比較とsolveのbit費を省略しない。同じ算術規約ならこれも同じ課題であり、Gにだけ効率的oracleを与えない。原Gの小人口conditioning・support障害・絶対E0との距離は残るが、その再研究・救済は今回行わない。
