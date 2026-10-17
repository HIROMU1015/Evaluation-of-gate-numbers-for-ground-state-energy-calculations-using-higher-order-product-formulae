# 新アルゴリズム研究戦略の独立科学レビュー

**日付：2026-10-17（JST）**  
**対象：Evaluation / Partially Randomized Trotterの既存研究との重複を避けた、次の独立アルゴリズム研究**  
**レビュー区分：Level 1**  
**開始承認：このチャットでのユーザー指示「レビューを開始して　丁寧に考えて」**

本書は承認された科学レビューの完成記録である。研究方針の正式採択、他系列の再開、数値実験・科学用記号計算・回路実装の実行承認を兼ねない。リポジトリへの書込み・状態変更・pushは行っていない。

---

## 1. 結論

### 1.1 推奨する研究判断

独立した新アルゴリズムを目指す研究は維持する。ただし、このチャットの次の主題を、PF係数・分割・外挿・相対形式誤差保証・乱択lawの追加改良にはしない。これらは両リポジトリで既に広範囲に扱われ、A2等には他チャットで具体的な進展もある。[G1–G5]

B′＋A′、すなわち「同条件の強いbaselineを確認し、差を具体的な構成問題にする」という考え方は有用である。ただし、完成した生成規則、普遍的に最強の対照、総E0費用の証明を探索開始の条件として要求する形では採用しない。既知手法との対応を早く調べることと、既知要素を使う研究を排除することは別である。

次に優先して構成を試みる方向は一つに絞る。

> **電子Hamiltonianの係数から、粒子数を保ちながら低エネルギー側へ確率重みを移す量子チャネルの遷移規則を生成する研究。特に、局所的な下降遷移では捕捉される状態を扱う集団的遷移を、非可換な電子相互作用の下で実装可能な操作列にする。**

これは「散逸・冷却を使うこと」の新提案ではない。冷却、ランダムな浴周波数、補助qubitのreset、スペクトルフィルタ付きjump、任意高次のLindbladシミュレーションは既に研究されている。[L1–L4] 新しい可能性があるとすれば、**どの遷移を、どのHamiltonian係数から、どの有限費用で生成するか**という構成部分である。

### 1.2 今回得たもの／得ていないもの

| 区分 | 今回の結果 |
|---|---|
| 研究戦略レビュー | 完了。既存研究との境界、過去の探索基準の修正、次の構成課題を提示 |
| 次に検討する研究方向 | 上記の状態準備・遷移生成方向を条件付きで推奨 |
| 完成した独立新アルゴリズム | 0件。新規性・効率性を認定した構成はない |
| 今回の紙上考察 | フィルタの遷移支持不変性、局所下降則の捕捉例、二電子resetの実制御写像と非可換項の障害、E0精度への十分条件 |
| 新しい一般定理の優先権 | 認定しない。紙上考察は設計診断であり、独立した新規性を主張しない |
| 新規科学数値計算 | 0件 |
| 研究状態・SOURCE変更 | 0件 |

「構成すべき対象を示した」と「その構成が得られた」は分ける。本書の推薦は、未検証の成功を前提にした正式採択ではない。

---

## 2. 根拠の種類と取得範囲

以下を区別する。

- **資料由来**：固定GitHub資料に記載された結果・状態・適用範囲。
- **外部文献由来**：今回取得した一次文献の、実際に確認した箇所。
- **本レビューの判断**：それらに基づく研究戦略・優先作業の提案。
- **本レビューの紙上考察**：明示した式からこの場で導いた設計診断。計算機実験でも既存資料の主張でもない。

### 2.1 固定したリポジトリ資料

| ID | 資料 | 固定commit・今回の確認 |
|---|---|---|
| G1 | Evaluationの2リポジトリ横断handoff | `609a63231ee0786cf8da31f6b33358acfd6f2548`。到達点・競合・未取得範囲を確認 |
| G2 | Evaluation × PRの20方向対応表 | 同上。対応表の主要部分を確認。個々の原論文の全証明を再監査した意味ではない |
| G3 | 2リポジトリ研究一覧 | 同上。研究ID、対象操作、評価量、現在状態の索引を確認 |
| G4 | PR既存20方向マップ | `d09ba606a9fceef806a9313e3f7c43cd21d19e3f`。該当部分を確認。19:09 JST時点の状態を最新と誤認しない |
| G5 | PR最新2ブランチ差分handoff | **`c6419859029824a4ee8c3dfd3c8126fe585ffbe2`**。本レビュー中に公開を発見し、判断用handoff全文を確認 |
| G6 | 研究方法論の横断分析 | `a80596c29e0eaaf7483f8981ed0e61c918335054`。終わり方の表、RC1–RC4を中心に確認 |
| G7 | P1–P8初期handoff | `67d9e3b938b8a03120b836a1c32283b7c9e9a1f0`。初期目的、分類、明示承認・制約を確認 |
| G8 | PR相対形式保証監査handoff | `051df4661eeffb6c6c4c978f70f43eeeaadfddd6`。技術成立範囲、未確定新規性、A2未採択を確認 |

