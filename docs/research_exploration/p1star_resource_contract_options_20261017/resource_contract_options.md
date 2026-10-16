# P1* Phase B：RAM実行環境と20万terms契約の比較

2026-10-17 JST。対象：**P1STAR-A-v1**。状態：**READ_ONLY_PREFLIGHT / UNADOPTED_PROPOSALS / NOT_READY**。

**案2（自前の管理項を20万に制限し、native内部はOSのRAM上限・全体wallで制御）を、正式判断に付す案として条件付きで推奨する。採択はしていない。現在のsandboxではjob全体の16 GiB RAM制限を設定できる経路を確認できず、どちらの案でも実行不可のままである。** 契約変更だけでNOT_READYを解除できるとはしない。

## 1. 固定資料、権限、科学契約

正本は技術基盤commit **208cb9bfdbca6116b11b70bc01937aba732e9199** の[技術判定報告][report]、[技術テスト結果][tests]、[README][readme]。必要な実装の`exact.py`、`solver.py`、`guards.py`も同commitで静的に読んだ。元の科学契約はcommit **1771564d919837e2440a9fcb175ac054284a729c** の[契約草案][contract]。今回これらを変更していない。

今回の承認はread-onlyの環境調査と、比較資料・契約変更案・provenanceの作成・公開だけである。科学用packageをimportせず、既存の人工テストも再実行していない。科学用driver、追加guard、solver patch、環境作成、科学計算、新しい数学的証明は作成・実行していない。

**4 modes、N=2、2因子とその値・単位重み、12 segmentと順序、12実振幅のbox、4次形式展開、full Fock主判定、exact算術、D1／D2は変更0件。** 新しい科学的仮定を加えない。因子適格性は未計算で、将来のPhase B冒頭の最初の科学gateに保持する。full Fockでの将来の不成立を、sector限定構成一般の不成立としない。

## 2. Task A：現在のRAM制御経路のread-only調査

調査範囲は**現在のCodex sandboxから見えるnamespace・PATH・列挙した既知のlocal path**である。外部clusterや通常ホストshellでの利用可能性まで否定しない。SSH接続、remote環境へのlogin、job投入、daemon・namespace・cgroup作成は行っていない。

| 経路 | 実際の観測 | 今回の結論／将来必要な確認 |
| --- | --- | --- |
| 現在のcgroup v2 | `/sys/fs/cgroup` mountはread-only。session、user-1001.slice、user.sliceのmemory.max／memory.swap.maxは全て`max`で書込み不可。sessionのsubtree_controlは空 | 専用jobの16 GiB制限を現在の権限で設定する経路なし。共有sessionの上限変更もしない |
| systemd user manager／既存delegation | systemd-run／systemctlは存在。user／system両managerへのread-only `show`照会が`Operation not permitted`で失敗。静的な`user@.service` templateは`Delegate=pids memory` | 静的templateは実効delegationの証拠にならない。通常ホスト側で既存delegationを利用できる可能性は**未確認**。別途許可された環境で実効controller・所有者・書込み可能な専用subtreeを確認する必要がある |
| 既存scheduler | PATH上のSlurm（srun／sbatch／scontrol／sinfo）、PBS／SGE（qsub／qstat／qrsh）、LSF、HTCondor toolを検出せず。列挙した`/etc/slurm`、PBS、Condor、`/opt/slurm`等も未検出 | 利用可能なscheduler経路は確認できない。外部schedulerの不存在を主張しない。既に利用権限がある接続先・site設定が示されるまで候補扱い |
| Container runtime | Docker／Podman／Apptainer／Singularity／runc／crun／LXCをPATHで検出せず。列挙したDocker／Podman／containerd socketも未検出 | 現在利用できるcontainerによる制限経路は確認できない。将来runtimeがあってもmemory controllerの実効設定が必要 |
| namespaceだけの隔離 | unshare／nsenterは存在。user namespace用sysctlは有効値だが、processのCapEff／CapBndは0、NoNewPrivs=1。namespaceの作成・移動は未実施 | toolやsysctlの存在を、job RAM制限の成立としない。namespaceだけでは専用memory controllerの上限は得られない |
| RLIMIT_AS／定期監視 | prlimit／timeoutは存在。旧技術テストは小さいvirtual address-space上限の試験に合格している | **RLIMIT_ASは仮想アドレス空間**。job RAMと無条件に同一視しない。RSSの定期監視も超過前の強制上限を保証しない |

