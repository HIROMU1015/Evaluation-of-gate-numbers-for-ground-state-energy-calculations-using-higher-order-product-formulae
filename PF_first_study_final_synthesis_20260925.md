# 第一研究 最終統合：S0--S4と停止判断

**確定日：2026年9月25日**  
**状態：`complete_mechanism_study_no_method_benefit`**  
**統合ブランチ：`first-study-final-synthesis-20260925`**

## 1. 最終判断

第一研究S0--S4は完了した。中核成果Aである有限時間校正の機構・信頼性解析は成立した
一方、S4で固定したoperator-sensitive二状態収束診断はpractical baselineに対する
資源効率の改善を示さなかった。S4の固定判定は`complete_no_benefit`である。

従って、今回の結果から次を確定する。

1. 状態置換、exact-state proxy--PF固有値差、有限時間model fit誤差を分離する機構研究を
   第一研究の中核成果とする。
2. 1%余裕付き予算の安全性とoracle referenceに対するregretを別の目的量として扱う。
3. S4の診断を調整して方法論上の成功へ見せない。
4. S4のbenefit条件が不成立だったため、S5の未使用active-space分子評価へ進まない。
5. 次の作業は追加計算ではなく、論文、図、主張台帳、再現パッケージの統合とする。

機械可読な判断は
[`PF_first_study_final_decision_20260925.json`](PF_first_study_final_decision_20260925.json)
に保存した。

## 2. 証拠の世代と固定source

S3は当時の統合報告
[`PF_first_study_results_20260925.md`](PF_first_study_results_20260925.md)のbyte hashを
source identityとして固定している。そのため同ファイルは変更せず、本書をS4までの
新しい統合層とする。

| Stage | status | 固定commit | 成果物 |
|---|---|---|---|
| S0 exact-time v1.1 | `complete_exact_time_scoring` | `cc3626a8135b647fe283fc60c963de70c5f6b2a5` | `artifacts/server_pf_first_study_s0_exact_time_v1_1_20260925_3279201/` |
| S1/S2 Phase B | `complete_with_findings` | `d13f49dc8923b0553f8c8596de3c44c8a7a6f14f` | `artifacts/pf_first_study_phase_b_20260925_5a2f0a2/` |
| S3 HF限定接続 | `complete_retrospective_synthesis` | `e768aaff19aa0a1a57c4ccf2563258f860c5b3ec` | `artifacts/pf_first_study_s3_hf_connection_20260925/` |
| S4 Phase A | `selection_frozen` | `95ed24c74bb29d883bbaf76d4578ff7af08ed995` | `artifacts/server_pf_first_study_s4_phase_a_20260925_f66e86f/` |
| S4 Phase B v1.1 | `complete_no_benefit` | `4d831b52475a7399b74a048a7471eaba6c4527c0` | `artifacts/server_pf_first_study_s4_state_convergence_v1_1_20260925_96699df/` |

固定hashは次である。

- 第一研究protocol：`410367f7ff1093fb5f171bb00ca8c22b292de34c19ff03553c600a0313565565`
- S4 parent protocol：`5c3c33fab6752b5ccf0ec9ee415e115bdf2134256e5a956f6b0e9b639f554c40`
- S4 uniform-anchor amendment：`9ce996b2732e02a7bb2fa4f1d6f8a4e09fd503896a4eda7a9a4496be0f402150`
- S4 frozen prediction：`47cdef9b52ea73feef0c005229cb9a482ee8e95afff87f038ff8461549f1c729`

## 3. S0--S3で確定した機構

S1/S2の固定128 caseでは、状態置換誤差が79 caseで支配し、49 caseがmixedだった。
fit誤差またはexact-state proxy--PF固有値差が単独支配したcaseはなかった。ただし、
これは全Hamiltonian・PF・時刻に対する普遍則ではない。

S0 exact-time採点では、N2/CO主4条件とHF stress 2条件の1%余裕付き予算が6/6安全
だった。一方、joint regretはN2/COで`2.1338%`--`22.7600%`、HFで
`107.6361%`--`114.1534%`だった。安全性と資源効率が異なるという判断は、保存gridの
近傍点ではなくexact selected timeでも維持された。

