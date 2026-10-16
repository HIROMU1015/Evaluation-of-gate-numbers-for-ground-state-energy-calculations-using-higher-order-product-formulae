# 量子化学を中心とする独立研究テーマの静的調査

2026-10-16 JST。**新しい静的調査の承認に基づく候補整理であり、研究テーマの正式採択・科学実行承認ではない。** 論文化可能性・投稿先・論文構成は評価していない。

## 1. 調査結果と証拠の強さ

追加の検討に残すのは、**T1：trap認証の取得費を含むPF位相推定の有限精度設計**の条件付き候補1件とする。正式採択できるだけの新規性・資源利益を確定した候補はない。T1も、既知の境界を単に合成するだけなら独立テーマから外す必要がある。[HANDOFF] [MATRIX]

A（QCELS/RPE等）、B（論理誤り・合成・PF）、C（表現・分解・軌道）、D（化学的エネルギー差）を調べた。一般的な組合せの多くには、2022〜2026年の近い一次研究がある。以下の「残す／今回は残さない」は今回の技術的候補整理であり、既存研究に新しいGO/STOPを出す意味ではない。

一次論文25件の版固定PDFを取得した。ただし、**全文取得と全文読了・証明監査は異なる**。中核比較では関連する本文・定理のstatement・適用条件を読み、他はabstract/導入/該当節の確認に留めた。読んだ範囲はprovenanceの各論文entryに明記する。公開実装は5 repositoryの構成を確認し、そのうち4 repositoryの13 textファイルを固定commitで取得・静的確認した。install・import・実行・benchmarkは行っていない。

## 2. A：位相推定とPFの組合せ

| 方向 | 一次資料で確認できた到達点 | 独立候補とする際の不足 |
|---|---|---|
| QCELSとHadamard test | 複素自己相関のleast-squares推定、multi-levelのalias制御、初期overlapによる最大時間短縮は既知。MM-QCELSも既存。[L01] [L02] | 「PFで時間発展を実装してQCELSへ渡す」だけでは差分にならない。Hamiltonian evolution oracleと、実際のPF回路・有限shot・device noiseを分ける必要 |
| RPEと短深度推定 | Ni–Li–Yingは不完全初期状態を含む低深度法と保証を扱う。Nelson–BaczewskiにはH2のTrotterized RPE/QCELSとsurface-code費用比較がある。[L24] [L04] | 単一ancilla、状態混合、Trotter費用の併記だけでは独立性を示せない |
| noise-aware QCELS | global depolarizing law、ノイズ率の別測定、gap・overlap条件下での改良lossと精度保証がある。[L03] | 一般logical noiseを同じ指数減衰lawへ置換できない。ノイズ率取得費・prior情報の取得可能性を含める必要 |
| error mitigationとcircuit division | EUMLE/MSQPEはノイズcharacterizationとquasiprobability情報を用いる推定・費用trade-offを扱う。[L06] | 漸近的一致性、標準偏差、有限標本の被覆確率は同じ保証ではない。化学の主要資源例はTHC/qubitizationで、PFの実証に読み替えない |
| Trotter外挿・補間 | Chebyshev補間、Richardson外挿、短深度測定のconditioningと誤差解析は既知。[L14] [L05] | 単なるzero-step外挿を新提案にしない。観測量外挿の定理を、枝同定・ground-state選別込みの全推定器保証へ無条件に移さない |
| 論理出力のtrap認証 | logical accreditationはtrap結果からTVDと観測量誤差を制約する。論文§IV.BはQCELS等の後処理を対象外と明記する。[L17] | 実測認証とPF近似誤差を分離し、エネルギー推定の有限標本保証と全取得費へ接続したときに有用な設計差が残るかがT1の問い |

T1の根拠は、最後の境界と、既存noise-aware法が要求する情報の違いである。**先行論文に未記載という確認は、誰も解いていないことの証明ではない。** 認証によりPF誤差まで測れる、新しいground-state certificateが直ちに得られる、という主張は採用しない。

