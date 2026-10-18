# 集団遷移生成の保留後：新アルゴリズム研究戦略の独立再レビュー

- 作成日：2026-10-18 JST
- レビュー区分：Level 1（研究方向・新規性・主要な構成課題の科学的判断）
- 開始承認：本チャットのユーザー指示「レビューを開始して」。本記録はその範囲のレビューである。
- 著者：GPT
- 状態：**レビュー完了。研究方向の条件付き推薦であり、正式採択・既存研究の再開・科学計算の承認ではない。**
- 今回実施：固定GitHub資料の読解、関連一次文献の調査、紙上での数理的考察、研究方針の比較、本Markdown作成。
- 今回未実施：新規科学数値計算、保存値再解析、科学用記号プログラム、solver、simulation、回路build/compile、benchmark、GitHubへの書込み、grant発行、研究状態変更。
- 運用正本：ローカルで取得した `research_project_instructions_unified_2026-10-17.md`。既存個別契約・SOURCE・結果・STOPを維持。

## 0. 結論

**現集団遷移生成系列のPAUSEDは維持する。冷却一般の不可能性は認定しない。次の探索を「別の既知分野へ移り、簡単な構成を作ってから既知性を調べる」形では繰り返さない。**

次に条件付きで推奨するのは、元の電子Hamiltonianを変更せず、量子状態内のcoherenceを保った小さな変分部分空間を、合法な係数・状態準備・測定から生成・更新する研究である。

ただし、QSCI、SQD、SKQD、QSE、QFD、量子Davidson、非unitary後処理は既知である。**「量子部分空間法を使うこと」は新候補ではない。** 今回提示する射影に基づく基本構成もQSEの特殊化として書ける。その点を最初から対照にする。

研究対象として残す問いは次の一件である。

> **電子係数と費用を計上した量子測定から、配置を一つずつ列挙せずcoherenceを保持する部分空間の生成・更新規則を作り、近似精度、行列要素の測定、古典対角化、状態準備の費用を同時に制御できるか。**

対象Hamiltonian familyと有効な生成規則は未確定である。従って、これは「独立新アルゴリズムの発見」ではなく、**次に構成を研究する課題の条件付き推薦**である。完成した独立新アルゴリズムは0件、正式採択も0件。

既知理論に含まれる枠組みを再証明することを次の成功条件にせず、**どの生成・測定・更新手順に、比較可能な計算上の差が生じるか**を成功条件にする。

---

## 1. 対象、証拠、読み取り範囲

### 1.1 対象リポジトリ

- Evaluation：`HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae`
- PR：`HIROMU1015/Partially-Randomized-Trotter`

ユーザーのローカルパスは作業場所の指定であり、本レビューがそのサーバーへ直接接続して全worktreeを監査したという意味ではない。GitHub connectorから固定本文を読んだ。過去のCodexによるhash・worktree保全の報告と、今回の科学レビューを区別する。

### 1.2 今回の主要固定SOURCE

| ID | Repository / commit | path / 読取り範囲 | 本レビューでの役割 |
|---|---|---|---|
| E1 | Evaluation `b58d5750b2d9d1917d3f34d25dd49bdcaf6b5c66` | `docs/research_exploration/collective_transition_pause_decision_20261018/research_decision_record.md`。判断対象、2段階の成果・障害、保留・再開条件、他系列保全の本文 | 現系列の正式PAUSEDを確認。科学的な一般NO-GOではない |
| E2 | Evaluation `12324144a3d4f7a247f1944b4866549e9cc19152` | `docs/research_exploration/collective_transition_multijump_cycle_20261018/cycle_paper_derivations.md`。今回再取得は行117–181、§4–6 | reset文法の必要十分条件M8–M9、flag-breaking項、限定入力・誤差の範囲 |
| E3 | Evaluation `609a63231ee0786cf8da31f6b33358acfd6f2548` | `docs/research_exploration/cross_repository_overlap_survey_20261017/algorithm_improvement_overlap_matrix.md`。既存20方向の対応本文 | PF/PR、保証、測定、encoding、downfoldingとの重複境界 |
| E4 | Evaluation `c6419859029824a4ee8c3dfd3c8126fe585ffbe2` | `docs/research_exploration/cross_repository_two_branch_delta_20261017/review_readiness_delta_handoff.md` 全文 | A2/R1-Pの相違、旧原本の公開、進捗・承認の区別 |
| P1 | PR `7af83266f96b714bb3fa2f1ef5e4bc89faf37db3` | `docs/research/qc_a2_certificate_connection_design_20261018/decision_handoff.md` 全文 | A2認証情報接続設計は既存の別作業。設計済みと採択・実装・実測を分離 |
| P2 | PR refs観測 | `git/matching-refs/heads/qc-a2` | 今回観測では接続設計7af83266とpreflight c62fe99dの2branch。全PR branchの網羅監査ではない |
| R0 | 前回GPTレビューのローカル原本 | `/mnt/data/research_reviews/new_algorithm_strategy_review_cross_repository_20261017.md`、40,880 bytes。結論、先行研究、紙上考察、次作業の該当部分 | 前回推奨と今回の変更理由を明示。原本は変更しない |

