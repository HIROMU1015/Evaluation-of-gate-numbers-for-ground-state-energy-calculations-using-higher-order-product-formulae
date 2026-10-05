# Budget-safety mechanism main analysis — review stop

Status: `second_study_v2_budget_safety_mechanism_analysis_complete_review_required`.
Direction Cとclaim scopeを先にlocal commit `d77b4644600fb8ef2af05108b766efd95e5704da` でfreezeし、
保存済みscalarだけを一回解析した。新規PF/H作用、Arnoldi、ground/truth/gap、GPU、runtime読取は全て0。
原本のprediction、budget、width、gate、formal decisionは変更していない。

## 1. 核となる説明：過小評価とmarginの比較

signed point errorとQPE errorの過小評価は異なる。
`e=abs(delta_direct)`, `c=abs(delta_C)`, `u=e-c` とし、固定budget multiplier gammaでは
`M_gamma=(1-1/gamma)*(epsilon-c)`。safeの算術条件は `u<=M_gamma`。
gamma=1のratioは未定義として30行全て空欄にし、slack `M_gamma-u` を使った。

HFの選択座標1.6T0は次のようになる（Hartree）。

| condition | e-c | M_1.01 | safety slack | post-hoc gamma_req | saved B2/H1 |
|---|---:|---:|---:|---:|---|
| eq | 1.28300068e-5 | 1.46426427e-6 | -1.13657425e-5 | 1.0949943864 | unsafe |
| stretch | 5.63018839e-7 | 1.50672428e-6 | +9.43705442e-7 | 1.0037134494 | safe |

eqはcheapの過小評価がmarginを超えた。stretchのsigned point errorは1.49247345e-5と大きく、
cheapとtruthの符号も反対だが、budgetが使う絶対値の過小評価は5.63018839e-7でmargin内に収まる。
したがってsigned精度やcheap stabilityだけではsafe/unsafeを説明できず、marginに対する不足量が必要。

H-chainの選択r=.8でgamma1.01のslackは次の通り。

| system | e-c [Ha] | safety slack [Ha] | saved B2/H1 safe |
|---|---:|---:|---|
| H2 | +6.29417109e-9 | +1.44612908e-6 | yes |
| H4 | -9.78122170e-7 | +2.42789724e-6 | yes |
| H5 | +2.00188275e-8 | +1.43380984e-6 | yes |
| H6 | -1.91538537e-6 | +3.36823396e-6 | yes |
| H7 | -1.19623314e-6 | +2.64690097e-6 | yes |
| H8 | -2.62857951e-6 | +4.08441451e-6 | yes |

H2/H5では小さい過小評価をmarginが吸収し、他4系ではcheap magnitude自体が過大評価だった。
全18 H-chain座標のgamma_req範囲は0.9824372543–1.0001363525。
gamma_req<1を勝手に新budgetへ採用せず、gamma>=1制約版も別fieldにした。
HCl全6点では0.9966780912–1.0166546542。既存main gamma1.02の同時刻budgetは全6点でsafe。
これらは条件付き事後診断であり、必要gammaを知るtruth-free方式の確立ではない。

HF B0は既存first-study baselineであり、新T0 proxyからのB_1.01と一致しない。
`epsilon-e-beta*K/(t*B_frozen)` の一般形でB0を採点した。HCl main baselineは各同時刻のgamma1.02であり、
HF/H-chainのcondition B0に統合していない。64 frozen selected decisionsの判定は原本と全件一致。

## 2. M1：point accuracy、width、abstention、decision windowは別

| native data | coordinates | M1 point improves vs cheap | empirical width covers | abstention |
|---|---:|---:|---:|---:|
| HF | 6 | 6 | 6 | 0 |
| H-chain (6 systems) | 18 | 11 | 18 | 12 |
| HCl / D2-A | 6 | 6 | 6 | 1 |

