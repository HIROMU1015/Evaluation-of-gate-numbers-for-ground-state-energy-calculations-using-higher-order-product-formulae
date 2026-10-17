# R1-P：独立研究候補としての不保持の正式判断記録

2026-10-17 JST。**ユーザーの明示承認に基づき、R1-Pは独立した新アルゴリズム研究候補として不保持とする。**

| 項目 | 記録 |
| --- | --- |
| 判断記録ID | R1-P-DECISION-20261017-NONRETENTION-01 |
| 判断対象 | T0で定式化されたR1-Pを、独立した新アルゴリズム研究候補として保持するか |
| 正式状態 | **NOT_ADOPTED**（R1-Pの独立研究候補としての不保持） |
| 判断権者・承認者 | 本作業を依頼したユーザー |
| 承認の出所 | 本チャットの「Codex作業指示：R1-Pの不保持判断を正式記録」 |
| 承認された判断 | 「R1-Pは独立した新アルゴリズム研究候補として不保持とする。」 |
| 判断根拠の固定commit | b39a54443e6b4780295bc0499ac8f8d7b10b083f |
| 元の定式化の固定commit | f0da24896b346e59ce225d1c264dd04420e1276c |
| 記録・公開担当 | Codex。承認済み判断の記録、静的同一性監査、commit・通常pushのみ |
| 管理方式 | 新規判断記録とprovenanceによる追記型。既存のSOURCE・handoff・状態記録は変更しない |

状態識別子は既存の研究状態管理にある `NOT_ADOPTED` を用い、対象を上表の独立研究候補に限定する。
研究全体の `CLOSED`、一般的な数学的 `NO_GO`、他課題の状態変更を意味しない。
以前の採択を取り消したという履歴も作らない。元のR1-Pは未採択の課題案だった。

今回の承認はユーザーの直接指示に基づく。外部承認ID、grant、新しい科学実行契約、GPT詳細科学レビューの実施を作成・推認しない。
固定handoffにある「正式不保持は行っていない」は当時の記録として保存し、今回の正式判断を本ファイルで追加する。

読む順序：本記録 → [provenance](provenance.json) → [固定判断handoff][handoff]。
個別の判断理由を確認する場合は、下記の固定資料を参照する。

## 承認された判断理由

以下は固定資料に記録された結果と、ユーザーが承認した判断の転記・整理である。
本作業で数学的な追加証明・独立認証・反例探索は行っていない。

1. **標準的な正の局所項のlayer分割（A+）では、目標上界の具体的な還元導出が得られた。**
   固定資料は、既知のcommutator・leakage評価、有限BCH打切り、Duhamel公式からR1-Pの目標上界を導く。
   [直接還元記録][reduction] §2–6、[既知定理対応][mapping] §3–6を判断根拠とする。
2. **この範囲では、独立した新しい構成原理や数学的保証を研究成果とする根拠が残っていない。**
   [不足補題の整理][lemmas] §1・§4と[固定handoff][handoff] §1を踏まえ、独立研究候補として保持しない。
3. **同じ低エネルギー情報を利用する通常4次PFにも既知の有限step保証がある。**
   R1-Pの成立だけでは元Hamiltonianの絶対E0に対する総資源優位を示せない。
   word定数、制御、synthesis、sampling、状態準備・情報取得の費用も残る。[baseline比較][baseline] §1–3。
4. **4軌道・2電子の追加検証は実施しない。**
   現在の独立性判断を変える見込みが乏しいという承認済み判断に従う。[固定handoff][handoff] §1 Q5・§3。
   元のT0検証案を今後の実行承認として扱わない。

ここでのA+は、正の局所項をlayersへ振り分ける標準grouping、または固定資料で明記された
正のrefinementと**同じJのnorm会計**を満たす範囲である。
任意の相殺fragmentや、sector圧縮後だけのPSDに、この還元結果を自動的に拡張しない。
今回、A+を元のT0正本や科学契約へ追加する変更も行わない。

## 判断の限界

今回承認されたのは、**現時点の証拠に基づいてR1-Pを独立研究候補から外す判断**である。
次の主張は含まない。

- 任意fragment分割におけるR1-Pの成立・不成立。
- 外挿PF一般の低エネルギー保証問題の解決。
- 新しい保証が存在しないという一般的な不可能性。
- 外挿PFが通常4次PFより常に高コストであること。
- 詳細科学レビューによる数学的証明の独立認証。

