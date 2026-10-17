# 既知法との対応・横断重複・最新資料の差分

2026-10-18 JST。構成研究と並行して一次文献・既存索引を確認した。全分野のpriority調査、既存証明の詳細科学レビュー、保存科学数値の再解析は行っていない。読取り範囲とraw hashは[registry](source_registry.json)。

## 1. 既知の部分空間冷却・cycleとの比較

| 一次資料 | 実際に確認した既知構成 | 今回との関係・未輸入の保証 |
| --- | --- | --- |
| Langbehnほか 2311.05258v2 [L01] | §IIのdetector/reset、hot/cold subspace、Eq12のnilpotent jump・共通kernel・image条件 | hot側全体からcold側への複数jumpは既知。今回はPを電子occupation flagと係数下界で選ぶ小class。本文のAKLT/MG到達性/mixingをH5へ輸入しない |
| Molpeceres–Lu–Cirac–Kraus 2503.24330v2 [L02] | §II.3 Eq6の有限subcycle合成、複数周波数/ランダムcycleの定義、coolingとDSPの区別 | 「複数cycleにする」自体は新規性ではない。今回C9はlogical gateによる既知resetで、自然なH+浴の発展とは同一視しない。論文の弱結合rate/性能を使っていない |
| Zhanほか 2503.15827v3 [L03] | §IIのfiltered jump、HのHeisenberg evolution積分、複数jumpのsplitting | 固有basisを列挙しないjump生成は既知。filterを呼ぶだけを新規則としない。本文のblock-encoding経路をD1下へ無断採用しない |
| Ding–Zhan–Preskill–Lin 2508.05703v2 [L04] | 既読Algorithm I/Thms1–3：random system–bath、reset、mixing/gap依存 | reset/1 bath/forward evolutionの既知性を保持。今回のelementary channelはH simulation oracleを使わないが、それだけで強い新算法とはしない |
| Schlömerほか 2605.01029v1 [L05] | 既読symmetry-preserving local toolbox、random bath、ETHに基づく接続性の限定 | spin-exchange等の複数fermion couplerも既知。一般相互作用のmixingはconjecture/未確定部分を区別。今回に一般収束保証を足さない |
| Marti–Mansuroglu–Hartmann 2403.14506v2 [L06] | 既読§§2.2–2.3：ideal/free coupler、spectroscopy、低energy subspace access | 今回はfree/eigenbasis couplerの前計算を使わずoccupation flagを使う。ただし既知conditional resetと対角試行stateへ戻り、一般の新選択則にはならない |

## 2. 既知法への還元をどこまで示したか

今回の3-jumpを、単に既知のgateから作れるという理由でBにしない。**生成後のチャネルそのものが、Pのweak measurement＋成功branchだけ既知bへreplacementするinstrumentと一致する**ことを示した。source labelの情報は環境へ捨てられ、Q側のstateとcoherenceはそのまま残る。θ=π/2はprojective flag＋conditional reset。この対応は操作・coherence・出力を含む。

Pの選び方も今回のclassでは、保存されたn2/n4、既知occupation support、簡単な係数norm下界で尽きる。有効なPを一般に探す新しいalgorithmや、baselineを越える費用/保証差を示していない。よって具体的なcycleは**既知法への還元**、独立新構成候補は0件と整理する。

[L01]のlocal冷却と今回のglobal source-P resetが同じ完全algorithmである、または今回の全係数不等式が同論文の定理に同じ形で載る、とは主張しない。適用対象・input/outputの異なる論文を無条件に包含と呼ばない。未確認は一般P選択・更なるcycleの新規性/費用であり、文献未発見を新規性へ格上げしない。

## 3. 既存横断整理との分担

[Evaluation旧対応表][X02]・[状態表][X03]、PR[4系列][P01]・[20方向][P02]・[SOURCE索引][P03]を再利用し、過去研究を全て再調査していない。

| 近接領域 | 今回との違い・維持する境界 |
| --- | --- |
| 第一・第二研究、FS-R1 | 保存PFの固有枝/proxy/経験的widthとbudget情報が中心。今回は実state人口を変えるCPTP列。相互のsafe/精度を新保証へ流用しない |
| P1*/J1、Q1 | unitary生成bus閉路や全固有basis挿入則を再開していない。bathへのentropy放出を実操作として許す別課題。ただしresetという語だけで独立性を認定しない |
| R1-P、A2/EW2 | PFのrestricted norm/相対log/読出し保証と、state preparationのpopulation移送は異なる。共通するPSDやtail評価を新原理としない |
| N3 occupation certificate | 既存の縮約/証拠/encoding/accessと、今回の既知occupation flag resetは同一結果とは判定しない。N3の旧CLOSED等を変えない |
| PR Track A/B、M1-S | signal/乱択law/±label/費用会計の系列へ合流しない。今回新しいPR費用や全round E0優位を計算しない |

## 4. 今回新たに確認した公開差分

remote先端を確認したところ、以前の2-branch差分[D01]以後に次の4公開branchが追加されていた。更新を必要以上に追わず、handoff/結果文書の関連箇所だけを固定参照した。