初期構成 `b7ec04fb84cd01eb846b9e3cc6d545bdf833e657` の結果はE1と過去に提供された構成本文にも依拠する。今回、その全10ファイルや全SOURCE registryを新たに独立再監査したとは主張しない。

関連するPRのH8は後続の再会計が既に公開されたとの固定記録が会話にある。E4に残る当時の「PR削減率未更新」を現在の状態へ移していない。本レビューではH8の優位率や費用を再算出せず、最新winnerを決めない。

### 1.3 証拠の階層

1. **資料が報告していること**：E1/E2の限定reset構成、既知法対応、正式状態。主張範囲を保存する。
2. **外部一次文献で今回確認したこと**：後掲L1–L12。abstract確認と本文・定理確認を区別する。
3. **今回の紙上推論**：§3、§7–9。既知の線形代数・量子測定を用いた構成診断で、優先権や新定理の認定ではない。
4. **研究方針の推薦**：§10–12。ユーザーの正式採択を代行しない。

---

## 2. 直近の結果をどう受け止めるか

### 2.1 保留の判断は維持できる

初期構成は、係数で解ける条件付き小ブロック変換とrank-one振幅減衰。複数jump構成は、既知source部分空間の弱測定と条件付きreplacementに帰着した。どちらも実行可能な操作を示す価値はあるが、そのまま一般電子Hの新しい効率的な準備法にはならない。[E1]

今回は「同じgateを使ったから既知」という理由だけではない。具体化した入力からの手順・チャネル作用・coherence・出力まで既知形式と対応し、さらに有利なsource/targetを一般に得る新しいアルゴリズムが残らなかった、という限定判断である。

### 2.2 ただし二回の不保持は、分野選択の失敗確率を測定していない

二つの構成は独立な無作為試行ではない。両者は、既知のoccupationまたは小ブロック状態を、既知targetへresetする近接した文法に属する。従って「2/2で失敗したので冷却の研究余地は乏しい」という統計的判断はできない。

停止理由は試行回数ではなく、**現文法で試すべき具体的な新差分がなくなったこと**である。未知の別coupler、feedback、coherent bath、許容加熱などを一般的に排除しない。ただし、その可能性だけを理由に停止済み系列を自動再開もしない。

### 2.3 前回推薦について修正する点

前回の「状態変換へ移れば既存PF/PRとは違う課題になる」という分類は妥当である。一方、そこから独立した新算法へ進む見込みは、十分に具体化されていなかった。

特に、局所energy下降を作る問題を選んだが、その成功例ではtargetを直接準備できたり、dark成分が残ったりした。**簡単な非可換模型でチャネルを作れることと、元の未知E0の取得費用が変わることの距離**が大きかった。

今後は、最小例を「難しい問題を簡単にしすぎた成功例」にせず、一般化で必要となる構造が残る例にする。小さいこと自体は問題ではない。重要なのは、何の機構を判別する例かである。

---

## 3. 紙上考察A：全状態の厳密energy下降は強い要請である

以下は今回の初等的導出。数値検証・形式証明器は用いず、独立priorityを主張しない。

有限次元の指定sectorでHamiltonianをH、最小固有値をE0、ground射影をP0とする。CPTP写像Cが

\[
\operatorname{Tr}[H\mathcal C(\rho)]\le\operatorname{Tr}(H\rho)
\quad\text{for every density operator }\rho
\tag{A1}
\]

を満たすと仮定する。ground支持状態ρ0では、H−E0I≽0から

\[
0\le \operatorname{Tr}[(H-E_0I)\mathcal C(\rho_0)]\le0.
\]

従ってC(ρ0)もground空間に支持される。Kraus演算子Kαで書けば、任意のground vector gについて

\[
0=\sum_\alpha\|\sqrt{H-E_0I}\,K_\alpha|g\rangle\|^2,
\]

すなわち

\[
(I-P_0)K_\alpha P_0=0 \quad\text{for all }\alpha.
\tag{A2}
\]

非縮退ならKα|g〉=cα|g〉。これは**全状態単調性ならgroundを正確に保つ必要がある**という必要条件であり、効率的な構成が不可能という定理ではない。局所係数からこの性質を間接的に保証する既知方法もあり得るし、近似・有限cycle・限定inputはA1を要求しなくてもよい。

E2の固定部分空間resetはさらに限定される。Q=I−P、b∈Q、Eb=〈b|H|b〉、0≤z<1として

\[
\Phi^*(H)-H=-(1-z^2)(PHP-E_bP)+(z-1)(PHQ+QHP).
\tag{A3}
\]

Q対角blockは0である。PHQ≠0なら、対応する二次元圧縮に非零off-diagonalと零Q対角がありdeterminantが負になる。従ってこの文法で全状態下降を要求するとPHQ=0が必要になる。[E2]

**教訓**：sourceを大きくしても、不変性を無条件に作れるわけではない。逆に、これを「任意の非unitary法には未知固有basisが必要」という一般主張へ拡張してはいけない。

---

## 4. 探索戦略の再評価

### 4.1 維持するもの

D1・D2、元Hとの対応、scalar/sector/モデル差、合法な情報と取得費用、同条件の強い対照、否定範囲の限定、SOURCE・STOP保全を維持する。

