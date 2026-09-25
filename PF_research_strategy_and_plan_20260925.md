# 対称4次PFの有限時間固有値誤差校正：研究方針・着地点・実行計画

**作成日：2026年9月25日**  
**位置付け：事前検証を終えた後の、本研究の計画案**  
**根拠の基準点：`e820f653a5916f27233ab4674a89d288cf969e37` と、同コミットの結果索引から参照される固定結果**

本書は、新しい実験が成功したという報告ではない。保存済みの証拠、標準的な数理関係、本書で提案する仮説・手順を区別して記す。指定リポジトリへの変更・新規分子計算は行っていない。実験条件や数値目標は、ユーザーから与えられた制約ではなく、以下で理由を付けて提案する研究設計である。

> **実行結果追記（2026年9月25日）**：本書のS0--S4は完了した。S1/S2で状態置換誤差が
> 固定case集合の主要成分となり、S3でHF成功・破綻対への条件付き接続を確定した。
> S4のoperator-sensitive二状態診断は全数値gateを通過したが、baseline比の平均regret
> 改善が`0%`で、固定判定は`complete_no_benefit`だった。従って中核成果Aを完成形とし、
> 発展成果Bの独立評価S5には進まない。確定値と適用範囲は
> [`PF_first_study_final_synthesis_20260925.md`](PF_first_study_final_synthesis_20260925.md)および
> [`PF_first_study_final_decision_20260925.json`](PF_first_study_final_decision_20260925.json)
> を正本とする。以下の将来形は、結果を見る前に定めた設計履歴として残す。
>
> 終了後に保存済みS0の6条件だけを再解析し、総regretをcalibration/budget、時刻選択、
> PF選択へ分解した。PF選択損失は6/6で0、HF 2条件は時刻選択支配、主4条件は
> calibration支配3・時刻選択支配1だった。この再解析は新規truth点0で、停止判断を
> 変更しない。

---

## 0. 推奨方針の要約

### 0.1 今回決める中心課題

> **主として対称4次PFについて、近似状態と少数の校正情報から行う有限時間の固有値誤差予測を、どの範囲で資源配分に使えるかを明らかにする。状態近似、代理量と固有値の相違、有限時間モデルの誤差を分離し、相殺がその各段階に与える影響を調べる。その結果に基づき、目標精度を満たすために凍結するQPE資源を、単純な基準法より小さくできる校正法を目指す。**

研究の上位目的は「予測しやすい新しいPFを作ること」でも、「相殺が悪いことを示すこと」でもない。**使える誤差予測と、使えない誤差予測の違いを、最終的な精度・資源の判断まで結び付けること**である。

相殺は重要な中心仮説として残す。ただし、相殺がすべての不安定性の原因だとは仮定しない。代理量の選び方、状態が固有状態でないこと、モデルの時間対称性、フィット窓、数値精度も競合する説明として扱う。

### 0.2 着地点を二段階にする

**必ず狙う中核成果**は、同一Hamiltonian・同一PF上で、校正誤差の発生源と凍結資源への影響を定量的に接続した、機構・信頼性の研究である。単なる成功率表ではなく、構成例、条件付きの解析、分子例を組み合わせる。

**その上で狙う発展成果**は、中核成果から選んだ一つの改善を使い、選択時に厳密基底状態・直接PF固有値を入力せず、強い単純基準よりよい精度―資源―古典費用の関係を示すことである。

汎用的な安価なselector、全電子全分子への保証、新しい最適PF係数を、最初の論文の必須条件にはしない。それぞれ独立した大きな課題であり、同時に要求すると研究が拡散する。

### 0.3 最初に着手すること

まず既存の6選択点の仕上げ採点を閉じる。その後の最初の本実験は、**「校正誤差の三分解と資源配分への伝播」**とする。H4と解析可能な二準位系から始め、相殺・状態方向・代理量の影響を分ける。大量の新分子や係数探索は開始しない。

最初の実装依頼は、別紙 `PF_first_study_protocol_20260925.md` にまとめた。

---

## 1. この方針を選ぶ理由

### 1.1 既に分かったこと

| 保存結果 | 根拠から言えること | まだ言えないこと |
|---|---|---|
| N2/COの固定ホールドアウト | 複数の既存PFと低次モデルが有効で、合格候補中では `current_m3` が低コストだった | 新しいPFはどの用途にも不要、とは言えない |
| `two_term_center` の費用対効果 | 予測残差を小さくしても、約15%の量子コスト増を必ずしも正当化できない | 予測可能性そのものに価値がない、とは言えない |
| F03 | 小さい先頭固有値係数は、小さい誤差演算子と同義ではない | 小さい係数を持つ全PFが不安定、とは言えない |
| F02 | 高次係数内で直接項と状態混合項の相殺が起きる | その相殺が二項モデル成功の唯一の原因、とは言えない |
| H02 | 同じエネルギー誤差・分散等でも校正値は一意に決まらない | 通常の状態情報から一切の上界が作れない、とは言えない |
| practical最小版 | 選択入力から厳密基底状態・直接truthを外した実装が動作した | 未使用分子での一般性、低い凍結予算超過率、大規模での安価さは未確立 |
| D04/H04/H05 | 点数、式の項数、実時間、メモリは別の資源である | 「二点」「compact」「matrix-free」だけで実用性を主張できない |

出典は [R1]–[R10]。肯定的な分子結果の多くは凍結内殻active-spaceであり、機構実証の中心は対称4次PFである。

### 1.2 現行の目的をそのまま継続しない理由

「固定した四つの指標を通る新PF」を探すことを目的にすると、指標を通るが量子コストは高いPFを作ることが成功になってしまう。一方、指標には落ちても、安全側で実行可能な予算を出す方法が不合格になる。

したがって、予測性を捨てるのではなく、その価値を次の二つへ分ける。

1. **資源を見積もる価値**：必要量をどの程度正確に報告できるか。
2. **設定を選ぶ価値**：実際に固定するPF・刻み幅・QPE予算が精度を満たし、余計な資源を使わないか。

両者は同じではない。研究の主要成果は後者への接続とし、前者は理由を説明する中間量として残す。

### 1.3 Codex案から採用する点と変更する点

「主として対称4次PF」「同一Hamiltonian・PFで因果的に接続」「相殺を確定原因でなく仮説にする」という点は採用する。

一方、「相殺 → 状態校正の失敗 → 資源損失」という一方向の筋書きを先に固定しない。状態による変化があってもPF順位は保たれるかもしれないし、実際には代理量とモデルの不整合が支配しているかもしれない。**どの説明が正しいかを判別できる設計にすること自体が、良い方向性である。**

---

## 2. 研究の問いを具体化する

### Q1. 予測と直接固有値のずれは、どこで生まれるか

同じH、分割、PF、時刻で、状態置換、代理量、モデル外挿を分離する。合計だけを見て一つの原因へ帰属しない。

### Q2. 相殺は、何に対する感度を増やすか

