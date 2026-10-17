# 複数jump／cycle：紙上導出と限定障害

2026-10-18 JST。式は本作業の限定的な紙上検討。科学用記号計算・数値行列・simulation・回路compileは使っていない。priority認定、形式証明器の検証、詳細科学レビューではない。

## 1. 同じrank-one jumpの反復は障害を変えない

直交a,b、`L=|b〉〈a|`、`P_a=|a〉〈a|` の振幅減衰を考える。resetを毎回行い、各cosineを `z_j∈[0,1]` とすると、有限合成は同じa,bについて有効cosine

\[
z_{\rm eff}=\prod_j z_j
\tag{M1}
\]

を持つ振幅減衰になる。aの人口は `z_eff²` 倍、aと補空間のcoherenceは `z_eff` 倍、失った人口だけbへ移るからである。jumpのglobal phaseを変えても各チャネルは変わらない。

`z_eff<1` で全状態energy非増加を求める限り、前回[rank-one条件][E02]のsource固有state性は残る。**同じsource/target、毎回reset、追加unitaryなし**という文法だけの結論である。bath coherenceを保持するcycle、別jump、Hとの実時間発展やfeedbackを含む一般cycleは否定していない。

## 2. 全sourceを同じ率で減衰させる有限合成

[構成C6](coefficient_to_cycle_construction.md)の相互直交source x1=12,x2=23,x3=25と共通target b=34を使う。各KrausはC7。`P_i P_j=0` (i≠j)、`L_j|b〉=0`、`L_jL_i=0` より、二つ以上のjumpを含むtrajectory Krausは零。

no-jump積は

\[
\prod_j[I+(z-1)P_j]=I+(z-1)P=Q+zP.
\]

jump jの前のno-jumpはx_jへ恒等、後のno-jumpはbへ恒等なのでsingle-jump Krausは `−isL_j` のまま。これがC9を与える。bathをsubcycleごとにresetするため、異なるjump履歴をcoherentに足して `ΣL_j` 一本へ置き換えない。

完全性は

\[
K_0^\dagger K_0+\sum_jK_j^\dagger K_j
=Q+z^2P+(1-z^2)P=I.
\tag{M2}
\]

CPはKraus形から従う。各L_jは等しい電子数/各spin数のket間を移し、NとN↑/N↓を保存する。TPから `Φ*(cI)=cI`。scalar cを最終の絶対energyから省かない。

## 3. 境界hoppingを残したH5の全状態進捗

### 3.1 係数だけのoperator証拠

source内の対角energyはc−U,c−μ,c+ε5。U>μ、ε5≥0から対角部分は `(c−U)P` 以上。各Hermitian hopping `a_p†a_q+a_q†a_p` のnormは1以下で、係数付きの二項をtriangle評価すると

\[
PH_5P\succeq(c-U-t-|\tau|)P=(E_b+\delta)P.
\tag{M3}
\]

τの効果を0にせず、負のoff-diagonal coherenceを含む全source blockを評価した。source固有vector・固有値・gapは求めていない。

H5はn2,n4を保存するためPH5Q=0。C9のdualを直接展開すると

\[
\Phi^*(H_5)=QH_5Q+z^2PH_5P+(1-z^2)E_bP.
\]

従ってC10。各source ketはhoppingで別sourceへ結ばれるため、それぞれのrank-one subcycleには前回と同型の正のdrift方向がある。**各substepは加熱し得ても、同率で全sourceを覆ったcycle全体は下降する**。これはsubstepのdriftを元stateで単純加算した計算ではなく、合成Krausからのexactな結果である。

### 3.2 複数cycle

`p0=Tr(Pρ0)` とすれば

\[
\operatorname{Tr}(P\Phi^m(\rho_0))=z^{2m}p_0,
\]
\[
\operatorname{Tr}(H_5\Phi^m(\rho_0))
=\operatorname{Tr}(H_5Q\rho_0Q)+z^{2m}\operatorname{Tr}(H_5P\rho_0P)
+(1-z^{2m})E_b p_0.
\tag{M4}
\]

したがって累積下降は少なくとも `δ(1−z^(2m))p0`。Q内の元population/coherenceは冷却されず、cross P/Qはz^m倍になる。sourceを空にすることとgroundへ収束することを混同しない。

### 3.3 真の低energy spectral weightへの接続

N=2全空間で対角部分の最小値はE_b、hopping norm上界はrなので

\[
H_5\succeq L I,\quad L=E_b-r,
\qquad E_0\le E_b.
\tag{M5}
\]

`E_cut=E_b+δ/2` とし、`Π_low=1_(−∞,E_cut](H5)` を**証明上だけ**使う。M3よりsourceの全スペクトルはcutoffより上なので `Π_low P=0`。bのenergy平均E_bと下界Lから

\[
g_{\rm low}:=\langle b|\Pi_{\rm low}|b\rangle
\ge\frac{E_{\rm cut}-E_b}{E_{\rm cut}-L}
=\frac{\delta}{2r+\delta}>0.
\tag{M6}
\]

これは既知の一次moment/tailの初等的評価。新規性にしない。C9から

\[
\Phi^*(\Pi_{\rm low})-\Pi_{\rm low}
=(1-z^2)g_{\rm low}P,
\]
\[
\operatorname{Tr}(\Pi_{\rm low}\Phi^m(\rho_0))-
\operatorname{Tr}(\Pi_{\rm low}\rho_0)
\ge\frac{\delta}{2r+\delta}(1-z^{2m})p_0.
\tag{M7}
\]

