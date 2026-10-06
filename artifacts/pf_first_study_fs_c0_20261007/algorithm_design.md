# FS-C1予定algorithmと未完了のproduction契約

1. 元sourceのH/CISD/ordered group spectra/basisとmetadataをidentity-onlyで検証し、truth/exact ground/overlap/gapを隔離する。現在これらのprivate配列は未確認なので開始不可。
2. 元CISD training時刻、元selected t0、K、B0を元binary64値から固定する。原baselineは3点であり、「元5点」への一致は不成立。時刻・baseline定義の修正は未承認のため operational training_times=null として実行を閉じる。
3. 同じHと元CISDで E、r=Hpsi-Epsi、固定residual KrylovのZを構築。MGS2pass、phase固定、machine-precision rank stop、最大m8をPhase0.5数値規則から継承。新m1/2/4測定、m16救済なし。
4. V=[psi,Z]、cached Hpsi/HZを使い、最大9次元のlowest projected Hermitian Ritz solve。小部分空間のsolveとfull-H ground solveを混同しない。rank0は元CISDへ戻る固定規則を保持する。
5. native merged S2順序の任意vector PF actionとexact-H echoで各stateのtraining/local scalarを測定。W=exp(-iHt)U、U≈exp(+iHt)、g=Im<state|W|state>/t。arg proxy、exp(-i<H>t) surrogate、反対時刻を無断で使わない。
6. 独立cold replayはbasis/PF/echo/preprocessingを再構築し、全作用をledgerへ記録。各passのscalarと完了ledgerをprivate create-only checkpointへ先に保存する。再試行の自動承認はない。
7. cold受入れ後、2state×2systemsの主fit4回を1度だけ行う予定。f=a4*t4+a6*t6、no intercept/unweighted OLS。列2-norm scalingは新designの規則だが、元baselineはrelative-time/response scaleを使うため、binary64再現許容差の契約が必要。C0でproduction fitは行わない。
8. 全4arm、scalar診断、source/code/protocol/schema/ledgerをprivate recoveryへ保存し、それからpublic schema/write/hash/readback。predictionとscorer/sourceをcommit freeze。
9. すべてのfrozen blobを実commit/SHAと照合した後だけ、元S0 exact selected time2値をscorerへ読む。missing/duplicate/time/sign/source/branch/quality mismatchは停止。scorerはstate/PF/fitを呼ばない。
10. 各条件別のraw safety slack、numeric identification、saving、state increment、safety repairを出し停止。C2・truth追加・gamma/rank変更を自動開始しない。

`scoring_skeleton.py` はscalar専用。`score_frozen` がprediction/protocol/schema/scorer/source manifestのbyte/SHA/commit、実行中scorerの同一性、coverage/identityを先に検証してからtruth callbackを呼ぶ。productionではscience_authorized・execution_readyの両gateも必須。C0 packageではともにfalse。

Response identityは説明用syntheticのみ: B=LZ、z=Z B+ Q A psi、w=Q(B+)† Z†r、g=<A>-2Re<w|A|psi>。fixed psi/Z/B/cutoffではwはobservable/timeに依存しない。rho_lin=|psi><psi|-|psi><w|-|w><psi|は一般に非正値。full residual LSのままで、Ritz同値・一般commuting補正ゼロ・必ず改善などを主張しない。

OLS線形性: X=[t4,t6]、列scale D、X_s=X D^-1、ell(t)^T=x(t)^T D^-1 X_s+。f=ell^T y、Delta f=ell^T Delta y。f!=0で d log B/d y_i=sgn(f)ell_i/(epsilon-|f|)。代数的感度であり、model/proxy biasの上界ではない。
