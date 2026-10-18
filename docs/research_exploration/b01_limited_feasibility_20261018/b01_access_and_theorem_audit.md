# B-01：accessと公表定理の限定照合

2026-10-18 JST。新しい認証法・回路・filterは構成していない。固定Phase Bの[課題カード](https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/ed6781f7004444ce77b2378303404fd23efbbc95/docs/research_exploration/e0_open_gap_survey_20261018/candidate_problem_cards.md)に対する技術調査である。文献IDと本文箇所は[literature registry](literature_registry.json)。公表定理の引用と、本作業による既知式の適用を以下で区別する。

## 1. 記号・誤差・対象

元の有限基底電子H、scalar・一体項・二体項・係数規約・指定電子sectorを保持する。`Hbar=(H-aI)/b`を使うなら既知係数からa,bを求め、絶対値は`E0=a+b Ebar0`へ戻す。`epsilon_bar=epsilon_Ha/b`、`t_physical=t_bar/b`であり、以下は正規化単位の式。近似モデル誤差、simulation bias、統計誤差、準備誤差を省略しない。

etaはground **population** の保証付き下界、真の重みp0とは別。sigmaは`[e-sigma,e+sigma]`の半幅（区間長2sigma）であり、真のgapではない。T_maxは一回のcoherent操作中のevolution時間、native depthではない。複数evolutionをcoherently連結する場合は絶対時間の和を数える。

## 2. 公表認証法のインターフェース

