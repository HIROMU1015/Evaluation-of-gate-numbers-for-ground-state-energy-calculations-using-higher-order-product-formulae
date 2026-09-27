# GPUサーバー側Codexへの再実行依頼：第二研究preflight v1.1のみ

初回preflightは科学計算前のsource identity gateで停止し、67 checks中66件が合格しました。
唯一の失敗は、同一GitHub repositoryに対するSSH URL期待値とHTTPS URL実測値の文字列差です。
初回branch、commit、outputを変更せず保存し、transport表記だけを厳密に正規化するv1.1で
**preflight全体だけを一度再実行**してください。

Phase A、Phase B、新規Hamiltonian、RHF/CISD、group spectrum、proxy、PF action、direct truthは
引き続き許可しません。preflight完了後に停止してください。

## 固定版

- protocol commit：`804331ecc976b83ae880940719706c11999247bc`
- protocol SHA-256：
  `a6290b107ebbf93f7c0ee3bc383208862c51e37603a670625091e15472d4584b`
- parent preflight実装commit：`3a0dd5684abd7039935c02c14b44e3cb24bb149a`
- v1.1実装commit：`0f3381863ed0eb0a31b59b8018e816bebe3840f7`
- v1.1 amendment：
  `review_response/second_study_safe_time_domain_preflight_amendment_v1_1.json`
- amendment SHA-256：
  `218d325d2b13eea24196302a52e4a1a3e34ae92973518b61835bf2ad3974759d`
- runner：`review_response/run_second_study_safe_time_domain_preflight.py`
- parent実行指示：
  `review_response/gpu_second_study_safe_time_domain_preflight_prompt.md`

## 保存する初回失敗

- branch：`gpu-second-study-safe-time-domain-preflight-20260927`
- result commit：`e1891dfd24ec5f0064b0598e51eb260073fd2b1e`
- output：
  `artifacts/server_second_study_safe_time_domain_preflight_20260927_3a0dd56/`
- status：`failed_source_identity`
- Phase A/B実行：0
- 新規科学計算：0

初回branch/outputをreset、rebase、amend、削除、変更、再利用しません。初回outputの
`local_source_preflight.json`や他のauditをv1.1 outputへコピーしません。

## v1.1で変えるもの

変更は`git:origin`のtransport正規化だけです。

- SSH SCP形式、HTTPS形式、`ssh://git@`形式からhost/owner/repositoryを抽出する。
- terminal `.git`を一つ除去し、case-insensitiveに比較する。
- 期待canonical identityは次で固定する。

```text
github.com/hiromu1015/evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae
```

- raw URLとcanonical identityの両方をauditへ記録する。
- 別host、別owner/repository、query/fragment、credential付きHTTPS、余分なpath、非対応transportは
  引き続き失敗させる。
- GPUサーバーの共有Git設定やremote URLは変更しない。

protocol JSON、分子、geometry、情報源、PF、候補時刻、threshold、停止規則、`gamma=1.01`、
`beta=1.2`は一切変更しません。

## branchとworktree

```bash
git fetch origin --prune
git cat-file -e e1891dfd24ec5f0064b0598e51eb260073fd2b1e^{commit}
git cat-file -e 0f3381863ed0eb0a31b59b8018e816bebe3840f7^{commit}
git merge-base --is-ancestor \
  804331ecc976b83ae880940719706c11999247bc \
  0f3381863ed0eb0a31b59b8018e816bebe3840f7
git merge-base --is-ancestor \
  3a0dd5684abd7039935c02c14b44e3cb24bb149a \
  0f3381863ed0eb0a31b59b8018e816bebe3840f7
```

v1.1実装commitから独立worktreeと新規branchを作ります。推奨名は

`gpu-second-study-safe-time-domain-preflight-v1-1-20260927`

です。同名があれば上書きせず連番を付けます。既存worktreeをreset、clean、stashしません。

## 新規outputとsource gate

新規outputは次を推奨します。

`artifacts/server_second_study_safe_time_domain_preflight_v1_1_20260927_0f33818/`

