# 保存するGの構成成果と既知手順への還元

2026-10-18 JST。承認済みCLOSED判断の根拠を固定資料から整理する。新たな数学的構成、文献調査、科学検算、重要科学レビューは行っていない。詳細式・導出を複製せず、固定commitへ参照する。

## 技術的成果として保持する内容

| 構成された内容 | 保持する意味と限界 | 固定根拠 |
| --- | --- | --- |
| Hamiltonian係数graphから有限predicate dictionaryを生成 | 支持・絶対係数の集計、ordered最大重みforestのcluster、occupation-count thresholdから候補を具体化した | [初期Gの§1.1][initial-G]、[P-c操作対応§1][pc-mapping] |
| coherent cell分割による変分部分空間更新 | 一つのseedのcell indicatorを二分する具体的なbasis更新。旧spanは子の和を通じて保持される。seedのzero supportは増やさない | [初期Gの§1.2・1.4][initial-G]、[P-c操作対応K1–K3][pc-mapping] |
| 共通測定記録による行列要素推定 | term・axis・符号・配置recordを各候補へ再labelし、Hermitian行列と別poolの人口Gramを得る | [初期GのG2–G4][initial-G]、[P-c情報比較I1–I4][pc-information] |
| 同時confidenceによるenergy gain判定 | 固定有限tree class全体のevent上でinterval差g_Lを評価する。population条件とRitz誤差幅の前提が残る | [初期数学M3–M4][initial-math]、[P-c操作対応K4][pc-mapping] |
| 古典追加費用を含む選択・STOP | 固定C_add proxyに対するg_L/C_add、固定tie、候補なし・上限・証拠不足での終了を具体化した | [初期Gの§1.4][initial-G]、[P-c操作対応K5・§4][pc-mapping] |

これらを有効な技術的構成記録として保持することと、独立した新アルゴリズム・資源優位を認定することは別である。C_addは全screening実費の最適性を保証せず、統計的Ritz誤差幅は元Hの絶対E0との差を埋めない。ここで科学的実行や機械による証明認証を追加していない。

## P-a～P-cの経過

| 判別 | 保存する結果 | 今回の扱い |
| --- | --- | --- |
| P-a | 共通測定記録と適応的confidenceは明示した前提下で紙上成立。ただしそれ自体は既知手法 | 成果と前提を保存。新しい保証とはしない |
| P-b | 測定再利用そのものの独立性は成立せず、VQNHE等と重複する | 独立したmeasurement再利用法というclaimに使わない |
| P-c | 初期構成では未確定だったが、限定照合でB：既知手順の具体的な特殊化・組合せへの還元 | ユーザー承認済みのCLOSED／NOT RETAINED判断の技術的根拠とする |

初期経過は[初期handoff§2–3][initial-handoff]、後続判定は[P-c判定][pc-assessment]に固定されている。初期文書の未確定記載を消さず、後続の結果・正式判断を新しい記録として結ぶ。

## P-c＝Bの内容と留保

既知法にも同じHamiltonian係数、seedと準備access、dictionary D、候補部分空間、測定情報・予算、精度・confidence、古典費用の範囲を認める。その条件では、piecewise complex Fによるdiagonal関数表現、QSEの線形係数solve、既知のgraph／count-threshold生成・confidence・interval比較・費用比greedyを接続すると、Gと同じ候補評価・g_L・C_add・固定tie・全更新列・STOPを再現できる。[操作対応§1–4][pc-mapping]

理想測定モデルでは、VQNHEの配置対測定recordを既知bit変換でGへ対応させられる。raw record lawには公平orientation coinを加える対応があり、Hermitian意思決定matrix族とC_addはorientation非依存なので、意思決定にはそのcoinも不要となる。同じshot数・seed準備回数で必要統計のjoint distribution、分散、相関まで対応する。独立に採った二つの有限shot実験が必ず同じ更新を返す、という主張ではない。[情報・費用比較§1–4][pc-information]

SSE原法のPauli pool、filter、Gram regularization、標準local shadowsはGと異なり、そのまま同じ選択結果・同shotの分散とはしない。VQNHEの無変更neural optimizerや全SSE変種・全実装がGと同一であるともしていない。対応は明記された強対照とwrapperについてのものである。[操作対応§5][pc-mapping]、[情報・費用比較§5–6][pc-information]

**具体的な独立生成機構、独立保証、資源優位は確認されていない。** ただしBは世界的priorityの網羅認証ではなく、すべての既知部品の組合せに新規性がないという一般命題でもない。未測定native費用や未確認priorityを、現Gを継続する自動ToDoへ変えない。正式な扱いは[判断記録](research_closure_decision.md)に従う。

[initial-G]: https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/7bbcc6c35a3d53bcdbbf720526c5cae0d885c7cd/docs/research_exploration/coherent_adaptive_subspace_initial_paper_20261018/adaptive_subspace_construction.md
[initial-math]: https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/7bbcc6c35a3d53bcdbbf720526c5cae0d885c7cd/docs/research_exploration/coherent_adaptive_subspace_initial_paper_20261018/mathematical_and_cost_analysis.md
[initial-handoff]: https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/7bbcc6c35a3d53bcdbbf720526c5cae0d885c7cd/docs/research_exploration/coherent_adaptive_subspace_initial_paper_20261018/research_decision_handoff.md
[pc-mapping]: https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/793cd63089dea8ca3e66b8c7faba173a198530eb/docs/research_exploration/coherent_subspace_pc_mapping_20261018/pc_known_method_mapping.md
[pc-information]: https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/793cd63089dea8ca3e66b8c7faba173a198530eb/docs/research_exploration/coherent_subspace_pc_mapping_20261018/pc_information_and_cost_comparison.md
[pc-assessment]: https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/793cd63089dea8ca3e66b8c7faba173a198530eb/docs/research_exploration/coherent_subspace_pc_mapping_20261018/pc_independence_assessment.md
