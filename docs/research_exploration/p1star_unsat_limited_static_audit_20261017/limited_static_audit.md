# P1* Phase B UNSAT：限定静的監査

2026-10-17 JST。対象snapshotは **9555517933596615064713e1988849835453eeb8**。読む順序：本書 → [静的照合記録](static_checks.json) → [provenance](provenance.json)。既存の科学結果・source・契約を変更せず、solver・科学処理・科学テストは実行していない。

**結論：固定ansatzに対する、保存された438条件と閉boxについてのZ3依存UNSATを支持する。限定したsource読解と保存データ照合では、それを撤回すべき具体的な条件欠落・追加制約・符号／演算子順序の不整合は見つからなかった。ただし、438条件の導出の独立な再検証や、数学的な不可能性の独立証明を完了したという結論ではない。**

## 4試行と技術修正

各planの実bytes、入力hash、settings hash、各時点のsourceから計算したcode hashを照合した。科学入力SHA-256は全試行で `eb6581e351cabae863eab4bb40ef659a91655c25685fdd5a0fb988ab9a2521a5`。固定4 modes・2因子・K全体・N=2識別用・full Fock主判定・共通bus・12 segment・12実変数の閉box・4次展開は維持されている。[試行記録][campaign]、[回復追補][recovery]を参照。

| 試行／source commit | 変更と静的判断 | 記録された終了 |
| --- | --- | --- |
| 1 / `d1d57110238d2ea283fb6f49bfcc519d2e8ef11e` | freeze時のdriver。出力中断を不整合認定へ変換していない。 | OUTPUT_LIMIT / INCONCLUSIVE |
| 2 / `0aebf2df13de19286b07030626348842e19798ee` | pure CAR積とWeyl積を順序付きキーでcache。miss時は元foundation規則、hit時は同じexact係数を利用する。η・振幅・factor／sectorの追加関係をキーや値へ混入させない。重複trace生成を削減。 | managed terms 200,000 / INCONCLUSIVE |
| 3 / `82a55a4fbec165e681e8ea19def5f785dca67301` | 管理term上限を **200,000→2,000,000** へ変更。これは資源契約の変更であり「元の予算を維持」とは言えない。閾値による微小項除去や係数の変更ではなく、枯渇時は例外／INCONCLUSIVE。最新の修正・再開承認と追補を根拠にした履歴がある。 | operator SIGTERM / ABNORMAL_EXIT / INCONCLUSIVE |
| 4 / `227d1541b98aa48147cf92cc91856da5cb87f1e6` | 右辺をη次数でbucket化し、旧sourceでも次数合計>4として捨てていた組を列挙前に除外。η次数は非負・加算的で、CAR／CCR縮約はη次数を減らさない設計。bus次数・body数による追加打切りはない。progress出力は資源metadataのみ。 | UNSAT / NO_SOLUTION_IN_FIXED_ANSATZ |

原科学契約の文書そのものは固定commit `1771564d919837e2440a9fcb175ac054284a729c` と同一bytes。foundation、`conditions.py`、`eligibility.py`、`science_spec.py`も元driverから不変。最終管理term peakは465,502であり、20万以内だったとは報告しない。最初の3試行はUNSATの証拠に数えず、出力制限で失われた試行1の内部solver呼出し有無も断定しない。

## 438条件の契約対応

| 確認点 | sourceと保存物から確認できた範囲 |
| --- | --- |
| 入力・積の向き | [固定入力][input]と[validator][spec]の行列・word・boxが契約と一致。`operators.py`の各segmentは `−iηx_jG_j`、左から `exp(h_j) * U` を掛け、`U12…U1` とする。 |
| 4次formal-log | [formal_log][operators]は各指数を `h^n/n!`、続いて `V=U−I` の `Σ(-1)^(n+1)V^n/n` を4次まで処理。科学契約が許す同値なformal-log方式。有限ηやbus norm収束は判定していない。 |
| target・符号 | [pipeline][pipeline]は `target=−iη²(L1²+L2²)` を作り、[Conditions][conditions]は `actual−target` の残差を判定。Kの一体成分も含めており、二体部分だけへの置換・global phase／cleanupの自由化はない。 |
| CAR／CCR | [algebra.py][algebra]は `aa†=δ−a†a`、同種交換の負符号、重複のnilpotency、creator昇順／annihilator降順、`PX=XP−i` を使用。busは異なるtensor factor、Weylは異なるX/P配列の平均。有限oscillator行列を使っていない。 |
| full Fock | 残差を `(η次数, CAR単項, Weyl単項)` ごとに全て集め、実部・虚部を別々に零化する経路。カテゴリは表示分類であり条件の選別には使わない。sectorタグは拒否。N=2のspan計算は入力gateのみで、係数条件へのsector縮約はない。 |
| 保存行の構造 | 438行のbasis＋実虚部キーが一意。各電子語は規定CAR順序、各係数はexact rational、振幅指数は12成分。η別は **20 / 54 / 108 / 256** 行、実部176・虚部262。保存monomial entriesは28,503。 |

カテゴリはbus非identity356、一体20、二体50、三体以上12。bus非identityにはその電子body数を問わず分類するので、列挙は排他的。非零scalar行は保存されていないが、sourceにscalarを除外するfilterはなく、ゼロ行だけを除く経路である。**この観察からscalar残差が数学的に零だったことを独立認定はしない。** 実虚部の分割や別basisで同じ多項式が現れる重複は、その保存同値条件を強める別の仮定ではない。

## 保存条件・SMT2・UNSATの証拠

stdlibだけのread-only検査でSMT2を構文解析し、`let` aliasを解決した。既存の加算・乗算の葉に書かれた係数と指数を列挙し、JSONの既存行と**行の多重集合**として比較した。新しい係数生成、多項式の展開・消去、方程式の求解は行っていない。

