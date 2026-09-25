# PF研究の方向性レビュー：事前検証後の判断

- 判断対象：`prevalidation-complete-results-index-20260925`
- 基準コミット：`e820f653a5916f27233ab4674a89d288cf969e37`
- 作成日：2026-09-25
- 確認方法：基準コミットの索引・研究状況文書と、索引が指す固定コミットの主要report、audit、protocol、predictions、CSVを照合。分子計算やPF計算の独立再実行ではない。凍結予算に関する一部の数値は保存値から算術再集計した。

## 1. 結論

**研究方針を判断するための事前検証は、ここで区切ってよい。** 全128項目の完遂、全分子での成功、実用selectorの完成を待つ必要はない。現在の結果から、何を中心にすべきか、何を主張しない方がよいかを判断できる。

研究の問題意識には意味がある。しかし、現在の「低次モデルで正確に予測できる新PFを探す」を中心目的として維持する根拠は弱くなった。より有力なのは、次の主題である。

> **高次PFの固有値誤差に現れる相殺が、有限時間の資源見積もりと近似状態による校正をどのように不安定にするかを明らかにし、その結果を踏まえてPF・時間刻みを選択するための条件と限界を示す。**

研究の中心は「新しい係数」ではなく、**小さい固有値誤差を、どこまで信頼できる資源低減につなげられるか**に置く。新PF設計は、既存PFと校正法では満たせない要件が明確になった場合の選択肢とする。

これは完成した汎用・低コスト・保証付きアルゴリズムが既に得られたという判断ではない。**本研究の問いを決める材料がそろった**という判断である。[R1][R2]

## 2. 現在の証拠から言えること

### 2.1 新PFが必要、という前提は支持されていない

N2/COの当時未使用だった主4条件では、Yoshida4＋二項、current_m3＋二項、two_term_center＋二項、Yoshida6＋三項が、それぞれ固定モデルの4基準で4/4に合格した。current_m3は余裕なしの凍結QPE予算も4/4達成した。[R3]

研究状況文書がまとめた直接格子最小コストでは、current_m3に対しtwo_term_centerは1.148–1.161倍、Yoshida4は1.900–1.936倍、Yoshida6は1.587–1.770倍だった。これは宣言された比較集合・評価規則内の結果であって、全PFの大域最適性ではない。[R2]

したがって、two_term_centerの予測残差や判定余裕がよいことだけから、追加量子コストを支払うべきだとは言えない。一方、m5_bestは同じ二項モデルでは0/4であり、「既存PFなら何でも二項化すれば解決する」とも言えない。[R3]

**研究判断：** two_term_centerの微調整を主作業にせず、PFごとの有限時間補正・状態感度・校正費用の違いを説明する方へ移る。

### 2.2 小さいa4と小さいD4は異なる

F03では、H2/H4のm5_bestにおいて中心化D4作用のノルムが|a4|の40–67倍だった。人工二準位族ではa4の零点へ近づいてもD4ノルムは有限に保たれ、一項モデルの解析刻みで直接誤差が目標の100倍以上になった。保存された連続枝追跡には警告がなく、少なくともこの人工族の破綻は枝の取り違えだけでは説明できない。[R4]

これは「最適化PFは悪い」という結果ではない。低い先頭係数が、大きな演算子の期待値相殺から生じた場合と、演算子全体の縮小から生じた場合では、その後の外挿や状態近似の扱いが異なることを示す。

**研究判断：** 先頭係数だけの順位から、相殺構造と有限時間の使用条件を含む評価へ進む根拠がある。

### 2.3 two_term_centerの滑らかさも、相殺と無縁ではない

F02では、最適化した4次PFのa8は、正のD8期待値と負のD4二次状態混合の差だった。two_term_centerの正味a8は、両成分の絶対値和の1.2–3.5%しか残っていない。[R5]

