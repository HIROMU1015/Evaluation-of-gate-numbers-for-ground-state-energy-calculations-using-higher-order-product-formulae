# GPUサーバー側Codexへの実行依頼：第二研究 safe-time-domain Phase Bのみ

第二研究のPhase Aはtruthを開かず完了し、予測・coordinate planがcommit、push、SHA-256固定されました。
ローカル側の独立境界確認も合格しています。今回は固定済み42 coordinatesに対する
**Phase Bを一度だけ実行**し、4 strategyを採点してください。

Phase A再実行、予測・selector・threshold変更、追加proxy、別PF・別分子・別basis・別精度、追加実験は
許可しません。`complete_no_benefit`も正式な完了結果です。結果を見た後に再調整しないでください。

## 固定identity

- protocol commit：`804331ecc976b83ae880940719706c11999247bc`
- protocol SHA-256：
  `a6290b107ebbf93f7c0ee3bc383208862c51e37603a670625091e15472d4584b`
- original runner commit：`e86e694805e8fcbc63659f7073eea95f67b8f435`
- Phase A parent bundle：`bbc063a05074260930860ef862d7e24bd81e3878`
- Phase A result commit：`efea5fe0718c2c2623935949460498da066bdec3`
- Phase A result branch：`gpu-second-study-safe-time-domain-phase-a-20260927`
- Phase A merge commit：`51215a7b93cadc1ee2278c0285746a1db60f5387`
- independent boundary audit commit：
  `1de4813915cdfb5d74a6813349f58983f9cdf8c8`
- Phase B execution bundle commit：
  `d4dd42fd107ac9fb90547a190a0c7080484ee667`
- boundary audit：
  `review_response/second_study_safe_time_domain_phase_a_boundary_audit.json`
- boundary audit SHA-256：
  `4b3de286c350afea2c00e822799edd54b52864bbbd219de3c389eece6639fc1a`
- Phase B runner：`review_response/run_second_study_safe_time_domain_phase_b.py`
- Phase B runner SHA-256：
  `0bfefe181421171395572de8d25f441577bde604c18dcdd5d851def9a86a3d50`
- prediction SHA-256：
  `3406d2f69237d95b14be298059f777df3fbd5043446add2c31559bf902a34b83`
- Phase A manifest SHA-256：
  `ce8f6206242b1ece6114854e61ed703422bd8a45f874ef69e100d20456b8bb48`
- Phase A runtime inventory SHA-256：
  `5dbe617f37dcfd4274fa5f89eddf6167ffe62a3816200bec6eb66f9e49e73d91`
- formal preflight v1.4 result commit：
  `2b37191594d7f79565314a5dad0d889f78aec504`
- PF：`current_m3`だけ
- 情報源：`multiple_window_consistency`だけ

## 保存・読み取り専用にするPhase A

Phase Aのtracked成果物は新しいPhase B worktreeにもcommit経由で存在します。しかし、Phase Bで読む
system cacheは、Phase A worktreeに保存された次の絶対pathだけを使用してください。

```text
/home/AbeHiromu/worktrees/gpu-second-study-safe-time-domain-phase-a-20260927/artifacts/server_second_study_safe_time_domain_phase_a_20260927_e86e694
```

その`.runtime`は56 files、113,469,289 bytesです。移動、コピー、再生成、修正、削除、再manifest化を
しません。Phase B runnerはdirect計算前に、全relative/absolute path、file set、byte count、総bytes、
SHA-256をcommitted `runtime_hash_inventory.json`と照合します。一件でも不一致なら停止します。

Phase A tracked artifactのGit上の相対pathは次です。

```text
artifacts/server_second_study_safe_time_domain_phase_a_20260927_e86e694
```

## branchとworktree

既存worktree、Phase A runtime、過去outputを変更せず、まず次を確認してください。

```bash
git fetch origin --prune
git cat-file -e efea5fe0718c2c2623935949460498da066bdec3^{commit}
git cat-file -e d4dd42fd107ac9fb90547a190a0c7080484ee667^{commit}
git merge-base --is-ancestor \
  804331ecc976b83ae880940719706c11999247bc \
  d4dd42fd107ac9fb90547a190a0c7080484ee667
git merge-base --is-ancestor \
  efea5fe0718c2c2623935949460498da066bdec3 \
  d4dd42fd107ac9fb90547a190a0c7080484ee667
git branch -r --contains efea5fe0718c2c2623935949460498da066bdec3
```

Phase B execution bundle `d4dd42f...`から独立worktreeと新規branchを作ります。推奨名は

`gpu-second-study-safe-time-domain-phase-b-20260928`

です。同名があれば上書きせず連番を付けます。既存worktreeをreset、clean、stashせず、mainへ
merge・force-pushしません。

## 固定process environment

formal preflight v1.4およびPhase Aと同じenvironmentを使います。

