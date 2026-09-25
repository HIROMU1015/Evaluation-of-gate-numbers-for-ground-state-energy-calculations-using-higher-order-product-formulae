# 第一研究 統合結果：校正誤差の三分解と凍結資源への伝播

**確定日：2026年9月25日**  
**状態：完了（protocolの停止条件を満たした）**  
**結果ブランチ：`first-study-mechanism-decision-v1-20260925`**

## 1. 結論

第一研究のS0、Experiment A、Experiment B/Cはすべて閉じた。固定protocolの
停止outcomeでは、**Outcome A：一つの誤差成分が支配する**が成立した。

固定したH4と二準位制御系では、resolved評価点の多数で

$$
E_{\rm state}=g_{\psi,P}-g_{0,P}
$$

すなわち**近似状態とexact groundのproxy差（状態置換誤差）**が、model fit誤差と
exact-state proxy--PF固有値差のそれぞれに対して3倍以上となった。128個の固定case
のうち79個が`E_state_hartree`支配、49個がmixedであり、`E_fit`または`E_proxy`が
単独支配となるcaseはなかった。H4だけでは56 case中49 caseが状態置換誤差支配で、
CISDとRHFについては4 PFすべてが状態置換誤差支配だった。

ただし、これは「状態誤差だけを直せば実用selectorが完成する」という結論ではない。
Phase BのH4では、凍結selectorは`m5_best`を選び、$\gamma=1.01$の精度予算には合格
した一方、固定direct gridに対するjoint regretは`64.513636%`、凍結予算はdirect
referenceより`98.352110%`多かった。**精度上の安全性と資源効率は別である。**

S0の既存practical selectorも同じ区別を示した。exact selected timeで、N2/CO主4条件
は$\gamma=1.0$と`1.01`の両方に合格し、HF stress 2条件も`1.01`では合格した。
しかしjoint regretはN2/COで`2.13%`から`22.76%`、HF stressでは`107.64%`から
`114.15%`だった。したがって、1%の安全余裕は今回の6条件で精度達成を保証したが、
低regretを保証しない。

この結果により、第一研究の中心的な次段候補は「PF係数探索」ではなく、
**近似状態に対するproxyの状態感度を抑える、または状態置換誤差を検出して安全性と
資源効率を分けて制御する校正法**となる。ただしprotocolの停止規則に従い、この
ブランチでは改善法、S3、追加分子、新PF探索へ進まない。

## 2. 固定仕様と実行境界

- 第一研究protocol：`PF_first_study_protocol_20260925.json`
- protocol SHA-256：`410367f7ff1093fb5f171bb00ca8c22b292de34c19ff03553c600a0313565565`
- formalization / Experiment A実装commit：`d3faddebe490dbe8224bd4274578f2edd313dfb0`
- Experiment A結果commit：`c609246171725e6706158a31bd738deed55324df`
- Phase A実装commit：`62652436a98ceaeac6f5d5d519d20d31ca70ceb7`
- Phase A結果commit：`5a2f0a2e0315493c892c79f1a6b8c9285cc52ac3`
- Phase A prediction SHA-256：`60058fe333d4b25f1ad4b8f3f5342a3736f2379ce9490b3f2ecde69583beeeda`
- Phase B結果commit：`d13f49dc8923b0553f8c8596de3c44c8a7a6f14f`

Phase Aでは近似状態proxyだけからselector出力を凍結し、Phase Bで直接固有枝を開いた。
Phase Bのprediction hashはPhase Aから不変で、三分解closureの最大残差は
`2.168404e-19 Ha`だった。

## 3. 各stageの完了状態

| Stage | Status | 主結果 | 成果物 |
| --- | --- | --- | --- |
| Experiment A | `complete_validation` | 数式・符号・正負時刻枝・80桁参照・三分解closureを含む17 gate合格 | `artifacts/pf_first_study_experiment_a_20260925_d3fadde/` |
| Phase A | `selection_frozen` | H4 selector/scorerとpredictionをtruth前に凍結 | `artifacts/pf_first_study_phase_a_20260925_6265243/` |
| Phase B / Experiment B/C | `complete_with_findings` | Outcome A成立。79/128 caseで状態置換誤差支配 | `artifacts/pf_first_study_phase_b_20260925_5a2f0a2/` |
| S0 v1.1 | `complete_exact_time_scoring` | 6条件・18新規点・6 anchorの全gate合格 | `artifacts/server_pf_first_study_s0_exact_time_v1_1_20260925_3279201/` |

Experiment B/Cでは1,536 decomposition行、2,256 observable行、1,764 direct truth行を
保存した。最大三分解closure残差、固有対残差、unitarity Frobenius残差はそれぞれ
`2.168404e-19 Ha`、`1.029590e-13`、`8.850249e-13`だった。

## 4. Experiment B/Cの機構判定

固定dominance ruleは、同一caseのresolved評価点の過半数で、一成分が他の各成分の
3倍以上となることだった。

| 範囲 | case数 | 状態置換誤差支配 | mixed | fit/proxy単独支配 |
| --- | ---: | ---: | ---: | ---: |
| H4 Experiment B | 56 | 49 | 7 | 0 |
| 二準位 Experiment C | 72 | 30 | 42 | 0 |
| 合計 | 128 | 79 | 49 | 0 |

この結果から固定outcomeは次のように確定する。

- Outcome A（一成分支配）：**成立**。
- Outcome B（介入条件による支配成分の切替）：**不成立**。
- Outcome C（material errorがあってもjoint regret 10%以下かつ$\gamma=1.01$で安全）：
  **不成立**。
- null result：**不成立**。

