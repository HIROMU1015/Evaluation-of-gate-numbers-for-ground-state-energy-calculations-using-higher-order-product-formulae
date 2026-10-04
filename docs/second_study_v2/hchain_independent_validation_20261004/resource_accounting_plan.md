# Resource accounting plan

Design only。実測H-chain calibration costやcombined H1 costは今回ない。量子continuous rotation proxyと古典秒を加算しない。

## Ledger separation

各system / coordinateに、reference preparation、candidate cheap、M1、H1 conditional acquisition、truth scorer、shared preprocessingを別ledgerで残す。

- CISD verification/generation：matrix/subspace preparation、eigensolve、norm/residual diagnostics、state/hash保存、wall/RSS。
- reference grid：最大34時刻/system、PF vector actionとH exponential actionを各1/未取得点。grid取得最大102ずつ。candidateの9作用とは別枠。
- candidate cheap：PF state actions最大9、H exponential actions最大9。expm_multiply内部H matvecは継承helperでは未露出でありunknownとする。H exponential actionをH matvec一回と数えない。
- M1：PF per-vector actions / PF block calls / H matvecsを別々に保存。H2 12、H4 24、H6 24、合計最大60ずつ。block callでvector数を隠さない。
- PF component materialization、sparse state multiplies、group-spectrum preprocessing、cached gate bytes、basis bytes、inner products、2-pass reorthogonalizationを別列とする。
- PF sequenceのK=108/2556/14344は量子step Pauli rotation数であり、上記classical action数ではない。
- full PF/Schur truthは最大9座標、computed/reused、new_target_phase_gap_countを別会計。同一点のgap取得を「計算なしreuse」と偽らない。ground preparationは別承認が必要。

## Shared H1 execution proposal

qをcheap-onlyでfreezeし、q=1 systemのM1取得を先に行い、H1 final actionをfreezeする。その後、always-M1比較用にq=0 systemを補完する。同じq=1 M1 chainを比較用にreuseし、全60上限を維持する。cheapのPF結果とArnoldi第一作用を同一とみなすcost discountは事前検証なしに行わない。

H1のactual combined intervalをcheap開始からq判定、条件付きspectral取得、final decision freezeまで測る。state/PF preprocessingはshared costとして別タイマーで持つ。H1にq=0 M1を先に取得・開示しない。比較用補完が終わるまで同じprocessで続けても、補完時間はH1 costに含めない。

C_H1=C_shared+C_cheap+q*C_spectral_given_cheap+C_decisionを保持する。system別timingと全体peak RSSを併記し、RSS peakを足し合わせない。C_spectral_given_cheapとstandalone C_spectralを同一視しない。

この案は実装されておらず、boundary/タイマー/counter検証が必要。別fresh H1 runを追加すれば60上限を超えるため別scope承認が必要。

## Comparator limitations

共有batchのcomparator completion時間はindependent cold standalone always-M1 timingではない。shared/cache warmness、execution order、process peak RSSを明示する。single-runで実測できないstandalone wallはnot_measured、比較不能ならcombined_cost_not_evaluableとする。

S1Aのsaved-arm replay envelopeは測定されたcombined costの上下限ではない。新H-chain実測の数学的保証されたlower/upperとして転用しない。classical superiorityをwallだけで認定できないときは、conditional acquisition system数とPF/H作用数を直接比較し、wall advantageは未確立とする。

## Resource ceiling and no rescue

CPU process1、BLAS thread各1、peak RSS4 GiB、各準備/cheap/M1/scorer stage1800秒以内はD2からの提案枠。cache/preprocessingも計上し、実行reviewでPython/backend/sourceを固定する。これは今回の実行承認ではない。

上限・数値・access gate失敗時は停止、別backend/GPUへの切替・追加chain・追加prefix・threshold変更はしない。科学結果を見てresource会計を変更しない。