verified phase estimation（VPE）は入力状態へ戻すuncomputation/postselectionを使う既知の対照である。名称のverifiedを、trapからのTVD認証や任意ノイズに対する有限標本エネルギー保証と同一視しない。状態準備の逆回路とpostselection費用も必要になる。[L23]

## 3. B：論理誤り・合成とPFのcodesign

| 方向 | 近い一次研究と確認範囲 | 今回の扱い |
|---|---|---|
| ノイズ下のPF次数選択 | spin modelで数学的Trotter誤差とgate errorを合わせる研究が既にある。ここではabstract確認まで。[L25] | 「高次は深く、ノイズを含む最適次数がある」という一般論を新候補にしない |
| code distance・factory・推定法 | surface-code上の位相推定比較と、error correction/mitigation/circuit divisionのtrade-offが既知。[L04] [L06] | 既存gate数に失敗確率を掛けるだけの再会計は除外。新しいノイズ情報や推定規則が選択を変える必要 |
| 小角回転と合成精度 | 2026年のBothe等は角度依存のClifford+T混合・準確率・fallback、rotation別の精度配分、化学Trotter回路の費用を扱う。[L12] | 「非一様な合成精度＋PF」の単純案は残さない。channel近似の期待値推定と、controlled複素signalの保証は別途必要 |
| STARとsingle-ancilla/PR | Kanasugi等の分子資源評価、Akahoshi等のRUS並列化・注入領域更新がある。[L07] [L18] | partial randomizationやunitary-weight concentrationの再実装を独立候補にしない。PR Track A/Bとの重複も大きい |
| architectureのdepth改善 | biplanar SPOQCにはfSWAP回避、回転合成とlogical errorを含むjoint budget、RUSの並列失敗負担の評価がある。abstract確認まで。[L22] | ハードウェア依存の大きい方向。手元に同等の実装・評価基盤があるとは確認していない |

小角合成論文の「小step極限で費用が一定」という結果を、shot、状態準備、logical noise、architectureを含めた全PF・全推定器の費用一定性へ一般化しない。PF次数を比較し直す価値があることと、新しい独立研究差分を確認したことは別である。[L12]

## 4. C：Hamiltonian前処理・表現変換

| 方向 | 最も近い確認済み研究 | 新規性・実現性の境界 |
|---|---|---|
| DF/低rank分解 | Motta等の低rank表現、SPRINT/GRADEによる分解とPF設計がある。[L21] [L09] | DF導入や既存factorizationの置換だけでは差分にならない |
| BLISS・LP-BLISS | 指定電子数sectorの作用を保持しつつ外sectorを変え、LCU 1-normを減らす方法とLP化がある。公開QuantumMAMBOも確認。[L10] [L11] [C12] [C13] | LCU 1-norm低減は最終PF固有位相誤差・推定資源の保証そのものではない。BLISSを再実装する候補は除外 |
| 軌道選択・局所化・basis切替 | Kronenberger等は3つの軌道変換戦略、descriptorの弱い相関、basis切替の制約を扱う。[L08] | 「局所化なら誤差が大きい／小さい」という前提で新テーマを作らない。oracleなしの有用な選択則は今回確立していない |
| 状態依存partition選択 | Mehendale等は摂動的固有値誤差と近似状態によるpartition選択を既に扱う。[L20] | U3/H05を分解最適化へ改名して再提案しない。係数取得の追加研究はSTOP |
| 対称性保護・leakage抑制 | SPRINTはnear-integrability、randomization、symmetry protection、QROM等を統合。別にpost-processed symmetry restorationもある。[L09] [L16] | 対称性を入れるという一般案は既知。近似fragmentが物理sector外へ出る場合の追加誤差も既に認識されている |

この調査では、Cから、既知DF/BLISS/軌道/PF設計と区別でき、必要情報まで具体化できた候補は残らなかった。Cの研究可能性一般を否定したものではない。block-encoding/qubitizationへ全面移行する案も今回の中心対象にしていない。

## 5. D：エネルギー差など