先頭係数の相対誤差、有限時間の絶対誤差、選択時刻、凍結資源の超過率を区別する。相対係数誤差が発散しても、目標精度に対する絶対寄与が小さければ、実用上は問題にならないことがある。

### Q3. どこまで正確に校正する必要があるか

時刻の最小点が平坦なら、高精度の係数推定は不要かもしれない。反対に、誤差予算の境界や狭い相殺点では小さな予測差が重要になる。その差を、モデル残差ではなく最終的な配分で測る。

### Q4. 得られた知見は、何を改善できるか

校正点を一つ増やす、状態近似を改善する、代理量を変える、時間域を限定する、別PFにする、のうち何が有効かを判断する。全機能を備えた巨大selectorを最初から作らない。

### Q5. 改善が成立しなかった場合も、何が残るか

「相殺がある」という確認だけでは弱い。改善法に至らない場合にも、少なくとも資源配分に使える条件・使えない条件、必要な情報量、または従来指標の限界について、再利用可能な定量的結論を残す。単なる負の結果の羅列で論文が成立すると約束しない。

---

## 3. 着地点と研究の完了条件

### 3.1 中核成果A：校正から資源までの信頼性解析

仮題：

> **対称4次積公式における有限時間固有値誤差校正の信頼性と資源配分**  
> *Reliability of finite-step eigenvalue-error calibration for fourth-order product formulas*

完成時に示したい内容は次の通り。

| 成果 | 必要な中身 | 不十分な状態 |
|---|---|---|
| 誤差の分離 | 同一H/Pで状態・代理量・外挿の各寄与を測り、合計を再現する | 異なる分子の別々の傾向を一つの原因として並べるだけ |
| 機構 | 解析可能な制御系で予想を導き、介入で確かめる | フィット係数の相関図だけ |
| 分子への接続 | 制御系の予想が分子例のどこで成立し、どこで破れるかを示す | 人工系の結果を分子一般へ言い換える |
| 資源への意味 | 固定予算の精度達成と超過率、同一PFの刻み幅損失、PF選択損失を分ける | 係数・時刻の誤差のみで「資源悪化」と呼ぶ |
| 実務上の含意 | 何を測れば追加校正・状態改善・時間制限が必要と判断できるか | 「もっと高精度にするべき」で終わる |

標準的な摂動恒等式や、誤差を足し引きした分解そのものは新規性ではない。**それを具体的な評価対象へ適用して、予測・反例・判断条件・改善につなげる部分**を貢献とする。

### 3.2 発展成果B：診断に基づく資源効率のよい校正法

Aの結果で支配誤差が分かった場合に、一つの改善方式を固定する。対象は、選択時にexact ground/direct truthを入力しない校正法である。次を示せた場合に方法論として強く主張する。

- 単純な固定PF＋同じ校正より有利な条件がある。
- 同程度の精度達成・coverageで、実際に凍結する資源が減る、または同程度の量子資源で校正費用が減る。
- 追加の状態生成、基底変換、群スペクトル、追加時刻評価を費用へ含める。
- 開発集合で固定した規則を、独立評価集合で一度採点する。
- 方法が失敗する条件、棄却、追加費用も含めて報告する。

「最大超過率10%以下」は以前のpreferred値として参照できるが、自然法則でも普遍的な採択基準でもない。最終的には強い基準法との比較と、用途上意味のある改善で判断する。数値目標を用いるなら本評価前に固定する。

### 3.3 条件付き成果C：新PF設計

A/Bで、既存PFのいずれも必要な精度・費用・校正費用を満たせない具体的な領域が現れたときだけ再開する。その際は、フィット残差の最小化ではなく、固定した校正法で実際に使う量子予算と信頼性を目的にする。

新PFの発見をA/Bの完了条件にしない。係数の再探索は、現在の第一実験には含めない。

### 3.4 到達しない場合の終了・縮小判断

同一条件での誤差分離ができても、標準的な性質の確認にとどまり、従来法との差分・新しい判断条件・実際の利益がないなら、独立論文としての主張は再検討する。データ・診断ツールとして整理し、別方向へ移る判断も残す。

逆に、相殺仮説が反証されても、代理量と固有値の違いや、少数情報からの非識別性が資源配分上重要だと示せれば、その機構へ中心を移せる。**仮説の維持を研究の成功条件にしない。**

---

## 4. 共通の数学的枠組み

### 4.1 対象と符号

固定された有限次元の電子Hamiltonian Hと、その保存則セクターを扱う。使用する分割・群順序・軌道表現を明示する。以下はリポジトリの直接評価に合わせて

$$
U_P(\tau)\approx e^{+iH\tau}
$$

を用いる。ネイティブQiskitの符号との変換は既存B01規則を継承する。

$\tau$ はPF一ステップの時間刻みであり、QPE全体の総時間ではない。HをHartree、$\hbar=1$ とする場合、$\tau$ はHartree$^{-1}$。$\delta E=\sum_j a_j\tau^j$ の $a_j$、および有効Hamiltonianの $D_j$ は、次元としてHartree$^{j+1}$ を持つ。既存の `a4_hartree` 等の列名を無断変更せず、新しいmanifestには係数の次元を別記する。

まず非縮退基底状態を扱う。縮退・準縮退・位相接近では、単一ベクトルの恣意的な選択を避け、射影部分空間での扱いか、明示した適用外判定を用いる。

### 4.2 直接の目的量

$$
U_P(\tau)|\phi_{0,P}(\tau)\rangle
=e^{iE_{0,P}(\tau)\tau}|\phi_{0,P}(\tau)\rangle,
\qquad
\delta_P(\tau)=E_{0,P}(\tau)-E_0.
$$

$\phi_{0,P}$ は小さい$\tau$から連続に追跡した基底接続枝である。孤立点で「最大重なりの固有ベクトル」を選ぶだけの方式と、連続追跡を区別する。$e_P=|\delta_P|$ が誤差配分に入る。

### 4.3 代理量

非対称echoを

$$
W_P(\tau)=e^{-iH\tau}U_P(\tau)
$$

と定義する。近似状態$\psi$に対し、既存の二種類を別々に扱う。

$$
g^{\mathrm{Im}}_{\psi,P}(\tau)
=\frac{\operatorname{Im}\langle\psi|W_P(\tau)|\psi\rangle}{\tau},
\quad
g^{\mathrm{arg}}_{\psi,P}(\tau)
=\frac{\operatorname{unwrap}\arg\langle\psi|W_P(\tau)|\psi\rangle}{\tau}.
$$

H02の固定プロトコルとコードは `arg` 版、practical最小版は `Im` 版を使用している。[R3][R11] 同じ「echo」と呼んで結果を直接混ぜない。arg版では振幅が小さい領域とunwrapの不安定性を別途扱う。

特にIm版はHermitian演算子

$$
A_P(\tau)=\frac{W_P(\tau)-W_P(\tau)^\dagger}{2i\tau}
$$

の期待値として厳密に表せる。この演算子は状態感度を解析する基準になるが、実装上いつも密行列として構築することを意味しない。

