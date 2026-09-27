# 第二研究 safe-time-domain 完了報告

正式判定は`complete_no_benefit`です。固定`current_m3`と
`multiple_window_consistency`だけを対象にした一回の独立評価は完了しました。全source・数値gateは
合格しましたが、新規規則は事前固定したbenefit条件を満たしませんでした。

## 固定identity

- protocol SHA-256：`a6290b107ebbf93f7c0ee3bc383208862c51e37603a670625091e15472d4584b`
- frozen prediction SHA-256：`3406d2f69237d95b14be298059f777df3fbd5043446add2c31559bf902a34b83`
- Phase B result commit：`4691ac1ea7423d3c3f5a0496c41c98b9dcba360f`
- Phase B manifest SHA-256：`eb3ac51a21b9b5edd4b65d1a01ee4486bea6ba811bb22ba5e8db4a5e526a0917`
- 評価点：4条件、42 direct coordinates、4 anchors。
- cache：同一run中断再開によりcomputed 22、reused 20。旧・外部cache再利用は0。

## 主結果

Multiple-window ruleは4条件中3条件で精度を満たし、1条件で未達でした。aggregate frozen budgetは
current fallback比`0.8933806671`まで減りましたが、equal-information baseline比では
`1.2526414181`でした。

| Strategy | Safe | Aggregate frozen budget | Mean selection regret | Max selection regret |
| --- | ---: | ---: | ---: | ---: |
| current fallback | 2/4 | 11,721,643,230.73 | 0.915322 | 2.289789 |
| equal-information | 2/4 | 8,359,846,080.46 | 0.487379 | 1.036689 |
| multiple-window rule | 3/4 | 10,471,889,449.41 | 0.714556 | 1.486727 |
| uncapped counterfactual | 3/4 | 8,689,143,504.85 | 0.387317 | 1.036689 |

Multiple-window ruleはcoverage 4/4、extension selection 1、classical information counts equality、
current比aggregate budget条件には合格しました。一方、安全数4/4、equal-informationより小さい平均・最大
selection regret、条件別regret増加上限には不合格でした。

したがって、近似状態と今回の有限校正情報だけから安全な時間域拡張を採用する根拠は得られませんでした。
uncapped counterfactualは診断専用であり、上限撤廃の運用根拠にはしません。

## 数値・再現性gate

- 最大eigenpair residual：`9.813001224800841e-14`。
- 最大unitarity Frobenius residual：`1.3700411950543468e-11`。
- 最小anchor ground overlap：`0.9999999683019025`。
- 最小previous overlap：`0.9220325861410396`。
- 最小tracked ground overlap：`0.9222306179948309`。
- 最小phase gap：`4.954692104540167e-05 rad`。
- branch disagreement：0。
- pre/post focused：各68 passed。
- pre/post full：各304 passed、許可済み任意依存だけ1 skipped。

独立再計算ではcoordinate plan、数値gate、16 strategy rows、benefit checks、最終判定が一致しました。
`uncapped_counterfactual`のaggregate budgetだけが加算順序により1 ULP、相対`2.20e-16`異なりましたが、
科学的値や判定への影響はありません。

## 資源と停止

- direct-point時間合計：`4068.031 s`。
- GPU peak process memory：`3002 MiB`。
- 最大CPU RSS：約`2.97 GiB`。
- 対話session中断のため全external wall timeは`>=2001.365 s`の下限です。

予測・threshold・候補時刻・truncation・規則の再調整は行っていません。このnegative resultで第二研究を
閉じます。追加diagnostic、別PF・別分子・別basis・別精度、第三研究は自動的に開始しません。
