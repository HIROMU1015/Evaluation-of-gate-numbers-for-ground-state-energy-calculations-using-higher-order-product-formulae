# B-01：etaと粗いenergy区間の取得条件

結論：既知etaを前提とする数学問題と、実用電子Hへの接続を分ける。既知の取得経路はあるが、前回カードのHubbard ladderや一般分子に対し、正のetaと有用な取得費を今回確立したわけではない。参照版は[literature registry](literature_registry.json)。

## 1. 条件付きの枝

固定seedについて`p0=||Pi0 psi||^2>=eta>0`が保証されるなら、L01/L02の公表前提として使える。その保証がpromiseなのか、係数だけの証拠なのか、確率的な取得結果なのかを区別する。確率的ならdelta_etaを全体失敗確率に加える。

「HFだから大きい」「有限サイズだから非零」「正規化した一様重ね合わせだからeta>=1/dimension」は保証にならない。同じN・Szでもspin等の違いや振幅相殺があり得る。FCI groundとの内積や、正解を使って調製したseedは取得経路として採用しない。

## 2. 既知のenergy/fidelity経路：必要な下界を明示する

[L11：Hangleiterほか](https://arxiv.org/pdf/1602.00703v4)の既知energy–fidelity評価は、既知ground energyとgap下界を用いる。親Hamiltonianのgroundを保証しても、それが元電子Hのgroundである根拠がなければD2のetaではない。

次は同じスペクトル分解による既知の評価を、上下界入力へ紙上適用したもの。元sectorで`L0<=E0`、`L1<=E1`、seed energyの上界EUを保証し、`L0<L1`かつ`EU<L1`なら

\[
\langle H\rangle\geq p_0L_0+(1-p_0)L_1,
\qquad
\eta=\frac{L_1-E_U}{L_1-L_0}\leq p_0.
\]

L1は**第一励起energyの保証付き下界**であり、Ritzの第一励起energy上界ではない。EUはseed期待値の上界。L0/L1/EUの生成・独立確認・精度とbit費を支払う必要がある。L1とground上界が同時に得られる経路はgap下界も与え得るため、その場合に未知gap認証を追加する価値は別途示す必要がある。

既知minmax/摂動評価の限定した十分条件もある。既に与えられた同sectorの可解な一体参照H_refに、既知ground energy e0、励起energy e1、準備可能なSlater ground Phi、`g_ref=e1-e0>0`があり、元Hを正確に`H=H_ref+V`と書けるとする。係数から保証する`B>=||V||`について、L0=e0−B、L1=e1−B、EU=e0+<Phi|V|Phi>を上式へ代入できる。粗い十分条件は`2B<g_ref`で、`p0>=1-2B/g_ref>0`となる。

これは新しい準備法・family・証明機構の構成ではなく、既知minmaxと上のenergy評価の十分条件の代入である。元HのVを捨てない。一体対角化・sector内level確認・係数norm bound・Slater準備・Wick期待値評価の費用が必要。密な二体係数の単純走査は入力規模O(m^4)、一体対角化は通常O(m^3)算術操作の規模だが、誤差認証・bit数・状態合成は別計上する。一般の強相関HではBが大きく条件が空になることがある。今回、特定分子やladderへの代入・数値確認はしていない。

## 3. 2026年のmoment/窓重み認証

[L09：Lin–Izmaylov 2503.12224v2](https://arxiv.org/pdf/2503.12224v2)は有限momentと保証付きspectral intervalから、窓のindicatorを上下から抑える多項式をLP/SDPで求める。公表誌の書誌はPRA114,042432、2026-10-16。今回読んだ本文はarXiv v2であり、出版版本文の同一性は未確認。

この経路はFCI固有vectorを必須としないが、窓に複数levelが入れば保証するのは**窓全体の重み**である。groundだけのetaとするには他levelを排除するspectral enclosureが必要。論文§II-Cはground窓と励起側の分離した囲いを前提としている。

momentが近似なら真のmomentを含む保証も必要。同論文§II-E/B.1のphysicalityへの射影だけで、元seedの真のmomentが保証付きで回復したとはしない。例えば既知のfeasible minorant `p_minus=sum_k c_k T_k`と同時誤差`|Mhat_k-M_k|<=zeta_k`があれば、通常の区間評価により

\[
P_I\geq\sum_k c_k\widehat M_k-\sum_k|c_k|\zeta_k
\]

と評価できる。これは線形誤差伝播であり、新しいSDP法の提案ではない。係数の可行性・丸め誤差も別に確認する。moment取得、spectral囲い、SDPと証拠検証、seed準備の総費用を0にしない。Hadamard記録から高階momentを無料取得できるとも扱わない。今回はsolver・moment計算を実行していない。

## 4. Hubbard関連の既存準備：推定値と証拠を分ける

[L10：Watanabe–Fujii 2609.15764v2](https://arxiv.org/pdf/2609.15764v2)はhalf-filled二次元Hubbardに対し、dimer/Heisenberg参照とSW由来charge操作を使う公表準備法である。§III-Bでは参照のfidelityをenergyとsinglet gapから評価し、回路とのfidelityと合成する。

本文は真のenergy/gapで評価した場合の厳密性を明示する一方、適用ではSSE energy、有限サイズgap・fit、simulation/statistical誤差を使う。これを保証付きetaへ移すには、必要なenergy下界・gap下界・simulation/統計誤差を囲う根拠が要る。2×L ladderへの同条件の証明・取得費も今回得ていない。論文の数値値は再計算・再解析していない。

したがって「その準備法があるからB-01へのeta接続は解決済み」としない。別familyや新seedを追加探索して救済することもしない。

## 5. 粗いenergy区間の合法な経路

既知etaの枝ではL02 Lin–Tong Corollary3の精度をsigmaとして使える。これは未知gapで

\[
\Pr(E_0\in[e-\sigma,e+\sigma])\geq1-\delta_{\rm coarse}
\]

を与え、fresh Hadamard回数は`Otilde(eta^-2 log(delta_coarse^-1))`、T_maxは`Otilde(sigma^-1)`、総evolution時間は`Otilde(sigma^-1 eta^-2 log(delta_coarse^-1))`。polylogはスペクトル正規化等にも依存する。後処理・準備・readoutは別費用。真のE0を使う区間の事後配置ではない。

L01がAppendix末尾で挙げる粗い推定法も準備数は無料でなく、QET-U型ならD1外となる。既知の古典的上下界`L0<=E0<=U0`から中点eと半幅sigmaを取る経路も合法だが、十分狭い囲いを得る費用はinstance依存である。幅が既に最終精度へ閉じていれば、新しい認証機構を足す必要性も別途説明する。

N_targetを認証部分だけの目標と読む場合も、eta/coarse取得を加えた総費用と区別する。例えばcoarseのeta^-2が目標の主要項eta^-1 sigma^2 epsilon^-2を上回る領域もあり、総費用改善は自動ではない。

coarse取得にetaを使い、そのeta取得に未取得のground隔離区間を使う場合は循環である。独立したpromiseまたは係数由来の証拠がなければ、二つを取得済み入力として同時に起動できない。

## 6. Confidenceと現在の不足

保証eventをeta、coarse、test、filter/simulation近似、その他へ分け、合計失敗確率をdelta_total以下にする。coarseから選んだ窓にfresh validationを使えば条件付きで固定窓の評価を適用できる。同じ記録を選択・検定へ再利用する場合は、その選択まで覆う同時保証が必要。

例えば`delta_eta+delta_coarse+delta_test+delta_approx+delta_other<=delta_total`とする。etaが決定論的な保証ならdelta_eta=0だが、その証拠取得費は0にならない。

**既知etaの数学枝：条件付きで定式化可能。弱摂動等の限定枝：既知十分条件あり。前回ladder・一般分子の有用なeta取得：未確立。coarse区間：既知etaなら公表経路あり。取得費込みのB-01資源改善：未確立。**