### 4.4 校正誤差の三分解

同じproxy定義を固定し、近似状態のデータから作ったモデルを$\widehat f_{\psi,P}$、exact groundでのproxyを$g_{0,P}$とする。

$$
\boxed{
\widehat f_{\psi,P}-\delta_P
=
\underbrace{(\widehat f_{\psi,P}-g_{\psi,P})}_{\text{モデル・外挿誤差}}
+
\underbrace{(g_{\psi,P}-g_{0,P})}_{\text{状態置換誤差}}
+
\underbrace{(g_{0,P}-\delta_P)}_{\text{proxyと固有値の差}}
}
$$

これは足し引きによる恒等式である。新規定理ではないが、原因の誤認を避けるための実験設計として重要である。各量を同じH/P/$\tau$で測る。符号付き成分を保存し、絶対値の和と、符号付き合計の両方を報告する。

数値誤差は第四の監査項として別に見積もる。数値誤差が機構差と同程度なら、その点を機構の根拠にしない。

### 4.5 相殺・状態感度・有限時間寄与を分ける

対称4次PFの局所的な有効Hamiltonianを

$$
H_{\mathrm{eff}}=H+\tau^4D_4+\tau^6D_6+\tau^8D_8+\cdots
$$

とする。$a_4=\langle0|D_4|0\rangle$、$Q=I-|0\rangle\langle0|$について、

$$
\chi_4=\frac{|a_4|}{\|D_4\|},\qquad
b_4=\|QD_4|0\rangle\|,\qquad
s_4=\frac{b_4}{|a_4|}
$$

を診断する。$a_4\approx0$では$s_4$が発散するので、$b_4$と絶対誤差を必ず併記する。比だけで危険・安全を分類しない。

非縮退摂動論では

$$
a_8=\langle0|D_8|0\rangle+
\sum_{n\ne0}\frac{|\langle n|D_4|0\rangle|^2}{E_0-E_n}.
$$

係数内相殺、異なる時間次数間相殺、近似状態での期待値相殺を別の現象として記録する。F02の小さい正味$a_8$は、有限時間全域の滑らかさや二項モデルの成功を単独で証明しない。[R4]

一項モデルによる時刻の選択では

$$
\tau_{\mathrm{ana}}=\left(\frac{\epsilon_E}{5|a_4|}\right)^{1/4},
\qquad
\frac{|a_6|\tau_{\mathrm{ana}}^6}{\epsilon_E}
=\frac{|a_6|\epsilon_E^{1/2}}{5^{3/2}|a_4|^{3/2}}.
$$

この関係は、$a_4$だけが小さくなると使用時刻で高次項が重要になる可能性を示す。$a_6$も同時に小さくなる場合まで不安定と結論しない。$a_4=0$にこの式を適用しない。

### 4.6 exact状態でもproxyと固有値は同じとは限らない

さらに、上記の局所・非縮退・対称4次の仮定では、exact groundのecho proxyは

$$
g_{0,P}(\tau)=a_4\tau^4+a_6\tau^6+
\langle0|D_8|0\rangle\tau^8+O(\tau^{10})
$$

となるため、

$$
g_{0,P}(\tau)-\delta_P(\tau)
=-\tau^8\sum_{n\ne0}
\frac{|\langle n|D_4|0\rangle|^2}{E_0-E_n}
+O(\tau^{10})
$$

という検証可能な予測を得る。ここでもIm版と連続なarg版は表示次数まで同じになる。

これは「正しい状態を使えばproxyは常に正しい固有値誤差になる」という扱いを避けるために重要である。F02で得た状態混合量を、三分解の第三項と同じH/P上で直接照合できる。係数内部の相殺と、proxyの有限時間誤差を結ぶ具体的な第一候補である。

この局所式は本計画の解析から得た予測であり、分子データで既に照合済みとはしない。標準的な摂動論を出発点とし、小行列の独立計算、既存F02の演算子参照、直接PF枝の三者で確認する。形式次数残差や枝の問題がある範囲へ延長しない。

---

## 5. 最初に追加しておきたい競合機構：proxyの時間対称性

### 5.1 なぜ必要か

対称PFでは$H_{\mathrm{eff}}(\tau)$は局所的に偶関数になる。しかし、**非定常な任意の状態に対する非対称echoのscalar proxyまで、必ず偶数次だけになるとは限らない。**

H02は複素位相$0,\pi/2,\pi,3\pi/2$を持つ制御状態に対し、非対称echoのargを$\tau^4,\tau^6$だけでfitしている。[R11] これはH02の反例を否定しないが、校正値の変化をすべて「小さい$a_4$の相殺感度」に帰属する前に、proxy自体の奇数次を切り分ける必要がある。

### 5.2 局所展開の予測

上記の符号・echo定義で、Im版の演算子を局所展開すると

$$
A_P(\tau)
=\tau^4D_4
+\frac{\tau^5}{2i}[H,D_4]
+\tau^6\left(D_6-\frac{1}{6}[H,[H,D_4]]\right)
+O(\tau^7).
$$

arg版も、小時間で振幅が1に近く連続なargを取る範囲では、表示した次数まで同じ係数を持つ。

exactなH固有状態では交換子の期待値が消える。実行列H・群と実ベクトル状態を使える条件でも、表示した$\tau^5$の期待値は消える。一方、一般の複素状態では消えるとは限らない。

したがって、$\langle\psi|D_6|\psi\rangle$を近似状態echoの$\tau^6$係数そのものと置くことも、無条件にはできない。

**位置付け：本計画で導出した検証用の数理予測。既存分子データで支配性を確認した結果ではない。** 2×2の解析的な有効Hamiltonian例について高精度行列指数による局所整合を確認したが、これはリポジトリの分子実験の代替ではない。導出と実装の独立チェックを最初の本実験に含める。

### 5.3 小さな判別実験

同一H/P/状態で$+\tau,-\tau$を計算し、

$$
g_{\mathrm{even}}(\tau)=\frac{g(\tau)+g(-\tau)}2,
\quad
g_{\mathrm{odd}}(\tau)=\frac{g(\tau)-g(-\tau)}2
$$

を保存する。realな$0,\pi$の状態対と、complexな$\pi/2,3\pi/2$の対を分ける。負時刻の評価費用も計上する。

偶対称化で改善すれば、proxyの構造を修正すべき場合がある。改善しなければ、状態置換誤差や高次の偶数項を調べる。偶対称化は状態近似誤差を消す処理ではない。

$e^{-iH\tau/2}U_P(\tau)e^{-iH\tau/2}$という対称echoも数学的対照になるが、異なる推定器であり、追加作用と係数の変化を含めて比較する。第一実験では必須の実用候補にしない。

---

## 6. 資源評価を研究の目的と一致させる

### 6.1 固定する簡略モデル

一ステップ費用$K_P$、連続QPE定数$\beta$を明示し、

$$
C_P(\tau;e)=\frac{\beta K_P}{\tau(\epsilon_E-e)}
$$

