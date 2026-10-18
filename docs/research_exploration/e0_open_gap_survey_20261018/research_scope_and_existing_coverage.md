# 絶対E0の次課題：限定調査の範囲

2026-10-18 JST。Phase Bは課題の整理だけであり、新アルゴリズム候補の構成・科学的採択・詳細科学レビューではない。判断候補は1件、[低深さGSEEの認証費用](candidate_problem_cards.md)。その改善可能性とD1内での実現可能性は未確立である。

## Phase Aとの分離

占有条件付き測定の固定構成はPhase Aで正式CLOSED／独立候補NOT RETAINEDとなった。[判断記録](https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/fe29fcc73290d35af8c68281330c84b9258e3296/docs/research_exploration/conditional_measurement_closure_20261018/research_closure_decision.md)と[公開receipt](https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/fe29fcc73290d35af8c68281330c84b9258e3296/docs/research_exploration/conditional_measurement_closure_20261018/publication_receipt.json)を固定参照する。Phase A最終11資料のremote SHA・独立fetch・blob・bytes・SHA-256・固定raw、および開始時305 checkoutの保全を確認してから、本branchを作成した。

本branch `qc-e0-open-gap-survey-20261018` は `fe29fcc73290d35af8c68281330c84b9258e3296` を親の起点とする。Phase Bの正式状態変更は0件。Phase Aの判断原本や旧成果物を再生成しない。

## 固定する計算問題

入力は、指定有限基底・指定電子sector上の元Hamiltonian

\[
H=cI+\sum_{pq}h_{pq}a_p^\dagger a_q
  +\frac12\sum_{pqrs}v_{pqrs}a_p^\dagger a_q^\dagger a_s a_r
\]

と、その係数規約・sector・合法な準備accessである。目標はこのHの絶対E0であり、任意のtrialの期待値や可視低energy成分の位置へ変更しない。積分近似・DF切捨て・active-space化をした別モデルのE0を元Hと同一視しない。

既知の係数boundから得るshift aとscale b>0を使う場合は、`Hbar=(H-aI)/b`、`E0=a+b Ebar0`、`epsilon_bar=epsilon_Ha/b`を明示する。scalarを復元し、モデル誤差・simulation誤差・統計誤差を別々に会計する。以降の漸近式は無次元化したエネルギーであり、Haやnative gateへ直接読み替えない。

D1を維持する。block-encoding／QSVT／qubitization中心の新方向は採択しない。文献にその操作が含まれる場合も、強い対照から隠さず記載する。対象accessとの不一致を、アルゴリズムの改善や実用性の証拠にはしない。

未知のground state・gap・固有projector・完全振幅表は入力にしない。ground重み下界etaを仮定する結果は、条件付き命題として扱い、etaの合法な根拠と取得費を別fieldで必要とする。本調査はその根拠を新しく作っていない。

## 既存の分担

[横断マップ609a632](https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/609a63231ee0786cf8da31f6b33358acfd6f2548/docs/research_exploration/cross_repository_overlap_survey_20261017/algorithm_improvement_overlap_matrix.md)、[差分整理c641985](https://github.com/HIROMU1015/Evaluation-of-gate-numbers-for-ground-state-energy-calculations-using-higher-order-product-formulae/blob/c6419859029824a4ee8c3dfd3c8126fe585ffbe2/docs/research_exploration/cross_repository_two_branch_delta_20261017/review_readiness_delta_handoff.md)、[PR20方向](https://github.com/HIROMU1015/Partially-Randomized-Trotter/blob/d09ba606a9fceef806a9313e3f7c43cd21d19e3f/docs/research/qc_four_track_strategy_handoff_20261017/overlap_and_progress_map.md)を再利用した。SOURCEの正確なpath・取得範囲は[source_registry.json](source_registry.json)を正とする。過去の全探索履歴は作り直さない。

PRM11のcopies測定、PRM15の全round絶対E0、PRM04/16の保証に接する。今回の問いは推定結果を受理する統計的条件であり、PFの有限step作用素誤差boundの改良ではない。対応は[重複照合](overlap_and_reduction_screening.md)に限定して記録した。

J1/Q1 PAUSE、R1-P独立候補不保持、集団遷移生成PAUSED、G CLOSED、A2 NOT_ADOPTEDと現実用経路の追加投資なしを維持する。第一・第二研究、PR Track A/B、他系列の正式状態も変更しない。

## 実施したことと境界

一次論文の版・入力・操作・保証・費用・後続を限定照合した。2025年に明示された課題と2026年の関連結果を区別した。新生成規則・回路・新証明・科学数値計算・保存値再解析・solver・symbolic checker・compile・grantは0件である。

公開するのは本調査の記述・参照・hashのみ。非公開指示/GPTレビュー原本は移動・複製・再公開せず、以前拒否された公開を再試行しない。未取得の過去原本、未読の引用先や未確認実装を取得済みとしない。公開論文PDFも原文は本packetへ再配布しない。

管理作業のGit/read/hashだけを実行した。CPU・RAMを観測し、共有設定・他job・固定資源契約を変更していない。静的監査は科学的正しさやpriorityの認証を意味しない。
