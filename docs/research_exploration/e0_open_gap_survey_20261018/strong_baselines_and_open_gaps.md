# 強い既知対照と残る条件

本文で確認した事実を以下に集約する。版・本文箇所・hash・限定した読取範囲は[literature registry](literature_registry.json)、検索と未取得範囲は[literature provenance](literature_provenance.json)を参照する。引用は一次資料だけを根拠とした。ここでいう「残る」は各定理の条件との差であり、世界全体の未解決を意味しない。

## 記号と比較モデル

`eta <= p0=||Pi0 psi||^2`は確率重みの下界、`gamma=sqrt(eta)`は振幅下界、epsilonはエネルギー精度、deltaは失敗確率。`T_max`は一回のcoherent evolutionの時間費用、`T_sum`は総時間であり、native depthと同一ではない。QET-U等で一回に複数evolutionを使う場合は、その絶対時間の和をT_max側にも数える。公表論文のproxyと実装費用を区別する。

## L01：Wang–Stilck França–Rendon–Johnson

[2304.09827v2](https://arxiv.org/pdf/2304.09827v2)、PRA111,012426 (2025)、Theorem2.3/2.6/5.2、Algorithm4、AppendixC、§6を確認。スペクトル[0,pi]、非縮退ground、準備psi、既知eta、controlled exp(iHt)を使う。推定本体は既知gap下界Deltaで

\[
N_{\rm est}=\widetilde O\!\left(\eta^{-1}
(\Delta^2\epsilon^{-2}+\log\Delta^{-1})\log\delta^{-1}\right),
\qquad T_{\max}=\widetilde O(\Delta^{-1}).
\]

認証はgap下界を不要とするが、粗い推定`|Ehat-E0|<=sigma`とetaを必要とする。Gaussianを拒否標本化し、局所のpeak・条件付き平均/分散を検査する。Theorem5.2の公表上界はGaussian filter呼出しの期待数`Otilde(eta^-3 epsilon^-4 log(delta^-1))`。一呼出し時間は`Otilde(sigma^-1)`。誤受理を抑え、sigmaが真のgapより十分小さいと受理する。実装はQET-Uによる関数のblock-encodingを明記する。§6は認証費用改善を将来課題とする。これは上界であり、必要費用の下界ではない。

## L02/L03：D1に沿うspectral-record法

[Lin–Tong 2102.11340v2](https://arxiv.org/pdf/2102.11340v2)、Corollary3/§4–5：一ancilla Hadamard記録からFourier CDFを作り、eta付きしきい値で反転する。既知etaでgap不要のE0保証を持つ。`T_sum=Otilde(epsilon^-1 eta^-2)`、`T_max=Otilde(epsilon^-1)`。粗いsigma精度の取得も無料でない。etaを知らずに未観測の低energy重みを排除したとはしない。

[Ding–Lin QCELS 2211.11973v2](https://arxiv.org/pdf/2211.11973v2)、Theorem2/3・Corollary4：時刻を段階的に延ばして複素指数least squaresを解く。高いground重み、またはfilter区間のrelative overlap >0.71と分離幅の条件でdepthを短縮する。小gapでも成立する場合がある。これらのrelative overlapと区間位置は、未知gapの代わりの追加条件であり、今回の候補へ無料で付与しない。

## L04/L05：gapや重み推定を避ける実用手順

[Kissほか2405.03754v2](https://arxiv.org/pdf/2405.03754v2)、Quantum9,1682 (2025)、§3–4：CDFのinflection/changepointで可視低energy集積を検出する。精度の理論保証にはoverlap情報が必要と本文に留保がある。低energy manifoldへの質量と元Hのground重みを区別する。

[Surana–Allen 2605.18876v1](https://arxiv.org/pdf/2605.18876v1)、§III/IV-B、Algorithm5：符号付きPauli係数のrandom compilation、Fourier対称性、binary segmentationを扱う。etaなしchangepoint節に、今回要求する全入力での`Pr(ACCEPT and |Eout-E0|>epsilon)<=delta`という定理は確認できなかった。これはその方式一般の不可能性や全ての保証の不存在の証明ではない。本文のeta付きbinary search保証とは分ける。

## L06/L07/L08：2026年の強いcoherent対照

[Jeffery–Witteveen 2608.24494v1](https://arxiv.org/pdf/2608.24494v1)、Theorem1.1/4.2：transducerでeigenphaseしきい値を判別しbinary search。制御付きA/A†とU/U†、既知振幅gammaで、U呼出し`O((gamma epsilon)^-1 log(delta^-1))`。A呼出しは`O(gamma^-1 log(epsilon^-1) loglog(epsilon^-1) log(delta^-1))`、追加qubitsは`O(log((gamma epsilon)^-1))`。総query最適性は、毎回fresh copyを測る固定短時間記録の保証ではない。これを「精度・重み依存の一般query改善が未解決」と再提示しない。

[Somma–de Wolf 2608.24493v2](https://arxiv.org/pdf/2608.24493v2)、主定理：十分な次元で上記query依存のmatching lower bound。任意の二体電子積分classや一回のdepth制約への下界移送は本調査では得ていない。

[2609.38091v2](https://arxiv.org/abs/2609.38091v2)はabstract/版履歴だけ確認。ground準備の後続は既知の近似energy・gap promise・A/A†を入力とする。未知gap認証を解いた証拠として用いない。全文・実装は未確認。

## L09：古典certificateも公平な対照へ入れる

[Wangほか2310.05844v5](https://arxiv.org/pdf/2310.05844v5)、PRX14,031006 (2024)、§I–II：変分上界とSDP緩和下界を組み合わせる公表法。必要な精度まで上下が閉じるinstanceは、gapなし認証の反例対照になる。有限のrelaxation費用で全電子Hamiltonianの幅が閉じる保証を本論文からは採用しない。

## B_pub / B_fairと判断の限界

**B_pub**は各論文の具体的操作と実際のpromiseを維持する。L01の認証は最も直接の対照だが、QET-Uを含むためD1内の実装案として採用しない。D1内の基準はL02/L03である。総queryの強対照L06を、U=evolutionで使えるのにqubitization専用だとして排除しない。

**B_fair**には同じH係数・準備access・etaの根拠・粗い区間・測定情報・confidence・費用範囲を与える。独立validation copies、適切なfailure配分、通常のconcentration改良・scaleを保つ既知のbound整理、合法な古典上下界を許す。L01の保守的な上界だけを弱い敵に固定しない。A†やfilterを許すclassと、Hadamard記録だけのclassは別比較にする。追加した記録はshot・準備・回路費へ加算する。

改善が標準的な統計の特殊化だけで得られるなら独立新アルゴリズムとは扱わない。どの標準改善まででgapが閉じるかは未判定。**B_plus_coreは作成していない**。新しい核心・候補アルゴリズムが今回存在しないためである。

文献上の根拠は「L01の2025年本文が明示する問い」。2026年のL05–L08では同じ低depth・未知gap・同じconfidenceとaccessの解消は確認できなかった、という限定結果に止める。検索で見つからないことを現在のopen problemの網羅証明にはしない。
