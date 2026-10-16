# P1* Phase B：実行環境binding記録

2026-10-17 JST。契約：**P1STAR-A-v1**。記録種別：**STATIC_ENVIRONMENT_BINDING_ONLY**。

**係数処理の部品をCPython 3.11.1／SymPy 1.13.3へbindする。ただし、exact実数判定backend、契約用checker、資源制限の実行経路が揃っていないため、Phase Bは実行不可（NOT_READY）。科学計算は未承認・未実施である。** この不足は仮説の不成立を意味しない。

## 1. 正本と今回の権限

正本はcommit **1771564d919837e2440a9fcb175ac054284a729c** の[実行前契約草案][contract]。本記録は環境・停止経路だけを補足し、正本を上書きしない。正本のbyte数は **24,542**、Git blobは **8697af1403c5f1603bd099655c0b0610b39fcf59**、SHA-256は **96f6b22768e2a92944259a44a550cb734cb6f789ee8ea5a9a66193a1994887d6**。固定commitのGit blob、worktree、GitHub raw取得bytesを照合した。

今回のユーザー指示が承認するのは、インストール状況、既存実装、公式documentの静的確認と、新規binding資料の保存・通常push・公開照合だけである。パッケージ導入、checker／launcherの作成、科学用import・試験問題の実行は行っていない。環境確認用のPythonは標準ライブラリのmetadata・ファイル・hash・Git監査に限定した。

**Phase Bの4分類は今回どれも実行結果として付与しない。** 以下のINCONCLUSIVEは将来の実行契約に対する停止規則である。今回のNOT_READYをNO_SOLUTIONへ読み替えない。

## 2. 静的に確認した環境と版

| 要素 | 確認した版・経路 | binding上の扱い |
| --- | --- | --- |
| Python | CPython **3.11.1**, GCC 11.4.0。`/home/abe/myproject/Evaluation_numGate_highorder/venv/bin/python` | 係数処理の指定interpreter。shellの`python`には依存しない |
| SymPy | **1.13.3**、同venvの`lib/python3.11/site-packages` | exact係数・多項式操作の部品として固定。契約全体の実行能力は未確認 |
| mpmath | **1.3.0** | 依存package。近似算術・零判定には使わない |
| NumPy／SciPy | **1.26.4／1.14.1** | インストール確認のみ。科学経路には採用しない |
| OpenFermion | **1.6.1** | CAR／CCR実装の静的比較対象。既定APIを契約checkerとして採用しない |
| psutil | **7.2.1** | 存在確認のみ。監視できてもhard memory limitにはならない |
| exact実数可解性backend | **NONE／version N/A／実行経路なし** | 実行を開かない。自動導入・別backendへの自動切替なし |
| OS | Linux **6.8.0-47-generic**, x86_64, glibc 2.35 | 現在の観測環境。専用job sandboxは未設定 |
| 資源管理tool | systemd **249.11-0ubuntu3.16**、GNU timeout **8.32**、prlimit／taskset **util-linux 2.37.2** | 実行file・version・manualのみ確認。制限付きjobは起動していない |

調査範囲は上記venv、pyenvの3.11.1／3.12.3、`~/.virtualenvs/PythonProject`、`/usr/bin/python3`（3.10.12）、存在するuser-site metadataと現在のPATH。venv以外の調査interpreterではSymPyを検出せず、調査したpackage metadataにz3-solver、cvc5、PySMT、Sage、python-flint、gmpy2を検出しなかった。PATHにもZ3、cvc5、Sage、Singular、QEPCAD、REDUCE、Wolfram実行fileを検出していない。**ホスト全域に存在しないという証明ではない。** ほかの未調査環境を実行可として扱わない。

版の根拠はmetadataだけにしなかった。公式[PyPI SymPy 1.13.3 metadata][pypi]が指定するwheelを取得し、archive SHA-256 **54612cf55a62755ee71824ce692986f23c88ffa77207b30c1368eda4a7060f73**を照合した。Gaussian rational、polynomial、inequalities、secondquant、boson、ground-typesの**6 source fileだけ**について、インストール済みbytesとの一致を確認した。wheelは展開実行・導入していない。distribution全体の完全性やimport成功を確認したものではない。