したがって、「二項モデルがよく当たるPF」は「高次演算子が全体として小さいPF」と同義ではない。先頭係数の相殺を避けて高次係数の相殺に依存している可能性もあり、残差の小ささと移植性を同一視しない。

相殺自体を排除する必要もない。安定して予測できる相殺は利用価値がある。問うべきなのは、**どの相殺なら限られた校正情報で信頼して利用できるか**である。

### 2.4 全電子HFの結果は、単一原因の証明ではない

HF機構bridgeでは、Yoshida4の伸長に伴い|a4|/||D4||が約2.43e-3から7.02e-4へ低下し、解析刻みは1.384倍へ増加した。その刻みでの8次寄与比は0.00767から0.0371へ増加した。正規化位相gapの圧縮は検出されていない。[R6]

ただし、状態混合項の絶対値が伸長で増えたわけではない。報告された伸長/平衡比は、D4対角成分0.2725、D4結合0.4768、D8直接成分0.3319、D4状態混合0.2382である。**小さい先頭係数から長い刻みを選ぶため、高次項の相対的重要性が増す**という説明が重要である。[R6]

有限区間からD4/D6/D8を回収するfitには大きな不安定性も記録されている。形式的なArb演算子と有限時間fitを区別し、この検証を「全電子破綻の唯一の原因を厳密に特定した」とは書かない。

### 2.5 一般的な状態品質と校正品質は異なる

H02では、エネルギー誤差、分散、Hamiltonian残差、厳密基底状態重なりを等しくした32組の位相quartetが構成され、有限時間校正量の違いが確認された。一方、調べた集合でPF選択の反転とPF-choice regretは0だった。[R7]

正確な主張は、これらの状態品質スカラーが**校正量を一意には決めず、単独で自動的に要求校正精度を与えるわけではない**というものになる。演算子ノルムやギャップ等の補助情報を含む上界が不可能だという意味ではない。また、PF選択失敗が既に実証されたという意味でもない。

**研究判断：** 「良い近似基底状態か」だけでなく「このPF誤差を評価するのに適した近似状態か」を扱う研究には、具体的な根拠がある。

### 2.6 少数点・高速計算・大規模適用は別々の主張

H04は、H03で顕在化した素朴BCHの式生成ボトルネックを解消した。H4/Yoshidaの対象は168,560個のraw commutatorから456個のgrouped termへ縮約された。ただし、密な入力行列・状態ベクトルの制約は残る。[R8]

H05では正確なa4と2つの直接点を使う方法が8/8で残差基準に合格したが、D04でa4取得費用を含めると、自由5点fitより速かったのは1/8だった。ゼロ直接点のdense BCHも、前処理を含む普遍的な高速方式ではない。[R9][R10]

**研究判断：** 「2点で済む」を独立した実用価値にしない。量子資源、古典実時間、メモリ、再利用回数を分ける。compact BCHは有用な基盤であり、その一般的な発想には明確な先行研究がある。[L2]

### 2.7 oracle-free最小版は前進だが、完成した低regret selectorではない

実用候補では、厳密基底状態、直接PF固有値、直接最適時刻、既存direct時刻座標を選択器へ与えず、CISD由来proxyから選択している。予測ファイルは凍結後の採点で変更されていない。これは従来のoracle-assisted校正からの前進である。[R11][R12]

ただし、次の限定がある。

- 対象は既に見たN2/CO/HFであり、selectorの独立ホールドアウトではない。
- 全6条件でcurrent_m3が選ばれている。PF選択機構の便益は、固定current_m3を使う基準法と分けて示す必要がある。
- 予算判定は連続コスト・加算誤差proxyであり、実際のQPE出力成功確率の検証ではない。
- 残る密行列・状態ベクトル表現から、大規模量子優位領域への適用は未証明である。
- 採点時刻は選択時刻そのものではなく、最大0.5%の相対差を許した既存direct点への最近傍写像である。
- 報告selection regretは、固定予算そのものの超過率ではない。[R12][R13]

## 3. 今回のレビューで区別を追加したい二つの評価

