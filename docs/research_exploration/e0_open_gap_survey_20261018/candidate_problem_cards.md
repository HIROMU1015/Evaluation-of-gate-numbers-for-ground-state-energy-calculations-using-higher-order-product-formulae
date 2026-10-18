# 判断用task card：1件、未採択

以下は課題の提案であり、構成された新アルゴリズム候補ではない。達成可能性・独立新規性・資源優位・論文化可能性を認定しない。公表済みの費用・操作は[対照資料](strong_baselines_and_open_gaps.md)に一度だけ記し、ここでは次の判断を変える未証明の問いを定める。

## B-01：未知gapでの低深さGSEE認証の標本費用

**研究課題。** low-depthで得たenergyを、真のgap下界を用いずにconfidence付きで受理する処理について、推定本体に比べ大きい認証標本費用を除けるか。それがD1に沿うcontrolled real-time測定だけで可能かを、最初の可否判断とする。

**根拠と最強対照。** L01のTheorem5.2/AppendixCと§6が直接の公表根拠。L02/L03、L06の総query最適法、L09の古典certificateも外さない。L01のQET-Uを無断採用せず、D1内とD1外の対照を併記する。問題全体に一つの「最強」を宣言せず、同一accessと費用軸ごとに強い対照を選ぶ。

**残る条件。** unknown gapでのsoundnessは既にL01が解いている。未解決とするのはその存在ではなく費用差である。L01の受理完備性はgapとsigmaの関係に依存する。任意に短い深さで全入力の受理を求めない。2025年の公表された問いの後続解消は、今回読んだ2026年の結果では確認できなかった。現在の全先行研究でも未解決であるとの断定は保留する。

## 合法な入力と費用を先に固定する

候補問題の入力は元Hの係数・指定sector、繰返し可能な準備手順、既知のスペクトル囲い、epsilon/delta、粗い区間幅sigmaである。eta>0を使う命題は**etaの保証を条件とする枝**だけに限定する。etaを未知ground振幅の無料oracleにしない。各対象familyにおけるetaの合法な根拠と費用C_etaがなければ、電子Hamiltonianへの実用候補としては残せない。

粗いintervalは`Pr(E0 in [e-sigma,e+sigma])>=1-delta_coarse`の公表法で取得可能かを確認し、C_coarse・準備回数・時間を支払う。真のE0で区間を配置しない。最終失敗確率は`delta_coarse+delta_test+delta_other<=delta_total`のように合算する。sigmaの再試行や適応選択をする場合の全stage confidenceも含める。

D1内で最初に比較する測定accessはfresh psiに対するcontrolled exp(-iHt)のHadamard試行と通常の古典処理。記録は(t,測定軸,±1結果)であり、時刻選択も費用へ含める。準備A†・反射・QET-U filterやその成功条件付き標本は、この記録から無料で得られない。許すaccessを変更する場合はユーザー/GPTの別判断が必要である。

## 次に必要な最小の数学的命題（未証明）

正規化後`epsilon << sigma << 1`、既知eta、合法な粗いintervalの条件で、次の性質を同時に満たす判別がD1内で可能かを問う。

1. **Soundness:** すべての許容入力について

   \[
   \Pr[\mathrm{ACCEPT}\ \wedge\ |E_{\rm out}-E_0|>\epsilon]
   \leq\delta_{\rm test}.
   \]

   受理したという条件付きの誤り確率とは異なる。常にREJECTすれば満たせるため、これだけを成功にしない。
2. **Completeness:** 真のgapがsigmaに対し十分大きい入力class（定数とpolylogは比較前に固定）では、gap値を入力せずに少なくとも1-delta_testで受理する。より短時間で受理できる構造があるかは追加条件であり、今回構成しない。
3. **費用判別:** 同じT_maxの下で、認証に必要なfresh準備・回路数を、対照の推定本体と同程度のepsilon・eta依存へ下げられるか。目標の比較式は、sigmaをgap相当の設計scaleとした本体の式

   \[
   N_{\rm target}=\widetilde O\!\left(
     \eta^{-1}(\sigma^2\epsilon^{-2}+\log\sigma^{-1})
     \log\delta^{-1}\right),\quad T_{\max}=\widetilde O(\sigma^{-1}).
   \]

   これは本調査が証明した上界ではない。sigmaは保証済みgap下界ではないため、推定本体の定理に置換するだけでは成立しない。標準的なconcentration改善で既知認証が同じ依存へ到達するなら、新規生成研究へ進める根拠は消える。逆に、弱い上界との差だけで改善可能とはしない。

まずspectral-recordの条件付き判別問題として定式化し、電子Hamiltonianへ移す条件を明示する。record模型で得る下界を、係数を知る全アルゴリズムの下界へ拡張しない。古典的に元Hを安く解けるinstanceは強対照が既に認証可能なcontrolであり、量子優位の識別例にはしない。

## 最小のfamily指定と判別点

新しいfamilyを構成する作業はしていない。最初の定式化対象は既知のnumber-conserving有限二体電子Hamiltonian classである。小さい既存診断classとして、2×L open Hubbard ladder（L>=2、各連結edgeの非零hopping、onsite U>0、既知scalar）、N=2L・Sz=0を使えるかを判断対象にする。比較定理と揃える枝では非縮退groundを仮定し、縮退一般への拡張は要求しない。これは既知モデルの問題指定であり、識別例の構成・解・gap・etaの証明は行っていない。Coulomb積分を持つ一般分子への移送も未確立である。サイズ・係数範囲・準備手順・eta証拠は将来の仕様で先に固定し、未知スペクトルに合わせて選ばない。

固定小サイズが古典的に容易であることと、サイズを増やしたfamilyでの情報費用問題を分ける。上のclassで所要etaが合法に得られない、既知の古典上下界だけで同予算内に閉じる、あるいは候補差が標準統計手順だけなら、このカードは新量子アルゴリズム課題として取り下げ得る。今回、それらの不存在・成立を証明していない。

## 科学的に変わり得る点と残る全体費用

成功すれば、未知gap下でも短いcoherent evolutionを使うか判断する際の認証負担が軽くなり得る。原HのE0推定で、推定値を出す費用だけから、受理までの費用へ議論を進められる。ただし改善可能性は未確立である。

最終比較は少なくとも

`C_total = C_input + C_eta + C_coarse + N_prep C_prep + C_controlled_evolution + C_filter_if_allowed + C_readout + C_classical + C_memory`

を記録する。NとT_maxの漸近式だけではnative gate・routing・noise・準備を含む総費用優位にならない。simulation biasや係数近似の誤差を加えると統計的soundnessが維持される条件も別途必要であり、A2やR1-Pの再開には読み替えない。

**プロジェクトで未解決:** 同一条件での上記命題・合法eta証拠・有限総費用。**文献上の根拠:** 2025年論文の明示課題。**現時点の全世界的open認証:** 未取得。**正式採択:** なし。

次の判断はGPT／ユーザーが、D1内の限定可否問題として扱う価値とeta/intervalの条件を承認するかである。Codexによる新構成・証明・数値検証は今回開始しない。