取得したGitHub `1.13.3` URLのsourceは上記6件中4件でwheel／ローカルとbytesが異なった。原因・tagのimmutable commit対応は未確認であり、これらをインストール版の同一性根拠には使わない。確認したローカルsourceとwheelを能力判断の根拠とし、両取得物のhashを[provenance.json](provenance.json)へ分けて保存した。`latest`のSymPy公式documentは取得時に1.14.0を表示したため、1.13.3の機能保証として代用していない。

## 3. 記号表現とexact算術のbinding

### 3.1 係数と多項式

将来の係数処理は**Python整数＋SymPy Rational、exactなI、明示したQQ_I係数domain**に限定する。ground typesは起動前に **`SYMPY_GROUND_TYPES=python`** と固定し、自動選択によるflint／gmpyへの切替を避ける。これは既存sourceの設定経路を読んだbindingで、今回importして有効化を試したものではない。

ローカル`gaussiandomains.py`の`GaussianRationalField`と公式wheelはQQ_Iを有理実部・虚部からなるexact domainとして定義している。`polytools.py`には明示domainのPoly、terms、domain変換、Groebner操作がある。一般説明は[公式domain document][sympy-domains]を参照し、インストール版の判断は上記wheelとのsource照合による。

将来はx1〜x12の順序を固定した可換多項式係数と、電子・busの非可換basis keyを分離して保持する。形式次数ηは別gradeとし、固定4次の意味を変えない。係数の零判定はexact domainで行い、`Float`、Python float／complex、`evalf`、mpmath、numerical rank／近似根／許容誤差を経由しない。実数判定への受渡しでは、実変数についてexactな実部・虚部の係数条件へ分離する方式を固定する。**今回、その係数条件や式は生成していない。**

多項式の整理部品があることと、契約のoperator係数が正しく得られることは別である。無制限の汎用expand／simplify／Groebnerへ渡すだけでは、正規形、項数上限、全実数可否の完了を確認できない。未対応domainへの暗黙変換や、不明な零判定はINCONCLUSIVEで停止する。

### 3.2 CAR／CCRの正規形

| 必要な機能 | 読んだ既存実装 | この契約への接続状態 |
| --- | --- | --- |
| CARによる電子normal order | OpenFermion `normal_ordered_ladder_term`に交換・縮約・重複fermion処理がある | index順はcreationも高index優先で、契約のcreation昇順と一致しない。exact係数・符号・full Fock規約へのadapterは未作成 |
| fermionのWick処理 | SymPy `physics.secondquant.wicks`／NO | 既存のFermi基準・index規約を契約の全粒子数CAR恒等式へ自動同一視しない。契約用接続は未確認 |
| oscillator CCR | SymPy `physics.quantum.boson`に交換子実装、OpenFermion `normal_ordered_quad_term`にquadratureの再配列実装がある | 契約が要求するX/PのWeyl対称basisへの変換・exactな係数経路は未接続 |
| 電子×busの共同basis、由来タグ | 調査対象のAPI単体では契約全体の実装を確認できない | CAR・factor固有・N=2専用関係とLie-word由来を分離するadapterが必要。未作成 |

OpenFermionの[再配列source][of-order]は規約確認用に読み、[係数source][of-coeff]の`_issmall`／`compress`等にtolerance処理があることを確認した。quadrature側には既定`hbar=1.0`とPython複素数を使う経路もある。**そのままのAPI呼出しをexactな証拠に採用しない。** SymPyの確認済み`wicks`には複数bosonの処理でNotImplementedErrorへ進む分岐もあり、fermionとbusの共同正規化が実装済みとはいえない。

使える手段は、上記既存CAR／CCR実装を参照しながら、exact係数に限定した契約用の明示的なrewrite・basis adapterを後に承認された範囲で実装すること。現時点では**部品の存在だけを確認**した。rewrite式の新規導出、normal formの生成、Weyl変換の試行、checker作成は行っていない。未接続のまま科学計算を開始しない。

## 4. 12実パラメータ＋boxのexact判定

**現在のbinding：判定backendなし。SymPyだけで契約全体を実行する経路は採用しない。**

