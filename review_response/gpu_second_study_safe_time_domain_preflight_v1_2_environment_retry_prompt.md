# GPUサーバー側Codexへの再実行依頼：第二研究preflight v1.2のみ

v1.1 preflightは科学計算前の環境gateで停止しました。source identity 67/67、H01/P03、
第一研究source identity、独立性検索、GPU memory gateまでは合格し、唯一の停止理由は指定した
`/usr/bin/python3`に必要packageが存在しなかったことです。

repository内の既存GPU実行記録で一貫して使われている
`/home/AbeHiromu/venvs/trotter-common/bin/python`を新規installなしで厳密に同定し、
**preflight全体だけを新規branch/outputへ一度再実行**してください。v1.1のbranch、commit、
outputは変更せず保存します。

Phase A、Phase B、新規Hamiltonian、RHF/CISD、group spectrum、proxy、PF action、direct truthは
引き続き許可しません。preflight完了後に停止してください。

## 固定版

- protocol commit：`804331ecc976b83ae880940719706c11999247bc`
- protocol SHA-256：
  `a6290b107ebbf93f7c0ee3bc383208862c51e37603a670625091e15472d4584b`
- parent preflight実装commit：`0f3381863ed0eb0a31b59b8018e816bebe3840f7`
- v1.1 review済みbundle commit：`ee9103b18b48dccde5700287405780565bd35cb7`
- v1.2 environment amendment commit：
  `9e2b9b0ba2d068b18ca8fda5b3a346954551938f`
- v1.2 review済みbundle commit：
  `a23b5beb8c62380b8f873385e37fd0031e265da2`
- v1.1 amendment：
  `review_response/second_study_safe_time_domain_preflight_amendment_v1_1.json`
- v1.1 amendment SHA-256：
  `218d325d2b13eea24196302a52e4a1a3e34ae92973518b61835bf2ad3974759d`
- v1.2 environment amendment：
  `review_response/second_study_safe_time_domain_preflight_environment_amendment_v1_2.json`
- v1.2 amendment SHA-256：
  `ab87da7c42aba20658e5f5d4a204cdf761c50f0814d24719a36e72be674da77e`
- source runner：`review_response/run_second_study_safe_time_domain_preflight.py`
- parent実行指示：
  `review_response/gpu_second_study_safe_time_domain_preflight_v1_1_retry_prompt.md`

## 保存する2回の停止記録

初回：

- branch：`gpu-second-study-safe-time-domain-preflight-20260927`
- result commit：`e1891dfd24ec5f0064b0598e51eb260073fd2b1e`
- output：
  `artifacts/server_second_study_safe_time_domain_preflight_20260927_3a0dd56/`
- status：`failed_source_identity`

v1.1：

- branch：`gpu-second-study-safe-time-domain-preflight-v1-1-20260927`
- result commit：`b520f9bd8f575456531e7c0b0f2692973b436e21`
- output：
  `artifacts/server_second_study_safe_time_domain_preflight_v1_1_20260927_0f33818/`
- status：`failed_environment`
- source checks：67/67合格
- suspicious independence hit：0
- 独立4条件の生成済み数値結果：0
- GPU memory gate：合格
- focused/full tests：未開始
- Phase A/B実行：0
- 新規科学計算：0

両branch/outputをreset、rebase、amend、削除、変更、再利用しません。過去outputのauditやtest logを
v1.2 outputへコピーせず、全gateを今回の時刻とfilesystem stateで再実行します。

## v1.2で変えるもの

変更はpreflightに使用する既存Python environmentの選択とidentity記録だけです。

- 使用するabsolute path：
  `/home/AbeHiromu/venvs/trotter-common/bin/python`
- common site-packages：
  `/home/AbeHiromu/venvs/trotter-common/lib/python3.12/site-packages`
- `/usr/bin/python3`へfallbackしない。
- virtualenvをactivateせず、全commandで上記absolute pathを使う。
- package、Python、CUDA、driverをinstall、update、downgrade、修復しない。
- `PYTHONPATH`へ別environmentのsite-packagesを追加しない。
- environmentが欠損・不一致なら`failed_environment_identity`として停止する。