G5は、当初「完了報告待ち」とした差分整理の公開版である。したがって、本レビューを「その差分資料が未到着」という理由で保留する必要はなくなった。ただし、こちらが全7資料のbyte照合を独立再実施したわけではない。取得した文書内容とCodexによる照合報告を区別する。

G5に取り込まれたPRの固定根拠は、A2監査 `051df4661eeffb6c6c4c978f70f43eeeaadfddd6` とH8主要6軸結果 `ce6cd8ead5c0311ec72165c04869e7df4050b75b` である。A2はNOT_ADOPTED、H8は6軸PASSだがPR削減率未更新という区別を維持した。[G5,G8]

### 2.2 実施しなかったこと

全branch・全未保存チャット・全ローカルworktreeをリアルタイムに監査したわけではない。旧Claudeレビュー原本の全回収、過去のsolver証明の独立認証、A2の証明全体の再査読、H8科学値の再集計も実施していない。

外部論文も、取得した版・本文範囲で評価した。出版社の掲載情報と読解したarXiv版がある場合、それらの全式同一性を認定しない。検索結果のAI生成レビューは判断根拠にしない。

---

## 3. 既存研究との境界

### 3.1 このチャットで新研究として取り直さないもの

| 既存領域 | 重複する記録 | 本レビューの扱い |
|---|---|---|
| PF次数・係数・分割・corrector・外挿 | EV-PF/P3、PR BF/BM/H1、C2、R1-P等 | 本チャットの独立新テーマとして改名再開しない |
| Gaussian/frame共有、THRIFT、DF平方・basis費用 | PR Gaussian、M2候補、THRIFT、EV-X1/NA等 | 未取得費用の存在だけを新算法としない |
| 乱択law、return集約、parent配分、共有±label | PR G/D系列、Parent allocation、M1-S | 既存の主題・承認境界を尊重する |
| 有限step相対形式・PSD・energy window | PR SOS-PF A2、R1-P近接領域 | A2を「未着手だから新しい」と再提案しない。A2とR1-Pの同値性も勝手に確定しない |
| H8・強化baseline・native価格 | Track A、Phase C、非相殺会計、6軸compile | 継続中の評価研究へ本チャットを自動合流させない |
| 固有枝校正、state/proxy/fit、widthとbudget | Evaluation第一・第二研究、FS-R1 | 信頼性・誤差評価の既存follow-upと区別する |
| 全固有基底compiler・joint bus閉路 | Q1、P1*/J1 | 現保留・限定否定を保全。別名による再開はしない |

「同じ数式の道具を使う」と「同じ研究課題を繰り返す」は同じではない。例えば、Kraus作用の正値性にPSDを使うことは、単独S2の相対log誤差を評価するA2と同一定理であることを意味しない。しかし、実際の差が保証の言い換えだけなら、新方向として保持すべきではない。[G2,G5]

### 3.2 状態準備方向の位置

取得した研究一覧・20方向マップには、state preparationの費用・overlap・copies・測定との関係が記録されている。一方、**非可換電子Hに対し、係数から集団的な冷却遷移を作る具体的な構成系列**は、この取得範囲では同一案件として特定できなかった。[G2,G3,G4]

これは世界的新規性や、両リポジトリの全履歴で未検討であることの証明ではない。公開されていない別チャットが同じ具体課題を進めていれば、着手前に担当範囲を修正する。

また、P1*/J1のbusは電子unitaryを生成してbusを戻す設計だった。ここで検討するresetは、系に残る非unitaryな状態変化を利用する。P1*の失敗した閉路をpostselectionで救済する案ではなく、別の作用対象・別の研究契約である。[G7]

---

## 4. 過去の探索方針に対する科学的再評価

### 4.1 維持すべき基準

合法な入力情報と取得費を明示すること、scalar・sector・残余を保持すること、既知の強い対照を早期に確認すること、仮説と実証を分けることは維持する。

P1*固定wordの失敗をP1*一般へ広げず、Q1の限定文法の障害を全固有基底変換の不能性へ広げないという境界も正しい。今後も同様に、冷却の一つのcouplerや一つのモデルの失敗を、散逸的状態準備一般の否定にしない。

### 4.2 修正1：既知の道具で書けることを、不保持の一般原則にしない

任意の通常量子回路は既知の普遍gate集合から構成できる。その意味の還元を排除しては、新アルゴリズム研究自体が成立しない。

区別すべき還元は次の四段階である。

1. 目標となるunitaryや出力分布が同じ。
2. 使うprimitive、代数、証明道具が同じ。
3. 係数からの生成手順・前処理・補助情報・誤差伝播まで同じ。
4. 主張する条件・費用・保証まで既存結果に包含される。

1または2だけでは研究価値を否定できない。3と4まで対応し、独立した価値の差がない場合に不保持の根拠が強くなる。