SymPy 1.13.3のローカル`inequalities.py`には、対象の複数symbolを含む不等式でNotImplementedErrorとなる分岐がある。[公式の制限説明][sympy-ineq]とも対応する。solve／solveset／Groebnerの存在、単変数のexact root処理、有理解探索、数値最適化は、12変数の結合条件と閉box全体の実数可解性を必ず判定できる証拠ではない。特別な系についてexact不整合が示せる場合があることは否定しないが、**今回の固定系を扱う一般の完結経路は未確認**である。

不足する機能の候補として、Z3の**NLSat／QF_NRA**を静的に照合した。[公式Programming Z3 §6.5][z3-nlsat]は、実数上の量化子なし多項式算術に対するdecision procedureとして説明している。固定係数条件とboxをこのfragmentで扱う方式は適合し得る。ここでのfree real variablesの充足可能性は全実数assignmentを対象とし、有理数だけへの制限を入れない。[公式Python API][z3-api]にはexactなalgebraic number表現もある。

ただし、**Z3は検出できず、採用version・binary／library hash・in-process経路は未設定**。documentを読んだことはローカル利用可能性、30分内の完了、契約への正しい変換、証拠保存の確認ではない。今回導入せず、Z3以外を自動で探して走らせることもしない。

将来backendをbindする場合は、少なくとも以下を実行前に固定する。

1. exactなQF_NRA又は同等の実閉体判定を行う**一つのbackendと完全なversion**、取得物・実装・共有libraryのhash、使用API・非並列設定。
2. 全12変数がRealであり、元契約のbox端点をexactに含むこと。係数受渡し、分母処理、実虚分離に近似や未記録の除外条件がないこと。
3. 一つの条件集合の受渡し形式とhash。satなら最初の1例又は同時返却familyで止め、exact rational／real-algebraic表現を保持して元の条件へのexact代入を確認する経路。decimal表示だけを証拠にしない。
4. unsatなら、全実数boxに対するexact判定backendの結論、全入力、完全な設定と終了状態を保存する経路。unsat coreだけを独立した数学的certificateと呼ばない。独立検証可能なproof出力の可否は未確認であり、その有無とsolverへの信頼依存を明記する。
5. `unknown`、例外、予算超過、不完全な実数探索、exact witnessの再照合不能はINCONCLUSIVE。制限後に再求解しない。

現状ではこの入口が閉じている。**exact backendを埋める目的で、先に因子適格性、展開、方程式生成を始めない。**

## 5. 上限と実行経路のbinding

元契約の **1条件集合・1 job・1 CPU process・16 GiB RAM・全体wall 30分・保存中間terms総数200,000・text／metadata合計20 MiB** を維持する。以下は将来満たすべき制御仕様であり、設定済み・動作確認済みとは主張しない。

| 制約 | 必要な制御・確認 | 現在の状態／停止条件 |
| --- | --- | --- |
| 1 job・1 CPU process | 同時run・再試行・solver subprocess／portfolioを禁止。exact solverを同じPython process内で使い、科学workerのfork／子process生成を禁止する | science entrypointなし。監督はjob外のOS／scheduler側に置き、job内のworkerは1 processに保つ。未確認なら起動不可 |
| 1 CPU | 起動前に許可CPUを1つ選び固定したaffinityと単一threadを適用。現在のaffinityは0〜31。`OMP_NUM_THREADS=1`、`OPENBLAS_NUM_THREADS=1`、`MKL_NUM_THREADS=1`等を固定し、backend並列性も無効化する | taskset等は存在。CPUQuota=100%だけでは単一CPUへの固定にならない。実jobの適用は未確認 |
| 16 GiB RAM | 専用cgroup v2の`memory.max=17179869184`（systemdならMemoryMax）、swapなし、OOM時の全job停止と終了記録。必要ならRLIMIT_ASも保守的な追加制限にする | cgroup書込み不可。現在の共有sessionのmemory.maxは`max`。専用job上限は未設定 |
| 全体30分 | 因子gateから還元screen・出力まで単一monotonic deadline。起動・停止猶予を含め1800秒以内に終了させる外部監督、process group／cgroup全体のkillを固定 | timeoutは存在するがlauncherは未作成。30分後にさらにkill猶予を足して上限を延長しない |
| 保存terms総数200,000 | 保持するoperator／係数polynomial、中間式、queue、cache、copyを含む集計規約を実行前固定し、追加・展開**前**に上限を確認。内部の保存展開を数えられないAPIを無条件で呼ばない | 契約用の計数・増殖前停止が未実装。opaqueなSymPy／solver内部の展開項にも上限を守れる保証は未確認。計数できない経路は使わずINCONCLUSIVE |
| 出力20 MiB | 全text／metadataの合計を上限内へ抑え、停止記録用の余白を予め確保。出力を別fileへ分けても合計を超えない | future writer／監督の仕様として固定が必要。既存artifactを削って余白を作らない |

