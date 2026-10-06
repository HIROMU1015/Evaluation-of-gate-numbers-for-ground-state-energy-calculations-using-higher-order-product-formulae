# Algorithm design

## 定義と実装

元実装の`echo_proxies`は`W=exp(-iHt)U_P(t)`、`U_P≈exp(+iHt)`、`g=Im<psi|W|psi>/t`である。`A=(W-W†)/(2it)`はHermitianで、expectationは同じg。imag proxyはunwrapを必要としない。正負のUは独立構築するが、`W(-t)`を`W(t)†`と置いてはいけない。adjointは`U_P(t)† exp(+iHt)`の順序。

正規化されたCISDだけから`E=<psi|H|psi>`、`Q=I-psi psi†`、`r=Q(H-E)psi`を構築する。MGSを2pass行うArnoldiにより`r,Lr,L²r,...`から共有Zを作る。`L=Q(H-E)Q`。これは指定`r,QHr,QH²r,...`と同じprefix spanを持つ：shift項は既存方向、投影で失われるpsi方向をHへ戻すと`QHpsi=r`となり既存spanへ戻る。

各m=1,2,4,8で`B_m=LZ_m`を既存`HZ`から切り出す。時間に依存しないBをthin SVDで一度だけfactorizeし、各signed timeの`a=QApsi`へ適用する。`c=B_m^+ a`は凍結cutoffでのminimum-norm解、`z=Z_m c`。推定量は

\[
g_{resp}^{(m)}=g_{base}-2\operatorname{Re}(z^\dagger r).
\]

`L_m=Z†B`、`a_m=Z†a`は別途記録するがsolveへ置換しない。例えば`L=[[2,1],[1,3]], Z=(1,0)^T, a=(0,1)^T`ではfull-residual解はc=0.2、投影式解はc=0となる。ユーザー承認により前者を固定した。

Ritz比較は同じ`V=[psi,Z_m]`、同じcached `Hpsi,HZ`から`H_m=V†HV`を作る。最大9×9のlowest Ritz pairを解き、正規化した`phi=Vc`上でbare observableを評価する。m8がprimary、m1/2/4はdiagnostic。小行列の最低pairであり、full36×36 Hのground solveは行わない。

## Target invarianceと一次感度

`X=z psi†-psi z†`はanti-Hermitian、`[H,X]`はHermitian。z⊥psiなら

\[
\langle\psi|[H,X]|\psi\rangle=2\operatorname{Re}(z^\dagger r).
\]

任意のfixed Xとexact H-eigenstate Enについて`<En|[H,X]|En>=0`。従って`Atilde=A-[H,X]`は**そのfixed演算子のexact-eigenstate expectation**を変えない。これはsynthetic全eigenstatesで検証した。近似psiのg_respがexact ground値へ等しいという主張ではない。

isolated target eigenstate付近で、full responseが解け、gapが非零なら、responseは一次のstate-error couplingを打ち消す。二準位非可換observableのcentral derivativeでこれを検証した。有限subspaceの残差、SVD切り捨て、近似E、二次のpopulation誤差、近接準位は補正後にも残る。小さいresponse residualはobservable biasのcertificateではない。fitとexact-state proxy−directの差も残り、反対符号の相殺を崩す可能性がある。

## 可換性に関する承認済み修正

元要求§19.2のunconditional commuting-zero条件は一般に成立しない。`H=A=diag(0,1)`、`psi=(sqrt(.9),sqrt(.1))`では`E=.1`、`r=.3 chi`、`L chi=.8 chi`、`z=.375 chi`。補正は0.225、bare=.1、response=−.125となり、exact groundの0より絶対誤差が増える。可換なので元bareの一次感度は既にゼロでも、二次のpopulation correctionはゼロにならない。

ユーザーは式維持とtest修正を承認した。`A=alpha I`ならa=0でz=0、exact inputならr=0で補正ゼロを検証する。一般可換例は**worseningの可能性を示す反例テスト**として残す。可換性を判定して補正を止める追加分岐は設けない。

## 実装上の境界

Phase AはH、group、CISDのallowlistだけをdecodeする将来adapterに限定する。古い`load_h4_source`はexact state/energy、controlled states、D4/D6/D8、group eigendecompositionへアクセスするため使用不可。exact-overlapによるCISD phase alignmentも不要。raw canonical hash確認後にCISDを一度だけ正規化する。global phaseはproxyへ影響しない。

現在のkernelsはsynthetic dim≤16だけを受ける。Phase A builderはtruthの引数を持たず、Phase Bモジュールをimportしない。Phase Bはverified committed blob/hashを照合したfreezeを読む。これはデータ流の実装境界であり、任意のPython実行による意図的な迂回を防ぐsecurity sandboxという主張ではない。