bus socketはmode上アクセス可能でも照会が拒否された。mode bitだけで利用可能と判断しない。systemdの[delegation仕様][delegation]も、Delegateの記載が要求を表し、実際に得られるcontrollerは別に確認すべきことを説明している。インストール済みsystemdは旧binding記録の249系列であり、最新documentの後発機能を利用可能とは仮定していない。

現在のsandboxでの結論は**「権限昇格なしで設定できるjob全体RAM上限を確認できない」**である。sudo、mount変更、既存cgroupへの書込み、controller有効化、別namespaceへの迂回、service変更は0件。権限拒否された照会を昇格して再試行しない。

### 将来の実行環境として比較できる経路

| 候補 | 実現に必要な条件 | この時点で保証しないこと |
| --- | --- | --- |
| R1：通常ホストの既存user delegationを使う専用job subtree | 既に認められた通常user環境で、実効memory delegationと新規job用領域の管理権限を確認。job用limit設定・読戻し・人工テストは追加承認後だけ | 静的templateだけで利用可能とはしない。現在のsandboxを抜けたり既存sessionを変更したりしない |
| R2：既存schedulerのenforced memory job | 利用権限のあるsite・queue、memory enforcement plugin／設定、jobとstepの包含、OOM時全体終了、wall・CPU設定を確認 | Slurmの`--mem`等の資源要求だけではhard limitにならない。site設定は未確認 |
| R3：既存の許可済みcontainer実行環境 | cgroup v2とmemory controllerの実効利用、memory／swap設定、job内全processの包含、外側監督を確認 | venvやfilesystem隔離だけではRAM制限にならない。rootless runtimeにもdelegation等が必要。新規導入や起動は今回未承認 |

R1は、静的templateにmemory delegationの記載があるため**次に可否を確認する候補**として優先できる。ただし、利用可能だという推定ではない。R1が使えなければ、既に利用可能なR2又はR3の情報を確認する。新しいインフラ契約や外部環境の取得を今回提案の採択として実施しない。

Slurm公式資料は、memory requestだけではenforcementされず、`ConstrainRAMSpace`等の設定が必要と記す。またOOM時にstep内の他processが継続し得るため、全job停止の確認も要る。[sbatch仕様][slurm-batch]、[cgroup.conf仕様][slurm-cgroup]。Dockerもmemory／swapの値に固有の意味があり、container flagの指定だけで実効上限を確認したことにはならない。[memory制約][docker-memory]、[rootlessの条件][docker-rootless]。いずれも将来候補の条件説明であり、local利用実績ではない。

### 16 GiBを実行契約へbindする際の共通事項

候補環境では、job専用memory controllerについて **16 GiB＝17,179,869,184 bytes** を設定・読戻しし、swapを使わない方針、全科学process／native libraryの包含、OOM・外部kill時の全job終了と記録を固定する。共有session又はhost全体の上限を16 GiBへ変更しない。科学workerは1 process・1 CPU、監督は科学処理を分担せず、memory境界に含むprocessとjob外の監督を明示する。

ここでの上限はOS memory controllerの計上・enforcementの意味である。raw RSS合計や、あらゆる物理メモリが一瞬も16 GiBを超えないという数学的保証とは区別する。kernel公式仕様もmemory.maxの一時的超過を明記する。[cgroup v2仕様][kernel]。**厳密な瞬間最大値を旧契約が要求するなら、このOS方式が満たすとは認定できない。** この解釈は実行前に明示して判断を受ける。RAMの数値上限を増やす案ではない。

設定・読戻し・境界外processの不存在・人工的な超過時停止・deadline・停止記録の確認は、追加技術実装／技術テストの承認事項である。今回は設定も試験jobも実施していない。[CPythonのresource仕様][python-resource]に照らしても、RLIMIT_ASをこの確認の代用にはしない。

## 3. Task B：20万termsの2案

### 案1：既存の包括的上限を維持する

