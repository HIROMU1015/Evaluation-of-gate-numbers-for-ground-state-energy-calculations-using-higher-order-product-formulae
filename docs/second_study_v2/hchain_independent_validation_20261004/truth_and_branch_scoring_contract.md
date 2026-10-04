# Direct truth and scoring contract

Planning only。9座標のtruth/gap取得は将来の承認候補で、今回0件。既存truth値をpolicy/時刻の調整に使っていない。

## Source, sector and direct branch

同一Hamiltonian、population-sector basis、constant convention、PF sequence binary64、exact absolute time hexでだけreuseする。truthに必要なtarget gapがない場合は既存shiftを持っていてもcomplete tupleとはしない。nearest/interpolation、numerically-equivalentな別Hamiltonian、ULP variantは不可。

継承候補は `review_response/_pf_first_study_s0_exact_time_scoring_base.py:direct_branch_point` と first-study phase_and_branch_policy。各systemの固定3時刻を昇順処理し、最初はsame-H exact-ground overlapを最大化、以後は直前の選択枝とのcontinuityを最大化する。最大ground-overlap comparatorも別fieldで保存する。0からのground-connected候補という定義を固定し、追加の小時刻anchorは取らない。

helperは複素Schurを使用し、target eigenpair residualとunitarity、phase gap、cluster/projector overlapを保存する。degeneracy thresholdは継承値1e-8 rad。target gapがこの値以下、枝が認定不能、gap欠損、source/gauge不明ならtruth_branch_indeterminateとして、passを認定しない。helperが報告するindividual-vector continuationとprotocolのprojector continuationの差はresolved-phase例だけに限定して使い、degenerate clusterを救済しない。

継承数値gate：same-H ground residual <=1e-10、direct eigenpair residual <=1e-10、unitarity Frobenius <=1e-10。ground/previous overlap <0.9は継承warningを保存し、黙って別の枝へ置換しない。ground source/hash、実際のtruth wrapper、reuse completenessとwarning扱いはexecution review必須。

H6の200次元exact用Z2 restrictionは400次元predictor sectorと同一ではない。埋込・Hamiltonian・target対応を明示できないtruthはreuseしない。新same-H exact-ground計算の件数は未承認で、9 direct coordinate上限から推論しない。

## Quantities and units

- delta_direct：signed PF shift [Ha]。U_P~=exp(+iHt)。継承helperはarg(exp(-i*E0*t)*lambda_PF)/tを記録する。energy gauge / principal relative phase / branch provenanceを保存する。
- e_direct=abs(delta_direct)：continuous QPE予算に入れる量。signed errorをbudgetへ入れない。
- E_C=abs(delta_C-delta_direct)、E_M=abs(delta_M-delta_direct)。
- E_C/epsilon_E、E_M/epsilon_E、w_M/epsilon_E、empirical width coverage E_M<=w_Mを別fieldで保存する。
- g_phase=min principal circular target phase separation [rad]。g_E=g_phase/t [Ha]。g_chordはunit-circle eigenvalues間の距離。g_targetとg_rho_othersを交換しない。今回はgapを新しいwidthの入力に使わない。

## Representation-independent branch diagnostic

M1のみ abs(delta_M-delta_direct)<g_phase/(2*t) を保存する。abstaining predictionにも点診断は保存できるが、accepted actionとは数えない。gap非positive・非finite・未解決の場合はindeterminate。

絶対エネルギー基準のunwrap整数とground-relative shiftの整数を直接比較しない。E_PF_hat=E_H_Ritz+delta_MとE_PF_target=E0+delta_directが同一physical liftで保存できる場合はabsolute differenceを別列にする。近い点推定やgapだけでground certificateを主張しない。cheapにbranch-correct labelを付けない。

## Frozen resource scoring

safe iff abs(delta_direct)+beta*K/(t*B_frozen)<=epsilon_E。非finite、nonpositive budget/timeはinvalid。予算をceil/再計算して修正しない。B0もtruth safetyを採点し、unsafe anchorを安全なfallbackとは呼ばない。

各systemにつきB0、B1の4 arms、M1、B2、H1を比較する：selected time、frozen budget、fallback、abstention、unsafe、target met、total error、B/B0。target metはsafeかつt>T0かつB<=0.90*B0。extension呼称はextension_from_hchain_benchmark_anchor。

T0は新benchmark controlであり、HFの保存baselineを再現する義務とは違う。T0のM1 point/branch/widthとB0 safetyを必ず報告するが、保存HF truthとのreproduction gateを移植しない。

## Comparison and stop

各systemでB0→B1、B0→M1、safe B1 frontier vs M1、B2 vs H1、H1 vs always-M1、cheap vs M1 point error、acquisition costを並べる。required safe gammaは固定4値中の最小値を診断として出し、truthから新gammaを作らない。

H2/H4/H6は3systemのsize-series diagnostic。9座標を9 independent samplesにしない。scaling exponent、統計有意性、未知分子一般化、natural domain-loss recoveryを主張しない。H-chain robust_signal等の新taxonomyは今回定義しない。

計算後は事前固定predictionとformal resultを保存して研究方針レビューで停止する。新margin・新width・C1・LiF・H8・holdoutへ自動的に進まない。
