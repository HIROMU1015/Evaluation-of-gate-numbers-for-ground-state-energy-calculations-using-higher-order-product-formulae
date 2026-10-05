# G2を反映したRQ提案 — 最終freeze前

[旧RQレビュー](../research_direction_review_after_hchain_20261005/research_question_review.md)の数量定義・第一研究との接続を継承する。Direction Cはユーザーにより暫定承認済みだが、以下は最終RQ・方針文書の改稿ではなく、レビュー用候補である。

## Primary RQ候補

**有限時間PF-QPEの固定PF・状態・候補時刻・連続resource modelにおいて、追加校正情報はcheap-onlyに対してどの条件で安全な時刻・予算判断を改善し、その取得費用を評価できるか。**

現段階では「取得費用に見合う」を最適化済みと主張せず、費用が未測定なら未評価とする。価値は観測されたdecision utilityの呼称であり、一般的Bayesian value-of-information theoremではない。

第一研究は `F_model/F_margin/F_within/F_domain/F_PF` に損失を分解した。第二研究の問いはその損失を減らすためにどの校正情報が判断に必要かであり、estimatorの精度競争ではない。`H(F)=1-1/F` は他因子固定のalgebraic headroomで、介入の達成可能上限ではない。

## Secondary RQ候補

1. **Cheap stabilityとbudget safetyの境界。** H-chain適格6系とHF stretchではq=0/safe、HF eqではq=0/unsafe。共通ruleの反例は得たが、regimeを事前識別する新gateは未確立。
2. **Point accuracy -> width/abstention -> decision utility。** D2-A/C0では精度だけで低budgetへつながらず、H7/H8ではpoint精度自体も常に改善しない。HF M1 branch/coverageは6/6だがcondition-wise safe cheapを支配しない。
3. **追加情報量・取得費用の可評価性。** q=1 combined pathが未観測で、実測incremental costと実用effect thresholdは未確立。保存separate-arm costと今回のreplay時間を分ける。

## G2によって閉じた問い・残る問い

| 問い | G2後の状態 |
|---|---|
| HFでS1A Rules 1–3を変更せずsubset replayできるか | 別protocolで完了。旧4-condition S1A formal Dは保存 |
| 同じcheap gateでgeneral moleculeのfalse negativeが出るか | HF eqのdevelopment反例を確認 |
| H1が追加spectralを取得してdecisionを改善したか | q=0、変更0。q=1は未観測 |
| Spectralなしではsafe budgetを作れないか | 未証明。保存fixed gamma=1.10はHF両条件safe |
| 条件ごとの最小safe gammaをtruth-freeに選べるか | 未確立。Truth後のdiagnosticは新policyではない |
| 量子・古典の総合的優位があるか | 未確立。Combined costと許容ceilingが未取得 |
| 未使用分子へ一般化するか | 未確立。Known-development replayでholdoutではない |

`delta_direct`（signed shift）、`abs(delta_direct)`（QPE budget PF error）、`abs(delta_hat-delta_direct)`（point estimation error）、`w_M`（経験的width）を分離する。M1 width coverageを数学的certificateと呼ばない。Target gapの種類・alias・target identityはC0の未取得条件を保持する。

HFの2条件は既存pilot/bridgeと同じデータであり、新しい独立な2標本ではない。G2の6座標、H-chainの18座標をindependent samplesとしてpoolしない。H3は適用不能であり、scored effect=0ではない。

## 研究方針との関係

Direction Cならcheap-sufficient、accurate-but-no-decision-benefit、stable-but-unsafeという観測例を同じ問いで整理できる。最終的なRQ wording、secondaryの優先順位、情報費用を主RQのどこまで主張するかは[レビュー事項](review_questions.md)で決める。新しいpolicy開発や計算へ自動的に移らない。
