# R1-P：直接還元の紙上確認

**判定：正の局所項をlayerへ分ける標準の(A+)解釈では、既知定理の直接的な帰結としてR1-Pの型を導ける。**
任意の相殺fragmentまで含める正本の読み方には、この判定を拡張しない。
条件の区別は [対応表](r1_known_theorem_mapping.md) §3。元のT0 SOURCEは変更しない。

今回の導出は固定された二点Richardson作用だけを扱う。使うのはL09の既知commutator／tail補題、
M26の有限BCH打切り、Duhamel公式二回と幾何級数。別PF、別係数、新ansatz、一般外挿定理の証明探索は行わない。
4 modes・2 electrons等の新しい具体例も実施しない。

## 1. 共通係数の相殺――単なる個別上界の加算ではない

L08 Lemmas 12–14／Appendix Aが示す共通展開では、固定有限Hamiltonianで
\[
 U_r(t)=U(t)+r^{-2}A_2(t)+r^{-4}A_4(t)+\cdots,
 \qquad U(t)=e^{-itH_+}.
\]
同じA_2を持つことにより、\((4/3)/4-1/3=0\) となる。
形式展開のA_4係数は \((4/3)/16-1/3=-1/4\)。
これだけではR1-Pのfinite-r保証ではないため、以下では共通の有限多項式に置き換えて証明する。

## 2. 既知Lie係数に対する上界

固定wordを \(S_2(h)=\prod_{v=1}^{N_f}e^{-ia_vhH_{\gamma_v}}\)、
\(W=\sum_v|a_v|\) と書く。
N_fはlayer exponentの数で、層内の物理gate数ではない。固定Γ・固定wordではnに依存しない。
scalarは正本どおりcに保持し、局所和のnorm会計に含まれる非空の局所項を対象とする。
M26 Eqs.42–46のBCH係数D_{j+1}は長さj+1のnested commutatorの線形結合。
式中の順列係数の絶対値とmultinomialを足すと、その絶対係数総量は
\(W^{j+1}/(j+1)^2\) 以下になる。
これは係数探索・係数生成プログラムではなく、掲載Lie多項式の上界の読み替えである。

(A+)なら \(0\preceq H_\gamma\preceq H_+\)。
\(P_b=1_{[0,b]}(H_+)\)、\(Q_b=I-P_b\) と書き、L09 Theorem S1を各nested commutatorへ使える。
局所項へ展開したcommutatorはsupportが高々(j+1)kで、L09 S40の総norm上界とS41のtailも使える。
したがって、固定word・kに依存する明示的な
\[
 \kappa=2ek\max\{1,W\}
\]
を大きめの係数envelopeとして、j≥2について
\[
 \|P_bD_{j+1}P_b\|\le\kappa^{j+1}j!J^jb,
 \qquad \|D_{j+1}\|\le\kappa^{j+1}j!nJ^{j+1}, \tag{D1}
\]
\[
 \|Q_bD_{j+1}P_a\|\le\kappa^{j+1}j!nJ^{j+1}
 e^{-(b-a)/(4kJ)},\qquad b>a. \tag{D2}
\]
を得る。D2で生じる \(e^{3(j+1)/4}\) はκへ含めた。
Corollary S2の期待値上界をnormの和へ交換した導出ではない。

以下J>0、n≥1、E≥0。J=0／t=0は(A+)の下で誤差ゼロの退化場合。

## 3. 二つのnodeに同じ打切りを使う

\[
 L=\log(nr/\zeta),\quad \varepsilon_{tr}=\zeta/(60r),
 \quad q_0=\lceil\log(180nr/\zeta)\rceil,
 \quad h_\nu=t/(\nu r),\quad \nu\in\{1,2\}.
\]
同じq_0、同じDを使い
\[
 B_h=\sum_{\substack{2\le j\le q_0-1\\j\ \mathrm{even}}}h^jD_{j+1},
 \quad R_h=B_h-h^2D_3,\quad \widetilde U_h(t)=e^{-it(H_++B_h)}.
\]
B_hはHermitian。未知固有位相のlog branchを入力していない。
M26 Theorem 3のstep条件を満たせば、unitaryのtelescopingで
\[
 \|U_{\nu r}(t)-\widetilde U_{h_\nu}(t)\|
 \le\nu r\varepsilon_{tr}\le\zeta/30. \tag{D3}
\]

\(\kappa J|h|q_0\le1/2\) とする。有限和の連続するeven-j項の比は1/4以下なので、D1/D2から
\(K=64\kappa^5\) を十分な共通定数として
\[
 \|P_bB_hP_b\|\le K(J|h|)^2b,
 \quad\|B_h\|\le KnJ(J|h|)^2,
\]
\[
 \|Q_bB_hP_a\|\le KnJ(J|h|)^2e^{-(b-a)/(4kJ)}. \tag{D4}
\]
R_hには同じ式の \((J|h|)^2\) を \((J|h|)^4\) へ替えた上界が使える。
D_3にも \(KJ^2b\)、\(KnJ^3\) と対応するtail上界が使える。
q_0を無限大へ送らず、有限係数和だけを評価した。

## 4. 二段cutoffで片側normと二挿入項を管理する