現在のcgroup2 mountはsandboxからread-onlyで、sessionにmemory／pids controllerは見えるが、CPU controllerのjob設定は確認できない。`systemctl --user show`のread-only照会もbus接続がOperation not permittedとなった。**root／user managerへの権限昇格で科学jobを起動する経路は今回設定していない。** 専用scheduler又はdelegationを持つ環境が後に用意され、実効値を固定・確認できるまで資源gateは閉じる。

[systemd resource-control document][systemd-res]とインストール済み249のmanualを静的に照合した。cgroupのmemory.maxはkernelの上限・OOM機構であり、厳密に一瞬も超過しない数学的保証ではない。[Linux公式説明][cgroup]にも一時的超過の記述がある。事前に設定を読み返し、上限到達・OOM・killをINCONCLUSIVEとして扱う運用が必要である。

[CPythonのresource仕様][python-resource]でRLIMIT_ASはvirtual address spaceの制約である。RLIMIT_RSSやpsutilの定期監視を、job全体のRAM hard limitと同一視しない。[GNU timeoutの仕様][timeout-doc]では追加kill猶予が別に存在する。各stageに新しい30分を与えたり、solverの内部timeoutだけに依存したりしない。

上限を維持できない場合に、termsを部分的に捨てる、係数を丸める、次数を減らす、rational-onlyへ変える、別sectorへ切り替える等の縮退実行はしない。**backend・資源機構の不足は、科学処理前に停止する理由である。**

## 6. 将来の停止順序と入力freeze

実行経路は現在 **NOT_BOUND（entrypointなし）**。科学計算開始の明示承認とは別に、以下の準備が必要である。本書の公開だけでそれらを実施しない。

1. **非科学pre-launch gate**：別途のユーザー明示承認、契約hash、backend／checkerの完全版・hash、exact実数判定の経路、全資源制御と1条件集合の計画を確認する。不足時は起動せず、将来の承認済みrunについてのみINCONCLUSIVE／原因を記録して停止する。現在はこの手前でSTOP。
2. **Phase B冒頭の科学gate**：正本§2.3の因子適格性をexactに判定する。非可換性、full Fock・N=2での二体非自明性等を未計算のまま通過させない。不成立／未確定ならINCONCLUSIVEで止め、factorを交換しない。
3. 適格性gate通過後だけ、元契約の順序で4次形式展開、CAR／CCR整理、一つの係数条件集合、exact box可解性判定へ進む。正規形・算術・terms等を保証できないstageでINCONCLUSIVE。
4. exact整合例ならexact代入と限定還元screenへ進み、CARによる選択規則の説明不足も元契約どおりINCONCLUSIVE。exact不整合を閉じられた場合だけNO_SOLUTION_IN_FIXED_ANSATZ。他の分類も正本の条件を維持する。
5. いずれの結果・上限到達でもSTOP。同じ予算での自動再開・代替入力・別解探索はしない。

科学開始前のfreezeには次を含める。

