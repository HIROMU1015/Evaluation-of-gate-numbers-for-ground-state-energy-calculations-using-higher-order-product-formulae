# CG／Paldusへの実操作対応と保証範囲

2026-10-17 JST。**判定：確認（理想unitaryとしての構成対応）。**
占有符号化・符号・label・multiplicity・phase・逆変換を明示する。
実際のgate列生成、有限精度compile、resource測定は行っていない。

## 1. 必要なlabelと可逆符号化

元入力はtargetのN個の占有と、補助pair label \(p<q\)。
pairをM個のb-modeのweight-2 occupationへ写すEは、既知の整数labelの可逆符号化である。
有効code上では元labelとweight-2 bit列は一対一。labelのcopyや中間workは逆写像で消せる。
target全振幅、未知のground、gap、化学固有値を読んで構成する変換ではない。

次にall-a then all-bのcreation順から
\((a_1,b_1,a_2,b_2,\ldots,a_M,b_M)\)へ直すFを適用する。
普通のwire permutationだけでは足りず、

\[
F:|n;m\rangle\longmapsto
(-1)^{\sum_{i<j}m_i n_j}|n_1m_1\cdots n_Mm_M\rangle
\tag{G1}
\]

とする。b_iをa_j（i<j）の手前へ動かすときの占有対の数を数えた符号である。
fermionic SWAP又は可逆parity演算でこの既知符号を生成する仕様になる。
u,vではそれぞれ−,+なので、これを省くと指定入力の二つのweight間のcoherenceも変わる。

一つのsiteのlocal空間は

| occupation | local spin／magnetization | Paldusで保持する区別 |
|---|---|---|
| 00 | 0,0 | empty |
| 10 | 1/2,+1/2 | single |
| 01 | 1/2,−1/2 | single |
| 11 | 0,0 | double |

doubleとemptyは同じspin 0でも別の状態。N／weight／path labelからこの区別を捨てない。
local \(a_i^\dagger b_i\)は01を10へ正符号で写し、00と11では0。
従って(G1)の後は、singleの通常のspin結合で(C12)のSを得られる。

## 2. 「CGで対角化する」の具体的意味

簡明な経路はwをcoherentに記録し、そのweightのsingle siteを昇順に結合する方法。
singleのspin列\(\sigma\)を、既知のCG変換Tで

\[
|w\rangle|\sigma\rangle\longmapsto
\sum_{S,\nu}c_{S\nu}(\sigma)|w\rangle|S,m,\nu\rangle,
\tag{G2}
\]

へ写す。\(\nu\)は全てのintermediate spinのpathであり、multiplicity空間を保つ。
総spin Sだけを残して他の情報を消す写像ではない。
r=0のS=1/2は5コピー、S=3/2は4コピーあるので、この区別なしではunitaryにならない。

各spin-1/2の追加は、既結合spin jと新しいtotal magnetization tについて、次の実係数を使う。

\[
|j+\tfrac12,t\rangle
=\sqrt{\frac{j+t+1/2}{2j+1}}|j,t-\tfrac12\rangle|\uparrow\rangle
+\sqrt{\frac{j-t+1/2}{2j+1}}|j,t+\tfrac12\rangle|\downarrow\rangle,
\]
\[
|j-\tfrac12,t\rangle
=-\sqrt{\frac{j-t+1/2}{2j+1}}|j,t-\tfrac12\rangle|\uparrow\rangle
+\sqrt{\frac{j+t+1/2}{2j+1}}|j,t+\tfrac12\rangle|\downarrow\rangle.
\tag{G3}
\]

これで本資料のCG位相規約を固定する。存在しないj−1/2、範囲外のmagnetizationは使わない。
係数対のnormと直交性により、各段は既知の2成分回転と可逆label更新で実現するunitaryとなる。
spin-0追加はspinとmagnetizationを変えず、empty／doubleというlabelを保持する。
CGをcascadeしてmultiplicityを残す操作の入出力はBacon–Chuang–Harrow §IV.1–IV.2に対応する。[L1]

full Paldusを直接使う経路でも同じ情報が残る。
その論文のnotationとの対応は、空間軌道数d=M、総粒子数\(N_{\rm paper}=N+2\)、
spin \(S_{\rm paper}=S\)、spin projection \(M_{\rm paper}=m\)、残りのGT step vector \(\boldsymbol d\)がmultiplicity／orbital情報。
\(|N_{\rm paper},S,M_{\rm paper};\boldsymbol d\rangle\)を別registerのlabelへ写し、
3phaseはSにだけ依存させ、\(\boldsymbol d\)にはidentityを作用させる。
論文のTable I、II.F Eqs.(10)–(12)、III.A Eq.(14)のempty／double及びCGの区別がこの入出力を与える。[L2]
一般のspin-free化学Hがこの変換だけで対角化されるとは言わない。今回のJがSだけの関数であることが追加の根拠。

## 3. M=5・N=3の明示的CG path

