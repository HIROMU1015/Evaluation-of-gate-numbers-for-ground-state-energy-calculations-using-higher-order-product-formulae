# 第2研究prospective validationのサーバー事前確認

強いCPUを持つGPUサーバーで、分子と条件ごとの並列CPU実行を準備する。
現在の指示はhardware/allocation、既使用条件、可用性、資源見積り、
protocol案までに限る。新規科学計算はまだ許可していない。

## サーバーへ渡す資料

[実行指示書](../../../review_response/gpu_pf_study2_prospective_preflight_prompt_20261005.md)を
handoff messageの40文字commitから全文読む。
[許可範囲](authorization_scope.json)、[source registry](source_registry.json)、
[bundle manifest](bundle_manifest.json)も同じcommitの内容を使う。

起点は公開済み成果整理snapshot
`e895870f16878ee4181b0e0dfe3159826a791563`。
本資料を含むpublication commitは、Codex最終報告の40文字SHAを使う。
自己参照hashをこのファイルへ埋めない。

## 進め方

1. 今回はサーバーread-only preflightと未承認protocol案を作り、GitHubへ公開して停止する。
2. GPT側とユーザーが条件一覧、科学規則、計算上限、M1範囲を承認する。
3. 別承認でimplementation sealとtruth-free tests、input/reference/座標freezeへ進む。
4. 条件単位にCPU並列化し、全predictionのcommit/hash freeze後だけtruthとscoringへ進む。
5. 追加救済をせず、結果をGitHubへ公開し、GPT側で研究上の解釈をレビューする。

GPUサーバーという呼称は設置環境を指す。今回はGPUの照会・割当・移植を行わない。
強いCPUや多数の並列枠があるというユーザー報告と、利用可能な実割当の確認は分ける。
推奨する並列単位はconditionであり、process数とBLAS thread数の積、同時RAM予約を管理する。

## 提案の出所と未確定事項

ユーザー提示のprospective multi-molecule構想は20〜40条件、各3候補時刻を想定する。
元添付のSHA-256は
`5024ae822bc0bdf528d4a57f733a536b0acd7289fdcbc3cbea9d0f9ef97edf1e`。
添付はgovernance上の提案であり、科学的evidenceや最終protocolではない。
本指示が必要な範囲と未確定項目を公開形で整理している。
「研究完成度」「論文の格」や添付内の未解決citationは、本指示の根拠に採用しない。

分子名・geometry・state/basis・一般分子のreference/time rule・M1のrank/width/subset・
truth method/gates・CPU/RAM/wall/retry上限は未承認。
H-chainやHFのnative contractを一般分子へ無断で流用しない。
候補例が本当に未使用かは過去使用履歴の確認が必要で、LiF等を未使用と断定しない。

添付の段階列挙に関わらず、M1は最終prediction freezeと新truthより前に実施する設計とする。
cheapのsign flipやspectralが勝つ結果を見て新条件を選ばない。
新familyと同じfamilyの新geometryを区別し、欠測・適用不能を事後除外しない。
slackによるsafe/unsafe整理はbudget式の同値変形であり、運用上のcertificateとしない。

## 参照資料

- [承認済み研究方針とclaim scope](../result_synthesis_20261005/approved_scope_and_rq.md)
- [成果整理版の未確立事項](../result_synthesis_20261005/outstanding_claims.md)
- [主解析のquantity dictionary](../budget_safety_mechanism_20261005/quantity_dictionary_and_analysis_spec.md)
- [H8の保存実測と資源上の限定](../../../artifacts/hchain_h8_memory_safe_extension_20261004/report.md)
- [SciPy公式の並列実行説明](https://docs.scipy.org/doc/scipy/tutorial/parallel_execution.html)

origin/resultとverified snapshotの区別はsource registryで保持する。
H8の保存値は計画算術の参考であり、別server・分子の性能保証や新規計算の承認ではない。
本資料作成時にはsource code、scalar、prediction、truth、主図を変更していない。

## GPT側で次に判断する事項

対象条件とstrata、一般分子へのreference契約、M1を全件か固定subsetにするか、
各phaseの資源上限、truth/gap方法と失敗処理を判断する。
preflight完了statusは `prospective_budget_safety_preflight_complete_review_required` とし、
そのstatusだけでは本実行を開始しない。