を、PF部分の資源proxyとして使用する。分母が非正なら実行不可能であり、微小正数へclipしない。

この式の下で、モデルが出した予算を

$$
B=\gamma\widehat C_P(\widehat\tau),\qquad
\epsilon_{\mathrm{PE}}=\frac{\beta K_P}{\widehat\tau B}
$$

として固定する。$\gamma=1$と既存比較の$1.01$を両方残す。採点後に$B$を真値で修正しない。

### 6.2 精度達成は方向付きで採点する

簡略加算モデルの精度余裕を

$$
S_E=\epsilon_E-\bigl(|\delta_P(\widehat\tau)|+\epsilon_{\mathrm{PE}}\bigr)
$$

とする。$S_E\ge0$はこのproxy内の達成であり、QPEの確率的出力や実機全体の成功保証ではない。

$\widehat e=|\widehat f|$、$\Delta e=|\delta|-\widehat e$とすると、同モデル内では

$$
S_E\ge0
\iff
\Delta e\le(1-\gamma^{-1})(\epsilon_E-\widehat e).
$$

この式から、許される過小評価は一定の相対係数誤差ではなく、残りの誤差予算に依存すると分かる。三分解の符号付き誤差と、この絶対誤差差分を混同しない。

### 6.3 三つの費用比較を分離する

| 指標 | 定義・役割 |
|---|---|
| 同一PF内の時刻選択損失 | 選択時刻で直接誤差を用いた必要費用を、そのPFの基準格子最小と比較する |
| PF選択も含む直接費用損失 | 同じ直接費用を、許されたPF集合全体の基準格子最小と比較する |
| 凍結予算の超過率 | $R_B=B/C_{\mathrm{ref,grid}}-1$。実際に固定した予算と、保存済み基準格子を比較する |

三番目が主要指標である。最初の二つは、損失が刻み幅・PF選択・保守的予算のどこから来たかを説明する。

前レビューで確認されたN2伸長の約42.4%は、$1.01\widehat C/C_{\mathrm{ref,grid}}-1$であり、報告済みの直接費用損失約22.4%とは異なる量である。[R3] 今後は列名にも違いを残す。

### 6.4 基準解の作り方

参照集合$\mathcal S$は、PF・時刻範囲・branchの信頼条件を事前に明示した有限集合とする。直接誤差が$\epsilon_E$未満である点を用い、

$$
C_{\mathrm{ref,grid}}=\min_{(P,\tau)\in\mathcal S} C_P(\tau;|\delta_P(\tau)|)
$$

を作る。

特定のモデルに不合格だったPFを、物理的な基準解から自動的に除外しない。これを除外すると、そのモデル自身に都合のよい最良基準になる。モデル適格性による運用集合と、直接truthによる物理的参照集合を別にする。

一方、枝不明・数値不安定な点をoracle最小に混ぜない。候補集合や時刻格子の違う過去結果同士のregretを、そのまま横比較しない。

### 6.5 古典費用と安全性を別軸で残す

状態生成、群行列・スペクトルの構築、compact BCH、時間発展、追加時刻、fit、選択のそれぞれを計測する。coldとwarmの費用を分離する。古典秒と量子rotation数を、換算規則なしに足し合わせない。

CISD入力だけなら安価、dense D4を作らなければscalable、校正点が少なければ安い、とはしない。特にechoが必要とする$e^{-iH\tau}$の古典作用費用を省かない。[R8][R9][R10][R11]

---

## 7. 最初の本実験：三分解と介入を同一条件でつなぐ

### 7.1 主分子とPF

最初の主分子は保存済みH4、PFはYoshida 4次、`current_m3`、`two_term_center`、`m5_best`とすることを提案する。既存F/Hデータとの接続と、相殺の程度の異なる比較ができるためである。これらは開発条件であり、新しい独立ホールドアウトとは呼ばない。

H2は実装の検算に使う。2電子の完全空間ではCISDがFCIと一致するため、H2のCISD一致だけを「安い近似状態でも一般に十分」の証拠にしない。

H4の同一条件解析が閉じた後、既存HF分子の平衡・伸長対を機構の外部確認として使う。ここでHF分子とHartree–Fock状態を混同しないため、状態名は `rhf_state`、分子名は `HF_molecule` とする。

### 7.2 状態の二群

**実用近似群**：exact、RHF、CISD。利用可能であれば、同じアルゴリズムの収束度を変えた一つの系列を後で追加する。

**機構制御群**：

$$
|\psi(q,\phi,\chi)\rangle=
\sqrt{1-q}|0\rangle+e^{i\phi}\sqrt q|\chi\rangle,
\quad \langle0|\chi\rangle=0.
$$

同じ$q,\chi$で$\phi$だけ変えれば、Hのエネルギー誤差・分散・重なり等を保ったまま、誤差演算子に対する方向を変えられる。異なる$\chi$同士でも全スカラーが同じ、と無条件には主張しない。

方向は、CISDの基底状態直交成分、RHFの同成分、理論上の強結合方向$QD_4|0\rangle$等を候補とする。最後はoracleを用いた最悪方向診断であり、実用状態生成法ではない。PF依存の方向で作った状態は、そのPF内の感度診断に使う。PF間の選択を比べる際には、全PFへ同じ状態を渡す。

### 7.3 固定時刻と、選択によって変わる時刻を分ける

最初は同じ絶対時刻に対して三分解を行う。これにより、「状態によって学習・評価時刻自体が変わった効果」を混ぜずに測れる。

次に、各状態由来の校正だけで学習点・最適時刻を選ぶ本来の運用を行い、予算を凍結する。同じ時刻での感度と、時刻選択まで含む増幅を別の結果として示す。

### 7.4 反事実的な置換による寄与診断

同じ候補集合で、以下をoffline診断として比較する。

- 近似状態proxyをfitした元のモデル。
- 近似状態proxyをより直接に評価し、fit誤差だけを抑えた参照。
- exact状態proxyへ置換した参照。
- 直接固有値誤差を用いた参照。

どの置換で資源差が縮小するかを調べる。ただしこれらはoracleを用いた原因診断であり、実用selectorの成績として計上しない。また非線形な最適化において損失は単純に加算できないため、置換順序への依存と交互作用を残す。

### 7.5 既存の人工族だけでは「相殺だけ」を変えたことにならない

F03の$A(\lambda)=X+\lambda Z, B=Z$では、全Hamiltonianも$X+(\lambda+1)Z$へ変化する。そのため、既存の人工族を「H・ギャップを固定し相殺だけを変えた」と説明しない。

追加の制御案として、

$$
H=X+Z,\quad A(\lambda)=X+\lambda Z,
\quad B(\lambda)=(1-\lambda)Z
$$

を使う。同じYoshida4合成で全H・固有状態・物理ギャップ・群数を固定し、分割に伴う係数構造を変えられる。

