# 新しい独立研究テーマ：静的調査handoff

2026-10-16 JST。**条件付き候補は1件。正式採択、新規性の確定、科学実行承認は行っていない。** 今回は科学的知見・algorithm・情報費込みの実用価値と技術的実現性を調べ、論文化・投稿は評価していない。

## 1. T1：trap認証の取得費を含むPF位相推定の有限精度設計

### 中心的な研究課題

deterministic PFを用いるsingle-ancillaのenergy推定について、trap回路で得るlogical output errorの上界を使い、**所定の精度・失敗確率に対して、time schedule、PF discretization、target/trap shotsをどう選ぶべきか**を問う。推定不能ならabstainすることも結果とする。

noise率を既知の指数減衰lawとして与える場合と、認証情報を追加回路で取得する場合を分ける。単なるPF cost proxyの再ランキングではなく、測定recordからenergyを推定するプロトコルと、その情報取得を含めた資源の問題である。初期対象はdeterministic PFに限定し、PR/RTEの方式変更やPF係数探索は含めない。

### 最も近い既存研究と差分の根拠

logical accreditation `2508.05523v3`はTrotterized logical circuitのTVD/observable誤差を扱い、§IV.BでQCELSのような後処理を解析対象外とする。一方、同論文はそのようなapplicationへの適応可能性も述べるため、**単にQCELSへ接続することを新規claimにはできない**。[L17]

noise-aware QCELSはglobal depolarizing law、rate calibration、gap/overlap条件を用いる。EUMLEはnoise characterization/quasiprobability情報を用いる。H2の既存EFT比較もPF・RPE/QCELS・surface-code費用を扱っている。[L03] [L06] [L04] VPEのstate-return検査も強い近接対照である。[L23]

残す差分候補は、これらの情報契約を比較した上で、**実測した誤差上界の取得費を含めると、どの推定scheduleが実行可能で、どの条件では認証が利益を消すかを具体化すること**である。同じ問題を既存研究が未解決とする証明は得ていない。追加の文献照合と、独立した科学的判断が必要な候補である。

### 科学的価値と否定的結果の価値

肯定的な場合は、既知noise modelやexact spectrumを運用時に与えず、明示したnoise・state priorの条件で、認証情報により使える時刻/回路/shot配分が変わることを示せる可能性がある。精度だけでなく、同じconfidenceと同等情報の強い対照に対する総取得費が評価対象になる。

否定的な場合も、認証費、保守的なPF bound、state prior、alias/混合のどれが実行可能性を支配するかを、固定した小系・noise family・資源契約の範囲で区別できる。単に試した候補が負けただけで全認証法のno-goにしない。既知境界の自明な合成に留まると分かった場合は、**独立研究としての差分不足**というテーマ選定上の結論を受け入れる。

### 必要実装と技術的実現性

既存H生成・Pauli grouping・PF composition列、公開QCELSのclassical fit、公開Qiskit RPEのcircuit callbackを参考にできる。[HAM] [PF] [C02] [C05] [C06] ただしQCELS著者codeはspectrum/populationからのsignal generationを含み、そのまま実データ取得器とはならない。H2公開codeのexact state準備もbenchmark oracleとして分離する必要がある。

大きな追加部分は、logical target/trap compiler、state準備を含むnoise semantics、認証recordとH-test shot record、有限標本confidenceを扱う推定interface、全費用の会計である。L17の著者実装の所在は確認できなかった。既存codeのinstall/実行互換性も未検証である。

CPU affinity 32、host memory metadataを確認したが、GPU driverは利用確認に失敗した。少qubitの機能試験はCPUで検討可能という静的評価に留め、FT大系simulationやruntime利益を実証済みとはしない。[PROVENANCE]

### 最低限、将来何を検証する必要があるか

1. **差分・保証の接続を先に確認する。** L17のTVD上界が何を認証しないか、QCELS/RPEのoverlap/alias条件、VPE/EUMLEとの情報差を確認する。既知結果で同じ設計が完了していれば候補を取り下げる。今回新証明を作ってこの不足を埋めていない。
2. **別承認があった場合の小系機能試験。** fresh/publicな2〜4 system-qubit程度のHamiltonian、1 ancilla、少数time levels、S2/S4、明示したprepared state。真値は採点専用とし、calibration/selectionへ戻さない。FS-R1の凍結入力・truthを使わない。
3. **強い対照と同じ目的量で比較する。** model-known noise-aware法、VPEを採る場合のunpreparation/postselection費、global認証配分、time別配分を比較。coverage、abstention、最大depth、全target/trap/state-preparation費を別々に報告する。