同一Hamiltonianの低励起state間のTrotter誤差相殺と、nanographeneでのtensor-network spectral評価は2026年の一次研究にある。今回この論文はabstractと資料所在の範囲を確認した。[L13] 異なる核配置間のエネルギー差は、PRの旧R7にも既に候補として記載されている。[PRR5]

従って「絶対energyでなく差を取る」「似た構造で相殺を期待する」だけの候補は追加しない。反応・励起・力への展開を全て調べたわけではないが、件数を増やすために関連の弱いDを採らない。

## 6. 今回残さない方向と理由

| 調べた案 | 今回の除外理由 |
|---|---|
| QCELS＋既存PFの通常実装 | 近い回路・資源比較が既存。新しい推定誤差・情報契約の差分が不足 |
| 高次PFの単純なlogical error重み付き順位 | 既知のノイズ/次数・code distance評価の再会計に留まる |
| rotation別合成精度の最適化だけ | 小角・準確率・配分まで近い2026年研究が存在 |
| Richardson/ChebyshevによるTrotter誤差除去一般 | 既知アルゴリズムと保証があり、その再提示は差分でない |
| 軌道局所化・BLISS・DFを単に組み合わせる | 近い前処理・統合設計がある。未知入力での改善手順を特定できていない |
| 高次係数の安価取得、AR適用条件、direct最適時刻サイズ則 | U1/U3/U4の終了課題に実質的に戻るため除外 |
| PRの確率/proposal/normalizationやrandom-tail負担の最適化 | Track A/BとR5の対象。独立候補へ改名しない |
| 化学的energy差の相殺を観測するだけ | 近い一次研究と旧R7があり、予測・設計上の差分が不足 |

## 7. 既存研究との境界

| 既存系列 | 固定資料による照合と保全 |
|---|---|
| U1-AR / U3 / U4 | C1 / E4 / C4完結と追加研究STOPを維持。今回の静的調査承認は解除ではない。[U1] [U3] [U4] [CLOSURE] |
| 第一研究formal | final synthesisとclaim ledgerのscope、S0〜S4完了、S4否定結果を維持。旧cost proxyの順位を見直す研究にしない。[SYNTH] [CLAIMS] |
| FS-R1 Phase B | 既存follow-up、科学実行未承認、truth barrier不変。新しいテーマの試験入力へ流用しない。[FSR1] |
| 第二研究Direction C / U7 | spectral推定のpoint/width/採用・資源価値という既存成果を再命名しない。T1は新たなtrap実測入力とlogical noiseの条件を伴う別の推定問題でなければ独立候補にしない。[DIRC] |
| PR Track A | 指定DF Hamiltonianの有限時間complex signal精度と測定込みcompiled資源がscope。最終energy certificateは別問題と明記されている。T1ではPR方式間のsignal費用比較を再開しない。[PRA] |
| PR Track B | 部分乱択・coherent平均signal・減衰/位相保証、sampling/合成の研究scopeを確認。T1初期案ではdeterministic PFだけを扱い、RTEや共有乱数方式を変更しない。最新の実行状態の再判定はしていない。[PRB] |
| R5 | 指定PR repositoryの旧設計§9で、random-tail負担を含むenergy用PF係数設計を確認。PAUSEは今回のユーザー指示をauthorityとして維持。現在の独立したPAUSE原本は本調査では特定できず、旧計画を最新statusへ代用しない。[PRR5] |

PR資料は公開済みsnapshotのscope照合だけに使い、コピー・再解析・変更・再開していない。private dataや未公開の研究成果を今回新規公開しない。

## 8. 未確認事項と作業終了

T1には、論理認証の著者実装の所在、有限標本のenergy推定への接続、prior/overlapの取得、認証費込みの優位性が残る。これらは、文献未確認・未検証の事項であり、不可能性や未解決性の証明ではない。25 PDFの取得を網羅的新規性調査の完了と呼ばない。

成果物は本書、[比較表][MATRIX]、[候補handoff][HANDOFF]、[provenance.json](provenance.json)の4点のみ。新規科学計算・保存値再解析・再fit・新証明・反例構成・科学実装・benchmark・既存STOP解除は0件。引用・source text・Git/byte/hashのみを確認し、公開照合後Mandatory STOPとする。