したがって、固定資料の予備還元確認を独立した詳細科学レビューの完了へ格上げしない。
条件外の未確認事項を、新しい研究候補として自動保持することもない。

## 将来の再検討条件

**R1-Pと実質的に異なる未解決の数学的問題が具体化された場合に限り、再検討を提案できる。**
例えば、既存定理へ還元できないHamiltonian分割クラスを合法な入力・局所性・Jの会計とともに明確化できた場合、
または、同等条件の強いbaselineに対する独立した保証・総費用差が示された場合である。

単に既存のR1-Pの名称、fragment、係数、定数を変えるだけでは再開条件を満たさない。
これらの条件は将来の提案を判断する基準であり、今回その証拠を探す指示ではない。
新しい証拠が得られても自動再開せず、GPT／ユーザーが採否と範囲を判断する。
Codexは別途承認された作業範囲を受けてから実施する。

## 保全と今回の実施範囲

今回の変更は、本判断記録と[provenance](provenance.json)の新規追加だけである。
固定判断資料、元の定式化、過去のSOURCE・provenance・handoff・判断記録を上書きしない。

- J1は[既存正式記録][j1]の `PAUSED_PENDING_NEW_MECHANISM` を維持する。
- Q1は[既存正式記録][q1]の `PAUSED_PENDING_NEW_LEVEL_INSERTION_RULE` を維持する。
- 第一・第二研究、PR Track A/B、その他のSOURCE・raw結果・grant・承認・固定科学契約・STOP・PAUSEを維持する。
- D1を維持し、block-encoding・qubitizationを研究の中心へ移行しない。
- D2を維持し、元の有限基底電子Hamiltonianの絶対E0、scalar、一体項、残余相互作用、誤差を省略しない。
- 新規科学計算、solver、simulation、科学用記号計算、回路build・compile、追加証明、反例探索、4軌道・2電子検証は実施しない。
- 別の外挿PF、新アルゴリズム候補、別gap、次の研究課題の探索や、探索戦略の変更を開始しない。

Git・文書・JSONの静的確認とhash照合だけを実施する。既存worktreeのHEAD・branch・status・staged／unstaged diffを比較する。
未追跡・ignoredファイルの内容や共有環境全体を網羅する保全証明ではなく、監査範囲はprovenanceに明記する。
既存の固定資源契約は変更しない。

## 公開・担当・停止

Repository：`HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae`。
branch：`qc-r1-nonretention-decision-20261017`。親commitは判断根拠の固定commit `b39a54443e6b4780295bc0499ac8f8d7b10b083f`。
新規2ファイルだけを明示的にstageし、通常commit・non-force pushを行う。
remote SHA、独立した空bare repositoryへのfetch、Git blob、bytes、SHA-256、commit固定rawを照合する。
provenanceはmanifestから自己除外し、公開commitのSHAと2ファイルの照合結果は最終handoffで報告する。

**Mandatory STOP：正式判断記録の公開・照合後に停止する。追加作業は不要。**
現時点で次の研究選定・探索・科学計算・追加科学レビューへの実行承認はない。
将来の再検討提案の採否はGPT／ユーザーが判断し、Codexは新しい指示を待つ。

[handoff]: https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/b39a54443e6b4780295bc0499ac8f8d7b10b083f/docs/research_exploration/r1_known_theorem_reduction_20261017/r1_decision_handoff.md
[reduction]: https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/b39a54443e6b4780295bc0499ac8f8d7b10b083f/docs/research_exploration/r1_known_theorem_reduction_20261017/r1_direct_reduction_check.md
[mapping]: https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/b39a54443e6b4780295bc0499ac8f8d7b10b083f/docs/research_exploration/r1_known_theorem_reduction_20261017/r1_known_theorem_mapping.md
[lemmas]: https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/b39a54443e6b4780295bc0499ac8f8d7b10b083f/docs/research_exploration/r1_known_theorem_reduction_20261017/r1_missing_lemmas.md
[baseline]: https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/b39a54443e6b4780295bc0499ac8f8d7b10b083f/docs/research_exploration/r1_known_theorem_reduction_20261017/r1_baseline_and_scope.md
[j1]: https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/95be62395d3740db39b6830c68f4fd1e25f595ee/docs/research_exploration/p1star_j1_pause_decision_20261017/research_decision_record.md
[q1]: https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/17cf4073094c713257d6eabadb440d6d973a9229/docs/research_exploration/q1_pause_decision_20261017/research_decision_record.md
