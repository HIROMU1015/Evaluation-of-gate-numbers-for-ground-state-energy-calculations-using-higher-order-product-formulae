# H-chain追加scienceの完了受理と停止境界

2026-10-06のユーザー提示レビューを承認済み判断として記録する。Track RとTrack Gは完了扱いとし、H-chainの新規科学計算はいったん終了する。Codexによる新たな研究方針・RQ・中心claimの決定ではない。

| Track | 元の完了status | 完了レビュー対象の公開snapshot |
|---|---|---|
| R：H6/H7/H8 rank診断 | `hchain_m1_rank_convergence_complete_review_required` | `0c40a3d7987e0961262bfd38bbb214a9e2946824` |
| G：H6 geometry truth-only continuation | `hchain_h6_geometry_sweep_truth_continuation_complete_review_required` | `1e03a659f3111623fa2b7afc3d8a87eeda1f4730` |

Track Gのprediction freezeは `61ae95edce8c4a25167521c0e6e95a83c3cbc4bb`、ground freezeは `1e5d66a4914bc50a8afa55baa578cca55a227979`。途中のserialization/import-guard failureとその時点の未完了記録は履歴に残す。今回の成功・完了受理を理由に過去のfailure記録やfreeze済みstatusを書き換えない。

## 承認された整理

- H6 geometryの固定gamma1.01は15/15座標・5/5 geometryでsafe。gamma1のpost-hoc診断は12/15 safeで、unsafeはR1.6の3座標だけ。最大gamma_reqは約1.00218。
- general-molecule prospectiveの同じ固定gamma1.01は選択decisionで6/13 safe。H-chainでsmall marginが足りることを一般分子へ一般化しない。両者のcandidate/B0 contractは異なるため、同一設計の因果比較や合算成功率とも扱わない。
- Track Gのrank8 point改善/悪化と、Track Rのrank16/32 point改善後もsame-time cheapに対するbudget advantage 0/9という結果を分ける。M1 resource value不足をrank8 point errorだけでは説明しない。ただし全rank・全系についての不可能性証明ではない。
- PF/H-reference誤差分解は同一H・sector・energy origin・physical branchの対応を確認できたH-chain tupleだけに限る。shiftの一致を絶対PF固有値の高精度回収やcertificateと同一視しない。
- 約33%のB0比削減は主に固定時刻・先頭モデルの構造で説明される。安全性の実測と構造的削減を分離し、spectral calibrationの増分利益に帰属させない。

## 許可しない後続作業

H9/H10、追加geometry、rank64、追加gap/truth、gamma/width/gate調整、q=1例の探索、失敗条件の救済を自動実行しない。Track G/Rの再実行やformal budgetの変更もしない。再開が必要なら、GPT側が主張上の不足と範囲を判断し、ユーザーから対象・座標・作用上限・truth access・停止点の別承認を受ける。

許可済みの後続は、既存公開scalarのevidence mapとレビュー資料の整理。Direction C、既存RQ、formal結果、原本sourceは維持する。
