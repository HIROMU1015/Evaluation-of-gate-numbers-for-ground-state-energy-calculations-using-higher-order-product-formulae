# 未解決問題からの研究課題設計：判断用handoff

2026-10-17 JST。**保持する数学的研究課題案は1件（Q1）。新しいアルゴリズム又は独立原理の成立は0件。**
Q1の正式採択・中心claim・計算承認・旧研究状態の変更は行っていない。
一次文献11件の必要箇所、著者公開source3ファイル、固定した既存研究記録を調べた限定結果である。

## 1. ① 具体的に何が未解決か

**inhomogeneousなRichardson–Gaudin pairing familyで、係数だけから任意入力に使えるcoherentな全基底変換とenergy評価を、
指数個のstate／root setを列挙せず生成する構成。**
対象は[定式化](research_problem.md) (Q1)–(Q2)の明示familyとactive subset。
extensive fillingを含め、未知のgap・branch・rapidities・groundを無料入力にしない。

時間発展の実装そのもの、Bethe stateの表現又は個別準備が未解決、という意味ではない。
既知PF、ABCs、明示deterministic準備、条件付きRG parent準備が強い対照として存在する。
文献に明示される非摂動域のparent gap・classical charge解法の未閉鎖と、Q1の全入力の構成契約も区別する。
「既知法が見つからなかったから新規」とは認定していない。
今回確認した構成はこの追加契約を閉じていないが、全世界での不存在・優先権は主張しない。

## 2. ② 解決できれば何が新しくなるか

目指す成果は、既知\(W e^{-itD}W^\dagger\)という枠ではなく、
**levelを追加するunitaryを係数とcompactなlabelから生成する新しい再帰則**である。
既知のoverlap式や準備を各stateへ個別に適用する方法を越え、coherence、orthogonality、work返却、
有限精度operator残差と再帰費用を同時に保証することが必要。

目標命題は

\[
\|h_I-W_ID_IW_I^\dagger\|\le\zeta,
\qquad\text{全生成費用}\le\operatorname{poly}(L,b,\log(1/\zeta))
\]

と、branchを指数展開しない(Q7)のshared recurrence。
成功すれば、限定familyのcontrolled evolutionをpolylog時間・精度依存へ接続し得る。
これは既存PFの次数変更、既知gateの連結又は数値parameter最適化の提案ではない。
**生成則もcomplexity定理もまだ得ていない。** 全既知法に対する下界又は資源優位を示したとも扱わない。

化学との適用範囲には重要な限界がある。RG模型は一般のCoulomb Hの代わりではない。
まず厳密pairing模型／fragmentの構成課題であり、元有限基底電子Hのscalar、一体項、blocked sector、Rと誤差・費用を保持する。
絶対E0のstate準備・最低branchの識別・読出しをこの課題の成功だけで解決済みにはしない。

## 3. ③ 最初に何を数学的に検証するか

**4対軌道・2 pairsで、3＋3次元の親子作用に対する一つのlevel挿入則を紙上で書けるか。**
最初に確認するのは、(Q5)のself-pair scalarとoff-diagonal form factorを保持したまま、
全columnの個別QR／全root一覧を入力しない可逆な生成ができるかである。
その後に2 inputのsuperposition、garbage返却、controlled scalarを照合する案とした。

6次元対角化ができただけでは一般Lの成果としない。
全mの処理がsharedな多項式再帰になるか、conditioning・bit長・operator誤差が閉じるかが次の定理の核心。
詳細は[最小紙上検証案](minimal_paper_checks.md)。**この次段階の導出は今回実施していない。**

## 4. 判断事項と担当

1. **GPT／ユーザー**：明示pairing family／fragmentという限定範囲と、全入力coherentな生成補題という課題が、独立構成原理を目指す研究として適切か判断する。
   模型Hを一般分子Hと取り違えた採択はしない。
2. **GPT／ユーザー**：次に(Q5)の4-level例と挿入則に限る紙上検討を実施するか、又はQ1を保持しないか判断する。
   L02の既知構成の移送、既存可解代数研究との実質的重複が閉じるなら、独立性を撤回する。
3. **Codex（新しい明示指示がある場合のみ）**：承認された範囲の最小紙上導出を担当する。必要な科学計算が出た場合は実行せず、新しい科学契約と承認事項を提案する。

現依頼で残る作業は資料のcommit・通常push・公開照合だけであり、その後は停止する。
Q1の採択、詳細科学レビュー、新規計算・solver・simulation・実装・benchmark、追加探索へ自動移行しない。

## 5. 成果物とSOURCE

読む順序は以下。

1. 本handoff：1件の課題と3つの回答、適用限界、判断事項。
2. [研究問題](research_problem.md)：Hamiltonian／access、目標定理、level追加の具体的な構成対象、失敗条件。
3. [未解決問題調査](unresolved_problem_survey.md)、[先行研究比較](prior_art_comparison.md)：既知到達点、4区分、過去系列との重複と不保持方向。
4. [最小検証案](minimal_paper_checks.md)：最初の命題と反例・失敗判別。
5. [SOURCE registry](source_registry.json)、[static audit](static_audit.json)、[provenance](provenance.json)。

Repository: `HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae`

新規branch: `qc-open-problem-research-design-20261017`。
起点verified snapshot: `c23e9bc6028c52761e6220b91e2d1e1bd8b3ceaf`。
重要固定参照は`b5c49323957f1bfa2a24cb2786a0ebd1f3932925`、`813fd44bfd70f9bc4266e35cc8e4dd28037dedce`、
`95be62395d3740db39b6830c68f4fd1e25f595ee`。P1～P8と旧障害記録も固定commitで参照した。
sourceのorigin/result commitとverified snapshot commitは、同じblobでも別fieldに保持する。
manifestは自身を除外し、自身を含む公開commit SHAを文書へ埋め込む循環を作らない。
最終40文字SHAとGitHub固定リンクは、remote・独立fetch・blob・bytes・SHA-256照合後のchatに示す。
公開前provenanceの状態記録は歴史として保持する。

## 6. 保全と停止

新規8ファイルだけを追加する。元SOURCE、結果、grant、科学契約、承認、STOP・PAUSEは変更しない。
J1の`PAUSED_PENDING_NEW_MECHANISM`、NA/NBとcollisionの結論、第一・第二研究、PR Track A/Bの状態を保全する。
PRおよび著者sourceはread-onlyであり、他repositoryへ変更・commit・pushしていない。

新規科学計算、solver、数値最適化、simulation、科学実装、回路compile、新規benchmark、保存科学値再集計は0件。
記載数式は概念的仕様・既知関係・短い紙上整理であり、Q1の新しい正しさ／効率性証明ではない。
D1中心方向を変更せず、D2の元Hを保持する。共有環境・他ユーザーに影響する操作も行っていない。

**Mandatory STOP：資料公開・照合後に停止。**