このenvironmentは既存のD03、practical calibration、F/HF bridge、H9/H11、
H-chain、unused-molecule holdout用scriptとP03 metadataに記録済みです。今回の候補探索で選んだ
environmentではありません。

protocol JSON、分子、geometry、情報源、PF、候補時刻、threshold、停止規則、`gamma=1.01`、
`beta=1.2`は変更しません。

## branchとworktree

まずfetch後に次を確認します。

```bash
git fetch origin --prune
git cat-file -e e1891dfd24ec5f0064b0598e51eb260073fd2b1e^{commit}
git cat-file -e b520f9bd8f575456531e7c0b0f2692973b436e21^{commit}
git cat-file -e 0f3381863ed0eb0a31b59b8018e816bebe3840f7^{commit}
git cat-file -e ee9103b18b48dccde5700287405780565bd35cb7^{commit}
git cat-file -e 9e2b9b0ba2d068b18ca8fda5b3a346954551938f^{commit}
git cat-file -e a23b5beb8c62380b8f873385e37fd0031e265da2^{commit}
git merge-base --is-ancestor \
  804331ecc976b83ae880940719706c11999247bc \
  9e2b9b0ba2d068b18ca8fda5b3a346954551938f
git merge-base --is-ancestor \
  0f3381863ed0eb0a31b59b8018e816bebe3840f7 \
  9e2b9b0ba2d068b18ca8fda5b3a346954551938f
git merge-base --is-ancestor \
  9e2b9b0ba2d068b18ca8fda5b3a346954551938f \
  a23b5beb8c62380b8f873385e37fd0031e265da2
```

v1.2 review済みbundle commit `a23b5be...`から独立worktreeと新規branchを作ります。
推奨名は

`gpu-second-study-safe-time-domain-preflight-v1-2-20260927`

です。同名があれば上書きせず連番を付けます。既存worktreeをreset、clean、stashせず、mainへ
merge・force-pushしません。

## 新規output

推奨output：

`artifacts/server_second_study_safe_time_domain_preflight_v1_2_20260927_9e2b9b0/`

同名があれば連番を付け、既存directoryへ書きません。過去output/cacheを入力または再開用に
使いません。

## environment identity gate

科学moduleをimportする前に、使用するPython自体を読み取り専用で照合します。

1. executableが存在し、実行可能である。
2. requested path、symlink target、`realpath`、executable SHA-256を記録する。
3. `sys.executable`、完全なPython version、`sys.prefix`、`sys.base_prefix`を記録する。
4. `pyvenv.cfg`の実在path、内容のSHA-256を記録する。
5. `site.getsitepackages()`と`sys.path`を記録し、別virtualenvのsite-packages混入がないことを
   確認する。
6. `requirements-gpu.txt`のSHA-256と次のdistribution versionを照合する。

```text
numpy==1.26.4
scipy==1.14.1
matplotlib==3.9.2
pyscf==2.7.0
openfermion==1.6.1
openfermionpyscf==0.5
qiskit==1.3.0
qiskit-aer-gpu==0.15.1
```

さらに`pytest`、`qiskit_aer`、`cupy`、`pandas`をimportできることを要求し、module pathと
distribution versionを記録します。CuPy distribution名（例：`cupy-cuda12x`）も
`importlib.metadata`で記録してください。

これはimport smoke testだけです。CuPy array作成、device allocation、kernel、Hamiltonian/state生成、
proxy、PF actionを実行しません。environment、package、共有設定を一切変更せず、一項目でも不一致なら
`failed_environment_identity`として停止します。

## source identity gate

environment gate合格後、新規outputへprotocol/amendment hashを照合し、source runnerを同じPythonで
再実行します。

```bash
sha256sum review_response/second_study_safe_time_domain_protocol.json
sha256sum review_response/second_study_safe_time_domain_preflight_amendment_v1_1.json
sha256sum review_response/second_study_safe_time_domain_preflight_environment_amendment_v1_2.json

PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src:review_response:. \
/home/AbeHiromu/venvs/trotter-common/bin/python \
  review_response/run_second_study_safe_time_domain_preflight.py \
  --project-root "$PWD" \
  --output artifacts/server_second_study_safe_time_domain_preflight_v1_2_20260927_9e2b9b0/local_source_preflight.json
```

