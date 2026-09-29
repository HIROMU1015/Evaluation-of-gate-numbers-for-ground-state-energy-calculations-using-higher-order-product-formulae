# PF研究の全体像｜成果説明用の短縮版

**2026年9月29日｜v1.0・Git evidence audit済み内部成果整理版**
詳細・sourceの所在は、本体レポートと主張・証拠台帳を参照。

## 何を明らかにする研究か

本研究系列は、分子基底状態エネルギー推定に用いるproduct formula（PF）について、**どのPFが低コストか、その性能をどこまで信頼して予測できるか、追加の校正計算に費用を払う価値があるか**を調べる。出発点はH-chainでのPF性能比較であり、後続研究では、有限時間の誤差評価と実際に固定するQPE予算の関係へ焦点を移した。[S01](PF_research_claim_evidence_ledger_20260929.md#S01)[S02](PF_research_claim_evidence_ledger_20260929.md#S02)

## 第一研究で得られた中核成果

有限時間の予測とdirect PF固有値シフトとの差を、model/extrapolation、状態置換、proxy–eigenvalueの三成分へ分けた。H4と人工二準位系の固定128 caseでは79 caseが状態置換支配だったが、これは分子一般の普遍則ではない。[S04](PF_research_claim_evidence_ledger_20260929.md#S04)

さらに、校正、時刻、PF選択による資源損失を分けた。N₂/CO/HFのdevelopment 6条件では1%余裕付き凍結予算が全条件で目標を満たした一方、HFの費用は元2 PF・保存grid基準の約2.15倍、2.10倍だった。cap内の選択を完全に改善しても削減余地は約1.25%、0.32%に限られ、許容時刻域が主要な制約だった。追加の状態感度診断も固定比較では資源改善を示さなかった。[S03](PF_research_claim_evidence_ledger_20260929.md#S03)

ここでの中心的な結論は、**安全な予算、正確な誤差予測、低い資源費用は同じことではない**、という点である。

## 第二研究と原因診断で分かったこと

multiple-window情報による時間域拡張を、当時の独立LiF/HCl 4条件で一度評価した。3/4条件で目標を満たしたが、事前固定したbenefit条件には届かず、正式に`complete_no_benefit`で終了した。これはこの規則のnegative resultであり、時間域拡張一般の否定ではない。[S05](PF_research_claim_evidence_ledger_20260929.md#S05)

その後、同じ結果を使うR1事後診断で、LiF平衡にはmodel誤差、LiF伸長には大きいがsafe側のstate成分、HCl伸長の一部にはexact stateでも残るproxy–eigenvalue差があると分かった。一種類の精度改善だけで全ての資源判断を処理できると考えるのは適切でない。[S06](PF_research_claim_evidence_ledger_20260929.md#S06)

## 圧縮できる情報と、資源に使える情報は違った

D1はHCl既存6座標で、exact-ground由来の非対象スペクトル寄与を最大4clusterへ圧縮できる事例を示した。しかし、これは全情報を知った後の診断であり、4次元・4作用で取得できるという意味ではない。[S08](PF_research_claim_evidence_ledger_20260929.md#S08)[S09](PF_research_claim_evidence_ledger_20260929.md#S09)

D2-Aでは元CISDからの有限作用Arnoldiで点推定を得た。unwrap整数の座標系不一致を監査した後の採点では、6/6で目的shiftと整合し、最大誤差は約1.38×10⁻⁸ Haだった。ただし、付与した経験的幅によって1点を棄却し、予算を出した5点は目標を満たしたものの、主baselineより低予算は0/6だった。独立な一般化や厳密な枝認証を達成したわけではない。[S12](PF_research_claim_evidence_ledger_20260929.md#S12)

C0は、条件付きの鋭い幅に必要なfull-space gap、ground/reference、action-error等を整理したが、運用上の取得経路は未確立である。同じHCl時刻で校正を完全にしても、local CISD＋2%余裕からの改善上限は約0.33〜2.29%に限られるという保存算術も得た。[S13](PF_research_claim_evidence_ledger_20260929.md#S13)[S14](PF_research_claim_evidence_ledger_20260929.md#S14)

## 現在の到達点

| 得られたもの | まだ得られていないもの |
|---|---|
| 誤差と資源損失を切り分ける評価枠組み | 未知分子に一般化する低regret selector |
| 固定改善法のnegative resultと原因診断 | 普遍的に安全なmargin |
| HClにおける圧縮・高精度回収の限定的証拠 | 低費用なoperational certificate |
| 必要情報と同時刻利益上限の設計整理 | 大規模系・実機全体での資源優位 |

研究成果は、**性能→校正の信頼性→追加情報の価値**という流れで保持する。直近の未解決事項を全て解かなければ、それまでの成果が成立しないという構成にはしない。今後の研究候補は、有限の校正費用で時刻・QPE予算の判断を改善できる条件の比較であるが、その有効性は未検証である。

**今行うのは、この成果内容の整理と証拠のrepo統合である。新しい計算、C1、D2-B、LiF追加検証、独立holdout、新PF探索は自動的に開始しない。これは科学結果ではなく、今回の`governance_scope`である。**