この修正はJ1、Q1、R1-Pの正式状態を取り消すものではない。また、R1-Pの技術的接続を今回新しい論文成果として再採択するものでもない。**今後の一般的な判断基準を修正する**という意味である。

### 4.3 修正2：最終目標より強すぎる構成を当然の必要条件にしない

Q1は全入力coherentな固有基底変換とenergy評価を目標にした。これは明確な数学的課題だが、絶対E0を所定精度で推定するために常に必要ではない。低エネルギー成分へ十分な確率を集め、その後に妥当なenergy読出しを行う別経路がある。

ここで「基底忠実度が高い」「正確なgroundを作れる」「低energy測定結果が高確率で得られる」を区別する。近接励起を許すE0推定は、全固有vectorを解像する問題より弱い出力仕様である。ただし、その弱い仕様を実現する算法が安いことは別途示さなければならない。

### 4.4 修正3：生成規則の発見を、生成規則が既にある候補だけへ限定しない

これまでの指示には、生成規則がないため保留し、再開には新しい生成規則の提示を求める構造が繰り返し現れた。停止管理としては理解できるが、規則そのものを作る研究時間を確保しないと循環する。[G6]

今後は、以下を別の成果物として許容することを推奨する。

- 機構を構成する研究：具体的な操作列、可逆処理、確率更新、またはそれを妨げる明示的障害。
- 構成済み機構の検証：正しさ、既知法対応、有限精度、費用。
- 研究成果としての評価：新規性、適用範囲、強い対照との差、論文化。

第一段階に第三段階の完成を要求しない。逆に第一段階の仮説を、第三段階の成功として報告しない。

### 4.5 修正4：B′＋A′は地図であり、全候補に適用する硬い入場門ではない

同条件のbaselineが複数競合する場合、普遍的な一法を確定するまで研究を始められないわけではない。新しい操作の意義を判別できる関連対照を揃える。

文献で明示されたopen questionは有力な動機だが、それだけが研究問題の供給源ではない。新しい構成から初めて見える問いもある。

総E0費用の接続は重要である。ただし、構成補題の研究開始前に、一般分子・全準備・全readoutの費用証明を完成させる必要はない。どこまでが今回の成果、どこが後段の課題かを記録する。

### 4.6 修正5：少数の失敗を、D1の可能性の尽きた証拠にしない

局所型、対称型、spectral型という整理は過去の候補を理解する分類であって、D1の全算法に対する完全分類定理ではない。各方向が成熟していることも、別の構成が存在しないことを意味しない。

また、紙上確認で過去の候補が区切れたことから、将来の小規模数値実験が無価値とはいえない。科学計算の別承認は維持しつつ、具体的な反例・残差・機構を識別する計算は、必要になった段階で提案すべきである。

既存のone-shot・STOP・試行契約はそのまま守る。将来の全研究に「あと一回で保留」を機械的に適用することは推奨しない。

---

## 5. 外部文献から見た候補空間

### 5.1 冷却は既に確立した研究分野である

Marti–Mansuroglu–Hartmannはfermionic coolingで、free theory由来のcouplerと補助系resetを扱う。[L1]

Ding–Zhan–Preskill–Linは、ランダムなsystem-bath相互作用、forward evolution、再利用する補助qubitによる準備を構成している。確認したarXiv v2の定理では、一般の性能はmixing time等に依存し、明示的な効率保証の模型クラスが分けられている。単に「一つのancillaをresetする」「固有基底を事前に求めない」という点は新規性にならない。[L2]

Schlömerらの2026年稿は、粒子数・spin等を保つ局所couplerとランダムなbath周波数で強相関模型の冷却を示している。spectral connectivityに関するETHの説明はconjectureであり、早期のenergy減衰率の数値挙動は、系サイズ一様の収束時間の証明ではない。著者自身が相互作用系のmixingとLindbladian gapを将来課題に挙げる。[L3]

Zhanらは、quasi-free系や特定の弱相互作用spin/fermion系のrapid mixingを既に扱っている。「弱い相互作用で冷却の収束を示す」だけを未開拓と呼んではならない。[L4]

### 5.2 今回、独立候補としては保持しない言い換え

| 言い換え案 | 判定理由 |
|---|---|
| 1 ancilla＋resetによる冷却 | 既知の具体構成がある [L1,L2] |
| ランダムな局所couplerで相互作用fermionを冷却 | 既知の直接的な先行研究がある [L3] |
| Lindblad発展を高次の拡大unitaryへ写す | 任意高次の構成が既にある [L5] |
| 有限momentからground overlapを評価する | 既知のLP/SDP型の原著がある [L7]。既存N3/A2/情報取得研究とも近い |
| 冷却後の相や相関が合ったことをE0保証とする | 出力仕様が違う。低energy manifoldのphase decision研究も、絶対E0推定とは分ける [L8] |

これらを新候補数を満たすために残さない。

