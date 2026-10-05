# 有限時間PF校正の予算信頼性と資源削減余地

固定current_m3と連続rotation費用モデルの保存結果は、校正の点精度、凍結予算の安全性、
強いcheap対照からの残余改善余地が異なることを示す。
HFでは同じ安定性gateのq=0がsafeとunsafeに分かれ、H-chainではfixed cheapとB2/H1が同じ安全判断を与えた。
追加spectral校正の価値は点精度だけでは決まらず、oracleまでの余地とwidth/rank/採用の組で評価する。

本書は[承認済み方針](approved_scope_and_rq.md)を実装した成果整理である。
数値の根拠は[主解析report](../../../artifacts/budget_safety_mechanism_20261005/report.md)と既存CSVで、
新規科学計算、policy変更、再fit、主解析再実行、再採点はしていない。
safeはnumerical truthとcontinuous cost proxy上の判定で、certificateや実機成功確率ではない。

## 評価対象と比較単位

**Table 1.** 元のcontractを保った評価対象と適用範囲。

| 条件 | 保存座標とbenchmark | 適用と観測単位 | 元のstatusと根拠 |
|---|---|---|---|
| HF eq と stretch150 | 各T0,1.3T0,1.6T0、計6。B0は第一研究から継承し、新T0 cheap式で置換しない | 2 development条件。pilotとG2は同じdataの再利用で独立再現ではない | HF pilot robust_signalとG2 review-requiredを共に保存。[G2 COMPLETE](../../../artifacts/hf_g2_fixed_rule_replay_20261005/result/COMPLETE.json) |
| HCl eq と stretch150 | 各0.5,0.65,0.8 t_ana、計6。対照はmain同時刻gamma1.02 | 2 development条件。HClにHF/H-chain selectorを追加適用しない | D2-A formal close-spectral stopとpost-hoc branch auditを分離。[主解析report](../../../artifacts/budget_safety_mechanism_20261005/report.md) |
| H2,H4,H6,H8 | 各0.5,0.65,0.8 t_ref、計12。B0はr=.5 fixed1.01 | 4 neutral-singlet系。H2のsector/CISDは4/4で有限次元飽和を含む | 個別review-required statusを変更しない。[H-chain総括](../hchain_independent_validation_summary_20261005.md) |
| H5,H7 | 同じ3比率、計6 | 2 cation-triplet系。evenとの差は純粋なparity比較ではない | Odd extension review-required。[H-chain総括](../hchain_independent_validation_summary_20261005.md) |
| H3 | 入力とreference-grid取得のみ。候補・truth・decisionなし | 参考attempt 1。Reference規則不成立、性能0とはしない | H3_reference_scale_unavailable_under_frozen_protocol。[総括のH3節](../hchain_independent_validation_summary_20261005.md#h3のreference適用不能) |

解析対象は採点済み10条件30座標。H-chainはattempted7、reference適格6である。
座標30、safe oracle比較29、保存decision64、算術監査33,434を独立標本数や発見件数にしない。
Native時刻集合は異なるため合同の連続時刻最適化や共通holdout結果ではない。

## 予算の安全性を決める片側の不足量

e=abs(delta_direct)、c=abs(delta_C)、a=beta*Kと置く。
指定taskのsafe判定は e+a/(t*B)<=epsilon_E。
Fixed cheap budget B_gamma=gamma*a/[t*(epsilon_E-c)]では、
u=e-c、M_gamma=(1-1/gamma)*(epsilon_E-c)によりsafe iff u<=M_gamma。
実際の保存B0を含む一般budgetにはslack=epsilon_E-e-a/(t*B_frozen)を使う。
gamma1ではratio未定義で、slackだけを扱う。
これはモデルの同値変形であり、新しいPF誤差boundではない。

![Figure 1 予算の過小評価とmargin](../../../paper/study2/figures/figure_1_budget_safety.png)

HF eqの1.6T0ではu=1.28300068e-5 Haがmargin=1.46426427e-6 Haを超え、
slack=-1.13657425e-5 Haとなる。Stretchでは符号が逆でsigned point errorは
1.49247345e-5 Haだが、絶対誤差の過小評価は5.63018839e-7 Haで、slack=9.43705442e-7 Haは正だった。
H2/H5では小さい過小評価をmarginが吸収し、他4 H-chain系ではcheap magnitudeが過大評価だった。
[Selected CSV](../../../artifacts/budget_safety_mechanism_20261005/selected_frozen_budget_safety.csv)。

同じeligible集合上で全costに共通の正のgammaを掛けてもargminは不変である。
従ってgamma間で選択が同じという情報は、独立推定器が一致したことではない。
Eligibility/fallbackが変わる場合は別であり、この反例は現gateの失敗を示すが、
全cheap diagnosticの不可能性やspectral不可欠性を示さない。
Signed精度が不要という解釈もuncorrected taskだけで、bias correctionへは拡張しない。

## 完全情報の改善余地と実M1を分ける

同じ時刻でe<epsilon_Eならcost-free truth floorはB_truth=a/[t*(epsilon_E-e)]。
名指しした安全なB_Cからの残余headroomはh=1-B_truth/B_Cである。
これは固定task・同じK/beta/time・continuous metricの費用下限算術で、
情報取得が無償でも届く削減余地を示す。介入の達成可能性は未確立である。

| 同時刻対照 | safe比較 | 残余headroom |
|---|---:|---:|
| HF fixed gamma1.01 | 5/6 | 0.1506–2.2428% |
| H-chain fixed gamma1.01 | 18/18 | 0.9766–2.7290% |
| HCl main gamma1.02 | 6/6 | 0.3280–2.2865% |

HF eqの1.6T0 fixed1.01はunsafeなので改善率を定義しない。
この29の名指し安全比較では完全truthでも10%同時刻削減に届かない。
別gamma、別時刻、候補域拡大、新PF、bias correction、異なるmetricの利益まで否定していない。
[Same-time CSV](../../../artifacts/budget_safety_mechanism_20261005/same_time_oracle_headroom.csv)。

![Figure 2 Oracle headroom と実M1](../../../paper/study2/figures/figure_2_headroom_and_m1.png)

一方、w_win=epsilon_E-abs(delta_M)-a/[t*(1-eta)*B_C]が負なら、
**固定M1 pointのまま非負widthだけを縮めても**目標には届かない。
これはperfect-truth floorの比較とは異なる。現在のwidthは変えず、
point、経験的coverage、rank、allowance、candidate eligibility、最終fallbackを分ける。

| 対象 | 点精度改善 | 経験的coverage | 元abstention |
|---|---:|---:|---:|
| HF | 6/6 | 6/6 | 0/6 |
| H-chain | 11/18 | 18/18 | 12/18 |
| HCl | 6/6 | 6/6 | 1/6 |

H-chain always-M1は6系ともB0 fallback、B2/H1はfixed1.01と同じr=.8を選んだ。
元3候補でのtruth oracle最良も6系ともr=.8だった。
選択済みcheap budgetからこのnative-grid oracleまでの残りは0.9766–2.7290%。
r=.8は候補端で、長時刻を含む最適値ではない。
[Native oracle CSV](../../../artifacts/budget_safety_mechanism_20261005/oracle_headroom_by_contract.csv)。

HF eqでは共通fixed1.10がsafeでM1より安く、stretchではfixed1.01がsafeでM1より安い。
ただしtruth後の条件別最小safe gammaはoperational方式ではない。
**同じ事前固定gamma1.10を両HF条件へ使った合計**ではM1が約1.46%安いという保存比較を残す。
大きな情報一般の勝利・不要性とは結論しない。M1の不利益は情報を無視できない普遍原理ではなく、
当該推定器・empirical width・採用規則の組の性能である。

## PF回収とreference誤差の分解

同じH/sector/origin/physical liftを確認したH-chain18点では
delta_M-delta_direct=A-R、A=Ehat_PF-E_PF、R=Ehat_H-E0を分けられる。

![Figure 3 PF とH-referenceの成分](../../../paper/study2/figures/figure_3_pf_reference_components.png)

H4/H5ではreference誤差がPF側より大きい。H6/H7/H8では二つの正の成分が部分的に相殺する。
H8のr=.8はA=2.79934e-5 Ha、R=6.39472e-5 Ha、shift error=-3.59538e-5 Haである。
Shiftだけの点精度をabsolute PF回収精度と同一視しない。
差の誤差相殺原理自体は新規性ではなく、state/rank原因も未検証である。
H2の1e-16級は丸め域、HF/HCl12点はidentity不足のままであり、
独立groundを新規生成して補完していない。
[Decomposition CSV](../../../artifacts/budget_safety_mechanism_20261005/m1_reference_error_decomposition.csv)。

## 原稿の着地点と付録

本文は問題設定、安全性の軸、safe/unsafe事例、headroomと実M1、reference誤差、
限定と実務的含意の順にする。D1/D2/C0/G2という作業履歴は証拠のprovenanceへ残し、
本文の論理順にはしない。

H-chainの32.83–33.09% benchmark削減はleading-model 32.7741%との差が
0.0563–0.3199 percentage pointsである。これは付録で解釈を統制し、adaptive主成果とはしない。
[Leading-model表](../../../artifacts/budget_safety_mechanism_20261005/hchain_model_vs_observation.csv)。
全gamma/全座標は既存[capacity CSV](../../../artifacts/budget_safety_mechanism_20261005/budget_safety_capacity.csv)、
[width CSV](../../../artifacts/budget_safety_mechanism_20261005/width_decision_windows.csv)へリンクし、主解析CSVを再生成しない。

費用は[resource scope CSV](../../../artifacts/budget_safety_mechanism_20261005/resource_accounting_scope.csv)の
元JSON pointer・unit・stageを保つ。Overlapping wall/RSSを合算せず、q=1 combined/cold cost、
回路総費用、量子・古典net advantageは未確立である。
H8のlegacy full-suite問題も[元総括](../hchain_independent_validation_summary_20261005.md#h8のmemory-safe拡張とsoftware-caveat)通りで、
本資料のfocused検証によってrepository全体がgreenになったとはしない。

Contributionsの根拠と制約は[claim–evidence台帳](claim_evidence_ledger.md)、
近接手法との差分は[先行研究表](related_work_delta.md)、未達claimは[未確立事項](outstanding_claims.md)を参照する。
