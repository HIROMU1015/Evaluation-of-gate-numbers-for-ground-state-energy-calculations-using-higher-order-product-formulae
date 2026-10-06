# Production adapter design

Normative authority: [`response_pilot_protocol.json`](../pf_first_study_response_pilot_phase05_20261006/response_pilot_protocol.json), frozen commit `48f3d889d096f2fe3af55c200a757747df384941`, SHA-256 `38ddb97f8f3c0bcc155eb9be23fb650772db264b6da0686f905a1d7d8ba482e3`。本実装は接続・実行管理だけを追加し、既存science仕様を変更しない。

## Data flow

`phase06_contract.py` → `phase06_inputs.py` → `phase06_backend.py` / `phase06_kernels.py` → `phase06_phase_a.py` → `phase06_freeze.py`。Phase B readerは別module。Phase A kernel/input/backendはPhase Bをimportしない。

`PhaseAData`の配列fieldはH・ordered groups・CISDだけ。既存mixed loaderは使用しない。NPZ全bytesのSHA-256とGit blobをdecode前に照合し、member allowlistをZipFile.open前に確認する。15 memberのcanonical hash、`<c16`、shapeをdecode後に照合しread-only化する。36次元sector metadata、ascending basis order、13 group順序、group sequence hashはPhase0.5 identityに固定。元bundleのpublication commitとgeneration dirty-worktree headは別fieldで記録する。

identity-only loaderにはnormalization、norm、H matvec、PF、Ritz、fitがない。norm/group-sum/Hermiticity等の科学的入力gateは承認後のPhase A開始時に行う。

## Echo backend

scipy 1.14.1 `expm` scaling/Padé、numpy 1.26.4、complex128。protocolの7 S2 weightsをそのまま用い、各unique weight（4個）についてgroups 0..11 half、12 full、11..0 halfを左乗算し、7 blocksも左乗算する。block cacheは単一signed build内だけ。正負時刻のUとexp(-iHt)を独立構築する。

forward: `exp(-iHt) @ (U(t) @ state)`。adjoint: `U(t)† @ (exp(+iHt) @ state)`。`W(-t)`をadjointに代用しない。unitarityと`U(-t)`対`U(t)†`は固定gateでauditする。synthetic比較は同じ固定sequenceの独立spectral S2 builderを用いる。production full-H/group eigensolveやSchurは使わない。

## Response / Ritz

`phase06_kernels.py`はPhase0.5 mathematical kernelsをproduction dimension≤36へ接続した実装。変更はdomain guard、ledger、scalar診断の接続で、Phase0.5原本は保存する。E、Q、r、L、a、residual-start Arnoldi span、m=1/2/4/8、primary8を維持。MGS2 passes、psi投影、deterministic phase、64eps rank threshold、first rejection prefix stop、thin truncated SVDを維持する。

primary solveはfull `B=LZ` に対するminimum-norm least-squares。`L_m`・`a_m`はprivate診断だけ。`g_response=g_base−2Re(z†r)`。replacement、ridge、Galerkin切替、第三MGS pass、parameter searchはない。commuting H,Aで一般にzero correctionとはしない。ユーザー承認済みPhase0.5 amendmentsを継承する。

Ritzは同じcached Hpsi/HZから`V=[psi,Z_m]`、`V†HV`を構築し、最大9次元small eigensolveだけを行う。固定Hermiticity gate、lowest-subspace tie rule、deterministic phase、rank0 original-state fallbackを維持する。

## Proxy / fit / diagnostics

9 arms: A0 bare、A1 response8、A2 Ritz8、response1/2/4、Ritz1/2/4。22 signed coordinatesは固定。A3はPhase B専用。全armsが同じfixed positive-five OLS、column scaling、no intercept、quality/condition gateを使う。evenized/odd fitsは診断のみ。noiseはunitarity/|t|、complete replay difference、50eps max(||H||2,1/|t|)の最大値でtruthを使用しない。

Phase Aはstrict scalar JSON schemaに従い、source/code/protocol、rank/threshold/orthogonality、response residual/SVD、Ritz、noise、27 fits、108 predictions、全action countersを保存する。raw projected matricesとvectors/statesは公開artifactに含めない。L_m/a_mはrepository外private directoryへ保存する。

## Execution gates

production domainはphase-specific承認recordがなければscience演算前に停止する。productionをsyntheticとして実行するとdomain mismatchで停止。production CLIはcodeとschemaがHEAD blobと一致することも演算前に確認する。approval recordは別途承認を記録するためのworkflow gateで、人間の承認を暗号学的に証明する機構ではない。

H4の実行結果と実行時間は未取得。今回のready判定は実装とidentity/synthetic testsの完了を意味し、science gate通過や研究claimを意味しない。