この案の小行列形式級数では、非自明な$a_4$零点候補$\lambda=-2+\sqrt{15}$で、$D_4$が非零のまま$a_4$が消えることを高精度で確認した。これは本計画内の数学的試作であり、リポジトリの完了結果ではない。Codex実装では独立に検算し、再現しなければこの零点値を使わない。

この分割でも群ノルムや高次係数は変わる。したがって「$a_4$だけの単独介入」とは呼ばず、変化した演算子・係数をすべて記録する。必要なら形式的な有効Hamiltonianで対角成分だけを変える理論対照を別に作るが、実装可能なPFと混同しない。

### 7.6 何が出たら次へ進めるか

同一H/Pの因果接続は、「全部の矢印で悪化した」という結果でなくてよい。

| 結果 | 解釈・次の課題 |
|---|---|
| 状態置換誤差が支配し、凍結配分に影響 | 状態方向を捉える診断・状態改善が候補 |
| proxy–固有値差が支配 | 同じproxyのfit精度を上げても限界。推定器や適用時刻を見直す |
| model–proxy差が支配 | 追加点・構造に合うモデル・適応時刻が候補 |
| 複素状態の奇数次が支配 | 偶数次モデルの適用条件を修正。real状態での実益を別途確認 |
| 係数は敏感だが予算・時刻選択は頑健 | 高精度校正の必要性を減らす方向が候補 |
| 枝・数値精度が支配 | その点で機構結論を出さず、計算経路を修正 |

この段階で原因を二つ以上の競合説明から識別できれば、最初の本実験は完了とする。仮説に合う分子を探して追加し続けない。

---

## 8. 得られた機構から、改善法を一つに絞る

### 8.1 改善する箇所を間違えない

同じ近似状態の同じproxyを一点追加しても、状態置換バイアスやproxy–固有値差は原理的には解消しない。追加点は主としてmodel–proxy誤差の改善である。この区別を方式選定の基準にする。

### 8.2 三つの候補から、根拠のある一つだけを進める

| 支配する誤差 | 第一候補 | 必須の比較・限界 |
|---|---|---|
| model–proxy | 予算候補近傍への追加sentinelと、固定した縮小・再fit規則 | 同じ追加点予算を与えた単純法と比較。truthは見ない |
| state substitution | 誤差演算子作用に敏感な状態収束チェック、または一段だけ状態近似を改善 | 状態生成費用を含める。二状態の一致を厳密保証にしない |
| proxy–eigenvalue／parity | proxyの対称性に合うfit、偶対称化、またはoperatorベースの限定的補正 | 追加作用費用、state bias、高次補正の取得費用を残す |

複数が同程度に支配する場合には、まず適用範囲を限定した方式を作る。危険指標を後付けで多数積んだ複雑なselectorを作らない。

### 8.3 主要ベースライン

最終比較には少なくとも以下を入れる。具体的な余裕倍率や時刻縮小は開発段階で候補を決め、本評価前に固定する。

- `current_m3`固定＋同じ校正・同じ余裕。
- Yoshida4固定＋同じ校正・同じ余裕。
- 現在の二PF selectorそのまま。
- 同じ追加古典計算を使う、単純な追加点または保守的刻み幅法。

「複数PF選択」の利点がない場合は、固定PFの刻み幅校正として論文をまとめる。全条件で同じPFが選ばれることを失敗扱いしないが、選択器の価値を主張しない。

### 8.4 アブレーション

改善法の有効な部分を特定するため、基準法、新しい診断のみ、fallbackのみ、両者の組合せを比較する。診断が全条件で不発だった場合には、その診断のおかげで成功したと解釈しない。

### 8.5 実用性の到達レベルを区別する

1. 小系のtruthを使った性能上限・機構参照。
2. 選択時にexact ground/direct truthを使わない小系実装。
3. 状態・演算子の表現を含め、対象サイズで古典費用が抑えられる実装。
4. 独立分子群での固定規則評価。
5. 制御回路、状態準備、測定分布を含めたQPE全体での実益。

現在のpractical最小版は主に2の開発評価である。3〜5を一括して達成済みと呼ばない。中核成果Aのために5まで要求しない。

---

## 9. 具体的な実行順序と中間報告

以下は日数見積もりではなく、成果物と判断で区切る工程である。

| 工程 | 作業 | 成果物 | 次へ進む条件 |
|---|---|---|---|
| S0 | 既存結果の確定、6選択点の正確な採点 | 原予算を保持したexact-time採点と二種類の費用比較 | 枝・符号・数値精度・予算定義が整合 |
| S1 | proxy定義、三分解、時間対称性の実装 | 解析2×2例とH2の単体テスト、推定量対応表 | 分解が再構成でき、Im/arg・符号の取り違えがない |
| S2 | H4・固定H人工系で同一条件介入 | 原因別曲線、状態対、凍結配分、反事実比較 | 支配誤差または頑健性の理由が絞れる |
| S3 | HF成功・破綻対等への限定接続、理論の整理 | 機構が移る条件・移らない条件、条件付き関係 | 中核主張と適用範囲を一文で言える |
| S4 | 支配誤差に応じた改善法を一つ固定 | 強い基準法との開発比較とアブレーション | 実益があれば独立評価へ。なければAを完成させる |
| S5 | 必要な範囲の独立評価・論文・再現パッケージ | 凍結プロトコルの評価、図、主張台帳、原稿 | 主張を支える比較がそろい、残る限界を明記できる |

### S3実行記録（2026年9月25日）

S3は追加計算を行わない回顧的証拠統合として完了した。第一研究の三分解、H01、HF
mechanism bridge、S0 exact-time採点をsource identity付きで接続し、状態置換軸と
exact-state有限時間演算子軸を同一原因へ潰さず整理した。

- 統合報告：[`PF_first_study_s3_hf_connection_20260925.md`](PF_first_study_s3_hf_connection_20260925.md)
- 機械可読判断：[`decision.json`](artifacts/pf_first_study_s3_hf_connection_20260925/decision.json)
- status：`complete_retrospective_synthesis`
- 新direct truth点、新Hamiltonian、新fit：すべて0。

S3の結果、S4候補はoperator-sensitiveな二状態収束診断と事前固定fallbackの一方式へ
限定した。この方式は後述のS4専用protocolでthreshold、fallback、費用、baseline、
ablationをtruth前に固定して実行した。

### S4実行記録（2026年9月25日）

S4は6条件×7 strategyをPhase Aで固定し、Phase B v1.1で20 unique selection、60挿入
direct点、12 uniform anchorを採点した。全source/numerical gateは合格した。

- S4 Phase A commit：`95ed24c74bb29d883bbaf76d4578ff7af08ed995`
- S4 Phase B v1.1結果commit：`4d831b52475a7399b74a048a7471eaba6c4527c0`
- status：`complete_no_benefit`
- targeted fallback：$\gamma=1.01$で6/6安全、平均主regret`42.8416%`。
- practical baseline：$\gamma=1.01$で6/6安全、平均主regret`42.8416%`。
- baseline比平均regret改善：`0%`（固定必要条件10%以上に不合格）。
- equal-cost 7点fit：平均主regret`42.3828%`で、相対改善は約`1.07%`。

