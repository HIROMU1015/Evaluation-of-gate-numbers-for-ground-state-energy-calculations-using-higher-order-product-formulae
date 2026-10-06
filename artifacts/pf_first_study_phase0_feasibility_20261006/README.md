# 第1研究 Phase 0 feasibility audit（2026-10-06）

**推奨：GO_response_pilot。GPT/ユーザーの研究判断待ちであり、pilot実行許可ではない。**

目的は、state substitutionが介入に値するfailure modeかを、保存scalarからmechanism・unsafe方向・resource headroomに分けて確認すること。formal第1研究、79/128、S4 no-benefit、gamma=1.01の6/6安全という結果は変更していない。新規science calculationは0。

H4のfit_ok/resolved 588行ではoracle state-removalで絶対誤差総和が89.2808%減り、同符号の過小評価356行の340行でstateが最大のunsafe寄与だった。Phase-averageのstate誤差減少はH4のresolved quartetで26.9828%、PF別で23.57%-51.10%。これはexact-groundを含むcontrolled状態族の機構診断であり、実用校正法の達成結果ではない。

N2/COのsame-time cost-free校正headroomは7.20%-13.79%。HFは0.41%-1.26%、同じPF・同じcap内のtruth-free上界も1.58%-1.66%で、time-domain制約が残る。実分子のheadroomをstate correctionが回収できる割合は未確立。

## Source identityと読み順

起点snapshot：`c515562f1c00b5402d5ca266852986ba12ca4002`。
元result commitとverified snapshotは[source registry](source_registry.json)の別fieldに記録した。16 authorityと15 supporting/protected sourceの31 blobを固定snapshotと照合している。既存資料は複製・変更していない。

1. [Report](report.md)：RQ0-1〜4、限界、論文への含意、最小pilot案。
2. [機械可読な推奨](feasibility_decision.json)：GOの理由、未確立事項、未承認の次段案。
3. [Margin capacity](margin_capacity_first_study.csv)・[Resource headroom](resource_headroom.csv)：6条件の安全性と費用。
4. [Mechanism / budget summaries](mechanism_and_budget_summary.csv)・[Phase summaries](phase_group_summary.csv)：PF、state family、time別の連続値。
5. [Analysis protocol](analysis_protocol.json)・[Metric dictionary](metric_dictionary.md)・[Source registry](source_registry.json)・[Verification](verification.json)・[Tests](tests.log)・[Publication manifest](publication_manifest.json)。

## 再現

リポジトリrootで、まだ存在しない新しいoutput directoryを指定する。stdlibのみで既存CSV/JSONを読む。既存outputを上書きする指定は拒否する。

```bash
PYTHONDONTWRITEBYTECODE=1 python review_response/audit_pf_first_study_phase0_feasibility.py --output /tmp/first-study-phase0-audit-reproduction
PYTHONDONTWRITEBYTECODE=1 python -m pytest -q -rs review_tests/test_pf_first_study_phase0_feasibility.py -p no:cacheprovider
```

Builderは数値CSV/JSONを再現する。README/report/decisionは今回の結果に基づくレビュー用の編集文書である。Manifestは自身を除外し、handoff commitの自己参照を含めない。Publicationの実確認はGitHub handoffで別途報告する。

原本のHamiltonian/state/vector/unitary/pickleを開いたり公開したりしていない。science runnerをimportせず、PF action、ground solve、truth、fit、threshold/selector変更、追加分子/geometry/PF探索はすべて0。Phase 0終了時に停止する。
