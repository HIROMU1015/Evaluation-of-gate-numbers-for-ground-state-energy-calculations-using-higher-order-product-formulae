# Complete cold replay and accounting

Phase Aは`_one_pass`を独立に2回呼ぶ。各回でCISD working copy/normalization、Hpsi/residual、MGS basis/HZ/B、distinct-prefix response thin SVD、small Ritz state、全22 signed PF/echo matrices、全proxyとresponse RHS solvesを構築する。

2回の間で共有できるのはread-only source H/groups/raw CISD、metadata、固定protocolだけ。basis object、Z/HZ/B/r/working psi、SVD U/s/Vh、PF U/echo matrices、Ritz statesはobject identityと`np.shares_memory`で非共有を検証する。proxiesとlocal S2 block cachesも各回のlocal objectとして新規生成する。rank/statusが一致しない場合は停止する。

first pass scalarとcold replay scalarの差を各armのnoise ruleへ渡す。fitはreplay後に1回のみ、9 arms × primary/evenized/odd＝27 fits。full replayを省略した一部actionの再実行や、first-pass factor/stateの再利用は行わない。

nominal rank8では各pass H9、PF forward110、adjoint22、response SVD4、RHS88、Ritz4。合計H18、forward220、adjoint44、SVD8、RHS176、Ritz8。actual dense buildはPF44、group expm4400、H expm44、matrix multiplication4708、H-norm SVD2。exact-H echo action264は別counterであり、free quantum oracleとして扱わない。

rank停止時はk=actual rank、u=distinct nonzero min(m,k)。2-pass H=2(1+k)、forward=44(1+u)、adjoint44、response/Ritz factors=2u、RHS=44u。rank0ではresponse z=0、Ritz proxy＝baseline、new Ritz state/action0。

synthetic rank8/rank1停止/rank0で、expected、implemented、first-pass counts、cold incrementsを[expected_vs_implemented_action_counts.json](expected_vs_implemented_action_counts.json)へ保存した。production H4の実際のrankやaction countは未観測。科学的結果を見てcounter scopeを変更しない。
