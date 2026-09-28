# GPTへの依頼：D2R R1完了後のPF研究方針レビュー

次のGitHub branchに、第一・第二研究の閉鎖結果、D2R R0 failure ledger、D2R R1事後原因分離をまとめています。

- repository：`HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae`
- branch：`research-direction-review-after-d2r-r1-20260928`
- R1 result commit：`2cb78527ab8fd1fe99bffbdae46a5dfac1e325a3`
- 入口：`docs/pf_research_status_after_d2r_r1_20260928.md`
- 機械可読資料索引：`review_response/pf_research_direction_review_materials_20260928.json`

GitHub上の実ファイルを確認し、下記の目的で研究方針を批判的に再設計してください。要約だけを前提にせず、CSV/JSON、固定hash、decision、source/resource auditまで照合してください。

## 重要な境界

1. 第二研究の正式判定は`complete_no_benefit`で閉じています。R1を使ってこの判定を変更しないでください。
2. R0/R1は閉鎖済み4条件を用いたpost-hoc development diagnosisです。独立検証、preregistration済み有効性評価、新規ホールドアウトとは扱わないでください。
3. R1のstatusは`r1_complete_stop_for_research_direction_review`、`r2_authorized=false`です。
4. 今回依頼するのはレビューと次protocolの設計だけです。コード作成、計算実行、新規数値生成、threshold調整、分子・PFの選定を実行しないでください。
5. negative result、停止記録、local reconstruction bridge失敗を欠陥として消さず、設計上の証拠として保持してください。

## 必ず読む資料

次の順に読んでください。

1. `docs/pf_research_status_after_d2r_r1_20260928.md`
2. `review_response/second_study_safe_time_domain_completion_report.md`
3. `artifacts/server_second_study_safe_time_domain_phase_b_20260928_d4dd42f/decision.json`
4. `artifacts/pf_candidate_validation_r0_20260928_05649f1/report.md`
5. `artifacts/pf_candidate_validation_r0_20260928_05649f1/failure_ledger.csv`
6. `artifacts/pf_candidate_validation_r0_20260928_05649f1/selected_coordinate_plan.csv`
7. `artifacts/server_pf_candidate_validation_r1_20260928_fba3383/report.md`
8. `artifacts/server_pf_candidate_validation_r1_20260928_fba3383/coordinate_proxy_results.csv`
9. `artifacts/server_pf_candidate_validation_r1_20260928_fba3383/strategy_cause_decomposition.csv`
10. 同R1 directoryの`decision.json`、`resource_audit.json`、`source_manifest.json`、`manifest.json`
11. `review_response/pf_candidate_validation_r1_protocol.json`とR1のcache/test/source-gate amendment
12. `docs/pf_data_use_ledger.md`と`docs/current_research_status.md`

資料間に矛盾があれば、推測で埋めず、path、field、値を示してください。指示書の存在だけで実行済みと判断せず、`decision.json`、completion marker、result commit、manifestを優先してください。

## まず監査してほしいこと

- 第二研究の`complete_no_benefit`へ至ったbenefit checkを正しく再構成できるか。
- R0のunsafe 6/16とdeduplicated 10 coordinatesが、R1の入力と一致するか。
- R1の分解

\[
f_{\mathrm{model}}-\delta_{\mathrm{direct}}
=(f_{\mathrm{model}}-g_{\mathrm{CISD}})
+(g_{\mathrm{CISD}}-g_{\mathrm{exact}})
+(g_{\mathrm{exact}}-\delta_{\mathrm{direct}})
\]

  が16行でclosureし、固定materiality/2倍dominance規則と報告分類が一致するか。
- LiF平衡の大失敗、LiF伸長のstate成分、HCl平衡のcurrent failureとmultiple-window success、HCl伸長の停止判断について、現文書の因果表現が証拠の強さを超えていないか。
- CISD-local 11/16、exact-local 15/16というcounterfactualをどこまで方法設計に使え、どこから外部妥当性を主張できないか。
- R1が新規direct truth 0、Phase A runtime byte identity、source override exact 1・unlisted difference 0を満たすか。

## 方針選択で答えてほしい問い

次の候補を相互排他的と決めつけず、主仮説、補助仮説、見送る案に整理してください。

- selected candidate timeでのlocal model recalibration
- LiF型に対するstate-sensitive calibration
- HCl型に対するeigenvalue寄りsurrogateまたはbranch-aware spectral method
- uncertainty-aware budget allocation
- high-accuracy fitより安全なrobust decision rule
- 条件ごとに取得情報を変えるadaptive information acquisition

特に、R1が示唆する「次に一種類だけ情報を得るなら、既存HCl selected pointsでのPF固有ベクトル重なり・固有位相branch identity」という候補を、費用、識別力、既存truthへの依存、将来の運用可能性の観点から評価してください。より良い一種類があるなら、同じ情報予算で置き換える理由を明示してください。

## 提案してほしい次段階

R2を直ちに実行する指示ではなく、まず最小の`protocol-design pilot`を設計してください。少なくとも次を具体化してください。

- 一文で表した研究目的と、否定可能な主仮説。
- どのR1所見がその仮説を支持し、どの所見が反証し得るか。
- 取得する情報を一種類に制限するか、制限しないならその必要性。
- 使用を許す既存データ、development条件、将来の完全未使用holdoutの分離。
- 入力、出力、座標数、PF、state、truth access、計算上限。
- 事前固定する評価指標、成功条件、no-go条件、停止規則。
- pilot後に本preregistrationへ進むgateと、研究を閉じるgate。
- leakage防止、hash/commit固定、Phase A/B境界。
- negative resultでも残る論文上の価値。

同じ4条件で案を選び、同じ4条件を独立評価に再利用する設計は不可です。既存4条件はdevelopment/cause-diagnosis専用として台帳化し、将来holdoutは方式固定後に一度だけ開く設計にしてください。

## 出力形式

次の順序で回答してください。

1. **監査判定**：資料の整合性、未解決のidentity問題、研究を止めるべき問題の有無。
2. **確定事実 / 合理的推論 / 未検証仮説**：三列で明確に分離。
3. **条件別cause table**：LiF平衡、LiF伸長、HCl平衡、HCl伸長について、観測、支配成分、解釈の限界。
4. **研究方針の順位付け**：主方針、補助方針、見送る方針と理由。
5. **最小protocol-design pilot**：実行可能な固定仕様。ただし実行はしない。
6. **将来のpreregistration骨子**：development/holdout、成功・停止規則、情報・計算予算。
7. **論文化方針**：現時点で言える主張、言えない主張、negative resultの位置付け。
8. **次の意思決定**：人間が選ぶべき事項を最大5件に絞る。

## 禁止する提案

- 結果を見た同じ条件でthreshold、候補時刻、fit次数、marginを調整し、それを検証と呼ぶこと。
- R1を独立ホールドアウトまたは第二研究成功の証拠として扱うこと。
- 失敗条件を別分子・geometry・basisへ差し替えること。
- 複数の新情報を無制限に追加し、どれが効いたか識別不能にすること。
- direct truthを運用時入力とする方式をoracle-freeと呼ぶこと。
- 数値を追加確認するためだけの無目的なR2/R3や新PF探索。

最終的には、次に何を計算するかではなく、**どの不確実性を、どの最小情報で、独立性を失わずに減らす研究へ組み直すか**を決めてください。
