# Evaluation project — Codex working agreements

## Global repository safety rules

- Never commit to or push to quration repositories, including
  `/home/abe/Project/quration/quration-core` and remotes under `quration/*`.
- Only commit or push when the target repository remote is under `HIROMU1015/*`.
  Check the actual fetch and push URLs before any commit/push; do not change a remote
  to bypass this rule.
- If a task touches both allowed and other repositories, keep other-repository
  changes uncommitted and unpushed unless the user explicitly changes this global rule.
- Preserve unrelated edits and staged files. Do not use reset, clean, stash,
  force-push or merge to main to prepare a research handoff.

## 研究判断の役割分担

- **GPT側**：研究全体の方針修正、RQ、新規性、論文の着地点・中心claim、
  追加検証の必要性と範囲を判断する。
- **Codex側**：ユーザー/GPTが承認した仕様に沿う細かい検証、保存値の再集計、
  実装・テスト、provenance監査、GitHubレビュー資料の整理を担当する。
- 検証結果が方針変更を示唆しても、Codexが独自に研究方針を変更しない。
  根拠・制約・未解決事項・選択肢をまとめ、GPT側の判断とユーザー承認を待つ。
- GPTの承認済み判断を文書や実装へ反映する作業はCodexが行ってよい。
  承認済み判断とCodexによる提案・未承認事項を明確に区別する。

## 検証の境界

- 検証の包括的な依頼を、新規科学計算や無制限の再実行の承認と解釈しない。
  計算対象・候補座標・PF・state・作用回数・truth access・停止点を既存承認から確認する。
- 再集計・手続き監査は原本のprediction、budget、width、threshold、gate、
  formal resultを変更しない。post-hoc analysis/auditは別artifactに残す。
- 新しい分子/時刻/PF/rank/gap/truth、fitting、threshold/gamma調整、
  結果後の救済は個別承認がなければ進めない。freezeとtruth barrierを維持する。
- 研究判断が必要になった場合は、その部分を未承認として停止し、
  承認済み範囲内の監査・資料整理だけを続ける。

## GPTへのGitHub handoff — commit/push必須

GPTはローカルファイルではなくGitHubリポジトリを確認する。
GPT向けレビュー資料の引き渡しには、必要資料のcommit・pushを作業の一部として含める。
このユーザーの継続指示は、許可リポジトリで必要資料だけを通常のnon-force pushで
公開する承認であり、無関係な変更や科学計算の追加承認ではない。

1. summary/report、必要なscalar結果、protocol/claim scope、source registry、
   hash/manifest、関連test/auditを列挙する。ローカル絶対pathだけを根拠にしない。
   既存commit内の資料は再生成・重複commitせず、公開branchの履歴に含まれることを確認する。
2. sourceの`origin/result commit`と`verified snapshot commit`を別fieldで保持する。
   同一blobでも役割を統合しない。manifestは自己除外を明示する。
3. 必要ファイルだけを明示的にstageしてcommitする。`git add .`で
   他の作業を巻き込まない。dirty rootでは独立したclean worktree/branchを使う。
4. `HIROMU1015/*`の適切な研究branchへnon-force pushする。
   remoteのbranch先端SHAを`git ls-remote`等で照合し、handoff commitが
   remoteから取得可能で、必要資料がそのcommitのblobに含まれることも確認する。
5. 最終handoffにはrepository、branch、40文字commit、GitHubのcommit固定リンク、
   読む順序、検証済み事項と未確立事項、GPTに判断してほしい項目を示す。
6. push失敗、remote不一致、必要blob不足なら、引き渡し未完了として報告する。
   local commitだけで「GPTが確認可能」「公開済み」と言わない。
   後続のユーザー指示がlocal-only/push禁止ならそれを優先し、GitHub handoffを保留する。

認証秘密、`.runtime`、pickle、matrix/vector、unitary、exact stateは、
別途明示承認された公開方針がなければcommit/pushしない。
履歴内の「push未実施」「push_authorized=false」は作成時点の記録として保存し、
後の公開を理由に凍結artifactを書き換えない。現在の公開状態はhandoffで別途報告する。

## Worktree内での継続

- 新しいworktreeでも、この役割分担とhandoff規約を確認してから作業する。
  Git rootが異なる既存worktreeに親workspaceの指示書が自動適用されるとは仮定しない。
  このファイルが起点commitにない場合は、ユーザー提供の同規約を参照するか、
  許可された指示書追加として取り込む。凍結science sourceを変更して導入しない。
