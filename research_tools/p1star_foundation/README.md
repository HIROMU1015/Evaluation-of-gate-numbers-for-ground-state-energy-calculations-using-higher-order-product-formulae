# P1* technical foundation

汎用exact演算・人工問題の技術テスト用package。**判定はNOT_READY。P1*の科学入力、因子適格性checker、Magnus／formal-log生成、科学用方程式生成、Phase B driverは含まない。** 科学計算の実行には別途明示承認が必要。

成果と限界は[技術的準備判定](../../docs/research_exploration/p1star_technical_foundation_20261017/technical_readiness_report.md)、実測の技術テスト結果は[technical_test_results.json](../../docs/research_exploration/p1star_technical_foundation_20261017/technical_test_results.json)を参照する。

## 隔離環境と人工テストの再現

repository rootから実行する。以下の出力先は新規fileとし、保存済み結果を上書きしない。既存venvは変更しない。

```bash
/home/abe/.pyenv/versions/3.11.1/bin/python -m venv /tmp/p1star-tech-env
/tmp/p1star-tech-env/bin/python -m pip install --only-binary=:all: --require-hashes -r research_tools/p1star_foundation/requirements.lock
PYTHONDONTWRITEBYTECODE=1 SYMPY_GROUND_TYPES=python PYTHONPATH=research_tools /tmp/p1star-tech-env/bin/python -m p1star_foundation.environment
PYTHONDONTWRITEBYTECODE=1 SYMPY_GROUND_TYPES=python OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=research_tools /tmp/p1star-tech-env/bin/python -m p1star_foundation.technical_suite --output /tmp/p1star-new-technical-results.json
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=research_tools /tmp/p1star-tech-env/bin/python -m p1star_foundation.guards
```

環境はLinux x86_64、CPython 3.11.1、Z3-solver 4.13.3.0、SymPy 1.13.3、mpmath 1.3.0へ固定。requirements.lockは取得wheelのSHA-256を固定し、[environment_lock.json](environment_lock.json)は実際にloadしたlibz3.so、CLI binary、Python binary／libpythonとpackage source inventoryのhashを記録する。環境確認moduleと各solver callはZ3のversion・mapped library hash・runtime package versionの相違を拒否する。ローカルpathの移動自体は拒否理由にしない。

上の再現手順は**人工技術テスト**である。今回保存したテストはさらに外側からtimeout 60秒、CPU affinity 0、RLIMIT_AS 1 GiB、core dump無効の条件で実行した。小さいOS probe workerには128 MiBのvirtual-address limit等を使用した。これらをPhase Bの16 GiB RAM保証と読み替えない。再構築した環境の全system library、kernel、全Python sourceの一致まで起動時に保証するものでもない。

## APIと管理責任

| Module | 提供する部品 | 使用上の境界 |
| --- | --- | --- |
| `exact.py` | Fractionの対によるQ(i)、flatな疎多項式、TermLedger／TermMap | float／Python complexを拒否。mapの所有者はcontext manager又はcloseで明示解放する |
| `algebra.py` | CAR normal order、CCRのX-before-P、Weyl対称basis、tensor basis・formal grade・body数・由来 | 4-mode等の科学入力を内蔵しない。変換に失敗したTensorExpressionは閉鎖し、部分結果を返さない |
| `solver.py` | exact real polynomial／closed boxの単一QF_NRA呼出し、SAT／UNSAT／UNKNOWN、exact witness | SMT ASTはexactなint／Fraction／real-algebraic値から構築する。すでにfloatから作られたASTの履歴は検出できない |
| `environment.py` | インストール／load済みbinary・sourceのidentity記録とbackend照合 | package inventoryは観測記録。再構築後の全inventoryを自動で同一と判定しない |
| `guards.py` | 所有map項数、集約出力byte、job lock、monotonic deadline、read-only readiness | 専用cgroupを作らない。`require_phase_b_ready()`は現在必ず拒否する |
| `_probe_worker.py` | allowlistしたCPU／memory／wall／outputの人工worker | 任意command、科学入力又はPhase B実行の入口ではない |
| `technical_suite.py` | unittestと既知人工問題のJSON記録 | 科学入力を受け取るoptionなし。保存先は排他的な新規file |

Fermionの規約はcreation index昇順、annihilation index降順。busの比較basisは各X/P個数に対する全distinct wordの平均で定義するWeyl対称basis。有限oscillator行列を使わない。電子とbusを別のtensor keyにし、η次数、parameter exponent、電子body数を保持する。number-changing monomialのbody数はNoneとし、number-conservingなk-bodyへ誤分類しない。

`Scope.CAR`、`CCR`、`FIXED_FACTOR_SPECIFIC`、`SECTOR_SPECIFIC`は別のタグである。sectorタグを持つ由来のfull Fock認定は拒否する。factor固有・sector固有の関係を実際に発見・適用する機能は未実装で、今回のテストはタグの分離だけを検査する。inputごとのoriginと変換ruleをtraceへ残すが、これはソフトウェア上の由来であり、P1*のCAR依存制御選択規則を示す科学的成果ではない。

SAT witnessは有理数の分子・分母又はSMTのexact `root-obj`式で保持する。元条件・boxへのexact代入確認は同じZ3を信頼する。UNSATはtrusted solver conclusionであり、独立証明書の検証成功を主張しない。timeout／resource-limit／unknownはUNSATにしない。

TermLedgerが厳密に制御するのは、同一ledgerへ登録されたTermMapの**保持entry総数**である。入力tuple、再帰stack、Python一時object、trace metadata、Z3内部のpolynomial／projection／AST、SMT serializationなどは包括的に数えていない。別ledgerを作って総予算を分割することもPhase Bでは許されない。管理範囲を狭める契約変更を勝手に行わず、現状では科学jobを開かない。

OutputBudgetはそのownerを通るfileへのwrite合計を事前に制限する。直接write、native libraryの出力、file以外の蓄積を包括的に制限しない。SingleJobも同じlock pathを使うlauncher同士の制御であり、ホスト全体の排他ではない。技術probeのRLIMIT_AS／NPROC、affinity、外部killはchildだけへ適用し、他のprocessやcgroupを変更しない。

**Mandatory STOP：実装・技術テスト・公開照合で終了。科学計算、科学レビュー、正式採択へ自動進行しない。**
