# 識別例：何が変わり、何が変わらないか

2026-10-18 JST。[P2 family](research_problem_and_gap.md)と[G1–G4](generation_rule_construction.md)を用いる紙上導出。数値state・行列・標本・科学用記号計算は生成していない。全例で元HとN=2を保持し、Fの都合のよいsectorへH全体を置き換えない。

## D1. 条件付き回転を外すと同時対角化できない場合

N12=N34=1の部分に限って識別する。s=±1に対するactive演算子は

\[
h_+=tX+(d+u)Z,\qquad h_-=tX+(d-u)Z,
\quad [h_+,h_-]=4ituY.
\tag{D1}
\]

tu≠0なら非可換なので、**両contextを一つの同じactive軌道回転で対角化することはできない**。条件付き規則は異なるθ_±を使って両方を対角化する。これは全Gaussian回転、全複数basis戦略、全測定法への下界ではなく、spectatorを固定読出しする一つのactive基底に限る障害である。

recordについても同じ限定を直接確認できる。一軸qのactive測定しか使わない場合、h_sのBlochベクトルと非平行なqでは、qに直交しh_sと内積非零のunit vector wを選べる。active density (I±w·σ)/2と同じ固定spectatorを持つ二stateは、その一軸record lawが一致するが、F平均は2h_s·wだけ異なる。従ってそのrecordから、未知stateに依存しない古典変換だけで全stateのF spectral recordを再現できない。

t=0なら元occupation basis、u=0なら共通Givens、又は入力stateが既知の単一contextに限られる場合には、この差は消える。対照にわざと二つの角度を禁止して得た差を、強いB_fairへの独立差と数えない。

## D2. 実際の一標本分散が変わる例

d=ν=0、t>0、u≠0、η≠0とする。r=√(t²+u²)、Zの−1 eigenstate |−z〉=|01〉、g_s=U_s|−z〉と書き、Fock順を固定した

\[
|\Psi\rangle=\frac{|g_+\rangle_{12}|10\rangle_{34}
                         +|g_-\rangle_{12}|01\rangle_{34}}{\sqrt2}
\tag{D2}
\]

を測定診断に用いる。これはHの未知groundを無料で与える仮定ではない。spectator一電子の等重ね合わせを作り、そのoccupationをcontrolとするGivens回転で有限に準備できるstateの式である。この準備費C_A（必要な条件付きgateを含む）は全対照に共通で払う。N=2、N12=N34=1を満たすが、全Hの不変部分空間とはしていない。

各contextでFのeigenvalueは−rなので、条件付き測定のscoreは常に−r、Var(y_F)=0。一方、核心を外してtXとuSZを独立poolで測るablationでは

\[
\langle X\rangle=-t/r,\quad\langle SZ\rangle=-u/r,
\quad v_{tX}=v_{uSZ}=t^2u^2/r^2.
\tag{D3}
\]

総m copyを二poolへ最適に配った標本平均和の分散は、連続allocationの理想化では

\[
\min_{m_1+m_2=m}\left(v_{tX}/m_1+v_{uSZ}/m_2\right)
=4t^2u^2/(r^2m)>0.
\tag{D4}
\]

よって**測定変更による標本分散の差自体はある**。しかし公表済みL01の測定も同じG4を実現してVar=0となる。候補対B_fairのshot利得は得られない。また、これは指定されたsample-mean estimatorの比較であって、全推定量のcopy下界ではない。D2の完全な準備記述と係数が既知なら−rを古典式から返せる対照もあり、小系での量子優位の根拠にできない。

このstateはFのeigenstateであって、η≠0のHのgroundとは認定しない。Rの測定分散・期待値とstate品質は別問題であり、D4を絶対E0総費用の改善率へ使わない。

## D3. 全Hを同じ記録だけで評価しようとすると失う情報

spectatorを先に測るchannelは、結果を捨てたとき

\[
\mathcal D(\rho)=\sum_zP_z\rho P_z,\qquad
\mathcal D^*(F)=F,\qquad\mathcal D^*(R)=0.
\tag{D5}
\]

X23はn3を、X34は(n3,n4)を変えるので、各P_z R P_z=0となる。従ってこの手順の同じcopyを、元Rの測定用copyとして無料再利用できない。

さらに

\[
|\chi_\pm\rangle=(|1100\rangle\pm|1010\rangle)/\sqrt2
\tag{D6}
\]

はどちらもN=2で、D(χ_+)=D(χ_−)。全てのG4 record lawが同じなのに、〈R〉_±=±η（X34の平均は0）となる。したがって任意stateに有効な**recordのみの**後処理からR平均を再構成することはできない。これは未知ρに対する測定記録の識別障害であり、係数が既知なE0問題の無制限古典計算下の情報理論的下界ではない。

この障害を避ける本仕様はRに別のfresh poolを使う。Rを0とする、ηを結果後に小さくする、postselectionでcross-context成分を捨てる、coherent Uなら全H情報も同時に読めると仮定する、といった救済は行わない。

## 判別が決めたこと

| 問い | 紙上の結果 |
| --- | --- |
| 操作変更は空疎か | いいえ。D1の固定一基底障害、D2の分散差がある |
| その差はB_fairにも残るか | 残らない。L01の公表済み条件付き測定が同じlawを実現する |
| Fの利得を全Hへ無償で移せるか | 移せない。D3でcross-context情報が失われる |
| 有用な絶対E0保証・量子優位が得られたか | 未構成。小例の成立はその証拠ではない |

限定的な障害は上の各構成classだけに及ぶ。全条件付き測定、全電子family、D1下の新算法一般を否定しない。