実行時にΠ_low・E0・正しいbranchを入力していない。ground projector Π0もPと直交するので同形の不減identityはあるが、`〈b|Π0|b〉` の有用な下界・groundへの収束率は今回示していない。M7のcutoffはE0+所望精度とは限らない。

### 3.4 Spin sectorと絶対E0の範囲

上のM3–M7はfull N=2・10次元を対象とし、便宜的sectorの最小値へ無断に置換していない。さらに1,3,5=↑、2,4=↓なら、N↑=2,N↓=0の対角部分はc−μ以上、hopping補正は高々rなのでそのenergyはc−μ−r以上。`U+μ−r>U−μ>0` よりE_bより高い。N↑=0,N↓=2の唯一のket24もenergy c−μ>E_b。従ってこのclassのglobal N=2 groundはN↑=N↓=1にあり、その中でもQ側にある。

一般分子/別sectorについてこの包含を認定したものではない。模型自体は一般ab initio Coulomb入力を網羅しない。

## 4. 部分空間reset文法の正確な全状態条件

任意の既知P、Q=I−P、既知b∈Q、`E_b=〈b|H|b〉` に対してC9を定義すると

\[
\Delta_H:=\Phi^*(H)-H
=-(1-z^2)(PHP-E_bP)+(z-1)(PHQ+QHP).
\tag{M8}
\]

0≤z<1に限れば

\[
\Delta_H\preceq0
\quad\Longleftrightarrow\quad
PHQ=0\ \text{かつ}\ PHP\succeq E_bP.
\tag{M9}
\]

十分性はM8。必要性は、Q上の対角blockが零であることから分かる。PHQ≠0ならQのvとPのuを選び、対応する圧縮は非零off-diagonalと零のQ対角を持ち、determinant<0となる。P上のテストはPHP≥E_bPを要求する。

rank-oneの固有state条件は、ここでは**部分空間の不変性**へ移った。内部sourceを同率で減衰すれば固有basisを要しないが、任意のboundaryを無条件に吸収できるわけではない。この必要条件はC9型に限り、多target/feedback/別cycle一般のNO-GOではない。

## 5. Source flagを変えるhopping：残る障害と限定input

\[
H_\eta=H_5+R_\eta,\quad
R_\eta=\eta(a_4^\dagger a_2+a_2^\dagger a_4),\quad\eta\ne0.
\tag{M10}
\]

これはNとN↑/N↓を保存するが、P/Qを混ぜる。特に `R_eta|34〉=−η|23〉` なので `PH_eta Q≠0`。`PR_eta P=QR_eta Q=0`、対角E_bは不変。固定cycleは

\[
\Delta_{H_\eta}=-(1-z^2)(PH_5P-E_bP)
+(z-1)(PR_\eta Q+QR_\eta P).
\tag{M11}
\]

となり、M9から全状態のcycle単調性は不成立。occupation hopping graphのclosureをさらに広げると、N↑=N↓=1の6配置が全て連結しtarget bも含む。**b∈Qを保ったまま、このcomponent-closureだけでsourceを拡大する文法は止まる**。別の非自明projectorを未知spectral情報から無料取得して回避しない。

### 5.1 Block-diagonal inputなら反復energy下降は残る

`PρQ=0` のinput classでは交差項の期待値が零。C9自体もこのclassを保存する。したがってlogical cycle列だけなら、H_etaという元の非可換Hを評価しながら、M3/M4と同じenergy下降が全mで成立する。occupation productやP/Qの既知classical mixtureはこの条件を満たす。

ただしC9はR_etaが好むP/Q coherenceを生成しない。得るenergyはtargetの試行値に留まり得る。**H_etaの実時間発展を途中で入れる場合、このinput classは一般に不変でなく、同じ反復保証を適用できない**。自然なsystem–bath coolingとlogical gate channelの違いを隠さない。H_etaのground weightや低cutoffのM7も自動移植しない。

### 5.2 Coherenceを許すinputの十分条件

一般Hで `A=PHP−E_bP≽δ_R P`、`b_R=‖PHQ‖`、`p=Tr(Pρ)` とする。positive ρのCauchy–Schwarzより

\[
\operatorname{Tr}(\rho\Delta_H)
\le-(1-z^2)\delta_R p+2(1-z)b_R\sqrt{p(1-p)}.
\tag{M12}
\]

`a=(1−z²)δ_R>0`、`b=(1−z)b_R` と置けば `p≥4b²/(a²+4b²)` は一cycle非増加の十分条件。H_etaではδ_R=δ、b_R≤|η|という係数証拠を使える。pやtightなcoherence boundを測って使うならcopies/読出しの取得費と別承認が必要。sourceが減る反復へこのthresholdを無条件に継続適用しない。

## 6. 実装誤差と否定した範囲

理想cycleと実装cycleのdiamond差がε_ch以下、`B_H≥‖H−cI‖` なら、一cycleのenergy差のずれは高々B_H ε_ch。m cycleの粗いtelescoping誤差はm ε_chを使えるが、収束時の厳密単調性を自動保持しない。bath reset・gate drift・parity・angle・sector leakageを予算化し、数値は今回設定しない。

否定したのは、同一rank-one resetの細分化と、固定C9型をPHQ≠0の元Hで全状態単調とする主張。一般の複数jump/cycle、有限加熱、別の入力class、coherentなbathやfeedbackは否定していない。

[E02]: https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/b7ec04fb84cd01eb846b9e3cc6d545bdf833e657/docs/research_exploration/collective_transition_initial_construction_20261017/noncommuting_paper_verification.md