位相依存の一部caseでは`E_fit`と`E_state`がmixedとなった。従って、状態置換誤差の
支配は全点・全状態に対する普遍則ではなく、今回の固定case集合に対する判定である。

## 5. H4の凍結資源判定

Phase Aが選んだPFと時刻は`m5_best`, `t=2.1466061014866242 Ha^-1`だった。

| 指標 | 値 |
| --- | ---: |
| predicted cost | `17,568,978.68` |
| selected-time direct cost | `14,717,463.43` |
| direct grid best cost | `8,946,044.72` |
| same-PF / joint regret | `64.513636%` |
| $\gamma=1.0$ energy margin | `2.463489e-05 Ha`（合格） |
| $\gamma=1.01$ energy margin | `2.589377e-05 Ha`（合格） |
| $\gamma=1.01$ budget/reference - 1 | `98.352110%` |

このcaseではselectorは安全側だったが、時刻選択と予算はdirect grid基準から大きく
過剰だった。このため、状態感度の診断を単に安全marginへ変換するだけでなく、
over-allocationを抑える評価が次段では必要になる。

## 6. S0 exact-time採点

S0はpractical最小版の既存6 predictionを変更せず、各selected timeの
`0.99, 1.00, 1.01`倍を直接計算した。frozen prediction SHA-256は
`fd354e0c0d161dae86bee1e220e36958a450659ea2ed5409d10cf4c13674477e`のままである。

| 条件 | group | exact-time joint regret | $\gamma=1.0$ | $\gamma=1.01$ |
| --- | --- | ---: | :---: | :---: |
| N2 equilibrium | primary | `2.133755%` | pass | pass |
| N2 stretch150 | primary | `22.759988%` | pass | pass |
| CO equilibrium | primary | `3.184296%` | pass | pass |
| CO stretch150 | primary | `7.181965%` | pass | pass |
| HF equilibrium | stress | `114.153436%` | fail | pass |
| HF stretch150 | stress | `107.636129%` | pass | pass |

従って、$\gamma=1.0$は全体5/6、主条件4/4、HF stress 1/2、$\gamma=1.01$は
全体6/6だった。これは以前観測済みの条件に対するdevelopment scoringであり、独立な
分子transfer検証ではない。

### 6.1 初回runとv1.1

初回S0 result commit `0ee4cc4c2567d7bda25d8e2e93d2ba051d2a0678`は、
`CO_active_eq_sto3g`のP03-only anchor値をH01 pickleで再計算し、差が
`1.041412e-07 Ha`となったため`failed_numerical_validation`である。`COMPLETE`はなく、
その数値を科学的結論に使用しない。

v1.1はanchor source identityだけを
`new_h01_continuous_branch_calculation`へ固定した。selector、selected time、budget、
truth triplet、閾値、regret referenceは変更していない。

- v1.1 anchor protocol SHA-256：
  `8f776ded65e42b7657d5c014cf525421b95cbbfb40aa0744c69d2c11f00204b1`
- GPU result branch：`gpu-first-study-s0-exact-time-v1-1-results-20260925`
- GPU result commit：`cc3626a8135b647fe283fc60c963de70c5f6b2a5`
- 統合commit：`7715400a275d83bf9353f89eb3a0517b3de0913a`
- 18 new direct truth points、6 anchor recomputations、旧cache再利用0。
- 最大anchor再現差：`1.367331e-14 Ha`（閾値`1e-9 Ha`）。
- 最大固有対残差：`3.103193e-14`。
- 最大unitarity Frobenius残差：`9.886690e-12`。
- 最小previous-branch overlap：`0.9999999919683533`。
- 最小ground-state overlap：`0.9999996340938037`。
- 最小phase gap：`0.03252669041934374 rad`。
- 実時間：`121.929 s`、最大CPU RSS：`1,011,716 KiB`、最大GPU memory：`701 MiB`。

GPU保存ログは集中26件、全体`205 passed, 1 skipped`だった。結果commitに対する独立
再実行では集中26件、全体207件が合格した。全12 manifest artifact hashも一致した。

## 7. 主張できること／できないこと

### 主張できること

1. 固定H4/二準位case集合では、三分解した校正誤差のうち状態置換誤差が最も頻繁に
   支配した。
2. 状態置換誤差の支配と、凍結予算の精度達成は同義ではない。大きなregretを伴って
   安全側になるcaseがある。
3. exact selected timeで採点しても、practical selectorの1%安全余裕は今回の6条件で
   精度を満たした。
4. 同時に、同じselectorの資源効率は条件依存であり、HF stressでは100%を超える
   regretが残った。

### 主張できないこと

1. 未使用分子へtransferする安価なselectorが確立したとは言えない。
2. 状態置換誤差が全Hamiltonian、全PF、全時刻で常に支配するとは言えない。
3. 1%安全余裕が一般に十分とは言えない。
4. 今回の結果だけから、特定の改善calibrationまたは新PF係数を選ぶことはできない。
5. 保存direct gridの最小を連続時間の厳密最小とは呼ばない。

## 8. 停止判断

固定protocolの完了条件はすべて満たされた。

- S0 exact-time scoring：v1.1で完了。
- Experiment A：全validation gate合格。
- Experiment B/C：固定decomposition/resource表を生成。
- stopping outcome：Outcome Aを同定。
- source identity、Phase A/B境界、row/hash accounting：合格。

よって第一研究はここで停止する。次の研究判断では、状態置換誤差を直接減らす方法、
状態感度を検出してabstainまたは追加校正する方法、過剰な凍結予算を削減する方法を
候補として比較する。ただし、その選択には新しい事前固定protocolが必要であり、この
完了runの結果を見て同じprotocol内で改善法を追加しない。