### 3.1 選択時刻と採点時刻

最小selectorのprotocolは`continuous_time_from_cisd_proxy_only`を選択結果とし、採点では`nearest_saved_direct_point`を用いる。最大許容相対差は0.005であり、補間も新しい直接点も使っていない。[R12]

実際、N2伸長では

- 選択時刻：0.8303584711475099
- 採点時刻：0.8332680282293169
- 相対差：約0.3504%

だった。[R13]

この設計は「truth座標を選択へ漏らさない」という点で適切である。一方で、**近傍点での予算達成は、選択時刻そのものの厳密な予算達成を意味しない**。現在の6/6は、その近傍採点規則の下での結果として記す。

研究方向の決定を止める理由にはならない。方法論の本検証では、凍結した選択時刻そのもので直接誤差を測る、または区間内変動の有効な上界を用いる必要がある。

### 3.2 直接再評価コストと、凍結した予算コスト

現在の単純コストモデルを

\[
C_P(t)=\frac{\beta K_P}{t(\epsilon_E-e_P(t))}
\]

とする。次の二つは異なる。

\[
R_{\mathrm{direct}}=\frac{C_{\mathrm{direct}}(\widetilde t)}{C_{\mathrm{ref,grid}}}-1,
\qquad
R_{\mathrm{budget}}=\frac{1.01\,\widehat C_P(t_{\mathrm{selected}})}{C_{\mathrm{ref,grid}}}-1.
\]

前者は真の誤差を使い直した資源評価、後者は事前に決めた予算を実際に採用する場合の連続資源proxyである。今回の参照は**許可された2つのPFの既存格子上の最良費用**であり、全PF・連続時間の大域最適値ではない。[R12][R13]

N2伸長では、保存値から

\[
\widehat C=208{,}603{,}332.59679866,
\quad C_{\mathrm{ref,grid}}=147{,}957{,}576.27790663
\]

なので、

\[
R_{\mathrm{budget}}\simeq0.423985
\]

となる。報告されている直接再評価regretの22.43%に対し、1%余裕付き凍結予算の超過率は**約42.40%**である。[R13][R14]

同じ定義で、保存auditの時刻・誤差・費用から再集計すると次のようになる。

| 条件 | 報告された直接再評価regret | 1%余裕付き凍結予算regret |
|---|---:|---:|
| N2平衡 | 2.12% | 10.06% |
| N2伸長 | 22.43% | 42.40% |
| CO平衡 | 3.16% | 12.07% |
| CO伸長 | 7.25% | 19.34% |
| HF平衡 | 114.15% | 115.03% |
| HF伸長 | 107.65% | 110.29% |

これは新しい分子計算ではなく、同じ保存値と費用式からの算術再集計である。時刻写像、限定された基準格子、QPE全体を含まないproxyという制約はそのまま残る。

**含意：** 現在のselectorは「正解を入力せず保守的に設定を決められる見込み」を示すが、「小さい資源損失で運用できる完成方式」ではない。元の数値を誤りと決めつけるのではなく、両指標を別の列として残すべきである。

## 4. 最も意味のある主題：相殺に敏感な固有値誤差の信頼性

### 4.1 問い

> 最適化PFで得られる小さい基底状態固有値誤差は、どこまで有限時間の低資源化につながり、その見積もりにはどの程度・どの方向の近似状態精度が必要か。

この問いはF03、F02、H02、実用校正を一つにつなぐ。

### 4.2 二つの敏感さを結ぶ

非縮退基底状態で局所展開が有効な範囲において、対称4次PFを

\[
H_{\mathrm{eff}}(t)=H+t^4D_4+t^6D_6+t^8D_8+\cdots
\]

と書くと、

\[
a_4=\langle0|D_4|0\rangle,
\qquad
a_8=\langle0|D_8|0\rangle+
\sum_{n\ne0}\frac{|\langle n|D_4|0\rangle|^2}{E_0-E_n}.
\]