- 正本commit／path／blob／byte／SHA-256、本bindingとそのprovenanceの公開commit・hash、将来の明示承認の対象・停止点。
- 正本内の2因子、単位重みK、4 modes、識別用N=2、full Fock主判定、H_known=0、共通busとCAR／CCR、固定12 word、x1〜x12とbox、共通Δとη、4次・normal-order／Weyl規約。入力は正本bytesを参照し、今回別の数値入力fileを作らない。
- interpreterの実path・binary hash、OS／architecture、依存package・実source・native libraryの版とhash、隔離環境の完全lock、exact backendの設定・共有library hash。現記録の選択的hashを将来の全環境lockの代用にしない。
- checker／adapter／launcherの承認範囲・commit・全source hash、由来タグとexact代入・還元screenの経路、term集計定義、保存形式、例外・kill時の記録方法。今回は存在しないのでhashを捏造しない。
- CPU affinity・thread設定、cgroupの専用pathと実効memory／swap値、単一deadline、出力上限、作業directory、事前予約された停止記録。実行環境が変われば再bindし、黙って別interpreterで実行しない。
- 科学計算後に初めて存在する条件集合・witness等は、生成stageでhashを残す。開始前に未生成artifactのhashを持つとは記さず、生成規則・checkerを事前固定する。

## 7. 科学契約の保全と残条件

4 modes、N=2、full Fock主判定、2因子、12 segment、4次形式展開、振幅boxは**変更0件**。因子適格性はPhase B冒頭の最初の科学計算であり、環境確認を理由に先行実行していない。full Fockの固定条件が将来不成立でも、sector限定構成一般の不成立とはしない。D1／D2、元電子Hamiltonianの絶対基底エネルギーとの対応を維持する。

残条件は、**exact実数判定backendの導入・完全versionとhashの固定、専用資源制限環境の確保、承認されたchecker／adapter／launcherの作成範囲と実行経路の確定、ユーザーによるPhase B実行の別途明示承認**である。現状のSymPy部品確認だけでこれらを満たしたことにはならない。科学契約の変更が必要になった場合は、その変更を実施せず理由・必要な承認を別に提示する。

既存SOURCE、結果、grant、authorization、STOP／PAUSEと他worktreeは変更しない。U1／U3／U4、T1-D、FS-R1 Phase B未承認、PRの既存CLOSED／STOP／PAUSED／HOLD／NOT_ADOPTEDを維持する。保全監査の範囲・限界はprovenanceへ記録する。

保存先は新規branch **qc-p1star-phase-b-environment-binding-20261017**、baseは正本の1771564d919837e2440a9fcb175ac054284a729c。公開対象は本書とprovenance.jsonの新規2件のみ。読む順序は**本書→provenance→固定契約**。資料のbyte／blob／SHA-256とremote commitは公開後に独立照合し、そのreceiptは自己参照を避けてlocalに保存する。

**Mandatory STOP：binding資料の公開・照合後に停止する。科学用checker作成・実行、因子適格性計算、Magnus／CAR係数・方程式生成・求解、simulation、新証明、回路生成、pulse最適化、詳細科学レビュー、正式採択へ進まない。**

[contract]: https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/1771564d919837e2440a9fcb175ac054284a729c/docs/research_exploration/p1star_symbolic_preflight_20261017/symbolic_verification_contract_draft.md
[pypi]: https://pypi.org/pypi/sympy/1.13.3/json
[sympy-domains]: https://docs.sympy.org/latest/modules/polys/domainsref.html
[sympy-ineq]: https://docs.sympy.org/latest/guides/solving/reduce-inequalities-algebraically.html
[of-order]: https://github.com/quantumlib/OpenFermion/blob/v1.6.1/src/openfermion/transforms/opconversions/term_reordering.py
[of-coeff]: https://github.com/quantumlib/OpenFermion/blob/v1.6.1/src/openfermion/ops/operators/symbolic_operator.py
[z3-nlsat]: https://z3prover.github.io/papers/programmingz3.html#sec-nlsat
[z3-api]: https://z3prover.github.io/api/html/z3.z3.html
[systemd-res]: https://github.com/systemd/systemd/blob/v249/man/systemd.resource-control.xml
[cgroup]: https://github.com/torvalds/linux/blob/v6.8/Documentation/admin-guide/cgroup-v2.rst
[python-resource]: https://github.com/python/cpython/blob/v3.11.1/Doc/library/resource.rst
[timeout-doc]: https://github.com/coreutils/coreutils/blob/v8.32/doc/coreutils.texi