**自前の項とnative内部を含む全ての保存中間termsに対する200,000上限を維持する。** 現在のZ3 4.13.3.0／Python wrapperと自前TermLedgerだけでは、この包括保証は成立していない。保存総数の時間方向の意味（同時保持か生成累計か）に未固定部分がある場合も、資料側で元の意味を狭めず、正式判断で固定する。案2の条項案は同時保持と明示して提示する。

自前の`TermLedger`は登録されたmap entryを数えるが、native polynomial、projection、AST／cache、model／algebraic値、serialization、Python一時表現などを数えない。`solver.py`からZ3への受渡しにも、その内部項を共通ledgerへ予約するhookはない。既存41テストはこの包括上限の確認ではない。

Z3の`rlimit`はresource counterであって「同時保持monomial数20万」という契約ではなく、statisticsは全生存項のallocation前予約を与えない。memory用parameterも、Python等を含む全job RAM制限や項数制限の代用ではない。[Z3公式parameter説明][z3-params]を参照したが、最新documentを固定4.13.3.0の未試験機能の根拠にはしていない。

この案を追うなら、少なくとも次が追加で必要になる。

- 異なる表現で何をtermと数えるか、共有・copy・cache・寿命・同時保持・係数内部との境界を定義し、元の包括保証を狭めない計数仕様を固定する。
- Python入力／一時表現とnative内部の関連allocation経路を監査し、全保持箇所を一つの予算へ接続する。allocation後のsamplingではなく、増加前の予約、解放、例外・中断時の整合を実装する。
- native instrumentationが必要ならsource commit／patch／build条件／binaryを新たに固定し、exact算術・SAT／UNSAT／UNKNOWN・witnessの扱い・中断処理を人工問題で再検証する。既存wheelのhash・既存テストを変更版の検証として流用しない。
- 同等の包括計数を持つ別backendを選ぶ場合も、全12実変数・exact box判定と計数範囲を新しく確認する。backend変更は自動実施しない。

**現在この追加実装が可能・完了するという保証はない。** 全項を20万に抑えても、一つのexact係数の整数桁数やmetadataのbytesは別のため、16 GiB RAMと全体wall上限は引き続き必要である。未達ならNOT_READYを維持する。案1を採らないことを科学的な不可能性や仮説の低価値へ一般化しない。

### 案2：TermLedgerの管理項に対象を限定する契約変更案

これは**旧包括保証の実質的な縮小**であり、単なる説明の修正ではない。次の条項案を提示するが、元契約へ適用・採択していない。

> **未採択条項案 R-TERMS-2**：保存項数の上限200,000は、run全体で共用する唯一のTermLedgerに登録した全TermMapの同時保持entry総数に適用する。operator／parameter monomialをflattenしたentry又は係数多項式のmonomial entryを単位とし、所有mapのcopyは別に数える。viewの共有参照だけでは追加entryにしない。新規entryを保存する前に予約し、相殺・解放時に減算する。stage変更やsolverへの受渡しを理由にledgerを作り直さない。上限超過はINCONCLUSIVEとしてrunを終了する。
>
> native solver内部とその他のledger外表現のterms数については、20万という保証を行わない。それらの資源消費は、同じjobのOSによる16 GiB memory制限と、入力gateから最終記録までの単一1800秒wall上限に含めて制御する。既存の1条件集合・1 job・1 CPU process・text／metadata合計20 MiBを維持する。

| 表現 | 案1 | 案2の提案する扱い |
| --- | --- | --- |
| 自前TermMap内のoperator／係数monomial | 全保持項へ包含 | 唯一のledgerで集約して20万上限。別ledgerや通常dictへの退避で回避しない |
| 自前mapのcopy・cache | 全保持項へ包含 | TermMapとして保持するcopy／cacheは全て集約。外部へ無断copyして計数を回避しない |
| 入力tuple、再帰stack、Python一時object、Fraction内部の整数 | 包括計数との境界・項単位を定義し、必要部分を計数 | ledger項数の対象外。job RAM／wallへ包含。項数による内部膨張の予防保証は失う |
| Z3 AST、native polynomial／projection／cache、algebraic値・model、native簡約・代入 | 全ての保存中間termsを包含する実装が必要 | ledger項数の対象外。native内だけで20万を超え得る。OS RAM／wallへ包含 |
| SMT textの生成、witness／proofの表現、trace metadata | 項としての定義と保持範囲を漏れなく監査 | ledger外。生成中はRAM／wall、保存するtext／metadataは20 MiB総出力へ包含 |