これは摂動論の恒等式であり、それ自体の新規性を主張しない。[R5][L1]

**有限時間に対する敏感さ。** 一項モデルを使うと

\[
t_{\mathrm{ana}}=\left(\frac{\epsilon_E}{5|a_4|}\right)^{1/4}.
\]

したがって、他の係数が独立に十分小さくならない状況では、

\[
\frac{|a_6|t_{\mathrm{ana}}^6}{\epsilon_E}
=\frac{|a_6|\epsilon_E^{1/2}}{5^{3/2}|a_4|^{3/2}},
\qquad
\frac{|a_8|t_{\mathrm{ana}}^8}{\epsilon_E}
=\frac{|a_8|\epsilon_E}{25|a_4|^2}.
\]

a4だけを小さくすることは、使用時刻における高次寄与の重要性を増すことがある。ただし、t_anaが局所展開の有効域を出ればこの式を真の誤差式として使えない。その破綻こそ検討対象である。

**近似状態に対する敏感さ。** 正規化状態を

\[
|\psi\rangle=\sqrt{1-\eta}|0\rangle+e^{i\phi}\sqrt\eta|\chi\rangle,
\quad\langle0|\chi\rangle=0
\]

と書くと、

\[
\langle\psi|D_4|\psi\rangle-a_4
=2\sqrt{\eta(1-\eta)}\,\mathrm{Re}\!\left[e^{i\phi}\langle0|D_4|\chi\rangle\right]
+\eta\left(\langle\chi|D_4|\chi\rangle-a_4\right).
\]

一方、状態エネルギー誤差は

\[
\langle\psi|H|\psi\rangle-E_0
=\eta(\langle\chi|H|\chi\rangle-E_0)
\]

であり、同じηと|χ⟩でもφによってD4の評価が変わり得る。小さいa4に対する相対誤差はとくに増幅され得る。この式も標準的な状態展開からの導出である。

**研究の価値は、これらの式を再発見することではない。** 実分子・実PFのどの領域で二つの敏感さが資源見積もりを左右するかを示し、先頭係数、演算子作用、高次寄与、必要な校正情報を結びつけることにある。

### 4.3 到達点

最低限のまとまった成果は、次の組合せになる。

1. 先頭係数・高次係数の相殺と、近似状態の方向依存性を区別する解析。
2. 人工反例だけでなく、分子の成功例・破綻例でその説明が有効なことを示す。
3. 誤差曲線の精度、PF順位、刻み幅選択、凍結QPE予算を別評価とし、どの誤差が実際の資源損失を生むかを示す。
4. 一項モデル、固定二項モデル、保守刻み、最小oracle-free校正の使い分けと限界を明示する。

全分子を1つのPFで解決すること、普遍的保証を最初から得ることを必須にしない。限定された適用範囲と、使えない理由の説明にも成果がある。ただし「いくつかの条件でfitできなかった」だけで終えず、資源評価への帰結までつなぐ。

## 5. 残しておく研究方向の比較

| 方向 | 現在の根拠 | 着地点 | 主な不足・リスク | 推奨する扱い |
|---|---|---|---|---|
| A. 固有値誤差の相殺・校正感度・資源見積もりの信頼性 | F02/F03/H02、分子比較、oracle-freeとの落差 | 機構を説明する解析＋検証可能な評価手順＋適用限界 | 標準摂動論の再説明だけでは弱い。実用域と資源への帰結を示す必要 | 主題に推奨 |
| B. 限られた古典情報による低損失の時間刻み校正 | oracle-free最小版、CISD、compact D4基盤 | 精度達成と凍結予算損失の両方を改善する方法 | 独立検証、固定PF基準、校正費用、大系表現が未解決 | Aに接続する発展先 |
| C. 校正しやすさを含むPF共同設計 | PFごとの相殺・状態感度差 | 同じ信頼性と校正予算で既存PFより有利な係数 | 現two_term_centerの優位は未立証。探索目的の自己目的化 | 条件付き保留 |
| D. compact BCH・作用評価の方法論 | H04の実装と一般S2合成への拡張 | 独立に使える高効率バックエンド | compact BCH一般には先行研究。D6/D8、大系表現の問題 | 支援基盤、差分が十分なら別主題 |