| 固定commit | 最新記録から確認した差分 | 本研究での扱い |
| --- | --- | --- |
| `c62fe99d29e7edcaf0cb655d789d297890709a29` [N01] | A2実用preflightは **INPUT_CLASS_FOUND_CERTIFICATES_INCOMPLETE**。入力classの既知経路とcertificate/accessの未完成を分離 | A2 NOT_ADOPTED、A1 CLOSED、K1-F未承認/未実行を維持。分子用証拠完成やstate無料accessを仮定しない |
| `db1819587df36ee8833b37227ca0083faa0408ec` [N03] | EW2監査は **VALID_SYMBOLIC_ADVANTAGE_CONDITION**、実用/総費用には **NO_COMPARATIVE_ADVANTAGE_ESTABLISHED** | 低energy windowの紙上statementを今回のstate準備の成立証拠へ流用しない。科学採択/計算承認と区別 |
| `96e69a01d1fae7a402aac2c4efa570a59f8cc7a0` [N05] | H8主要6軸の実測単価反映による限定再会計が既に完了、PASS_MANDATORY_STOP | 「PR削減率未更新」は旧差分当時の観測として保存し、現在の事実として繰り返さない。今回は数値表の転記/再会計/rerankをしない |
| `621d7d7bed183862db8d9f01b6fdb4406f942309` [N06] | H4/H8等の証拠区分・比較条件・未解決項目が整理済み | 新しい母平均保証、厳密bias、全候補実測、end-to-end E0費用を認定しない。履歴を再作成しない |

N05の文書result commitと実行SOURCE `aa984d98a7b438dc953a829a24fe3d7edc9d0a6b` は区別する。N01/N03のpayloadはそれぞれ `370372e0160ce181f17a09ea552064e6e9f493bc` / `87ac2233fb454ce2f7ef7200f16a3b43ee9d63c0`、最終snapshotは上表であり、同じ役割へ統合しない。過去の「未更新/未実施」記録は上書きしない。

この差分参照は新しいA2/H8科学レビューではない。fixed resultの状態を読むことと、元runtime・全引用証拠を再監査することを分ける。他系列のgrant/STOPを今回の実行権限に使わない。

## 5. 判断と未確認範囲

今回、成立した具体的cycleはB、同一rank-one反復/非不変Pへの固定resetの障害はC、flag-breaking Hのcoherenceを取り込む新生成則はD。新規性・資源優位・一般NO-GOは認定しない。既知のcoarse measurement/resetを越える操作選択・進捗・費用の差が必要であり、そのための追加探索は公開後自動開始しない。

[L01]: https://arxiv.org/html/2311.05258v2
[L02]: https://arxiv.org/html/2503.24330v2
[L03]: https://arxiv.org/html/2503.15827v3
[L04]: https://arxiv.org/html/2508.05703v2
[L05]: https://arxiv.org/html/2605.01029v1
[L06]: https://arxiv.org/html/2403.14506v2
[X02]: https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/609a63231ee0786cf8da31f6b33358acfd6f2548/docs/research_exploration/cross_repository_overlap_survey_20261017/algorithm_improvement_overlap_matrix.md
[X03]: https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/609a63231ee0786cf8da31f6b33358acfd6f2548/docs/research_exploration/cross_repository_overlap_survey_20261017/active_and_pending_research_map.md
[P01]: https://github.com/HIROMU1015/Partially-Randomized-Trotter/blob/d09ba606a9fceef806a9313e3f7c43cd21d19e3f/docs/research/qc_four_track_strategy_handoff_20261017/strategy_handoff.md
[P02]: https://github.com/HIROMU1015/Partially-Randomized-Trotter/blob/d09ba606a9fceef806a9313e3f7c43cd21d19e3f/docs/research/qc_four_track_strategy_handoff_20261017/overlap_and_progress_map.md
[P03]: https://github.com/HIROMU1015/Partially-Randomized-Trotter/blob/d09ba606a9fceef806a9313e3f7c43cd21d19e3f/docs/research/qc_four_track_strategy_handoff_20261017/fixed_evidence_index.json
[D01]: https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/c6419859029824a4ee8c3dfd3c8126fe585ffbe2/docs/research_exploration/cross_repository_two_branch_delta_20261017/review_readiness_delta_handoff.md
[N01]: https://github.com/HIROMU1015/Partially-Randomized-Trotter/blob/c62fe99d29e7edcaf0cb655d789d297890709a29/docs/research/qc_a2_practical_preflight_20261017/decision_handoff.md
[N03]: https://github.com/HIROMU1015/Partially-Randomized-Trotter/blob/db1819587df36ee8833b37227ca0083faa0408ec/docs/research/qc_relative_form_ew2_step_audit_20261017/decision_handoff.md
[N05]: https://github.com/HIROMU1015/Partially-Randomized-Trotter/blob/96e69a01d1fae7a402aac2c4efa570a59f8cc7a0/docs/research/track_a_h8_six_axis_reaccount_run01_results_20261017.md
[N06]: https://github.com/HIROMU1015/Partially-Randomized-Trotter/blob/621d7d7bed183862db8d9f01b6fdb4406f942309/docs/research/track_a_h4_h8_cross_system_evidence_inventory_20261017.md