「強いbaselineから具体的な不足を見つけ、小さな命題へ分ける」B′＋A′の考え方も有用である。ただし、普遍的な最強法の証明や、論文がopen questionと明記したことを、全ての探索の必須入場条件にしない。

### 4.2 変更するもの

- **分野名単位から、生成・取得・更新手順単位へ**：cooling、QSCI、QSE、counterdiabaticなどの語だけで新方向と数えない。
- **作用の存在から費用を伴う生成規則へ**：目標の小行列やprojectorが書けることと、それを係数から安く作れることを分離する。
- **個々のtoy成功からfamilyを判別する命題へ**：全固有basisや全状態単調性を初期要件にせず、同時にtoyの直接準備可能性やclassical解法を無視しない。
- **新規性の純粋性からアルゴリズム上の差へ**：既知部品を使うことを排除せず、同じ入出力・同じ手順・同じ保証に尽きるものを新規とはしない。
- **少し進むたびの戦略レビューから、まとまった構成作業へ**：既知性が予め分かっている基本式の再発見を完了成果にしない。構成・対照・必要条件を一つの作業パケットで扱う。

### 4.3 「既知法に含まれる」の判定を二段に分ける

1. 大きなframeworkに含まれること。QSE、Rayleigh–Ritz、Lindblad、変分法など。これは単独で不保持の十分条件ではない。
2. 主張した新しい部分が、生成手順・必要情報・評価量・費用まで含めて既存具体法の直接特殊化であること。別の計算上の差がなければ不保持の根拠になる。

今回のresetは2に近い。次に検討する射影部分空間の基本形は1として**初めから既知**である。研究対象は、それを選び更新する規則と総費用の差に限定する。

---

## 5. 他研究との分担

| 既存系列 | 今回再提案しない内容 | 今回の条件付き方向との関係 |
|---|---|---|
| Evaluation第一・第二研究、FS-R1 | PF固有枝校正、経験的width、fit、安全性/資源regretの再開 | 元Hの低energy近似部分空間を生成する課題とは異なる。経験的安全性を新部分空間の精度証明へ流用しない |
| PR Track A/B、Parent allocation、M1-S | native価格再会計、sampling law再配分、±branch共有、既存有限law | 構成するのはRTEのlawではなく、電子状態の変分表現。共通の測定・費用語だけで同一研究にしない |
| SOS-PF A2 | relative log/EW2の新規性審査、certificate adapter・checker・step比較の取り直し | A2は接続設計まで別系列で進行。今回の部分空間近似誤差はPF有限step保証と同じではない |
| R1-P | 外挿PF restricted-norm保証の再調査 | 不保持維持。今回Richardson係数やPF次数を新しい研究軸にしない |
| N3、旧C3、downfolding | 既存縮約・証拠・有効H構成の再開 | P_S H P_Sを元Hの変分制限として用い、元Hを別の有効模型に置き換えない。ただし近接研究であり、完全無重複を断定しない |
| Q1 | 全固有基底の挿入再帰 | 全固有basisや全入力対角化を求めない |
| 現集団遷移生成 | reset数・angle・source flagだけを変えた延長 | PAUSED維持。状態人口の移送を新課題にしない |

この表は今回の固定記録からの分担評価である。[E1–E4,P1] 未保存チャットまで含む絶対的な無重複保証ではない。新たな同時作業が具体的に見つかった場合は、その課題単位で分担を更新する。

---

## 6. 外部先行研究を踏まえた代替方向の評価

### 6.1 単純なQSCI/SKQDへの移行は新算法ではない

QSCIは量子状態の測定から配置を選び、元の係数で作る部分空間Hamiltonianを古典対角化する既知手法である。[L1] 時間発展を状態生成に使うことも既知であり、SKQDのAlgorithm 1・Theorem 1は、疎性、初期overlap、スペクトル条件に依存した保証を与える。[L2]

SKQDではsimulation誤差と最終energy誤差を単純に同一視せず、sampling成功への影響を扱う。従って「正確なevolutionを作る代わりにconfigurationだけ得る」という一般観点を新発見にしない。

QSCI-CMPには、化学的に自明な配置を先に古典側へ入れ、励起階数やseniorityの安価な判定を使う構成が既にある。[L3] 見えていない配置を増幅する、化学的知識でpreselectionする、というだけでも新規差分はない。

### 6.2 残差で基底を増やすことも既知

QDavidsonに加え、2026年にはQJDとsample-based版が提案されている。[L4] 今回そのabstractで方法の存在を確認したが、全証明・実装・最大性能まで検証したわけではない。詳細の新規差分を主張するなら本文の対応が必要である。

少なくとも「Ritz残差を使ってsubspaceを拡張する」という題名だけを新構成候補にはしない。

### 6.3 非直交基底の問題には既知の改善がある

QFDは量子生成basis上でHとoverlapを測り、一般化固有値問題を解く既知経路であり、DFとの結合も存在する。[L5] Partitioned QSEは部分空間を逐次接続する構成、measurement-efficient Krylovは統計誤差・測定費用を扱う。[L6,L7]