「どれか1本しか成立しない」と決める必要はない。ただし、本研究の主たる問いをAに置き、Bを成功時の強化、Cを必要性が確認された後の分岐にすると、どれかの新手法が勝たなければ全体が無価値になる構造を避けられる。

## 6. 先行研究との位置付け

- MehendaleらのDigital Discovery 2025論文は、分子系の二次Trotter、摂動論に基づく固有値誤差評価、CISD等の近似状態、Hamiltonian分割と資源の関係を既に扱う。「固有値誤差を使う」「CISDを使う」だけを新規性にしない。[L1]
- Maxwellらの2026年プレプリントは、BCH対角成分の重要性、compact BCH、importance sampling、テンソルネットワーク等による大規模評価を扱う。H04の大幅な式数削減をすべて本プロジェクト独自の一般原理としない。[L2]
- MoralesらのPF比較・係数構築も既存研究である。係数の改良や次数比較だけでは、差分を個別に示す必要がある。[L3]

このプロジェクトの差分候補は、**固有値誤差を小さくする相殺が、有限時間外挿と近似状態校正の両方を難しくし得る点を、同じ資源選択問題で検証・定量化すること**に置くのが自然である。

ただし、これは新規性が完全に確定したという意味ではない。提案する診断量・命題・アルゴリズムを具体化した時点で、該当する主張単位の文献比較が必要になる。

## 7. 現在の方針から変更したいこと

### 7.1 モデル合格と実行判断を分ける

従来の1%コスト誤差、5%時刻差、0.05ε残差の判定は、比較の再現性のため維持してよい。ただし、その判定を運用上の精度達成や低費用と同一視しない。主評価を次の三段にする。

- モデル評価：符号付き誤差曲線と係数をどこまで再現するか。
- 選択評価：どのPFと刻み幅を選ぶか。PF選択損失と同一PF内の刻み損失を分ける。
- 予算評価：真値で配分し直さない凍結QPE予算の成否と超過費用。

### 7.2 「active-spaceなら成功」を物理法則にしない

現データにはその傾向があるが、full-electron/frozen-coreはHamiltonianのエネルギー尺度、群分割、先頭係数、実用刻みを同時に変える。ラベルを成功判定器とせず、相殺・高次寄与・状態感度で説明を目指す。[R2][R6]

### 7.3 「高次PFは不要」と結論しない

D03のcoverageは限られる。NH3ではCAが0/14、CA/100が2/14、P0-3集合でもCAが4/24、CA/100が8/24である。coverage外は不合格や劣位と同義ではない。[R15]

M01で順位が不変だったのは、主にN2の平衡・伸長×CA/10・CA/100における比較可能なPF集合である。HF伸長・CA/100では、raw費用最小のcurrent_m3がモデル不合格で、合格候補に限定するとYoshida6だけが残る。[R16]

したがって、現データは「この代表範囲でcurrent_m3が有利」を支持するが、Morales8次・10次や他精度域を否定しない。研究方針を決める前提としてcoverageを全面補完する必要はない。

### 7.4 oracle-freeとスケーラブルを区別する

厳密解を入力しないことは重要だが、密なHamiltonian、群スペクトル、状態ベクトルや参照時間発展の古典計算が残る。これを「任意サイズで安価」とは呼ばない。大規模適用を主張する場合だけ、状態表現と作用評価のスケーリングを本研究の検証へ追加する。[R8][R9][R11]

## 8. 事前検証の終了と、本研究の次の作業

### 8.1 これ以上の広い事前検証は不要

新分子大量追加、全精度全PFの総当たり、mの全面探索、QPE方式・FTQCアーキテクチャの全面比較を、研究方針を決める前の必須条件にしない。