診断はHFの`current_m3`でstate riskを記録したが、targeted fallbackの選択結果を改善
しなかった。従って同じdevelopment集合で閾値や診断を調整せず、S5の独立評価には
進まない。これは無効runではなく、事前固定基準による有効なnegative resultである。

### 第1回の進捗共有

S0/S1と、H4の代表PFのS2が一通りそろった時点。持ってくるものは、追加の長い検証一覧ではなく、三分解図、real/complex対照、実際の固定予算、どの説明が有力かの一枚の判断表とする。

### 第2回の進捗共有

S2/S3の完了時。ここで中核成果Aの論文構成を確定する。改善法Bを行う理由が得られた場合だけ、S4の一方式を選ぶ。

### 最終の進捗共有

S4は`complete_no_benefit`で終了したため、S5を開かずに方式・主張を凍結した。今後
別研究として独立評価を設計する場合も、新しい分子結果を見て方式へ戻らず、一度見た
集合を以後の開発集合として扱う。

### 並行化

数理・小行列・H4解析はローカルで進めやすい。既存6点のdirect採点や、大きい保存セクターを扱う部分はサーバー候補とするが、CPU/GPUは代表点の時間とメモリで選ぶ。GPU使用は研究条件ではない。

論文の導入・既存研究との差分・定義・図の設計はS1から並行して書く。すべての実験後に初めて論旨を考える進め方は避ける。

---

## 10. 理論として狙う成果と、狙いすぎない範囲

### 10.1 最初に確立する基準関係

Im proxyのHermitian演算子Aに対し、$a_0=\langle0|A|0\rangle$、$b=\|QA|0\rangle\|$とする。

$$
|\psi\rangle=\sqrt{1-q}|0\rangle+e^{i\phi}\sqrt q|\chi\rangle
$$

なら、厳密に

$$
\langle A\rangle_\psi-a_0
=q(\langle\chi|A|\chi\rangle-a_0)
+2\sqrt{q(1-q)}\operatorname{Re}
[e^{i\phi}\langle0|A|\chi\rangle].
$$

したがって

$$
|\langle A\rangle_\psi-a_0|
\le 2\sqrt{q(1-q)}b
+q\|Q(A-a_0I)Q\|.
$$

これは標準的な分解・ノルム評価であり、新規性を主張しない。ここから、どの状態方向が最悪か、どの時刻で目標精度に対して無視できないか、どの量を安く近似できるかを、対象PF上で明らかにする。

### 10.2 「スカラーでは不可能」の言い過ぎを避ける

H02は、同じスカラーから有限時間校正量が一意には決まらないことを示す。一方、忠実度、演算子ノルム、ギャップ等の追加情報があれば保守的な境界を作れる場合がある。「状態エネルギーや分散は一切役に立たない」とは書かない。

上記のqやexact枝を使う理論境界は、まず機構診断用である。選択時にqを使うには、別の近似・認証・事前情報が必要で、その費用と仮定を示す。

### 10.3 最適時刻の平坦さ

一項モデルで次数p、一ステップ費用が固定なら、$x=\tau/\tau_{\rm ana}$に対し

$$
\frac{C(\tau)}{C(\tau_{\rm ana})}
=\frac{p}{(p+1)x-x^{p+1}}
=1+\frac{p+1}{2}(x-1)^2+O((x-1)^3).
$$

これは、係数・時刻の誤差があっても直接費用損失が小さい理由の基準になる。境界最適、誤差ゼロ交差、合成費用による$K(\tau)$依存へ無条件に延長しない。

### 10.4 強い理論成果の候補

次のいずれか一つが定量的に示せれば、中核成果の価値が強くなる。

- 相殺と状態方向を含む、有限時間proxy誤差の適用域・境界。
- calibrationの精度から凍結配分の達成条件へ変換する、対象構造を活かした鋭い評価。
- 少数校正点が一致しても配分結果が異なる構成例と、その非識別性を解く追加情報。
- 係数の相対精度を要求しなくても、配分を保てる十分条件。

全分子・全時刻の一様で鋭い上界を、最初の研究の必須条件にはしない。条件付きの命題を出すなら、真値を含む高価な量と、運用時に取得できる量を分ける。

---

## 11. 既存研究との差分と、本プロジェクト固有の貢献候補

| 一次文献 | 既に扱っていること | 本研究が追加しなければならないこと |
|---|---|---|
| Yi–Crosson [L1] | 固有状態に近い入力に対するPFの固有値・固有ベクトルの摂動解析 | 本研究の対称4次・有限時間proxy・近似状態校正・凍結配分への接続 |
| Mehendale et al. [L2] | 分子の固有値誤差推定、CISDによる近似、分割の資源比較 | 相殺に敏感なPF、proxy差、有限時間と配分結果の三分解・適用条件 |
| Maxwell et al. [L3] | 漸近的な対角誤差構造、compact BCH、重要成分選別、大規模応用 | その既知技術を評価backendとして使い、校正の信頼性・意思決定を検証 |
| Morales et al. [L4] | PFの次数・長さを跨ぐ比較と係数設計 | 係数設計とは別に、推定に使える情報と有限時間配分の信頼性を明示 |
| Tran et al. [L5] | Trotter step間の誤差干渉 | 一つの固有値係数内部の相殺と、状態・proxy感度の区別 |
| Bay-Smidt et al. [L6] | 低励起状態間のエネルギー差での相殺、スペクトル評価 | 今回は主として単一基底状態の係数・校正内部の相殺を扱う |
| Rendon et al. [L7] | Trotter刻みをゼロへ外挿する補間・誤差解析 | 今回は有限刻みを選ぶ校正。エネルギー外挿法を提案する場合は別途費用比較 |
| Abe et al. [L8] | 水素鎖での高次PF・回転数・RZ深さの比較 | 今後は順位そのものだけでなく、その順位をどこまで信頼して選べるかを調べる |

「係数内相殺」という単語の違いだけで新規性は成立しない。先行研究で既知の期待値・摂動構造を使いながら、未解決の校正―配分の問題に、どの新しい予測・境界・方法を与えたかで示す。

文献調査は本書の主張に関係する一次文献を確認した範囲であり、網羅的な新規性証明ではない。原稿の各主要主張を既存研究と対応させる表を更新する。

### 11.1 既存論文との関係

前論文は「与えられた誤差評価からどのPFが低コストか」を扱い、今後の研究は「その誤差評価をどの条件で信頼して使えるか」を扱う、と区別する。異なるHamiltonian・係数版・grouping・精度の結果を用いて、前論文全体の結論を遡及的に否定しない。

もし同じ条件の再評価で旧結果に修正が必要なら、その修正は新研究の成果とは別に透明に管理する。整合性の修正を、新規な方法の優位として数えない。

---

## 12. 論文・発表の構成案

### 中核版：機構と校正の信頼性