案2でも**現在の実装を無変更で完成扱いにしない**。future driverを含む全管理mapが唯一のledgerを共有すること、計数回避する保持経路がないこと、output・例外・native中断を全体予算へ接続することを追加承認後に技術確認する必要がある。terms上限は生成累計ではなく同時保持entryの上限であり、この意味も正式判断前に明示する。

### 案2の追加リスク、停止条件、再現性

案2ではnative内部が20万を超えたか分からず、RAM又はwallまで大きな内部表現を持ち得る。countが小さくてもbig integer、trace、model、serialization等がRAMを消費する。OS killはpartial outputだけを残す可能性もある。**元の包括term保証を失ったことを結果とprovenanceへ明記し、包括保証済みrunと同じresource claimにしない。**

実行前のRAM境界・wall／全出力・唯一ledger・source／環境lock等が未確認なら、科学jobを起動せずNOT_READYを維持する。将来の承認済みrunでは、ledger上限、OOM／外部kill、全体deadline、出力上限、backend UNKNOWN、例外、exact witness再照合不能、必要な記録の欠落をINCONCLUSIVEとする。nativeが途中でSAT／UNSATを表示しても、必要な照合・記録を予算内で完了できなければ、科学的結論へ昇格させない。

停止後にRAM・time・term上限を増やす、solverを再起動する、別word・factor・sector・parameter固定・近似算術で救済する、といった再試行はしない。項数を上限へ合わせるための項の切捨ても行わない。

数学的な入力・exact判定の意味は変えないが、資源不足でどこまで到達するかは、kernel／cgroup計上、同居負荷、libraryのallocation、serialization、外部監督に依存する。したがって同一sourceだけで終了分類・wall・peak memory・返るwitnessがbit単位で再現するとは保証しない。native term数の再現性も保証しない。

将来は、入力・source・Python／Z3／native library／OSの版とhash、backend設定、RAM／swap実効値、cgroup又はscheduler jobの識別・包含、CPU／process設定、唯一ledgerのlive／peak、全体deadlineと終了原因、出力byte数、条件集合・exact witness等のhash、利用可能なOS memory event／peak情報とその取得方法を固定・記録する。memory samplingやsolver statisticsは補助診断に留め、hard limit又はnative項数の証明としない。記録は20 MiB内で必要な停止情報の余白を確保し、不足時に未承認の保存先へ逃がさない。

## 4. Task C：比較と推奨の範囲

| 判断軸 | 案1：包括20万を維持 | 案2：管理項20万＋nativeはRAM／wall |
| --- | --- | --- |
| 現在の可否 | NOT_READY。RAM経路に加え、nativeを含む計数機能がない | NOT_READY。RAM経路なし、条項は未採択、全体guard統合も未完了 |
| 残せる保証 | 全項の計数を実装・検証できれば、包括term上限を維持 | 自前の管理entryの上限のみ。nativeを含む全項上限は保証しない |
| 主な追加作業 | 共通term単位・全保持経路・native instrumentation、変更backendのlock／人工再検証 | 管理範囲の正式固定、唯一ledger・全job RAM／wall／output・停止記録の統合と人工テスト |
| 残る保証の欠落 | 現在の全項計数未達。RAM／wall／全出力も別途必要 | native項数は契約上も対象外。RAMの計上・一時超過、kill時記録、全出力等の実効確認は別途必要 |
| 数学・物理の変更 | なし。達成困難を理由に科学条件を緩和しない | なし。変更するのは資源契約の計数対象だけ |
| 正式判断 | 既存term契約を維持する方針と、必要な追加技術作業の範囲 | 包括保証を失う変更を明示してユーザー／GPTが正式判断する必要 |
| 科学実行の承認 | 技術検証・freeze完了後に別途必要 | 契約変更承認・技術検証・freeze完了後に別途必要 |

技術的な解決方針としては、**案2を採択判断に付すことを条件付きで推奨**する。自前で監査できる項数制御と、opaqueな内部消費を受け持つOSの資源制御を明確に分けられ、現backendを全面改変する案1よりも追加作業の境界を定義しやすい。ただし作業量・必要時間・P1*での完了率は未評価であり、実現済み・安価・資源優位とは主張しない。

