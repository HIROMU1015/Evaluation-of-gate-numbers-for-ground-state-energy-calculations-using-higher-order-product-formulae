# H-chain後の推奨研究方針

Status: `second_study_v2_post_hchain_direction_review_complete_review_required`

2026-10-05。確認snapshot: `50cdc62d69a28bc5d4f4893f3c589e0bbd6d81db`。本書は研究方針の提案（`governance_scope`）であり、新しい実験結果や実行承認ではない。

## 推奨はDirection C：calibration informationのdecision value

中心RQを「有限時間PF-QPEの固定resource modelにおいて、追加校正情報は、cheap-onlyに対してどの条件で安全な時刻・予算判断を改善し、その取得費用に見合うか」とする。Selective spectralは答えの一候補であって、勝つことを研究の成立条件にしない。

この変更は第一研究との接続を保つ。第一研究はmodel・margin・within-domain・domain・PF選択にresource regretを分解した。第二研究は、その損失を減らすための情報を、最終decisionと取得費用で評価する。因子の独立な介入可能性や、全損失を回復できることは仮定しない。

## 既存証拠が支持すること

| 保存結果 | 支持する解釈 | 支持しない解釈 |
|---|---|---|
| H2/H4/H5/H6/H7/H8でq=0、B2/H1 safe、B/B0約0.67。Fixed cheap gamma=1.01も同一decision | この固定familyにはcheap-sufficient regimeがある | B2のadaptive利益、H1のselective追加利益、未知分子の保証 |
| HFのM1は2条件safe。共通safe cheap gamma=1.10比でaggregate約1.4622%低予算 | 高精度情報の追加量子利益は小さく、condition依存 | Spectralが必須、condition-wiseにcheapを支配、H1がvalidated |
| HF eqではsafe gamma=1.10のcheapがM1より低予算。Stretchではsafe gamma=1.01がM1より低予算 | 各条件にはM1より安いsafe cheap armが保存されている | Truth-freeにそのgammaを選べた。Condition-wise oracleはoperationalではない |
| HCl D2-A auditでphysical branch 6/6、max error 1.38e-8 Ha、baselineより低予算0/6 | 点回収とdecision-useful widthは別問題 | Original formal verdictの書換え、spectral回収が全部失敗したとの解釈 |
| H7/H8ではM1点誤差がcheapより大きく、always-M1は全eligible chainでB0 fallback | Widthだけでなくpoint estimatorのsystem依存性もある | M1の精度は常に高い、Arnoldiを深くすれば解決 |
| S1Aはformal DでB2/H1 replay未実行 | General-molecule policy evidenceが欠けている | S1Aでpolicy validation済み、selectiveが否定された |

根拠は[全evidence matrix](evidence_matrix.csv)、[RQレビュー](research_question_review.md)、[source registry](source_registry.json)。H-chain summaryの実験status、D2-A original decision、S1A Dは保存したままとする。

## 中心・代替・終了推奨を分ける

- Recommended central direction: **C — value-of-information / regime characterization**。ここでのvalueはdecision-levelの実測比較であり、確率分布を仮定したexpected value-of-informationの定理ではない。
- Alternative direction（最大1件）: **B — cheap-first finite-time calibration**。ただしadaptive cheapの勝利は未確認。Fixed cheapで説明できる効果とadaptive追加効果を区別する。
- Spectral route: `retain_as_conditional_secondary_route`。既存M1を対照・診断に残すが、q=1 positive case探索を主目標にしない。
- 終了推奨: 旧multiple-window routeの再開、point accuracyだけを追うArnoldi精密化、HClの小さいsame-time headroomを救うfull-space gap/certificate取得を主線にすること、16 missing M1の一括補完、H-chain追加size、truthを見てq=1を作る規則変更。
- 終了しない主張: spectral informationがあらゆるregimeで不要、generic cheap calibrationが普遍的にsafe。どちらも証拠不足。

## 次の最小検証案はG2、今回は実行しない

`NEXT_MINIMAL_VALIDATION = HF_two_condition_frozen_rule_replay_design`

HF equilibrium/stretch150の既存6候補だけを対象に、別protocolでS1A Rules 1–3を変更せずB2/q/H1をreplayする案を推奨する。両条件を全部含め、truthからgeometryを選び直さない。既存cheap four-gamma、M1、truth、separate-arm costが揃うため、新PF/H action、M1、truthはすべて0の案である。

まずsubsetとfield projectionを独立にfreezeする必要がある。元の4-condition S1AのDを解除・改称して実行するものではない。既知development結果のreplayであり、prospective validation/holdoutではない。Costが揃わなければunknownとし、combined runtimeのhard boundを作らない。

このレビューではqやB2/H1新decisionを計算していない。候補として最も情報利得が大きい理由は、追加取得なしで「cheap instability gateが、既知の条件依存margin問題を見逃すか」を反証できるためである。q=0継続もgate failureも有効な結果として扱う。[具体的範囲と停止規則](next_validation_options.md)を参照。

## 人間の承認が必要な事項

1. 主線C、代替Bへの再定義と、selective positiveを必須としない着地点。
2. G2のHF-only development replayを別protocolとして許可するか。
3. 後続のpractical effect size、classical-cost ceiling、noninferiority margin。今回は未解決のまま保持する。
4. 投稿前の差分文献レビュー。外部照合は実施したが新規性は確定していない。

この4点の承認前に研究現状ページを更新せず、HCl frontier生成、LiF、追加分子、C1/D2-B、外部estimator実装、科学計算、pushへ進まない。

## レビュー資料の入口

- [研究経緯と改訂RQ](research_question_review.md)
- [4方向の比較とranking](direction_comparison.md)
- [新規性・先行研究の照合](novelty_assessment.md)
- [3つの論文着地点](publication_landing_options.md)
- [次検証の比較・最小案](next_validation_options.md)
- [機械可読decision](decision.json)、[provenance](source_registry.json)、[manifest](manifest.json)