「行列がill-conditionedだからorthogonalizeする」「Krylovを分割する」だけで新規とはしない。量子側の測定費を増やさずに何が改善するのかが必要である。

### 6.4 Counterdiabatic/adiabatic方向

Counterdiabatic ADAPT-VQEの分子向け提案が2026年に公開されている。[L8] 係数から近似gauge potentialを組み立てる方向は、既に具体的な競合がある。また本プロジェクトのframe/交換子/補正の研究と近接する。

この方向に研究余地がないとは言わないが、本レビューでは同条件での独立した生成差を得られなかったため第一候補にしない。

### 6.5 Fragment化や振幅再重み付け

相関したfragment状態をtensor-product basisにしてselected CIを行うTPSCIは既知である。[L9] 状態をdiagonalな非unitary因子で再重み付けするnu-VQEや、古典neural後処理を用いるVQNHEも既知である。[L10,L11]

「配置をまとめる」「fragment内の相関を保持する」「coherenceを保って振幅を重み付けする」という語だけで新規性を認定できない。

### 6.6 比較の結論

| 方向 | 今回の評価 |
|---|---|
| 冷却/resetの小変更 | 現系列保留維持。別機構なしでは再開しない |
| PF/PR・A2の再改良 | 他チャットの進行領域として今回の主線にしない |
| 既知QSCI/SKQDの実装 | 有力なbaselineだが、新構成の成果ではない |
| 残差型QDavidson/QJDの再提示 | 既知。これだけを候補にしない |
| Counterdiabatic ADAPT | 関連既知法・内部近接性が大きく、今回は具体差未提示 |
| **coherence保持部分空間の生成・更新と測定費の同時設計** | **枠組みは既知。未確定な生成則と費用差を研究する課題としてのみ条件付き推奨** |

---

## 7. 紙上考察B：次の問題を操作の水準で定義する

### 7.1 既知の変分出発点

指定した正しい粒子数等のsector内で、部分空間Vを用いて

\[
E_V=\min_{|\phi\rangle\in V,\ \|\phi\|=1}\langle\phi|H|\phi\rangle
\tag{B1}
\]

を求める。理想行列・厳密演算ならE_V≥E0。V⊂V′ならE_V′≤E_V。

ここにPHQ=0は不要である。近似部分空間がHで不変でなくても変分原理は使える。ただし、E_V−E0が小さいことはB1からは従わない。

これはRayleigh–Ritzと既知QSEの出発点であり、新原理ではない。[L1,L5,L12]

### 7.2 診断用の具体的構成：coherenceを保つ配置の集約

**以下を新アルゴリズムと認定しない。既知frameworkとの対応と、残る構成課題を可視化するbaselineとして書く。**

実際に生成可能な純粋seed `|ψ〉=A|0〉` を用意する。AはSOURCE・精度・費用を持つ。exact groundとは仮定しない。再利用可能なcopies、inverse、controlled-Aは別accessであり、必要になったものだけを計上する。

occupation bitstring xをK個のlabelへ写す古典的に計算可能な関数f(x)を使い、

\[
\Pi_a=\sum_{x:f(x)=a}|x\rangle\langle x|,
\quad |\chi_a\rangle=\Pi_a|\psi\rangle,
\quad p_a=\langle\psi|\Pi_a|\psi\rangle
\tag{B2}
\]

とする。labelを計算する可逆回路は

\[
|x\rangle|0\rangle\longmapsto|x\rangle|f(x)\rangle
\]

で定義できる。未知のenergy射影をoracle化していない。fが複雑なら、その生成・可逆評価費を払う。

p_a>0のχaは互いに直交しており、

\[
S_{ab}=\langle\chi_a|\chi_b\rangle=\delta_{ab}p_a,
\quad H^{(f)}_{ab}=\langle\psi|\Pi_a H\Pi_b|\psi\rangle.
\tag{B3}
\]

K次元の一般化固有値問題H^(f)c=EScを解く。

QSCIと違い、一つのbasis vectorの中に多数の配置の振幅と相対位相を残せる。ただし、その振幅はseedが与えたものに拘束される。K=1なら元seedだけで、何も改善しない。fを全bitstringのidentityにすれば、seedが非零である各配置のspanになり、最悪指数次元へ戻る。

### 7.3 行列要素をどう取得するか

Hを既知Pauli和 `cI+Σ_l h_l P_l` に符号化でき、fのmembershipを有限回路で評価できる場合を考える。R_a=I−2Π_aをmembership反射とすれば

\[
\Pi_aP_l\Pi_b=
\tfrac14(P_l-R_aP_l-P_lR_b+R_aP_lR_b).
\tag{B4}
\]

右辺は既知unitary積の有限線形結合である。各期待値の実部・虚部はHadamard型の測定で取得できる。R_aはfの可逆評価・label比較・位相反転・uncomputeから作る。これはHのblock-encodingを新たな中核にする構成ではない。

ただしB4は測定が安いという結論ではない。最悪でK²個のmatrix entry、Hamiltonian term数、f計算費、精度に応じたshots、seed再準備、controlを払う。p_aはlabel測定から推定できるが、同じ測定でoff-diagonal Hも得られたことにはならない。

