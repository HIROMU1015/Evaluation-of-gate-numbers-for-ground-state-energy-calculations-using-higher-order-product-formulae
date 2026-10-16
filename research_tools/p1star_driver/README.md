# P1STAR-A-v1 driver — 人工検証済み技術基盤

このpackageは、既存 `p1star_foundation` を変更せず再利用する。今回許可された実行は人工問題と既知恒等式の技術テストのみ。**P1*の科学実行、固定factorの適格性判定、固定12 segment展開は未実施・未承認。**

読む順序：

1. [技術判定](../../docs/research_exploration/p1star_science_driver_20261017/driver_readiness_report.md)
2. [資源追補](../../docs/research_exploration/p1star_science_driver_20261017/resource_policy_addendum.md)
3. 本READMEと [test結果](../../docs/research_exploration/p1star_science_driver_20261017/technical_test_results.json)
4. [provenance](../../docs/research_exploration/p1star_science_driver_20261017/provenance.json)

## 構成とexact性

| Module | 処理 |
|---|---|
| `operators.py` | Gaussian rational係数、CAR電子正規形×対称Weyl oscillator基底、η次数・parameter monomial、積・交換子・形式log |
| `eligibility.py` | 2個のHermitian一体factorの非可換性、平方和targetの非退化、full Fockの二体項、指定Nでのscalar+全一体作用のexact span判定 |
| `conditions.py` | full Fock residualを全basisで照合し、実部・虚部を別の有理多項式等式へ変換、box付きexact solver、exact witness再読込・代入 |
| `screen.py` | adjacent merging、literal四pulse group commutator・single-factor quadrature loop・そのliteral連結、CAR選択の主張と事後整理の記録 |
| `pipeline.py` | eligibility→formal log→conditions→1 solver call→witness再照合→bounded screen。失敗時INCONCLUSIVE、retryなし |
| `practical.py`, `_worker.py` | 単一計算worker、CPU affinity、AS制限、wall/RSS/output監視、異常停止 |
| `authorization.py`, `science.py` | 別途承認とfreeze hashの確認、承認前の科学input読込拒否、1回限りのattempt journal |
| `science_spec.py` | 承認後だけlazy loadする、元契約とのliteral入力照合。今回importも実行もしていない |
| `fixtures.py`, `tests/`, `technical_tests.py` | 小規模人工問題、既知恒等式、技術test runner |

係数は `int` / `Fraction` / `QComplex` のみ。float、Python complex、近似ゼロ判定を使わない。電子はcreation昇順、annihilation降順、busはdistinct X/P wordを対称化したWeyl基底。bus有限cutoffを使わない。degree、body数、tensor成分を別fieldに保持する。relation scopeはCAR・CCR・特定入力factor・sectorを区別し、sector tag付き式はfull Fock条件へ入れない。sector内のrank判定に使うexact entriesは一時メモリ内だけであり、state simulationや真値oracleではない。

形式logは標準の有限次数seriesで構成する。chronological listの各segmentについて `exp(-i η x_j G_j)` を左から掛け、`U_last ... U_first` を作る。ηの次数を積のたびに切り、`V=U-I` に対して `V - V²/2 + V³/3 - V⁴/4` を指定次数まで使う。新たなMagnus定理・誤差保証の証明ではない。小さい2生成元の標準BCH式（4次まで）、同一生成元、central CCR rectangleを別表現と照合する。

Z3 **4.13.3.0**、QF_NRA/NLSatは既存lockでmapped library hashとversionを検査する。実12変数を扱う能力は継承した人工12変数testで確認する。数学変数はreal、係数入力はQ(i)を実虚に分解したexact rational。solverのalgebraic witnessはSMT-LIB `root-obj` で保持し、decimal approximationへ変換しない。出力sexpr中の `1.0` もZ3のexact rational numeralでありPython floatではない。

