# Coherence保持・適応的部分空間：初期紙上構成handoff

2026-10-18 JST。**係数からbasis候補・測定計画・更新操作までの具体的な規則Gを一件記述した。しかし、独立した新アルゴリズム候補の成立・資源優位は認定していない。** 技術分類は、Gの生成・選択規則の独立性について「追加証拠が必要」。射影QSE、diagonal後処理、paired測定と再利用は既知法への還元として切り分けた。

これはユーザーが承認した初期構成作業の報告であり、GPT Level 1科学レビュー、方向の正式採択、追加計算の承認ではない。J1・Q1・R1-P・集団遷移生成PAUSE・A2等の状態は変更していない。

## 1. 今回初めて具体化した手順

Gは、電子係数の支持と絶対係数graphから有限のoccupation-count predicateを生成し、一つのseedのcoherent cellを分割する。Pauliが結ぶ配置対の位相を共通記録に残し、各候補への再labelでH/Sを推定する。有限tree class全体のconfidenceを用い、確率付きenergy gainを追加古典費で割った規則により更新する。正解振幅・ground・gap・固有projectorは要求しない。

小さな部分空間問題を解くこと自体を新生成規則と数えず、predicate生成から停止条件までを記述した。新しい標本、matrix/vector、分子入力、数値solver、回路は生成していない。

## 2. 何が成立し、何が残ったか

| 分類 | 結果 |
| --- | --- |
| 具体化 | 係数→有限辞書→split候補→共通記録→confidence付き選択、という入力からの写像を記述 |
| 紙上で成立 | 全候補の不偏entry推定、固定classでの適応的再利用の同時誤差幅、理想span包含、confidence event上の受理更新によるenergy低下 |
| 既知法への還元 | basisは射影QSE、stateはVQNHE型diagonal関数。paired測定・再利用はVQNHEと同じ情報を取得する。小space gainによる選択はSSE等に具体的先行例あり |
| 限定的障害 | 対角文法はseedのzero supportを増やせない。直交Gramでもp_minは測定費に残る。人口samplesだけでは位相matrixを得られない |
| 別案R | 係数termからnumber-conserving操作poolを作る案は既知operator-pool QSEの組合せへ帰着。独立した取得・費用差は未構成 |
| 追加証拠が必要 | Gの係数dictionaryとconfidence／費用選択の組に、強い既知手順と異なる有用な差があるか |
| 未構成・未判定 | 非自明な連結H_dd familyでの小K近似保証、p_minの合法な下界、同精度の総費用差、絶対E0への有用な停止証拠 |

「具体的な独立候補が残る」との判定には進めない一方、QSEに属することだけを理由に研究領域全体をNO-GOともしない。現時点で正式採択・新規性認定したアルゴリズムは0件である。

## 3. 最小判別から分かったこと

P-a（共通記録と適応的confidence）は紙上成立した。P-b（再取得回避そのものの独立性）は成立しない。VQNHEでも同じpiecewise関数の双線形形式を同じ記録から再評価できるためである。従って「新measurement再利用法」という中心claimには使えない。

残るP-cは、係数dictionaryの生成・費用を含む選択規則の差である。SSEの2次元filterや適応QSEへ同じ辞書とcriterionを与えれば、同じspace／同じ選択になる場合がある。未知の差をbasis圧縮率や小例の理想energy低下で代用しない。

非自明な連結familyでの有用性P-dを数値化する前に、P-cに比較可能な差があるかを判断する必要がある。これは今回の結果を見た後で別の成功条件へ切り替える許可ではない。

## 4. GPT／ユーザーに判断してほしい事項

1. Gの残る部分を、独立候補のための限定的な文献・還元照合として追う価値があるか。それとも今回を構成ノートで区切るか。
2. 追う場合、VQNHE＋同じ関数class・shadow QSE＋同じ辞書を主対照に固定してよいか。既知手順と同じなら別名の候補を保持しないという判別を採るか。
3. P-cの差が得られた場合に限り、連結H_ddの一splitを合法情報から有用と認証する係数条件P-dを次の紙上課題にするか。一般分子への保証・数値実験は別判断である。

Codexは研究方向・新規性・論文claimを独自に採択していない。上は次段階の**提案**であり、追加作業の実行承認ではない。

## 5. 読む順序と監査

本書 → [課題・access](research_problem_and_access.md) → [一次文献・強対照](prior_art_and_baselines.md) → [生成・更新規則](adaptive_subspace_construction.md) → [数学・費用・判別命題](mathematical_and_cost_analysis.md) → [将来検証の条件](future_validation_conditions.md) → [SOURCE registry](source_registry.json)・[文献registry](literature_registry.json)・[静的監査](static_audit.json)・[provenance](provenance.json)。承認と前回GPT判断の原本は[inputs](inputs/user_instruction.txt)と[再レビュー](inputs/gpt_rereview_20261018.md)。

固定7commitに対応する13資料のblob／bytes／SHA-256と固定rawを照合した。origin/resultとverified snapshotは別field。特にPR A2 handoffのoriginは8031f29effdfd1b17dacef55233a1a5a10dc4d78、指定snapshotは7af83266f96b714bb3fa2f1ef5e4bc89faf37db3。過去資料の全transitive監査や数値再解析は行っていない。

文献は13件のHTML本文の方法該当箇所と補助8件の一次abstractを確認した。後者にはGを具体化した後のCASH-QSE、graphによるoperator選択、energy選択、AIM／Pauli再利用、Boolean表現の限定追加検索6件を含む。QJD本文は今回取得できた。一方、全出版版差分・全supplement・同時期の全手法を網羅していない。

保全監査では既存7 checkoutのHEAD・branch・tracked diff digestを比較した。6件はstatusも同一。PR rootには並行作業による未追跡文書 `qc_a2_phase_b_results_scientific_review_20261018.md` の追加を観測した。今回これを作成・変更・読解せず、固定A2 SOURCEを置き換えていない。全chatの最新状態を確認したという意味ではない。

## 6. 公開とMandatory STOP

repositoryは `HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae`、branchは `qc-coherent-adaptive-subspace-paper-20261018`。baseはb58d5750b2d9d1917d3f34d25dd49bdcaf6b5c66で、Evaluation側の必要な旧資料はbranch履歴に含まれる。PR資料は固定commitリンクで参照し、重複copyしない。

本directoryだけを通常commit/non-force pushし、remote SHA・独立fetch・全新規blob／bytes／SHA-256・固定rawを照合する。payload公開後の結果を子commitのpublication_receipt.jsonへ保存し、最終receipt自身を含む照合はチャットで報告する。manifestは自己除外を明示する。自分の最終commit SHAを自分のblobへ埋める循環を作らない。

**公開・照合後に停止する。** 次の担当はGPT／ユーザー：§4の継続可否・比較範囲を判断する。Codexの次の作業は、その別指示がある場合だけP-cの限定照合を行う提案である。数値検証・実装・科学実行契約やgrant発行・既存系列の再開へ自動進行しない。
