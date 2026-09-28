# D1後の研究方針：spectral recoverabilityと情報費用

作成日: 2026-09-28

## 結論

P-SPEC-6/D1は、HClの既存6座標について、exact-ground由来のPF spectral measureが少数の非対象clusterで圧縮できることを示した。しかし、これは取得可能な近似状態から同じ情報を安定かつ低費用で回収できることを示していない。

次の研究課題は、有限時間PF誤差について次を分離して評価することである。

1. 少数成分への圧縮可能性。
2. truth-freeな近似状態と有限回の作用からの回収可能性。
3. ground reference、PF branch、phase aliasを同定できる範囲。
4. 数値誤差、状態置換誤差、reference誤差を含む精度。
5. 追加古典費用と凍結量子予算のtrade-off。

最初の方法候補は、古典explicit-vectorの再直交化unitary Arnoldi / small-subspace法とする。Arnoldi自体を新規手法とは主張しない。全D1 top-Kの復元ではなく、目的PF固有枝の位相と有限時間energy shiftを主目的にする。

## 固定evidenceとprovenance

- D1 implementation commit: `03747a2ca85c46d593b4fcf1e4969fd45005e37e`
- reviewed D1 execution-prompt bundle: `e0aad5a06eb3a8f5385efd8c6129f4e74f35e5cc`
- D1 result commit: `94ba9d6f71c1318ee03b85498e7a0b8b23abfd7a`
- D1 result parent: `03747a2ca85c46d593b4fcf1e4969fd45005e37e`
- D0-frozen P-SPEC-6 protocol SHA-256: `44d69fa249a075a6dd863ddc518a5d93da7e6699d4f888037c8476e68e5cdb9e`
- D1 authorization SHA-256: `5ec7fc1d041f3b2c8d1ea9d1e5418a7a6e9c7d9773c96532d826a003714cc186`
- D1 output manifest SHA-256: `44b3bc7a702f50693c7b6e17e2f98d8af222b0b430d3fb6c136200fa1dc18c05`

GPU側のresult commitはimplementation commitの直接の子であり、reviewed execution-prompt bundleの子ではない。固定hashと科学結果は整合しているが、この手続上のprovenance差を隠さない。

## D1から引き継がないもの

D1のKはtarget clusterを除いたnon-target clusterの保持数である。Krylov次元、PF作用回数、QPE cost式の`K_current_m3`とは別である。

次はD2 predictorの入力にしない。

- exact ground stateまたはexact ground energy。
- D1 spectral weights、target cluster ID、true phase gap、`q_omit`。
- Phase B direct shift、branch label、ground overlap。
- R1 exact-state proxyまたはD1/R1のpass/fail label。
- scorerが生成した値。

D1の`2*q_omit/t`は事後診断であり、D2 estimatorの保証にはしない。

## D2-Aの位置付け

D2-Aは既使用のHCl 6座標によるdevelopment feasibilityであり、holdoutではない。元CISD、元Hamiltonian、`current_m3`、既存時刻だけを用いる。

主計算は1座標あたり最大8回のPF state actionと8回のHamiltonian matvecで、一つのArnoldi chainから`m=1,2,4,8`のprefixを得る。full-H diagonalization、full-PF construction/eigendecomposition、GPU、新時刻、threshold fittingはpredictorで禁止する。

predictorとscorerは別process・別entry pointにする。predictorはallowlist inputだけを読み、prediction artifactを閉じてSHA-256を固定する。scorerはその後だけ既存truthを開き、prediction、branch、`e_use`、`B`を変更できない。

PF state action、Hamiltonian matvec、Hamiltonian exponential action、component-gate materialization、sparse multiply、block call、per-vector action、再直交化、memoryを別々に記録する。

## D2-A後の停止と三分岐

D2-Aの全結果をcommitして停止する。D2-Bは自動的に許可しない。

- truth-freeに目的枝を安定取得でき、凍結予算が安全で費用も現実的: D2-Bを別承認で検討する。
- HClでは取得可能だが費用、conditioning、reference幅で不利: calibration information costとquantum marginの限界研究を検討する。
- branch、reference、conditioningの根本gateが不成立: spectral/Arnoldi routeを閉じる。

第二研究の`complete_no_benefit`は変更しない。第一研究の完成条件にも追加しない。