### 5.3 条件付きで残す構成問題

> **局所下降couplerでは到達できない低energy遷移を、電子係数と有限の操作から生成する。非可換な電子Hの下で、実際のチャネルに対する進捗または最終誤差を示し、coupler選択・制御・resetを含む費用を会計する。**

既知冷却の応用一般ではなく、transition generatorの構成問題として限定する。例えば、単粒子移動が局所的なenergy障壁に阻まれるとき、複数電子を一つの遷移として扱う規則を考える。しかし、多電子jump自体を新原理とは呼ばない。どのjumpを係数から選び、どの非可換誤差を制御し、どのクラスで既存の局所couplerより意味のある前進があるかが必要である。

この正確な構成問題について、先行研究全体でのpriorityを確定したわけではない。「今回の検索で同じ式がない」を新規性の根拠にしない。

---

## 6. 本レビューの紙上考察I：フィルタと人口移送を区別する

以下は資料の転記ではなく、本レビューで用いた初等的な設計診断である。新しい定理の優先権は主張しない。

### 6.1 Hの関数だけの非選択測定はground重みを増やさない

Hのspectral projectorをP0、instrumentをM_a=f_a(H)、Σ_a M_a†M_a=Iとする。

\[
\sum_aM_a^\dagger P_0M_a=P_0.
\]

したがって、結果を選別しないチャネルのground-space populationは保存される。

postselectionなら条件付き比率は増え得るが、その成功率・再準備を払う。これはQPEやfilterが無価値という意味ではない。**測定による識別・選別と、実際に人口を移す状態準備とを混同しない**ための確認である。

### 6.2 同じcouplerへのspectral filteringでは、零の遷移を生成できない

Hの固有基底で

\[
\langle i|[H,A]|j\rangle=(E_i-E_j)A_{ij}.
\]

従って、有限多項式fについて

\[
\langle i|f(\operatorname{ad}_H)A|j\rangle
=f(E_i-E_j)A_{ij}.
\]

元からA_ij=0なら、fを変えても零のままである。時間積分型のspectral filterも、定義できる範囲で同じ構造を持つ。既知のjump式 [L4, Eq.(2),(4)] はこの形である。

この事実は「filterを変えても何も改善しない」を意味しない。非零遷移の率や選択性は変えられる。しかし、**存在しない辺を新しく作ることと、既存の辺の重みを変えることは違う**。

複数couplerの積・組合せ、追加の実相互作用、finite-temperature経路等には同じ否定を適用しない。次の構成研究で新しい遷移が必要なら、その生成を式として示す必要がある。

---

## 7. 本レビューの紙上考察II：局所下降規則の具体的な障害

### 7.1 二体電子Hamiltonianの診断family

N電子を、各N個以上のmodeを持つ二群A,Bへ配置する。N_A+N_B=Nと固定し、

\[
H_D=cI-\frac U2\{N_A(N_A-1)+N_B(N_B-1)\}-\mu N_B,
\qquad U>0,\quad \mu>0
\]

とする。これは一体項と密度–密度二体項からなる対角なfermion模型である。一般のab initio Coulomb Hamiltonianだとは主張しない。

全電子がAにある配置をs=0、Bへs個移した配置をsとすると、

\[
E(s)-E(0)=U s(N-s)-\mu s.
\]

k<Nに対し0<μ<U(N−k)なら、1≤s≤kの全移動はenergyを上げる。一方、全電子をBへ移したs=Nは

\[
E(N)-E(0)=-\mu N<0.
\]

従って、**一度に高々k電子しか移さず、厳密に下降遷移だけを許すcoupler**では、s=0の状態はnongroundなのに捕捉され得る。

これは大域的制御不能性ではない。有限温度での上昇、coherentなvirtual過程、多電子移動、別couplerを禁止していない。また有限時間の非理想filterには弱い上昇成分が残り得るので、その場合のescape timeをこの式だけで無限大としない。

H_Dは古典的に容易な診断例であり、量子優位の実験候補ではない。役割は「ランダムな局所結合があれば必ず速くgroundへ行く」という短絡を排除することにある。UをNに応じて尺度化する選択もでき、これは単に無制限に大きいnormを置いた議論ではない。

### 7.2 N=2、4 modeで実装可能なpair移送

A={1,2}、B={3,4}、N=2とする。

\[
H_D=cI-U(n_1n_2+n_3n_4)-\mu(n_3+n_4),
\quad 0<\mu<U.
\]

|12〉から一電子だけ移すとenergyはU−μ増えるが、|34〉へ二電子を移すと2μ下がる。

\[
T=a_3^\dagger a_4^\dagger a_2a_1,
\qquad P=T^\dagger T=|12\rangle\langle12|
\]

をN=2 sector上で使う。実ancillaの|0〉から、

\[
V_\theta=\exp\{-i\theta(T\otimes|1\rangle\langle0|+
 T^\dagger\otimes|0\rangle\langle1|)\}
\]

