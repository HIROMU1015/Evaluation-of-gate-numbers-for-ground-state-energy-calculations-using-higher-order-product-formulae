# R1-P：既知定理への還元確認handoff

2026-10-17 JST。Repository：`HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae`。
branch：`qc-r1-known-theorem-reduction-20261017`。
固定起点：[`f0da24896b346e59ce225d1c264dd04420e1276c`](https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/commit/f0da24896b346e59ce225d1c264dd04420e1276c)。
公開commit自身のSHAは循環参照を避け、最終チャットとGit履歴で報告する。

**予備判定：標準の正の局所項layer分割では直接還元。R1-Pの独立研究候補としての不保持を第一推奨とする。**
ただしT0の「layer」が任意の相殺fragmentまで含む読みには拡張しない。
分割条件の明確化が必要であり、元のSOURCEや科学条件を今回書き換えてはいない。
正式採択・正式不保持・正式PAUSEはいずれも行っていない。

読む順序：本書 → [定理対応](r1_known_theorem_mapping.md) →
[直接還元の導出D1–D10](r1_direct_reduction_check.md) →
[不足事項の整理](r1_missing_lemmas.md) → [通常4次PF比較](r1_baseline_and_scope.md) →
[SOURCE](source_registry.json)／[静的監査](static_audit.json)／[provenance](provenance.json)。

## 1. 最終質問への回答

### Q1：既存定理の直接的な帰結か

**正の局所項をlayersへ振り分ける標準の解釈では、はい。**
L09のTheorem S1／Eq.S41、M26 Theorem 3による共通有限BCH、Duhamel公式二回を組み合わせると、
正本の同じE'、同じr-domain、同じ二つの時間次数を持つR1-Pを導ける。
固定word・localityだけから選ぶ十分なC/C_0と、二nodeのtruncation／tail予算も明示した。
大きな保守的定数の存在を示す導出であり、実用性を示す値ではない。

正本T0には正の局所和とcommuting layersが記される一方、任意fragmentのpositive refinementとJの会計は別式で指定されていない。
標準groupingならその条件は満たされるが、任意相殺fragmentまで含む解釈には未確定部分が残る。
したがって「T0のあらゆる読み方で無条件に証明済み」とは報告しない。

### Q2：直接導けない部分にどの補題が不足するか

上記標準解釈では、**新しい接続補題を必須とする理由は残らなかった**。
全Dyson次数のrestricted chainを別々に抑える必要があるという見方は強すぎる。
二回のDuhamelで外側をunitaryのまま残し、既知の一挿入・二挿入tail上界でfinite-r剰余を閉じられる。

任意fragmentの読みで不足するのは、まずPSD局所分割と同じJの会計の確認。
これはSOURCE／定理適用の条件問題であり、今回それを新しい数学的候補へ変換しない。
その別classの成立・不成立を示す反例計算は行っていない。

### Q3：技術的な接続か、新しい保証の可能性か

固定二点外挿の保守的目標については、**既知証明の技術的接続として整理できる**。
紙面に同じR1-P式が見当たらないことは数学的新規性を意味しない。
既知作用・既知補題からの限定的な帰結であり、新原理やpriorityを主張しない。
L08 §1.7の一般的なlow-energy／average-case外挿問題全体を解決したとも言わない。

### Q4：通常4次PFと同じ情報でも差分が残るか

L09 Corollary S4のp=4は、同じlow-energy入力に対し、既知のfinite-step \(R^{-4}\) 保証を持つ。
R1-Pにはさらにcutoff二次項があり、その成立だけで通常4次PFより強い保証・低い総費用にならない。
外挿にはsigned weightの統計価格も残る。

word定数・control／synthesis・shot準備費は違うため、実費用の普遍的な負けやwinnerは認定しない。
ただし、T0で推薦した「同時保証の未確認」を独立した研究価値とする差分は、標準classでは今回の還元により弱まる。
新しい総費用ランキングは作っていない。

### Q5：4軌道・2電子の紙上検証へ進むべきか

**現時点では進まないことを第一推奨とする。**
標準classでは直接還元があり、小例で同じ相殺を再確認しても独立性の判断を改善しにくい。
R1-Pの成立を仮定した検証、別ansatz、一般次数拡張へ進む必要もない。

次はGPT／ユーザーが、(a) 標準groupingを正本の意図として確認しR1-Pを独立候補から外すか、
(b) 任意fragmentを意図したのなら条件とJの差分を先に明確にするかを判断する。
どちらも今回は提案で、正式研究状態の変更ではない。

## 2. 検証済み事項と限界

| 項目 | 今回の扱い |
| --- | --- |
| 共通leading係数とr^-2相殺 | 既知展開・共通打切りから確認 |
| 一側projector norm | cutoff外項を残して導出。両側normだけの結論ではない |
| cutoff・finite remainder・定数 | 同じE'とr-domainで、固定word依存の十分定数を提示 |
| sector | H_+の全energy射影で導き、最後に入力をsectorへ制限 |
| 実装oracle | projector、exact U、BCH係数は証明用。無料操作として仮定しない |
| 数学的独立性 | 標準classでは既知の帰結。任意fragment・全prior artのpriorityは未判定 |
| E0資源優位 | 未確立。state、eta、tail情報・全protocol費を保持 |
| 4 modes・2 electrons | **未実施**。新Hamiltonian／行列／具体例を生成していない |
| science／実装 | solver、科学用記号プログラム、simulation、build／compile、benchmarkは全て未実施 |

この文書は依頼された予備還元確認。GPT詳細科学レビューや新しい一般理論の探索を代行したものではない。
新しいPF／Richardson係数／ansatzは作っていない。

## 3. 次の担当と承認

- **GPT／ユーザー**：条件付き還元の射程と不保持推奨を判断する。元の「layer分割」の意味を確認する。
- **Codex**：今回の公開・照合で停止する。正式判断の記録、追加証明、4軌道例、詳細レビューは新しい指示の対象。
- **追加作業**：現時点で承認済みのものはない。不保持判断を採るなら4軌道検証は不要。

J1 `PAUSED_PENDING_NEW_MECHANISM`、Q1 `PAUSED_PENDING_NEW_LEVEL_INSERTION_RULE` を維持する。
第一・第二研究、PR Track A/B、既存SOURCE・raw・grant・authorization・固定科学契約・STOPも不変。

## 4. 公開と停止

成果物は5 Markdown＋SOURCE registry＋static audit＋provenanceの8件。
origin/result commitとverified snapshot commitを別fieldに保持し、provenanceはmanifestから自己除外する。
normal push後、remote SHA、独立空bare repo fetch、Git blob・bytes・SHA-256・commit固定rawを照合する。
最終観測は最終チャットで報告し、過去のSOURCEへ公開状態を遡及反映しない。

**Mandatory STOP：公開・照合後に停止。正式採択・正式不保持、追加数学検証、科学計算、実装、詳細レビュー、既存研究再開へ自動進行しない。**