正本と同じ \(E'=E+C_0JL\) を用い
\[
 d=(E'-E)/2,\quad E_1=E+d,\quad E_2=E+2d=E',
 \quad \eta_d=e^{-d/(4kJ)}.
\]
内部cutoffはE'以下であり、正本のE'を \(E+J\log^2(nr/\zeta)\) 等に増やしていない。
D4を片側normへ移すと
\[
 \|R_hP_E\|\le K(J|h|)^4(E'+nJ\eta_d^2). \tag{D5}
\]

exact U(v)は各energy projectorと可換である。二挿入項にP_{E_1}+Q_{E_1}を一度挿入し、
左のB_hへの出力cutをE_2に取る。D1/D2/D4より
\[
 \|B_hU(v)D_3P_E\|
 \le K^2h^2J^4(E')^2+2K^2h^2n^2J^6\eta_d. \tag{D6}
\]
低energyを外れる第二項を捨てない。
この評価では \(\|H_+\|\le nJ\) も使える。cutoffがnJを越える場合、そのprojectorは全空間となり対応するtailはゼロ。
したがって中間のcutoffを \(\min(E_i,nJ)\) で評価すれば同じD6で足りる。

## 5. Duhamel二回で有限剰余を閉じる

\[
 A(t)=-i\int_0^tU(t-s)D_3U(s)\,ds.
\]
これは証明内の演算子で、実装oracle・状態入力ではない。
\(\widetilde U_h-U=-i\int\widetilde U_h B_hU\) を使い、その左側の差にもう一度同公式を適用すると、
\[
 \|(\widetilde U_h(t)-U(t)-h^2A(t))P_E\|
 \le |t|\|R_hP_E\|
 +\frac{h^2|t|^2}{2}\sup_{|v|\le|t|}\|B_hU(v)D_3P_E\|. \tag{D7}
\]
外側に残る \(\widetilde U_h\) はunitaryなのでnormを増やさない。
**ここで全Dyson次数のrestricted chainを別々に証明する必要はない。**
D5/D6を代入し、\(F=J^4E'|t|^5+J^4(E')^2|t|^6\) とすると、各nodeについて
\[
 \|(\widetilde U_{h_\nu}-U-(\nu r)^{-2}t^2A(t))P_E\|
 \le {K^2F\over(\nu r)^4}
 +K^2\left\{\frac{n(J|t|)^5}{(\nu r)^4}
 +\frac{n^2(J|t|)^6}{(\nu r)^4}\right\}\eta_d. \tag{D8}
\]
形式的なO記号ではなく、finite truncation・二挿入tailを保持した不等式である。
負のtにも積分の向きと絶対値を変えて同じ評価を使う。H_+を負にしてPSD補題を使い直すわけではない。

## 6. 定数と正本step条件の照合

固定wordの指数係数について \(|a_v|\le1\) の表示ならM26のc_*をそのまま使う。
一般の固定係数なら指数を同じfragment上の有限個の等価な指数へ分けて証明でき、
\(c_*=N_f\lceil\max(1,\max_v|a_v|)\rceil\) を保守的なstage定数に取れば足りる。
これは同じS_2の恒等的表示で、PF・係数の探索や回路compileではない。

次は一つの十分な、意図的に緩い選択である。数値計算していない。
\[
 a_0=4+\lceil\log_2(360K^2)\rceil,
\]
\[
 C_0=\left\lceil\max\left\{4,\ 8ka_0,\sqrt{24\kappa},
 \sqrt{96e^3c_*k}\right\}\right\rceil,\qquad C=K^2. \tag{D9}
\]
これらはkと固定wordだけに依存し、n、粒子数、E、t、r、ζには依存しない。
正本step条件からr≥4、nr≥2、q_0≤12L、および
\[
 J|h_\nu|\le(C_0^2L)^{-1}
\]
が従う。D9によりM26の \(|h|\le[8e^3c_*q_0kJ]^{-1}\) と
\(\kappa J|h|q_0\le1/2\) の両方が成立する。

D8のtailは \(J|t|\le r\) を使って
\[
 6K^2(nr)^2\left(\frac{nr}{\zeta}\right)^{-C_0/(8k)}\le\zeta/240
\]
と抑えられる。D3を加えると各nodeの共通係数後の残差は
\(K^2F/(\nu r)^4+\zeta/20\) 以下。
\((4/3)/4-1/3=0\) で同じ \(t^2A(t)\) を相殺し、最後に残差だけを絶対値で足すと
\[
 \|(X_r-U)P_E\|
 \le {5K^2F\over12r^4}+\frac{\zeta}{12}
 \le {CF\over r^4}+\zeta. \tag{D10}
\]
正本と同じE'、r-domain、二つの時間次数で閉じる。
定数は最適でも実用的でもなく、資源優位の証拠にはならない。

## 7. 判定の射程

以上は(A+)と符号化上のlocality・PSDを満たす標準解釈での、既知定理と有限の代数操作による直接還元。
L08 Theorem 32をP_Eへ誤適用する経路や、単独PFの誤差の加算だけの経路は使っていない。
指定sectorへの入力制限は、全low-energy入力に対する上界の右にsector射影を掛けて得る。

任意の相殺fragmentやsector圧縮だけのPSDまで正本が含むかは、条件の明確化事項として残る。
この不足を埋めるために元の正本を変更したとは扱わない。
一般の外挿次数、L08のopen question全体、実用的な定数、総E0費用、論文priorityは解決・認定していない。