これは将来の検証の目的・規模の案であり、実行契約、座標・閾値、計算予算、科学実行許可ではない。adaptive選択を行う場合の同時confidenceやdata reuseの正当性も未確立である。初期検討では固定scheduleと独立calibration/main recordsを優先して、その問題を隠さない。

一つのfit内では共通のPF wordとそのinteger powersを出発点とし、時刻ごとに異なるeffective Hamiltonianを作って同じfrequency modelへ渡さない。PFの選択はまずprotocol単位で比較する。time-dependentなPF/stepの切替まで認める保証は未検討である。

### 実行費用と情報上の制約

trap meanの精度を厳しくするとshot負担が二乗則で増えるという既知コストがある。trap数がqubit数に依存しないことは、trap回路・state準備・logical compilationが無料であることではない。[L17] PF/synthesis近似は別のboundが必要で、認証がtightでもHamiltonianへの誤差予算が残らない場合がある。

十分なtarget overlapやisolating energy windowが取得できなければ、true ground-stateのenergy保証に進めない。既知noise率・exact state・exact spectrumを無料に与えたoracle-assisted比較は診断として分離する。logical/physical資源、古典計算費、sampling費の単位を混ぜない。具体的なruntime・speedupは未測定である。

## 2. 既存研究との重複判定

| 既存研究 | T1で越えてはいけない境界 |
|---|---|
| U1-AR、U3/H05、U4 | AR閾値・高次係数取得・サイズ移送の追究を再開しない。C1/E4/C4とSTOPを維持。[U1] [U3] [U4] |
| 第一研究formal / FS-R1 | 既存safe/efficient分解の再命名にしない。S4否定結果とclaimは不変。Phase B未承認・truth barrierを維持。[CLAIMS] [FSR1] |
| 第二研究Direction C / U7 | spectral point/width/資源価値と重なる部分は既知。T1は新しいhardware trap測定とlogical noise・有限標本推定を必須入力にする。ここを外してwidth法だけを作るなら既存scopeへ戻る。[DIRC] |
| PR Track A | 有限時間signal精度と測定込み回路資源の既存研究。PR/DF方式の資源順位や不足を再評価しない。[PRA] |
| PR Track B | randomized coherent mean signal、tail構成、normalization、proposal/合成の既存研究。T1では変更しない。[PRB] |
| R5 | 指定PR repositoryの旧計画§9でrandom-tail負担を含むPF係数設計を確認。今回のユーザー指示に従いPAUSEを維持。現在のPAUSE原本を回収済みとは記録しない。[PRR5] |

内容上の隣接はあるが、既存状態を変更してT1へ合流させる承認はない。T1の独立scopeが保てるかも、将来の正式採択前にユーザー/GPTが判断する事項である。

## 3. 他の候補を残さなかった理由

Aの通常QCELS＋PF、Bの単純な次数/noise/合成精度最適化、CのDF/BLISS/軌道/対称性の一般的組合せには近い一次研究があり、今回具体化できた差分が不足した。[L01] [L04] [L06] [L08] [L09] [L10] [L11] [L12] エネルギー差の相殺観測も既報と旧PR R7に近い。[L13] [PRR5]

これは各分野の研究価値の否定ではない。件数を3に揃えず、具体的な入力・保証・費用まで比較できるT1だけを条件付きで残す。詳細は[landscape][LANDSCAPE]と[evidence matrix][MATRIX]。

## 4. 推奨する次の判断順序

推奨するのは、**科学計算の開始より先に、T1の差分と情報契約を判断すること**である。L17の後続研究・著者実装、finite-sample PEとVPE/EUMLEの比較を追加確認する必要があるか、測定で得るgammaとstate priorの組を現実的な入力と認められるかをユーザー/GPTへ返す。

その上で、既知結果の合成・単なるresource再会計に留まらないと判断された場合にだけ、別件として最小検証の対象・noise条件・oracle access・費用上限・停止点を承認する。今回、数学的証明、新実装、synthetic science、分子計算、benchmarkを開始する承認はない。

「残った候補1件」は採択推奨の確定ではない。現段階で最も必要なのは、差分が残るかを絞る判断であり、論文化可能性や投稿戦略を決めることではない。

## 5. 成果物・保全・Mandatory STOP

