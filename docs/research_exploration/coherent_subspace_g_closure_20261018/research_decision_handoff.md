# 現G探索の正式CLOSED記録：handoff

2026-10-18 JST。**現G探索 CLOSED／独立新アルゴリズム候補 NOT RETAINED／技術的根拠 P-c＝B。P-dは未実施・未判定。他研究系列の状態変更なし。**

## 記録した判断

ユーザーの今回の明示承認に従い、固定されたG構成を独立新アルゴリズムとして継続する探索を終了した。Codexが終了方針を新たに選んだものではない。QSE、QSCI、VQNHE、coherence保持部分空間法全般はCLOSEDの対象外である。

Hamiltonian係数graphからの有限dictionary、coherent cell更新、共通測定記録、同時confidence、古典費用を含む選択・STOPの具体化は技術的成果として保存する。同じ有利なdictionary・seed/access・測定情報・confidence・費用・固定規約を与えた場合、VQNHEのpiecewise complex F、QSEと既知の選択手順でGの操作・全更新列を再現できるというP-c判定Bを根拠とする。

理想測定モデルでは配置対測定から必要な意思決定統計の標本分布・分散・相関まで対応する。一方、SSE原法の標準shadow分布と選択手順には違いがある。具体的な独立生成機構、独立保証、資源優位は確認されていない。Bは網羅的priority認証でも全実装の同等性証明でもない。

P-dの有用性、native回路・noise・routing費、元Hの絶対E0への有用な精度保証、網羅的priorityは未解決のまま保持する。不可能性を証明したとは記録しない。現Gの独立候補としての継続根拠が得られなかったため、追加検証には進まない。

## 固定SOURCEと読む順序

1. [正式判断](research_closure_decision.md)と[機械可読決定](decision.json)。承認の出所と対象を確認する。
2. [技術成果・還元](technical_outcomes_and_reduction.md)。P-a～P-cの経過と固定根拠を確認する。
3. [未解決事項・境界](remaining_questions_and_scope.md)。不可能性へ広げない範囲と他系列の保全を確認する。
4. [SOURCE registry](source_registry.json)、[静的監査](static_audit.json)、[provenance](provenance.json)。identity・来歴・監査範囲を確認する。

初期構成は`7bbcc6c35a3d53bcdbbf720526c5cae0d885c7cd`の`coherent_adaptive_subspace_initial_paper_20261018/`、P-cは`793cd63089dea8ca3e66b8c7faba173a198530eb`の`coherent_subspace_pc_mapping_20261018/`。両者はこのbranchのbase履歴内にあり、既存25資料を複製・修正していない。横断／PR参照5件と合わせて固定30資料のblob・bytes・SHA-256・commit固定rawを照合する。origin/result commitとverified snapshot commitは別fieldを保持する。

最新共通運用指示`research_project_instructions_unified_2026-10-17.md`を確認して適用した。旧版を運用正本として併用しない。今回の直接ユーザー指示、rootと新worktreeのAGENTSも適用する。untrackedな共通指示原本はコピー・公開せず、観測identityと適用範囲をprovenanceに記録する。既存のSOURCE・科学契約・承認・grant・STOPは変更しない。

## 公開・検証の範囲

Repository：`HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae`。branch：`qc-coherent-subspace-g-closure-20261018`。base：`793cd63089dea8ca3e66b8c7faba173a198530eb`。今回専用の新規directoryだけを明示stageし通常commit/non-force pushする。

公開後にremote SHA、空の独立bareへのfetch、Git blob、bytes・SHA-256、commit固定rawを照合する。親payloadの照合を子commitの`publication_receipt.json`に記録し、receipt自身を含む最終照合は最終チャットで報告する。manifestは自己除外を明示する。既存2 repositoryに登録された開始時303 checkoutのHEAD・branch・porcelain status digestと両rootのstaged／unstaged diff digestを比較し、並行変更があれば書き戻さず区別して記録する。未追跡ファイル内容・ignored runtime・全共有jobの包括監査ではない。

監査はGit・文書・JSON・link・hash・保全の確認だけである。今回の唯一の正式状態変更はユーザー承認済みの現Gに限定する。新規科学計算、保存科学値再解析、科学用symbolic checker、solver、P-d構成、新候補探索、回路build/compile/benchmark、新重要科学レビュー、新科学契約・grant発行は行わない。

## 次の担当とMandatory STOP

**Codexは公開・照合後に停止する。後続の承認済み研究作業はない。** 本判断の再承認や追加の詳細レビューを今回の完了条件として要求しない。

次の研究方針はユーザー／GPTが別途判断する。新しい方向の探索・現G再検討・科学実行が必要な場合も、その新しい依頼の対象・範囲・承認を受けるまで開始しない。