H-chain rank不足はH2の2点。no-positive-QPE-allowanceはH5の1点、H6/H7/H8の各3点。
H4はabstainしないが、固定width込みbudgetがintervention条件を満たさずalways-M1はB0 fallback。
H7/H8ではpoint estimateもcheapより劣るので、全体を「accuracyは常に良いがwidthだけ悪い」とは言わない。
H2のrank-reduced point estimateが正確でも、事前rank gateのabstentionを救済しない。

same-timeのsafe fixed-cheap comparatorに対するwidth windowを、そのままのwidthで評価した。

| comparator | valid safe comparisons | current width in eta=0 window | eta=.10 window |
|---|---:|---:|---|
| HF gamma1.01 | 5/6 (eq 1.6T0 excluded: unsafe) | 3/5 | all 5 negative |
| H-chain gamma1.01 | 18/18 | 3/18 | all 18 negative |
| HCl main gamma1.02 | 6/6 | 0/6 | all 6 negative |

これは既存cheap marginが小さい場合、同時刻でwidthを縮めるだけでは10%改善に届かないことを示す。
H-chainのeta=0窓に入る3点はH2で、そのうち2点はrank gateによりabstainしており採用successではない。
全gamma frontierとB0に対する窓もCSVに残し、time-domain変更によるbaseline改善と同時刻比較を分離した。
negative windowを小さいwidthに置き換えることは行っていない。

HF eqの保存frontierではgamma1.10がsafe、stretchは1.01でsafeだった。両者は同じ1.6T0を選び、
各条件でこのsafe frontier値はM1より小さい。これはtruthを見た後の条件別frontier比較であり、
条件別gammaを事前に選ぶoperational方式を追加した結果ではない。
common gamma1.10とのaggregate spectral advantageが小さいという既存bridge/G2の解釈は維持し、
「cheap gate失敗なのでspectralが不可欠」とは結論しない。

HCl同時刻のcost-free perfect-truth headroomは0.327975%–2.286462%。C0の6値と一致した。
高精度point estimateがそのまま大きな資源利益になるわけではない。
別表のnative 3候補oracleは候補集合内だけの事後比較であり、連続時刻最適化でも運用可能なoracleでもない。
HCl oracleのreferenceは最小保存時刻のmain budgetで、formal selected baselineとは呼ばない。

## 3. H-chainの約33%：モデル基準と実証を分ける

PF errorを無視した固定時刻比 .5/.8 はcost ratio .625（37.5%削減）。
leading `c=alpha*t^4`, `t_ref=(epsilon/(5*alpha))^(1/4)` を含めると、
`.5*(1-.5^4/5)/[.8*(1-.8^4/5)]=0.6722589534681074`、削減率32.77410465%となる。

| system | saved B2/B0 saving | modelとの差 [percentage points] | saved truth safety |
|---|---:|---:|---|
| H2 | 32.942826% | +0.168721 | safe |
| H4 | 32.830439% | +0.056335 | safe |
| H5 | 33.004909% | +0.230805 | safe |
| H6 | 32.965278% | +0.191173 | safe |
| H7 | 32.870855% | +0.096751 | safe |
| H8 | 33.094037% | +0.319933 | safe |

大部分のbudget ratioが固定時刻とleading-model算術に近いことと、実際の凍結予算が安全だったことは
異なる主張である。差を独立な因果的adaptive効果と解釈しない。
全6系q=0でH1=B2。条件付きspectral pathの性能・費用は一度も実測されていない。
H3はreference不成立のまま除外理由を保存し、safe 0や効果0として追加しない。

## 4. PF/H-reference誤差：18点のみidentityを満たす

H-chainはprediction/ground/truthのHamiltonian・sector・ground-vector hash、exact time、
resolved physical liftを照合でき、実際に使ったprimary prefixのenergyを用いて
`delta_M-delta=(Ehat_PF-E_PF)-(Ehat_H-E0)` を18点で分解した。
energy-scale ULPによるclosure丸めを記録し、uncertainty/certificateに転用しない。

選択r=.8の例（Hartree）:

