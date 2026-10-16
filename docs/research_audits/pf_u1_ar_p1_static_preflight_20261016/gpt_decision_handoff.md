# GPT判断用handoff：U1-AR P1-S1〜S3静的確認

2026-10-16。S1〜S3の資料取得・schema確認・定義監査を完了した。新規科学計算、科学値の再集計/再ranking、科学実装はいずれも **0件**。P1-A1〜A4は実行せず、AR仮説の実証・棄却、P1 GO、U1-AR採択、C1からの方針変更も決定していない。

Claude `レビューoutter(5).md` は検索したアクセス可能範囲で取得できなかった。ユーザーが列挙した論点に従って監査し、Claude原文との逐語照合不能を残した。P1-A1〜A4の正確な原文仕様も未取得。原文の代作や推定仕様による実行はしていない。

## 読む順序と固定根拠

1. 本handoff。
2. [literature_correspondence.md](literature_correspondence.md)：必須9論文の実取得版・本文読解箇所・既知/未確認の区別。
3. [stored_data_availability.md](stored_data_availability.md)：固定commitリンク、保存field、private/欠落/所在未確認/identity不足。
4. [definition_contract_audit.md](definition_contract_audit.md)：S3-1〜4と4分類。Claude原文未確認と、sourceで確認した相違を分離。
5. [provenance.json](provenance.json)：GitHubから取得したsourceのbyte/SHA/blob、origin/resultとverified snapshotの分離、paper identity、自己除外manifest。

前提となる完結性監査は固定commit `b4a7a8204b8d7fa0a2a1bc79bfbdd7cf63177ca1` の [audit](https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/b4a7a8204b8d7fa0a2a1bc79bfbdd7cf63177ca1/docs/research_audits/pf_finite_time_completion_20261016/research_completion_audit.md) → [evidence map](https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/b4a7a8204b8d7fa0a2a1bc79bfbdd7cf63177ca1/docs/research_audits/pf_finite_time_completion_20261016/open_question_and_evidence_map.md) → [options](https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/b4a7a8204b8d7fa0a2a1bc79bfbdd7cf63177ca1/docs/research_audits/pf_finite_time_completion_20261016/research_completion_options.md) → [provenance](https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/b4a7a8204b8d7fa0a2a1bc79bfbdd7cf63177ca1/docs/research_audits/pf_finite_time_completion_20261016/provenance.json)。この4資料をGitHubから取得し、前回manifestのmarkdown hashとも照合した。再生成・書換えはしていない。

## 判断に影響する結果

| 論点 | 静的に確認した範囲 | 未確立の範囲 |
|---|---|---|
| S1：新規性 | R3–R5でFloquet折り返し・回避交差・混合・共鳴の議論が既存。R6は化学QPEのwrappingを扱う。L5/L7/L8は固有値特化誤差・QPE資源/step選択に重なる。 | 「共鳴がある」「化学QPEでwrappingが重要」だけでは独立した新規性は確認できない。本条件の有限時間モデル破綻との因果性・予測能力・適用域保証は未確認。 |
| S2：データ | F02に物理励起gap/D4結合、F05/X02/HFに選択PF枝のphase gap・overlapが公開される。F01/HF private cache実体とhashを確認。 | 最近接相手ID・相手のH励起状態対応・全PFベクトルは確認した公開出力にない。HFの36 eigendecompositionはscalar保存で、全36系が再利用可能とは言えない。NH3/N2/COの完全励起/全PF checkpointは未特定。 |
| S3：定義 | τは外側一step/Ha⁻¹、phase gapはsector内の円周距離/rad、overlapは確率。 | warningはORでAR onsetではない。X02 previous最大とHF/NH3 ground最大は異なる。unwrap integerは物理state IDではない。Claude原文との一致は未確認。 |
| source identity | F02/F03は同じNPZ hash、X02コードは別公開commitから実行時hash一致で補完。 | X02とF01のH/basis共通byte identityは未完結。label一致だけで完全な共通基底を仮定できない。historical N2/COを後続の別sourceで救済しない。 |

## 独立確認が必要な数学的箇所

命題Aは局所gap付き解析性から全実軸一意接続への移行、Bは実phase近接と複素特異点/Taylor半径の関係が未確認。Mは十分条件の適用範囲と、PF stage・負係数・ノルム・gaugeの対応が必要。R/Nは主張する不可能性の対象クラス・入力・精度・領域が未定義で、読了範囲にその一般定理は確認できない。今回は詳細数学レビュー・新証明・反例を開始していない。

既存データだけでP1の問いを判定できるかは、正確な問いと必要な対応fieldに依存する。scalarの所在確認は完了したが、AR相手や因果性を問う判定が既存資料だけで完結するという根拠はない。新しい計算が不要とも必須とも一括決定しない。まず原文・定義・checkpoint/identityを閉じる必要がある。

## GPTに留保する判断と実行前の条件

- C1で完結する場合：前回optionsの既存結果・限定claimを維持できる。今回の資料はARを新しい確立claimに加える根拠にはならない。既存の数学的不可能性を一般定理へ拡張しない。
- 狭いU1-ARを検討する場合：既知Floquet/化学wrappingとの差分を、対象分子・PF・誤差モデル・測定量・有効域の問いとして限定できるかをGPTが判断する。採択やGOはまだ行っていない。
- 計算前：Claude原文とP1-A1〜A4仕様、枝/sector/gauge/時間・必要field、source identity、既存checkpointの保存範囲を確認する。Magnusの十分条件を実AR閾値とせず、W_S/ω_n/結合の定義を先に固定する。
- 追加計算を必要と判断した場合：分子・geometry・PF・state・座標・回数・truth access・freeze・停止点を別途承認する。未保存fieldを理由に無制限に再実行しない。今回の静的確認はその承認ではない。

## 公開単位・検証・保全

Repository：`HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae`。branch：`pf-u1-ar-p1-static-preflight-20261016`。base：`b4a7a8204b8d7fa0a2a1bc79bfbdd7cf63177ca1`。新規5資料だけを独立worktreeで作成・明示stageし、通常のnon-force pushで公開する。既存の原本result/sourceは固定commitをリンクし、今回のcommitへ再コピーしない。commitの自己参照を避けるため最終handoff SHAとremote再取得検証は実行完了後の最終報告に記す。

公開前に新規文書のリンク先Git object・SHA/manifest・変更範囲を検査する。公開後にremote先端SHAを照合し、GitHubから独立bareへ再fetchして新規5 blobのbyte/SHA-256一致を確認する。検証失敗時はhandoff完了とは報告しない。

既存dirty/staged/untracked root、active `src/trotterlib/cost_validation.py`、科学SOURCE・raw CSV・protocol・method status・decision/review・authorization/grant/ledger・既存manifest・STOPを変更しない。第一/第二研究の正式状態、FS-R1 Phase B、R5で停止した新アルゴリズム系列を再開しない。private pickle/NPZ・matrix/vector/state/unitary、認証情報は公開しない。過去の `push_authorized=false` 等は作成時点の凍結記録として保存する。

科学計算・科学値再集計・科学実装：**0件**。P1 GO / U1-AR採択：**未判断**。**Mandatory STOP：この静的handoff後、自動的にP1・数学的詳細レビュー・新研究・FS-R1その他へ進まない。**
