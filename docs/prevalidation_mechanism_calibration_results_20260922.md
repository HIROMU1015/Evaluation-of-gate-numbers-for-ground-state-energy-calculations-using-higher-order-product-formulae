# 機構診断・校正費用事前検証の結果台帳（2026-09-22）

## 位置付け

この文書は、`PF_research_prevalidation_catalog_2026-09-20.md` のうち、
有限時間での低次モデル破綻機構と古典校正費用に関係するローカル検証を、
GitHubで参照可能な形へまとめた結果台帳である。

- 基点commit：`2ba6174b6f9617d51766579c775a77132f3c7f57`
- 結果ブランチ：`prevalidation-mechanism-calibration-results-20260922`
- 対象：F01、F02、F05、H01小系pilot、H03、H04、H05、D04
- 非対象：新PF係数探索、新分子追加、別基底、別目標精度、全電子HF伸長の追加機構計算

保存済みmanifestに生成環境の絶対パスが1件ずつ含まれていたため、公開時に
`source_sha256`のキーだけをリポジトリ相対パスへ正規化した。hash値、audit、CSV、
NPZ、図、科学的結論は変更していない。

H01 pilotが参照する既存PF射影については、commit禁止のローカル探索実装を含めず、
同じ4次モーメント方程式だけを`fourth_order_projection.py`へ分離した。m=2/m=3の
保存候補係数が要素単位で一致することを確認し、生成時source hashと公開時source
hashの両方をH01 manifestへ記録した。

## 完了状態

| 項目 | status | 対象・役割 | 主な結論 |
|---|---|---|---|
| F01 | `complete` | H2/H4、4種類の4次PF | D4の対角期待値、全演算子ノルム、励起空間結合は同一指標ではない |
| F02 | `complete_with_findings` | F01のD4/D8を使うa8分解 | 最適化PFではD8対角項とD4状態混合が強く相殺する |
| F05 | `complete` | X02枝曲線とF02機構量の結合 | 最小物理ギャップだけでは混合も有限時間位相近接も説明できない |
| H01 pilot | `pilot_complete_with_findings` | H2/H4 exact/HF/CISD | CISDは小系で選択を再現、HFは再現しない。分子間保証ではない |
| H03 | `complete_with_scaling_blocker` | 行列フリーD4 state action | 数値的には正しいが、素朴な記号BCH生成が13群で律速する |
| H04 | `complete_with_findings` | compact/grouped BCH | 168560 raw項を456 grouped項へ圧縮。norm-only枝刈りは安全でない |
| H05 | `complete_with_findings` | a6/a8取得法比較 | exact responseは8/8、CISD responseは7/8。安価なD8構築は未解決 |
| D04 | `complete_with_findings` | 同一点数・同一古典時間監査 | exact-a4＋2点は8/8だが、a4取得込みでは一様な時間・メモリ削減ではない |

## 研究判断

1. 低次係数が小さいことを、誤差演算子そのものが小さいことと解釈してはいけない。
   最適化PFでは対角期待値の相殺と励起空間結合が重要である。
2. a8はD8の対角期待値だけではなく、D4による二次状態混合を含める必要がある。
3. 有限時間の危険域は物理ギャップだけから決められない。PF依存の位相圧縮、
   対象枝重なり、結合行列要素を併記する必要がある。
4. H03の記号展開ボトルネックはH04のfull grouped表現で解消できる。ただし、
   norm-only top-k近似は最大14.90%の直接PF選択損失を生じたため採用しない。
5. 直接点数の削減とend-to-end古典費用削減は別である。D04ではexact-a4＋2点法が
   free 5点法より速かったのは1/8、推定peak memory以下だったのは0/8だった。

## 適用範囲と未完了事項

- F01/F02はH2/H4小系での機構検証であり、N2/COや全電子HF伸長の破綻原因を
  直接確定していない。
- H01 pilotは後続H03/H04/H05のH2/H4状態入力であり、GPUサーバー上のN2/CO H01
  結果とは別物である。
- H05の`direct_fixed_a4_2_tail`はdirect PF固有値2点を必要とし、oracle-freeな
  practical calibrationには該当しない。
- 次は成功条件1〜2件と破綻条件1〜2件だけを用いたF01/F02/F05 bridgeを行い、
  その後にCISD＋full grouped D4作用＋固定安全余裕の1方式を凍結して採点する。

## 検証方法

今回追加した関連テストは次のimport pathで実行し、37件すべて合格した。

```bash
PYTHONPATH=.:src:review_response pytest -q \
  review_tests/test_bch_matrix_series.py \
  review_tests/test_f01_effective_hamiltonian_pilot.py \
  review_tests/test_f01_effective_hamiltonian_multipf.py \
  review_tests/test_f02_tau8_state_mixing.py \
  review_tests/test_f05_energy_phase_gap.py \
  review_tests/test_h01_approximate_state_pilot.py \
  review_tests/test_h03_matrix_free_d4_action.py \
  review_tests/test_h04_compact_bch_importance.py \
  review_tests/test_h05_higher_order_acquisition.py \
  review_tests/test_d04_equal_classical_budget.py
```

PennyLaneを使う独立BCH cross-checkも`requirements-bch.txt`の分離環境で2件合格した。
8個のmanifestに記録されたartifact/source/input SHA-256は128件すべて再照合した。

全`review_tests`の収集は、基点`2ba6174`に既に存在するB08監査がGit未収録の
`refine_joint_full_frozen_m3_local.py`と展開済み
`refinement_results.json`を要求するため停止する。この旧探索依存一式は今回の
F/H/D結果に無関係であり、約17 MBの親探索JSON等を結果ブランチへ混在させない。
したがって上記39件とmanifest hash照合を本ブランチの検証範囲とする。