- **438等式すべて一致**。12個のReal宣言、各変数の `−1≤x_j≤1` の24制約、合計462 assertと1 check-satを確認。JSON→SMT2間の欠落・追加・係数符号の不一致はなかった。SMT内の `1.0` 等はexact Real numeralでありbinary floatではない。`set-info :status unknown` は出力時のmetadataであり、solverの返答ではない。
- [source registry][registry]の78ファイルを対象snapshotのbytes・Git blob・SHA-256と照合。4試行のcode hashも各履歴から再計算して一致。最終combined code SHA-256は `81e798e87630c645557a64b2dc8bae2b04cf60465a5159d8b15f81164d17b17b`。
- 既存runtime原結果をread-onlyで照合し、公表時に分離されたJSON・SMT2と同じ内容であること、traceのcount/hashとその他の元の結果fieldが公表summaryに対応することを確認。runtime原本は再公開しない。これはデータ同一性の照合であり、結果の数学的独立再検証ではない。

| artifact | bytes | SHA-256 |
| --- | ---: | --- |
| [coefficient_conditions.json][equations] | 1,660,955 | `5fb523ef2c39bb447783e779e6f04564a33a5bf585196c3b15caf0a2f4a2df9a` |
| [exact_solver_input.smt2][smt] | 2,532,283 | `1ad8745ce781e9b471028e7e6102b79f535a1dcdab2fa670439d12524ed4e8bf` |

[solver source][solver]は `SolverFor("QF_NRA")` に全等式と閉boxを渡し、SAT／UNSAT／UNKNOWNを区別する。保存[summary][summary]はZ3 **4.13.3.0**、UNSAT、`independent_certificate_verified=false`。同時に `exact_substitution_verified=false` なのはSAT witnessがないためで、UNSATの独立証明があるという意味ではない。環境snapshotはPython 3.11.1／SymPy 1.13.3を記録するが、今回それらの科学機能を起動していない。

## 残る限界とGPTへ戻す判断

1. **係数生成の独立性**：固定12 wordを別実装で再展開していない。438行が契約のformal-log残差そのものに完全一致すること、全符号やゼロ化が正しいことの数学的独立保証は未取得。保存80件の人工技術テストは補助証拠であり、同じfoundationを共有する比較もある。今回テストは再実行していない。
2. **traceの由来追跡**：cache missの正規化規則とhit集計は残るが、各振幅monomial・segment・formal-log積からの寄与を辿る完全な導出DAG／証明書ではない。公開物はtrace本文を省きcount/hashを保持する。元契約§5.6の由来追跡について完全な再生可能性まで満たすとは認定しない。これは係数誤りの発見ではなく、独立監査できる範囲の不足である。完全な由来監査を要求する場合は、別承認の範囲・必要性をGPT側で判断する。
3. **UNSATの独立性**：保存SMT2のデータ対応は確認したが、独立した証明書検証・別solver照合はない。現時点で使用できる表現は「固定word・factor・box・4次・full Fock条件についてのZ3依存の不整合結果」。数学的no-go定理とはしない。
4. **判断の境界**：この限定された否定結果をP1*の次の研究判断に用いる際、どの独立保証を要求するか、traceの不足をどう扱うかはGPT／ユーザーに戻す。P1*一般、別word／factor／次数／box、sector限定共同閉路の不存在へ拡張しない。資源上限の変更を隠して元予算内の結果とも呼ばない。

修正・再計算を要する具体的な誤りは本監査では検出していない。上記の保証不足を埋める作業は今回未承認であり実施しない。既存の結果、科学契約、authorization、STOP／PAUSEを維持する。**Mandatory STOP：監査資料の公開・独立照合後に停止。追加科学計算・詳細レビュー・科学的GO／正式採択へ進まない。**

[campaign]: https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/9555517933596615064713e1988849835453eeb8/docs/research_exploration/p1star_phase_b_execution_20261017/campaign_attempts.json
[recovery]: https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/9555517933596615064713e1988849835453eeb8/docs/research_exploration/p1star_phase_b_execution_20261017/resource_recovery_addendum.md
[input]: https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/9555517933596615064713e1988849835453eeb8/docs/research_exploration/p1star_phase_b_final_freeze_20261017/scientific_input.json
[spec]: https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/9555517933596615064713e1988849835453eeb8/research_tools/p1star_driver/science_spec.py
[operators]: https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/9555517933596615064713e1988849835453eeb8/research_tools/p1star_driver/operators.py#L170
[pipeline]: https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/9555517933596615064713e1988849835453eeb8/research_tools/p1star_driver/pipeline.py#L51
[conditions]: https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/9555517933596615064713e1988849835453eeb8/research_tools/p1star_driver/conditions.py#L20
[algebra]: https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/9555517933596615064713e1988849835453eeb8/research_tools/p1star_foundation/algebra.py
[registry]: https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/9555517933596615064713e1988849835453eeb8/docs/research_exploration/p1star_phase_b_execution_20261017/source_registry.json
[equations]: https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/9555517933596615064713e1988849835453eeb8/docs/research_exploration/p1star_phase_b_execution_20261017/coefficient_conditions.json
[smt]: https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/9555517933596615064713e1988849835453eeb8/docs/research_exploration/p1star_phase_b_execution_20261017/exact_solver_input.smt2
[solver]: https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/9555517933596615064713e1988849835453eeb8/research_tools/p1star_foundation/solver.py#L114
[summary]: https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/9555517933596615064713e1988849835453eeb8/docs/research_exploration/p1star_phase_b_execution_20261017/scientific_result_summary.json