| system | PF energy error | H-reference error | signed shift error |
|---|---:|---:|---:|
| H4 | +6.67348399e-11 | +3.80582810e-9 | -3.73909331e-9 |
| H5 | +1.62666769e-10 | +4.57482565e-8 | -4.55855897e-8 |
| H6 | +2.42817404e-6 | +3.36121776e-6 | -9.33043715e-7 |
| H7 | +5.12632471e-6 | +8.53820085e-6 | -3.41187614e-6 |
| H8 | +2.79934265e-5 | +6.39472434e-5 | -3.59538169e-5 |

H4/H5では保存値上のH-reference誤差がPF-side誤差より大きい。
H6/H7/H8では二つの正の誤差が差を取ることで一部相殺される。shiftのpoint errorだけから
absolute PF recovery精度を断定できない。これは観測分解であり、state/rankの因果的検証ではない。
H2の1e-16級成分は浮動小数点丸め域で、物理的差を論じない。

HF/HClの12点は今回の限定registryで独立same-H ground origin/absolute targetを閉じられず、
`indeterminate_identity_or_independent_energy_missing` とした。
HCl branch auditのH-reference基準truth targetを独立E_PFとして代用していない。
追加ground/gap計算による穴埋めはしない。

## 5. Information-costとclaim scope

保存resource field 2220件を原本JSON pointer、unit、stage scope付きで転記し、合計しない。
HFの保存cheap/M1 arm wallは0.2739521554/0.4933428355秒、process peak RSSは446460 KiB。
even H-chainの保存cheap/M1 named arm wallは0.0984617537/0.1758624241秒。
これらはCLI全体・shared preparation・reference・cold standaloneの費用ではない。
内部expm matvecはunknownのままでありH exponential1回をH matvec1回と数えない。
q=0 comparator completionはH1費用に入れず、q=1 combined costやrigorous cost envelopeを推定しない。
scorer ground/truthの保存費用はvalidation costで、operational calibrationに混ぜない。

30座標はHF2/HCl2/H-chain6のnative 10条件に属する再利用データで、30 independent samplesではない。
HF pilot/G2を独立再現と数えず、偶奇H-chainのcharge/spin交絡も維持する。
safeはcontinuous proxy+numerical truth上の判定で、厳密保証・離散QPE・scaling claimではない。
旧formal resultとbranch auditは原本のままで、今回のphysical branch/width tableはそれらの再集計。

## 6. 次のレビュー：論文着地点を確認して停止

方針の全面再設計を再開するのではなく、次をレビューする。

1. Primary RQを「cheap過小評価と固定予算marginの関係」に置く主張が十分限定されているか。
2. M1のaccuracy/width/reference-cancellation/decision-valueの区別をsecondary resultとするか。
3. H-chain約33%を新adaptive方式の成果とせず、fixed-domainモデルに近い安全な事例と表現できるか。
4. information costはstage inventoryに留め、net advantageを主張しない論文着地点でよいか。
5. 既存文献との非自明な差分を何に限定するか。gamma/slackの代数自体を新規性とは呼ばない。

候補の着地点は「有限時刻PF校正のQPE予算判断：margin capacityとspectral uncertaintyのregime分析」。
追加policyやcertificateの完成を要求しない。追加計算が本当にclaim上の穴として残る場合のみ、
次の別承認で対象と情報価値を限定する。本タスクでは追加計算・threshold修正・pushは未承認。

## 検証

解析前/後のsynthetic stdlib testsは各26 passed、fail/skip 0。
独立Decimal60算術・CSV/JSON・source origin/snapshot・manifest auditは33434 checks PASS。
64 decision、30 gamma1ゼロmargin、C0の6同時刻headroom/widthを照合。
独立verifier初版の括弧不足SyntaxErrorを修正して再実行したが、凍結解析コードや結果の再実行・変更は0。
runner manifestは生成時のまま保存し、報告・検証資料を含む別completion manifestを追加する。
legacy molecular testsは新しい科学計算を避けるため実行していない。過去のfull-suite状況をgreenへ書き換えない。