source runnerのschemaは、transport正規化実装を変えないため
`second_study_safe_time_domain_local_preflight_v1_1`のままです。次を要求します。

- protocol/v1.1/v1.2 amendment hashが各固定値と一致。
- raw/canonical originと`github_transport_normalization_v1_1`が記録される。
- source checksが67/67合格。
- Phase A/B authorizationがfalse。
- 新規Hamiltonian/state/proxy/direct truth countが全て0。

失敗時は`failed_source_identity`として停止し、remote URLや共有Git設定を変更しません。

## source gate後の残りpreflight

source checksが67/67合格した場合だけ、次をすべて再実行します。

1. H01/P03元成果物の読み取り専用identity照合。
2. 全worktree、全local/remote-tracking branch、tag、untracked artifact、binary、log、archiveを対象に
   したLiF/HCl独立性検索。
3. `nvidia-smi`によるGPU identity、process、各GPU free memory 8 GiB以上の確認。
4. focused tests。
5. 全`review_tests`。
6. 軽量audit、decision、manifestと全file SHA-256の照合。

v1/v1.1の停止output、v1.2 amendment、このprompt、追加testに含まれる分子名・geometryは
planning/validation記録としてpathごとに分類します。ただし未知のhitや、独立4条件に対する数値
PF error、QPE cost、proxy response、direct truthを自動的にplanning扱いしません。一件でもその
数値結果を発見したら`no_go_independence_contaminated`として停止し、条件を差し替えません。

過去の2166 hitという件数を今回結果としてコピーしません。全検索を再実行し、今回のworktree/ref/
archive数、hit数、分類、開始・終了時刻を新規auditへ記録します。archive展開物は一時directoryだけに
置き、commitしません。

focused tests：

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src:review_response:. \
/home/AbeHiromu/venvs/trotter-common/bin/python -m pytest -q \
  review_tests/test_second_study_safe_time_domain_protocol.py \
  review_tests/test_second_study_safe_time_domain_preflight.py \
  review_tests/test_practical_calibration_minimal.py \
  review_tests/test_pf_first_study_phase_boundary.py \
  -p no:cacheprovider
```

全review tests：

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src:review_response:. \
/home/AbeHiromu/venvs/trotter-common/bin/python -m pytest -q \
  review_tests -p no:cacheprovider
```

test logにはcommand、Python executable/realpath/version、開始・終了時刻、pass/fail/skip件数を記録します。
失敗時は`failed_tests`として停止し、package installやtest・科学閾値の緩和をしません。

## 成果物、commit、push、停止

新規outputには少なくとも次を保存します。

- `python_environment_identity.json`
- `local_source_preflight.json`
- `gpu_environment.json`
- `independence_search_inventory.json`
- `independence_search.log`
- `source_identity_audit.json`
- `focused_tests.log`
- `all_review_tests.log`
- `decision.json`
- `manifest.json`
- 全gate合格時だけ`PREFLIGHT_ONLY_COMPLETE`

`decision.json`と`manifest.json`には、parent/v1.1/v1.2 commitとhash、raw/canonical origin、
Python requested/resolved pathとhash、prefix、package versions、過去2停止記録を保存したこと、
全gate結果を記録します。

全gate合格時だけstatusを`preflight_pass_phase_a_not_authorized`とし、
`PREFLIGHT_ONLY_COMPLETE`を作ります。これはPhase A許可markerではありません。

pickle、npy、`.runtime`、archive展開物をcommitしません。軽量auditとtest logだけを新規branchへ
commitします。Codexにpush権限がなければ、それを科学的gate失敗にせず、local result commitを固定して
停止し、ユーザーが実行する次のnon-force commandを正確に報告してください。

```bash
git push -u origin gpu-second-study-safe-time-domain-preflight-v1-2-20260927
```

最終報告にはbranch、result commit、protocol/v1.1/v1.2 amendment hash、67 checks、H01/P03、
独立性検索scope/hit分類、Python environment identity、package/CUDA/GPU memory、focused/full tests、
go/no-go、未解決事項を示してください。

報告後に停止してください。Phase A、Phase B、新規分子生成、proxy、direct truth、threshold調整、
別PF・別分子へ進まないでください。
