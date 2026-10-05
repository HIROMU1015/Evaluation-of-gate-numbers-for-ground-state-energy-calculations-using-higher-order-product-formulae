# G2後の方向比較 — レビュー用更新

これは `governance_scope`。旧比較のranking **C > B > D > A** を暫定的に保持するが、新しい数値scoreや客観的順位の証明は作らない。ここでのDirection Dはspectral routeをnegativeとして閉じる研究案であり、G2分類 `D_gate_false_negative` と無関係である。

| Direction | G2による更新 | レビュー上の位置付け |
|---|---|---|
| C decision value / observed regimes | cheap stabilityと必要marginの乖離を具体的に追加できる | 暫定主線。positive spectralを必須にしない |
| B cheap-first / cheap adaptive | Fixed cheapはsafe対照を持つが、現B2はHF eqでunsafe | Cheap-first baselineは保持。Adaptive新方式の優位・安全性は主張しない |
| D spectral negative / route closure | H-chainの限定negativeは維持。ただしHF M1はsafeでcommon-margin対照差もある | 全spectralの不要性へ一般化しない。限定節の候補 |
| A selective spectral primary | HFでもq=0、H1改善0、false negative。q=1 positiveとcombined costは依然未取得 | 現gateを主方式に採用せず、positive selective論文を結論先取りしない |

G2はCそのものの成功を実験的に証明したのではない。Cが観測されたmixed/negative evidenceを過大解釈せず統合しやすい、という研究方針上の理由である。

「cheap-firstをbaselineにする」と「truthで選んだsafe gammaを新policyにする」は別。Spectralはconditional comparatorとして残すが、結果を救うための追加Arnoldiやwidth調整は行わない。方針の最終採否は人間レビューに戻す。