<!-- fixed-source-references -->

[C12]: https://github.com/iloaiza/QuantumMAMBO.jl/blob/f8fbc4dccb89e3f8bed97b544fc87a06600fd81a/README.md
[C13]: https://github.com/iloaiza/QuantumMAMBO.jl/blob/f8fbc4dccb89e3f8bed97b544fc87a06600fd81a/src/UTILS/bliss.jl
[CLAIMS]: https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/adb17c423fee304a87e5d49027f0c8f966dc799c/PF_first_study_paper_claim_ledger_20260926.md
[CLOSURE]: https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/adb17c423fee304a87e5d49027f0c8f966dc799c/docs/research_audits/pf_u4_candidate_exploration_closure_20261016/audited_candidate_scope_closure.md
[DIRC]: https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/adb17c423fee304a87e5d49027f0c8f966dc799c/docs/second_study_v2/result_synthesis_20261005/approved_scope_and_rq.md
[FSR1]: https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/adb17c423fee304a87e5d49027f0c8f966dc799c/artifacts/pf_first_study_fs_r1_b0_phase_b_barrier_20261008/README.md
[HANDOFF]: candidate_handoff.md
[L01]: https://arxiv.org/abs/2211.11973v2
[L02]: https://arxiv.org/abs/2303.05714v4
[L03]: https://arxiv.org/abs/2307.11257v2
[L04]: https://arxiv.org/abs/2403.00077v1
[L05]: https://arxiv.org/abs/2408.14385v2
[L06]: https://arxiv.org/abs/2410.05369v2
[L07]: https://arxiv.org/abs/2603.22778v2
[L08]: https://arxiv.org/abs/2602.18913v1
[L09]: https://arxiv.org/abs/2606.30741v1
[L10]: https://arxiv.org/abs/2304.13772v3
[L11]: https://arxiv.org/abs/2409.18277v2
[L12]: https://arxiv.org/abs/2605.31544v2
[L13]: https://arxiv.org/abs/2605.00745v2
[L14]: https://arxiv.org/abs/2212.14144v4
[L16]: https://arxiv.org/abs/2606.20242v1
[L17]: https://arxiv.org/abs/2508.05523v3
[L18]: https://arxiv.org/abs/2408.14929v2
[L20]: https://arxiv.org/abs/2312.13282v3
[L21]: https://arxiv.org/abs/1808.02625v2
[L22]: https://arxiv.org/abs/2605.05315v1
[L23]: https://arxiv.org/abs/2010.02538v1
[L24]: https://arxiv.org/abs/2302.02454v4
[L25]: https://arxiv.org/abs/2405.01131v3
[MATRIX]: candidate_evidence_matrix.md
[PRA]: https://github.com/HIROMU1015/Partially-Randomized-Trotter/blob/93bf0bf3420683d9d20755cea856d3814b951233/docs/research/track_a_shared_research_status.md
[PRB]: https://github.com/HIROMU1015/Partially-Randomized-Trotter/blob/cc2f451324b7292ae50cef94ff794d46f225d892/docs/tracks/algorithm_codesign/m1s_g0t1_s0_formal_theory_contract_20261016.md
[PRR5]: https://github.com/HIROMU1015/Partially-Randomized-Trotter/blob/cc2f451324b7292ae50cef94ff794d46f225d892/partial_randomized_trotter_research_redesign_20260925.md
[SYNTH]: https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/adb17c423fee304a87e5d49027f0c8f966dc799c/PF_first_study_final_synthesis_20260925.md
[U1]: https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/adb17c423fee304a87e5d49027f0c8f966dc799c/docs/research_audits/pf_u1_ar_c1_closure_20261016/decision_record.md
[U3]: https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/adb17c423fee304a87e5d49027f0c8f966dc799c/docs/research_audits/pf_u3_h05_e4_closure_20261016/decision_record.md
[U4]: https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/adb17c423fee304a87e5d49027f0c8f966dc799c/docs/research_audits/pf_u4_candidate_exploration_closure_20261016/decision_record.md