Python：

`/home/AbeHiromu/venvs/trotter-common/bin/python`

`PYTHONPATH`：

```text
src:review_response:.:/home/AbeHiromu/projects/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/venv/lib/python3.12/site-packages
```

`LD_LIBRARY_PATH`：

```text
/home/AbeHiromu/venvs/trotter-common/lib/python3.12/site-packages/nvidia/nvjitlink/lib:/home/AbeHiromu/venvs/trotter-common/lib/python3.12/site-packages/nvidia/cusparse/lib:/home/AbeHiromu/venvs/trotter-common/lib/python3.12/site-packages/nvidia/cusolver/lib:/home/AbeHiromu/venvs/trotter-common/lib/python3.12/site-packages/nvidia/cublas/lib:/home/AbeHiromu/venvs/trotter-common/lib/python3.12/site-packages/nvidia/cuda_runtime/lib
```

全commandで継承値をappendせず置換し、`PYTHONNOUSERSITE=1`、`PYTHONDONTWRITEBYTECODE=1`を
設定します。virtualenvをactivateせず、package/library、CUDA、driver、shell設定を変更しません。

## direct計算前gate

1. HEADにprotocol、formal preflight v1.4、Phase A result、boundary audit、Phase B bundleが全て含まれる。
2. protocol、boundary audit、Phase B runner、prediction、Phase A manifest/runtime inventoryのhashが一致する。
3. Phase A result commitがoriginに存在し、tracked artifactがcommit blobとbyte-identicalである。
4. frozen conditionはexact 4、strategyは各exact 4、PFは全件`current_m3`である。
5. Phase A oracle/direct/exact/GPU countsが全て0で、42 coordinatesが固定済みである。
6. Phase A `.runtime` 56 filesがinventoryと完全一致し、system cache 4件のhashも一致する。
7. formal preflight v1.4のsource/environment/independence gateが引き続き一致する。
8. GPU 0が存在し、空きmemoryが8 GiB以上である。他processを停止・signalしない。
9. 新規Phase B outputが存在しない。旧direct cache、第一研究cache、別run cacheを再利用しない。
10. 下記focused/full testsが合格する。

fixed focused tests：

```bash
PYTHONNOUSERSITE=1 PYTHONDONTWRITEBYTECODE=1 \
PYTHONPATH="src:review_response:.:/home/AbeHiromu/projects/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/venv/lib/python3.12/site-packages" \
LD_LIBRARY_PATH="/home/AbeHiromu/venvs/trotter-common/lib/python3.12/site-packages/nvidia/nvjitlink/lib:/home/AbeHiromu/venvs/trotter-common/lib/python3.12/site-packages/nvidia/cusparse/lib:/home/AbeHiromu/venvs/trotter-common/lib/python3.12/site-packages/nvidia/cusolver/lib:/home/AbeHiromu/venvs/trotter-common/lib/python3.12/site-packages/nvidia/cublas/lib:/home/AbeHiromu/venvs/trotter-common/lib/python3.12/site-packages/nvidia/cuda_runtime/lib" \
/home/AbeHiromu/venvs/trotter-common/bin/python -m pytest -q -rs \
  review_tests/test_second_study_safe_time_domain_protocol.py \
  review_tests/test_second_study_safe_time_domain_preflight.py \
  review_tests/test_second_study_safe_time_domain_execution.py \
  review_tests/test_practical_calibration_minimal.py \
  review_tests/test_pf_first_study_phase_boundary.py \
  -p no:cacheprovider
```

続けて同じenvironmentで全`review_tests`を実行します。focusedはfail/skip 0、fullはfail 0とし、
`review_tests/test_pennylane_bch.py`の任意依存`pennylane`だけを最大1 skip許可します。

## 固定direct plan

- independent condition：4。
- candidate grid：各9。
- original current selection：dedup後に必要なものだけ追加。
- uniform new anchor：各条件1、合計4。
- total unique direct coordinates：42、上限44。
- anchor：`0.5 * min(candidate-grid coordinates and original current selection)`。
- anchorだけexact-ground overlap最大の枝で初期化。
- 残りは時刻昇順にprevious-vector overlap最大で追跡。
- 各点で独立ground-overlap最大枝との一致も検査。
- interpolation、continuous global oracle、追加座標は使用しない。

数値gateは固定です。

- eigenpair residual `<=1e-10`。
- unitarity Frobenius residual `<=1e-10`。
- anchor ground overlap `>=0.9`。
- tracked previous overlap `>=0.9`。
- 全tracked ground overlap `>=0.9`。
- phase gap `>1e-8 rad`。
- branch disagreement 0。

## Phase B実行

初回outputは次を使います。

`artifacts/server_second_study_safe_time_domain_phase_b_20260928_d4dd42f/`