1. **問題設定**：有限時間で実際に使うPF刻み幅を、近似的な古典情報から決める必要がある。
2. **評価量の区別**：固有値シフト、Im/arg proxy、フィットモデル、凍結予算。
3. **理論の予測**：状態方向、proxyの偶奇性、先頭係数相殺と高次寄与。
4. **同一条件での機構実験**：固定H人工系とH4の介入、反事実診断。
5. **資源配分への影響**：過小配分、過大配分、平坦な最小点での頑健性。
6. **分子への適用範囲**：成功例・破綻例の限定比較。
7. **含意と限界**：どの追加情報が必要か、何を一般化しないか。

### 方法論拡張版

上記に、選んだ一つの校正改善、単純基準・アブレーション・独立評価を追加する。方法が複雑になるだけで利益がない場合、無理に方法論論文へ見せない。

### 主図の案

| 図 | 伝える結論 |
|---|---|
| 図1 | 同じ小さい短時間係数でも、有限時間と状態置換で異なる配分になる問題設定 |
| 図2 | 同一H/Pでの三分解と、どの成分が支配するか |
| 図3 | 状態方向・real/complex・proxy偶奇性の判別 |
| 図4 | 相殺、時間刻み、状態品質と凍結予算の関係。人工系と分子例を区別 |
| 図5 | 単純基準と提案診断／校正の精度―凍結資源―古典費用比較 |
| 図6 | 必要な場合だけ独立評価と適用外・棄却の結果 |

図の枚数は目安であり、各実験の全表を主図へ詰め込まない。

---

## 13. 再現性・コード構成・成果物

### 13.1 既存結果は不変

開始時にローカル作業と全結果ブランチを確認し、S0等が既に完了していれば再計算しない。基準索引はe820…で固定し、後続の修正結果は別のcommit/manifestとして接続する。

異なる結果ブランチのコードを一括mergeして動かさない。必要な機能を明示して取り込み、共通の小系sentinelを通す。未完了・欠損・retryを成功例へ混ぜない。

### 13.2 新規モジュール案

以下は提案名であり、現在存在すると主張するものではない。

```text
src/trotterlib/calibration_observables.py    # Im/arg/symmetry、符号・unwrap
src/trotterlib/calibration_error_budget.py  # 三分解、absolute gap、予算余裕
src/trotterlib/frozen_allocation.py         # 選択とread-only採点の分離
review_response/run_calibration_bridge.py  # 本実験の入口
review_tests/test_calibration_observables.py
review_tests/test_calibration_bridge.py
artifacts/calibration_bridge_<date>_<sha>/
```

既存 `sector_pf`、`component_sector_pf`、PF列、H01 action backend、compact D4 backendは、実際の版と依存関係を確認して再利用する。既存ファイルの大規模改名は行わない。

### 13.3 最低限のデータ

```text
protocol.json              係数、H、状態、時刻、fit、reference、判定規則
input_manifest.json        各入力hash、元commit、データ使用履歴
observables.csv            delta_direct、g_exact、g_approx、fitted、even/odd
error_decomposition.csv    三つの符号付き誤差、数値誤差、再構成残差
states.csv                 状態生成法、q、phase、エネルギー、分散、oracle診断
branch_audit.csv           ground/previous overlap、unwrap、固有対残差
predictions.json           truth採点前のP、tau、epsilon_PE、予算
scoring.csv               exact-time error、gamma1/1.01、R_time/R_choice/R_budget
counterfactuals.csv         offline置換比較。実用成績と明確に分離
resources.csv              cold/warm、CPU/GPU、メモリ、状態/群準備、追加作用
report.md                  証拠、反例、採否、次に行う工程
```

`selected_time`と`scored_time`、proxy由来係数と形式BCH係数、物理的reference最小とmodel適格集合最小を別列にする。新しい本実験の主採点では両時刻を一致させる。

### 13.4 数値健全性の扱い

固定した精度・窓変更のチェックで、結論に使う差が数値雑音と分離しているか確認する。小係数の相対誤差だけで判定せず、$\tau^j\Delta a_j/\epsilon_E$も保存する。

高精度演算子、有限窓fit、直接固有値fitは独立した参照として扱う。良い曲線fitから小さい高次係数の同定までできたと結論しない。全テストが緑でない場合、入力欠損・既存artifact依存・本実験の数値失敗を分離して報告する。

---

## 14. 続けない作業と、再開する条件

| 現時点で続けないこと | 再開する条件 |
|---|---|
| 新PF係数の大量探索 | 校正法を固定した比較で既存PFの明確な不足が残る |
| 全分子・全基底へ一律拡張 | 主張する適用範囲と方式が固定され、独立評価が必要になる |
| F/Hの分解をさらに細かく増やす | その量が新しい判別予測または改善に直接必要 |
| CA〜CA/100のcoverage全面補完 | 精度依存そのものを主張に含める、または対象領域の順位が未判定 |
| 6次・8次へ同じ機構を一般化 | 4次で論旨が成立し、一般化する追加主張と計算範囲が決まる |
| 完全FTQC runtime・qubitization競争 | 本研究の具体的主張がその比較を必要とする |
| エネルギー差・外挿への本格転換 | 単一エネルギーの校正より明確な価値があり、別の誤差・費用設計を行う |

スコープ外に置くことは価値を否定することではない。今回の論文で何を答えるかを明確にするための判断である。

---

## 15. 研究判断の台帳

各中間報告で、次の五行を更新する。

1. **現在の主張**：一文で、対象と目的量まで書く。
2. **支持する証拠**：同一条件の結果・構成例・固定評価を列挙する。
3. **反対または例外の証拠**：主張に都合の悪い条件も残す。
4. **未確定の因果関係**：相関、数理予測、介入結果を区別する。
5. **次の一工程と終了条件**：カタログから新項目を無制限に追加しない。

第一研究終了時の状態は以下である。

- 現在の主張：対称4次PFの有限時間校正では状態置換が主要誤差軸になり得るが、精度上の安全性と資源効率は別であり、通常の状態品質量や今回の二状態診断だけでは低regretな選択を保証できない。
- 支持：S1/S2の79/128状態置換誤差支配、S0の$\gamma=1.01$安全6/6と最大regret 114%、S3のHF限定接続、S4の固定7-strategy比較。
- 反対・例外：状態置換誤差が全caseで支配するわけではなく、S4ではdiagnosticがriskを検出してもtargeted fallbackの平均regret改善は`0%`だった。
- 未確定：別の安価な演算子感度情報で安全性と効率を同時改善できるか、また独立分子で1%余裕が維持されるか。ただし本研究内では追試しない。
- 次：追加計算ではなく、中核成果Aの論文、図、主張台帳、再現パッケージを完成させる。

---

## 16. 最終的な推奨

**主題は確定した。** 「対称4次PFの有限時間固有値誤差校正を、資源配分にどこまで信頼して使えるか」を中心にする。