保存先は `docs/research_exploration/quantum_chemistry_independent_topics_20261016/`。baseは既存完結commit `adb17c423fee304a87e5d49027f0c8f966dc799c`、新規branchは `quantum-chemistry-independent-topics-static-20261016`。本書、landscape、evidence matrix、[provenance.json](provenance.json)の4資料だけを公開する。PDF、著者code、既存研究artifact、private dataは新規公開しない。

U1/U3/U4 STOP、R5 PAUSE、第一・第二研究とPR Track A/Bのscope、FS-R1 Phase B未承認を維持する。既存SOURCE/results/protocol/manifest/claim/authorization/grant/STOP、元worktreeのdirty/staged/untrackedを変更しない。

**新規科学計算・simulation・Hamiltonian/PF生成実行・保存値再解析/再fit・新証明/反例・科学実装/benchmark・研究正式採択は0件。** 静的文献/source読取りと文書/Git/hash確認のみ実施。公開後のremote SHA・4 blob・byte・SHA-256を照合して最終回答で固定identityを報告する。

**Mandatory STOP：静的調査の公開・照合後に停止し、T1の採択、追加理論、実装、検証、旧研究の再開へ自動進行しない。**

<!-- fixed-source-references -->

[C02]: https://github.com/zhiyanding/QCELS/blob/0242c200d9c60f565443067d56e611c51e4fead8/qcels.py
[C05]: https://github.com/adbacze/qpe4earlyftqc/blob/563b763586fa55d67e79496c198167da177f8c74/H2_simulations/H2aRPE.py
[C06]: https://github.com/adbacze/qpe4earlyftqc/blob/563b763586fa55d67e79496c198167da177f8c74/packages/qpe_protocols/aRPE.py
[CLAIMS]: https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/adb17c423fee304a87e5d49027f0c8f966dc799c/PF_first_study_paper_claim_ledger_20260926.md
[DIRC]: https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/adb17c423fee304a87e5d49027f0c8f966dc799c/docs/second_study_v2/result_synthesis_20261005/approved_scope_and_rq.md
[FSR1]: https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/adb17c423fee304a87e5d49027f0c8f966dc799c/artifacts/pf_first_study_fs_r1_b0_phase_b_barrier_20261008/README.md
[HAM]: https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/adb17c423fee304a87e5d49027f0c8f966dc799c/src/trotterlib/chemistry_hamiltonian.py
[L01]: https://arxiv.org/abs/2211.11973v2
[L03]: https://arxiv.org/abs/2307.11257v2
[L04]: https://arxiv.org/abs/2403.00077v1
[L06]: https://arxiv.org/abs/2410.05369v2
[L08]: https://arxiv.org/abs/2602.18913v1
[L09]: https://arxiv.org/abs/2606.30741v1
[L10]: https://arxiv.org/abs/2304.13772v3
[L11]: https://arxiv.org/abs/2409.18277v2
[L12]: https://arxiv.org/abs/2605.31544v2
[L13]: https://arxiv.org/abs/2605.00745v2
[L17]: https://arxiv.org/abs/2508.05523v3
[L23]: https://arxiv.org/abs/2010.02538v1
[LANDSCAPE]: research_topic_landscape.md
[MATRIX]: candidate_evidence_matrix.md
[PF]: https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/adb17c423fee304a87e5d49027f0c8f966dc799c/src/trotterlib/product_formula.py
[PRA]: https://github.com/HIROMU1015/Partially-Randomized-Trotter/blob/93bf0bf3420683d9d20755cea856d3814b951233/docs/research/track_a_shared_research_status.md
[PRB]: https://github.com/HIROMU1015/Partially-Randomized-Trotter/blob/cc2f451324b7292ae50cef94ff794d46f225d892/docs/tracks/algorithm_codesign/m1s_g0t1_s0_formal_theory_contract_20261016.md
[PROVENANCE]: provenance.json
[PRR5]: https://github.com/HIROMU1015/Partially-Randomized-Trotter/blob/cc2f451324b7292ae50cef94ff794d46f225d892/partial_randomized_trotter_research_redesign_20260925.md
[U1]: https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/adb17c423fee304a87e5d49027f0c8f966dc799c/docs/research_audits/pf_u1_ar_c1_closure_20261016/decision_record.md
[U3]: https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/adb17c423fee304a87e5d49027f0c8f966dc799c/docs/research_audits/pf_u3_h05_e4_closure_20261016/decision_record.md
[U4]: https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/adb17c423fee304a87e5d49027f0c8f966dc799c/docs/research_audits/pf_u4_candidate_exploration_closure_20261016/decision_record.md