以下の仕上げ確認は、方向決定を先延ばしするためではなく、保存結果の表現を正確にするために行う。

**仕上げ確認1：凍結したselector出力の時刻そのものを採点する。** 現在の6つの選択結果を変更せず、その6時刻だけの直接誤差を求める。既に一致時刻の結果があれば再利用する。最近傍点の判定との差を記録し、結果が変わっても方式をその場で調整しない。

**仕上げ確認2：運用予算regretを併記する。** 本書3.2の定義を集計へ加える。これは既存値の再解析であり、PF計算を追加しない。既存のdirect-regretを削除・上書きせず、二つの意味を明示する。

これらが変わっても、相殺・近似状態・資源評価の信頼性を主題にする判断は成立する。実用selectorの肯定的主張の強さは変わり得る。

### 8.2 Aを主題にする場合の本検証

人工族の解析、実分子の対照比較、近似状態感度、凍結予算評価を一つの主張にまとめる。既存資料の再整理が多く、全F領域の再実行は不要である。

着地点を「相殺は危険」としない。相殺を利用してよい条件と、確認すべき情報を明確にする。特に、現在よく動く二項モデルを、任意の低次多項式fitの成功としてではなく、支配項と使用時間域の関係として説明する。

### 8.3 Bも実用手法として主張する場合の本検証

selectorを固定して、まだ見ていない分子群に1回の独立評価を行う。その際、最低限比較したいのは次の二つである。

- current_m3を固定し、同じCISD校正を使う基準法。
- PF選択・sentinel・fallbackを含む提案法。

これにより、性能改善がPF選択によるのか、単なる刻み縮小によるのかを分離する。手法が全条件でcurrent_m3を選ぶなら、成果を「汎用PF selector」ではなく「時間刻み校正」として正しく位置付ける。

相殺診断やsentinelの有効性を主張する場合、その機能を外した対照も同じ情報予算で比較する。全部を新しい独立実験群にせず、同じ固定評価内のablationにまとめる。

予算達成率だけでなく、全入力に対するcoverage、unsafe率、凍結予算regret、校正費用を報告する。判定不能は判定不能として残す。6/6や4/4を母集団の保証確率に読み替えない。

## 9. 論文・研究のまとまり方

仮題案：

> **高次積公式の固有値誤差相殺と、有限時間量子資源見積もりの信頼性**

図の構成案：

1. 同じPFの一項・二項モデルが、実用時刻と費用の判断に与える差。
2. F03のa4零点への接近：a4、D4ノルム、解析刻み、直接誤差の関係。
3. F02のa8直接項・状態混合・相殺後係数、HF成功/破綻の対照。
4. H02の同じ状態品質スカラーと異なる校正、H01/practicalの予算損失。
5. 選択情報量・誤差・凍結予算費用の関係と、適用範囲を明示した評価。

方法論としての追加主張が十分に立つ場合は、独立評価を含む「限られた古典情報によるPF時間刻み校正」を後半または別論文へ展開できる。現段階で汎用保証付きselectorを主題の必須成功条件にしない。

## 10. 最終判断

- 研究の問題意識：意味がある。
- 現在の「予測しやすい新PFを作る」という中心目的：修正を勧める。
- 最も証拠が厚い中心：相殺構造、状態依存の校正感度、有限時間資源評価の信頼性。
- 実用校正：有望な発展先。ただし現データだけで独立検証済み・低regret・大規模適用可能とは言えない。
- 新PF探索：現候補の微調整を再開するより、既存PFでは達成できない定量的要件が生じるまで保留。
- 追加事前検証：広いものは不要。評価の仕上げを2件に限定し、あとは選んだ研究主張を検証する本研究へ移る。

## 出典

以下は確認した固定コミットの文書・結果。索引の記述と個別reportが異なる場合、該当する個別結果の範囲と定義を優先する。