SATは同じbackendのexact substitutionを基盤側とdriver側で再照合する。独立solver・独立証明器の検証ではない。UNSATは記録したSMT2/hash、等式、全閉boxに対するtrusted solver結論であり、独立検証済み証明書ではない。[Z3開発者のProgramming Z3](https://z3prover.github.io/papers/programmingz3.html#sec-nlsat) を背景資料とし、利用可能性の根拠は実際のlock・source・人工testに置く。

## 人工testだけを実行する方法

CPython3.11.1、SymPy1.13.3、mpmath1.3.0、z3-solver4.13.3.0を、既存[requirements](../p1star_foundation/requirements.lock)と[environment lock](../p1star_foundation/environment_lock.json)に従う隔離環境で用意する。新driverの [environment_lock.json](environment_lock.json) は今回の技術snapshot。実行時に参照したvenvの所在はprovenanceに記録し、repositoryにvenvやbinaryを追加していない。

Repository rootで、`P1STAR_PYTHON` を当該隔離環境のabsolute interpreter pathに設定してから実行する。

```bash
PYTHONPATH=research_tools PYTHONDONTWRITEBYTECODE=1 SYMPY_GROUND_TYPES=python \
OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 \
timeout 150 "$P1STAR_PYTHON" -m p1star_driver.technical_tests /tmp/p1star-artificial-tests.json
```

既存41 testsと新driver testsを順次実行し、scalar audit、source hash、runtime identityだけを保存する。P1*のfactorや固定wordをtest fixtureとして使わない。人工target overrideは `purpose=ARTIFICIAL_ONLY` に限定し、science入力のliteral validatorはoverrideを拒否する。テスト出力のlabelは人工fixtureに対するものであり、P1*の結果ではない。

## 将来のscience入口 — 今回は実行禁止

`python -m p1star_driver.science --approved-plan <plan.json>` が明示入口である。**今回この入口・science worker branch・fixed-input loaderは実行していない。** Importに科学処理はない。通常testは共有承認ゲートで拒否を確認するだけであり、science入口を呼ばない。

次回、ユーザーがP1STAR-A-v1 Phase Bを別途明示承認した後、operatorが以下をreview・freezeする。

1. 元契約そのままのJSON入力。schema、matrices、particles、order、primitives、word、boxesが `science_spec.py` のliteral仕様と厳密一致し、整数をfloatやboolで代用しない。入力bytes/SHA-256を固定する。今回はこのinput JSONを作成していない。
2. 科学設定をすべて明記する：`wall_seconds`, `rss_bytes`, `address_space_bytes`, `output_bytes`（512 bytes〜20 MiB）, `terms`（≤200000）, `trace_events`, `solver_timeout_ms`、任意の `solver_rlimit`。toy設定を承認済み値としない。各値の意味と監視の欠落を追補とともに承認する。
3. `collect_runtime()` のraw JSON環境snapshotを保存し、bytes/SHA-256を固定する。CPython/libpython・package files・mapped Z3/CLIを含む。science preflightはこのrecordと現環境を完全照合する。再構築環境ではpath等も変わり得るため、既存lockを改変せず、新しい実行snapshotをreviewする。
4. code hashは `authorization.code_digest()` の規則（両packageの `.py`/`.json`、tests directoryを除外、相対pathとSHA-256のcanonical list）で固定する。公開commit、Git blobs、元契約SHA-256、追補SHA-256もfreezeする。code hashは科学SOURCEや今回の承認を変更する機構ではない。
5. planは `settings`, `input_path`, `input_sha256`, `environment_record`, `attempt_directory`, `approval` を含む。attempt directoryは全実行で共有する永続的なlock/journal directoryとし、他のworktreeへ勝手に作らない。operatorがその所在を承認記録に残す。
6. approvalは `explicit_user_approval=true`, `action=P1STAR-A-v1-PHASE-B-ONE-SHOT`, 実際の `approval_reference`, unique `run_id`, `attempt=1`, `allow_retry=false` と、`input_sha256`, `settings_sha256`, `code_sha256`, `environment_sha256`, `contract_sha256`, `resource_addendum_sha256` を持つ。settings hashはsort_keys+compact separatorsのUTF-8 JSON。本taskに有効なscience receiptは存在しない。

receiptは人が確認した明示承認の記録であり、署名付きaccess controlではない。JSONのtrueを書くだけで承認を捏造してはいけない。low-level `run_pipeline` は数学APIであり、approval sandboxではない。実科学は必ず承認済みの監視付き入口を使う。

Controllerはplanを確認し、workerも再確認する。plan bytes hashも照合する。入力を開く前に全bindingとruntimeを照合し、attempt markerをO_EXCLで作る。markerがある場合はretryしない。読込・hash不一致・backend異常でもmarkerを消して救済しない。新たなattemptの可否は別のユーザー判断である。

科学実行の最初は因子適格性gate。gateが通らなければINCONCLUSIVEとして停止する。通った場合に限り固定ansatzの展開・全residual等式・1回のexact求解へ進む。結果後に次のjobは起動しない。full Fockでの不成立をsector限定構成一般の不可能性へ拡張しない。

## 解釈と限界

`NO_SOLUTION_IN_FIXED_ANSATZ` は上記trusted exact UNSATの範囲だけ。`KNOWN_CONSTRUCTION_ONLY` はexact SATかつliteral known correspondenceがある場合。SATでscreen不一致なら `formal_consistent=true` と `INCONCLUSIVE` を併記し、独立した科学判断を待つ。`NONTRIVIAL_FORMAL_CANDIDATE` を自動出力しない。

CAR parameter-selectionの自己申告をscreenが独立に証明することはない。core constraintsを指す説明がない場合、`POSTHOC_NORMAL_ORDERING_ONLY` と明記する。claimがある場合もconstraint IDs・説明・stageを保存し、`independently_validated=false` を維持する。科学レビューの開始・新規性認定は別途承認が必要。

小さな人工4-pulseでもtraceが多数生成される。実P1*の12-pulseが現実的な運用枠で完了するかは未確認で、項数・trace・wall・メモリで停止し得る。効率・資源優位・誤差保証・科学的成立性はこの技術基盤のPASSからは分からない。

**Mandatory STOP：この技術成果物の公開・照合で終了。科学実行は別途明示承認まで開始しない。**