以下は(G3)の係数を掛けて手で得た表であり、行列生成・数値対角化ではない。
\(v_{\rm loc}=|\uparrow\uparrow\uparrow\downarrow\downarrow\rangle\)、
\(x_{\rm loc}=|\downarrow\downarrow\uparrow\uparrow\uparrow\rangle\)。
vで係数が非零のpathでは、最初の三段が\((j_1,j_2,j_3)=(1/2,1,3/2)\)。
Paldusのstep符号は、spin上昇を10、下降を01と書く（物理occupationのup/downと混同しない）。

| \((j_4,S)\) | 全step符号 | \(c_\nu(v_{\rm loc})\) | \(c_\nu(x_{\rm loc})\) |
|---|---|---|---|
| (1,1/2) | 10,10,10,01,01 | \(1/\sqrt2\) | \(1/(3\sqrt2)\) |
| (1,3/2) | 10,10,10,01,10 | \(1/2\) | \(-1/3\) |
| (2,3/2) | 10,10,10,10,01 | \(\sqrt{3/20}\) | \(-1/\sqrt{15}\) |
| (2,5/2) | 10,10,10,10,10 | \(1/\sqrt{10}\) | \(1/\sqrt{10}\) |

xにはこの4本以外のpathもあるが、vの係数が0なので\(\langle x|P_S|v\rangle\)には寄与しない。
例えば最初の行のv係数は\((\sqrt3/2)\sqrt{2/3}=1/\sqrt2\)。
x係数は\((1/\sqrt3)(-1/\sqrt2)(-1/\sqrt3)=1/(3\sqrt2)\)。
S=3/2の二つのpathの積は\(-1/6-1/10=-4/15\)。
これが[小例 §4](small_example_and_control.md)のprojector overlapを与え、Jの直接作用と比較できる。

uのlocal状態は\(-|\mathrm d\,\mathrm d\,\uparrow\,0\,0\rangle\)。
Paldus labelは\((N_{\rm paper},S,M_{\rm paper})=(5,1/2,1/2)\)、step符号は11,11,10,00,00。
前のminusは(G1)に由来し、phase後にFの逆で戻る。u全体には正しい\(e^{-i\theta/3}\)だけが残る。

## 4. phaseと逆変換までの作用

\(Q=TFE\)（wと全multiplicityを保持する有効code上の変換）と置く。

\[
D(\theta)|w,S,m,\nu\rangle
=e^{-i\theta\lambda_S}|w,S,m,\nu\rangle,
\qquad U=Q^\dagger DQ.
\tag{G4}
\]

M=5・N=3では\(\lambda_S=(1/3,-2/3,1)\)。
全weightで同じSの全multiplicityへ同じphaseを掛ける。
Dは有効labelの値を変えずphaseだけを掛けるため、Qのimageを保存する。
従って逆変換をimage外へ勝手に拡張した説明ではなく、任意の角度でQの逆を使える。
抽出imageを保存しなかった普通SWAPとの相違は、この不変性にある。
逆CG、逆fermionic permutation、pair labelへの逆符号化を順に行い、w計算等の補助workを戻す。
出力のtarget／補助は再びN／2粒子。未知のexp(J)をprimitiveにしてはいない。
full Paldusを使う場合も、Tを対応する既知Paldus変換として\(Q^\dagger DQ\)を同じように解釈する。

制御版ではQは両control枝で共通に作用させ、Dを1枝だけに作用させる。
0枝の\(Q^\dagger Q=I\)を保ち、scalarを含むD全体を制御する。
weight又はpathを測定したり、multiplicityを0へ捨てたりしない。
指定入力の有限角度control overlapとscalar脱落の反例は[小例 §5](small_example_and_control.md)。

## 5. 小例と一般保証を区別する

| 保証 | 根拠／限界 |
|---|---|
| 指定小例の次元・固有値・CG係数・coherence・control | この3資料の手での導出。M=5・N=3の指定状態を具体的に照合 |
| 一般M,Nの演算子恒等式 | [CAR再導出](independent_car_derivation.md)の(C5)–(C13)。小例からの推測ではない |
| 一般M,Nの理想CG還元 | 各weightのspin-1/2／spin-0分解、全path保持、(G3)の再帰と(G4)。存在sectorだけを使う |
| 既知回路との接続 | L1/L2のlabel入出力と既知CG回転へ対応。全文証明・全resource tableの再査読ではない |
| 実装・有限精度・費用 | 未検証。compile、回路列、hardware noise、rho2準備・reset費用、資源優位は実施していない |
| 元Hの絶対E0 | この還元だけで取得できたとはしない。scalar・一体項・残余・state overlap等の既存条件を維持 |

今回の対象還元を撤回又は訂正すべき演算子上の矛盾は見つからなかった。
未検証の実装価格や全文献調査を、演算子還元そのものの未解決性と混同しない。
新アルゴリズム探索や既存停止系列の再開へ自動で進まない。

[L1]: https://arxiv.org/html/quant-ph/0601001v1
[L2]: https://arxiv.org/pdf/2506.09151v2