nativeを含む包括term上限自体を必須の方法論的条件として維持する判断なら、案1を維持し、対応backend又は計数実装を得るまで停止を継続する。研究資源不足や仮説の低価値を理由に切り捨てる判断ではない。

## 5. 実行前の判断・承認を分離する

次の事項をそれぞれ別に扱う。本資料の公開は、いずれの承認にもならない。

1. **契約の正式判断**：案1維持か案2採択か、termの単位・包含、RAMのOS enforcementとしての意味をユーザー／GPTが決める。案2なら旧契約を直接書換えず、承認された追補のID・対象条項・版・hashを固定する。
2. **実行環境と追加技術実装の承認**：既に利用権限があるR1／R2／R3のどこで、どの専用領域・guard・人工テストまで行ってよいかを固定する。現在の権限拒否を迂回しない。科学driverの作成範囲は、必要になった時点で明示承認の対象に含める。今回は作成しない。
3. **技術判定の更新**：承認された環境・実装・人工試験の証拠に基づいてのみ準備状態を更新する。旧41テストや本比較だけで、未試験のRAM経路・新計数範囲・driverを準備済みとはしない。
4. **Phase B科学計算の別途明示承認**：入力・環境・source／artifact hash・1条件集合・全budget・停止点を固定した後に行う。因子適格性から始め、契約変更や技術実装の承認から自動で進めない。

現時点の科学的成立性は未判定であり、A/B分類、科学的GO、新原理、新規性、資源改善、正式採択を認定しない。

## 6. 保存・保全・終了

Repository：**HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae**。新branch：**qc-p1star-resource-contract-options-20261017**。base：**208cb9bfdbca6116b11b70bc01937aba732e9199**。

新規資料は**本書とprovenance.jsonの2件だけ**。読む順序は本書→[provenance.json](provenance.json)→固定技術報告・README・元科学契約。origin/result commitとverified snapshot commitを分け、manifestはprovenance自身を自己除外する。公開後にremote SHA、独立Git blob、GitHub raw bytes、byte数・SHA-256を照合し、結果は別local receiptと最終handoffへ記録する。

元workspace、既存SOURCE・科学結果・authorization・grant・STOP／PAUSEと他worktreeのdirty／staged／untrackedを保全する。T1-D、U1／U3／U4、FS-R1 Phase B未承認、PRのCLOSED／STOP／PAUSED／HOLD／NOT_ADOPTEDを維持する。並行更新はwriterを推定せず、書戻し・取消しをせず記録する。保全照合の方法と限界はprovenanceに記載する。

**Mandatory STOP：比較資料を公開・照合したら停止する。契約変更の正式採択、追加技術実装・技術テスト、科学用driver作成、Phase B科学計算、科学レビュー・正式採択へ進まない。**

[report]: https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/208cb9bfdbca6116b11b70bc01937aba732e9199/docs/research_exploration/p1star_technical_foundation_20261017/technical_readiness_report.md
[tests]: https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/208cb9bfdbca6116b11b70bc01937aba732e9199/docs/research_exploration/p1star_technical_foundation_20261017/technical_test_results.json
[readme]: https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/208cb9bfdbca6116b11b70bc01937aba732e9199/research_tools/p1star_foundation/README.md
[contract]: https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/1771564d919837e2440a9fcb175ac054284a729c/docs/research_exploration/p1star_symbolic_preflight_20261017/symbolic_verification_contract_draft.md
[kernel]: https://docs.kernel.org/6.8/admin-guide/cgroup-v2.html
[delegation]: https://systemd.io/CGROUP_DELEGATION/
[slurm-batch]: https://slurm.schedmd.com/sbatch.html
[slurm-cgroup]: https://slurm.schedmd.com/cgroup.conf.html
[docker-memory]: https://docs.docker.com/engine/containers/resource_constraints/
[docker-rootless]: https://docs.docker.com/engine/security/rootless/
[python-resource]: https://docs.python.org/3.11/library/resource.html
[z3-params]: https://microsoft.github.io/z3guide/programming/Parameters/