第一成果は、相殺を含む機構の同一条件解析と、配分に必要な精度・情報の理解に置く。
S4で選んだ一つの改善法は固定benefit基準を満たさなかったため、方法論上の成功や
独立transferを主張しない。negative resultを含めて中核成果Aを完成させ、新しいPF、
S5、追加diagnosticは別研究の条件付き課題とする。

これにより、今後は探索的な検証を増やす段階ではなく、確定した問いと結果を論文・
再現パッケージへまとめる段階である。

---

## 参考資料：固定GitHub結果と一次文献

リンクはブラウザから読める固定commitまたは一次文献である。ローカル `/home/...` やChatGPT内部参照を、公開の出典として使わない。

### 固定結果

- **[R1]** [現在の研究方針と検証状況](https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/e820f653a5916f27233ab4674a89d288cf969e37/docs/current_research_status.md)。
- **[R2]** [未使用分子固定ホールドアウト](https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/33a761d44a24022ad61192c41a196dd4cb3afbca/artifacts/server_unused_molecule_frozen_holdout_20260921_d288797/aggregate/report.md)。
- **[R3]** [practical calibration最小版：報告](https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/4f4374bdf4dbcb7d8e1d14f9682570c221e4c88a/artifacts/server_practical_calibration_minimal_20260923_79035cc/report.md)。
- **[R4]** [F02：4次PFの8次項と状態混合](https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/6d13384ef327e5b248c2ce93ae29ad4e7686b2e5/artifacts/prevalidation_f02_tau8_state_mixing_20260921_retry3/report.md)。
- **[R5]** [F03：小さいa4と誤差演算子の区別](https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/e820f653a5916f27233ab4674a89d288cf969e37/artifacts/prevalidation_f03_a4_operator_cancellation_20260922_retry2/report.md)。
- **[R6]** [H02：有限時間制御状態診断](https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/16bd6c264e0e2de6d86b0a785c9bc449ebbd4dfe/artifacts/server_h02_finite_time_controlled_state_20260922_a228b5f/report.md)。
- **[R7]** [HF分子の成功・破綻機構比較](https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/6eb1aa02f1d28904741b2cee4f70347e1203198f/artifacts/server_f_hf_mechanism_bridge_retry1_20260923_221c7c3/report.md)。
- **[R8]** [D04：同一古典予算比較](https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/6d13384ef327e5b248c2ce93ae29ad4e7686b2e5/artifacts/prevalidation_d04_equal_classical_budget_20260922/report.md)。
- **[R9]** [H04：compact BCHと重要成分選別](https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/6d13384ef327e5b248c2ce93ae29ad4e7686b2e5/artifacts/prevalidation_h04_compact_bch_importance_20260922_retry1/report.md)。
- **[R10]** [H05：a6/a8取得法](https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/6d13384ef327e5b248c2ce93ae29ad4e7686b2e5/artifacts/prevalidation_h05_higher_order_acquisition_20260922_retry2/report.md)。
- **[R11]** [H02の固定プロトコル](https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/16bd6c264e0e2de6d86b0a785c9bc449ebbd4dfe/review_response/h02_finite_time_controlled_state_protocol.json)。
- **[R12]** [M01：資源指標感度](https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/b5af6996159b3dfbd6e5bb3cc2467cb23155906d/artifacts/prevalidation_m01_resource_metric_sensitivity_20260925_3b6e5f0/report.md)。
- **[R13]** [D03：精度別coverage](https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/a8b9a92c9fcdb1b4187d5aa3c239ed8b7443dcfd/artifacts/server_d03_target_accuracy_followup_20260923_748b3d4/coverage_summary.csv)。
- **[R14]** [完了結果の総合索引](https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/e820f653a5916f27233ab4674a89d288cf969e37/docs/prevalidation_results_index.md)。
- **[R15]** [第一研究S4固定比較](https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/4d831b52475a7399b74a048a7471eaba6c4527c0/artifacts/server_pf_first_study_s4_state_convergence_v1_1_20260925_96699df/report.md)。

[R3] の定義・数値を確認する補助資料：

- [protocol.json](https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/4f4374bdf4dbcb7d8e1d14f9682570c221e4c88a/artifacts/server_practical_calibration_minimal_20260923_79035cc/protocol.json)
- [predictions.json](https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/4f4374bdf4dbcb7d8e1d14f9682570c221e4c88a/artifacts/server_practical_calibration_minimal_20260923_79035cc/predictions.json)
- [audit.json](https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/4f4374bdf4dbcb7d8e1d14f9682570c221e4c88a/artifacts/server_practical_calibration_minimal_20260923_79035cc/audit.json)

[R11] の実装照合：[H02 runner](https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/16bd6c264e0e2de6d86b0a785c9bc449ebbd4dfe/review_response/run_h02_finite_time_controlled_state_diagnosis.py)。特に `_echo_models` を参照。

### 一次文献

- **[L1]** Changhao Yi and Elizabeth Crosson, *Spectral Analysis of Product Formulas for Quantum Simulation* (2021). [一次資料](https://arxiv.org/abs/2102.12655)
- **[L2]** Shashank G. Mehendale et al., *Estimating Trotter Approximation Errors to Optimize Hamiltonian Partitioning for Lower Eigenvalue Errors*, arXiv:2312.13282v3. [一次資料](https://arxiv.org/html/2312.13282v3)
- **[L3]** William Maxwell et al., *Practical Estimation of Trotter Error for Hamiltonian Simulation*, arXiv:2606.30738v1 (2026). [一次資料](https://arxiv.org/html/2606.30738v1)
- **[L4]** Mauro E. S. Morales et al., *Selection and improvement of product formulae for best performance of quantum simulation*, arXiv:2210.15817v3; Quantum Information & Computation 25 (2025), DOI:10.2478/qic-2025-0001. 旧版の題名はGreatly improved higher-order product formulae for quantum simulation。 [一次資料](https://arxiv.org/abs/2210.15817v3)
- **[L5]** Minh C. Tran et al., *Destructive Error Interference in Product-Formula Lattice Simulation*, Physical Review Letters 124, 220502 (2020). [一次資料](https://journals.aps.org/prl/abstract/10.1103/PhysRevLett.124.220502)
- **[L6]** Andreas Juul Bay-Smidt et al., *Quantum simulation of nanographenes and Trotter error cancellation*, arXiv:2605.00745v2 (2026). [一次資料](https://arxiv.org/abs/2605.00745v2)
- **[L7]** Gumaro Rendon, Jacob Watkins, Nathan Wiebe, *Improved Accuracy for Trotter Simulations Using Chebyshev Interpolation*, Quantum 8, 1266 (2024); arXiv:2212.14144v4. [一次資料](https://arxiv.org/abs/2212.14144v4)
- **[L8]** Hiromu Abe et al., *Evaluating higher-order product formulae for molecular ground-state energy estimation*, arXiv:2605.30967v1 (2026). [一次資料](https://arxiv.org/abs/2605.30967v1)

文献情報の確認日：2026年9月25日。プレプリントの内容・題名は版を固定して比較する。上記参考文献の標準的な結果を、本研究の新規な発見として書かない。
