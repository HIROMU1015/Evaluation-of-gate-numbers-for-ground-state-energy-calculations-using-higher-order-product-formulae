# J1限定検証：判断用handoff

2026-10-17 JST。**CAR交換関係を1～3次条件を満たす実制御へ持ち上げることはできた。ただし、得たcellは既知gate＋echoへ還元される。J1固有の非還元な共同閉路が得られたわけではない。**

読む順序：本書 → [数学的導出](mathematical_feasibility_record.md) → [provenance](provenance.json)。参照正本はJ1 `dd36794069f2f8063d3eba6c7e3fcc989d9b0ceb`。本branchはこのcommitを親に持ち、過去の資料を上書きしない。

固定参照：[J1仮説](https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/dd36794069f2f8063d3eba6c7e3fcc989d9b0ceb/docs/research_exploration/p1star_joint_loop_principles_20261017/joint_loop_principle_hypotheses.md)、[元科学契約](https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/1771564d919837e2440a9fcb175ac054284a729c/docs/research_exploration/p1star_symbolic_preflight_20261017/symbolic_verification_contract_draft.md)、[UNSAT結果snapshot](https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/9555517933596615064713e1988849835453eeb8/docs/research_exploration/p1star_phase_b_execution_20261017/scientific_result_summary.json)、[3次障害の独立検証](https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/5110d347e1f032c9093430b3def13b3391602cdd/docs/research_exploration/p1star_cubic_obstruction_verification_20261017/independent_cubic_obstruction_verification.md)。本導出は過去の438条件やdriver出力を再利用して新cellの成立を推論したものではない。

## 得たものと得ていないもの

| 検証対象 | 結果 |
| --- | --- |
| 四軌道・許可Hermitian一体factor×共通X/Pでの有限実cell | 本記録に20-pulse列を明記。非Hermitian Eの直接指数化、無料二体oracle、補正操作なし。 |
| 1～3次formal log | \(\rho(\ell_1)=0,\ \rho(\ell_2)=-4iH_\diamond\otimes I,\ \rho(\ell_3)=0\)。全3次bus成分を確認。 |
| 比較代数での残余 | \(\ell_3=-2(Q_1+Q_2-Q_1^\dagger-Q_2^\dagger)\otimes X\neq0\)。full Fock CARで零になる。 |
| shuffle、Lie、Hermiticity | 実signed pulseの積から導出。面積と3次係数を独立に設定していない。 |
| 独立したJ1共同生成原理 | **未解決**。上のcellは**既知法への還元**に分類。診断条件を通ることだけでは独立性を認定できない。 |
| 明示した制御族の負の結果 | 同じ非零prefixで二つの完成blockを運ぶ族では、3次零化により2次信号も零。**限定的な不成立**で、一般J1のno-goではない。 |

※表中の数式は数学的導出本文と同じ記号を使う。今回の20-pulse列を新しい科学用入力・driverへ登録又は実行していない。

## 還元の具体的な理由

二つの可換hopping factorの4変位閉路Rを組み、交換側ごとに8-pulse block B1,B2を作れる。それぞれがfull Fockで既に

\[
\rho(B_j)=e^{-2i\eta^2H_j}\otimes I,
\quad H_2=-H_1,\quad \rho(B_2^{-1})=\rho(B_1)=B
\]

という完成したdouble-excitation gateである。$V=e^{-i\eta n_pX}$ として得たcellは

\[
U_J=(VB_1V^{-1})(V^{-1}B_2^{-1}V)
\]

だが、full Fockではexactに

\[
\rho(U_J)=(VBV^{-1})(V^{-1}BV)
\]

へ書き直せる。これは既知gateを反対向きに共役する汎用echoである。最初から同じB1を二度使えば、比較代数でも3次を零にできる。従って比較代数の残余がCARで消えたという事実は、J1固有性の十分条件ではない。

単に完成gateへCAR-null identityを足した例ではないが、それでも共同性の基準を満たさない。CARによる相殺が動作することと、CARが新しい生成規則に不可欠であることを分ける必要がある。

## 科学計算の要否を決める前に不足するもの

必要なのは、**完成gate＋汎用echoという説明に尽くされない、一つの未完了な目標生成cellの有限文法**である。そこでCAR交換対がどの2次・3次係数を拘束し、なぜ信号を残して全bus残余を消せるかを明示する必要がある。σを物理swapとみなす、任意のsignature係数を独立に割り当てる、という省略は許されない。

次の最小検証案は、その文法一つの紙上での実path化と還元確認である。現時点で科学計算を開始すべきだとは認定しない。今回の還元は全てのJ1構成の不可能性ではなく、高リスク・未証明だけを理由にJ1を取り下げる判断でもない。

4次以降、共同cell全体の有限時間bus帰還、一般の化学Hamiltonianへの拡張、新規性、費用優位は未確立。旧固定12 segment ansatzのUNSAT、科学契約、D1・D2、full Fockとsectorの区別、既存grant・STOPは維持した。新規科学計算・solver・科学用記号計算コードの作成／実行は0件。

**次の担当：GPT／ユーザーが、非還元な文法の追加検討を依頼するかと、その最小範囲を判断する。Codexは公開・remote SHA／blob／bytes／SHA-256照合後にMandatory STOPする。** 追加探索・科学計算・詳細レビュー・正式採択へ自動進行しない。