[L01：Wang–Stilck França–Rendon–Johnson](https://arxiv.org/pdf/2304.09827v2) Theorem5.2、Algorithm4、AppendixC、§6を再読した。入力は正規化H、反復準備可能なseed、既知eta>0、`|e-E0|<=sigma`、精度・失敗確率。推定本体Theorem2.3/3.7はgap下界Deltaを用いるが、認証ではその入力を外す。

認証の決定部分はGaussian畳込みの端の質量と、中央窓内の条件付き平均・二次中心momentを検査する。§5.1/AppendixBの実現はQET-UによるGaussian関数のblock-encodingと拒否標本化。公表費用`Otilde(eta^-3 epsilon^-4 log(delta^-1))`は期待Gaussian filter呼出し数である。各呼出しに`Otilde(sigma^-1)`のcoherent evolutionとfresh seedが必要で、通常のHadamard一shotとは異なる。

対して推定本体の公表回路数は`Otilde[eta^-1 (Delta^2 epsilon^-2 + log(Delta^-1)) log(delta^-1)]`、T_maxはOtilde(Delta^-1)。Deltaは保証されたgap下界であり、coarse半幅sigmaへ無条件置換できない。いずれも実行時間・native費用の全体値ではない。

## 3. Soundnessとcompletenessを分ける

公表Theorem5.2の主張は、粗い区間とetaの前提下での誤受理制御である。本調査では次のeventとして読む。

\[
\Pr(\mathrm{ACCEPT}\ \land\ |E_{\rm out}-E_0|>\epsilon)
\leq\delta_{\rm test}.
\]

`Pr(wrong | ACCEPT)<=delta_test`とは同じでない。後者の単純な変換には受理確率による割り算が入る。常時REJECTは前者を満たすが、完備性を満たさない。

AppendixのTheoremC.5は、内部精度epsilon_cで`|M-E0|<=4 epsilon_c`を記す。最終epsilonと対応させる際は例えばepsilon_c=epsilon/4として定数を揃える。主定理とAppendixのepsilonを同じ記号だから同じ許容誤差としない。

LemmaC.6の公表十分条件は、真のgapに対し概ね

\[
\sigma\leq\frac{\Delta_{\rm true}}
 {10\sqrt{\ln(2\eta^{-1}\epsilon_c^{-1})}}
\]

となる領域での受理である。主定理はより保守的なlog表現を使う。これは成功する入力classの条件であり、テストに真のgapを入力する意味ではない。任意に短いT_maxで全seed・全gapの受理を保証していない。p0=1等ではより短時間でも受理し得るが、それを一般seedへ移送しない。

## 4. D1の記録が与える情報

これはL02/L04の既知Hadamard/Fourier式の対応であり、新生成規則ではない。seedのスペクトル重みをpjとすると

\[
\chi(t)=\langle\psi|e^{-iHt}|\psi\rangle
       =\sum_jp_j e^{-iE_jt},\qquad
\Pr(B=b\mid t,A)=\frac{1+b\,m_A(t)}2,
\]

ここでb=±1、位相規約を揃えたX/Y軸について`m_X=Re chi`、`m_Y=Im chi`。時刻・軸は古典的に選べ、各結果にはfresh準備が必要である。χだけが見える測定ではseedの重み0の固有成分は現れない。係数を知る全古典・量子手順の不可能性を意味しない。

Gaussian畳込み`g_sigma=p*n_sigma`は

\[
g_\sigma(x)=\frac1{2\pi}\int_{\mathbb R}
e^{itx}e^{-\sigma^2t^2/2}\chi(t)\,dt
\]

であり、[L04：2209.06811v3](https://arxiv.org/pdf/2209.06811v3) §2/Algorithm1が既知の一般convolution推定を与える。記録から必要な線形汎関数を有限精度で評価する道はある。したがって「D1には認証情報が全くない」とは判定しない。

ただし、`g_sigma(x)`の評価、成功確率に従うBernoulli結果、`X~g_sigma | I`の**標本そのもの**は違う。L01のfilter成功確率は`sum_j pj |f_x(Ej)|^2`であり、成功時の条件付き法則を使用する。χの同じ線形情報からその量を再構成できても、同じ分散・準備数・成功条件付き標本が無料で得られるわけではない。

例えば、Iを固定し、`a_k=integral_I (x-e)^k g_sigma(x) dx`、q=a0と置く。条件付きmean/varianceはa1/q、a2/q−(a1/q)^2に依存する。既知convolution法で各a_kを評価する際にも、そのFourier重みのL1量、打切りbias、古典積分費、**qによる正規化誤差**が残る。[統計照合](b01_standard_statistics_screening.md)で分離する。

## 5. 同条件の強い対照

| 公表対照 | 合法access・主な条件 | 保証とB-01との差 |
|---|---|---|
| L02 Lin–Tong Corollary3 | fresh seed、controlled evolution、Hadamard、既知eta | gap不要のE0保証あり。ただしepsilon精度ではT_max=Otilde(epsilon^-1)、総時間Otilde(epsilon^-1 eta^-2) |
| L03 QCELS Theorem2/3 | Hadamard記録、高ground重み、または既知filter区間でrelative overlap>0.71 | depth短縮の既知保証。relative overlapと区間位置を未知gapの代わりに無料付与しない |
| L04 Wangほか2023 | 時刻の古典samplingとHadamard convolution | gap下界を使うlow-depth推定本体は既知。Algorithm4への情報接続は可能でも、η依存や条件付き標本費が同じとは限らない |
| L01 Wangほか2025 | QET-U/filterをcoherently実行し成功条件で採択 | 未知gap認証の強い公表対照。今回の優先D1 accessに含めない |
| L05 Jeffery–Witteveen2026 | controlled A/A†、U/U†、既知振幅gamma=sqrt(eta)、transducer | 総U queryはO((gamma epsilon)^-1 log(delta^-1))。fresh短時間記録の定理ではない。U=evolutionの実現も可能でありqubitization専用として排除しない |
| L06 Somma–de Wolf2026 | guiding-state oracle、一般H oracle、十分な次元 | matching総query下界。既知電子係数・固定T_maxの記録模型への下界移送は未実施 |

B_pubは公表操作とpromiseを保持する。B_fairには同じH・seed・etaの根拠・粗い区間・confidence・古典情報を与え、標準統計と既知の古典上下界も許す。D1外の強い対照を隠さず、D1側へそのfilter・A†を無料移植しない。今回は候補の核心が存在せずB_plus_coreも作らない。

## 6. 判定できた範囲

soundnessとcompletenessの公表インターフェース、およびD1で見える量は具体化できた。一方、必要精度の全汎関数を同時に得てN_targetを満たすD1内の手順・保証は未構成である。Theorem5.2をそのままHadamard shot数の保証とはしない。無条件のD1 NO-GOも証明していない。

公表Appendixの正規化・window条件を含む全証明を独立認証したという意味ではない。特にCorollaryC.4は未正規化momentを扱い、条件付きmomentへの移植にはqを落とせない。また同Corollaryの`|e±L|<=1`という正規化条件も要確認である。本調査は論文の訂正定理や反例を作らず、これらを移植時の未確認事項として残す。