を適用し、ancillaをtrace/resetする。得られるKraus作用は

\[
K_0=I+(\cos\theta-1)P,
\qquad K_1=-i\sin\theta\,T.
\]

\[
K_0^\dagger K_0+K_1^\dagger K_1=I,
\qquad [N,K_0]=[N,K_1]=0.
\]

よってこれは実行可能な粒子数保存CPTPチャネルC_θである。実装に必要なfermionic excitation制御・符号処理・合成費は無料ではない。

この対角模型では、

\[
\mathcal C_\theta^*(H_D)-H_D
=-2\mu\sin^2\theta\,P\preceq0.
\]

この式は一電子下降則の障壁を、実際の二電子移送が越えられることを示す。ただし、振幅減衰のStinespring実装と既知のfermionic excitationを用いた**既知の型の構成**である。これだけを独立新アルゴリズムとして保持しない。

### 7.3 非可換Hへ、そのまま移すことはできない

実質的な次の障害を見るため、

\[
H_\lambda=H_D+\lambda V
\]

とし、VをA,B間のone-body hoppingのHermitian和にする。PVP=0、〈34|V|34〉=0である。上の同じチャネルについて

\[
\mathcal C_\theta^*(H_\lambda)-H_\lambda
=-2\mu\sin^2\theta P
+\lambda(\cos\theta-1)\{P,V\}.
\]

χ=V|12〉≠0なら、{|12〉,χ/||χ||}上の圧縮は

\[
\begin{pmatrix}
-a&b\\b^*&0
\end{pmatrix},
\quad a=2\mu\sin^2\theta,
\quad |b|=|\lambda(\cos\theta-1)|\,\|\chi\|.
\]

b≠0のとき、この圧縮は

\[
\frac{-a+\sqrt{a^2+4|b|^2}}2>0
\]

という正の固有値を持つ。従って、**単に対角部分を冷却するpair resetを使うだけでは、元の非可換Hに対する全状態のenergy単調減少を保証できない**。

これも冷却一般の否定ではない。全状態で毎stepの厳密単調減少は十分条件であって必須条件ではない。複数stepのcycle、可制御な加熱誤差、異なるcoupler、finite-temperature経路等を許し得る。

この診断から、次の課題は「pairを移す」ことではなく、**非可換Vを含む元Hに対して、集団的遷移とcoherenceの変化を一緒に設計すること**になる。元のHをH_Dで置き換えて成功としない。

---

## 8. 本レビューの紙上考察III：絶対E0へ戻す十分条件

### 8.1 Exact ground fidelityは、energy出力の必要条件ではない

対象sectorのE0に対してH0=H−E0I≽0とする。準備されたσが

\[
\operatorname{Tr}(H_0\sigma)\le \alpha\epsilon/4
\]

を満たすとする。energyがE0+ε/2を越えるspectral weightはMarkovよりα/2以下。

さらに、POVMがHと可換な理想energy読出しについて、各固有energyに対する±ε/2の一様読出し精度が失敗確率α/2以下で保証されれば、union boundで最終出力は確率1−α以上でE0からε以内となる。理想的なHのpowersによるQPEはこの可換性を持つ。実装誤差がある場合には、理想instrumentからの全入力の作用誤差を別予算として加える。各固有vectorでの成功率だけを、非可換な一般POVMの全superposition保証へ移してはいけない。

ここにはground gapの下限も、σがほぼ純粋であるという条件も入っていない。ただし、energy excessを上の精度まで小さくすることは、それ自体が難しい状態準備課題である。未知E0を実行時に与えたわけではなく、E0は証明の記述にだけ使っている。

このMarkovの帰結自体を新規性にしない。低温Gibbs状態でもU_β−E0≤log(dim S)/βという既知のentropy評価があり、「精度εのenergyにはgapを分解する必要がない」という観点だけでは新算法にならない。Gibbs状態の生成費・mixingを含めて比較する。

### 8.2 構成に接続する一つの証明目標

ある実CPTPチャネルCについて、例えば

\[
\mathcal C^*(H_0)\preceq(1-\kappa)H_0+\nu I,
\quad 0<\kappa\le1
\]

を係数と明示したクラスから証明できれば、

\[
x_m:=\operatorname{Tr}(H_0\mathcal C^m(\rho_0))
\le(1-\kappa)^m x_0+
\nu\frac{1-(1-\kappa)^m}{\kappa}
\le(1-\kappa)^m x_0+\nu/\kappa.
\]

合法な粗い係数上界からx0≤Bを得て、ν/κ≤αε/8とし、κ<1ならmを

\[
m\ge \frac{\log(8B/(\alpha\epsilon))}{-\log(1-\kappa)}
\]

の非負ceil以上に取ることで、§8.1の条件へ接続できる。κ=1は別の退化場合として直接評価する。

この不等式は**例として挙げた十分条件**であり、すべての候補に課す必須契約ではない。block-cycle drift、低energy到達確率、invariant domain内の別評価でもよい。