scalarは

\[
H^{(f)}=cS+H_{\rm electronic}^{(f)}
\]

として保持する。元Hの二体項・境界項を削除して行列を安くすることを、元問題の解法として扱わない。

### 7.4 構造的な利点と、直ちには得られない利点

非直交basisのGram off-diagonal測定を必要としない設計は可能である。しかしSの最小非零要素p_minが小さいと、正規化されたHの推定精度が厳しくなる。**直交性は無料の統計安定性ではない。**

また、stateをmeasurement後にdiscardしてclassical labelだけ残すと、χa間のcoherence情報は失われる。B3を単なるlabel人口の統計で置き換えてはならない。

---

## 8. 基本形の既知性を、このレビューの段階で切り分ける

### 8.1 QSEへの包含

QSEで展開演算子をE_a=Π_aと選べばB2–B3になる。従ってこの基本形だけを新しい固有値算法と呼ばない。[L12]

### 8.2 Diagonal後処理への対応

任意の係数cに対し

\[
\sum_a c_a|\chi_a\rangle
=\left(\sum_a c_a\Pi_a\right)|\psi\rangle.
\tag{C1}
\]

これはseedへのdiagonalな再重み付けである。nu-VQE/VQNHE等と比較する必要がある。[L10,L11] それらの全ての式・費用定理との完全包含を今回認定したわけではないが、「diagonal再重み付け」を新規核心にしてはならない。

### 8.3 Linear parity labelも、そのままでは新原理ではない

f(x)=Fx mod2、Fはk×nのbinary行列、K=2^kとすれば

\[
\Pi_a=2^{-k}\sum_{s\in\{0,1\}^k}
(-1)^{s\cdot a}Z^{F^Ts}.
\tag{C2}
\]

Walsh変換は可逆だから

\[
\operatorname{span}\{\Pi_a|\psi\rangle\}_a
=\operatorname{span}\{Z^{F^Ts}|\psi\rangle\}_s.
\tag{C3}
\]

これは可換なPauli群で作るQSEのbasis変更である。exactなspan対応がある。label名やhashという呼称を変えて新規性にしない。もし性能差を主張するなら、Fの生成規則、測定再利用、誤差会計まで差を示す必要がある。

### 8.4 Refinementによるenergy下降も既知の変分論理

f′がfを細分化すればΠ_aは子射影の和なのでV_f⊂V_f′。従って理想E_f′≤E_f。

一つのcellを0/1へsplitし、p0,p1>0、正規化した子u0,u1を使うと、

\[
|d\rangle=\frac{\sqrt{p_1}|u_0\rangle-\sqrt{p_0}|u_1\rangle}{\sqrt{p_0+p_1}}
\]

は旧部分空間に直交する。旧最低Ritz状態φ、E=〈φ|H|φ〉、E_d=〈d|H|d〉、w=〈d|H|φ〉を用いると、新空間はspan{φ,d}を含むので

