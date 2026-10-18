# Phase A handoff：B-01正式保留

**B-01: `PAUSED_PENDING_NEW_EVIDENCE`。技術的根拠：E（構成研究着手の根拠なし）。** 最新ユーザー指示による正式な研究管理判断であり、Codex独自の採否判断ではない。他研究系列の状態変更は0件。

読む順序：[正式判断](research_pause_decision.md) → [技術的根拠と限界](technical_evidence_and_limits.md) → [再開条件](reopening_conditions.md) → [decision](decision.json) → [SOURCE](source_registry.json)・[静的監査](static_audit.json)・[provenance](provenance.json)。

前回の固定成果は `bbd12642e2540e0d5c6341339820f0b153091d10` と `ed6781f7004444ce77b2378303404fd23efbbc95`。両段階のhandoff、課題カード、定理/access、eta/coarse、標準統計、SOURCE/provenanceを確認し、原本は複製・変更していない。新しい科学的結果・不可能性・priority認証は追加していない。

再開には、正規化moment・confidence/標本費、費用付き合法eta、同一D1での生成規則/費用のいずれかについて判断を変える具体的証拠と、GPT／ユーザーの別判断が必要。これらの探索は今回の追加作業ではない。

Repository：`HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae`。
Branch：`qc-b01-pause-decision-20261018`。
Directory：`docs/research_exploration/b01_pause_decision_20261018/`。

payload公開後にremote SHA・空bareへの独立fetch・全blob・bytes・SHA-256・commit固定rawを確認し、その完了事実を子commitのpublication receiptへ記録する。receipt自身を含む最終commitも独立照合する。未実施の照合や自己hashを先にPASSとしない。

開始時308 checkoutのHEAD/branch/status、両dirty rootのstaged/unstaged diff digestとuntrackedの名前/size/mtime/mode等のmetadataを照合する。既存資料はread-onlyで扱う。untracked全内容・ignored runtime・共有jobの包括的監査を意味しない。今回参照する非公開原本は内容を公開せず、最小限のidentity metadataだけを保存する。

**Phase Aの公開・独立同一性・保全確認が全て完了した場合だけ、別branch/worktreeでPhase Bへ進む。** 問題があればPhase Bを開始せずSTOPする。Phase Bは既存成果の状況・原稿・残作業・暫定優先度の整理だけであり、原稿作成・追加検証・計算・重要科学レビュー・投稿・正式採否を開始しない。