初回実行前にこのdirectoryが存在する場合は連番を付けます。一度実行を開始した後は別outputへ切り替えず、
中断時だけ同じcommand・同じoutputを再実行できます。同一runの`.runtime/run_identity.json`と、固定cache
keyが一致する`.runtime/direct_cache/**/*.pkl`だけが再開時に許可されます。その他のfile、別identity、
`.pkl.tmp`があれば停止します。

単一GPU 0、単一processで実行します。

```bash
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 \
PYTHONNOUSERSITE=1 PYTHONDONTWRITEBYTECODE=1 \
PYTHONPATH="src:review_response:.:/home/AbeHiromu/projects/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/venv/lib/python3.12/site-packages" \
LD_LIBRARY_PATH="/home/AbeHiromu/venvs/trotter-common/lib/python3.12/site-packages/nvidia/nvjitlink/lib:/home/AbeHiromu/venvs/trotter-common/lib/python3.12/site-packages/nvidia/cusparse/lib:/home/AbeHiromu/venvs/trotter-common/lib/python3.12/site-packages/nvidia/cusolver/lib:/home/AbeHiromu/venvs/trotter-common/lib/python3.12/site-packages/nvidia/cublas/lib:/home/AbeHiromu/venvs/trotter-common/lib/python3.12/site-packages/nvidia/cuda_runtime/lib" \
/home/AbeHiromu/venvs/trotter-common/bin/python -u \
  review_response/run_second_study_safe_time_domain_phase_b.py \
  --project-root "$PWD" \
  --protocol review_response/second_study_safe_time_domain_protocol.json \
  --preflight-root artifacts/server_second_study_safe_time_domain_preflight_v1_4_20260927_9e0afa0 \
  --phase-a-root /home/AbeHiromu/worktrees/gpu-second-study-safe-time-domain-phase-a-20260927/artifacts/server_second_study_safe_time_domain_phase_a_20260927_e86e694 \
  --phase-a-commit efea5fe0718c2c2623935949460498da066bdec3 \
  --phase-a-artifact-relative artifacts/server_second_study_safe_time_domain_phase_a_20260927_e86e694 \
  --backend gpu \
  --gpu-id 0 \
  --processes 1 \
  --output artifacts/server_second_study_safe_time_domain_phase_b_20260928_d4dd42f
```

実行時間、CPU peak RSS、GPU 0 peak memoryを外部monitorでも記録してください。monitorは計算内容へ介入せず、
他processを停止・signalしません。

## 判定と停止規則

全source/numerical gate合格時だけ`complete_with_benefit`または`complete_no_benefit`と`COMPLETE`を
許します。benefit条件はprotocol記載の全条件をANDで評価します。改善しない場合も
`complete_no_benefit`として保存し、threshold、時刻列、truncation、budget、ruleを再調整しません。

数値gate失敗時は`failed_numerical_validation`として停止し、`COMPLETE`を作りません。閾値を緩めたり、
枝選択・anchor・追加時刻を変えたりしません。source、Phase A/runtime identity、environment、cache、testが
失敗した場合はdirect計算前に停止してください。

## 結果検証、commit、push

実行後、同じfocused/full testsを再実行し、logを保存します。次を照合してください。

- prediction hashが`3406d2f...34b83`のままである。
- direct pointsがexact 42、condition 4、anchor 4である。
- 初回runならcomputed 42、reused 0である。中断再開ならcomputed+reused=42で、全reuseが同一run keyである。
- numerical gateと全strategy scoringが固定protocolどおりである。
- current fallback、equal-information baseline、multiple-window rule、uncapped counterfactualを分離している。
- safety/miss、coverage/rejection、frozen budget、selection/frozen-budget regret、classical information countsを
  記録している。
- `COMPLETE`はcomplete status時だけ存在する。
- manifest内fileのSHA-256が一致する。

pickle、npy、`.runtime`、selected vector、archive展開物をcommitしません。軽量成果物、resource/test logを
Phase B branchへcommitし、originへ新規non-force pushしてください。push権限がなければlocal result commit
で停止し、正確な`git push -u origin <actual-branch>`を報告します。

最終報告には次を示してください。

- branch、Phase B bundle/result commit、protocol/prediction/manifest hash。
- 42 direct pointsと4 anchorの時刻、computed/reused内訳。
- 最大eigenpair/unitarity residual、最小anchor ground overlap、最小previous/ground overlap、最小phase gap、
  branch disagreement数。
- 4 strategyの安全数、coverage、条件別・aggregate frozen budget、平均/最大selection regret、
  frozen-budget regret、equal-informationとの差。
- 全benefit checkと`complete_with_benefit`/`complete_no_benefit`/failure判定。
- wall/CPU/GPU時間、CPU/GPU peak memory、focused/full test件数、未解決事項。

報告後に停止してください。再調整、追加diagnostic、別PF・別分子・別basis・別精度、第三研究へ進まないで
ください。