S3は新規truthを計算せず、第一研究、H01、HF mechanism bridgeを限定接続した。
近似状態の置換は主要な校正誤差軸だが、HF伸長におけるexact-state低次モデルの破綻は、
先頭係数の対角相殺、相対高次寄与、物理gapが同時に変わる条件付き現象である。
通常の状態品質スカラーまたはPF位相gapだけから資源効率を一意に予測できるとは
結論しなかった。

## 4. S4の固定比較

S4 Phase Aはfull CISDと決定論的99% truncated CISDのsigned proxy差をstate-riskとし、
6条件×7 strategyをtruth前に固定した。`oracle_information_used=false`、
`truth_opened=false`、新規truth点0でPhase Aをcommitした。

初回Phase Bは6 condition/PF群に保存済み下側anchorがなく、direct計算前に停止した。
v1.1ではPhase A予測を変更せず、全12群に一様な

$$
t_{\rm anchor}=0.5\,t_{\min}
$$

を適用した。20 unique selection、60挿入direct座標、12 uniform anchor、合計72新規
direct座標を計算し、旧cache再利用は0だった。全source/numerical gateは合格した。

| 数値監査 | 値 |
|---|---:|
| 最大固有対残差 | `3.66691e-14` |
| 最大unitarity Frobenius残差 | `1.01171e-11` |
| 最小anchor ground overlap | `0.9999999933192891` |
| 最小anchor phase gap | `0.004095126613043059 rad` |
| 最小挿入previous overlap | `0.9999996862933038` |
| 最小挿入ground overlap | `0.9999996340938037` |
| 最小挿入phase gap | `0.008190328488616692 rad` |

## 5. S4 strategy結果

| strategy | $\gamma=1.01$安全数 | 平均主regret | 最大主regret |
|---|---:|---:|---:|
| practical baseline | 6/6 | `42.8416%` | `114.1534%` |
| fixed `current_m3` | 6/6 | `42.8416%` | `114.1534%` |
| fixed Yoshida4 | 6/6 | `162.1592%` | `304.9154%` |
| diagnostic record-only | 6/6 | `42.8416%` | `114.1534%` |
| universal fallback | 6/6 | `90.3424%` | `114.1534%` |
| state-targeted fallback | 6/6 | `42.8416%` | `114.1534%` |
| equal-cost 7点fit | 6/6 | `42.3828%` | `114.1534%` |

state riskはHF equilibrium/stretch150の`current_m3`で発火した。しかしtargeted
fallbackはpractical baselineと同じ選択・平均regret・最大regretになった。固定benefit
判定のうちminimum safety、主4条件coverage、条件別悪化上限、universal fallbackに
対するspecificityは合格したが、baseline比平均regret 10%以上改善は不合格だった。

equal-cost 7点fitの平均regret改善は相対約`1.07%`に留まり、targeted diagnosticの
増分価値を示す根拠にもならなかった。fixed Yoshida4とuniversal fallbackは安全だったが
資源効率を悪化させた。

## 6. 主張範囲

主張できるのは次である。

- 固定H4・二準位case集合では状態置換が主要な校正誤差軸だった。
- 1%余裕は今回の6 development条件で安全だったが、低regretを保証しなかった。
- 今回固定した二状態診断はriskを記録できても、baselineの資源効率を改善しなかった。
- 改善しなかったS4も、事前固定判定に従う有効なnegative resultである。

次は主張しない。

- 独立分子へtransferする安価で低regretなselectorを確立した。
- 1%余裕が一般に十分である。
- 状態置換誤差がすべての分子・PF・時刻で支配する。
- S4が独立holdout、または方法論上の成功である。
- 新PF、別基底、別精度、完全fault-tolerant runtimeへ一般化できる。

## 7. 終了後の作業

S5、追加分子、閾値調整、追加diagnostic、新PF探索は開始しない。論文では
`complete_no_benefit`を隠さず、方法論拡張版ではなく中核の機構・信頼性成果として
構成する。将来別方式を試す場合は、本研究と異なるprotocol、開発集合、独立評価集合を
事前固定する。