重要な未解決点は、C、κ、ν、適用classを実際に構成することである。κを「mixingがよい」と仮定したり、νの取得に未知のgroundを使ったりして解決したことにしない。κが小さいことやν/κの残差が大きいことを隠すと、全費用の主張は成立しない。

### 8.3 Scalarと元H

H→H+cIの既知shiftで状態準備の相対energy flowは変わらないが、最終energy値にはcを戻す。近似DF等の模型で準備した状態を元Hに用いる場合、モデル差のoperator boundや実際の読出し対象を別に保持する。

対象sectorの選択が元の問題のgroundを含むことも必要である。seniority-zeroやspin sectorの便宜的制限を、元N電子問題の絶対E0へ無断で読み替えない。

---

## 9. 強い比較対象と全費用

比較には少なくとも、同じ合法な初期状態からの通常energy推定、既知のsystem-bath冷却、既知のfiltered-jump準備、必要なら既知の局所block-reset構成を含める。[L2,L4,L6]

CDFのη^-2依存を、すべての合法なenergy推定の不可避な下界として置かない。最大coherent時間や制御・状態保持を許す条件が違えば、high-confidence QPE反復との比較も必要である。素朴な低confidence QPEの最小値取得は偽の低energy tailを持ち、強い比較対象の代用にはならない。[L6]

### 9.1 基本的な既知QPE比較の紙上整理

初期ground-space重みがη以上で、各runのenergy読出しのPOVMがHと可換であり、全固有値について誤差ε/2・失敗確率βを満たすとする。実装による非可換なずれは、全入力のinstrument誤差として別に加算する。

\[
M=\left\lceil\eta^{-1}\log(2/\alpha)\right\rceil,
\qquad \beta=\alpha/(2M)
\]

なら、独立に準備したM runでgroundを一度もsampleしない確率はα/2以下、どれかの読出しが失敗する確率もα/2以下。最小の出力energyは、残る事象でE0±ε/2内に入る。

これは既知のconfidence amplificationとunion boundの整理であり、新しい推定法ではない。高confidence読出しを得る長時間・反復制御・補助register・PF/synthesis誤差は全て払う。異なる近似PFを別々に使った測定を、勝手に同一Hの理想射影測定と仮定しない。

### 9.2 費用座標

量子gate、depth、reset回数、最大coherent時間、古典前処理、記憶量は、換算規約なしに一つの数値へ足さない。

固定した量子gate座標gでは、例えば

\[
C^{(g)}_{\rm total}=C^{(g)}_{\rm setup}+
\sum_\ell N_\ell\left[
 C^{(g)}_{{\rm prep},\ell}
 +m_\ell C^{(g)}_{{\rm cool},\ell}
 +C^{(g)}_{{\rm read},\ell}\right]
\]

と会計する。古典certificate・coupler生成・前処理は別座標で併記し、償却条件があれば明示する。

既存準備のη、低energy tail、mixing、実装誤差、readout成功を一方だけ無料にしない。新しいcoolerでshotsが減っても、coolingの反復とreset費用を払えば総費用が増え得る。

本レビューはinstance未固定であり、どの費用が実測上支配的か、既存PF/PRより何倍よいかを計算・認定していない。

---

## 10. 次に依頼する具体的作業

### 10.1 推奨する一つの作業単位

**名称（提案）：非可換電子模型に対する、係数駆動の集団冷却遷移の構成検討。**

新しい永久研究IDや正式状態をここで作らない。担当は、ユーザーがこの方向と範囲を採ると判断した後のCodex／Claude Code。

最初の作業は、再び全分野のgap台帳を作ることではない。§7の障害を出発点とし、**元の非可換Hを保持した、具体的な有限CPTP操作列**を一つ作ることを中心にする。

### 10.2 必須の作業内容

1. **入力と作用を固定する。** 元H、粒子数sector、簡単に準備できるρ0、利用するgate・測定・resetを明示する。ancilla数・step数は勝手に極端に制限せず、費用として数える。
2. **既知構成との直接対応を、構成と並行して行う。** [L2–L5]、既知局所熱浴・spectral filtering・fermionic excitationとの対応を示す。文献の全再調査だけで終わらず、どの生成部分を新しく作るのかを記す。
3. **非可換項を捨てず、実チャネルを構成する。** §7.2の単純pair resetを再提示するだけでは不十分。複数step、coherent correction、複数coupler、有限の上昇を含むcycle等は、その具体的操作と費用を明示する。
4. **小例の結論を広げ過ぎない。** 4 mode対角模型は設計診断。小さいblockを全対角化してresetすれば作れるというだけでは、一般化する新規則とはしない。少なくとも境界相互作用を含む拡張で何が変わるかを記述する。
5. **進捗の対象を選ぶ。** 全状態の一step単調性を必須にせず、cycleあたりのenergy excess、低energy到達確率、正当化された入力classのいずれかで、元Hへの意味を持つ判別命題を置く。
6. **既存研究との差を表示する。** PF/DFの内部係数改善でも、A2の相対log保証でも、M1-Sの±信号減衰でもないことを具体的な入力・操作・出力で確認する。