同名があれば連番を付け、既存directoryへ書きません。

GPUサーバーには`python`がなく`/usr/bin/python3`が存在することが初回に確認済みです。今回の全command
では`/usr/bin/python3`を明示し、`sys.executable`とversionをauditへ記録してください。packageを
install/updateせず、既存環境だけを使います。

```bash
sha256sum review_response/second_study_safe_time_domain_protocol.json
sha256sum review_response/second_study_safe_time_domain_preflight_amendment_v1_1.json

PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src:review_response:. \
/usr/bin/python3 review_response/run_second_study_safe_time_domain_preflight.py \
  --project-root "$PWD" \
  --output artifacts/server_second_study_safe_time_domain_preflight_v1_1_20260927_0f33818/local_source_preflight.json
```

次を照合します。

- schemaが`second_study_safe_time_domain_local_preflight_v1_1`。
- protocol/amendment hashが固定値と一致。
- raw originは実測値のまま保存。
- `origin_repository_identity`が固定canonical identityと一致。
- `origin_identity_rule`が`github_transport_normalization_v1_1`。
- source checksが67/67合格。
- Phase A/B authorizationがfalse、新規計算countが全て0。

一つでも失敗すれば`failed_source_identity`として停止し、remote URLや共有設定を変更しません。

## source gate合格後に実行する残りのpreflight

source checksが67/67合格した場合だけ、parent実行指示の次の項目を省略せず実施します。

1. H01/P03元成果物の読み取り専用identity照合。
2. 全worktree、全local/remote-tracking branch、tag、untracked artifact、binary、log、archiveを対象にした
   LiF/HCl独立性検索。
3. Python package、CUDA/CuPy import、`nvidia-smi`、GPU free memory 8 GiB以上の確認。
4. focused testsと全`review_tests`。
5. 軽量audit、decision、manifestの作成とhash照合。

初回失敗branch/output、v1.1 amendment、今回のretry promptに含まれるLiF/HCl文字列は
planning/validation記録として個別に分類します。ただし、未知のhitや過去の独立4条件に対する数値
PF error、QPE cost、proxy response、direct truthを自動的にplanning扱いしません。一件でも数値結果を
発見したら`no_go_independence_contaminated`として停止し、条件を差し替えません。

focused testsは次を実行します。

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src:review_response:. \
/usr/bin/python3 -m pytest -q \
  review_tests/test_second_study_safe_time_domain_protocol.py \
  review_tests/test_second_study_safe_time_domain_preflight.py \
  review_tests/test_practical_calibration_minimal.py \
  review_tests/test_pf_first_study_phase_boundary.py \
  -p no:cacheprovider
```

その後、同じ`/usr/bin/python3`で全`review_tests`を実行します。依存package不足やtest失敗時は
`failed_environment`または`failed_tests`として停止し、その場でinstallやtest緩和をしません。

## 成果物、commit、push、停止

parent指示の成果物一式に加えて、decision/manifestへ次を記録します。

- parent/v1.1 implementation commit。
- parent protocol hashとamendment hash。
- raw/canonical originとidentity-rule version。
- 初回失敗branch/commit/outputを保存したこと。
- `/usr/bin/python3`のabsolute pathとversion。

全gate合格時だけstatusを`preflight_pass_phase_a_not_authorized`とし、
`PREFLIGHT_ONLY_COMPLETE`を作ります。これはPhase A許可markerではありません。

pickle、npy、`.runtime`、archive展開物をcommitしません。軽量auditとtest logだけを新規branchへ
commitします。Codexにpush権限がなければ、それを科学的gate失敗にせず、local result commitを固定して
停止し、ユーザーが実行する次のnon-force commandを正確に報告してください。

```bash
git push -u origin gpu-second-study-safe-time-domain-preflight-v1-1-20260927
```

push後もPhase Aへ進みません。最終報告にはbranch、result commit、protocol/amendment hash、67 checks、
H01/P03、独立性検索scope/hit分類、Python/CUDA/GPU memory、focused/full tests、go/no-go、未解決事項を
示し、そこで停止してください。