\[
E-E_{f'}\ge
\frac{\sqrt{(E_d-E)^2+4|w|^2}-(E_d-E)}2.
\tag{C4}
\]

これは計測可能な新matrix entryからsplitの意味を評価する入口になる。しかし小さいRayleigh–Ritz問題や残差による拡張自体は既知である。**C4を導けたことを、新アルゴリズム発見という完了条件にしない。**

実データではw/E_dのconfidence、候補選択に使ったデータの再利用、複数比較を会計する。理想C4を有限shotのguaranteed gainと取り違えない。

---

## 9. 新規性以前に解くべき、具体的な三つの問題

### 9.1 表現能力：粗いlabelはどの相関を失うか

ground vector gを**解析の記号**として使う。ψ_x=〈x|ψ〉、g_x=〈x|g〉なら

\[
\|P_{V_f}|g\rangle\|^2
=\sum_{a:p_a>0}\frac{\left|\sum_{x:f(x)=a}\psi_x^*g_x\right|^2}{p_a}.
\tag{D1}
\]

ψ_x≠0の領域でr_x=g_x/ψ_xと書くと、cell内でのrの加重分散がprojection誤差となる。ψ_x=0なのにg_x≠0の部分は、どれだけlabelを細分化しても同じseedからは作れない。

従って、人口が大きいcellを選べば十分ではない。cell内の位相・振幅比の変化が重要である。一方、rやgを入力としてfを作れば、解くべき問題をoracleへ移しただけになる。

**必要な研究**：Hの係数・構造と合法な測定から、rの近似可能性に結び付くfまたは複数seedの更新則を得ること。D1はその保証の代わりではない。

### 9.2 統計精度：小さいpが費用を支配し得る

B≥||H−cI||という合法な上界を使い、S=diag(p_a)、p_min>0とする。電子部分のmatrixをJ^(f)=H^(f)−cSと定義し、J^(f)とSをそれぞれ推定する。Hermitianな推定matrixの誤差が

\[
\|\widehat J-J^{(f)}\|\le e_H,
\qquad \|\widehat S-S\|\le e_S<p_{\min}
\]

なら、scalarを分けたRayleigh quotientの差を評価して

\[
|\widehat E_f-E_f|
\le \frac{e_H+B e_S}{p_{\min}-e_S}
\tag{D2}
\]

を得る。ここでE_f=c+λ_min(J^(f),S)、推定値も同じcを一回だけ加える。導出は、u†Su≥p_min||u||²、|u†J^(f)u|≤B u†Suを使い、同じuでの二つのquotientを比較してminを取ればよい。

これは保守的な十分評価で、最適sample complexityの下界ではない。重要なのは、Gramが対角でもp_minを消せないこと。K、Hamiltonianのterm/測定分散、許容e_H/e_S、seedとmembershipの費用を含める必要がある。

理想変分性と、ノイズを含む推定値の変分性も別である。有限shotで得た最低固有値が自動的にE0以上になるとは限らない。必要ならD2のような確率付き誤差幅を付けて上側の値を報告する。

### 9.3 元のE0との隔たり

厳密な低いE_fを得ても、E_f−E0の上界がなければ所定の絶対精度を達成したとは言えない。補空間を捨てた変分計算は、部分空間誤差を消さない。

r=(I−P_V)H|φ〉のnormが小さい場合でも、φが励起固有stateならr=0になり得る。従ってresidualだけをgap-freeなground証明へ変換しない。

将来は、対象familyにおける近似保証、正当なlower bound、または別の合法な停止保証が必要である。既存A2を勝手に追加開発して穴埋めせず、既存結果を使う場合はaccessと適用条件を同じにして明記する。

### 9.4 Classical easy caseを強い対照から外さない

ψがD個の配置とその係数として古典的に明示され、Hが一体・二体項なら、Hψに繋がる配置は一つ当たり高々多項式（粗くO(n^4)）で生成できる。残差のsupportや係数もO(D n^4)規模の候補処理で作れる場合がある。

この入力条件では、短時間evolutionで残差配置をsamplingするだけの量子的な役割は自明でない。逆にψの全振幅が古典的に明示されない実行可能回路の場合は、この古典処理を同じ費用で行えるとは限らない。両方を比較し、回路があるというだけで量子優位も仮定しない。

独立なfragmentのtensor-product状態が指数個の配置を持つ例は、配置列挙の弱点を示せるが、tensor構造を使う古典法で容易なことがある。TPSCI等を除外してその例を量子利得の証拠にしない。[L9]

---

## 10. 条件付きで推薦する研究課題

便宜的記述名：**coherence保持・適応的変分部分空間生成**。正式研究IDや採択済み名称はまだ作らない。

### 10.1 何を新しくしたいのか

既知QSEの理想的な線形代数ではなく、次の組を作る。

\[
(H\text{の係数},\ A,\ \text{明示した測定記録})
\longmapsto
(\text{basis生成規則},\ \text{測定計画},\ \text{更新規則},\ \text{検証可能な適用範囲}).
\]

典型的な候補は、係数の結合構造から計算可能なpredicateを選び、C4等で得る局所的情報を使ってcoherent cellを細分化する方式。ただし、この単純なgreedy選択も既知adaptive QSEやdiagonal後処理と比べる必要がある。存在しない新規性を与えない。

### 10.2 何が揃えば研究上の差分になるか

少なくとも一つの非自明な電子Hamiltonian familyと初期accessで、以下を同時に説明する。

- basisの選択・更新が未知のg/E0/gap/全振幅表を要求しない。
- basis数だけでなく、状態準備・membership・行列要素・古典solveの費用が計上される。
- 近似精度または同じ精度を得る費用について、宣言した強い既知対照との差がある。
- 元Hの非可換項・scalar・sectorを変えず、単に古典的に既知のtargetへresetした成功ではない。
- QSEに属することを隠さず、**QSE内のどの生成/取得アルゴリズムが変わったか**を具体化する。

一般の全電子Hでの多項式保証を初回から要求しない。一方、classを「望ましいbasisが既に分かる系」とだけ定義して核心を仮定しない。

### 10.3 この方向を選ぶ理由と不確かさ

理由は、現resetのPHQ=0という構成要件を引き継がず、元Hのenergyを直接変分的に扱え、既存のPF/PR・A2の主要作業と異なる生成対象を持つことである。

**測定が安くなる、一般分子で速くなる、古典法に勝つ、新規性があると判明したから選ぶのではない。** それらはまさに未確定である。現時点でこの方向の成功確率や他方向に対する数値優先順位を作る根拠はない。

また、ユーザーが求めるのが既知frameworkを使わない全く別の物理原理だけなら、本推薦はその強い条件を満たすものではない。本レビューが支持するのは、**独立した計算手順を狙うが、既知の枠組みを使うことは許す**という研究方針である。成果対象の変更はユーザーが判断する。

---

## 11. 次のCodex作業の設計案（未実施・別途指示後）

### 11.1 一つの作業パケットにまとめる

**名称案：coherence保持部分空間の生成則・測定費用・既知法差分の限定紙上設計。**

最初に「QSCIを実装」「QSEのCPTP性を確認」「小分子を一つ対角化」へ進まない。既知の基本形は本記録に明示してある。

| 作業 | 終了時に必要なもの |
|---|---|
| 具体的な対象familyとaccessの設計 | 何を入力とし、何を量子測定で得るか。既存の他チャットとの課題単位の差 |
| 生成・更新規則の構成 | 係数・測定から有限のpredicate/basis操作を出す規則。B2やC4の再提示だけで終わらない |
| 代表的な強対照との対応 | QSCI/SKQD、一般QSE、PQSE、QJD、nu-VQE/VQNHE、適切なclassical SCI/TPSCI等から、同じaccessのものを選ぶ。全ての方法との普遍勝利を要求しない |
| 表現・測定・取得費の同時分析 | K、pまたは別の正確なconditioning量、測定誤差、前処理/solve、取得方法。隠れ指数費を0にしない |
| 最小の判別 | 実際の新規則が既知のoperator選択と同じか、それとも測定再利用・選択・保証に実質差があるか |

紙上でfamily・規則を構成する範囲を明示承認した後、Codexに任せる。新しい科学数値計算はこのレビュー承認からは開始しない。必要な場合は、得たい情報がどの判断を変えるかを示す科学契約案を後から作る。

### 11.2 継続・停止の判断

- 既知frameworkに含まれるだけで直ちに終了しない。
- 生成規則・取得法・保証・費用まで宣言したbaselineと同じなら、別名の新算法として保持しない。
- 有用な規則が得られなければ、何が不足したかを記録する。新しい大分野のreviewへ自動移行しない。
- 小例だけでなく、Kや測定・古典費が系サイズと共にどう変わるかを判別する証拠を重視する。
- 未証明・高リスクだけを棄却理由にしない。既知法との差を求める作業そのものは明示的に許可する。
- 作業単位・科学call・STOPは固定するが、CPU/RAM/workerへ人工的な低い上限を課さない。共有環境や他ユーザーへの変更・干渉は絶対に禁止。既存承認契約は維持する。

### 11.3 論文化の着地点

可能な着地点は、明示した電子classと同じaccessのもとで、生成規則と測定計画により精度–費用tradeoffを変える構成アルゴリズムである。限定classであっても、なぜ成立するかと既知対照との差が示せれば独立成果の可能性がある。

単にQSEをこのfamilyへ適用した、ノイズなしのenergyが下がった、Gramが対角になった、小例でFCIに近づいた、というだけでは独立手法の論文主張には不足する。

negative resultを得た場合も、否定した生成classと情報モデルが明確でなければ一般的な論文化価値を自動認定しない。研究ノートとしての価値と独立原著の中心主張を分ける。

---

## 12. 最終判断・承認境界

| 判断 | 結論 |
|---|---|
| 現集団遷移生成のPAUSED | 維持。一般冷却のNO-GOではない |
| 直ちに別の新物理原理を採択 | 推奨しない。今回新原理を構成済みとはしていない |
| PF/PR/A2をこのチャットで再開 | 行わない |
| 次の条件付き研究課題 | coherence保持部分空間の**生成・更新規則と測定費の同時設計** |
| 新しく成立・新規性を認定したアルゴリズム | 0件 |
| 次作業の実務担当 | ユーザーが課題・範囲を承認した後のCodex/Claude Code |
| 新規科学計算・実装 | 未承認・未実施 |
| 本レビュー結果の正式採択 | ユーザー判断。repository状態は変更しない |

**レビューの中心的な修正点**：新規性のある「場」を探すのではなく、既知の枠組みを正面から比較対象として固定し、その中で入力から情報・basis・操作を作る手順の差を研究する。今回の射影部分空間はその設計対象を具体化するbaselineであり、それ自体が発明だとはしない。

---

## 13. 外部一次文献と実際の確認範囲

検索確認日：2026-10-18。最新・網羅的priorityを証明する調査ではない。本文が取得できなかったものはabstract以上の保証を輸入しない。二次まとめサイト、検索に現れた合成研究サイト、Wikipediaは科学的根拠に採用していない。PDF本文の解析・図表抽出は本レビューでは行わず、以下のHTML/abstractを用いた。

| ID | 一次資料 | 確認範囲・利用上限 |
|---|---|---|
| L1 | Kanno et al., *Quantum-Selected Configuration Interaction: classical diagonalization of Hamiltonians in subspaces selected by quantum computers*, arXiv:2302.11320; Phys. Rev. Research 8, 023268 (2026) | arXiv/publisher abstract。sampling、classical projection、理想変分性の方法同定。全定理再監査はしていない |
| L2 | Yu et al., *Quantum-Centric Algorithm for Sample-Based Krylov Diagonalization*, arXiv:2501.09702v3 | HTML Algorithm 1、§II.1 Theorem 1、§III、methodsの対応部分。疎性/overlap/gapを含む保証条件を確認。実験数値を新規再解析しない |
| L3 | Kamoshita and Mitarai, *QSCI-CMP*, arXiv:2608.05766v1 (2026) | abstract/metadata。化学的preselectionとAAの既知性。HTML全文取得できず、回路・定理の詳細は未検証 |
| L4 | Zhang et al., *Quantum Jacobi-Davidson Method*, arXiv:2602.01670v1 (2026) | abstract/metadata。QJD/SBQJDの存在・目的を確認。HTML本文未取得、収束/費用の一般的保証は認定しない |
| L5 | Cohn, Motta and Parrish, *Quantum Filter Diagonalization with Compressed Double-Factorized Hamiltonians*, PRX Quantum 2, 040352 (2021) | publisher abstractと既存調査で示された方法の位置付け。詳細な定数・最適費用は輸入しない |
| L6 | O’Leary et al., *Partitioned Quantum Subspace Expansion*, Quantum 9, 1726 (2025), arXiv:2403.08868v3 | publisher abstract、HTML本文入口と関連構成。分割はKrylovの逐次subspaceで、occupation cellと同一という主張はしない |
| L7 | Zhang et al., *Measurement-efficient quantum Krylov subspace diagonalisation*, Quantum 8, 1438 (2024), arXiv:2301.13353 | publisher abstract。測定誤差・費用が既に研究対象であること。今回D2の最適性をこの論文で認証しない |
| L8 | Tancara et al., *Counterdiabatic ADAPT-VQE for Molecular Simulation*, JCTC (2026), DOI:10.1021/acs.jctc.6c00197 | publisher検索本文/abstractの方法記述。一般保証や他法に対する普遍優位は主張しない |
| L9 | Abraham and Mayhall, *Selected Configuration Interaction in a Basis of Cluster State Tensor Products*, arXiv:2002.03107, JCTC (2020), DOI:10.1021/acs.jctc.0c00141 | abstract。相関cluster tensor-productの既知性。全性能定理は未確認 |
| L10 | Benfenati et al., *Improved Accuracy on Noisy Devices by Nonunitary Variational Quantum Eigensolver for Chemistry Applications*, JCTC (2021), DOI:10.1021/acs.jctc.1c00091 | publisher abstract。Jastrow型非unitary後処理、depth–measurement tradeoffの先行例 |
| L11 | Zhang et al., *Variational Quantum-Neural Hybrid Eigensolver*, PRL 128, 120502 (2022) | publisher abstract。一般的な古典neural後処理という近接先行。全supplement/全sample complexityは未取得 |
| L12 | McClean et al., *Hybrid Quantum-Classical Hierarchy for Mitigation of Decoherence and Determination of Excited States*, arXiv:1603.05681, PRA 95, 042308 (2017) | arXiv abstractと方法の位置付け。B2–C3へのQSE対応自体は今回の代数的同定 |

### 文献URL

- L1: https://arxiv.org/abs/2302.11320 ; https://doi.org/10.1103/dmn4-snfx
- L2: https://arxiv.org/html/2501.09702v3
- L3: https://arxiv.org/abs/2608.05766
- L4: https://arxiv.org/abs/2602.01670
- L5: https://doi.org/10.1103/PRXQuantum.2.040352
- L6: https://quantum-journal.org/papers/q-2025-05-05-1726/ ; https://arxiv.org/html/2403.08868v3
- L7: https://quantum-journal.org/papers/q-2024-08-13-1438/
- L8: https://doi.org/10.1021/acs.jctc.6c00197
- L9: https://arxiv.org/abs/2002.03107
- L10: https://doi.org/10.1021/acs.jctc.1c00091
- L11: https://doi.org/10.1103/PhysRevLett.128.120502
- L12: https://arxiv.org/abs/1603.05681

### Repository固定URL

- E1: https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/b58d5750b2d9d1917d3f34d25dd49bdcaf6b5c66/docs/research_exploration/collective_transition_pause_decision_20261018/research_decision_record.md
- E2: https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/12324144a3d4f7a247f1944b4866549e9cc19152/docs/research_exploration/collective_transition_multijump_cycle_20261018/cycle_paper_derivations.md
- E3: https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/609a63231ee0786cf8da31f6b33358acfd6f2548/docs/research_exploration/cross_repository_overlap_survey_20261017/algorithm_improvement_overlap_matrix.md
- E4: https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/c6419859029824a4ee8c3dfd3c8126fe585ffbe2/docs/research_exploration/cross_repository_two_branch_delta_20261017/review_readiness_delta_handoff.md
- P1: https://github.com/HIROMU1015/Partially-Randomized-Trotter/blob/7af83266f96b714bb3fa2f1ef5e4bc89faf37db3/docs/research/qc_a2_certificate_connection_design_20261018/decision_handoff.md

---

## 14. 記録上の限界

- 既存SOURCEのGit blob/bytes/SHA-256を本レビューで全件独立再照合したとは主張しない。本文取得と原文の意味の検討が今回のscopeである。
- 全先行論文・supplement・出版版差分を網羅確認したとは主張しない。特にL3/L4のHTML本文は取得できていない。
- 本文の新しい記号・式は紙上の説明・設計診断であり、実行済みコードや科学数値ではない。
- 新しい規則、電子familyでの近似保証、最適shots、総E0利得、独立新規性は未確立。
- D1/D2、既存PAUSED/CLOSED/NOT_ADOPTED、各grantとSTOPは本記録で変更しない。
- 本Markdownは新規ローカル成果物であり、GitHubへ公開・commitしたものではない。後続への正式採用はユーザーが判断する。

**ここでレビューを完了する。後続の構成作業・実装・科学計算へ自動進行しない。**