### 10.3 その作業で求める成果物

中心は文書の件数ではなく、次の内容である。

- 実装に接続するCPTP更新則またはunitary＋reset列。
- 係数からcouplerを選ぶ処理と、その情報取得費。
- 保つ対称性、変える人口、測定・resetの意味。
- 非可換項に対する残差・加熱・dark state・mixingの診断。
- 最も近い既知構成との差。差がないなら、その対応。
- 一般化に必要な補題、または提案文法を否定する限定反例。

この作業で全分子への多項式費用や総E0優位まで完成させる必要はない。逆に小例でenergyが下がっただけで独立アルゴリズム成功としない。

### 10.4 判定と承認

| 結果 | 次の判断 |
|---|---|
| 既知法と異なる具体的更新則があり、有限例で元Hへの意味がある | 適用class・一般化・必要な計算を評価する |
| 既知cooling・既知local reset・既知高次Lindbladへの実質的対応だけ | 新原理としては保持せず、得た対応を保存 |
| 構成できないが限定障害を特定できた | その障害を避ける機構があるか判断。分野一般のno-goとしない |
| 構成も有意な障害も得られない | 未解決としてSTOP。自動で次の候補探しへ移らない |

次の作業実施、研究課題の正式採択、科学計算の実行は別である。今回のレビュー開始承認だけで、数値行列生成・solver・科学用記号計算・simulation・compileを行う許可はない。

将来、数値検証が判別に有用なら、科学対象・入力・比較・誤差・出力・STOPを定めた別承認を提案する。CPU/RAM/worker数の恣意的な上限を置かず、空き資源と非干渉に沿って効率化・並列化する。既存の固定実行契約は変更しない。

---

## 11. 論文化の着地点

現時点で論文の新規性や採択可能性を認定しない。目指せる成果型は、次のいずれかに具体化する必要がある。

**構成定理**：係数から生成できる遷移規則が、従来の局所couplerで捕捉される非可換電子クラスを、明示費用・誤差で扱う。

**アルゴリズム上の改善**：既知の基本部品を使っていても、遷移選択・集団化・証拠取得・再利用の規則が非自明で、同一taskとaccessで費用または保証の差が証明される。

**特徴付け**：どの構成classで何が障害になり、どの種類の追加操作が必要かを明確にする。ただし、本書の簡単な対角障壁例やMarkov評価だけを独立原著の成果と認定しない。

「同じcoolingを分子へ適用し、有限例でenergyが下がった」というだけなら、応用・評価の成果としての位置付けと、独立新算法という目標を分離する。

---

## 12. 最終判断と保全

本レビューは、新しいアルゴリズムが必ず存在する・必ず研究成果になるという結論ではない。現在の証拠から、PF内部やA2保証を再びなぞるより、**実際にstate populationを変える遷移生成を、構成研究として一度具体化する方が、このチャットの独立性を保ちやすい**と判断した。

その判断は、一般の散逸法が既存法より優れるという科学的事実ではなく、既存研究との分担と文献の到達点に基づく研究戦略の推薦である。

J1、Q1、R1-P、SOS-PF A2、第一・第二研究、FS-R1、Track A/B、M1-Sの状態は変更しない。特にA2の新規性判断を本レビューで代行せず、H8の費用再会計も開始しない。

**完了：承認された研究戦略レビューと本Markdown記録。**  
**未実施：新規科学計算、実装、repository変更、研究の正式採択、他系列の再開。**  
**次の意思決定：上記の状態準備・遷移生成の構成検討を、独立した次作業として採るか。**  
**Mandatory STOP：本レビューの提出で停止し、採択・次の構成作業・科学計算を自動開始しない。**

---

## 参考資料・固定URL

### リポジトリ資料

[G1] Evaluation, cross-repository handoff, commit `609a63231ee0786cf8da31f6b33358acfd6f2548`：  
https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/609a63231ee0786cf8da31f6b33358acfd6f2548/docs/research_exploration/cross_repository_overlap_survey_20261017/future_review_preparation_handoff.md

[G2] 同、20方向対応表：  
https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/609a63231ee0786cf8da31f6b33358acfd6f2548/docs/research_exploration/cross_repository_overlap_survey_20261017/algorithm_improvement_overlap_matrix.md

[G3] 同、研究一覧：  
https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/609a63231ee0786cf8da31f6b33358acfd6f2548/docs/research_exploration/cross_repository_overlap_survey_20261017/cross_repository_research_inventory.md

[G4] PR, 4系列重複防止マップ, commit `d09ba606a9fceef806a9313e3f7c43cd21d19e3f`：  
https://github.com/HIROMU1015/Partially-Randomized-Trotter/blob/d09ba606a9fceef806a9313e3f7c43cd21d19e3f/docs/research/qc_four_track_strategy_handoff_20261017/overlap_and_progress_map.md

