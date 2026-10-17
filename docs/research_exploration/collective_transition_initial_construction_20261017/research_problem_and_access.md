# 非可換電子Hの集団遷移生成：課題とaccess

2026-10-18 JST（作業系列ID：20261017）。ユーザー添付「非可換電子Hamiltonianに対する集団遷移生成アルゴリズムの初期構成研究」の実施記録。新系列の限定紙上構成であり、新アルゴリズムの正式採択ではない。

## 1. 研究対象

有限基底のnumber-conserving電子Hamiltonian

\[
H=cI+\sum_{pq}h_{pq}a_p^\dagger a_q+
\tfrac12\sum_{pqrs}V_{pqrs}a_p^\dagger a_q^\dagger a_sa_r
\]

の係数から、coupler・ancilla unitary・resetを含むCPTP写像を決める。二体係数の反対称化や1/2の規約は入力ごとに固定する。本書の診断familyは、曖昧なVの再添字化を使わず、明示した密度項とHermitian hoppingを正本とする。

主な判別対象は、単に「冷却」「多電子jump」を使うことではなく、係数→有限操作列の規則、非可換項を保持したenergy変化、必要情報と既知法への対応である。一般分子の多項式収束・新規性・総資源優位を前提にしない。

## 2. 今回の限定classと入力

CAR `{a_p,a_q†}=δ_pq`、占有ketは昇順のcreation積とする。最小診断は4 modes、N=2の6次元sectorで

\[
H_D=cI-U(n_1n_2+n_3n_4)-\mu(n_3+n_4),\quad U>\mu>0.
\]

非可換な構成対象は

\[
H_*=H_D+t(a_3^\dagger a_1+a_1^\dagger a_3),\qquad t>0.
\tag{H*}
\]

tの位相がある単一edgeは、係数から決まる軌道位相変換で正の実数にできる。その変換とTの位相も追跡し、独立な複数edgeの全位相を同時に消せるとはしない。この模型は相互作用と非可換hoppingを持つが、一般Coulomb分子ではなく解析的な小ブロック模型である。

さらに、density境界条件で制御された単一hopping edge、および新たなhopping境界を持つ拡張を区別する。前者の条件付き2次元回転は既知の解析的手順。後者への一般化は得られていない。

許可入力はc,U,μ,tや一般の一体/二体係数、明示したsector・構造、精度、通常gateとancilla/resetである。初期状態例は占有product state |12〉。未知のE0、ground vector、gap、全遷移表、spectral projector、全H時間発展oracleは入力しない。

## 3. 操作・費用のモデル

1. 係数の読取り、差・平方根・atan2等の古典処理、有限精度の誤差管理を費用に含める。
2. number-preserving fermionic rotation、制御double excitation、占有bitの可逆制御、ancilla初期化/resetを通常gateへ接続する。式で指定したunitaryを無料oracleと扱わない。
3. Jordan–Wigner等のencodingとparity処理を固定する必要がある。4-modeの定数サイズ指定を一般Mで定数費用と呼ばない。
4. 理想角度の紙上恒等式と、有限bit/合成/reset誤差つき実装を分離する。回路build・compileは今回行わない。
5. 論理gateを実施するモデルであり、常時作用する物理Hを無費用で停止できると仮定したautonomous bathモデルではない。装置のdrift補償やgate誤差は後の実装契約事項。

選んだスピンラベルを1,3=↑、2,4=↓とすれば、例のhopping・pair移送はN↑/N↓も保存する。一般のS²保存は主張しない。便宜的spin/seniority制限を元電子問題のground sectorと同一視しない。

## 4. 既存研究との境界

[旧横断handoff][E01]・[重複表][E02]・[状態表][E03]、PR[既存整理][P01]・[20方向][P02]・[索引][P03]を再利用した。全面再調査はしない。[最新差分handoff][E04]のA2/H8取得状況を維持する。PR相対形式監査の正しい固定commitは **051df4661eeffb6c6c4c978f70f43eeeaadfddd6**。添付に併記された短い誤記はSOURCEとして用いない。[P04]

今回の目的は実stateの人口移送であり、PF係数/分割の最適化、A2の相対log保証、M1-Sの±信号、Q1の全固有基底挿入則を再開しない。ただし、人口移送という違いだけで新規性は認定しない。既知冷却との対応は[比較文書](prior_art_and_mechanism_comparison.md)で先に固定する。

D1：block-encoding/qubitization/QSVT中心へ移行しない。比較文献にそれらが含まれることと採用は別。D2：最終目標は元の有限基底電子Hの絶対E0であり、scalar・一体項・相互作用・残余/モデル差・state取得費を保持する。今回はE0を出力する完成算法ではない。

## 5. 成果の区分と禁止範囲

紙上で新たに導いた式は本系列の設計診断と明記し、独立したpriorityや詳細科学レビュー認証としない。本文でのA–E分類は技術整理に限る。既存J1/Q1/R1-P/A1/A2の正式状態は変えない。

実施したのは静的Git/文献確認、限定数学導出、文書/JSON/hash監査。新規数値計算、科学用記号プログラム、Hamiltonian数値行列生成、solver、simulation、回路build/compile、benchmark、科学grant発行は行わない。公開・照合後Mandatory STOPする。

[E01]: https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/609a63231ee0786cf8da31f6b33358acfd6f2548/docs/research_exploration/cross_repository_overlap_survey_20261017/future_review_preparation_handoff.md
[E02]: https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/609a63231ee0786cf8da31f6b33358acfd6f2548/docs/research_exploration/cross_repository_overlap_survey_20261017/algorithm_improvement_overlap_matrix.md
[E03]: https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/609a63231ee0786cf8da31f6b33358acfd6f2548/docs/research_exploration/cross_repository_overlap_survey_20261017/active_and_pending_research_map.md
[E04]: https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/c6419859029824a4ee8c3dfd3c8126fe585ffbe2/docs/research_exploration/cross_repository_two_branch_delta_20261017/review_readiness_delta_handoff.md
[P01]: https://github.com/HIROMU1015/Partially-Randomized-Trotter/blob/d09ba606a9fceef806a9313e3f7c43cd21d19e3f/docs/research/qc_four_track_strategy_handoff_20261017/strategy_handoff.md
[P02]: https://github.com/HIROMU1015/Partially-Randomized-Trotter/blob/d09ba606a9fceef806a9313e3f7c43cd21d19e3f/docs/research/qc_four_track_strategy_handoff_20261017/overlap_and_progress_map.md
[P03]: https://github.com/HIROMU1015/Partially-Randomized-Trotter/blob/d09ba606a9fceef806a9313e3f7c43cd21d19e3f/docs/research/qc_four_track_strategy_handoff_20261017/fixed_evidence_index.json
[P04]: https://github.com/HIROMU1015/Partially-Randomized-Trotter/blob/051df4661eeffb6c6c4c978f70f43eeeaadfddd6/docs/research/qc_relative_form_finite_step_audit_20261017/decision_handoff.md