- [R1] [結果索引](https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/e820f653a5916f27233ab4674a89d288cf969e37/docs/prevalidation_results_index.md)
- [R2] [研究状況](https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/e820f653a5916f27233ab4674a89d288cf969e37/docs/current_research_status.md)
- [R3] [N2/CO/HF固定ホールドアウト](https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/33a761d44a24022ad61192c41a196dd4cb3afbca/artifacts/server_unused_molecule_frozen_holdout_20260921_d288797/aggregate/report.md)
- [R4] [F03：a4とD4](https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/e820f653a5916f27233ab4674a89d288cf969e37/artifacts/prevalidation_f03_a4_operator_cancellation_20260922_retry2/report.md)
- [R5] [F02：a8の状態混合](https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/6d13384ef327e5b248c2ce93ae29ad4e7686b2e5/artifacts/prevalidation_f02_tau8_state_mixing_20260921_retry3/report.md)
- [R6] [HF機構bridge](https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/6eb1aa02f1d28904741b2cee4f70347e1203198f/artifacts/server_f_hf_mechanism_bridge_retry1_20260923_221c7c3/report.md)
- [R7] [H02：有限時間制御状態](https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/16bd6c264e0e2de6d86b0a785c9bc449ebbd4dfe/artifacts/server_h02_finite_time_controlled_state_20260922_a228b5f/report.md)
- [R8] [H04：compact BCH](https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/6d13384ef327e5b248c2ce93ae29ad4e7686b2e5/artifacts/prevalidation_h04_compact_bch_importance_20260922_retry1/report.md)
- [R9] [H05：高次係数取得](https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/6d13384ef327e5b248c2ce93ae29ad4e7686b2e5/artifacts/prevalidation_h05_higher_order_acquisition_20260922_retry2/report.md)
- [R10] [D04：同一古典予算](https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/6d13384ef327e5b248c2ce93ae29ad4e7686b2e5/artifacts/prevalidation_d04_equal_classical_budget_20260922/report.md)
- [R11] [practical校正report](https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/4f4374bdf4dbcb7d8e1d14f9682570c221e4c88a/artifacts/server_practical_calibration_minimal_20260923_79035cc/report.md)
- [R12] [practical固定protocol](https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/4f4374bdf4dbcb7d8e1d14f9682570c221e4c88a/artifacts/server_practical_calibration_minimal_20260923_79035cc/protocol.json)
- [R13] [practical auditと採点値](https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/4f4374bdf4dbcb7d8e1d14f9682570c221e4c88a/artifacts/server_practical_calibration_minimal_20260923_79035cc/audit.json)
- [R14] [practical凍結予測値](https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/4f4374bdf4dbcb7d8e1d14f9682570c221e4c88a/artifacts/server_practical_calibration_minimal_20260923_79035cc/predictions.json)
- [R15] [D03 coverage](https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/a8b9a92c9fcdb1b4187d5aa3c239ed8b7443dcfd/artifacts/server_d03_target_accuracy_followup_20260923_748b3d4/coverage_summary.csv)
- [R16] [M01 資源指標感度](https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/b5af6996159b3dfbd6e5bb3cc2467cb23155906d/artifacts/prevalidation_m01_resource_metric_sensitivity_20260925_3b6e5f0/report.md)

### 関連一次文献

- [L1] Mehendale et al., *Estimating Trotter approximation errors to optimize Hamiltonian partitioning for lower eigenvalue errors*, Digital Discovery 4, 3540–3551 (2025). https://doi.org/10.1039/D5DD00185D
- [L2] Maxwell et al., *Practical Estimation of Trotter Error for Hamiltonian Simulation*, arXiv:2606.30738v1 (2026). https://arxiv.org/html/2606.30738v1
- [L3] Morales et al., *Selection and improvement of product formulae for best performance of quantum simulation*, arXiv:2210.15817; Quantum Information & Computation 25 (2025). https://arxiv.org/abs/2210.15817