[G5] Evaluation, 最新2ブランチ差分handoff, commit `c6419859029824a4ee8c3dfd3c8126fe585ffbe2`：  
https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/c6419859029824a4ee8c3dfd3c8126fe585ffbe2/docs/research_exploration/cross_repository_two_branch_delta_20261017/review_readiness_delta_handoff.md

[G6] Evaluation, 方法論分析, commit `a80596c29e0eaaf7483f8981ed0e61c918335054`：  
https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/a80596c29e0eaaf7483f8981ed0e61c918335054/docs/research_exploration/research_strategy_redesign_20261017/exploration_methodology_analysis.md

[G7] Evaluation, P1–P8仮説handoff, commit `67d9e3b938b8a03120b836a1c32283b7c9e9a1f0`：  
https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/67d9e3b938b8a03120b836a1c32283b7c9e9a1f0/docs/research_exploration/cross_domain_mechanism_ideation_20261016/research_hypothesis_handoff.md

[G8] PR, A2相対形式監査handoff, commit `051df4661eeffb6c6c4c978f70f43eeeaadfddd6`：  
https://github.com/HIROMU1015/Partially-Randomized-Trotter/blob/051df4661eeffb6c6c4c978f70f43eeeaadfddd6/docs/research/qc_relative_form_finite_step_audit_20261017/decision_handoff.md

### 外部一次文献と今回の読取り範囲

[L1] S. Marti, R. Mansuroglu, M. J. Hartmann, *Efficient Quantum Cooling Algorithm for Fermionic Systems*, Quantum 9, 1635 (2025). Abstract・方法の概要を確認。本文全証明の査読ではない。  
https://quantum-journal.org/papers/q-2025-02-18-1635/  
https://arxiv.org/abs/2403.14506

[L2] Z. Ding, Y. Zhan, J. Preskill, L. Lin, *End-to-End Efficient Quantum Thermal and Ground State Preparation Made Simple*, arXiv:2508.05703v2。Algorithm description、main guarantees、analysis overviewを読解。Theorems 1–3とmixing依存を確認。出版版の全差分は未監査。  
https://arxiv.org/html/2508.05703v2  
出版情報：*Simple and efficient end-to-end quantum thermal and ground state preparation*, Nature Physics (2026), https://www.nature.com/articles/s41567-026-03389-y

[L3] H. Schlömer, L. Chen, S. F. Yelin, H.-Y. Hu, *Model-agnostic cooling algorithms for strongly interacting fermions*, arXiv:2605.01029v1。本文のcoupling construction、数値主張の限定、Discussionを確認。図の数値を再抽出・再解析していない。  
https://arxiv.org/html/2605.01029v1

[L4] Y. Zhan et al., *Rapid quantum ground state preparation via dissipative dynamics*, arXiv:2503.15827v3。Introduction、jump式(1)–(4)、結果の分類を中心に確認。弱相互作用の全証明を独立再認証した意味ではない。  
https://arxiv.org/html/2503.15827v3  
出版情報：Physical Review X 16, 011004 (2026), https://doi.org/10.1103/wzb3-dbg9

[L5] Z. Ding, X. Li, L. Lin, *Simulating Open Quantum Systems Using Hamiltonian Simulations*, PRX Quantum 5, 020332 (2024)。出版社本文の構成概要、Kraus→Stinespring、任意高次・非postselectionの到達点を確認。全高次係数を再導出していない。  
https://doi.org/10.1103/PRXQuantum.5.020332

[L6] L. Lin, Y. Tong, *Heisenberg-Limited Ground-State Energy Estimation for Early Fault-Tolerant Quantum Computers*, PRX Quantum 3, 010318 (2022)。CDFとconfidence／QPE比較に関する原著情報を参照。個別アルゴリズムの総費用の最新最適性を認定しない。  
https://doi.org/10.1103/PRXQuantum.3.010318

[L7] J. Lin, A. F. Izmaylov, *Bounding eigenstate overlap from Hamiltonian moments: Success-probability guarantees for quantum phase estimation*, Physical Review A 114, 042432 (2026)。出版社の原著abstractでmomentと粗いspectral情報を使うLP/SDP保証を確認。全定理の査読はしていない。  
https://doi.org/10.1103/3n75-vkxf

[L8] Li, Yang, Lin, *Dissipative phase decision without ground-state preparation*, arXiv:2606.28750v1。Introductionと出力taskの位置付けを確認。phase decisionを絶対E0保証へ転用しない。  
https://arxiv.org/html/2606.28750v1

**文献上の限界**：上記は本レビューでの限定した一次資料調査であり、全cooling・quantum Metropolis・reservoir engineering・Hamiltonian simulationの網羅的priority調査ではない。未知の構成が存在しないとも、新提案が世界で初めてとも認定しない。
