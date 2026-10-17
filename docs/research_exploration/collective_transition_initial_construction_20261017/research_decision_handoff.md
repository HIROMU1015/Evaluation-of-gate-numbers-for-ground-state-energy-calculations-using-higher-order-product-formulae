# 集団遷移生成：判断用handoff

2026-10-18 JST（作業系列ID：20261017）。**結果はB（具体化した規則は既知構成へ還元）＋C（限定文法の障害）。一般Hへの新しい係数生成則はD（未構成）。Aの独立新構成候補は0件。** 正式な研究採否や一般NO-GOを記録するものではない。

branch `qc-collective-transition-initial-construction-20261017`、親commit `c6419859029824a4ee8c3dfd3c8126fe585ffbe2`、保存先Evaluation。公開commitの40文字SHAと公開後照合は最終報告で示す。

読む順序：本書 → [構成](collective_transition_construction.md) → [非可換紙上検証](noncommuting_paper_verification.md) → [先行研究比較](prior_art_and_mechanism_comparison.md) → [入力/access](research_problem_and_access.md) → [E0接続](energy_estimation_connection.md) → [SOURCE registry](source_registry.json)・[静的監査](static_audit.json)・[provenance](provenance.json)。

## 1. 具体的な遷移生成規則を作れたか

**限定classでは作れた。** 対角係数からjoint pair下降predicateを作る規則Dに加え、非可換な

\[
H_*=cI-U(n_1n_2+n_3n_4)-\mu(n_3+n_4)
+t(a_3^\dagger a_1+a_1^\dagger a_3),\quad U>\mu>0,t>0
\]

について、係数→detuning/回転角→occupation-controlled W→W†/pair reset/Wという有限CPTP列を明示した。未知のeigenstate・gap・全遷移表や全H oracleを入力していない。紙上角度とgate/ancilla/resetの実装費を区別した。

## 2. 既知法と何が異なるか

裸pair resetからの差は、非可換hoppingと相互作用を角度に保持する点。しかし、その係数生成は**条件付き2次元blockの解析的対角化と標準rank-one振幅減衰**に尽きる。小blockを解いてresetするだけを越える規則にはならない。この模型ではtarget自体をW|34〉として直接準備でき、未知一般Hに対する資源優位もない。

同じgateを使ったことだけでBにしたのではない。今回具体化できた前処理・operation・保証まで小block解法へ還元されるためである。文献の特定アルゴリズムに全く同じW式が載るとは主張しない。一般Hに効く独立した生成差は未提示。

## 3. 非可換電子Hで何が示せたか

CAR符号を含め、source `a=W|12〉` とtarget `b=W|34〉` を生成し、正の差 `ω=μ+(R_B−R_A)/2` に対して

\[
\widetilde C^*(H_*)-H_*=-\omega\sin^2\theta\,|a\rangle\langle a|\preceq0
\]

を紙上で示した。N=2を保存し、spinを1/3=↑,2/4=↓と割り当てればN↑/N↓も保存。scalarはTPから保持される。

反復はaの人口をbへ移すが、他のdark成分は不変。単に非可換toyでenergyが下がったことを一般ground準備性能に広げていない。

## 4. 独立研究として残る科学的問題

一般の非可換電子係数から、解析的小blockの事前可解性に依存せず、元Hに対するcoherence変化と集団移送を同時に生成する規則は未構成。複数coupler/cycle/限定input classでの進捗という余地は未否定だが、今回そのための独立新候補を保持・採択したわけではない。

既存system–bath/filtered jump/fermionic coolingは、reset・多電子coupler・事前の全basis不要という要素を既に含む。新規性はこれらの語だけでは得られない。[比較文書](prior_art_and_mechanism_comparison.md)の一次資料到達点を維持する。

## 5. 最も重要な数学的障害

固定rank-one振幅減衰 `T=|b〉〈a|`、0<θ≤π/2では、全状態一step単調性の必要十分条件が

\[
(I-P_a)H|a\rangle=0,\qquad
\langle b|H|b\rangle\le\langle a|H|a\rangle
\]

になる。一般Hのsource固有stateを求める難しさを、jump定義へ隠せない。5番目のmodeへのhoppingを加えると旧aに補空間couplingが生まれ、旧dressing固定では単調性が破れる。

この条件は全状態一stepを要求したrank-one文法に限る。cycleや複数jump、許容加熱、入力classを否定しない。紙上検証V11/V12には、coherence残差とsource人口に基づく限定inputの下降十分条件も残した。

## 6. 次に必要な検証

最初に判断すべき命題は「全状態一step単調性を緩めた**具体的な**複数jump/cycleを、境界hopping込みの係数から作り、その実チャネルの進捗を示せるか」である。これは次作業の候補であり今回の延長実行権限ではない。未知source/projectorを入力する案、旧Wを固定したまま角度を微調整する案では不足する。

追加数値計算は今回不要・未実施。今後必要なら、[E0接続文書](energy_estimation_connection.md) §5の入力・判定・誤差・STOPを別契約/承認で固定する。既存toyの数値再確認だけで独立性が変わるとはしていない。

## 7. 継続・修正・保留の判断担当

**GPT／ユーザー**：B/C/Dの限定結果を読み、別の具体的cycle構成を依頼するか、入力class/出力目的を修正するか、この系列を保留するかを判断する。今回はその方針・正式状態を決めない。**Codex**：公開・同一性/保全照合で停止し、新探索・詳細レビュー・計算・実装を自動開始しない。

J1はPAUSED_PENDING_NEW_MECHANISM、Q1はPAUSED_PENDING_NEW_LEVEL_INSERTION_RULE、R1-Pは独立候補不保持、SOS-PF A1現分割生成探索CLOSED、A2 NOT_ADOPTEDを維持。第一・第二研究、Track A/B、M1-S、grant/authorization、SOURCE/raw結果/marker/STOPを変更しない。

## 8. 参照原本・監査・公開

指定された[戦略レビュー原本](inputs/new_algorithm_strategy_review_cross_repository_20261017.md)は、rootで未追跡だった40,880 bytesをbyte-identicalなcopyとして本dirへ保存した。SHA-256 `f080ec30684e3f44f5fb89712f00681375f2240e61c3ea4ff91ca2fb792c76e9`。root原本は変更せず、原文の「repository変更/push未実施」はそのレビュー作成時の記録として保存する。原本掲載は、その自己申告した承認チャットや科学claimの独立認証ではない。

原本の既知診断と今回の新しい紙上構成を分ける。Kraus完全性・裸pairの障害は指定課題/原本由来の再導出、係数依存W、V8–V12と境界例は今回の限定設計診断。どれもpriority・新アルゴリズム採択・詳細科学レビュー完了ではない。

既存横断資料は再利用し、PRはread-only。新規資料だけを明示stageし、通常commit/non-force push、remote SHA・独立fetch・Git blob/bytes/SHA-256・固定rawを照合する。manifestはprovenance自身を除外し、同ファイルも公開後照合対象に含む。

開始前Evaluation114・PR184の既存worktreeをHEAD/branch/status/staged/unstaged digestで比較する。これはignored runtimeや全未追跡内容/他jobの包括監査ではない。科学数値計算、科学用記号プログラム、solver、simulation、回路build/compile、benchmark、新grant、研究正式採択は0件。

**Mandatory STOP：成果物の公開・照合後に停止。**
