基準コミットは `20d64c2fea1ed2d2188777df4f3d962ee94df486`。作業ブランチは `poster-finite-time-20261116`、worktree は `/home/AbeHiromu/projects/poster-finite-time`。主対象は H₂・H₄・H₆、H₅は参考、H₈は見積もり後の確認待ち。H₃の診断は優先順位変更前の記録として保管し、主表には含めない。H₇の新規計算はない。

係数は基準コミットの `artifacts/trotter_expo_coeff_gr_original/*_ave` をそのまま使用した。次数は8/10/4に固定し、回転数は `config.DECOMPO_NUM`、ε=1.59360010199040e-4 Ha、β=1.2。比は丸め前のコストから算出した。新しいαのフィット、係数の再探索、既存設定の変更はない。

直接計算の方式は後続の `4672f3f` に合わせた。全保存則セクターの密なPFユニタリを複素倍精度で構築し、回文列の同一S2段を再利用する。GPUはユニタリ構築、CPU SciPy Schur分解は固有位相と完全なベクトルを求める。最初は最大基底状態重なり、以後は直前のベクトルとの最大重なりで連続追跡する。最大基底状態重なり枝も別途計算して照合した。元コードのスナップショットは `references/4672f3f/`、全履歴調査は `references/history_artifact_label_audit.json`。

各点には固有対残差、ユニタリ残差、Schur非対角成分、符号付きエネルギーシフト、基底状態重なり、隣接点との追跡重なり、枝間のシフト差、位相巻き数を保存した。重なり位相は補助診断であり、直接誤差として使用していない。H₄・H₅・H₆の8次では探索範囲の上側で連続枝が最大基底重なり枝から離れる。全範囲の照合不合格を消さず記録し、最小点近傍の照合・重なりを別途示した。後続研究の固定31点全域の合否を、そのまま今回の可変探索域に移したとは主張しない。

探索は0.3–2 t_anaの41点対数格子、厳密なt_ana点、0.03–0.3 t_anaの短時間診断点から開始した。最小点の左右を25点ずつ細分化し、最小コストの変化1e-4未満、時刻変化1e-3未満、最小点の隣接区間幅/時刻1e-3未満を要求した。隣接追跡重なりが低い区間も追加した。H₅・H₆の8次は細分化で追跡枝と見かけの最小値が変わったため、追加計算して収束を確認した。未収束の初回記録は `attempts/` に残し、主表に使用しない。結果は探索した有限領域の離散格子最小であり、連続時間の大域最小を証明しない。

`t_valid` は短時間側からの最初の連続10%適合域の最終合格点。先頭の数値床以下は未判定とし、現在の研究状況の5e-13 Haを採用した。一度不適合になった後の再適合は採用しない。境界は最後の合格点と次の不合格点で挟んで記録した。H₄・H₆の10次では最初の解像された点が10%を外れ、t_validを確定できない。これを0や後続の適合区間で置き換えていない。同じt_anaでのコスト比 p/(p+1-r) はJSONの `at_analytic_time.same_time_direct_to_model_cost_ratio` に保存した。

再現確認は新規探索の前に実施した。基準コミットの `validate_hchain_perturbative_estimator.py` でH₄/Y8m10bの先頭14点を再計算し、最大絶対差2.220446049250313e-15 Haで一致。H₈の解析比（1回の回転数/使用回数/総回転数）は、10次=1.9400750352803497/0.798435319755208/1.5490244311431625、新4次=0.29494372353973775/2.935986181032801/0.8659506964950289で再現した。`reproducibility.json` に元値と診断を保存した。

全履歴の3512個のJSON/Markdown/CSV成果物（約158 MB）を読み、対象3公式をこの水素鎖で直接再最適化した結果が後続ブランチに存在しないことを確認した。既存の短時間比較と他分子の新4次比較は区別した。既存解析の生成スクリプトは `analyze_wide_time_cost.py`、点計算は `run_morales_y8m10b_hchain.py`、直接曲線は `validate_hchain_perturbative_estimator.py`。`*_wide_refined.json` の `merged_sources` は回収できたが、履歴内の325個のPythonソースにも独立した統合スクリプトや当時の正確な統合コマンドは見つからなかった。この来歴上の欠落は `references/script_provenance.json` に明記した。

図Aは新規H₄の3公式。図Bは既存データだけでH₂/H₄/H₆のY8m10bを表示し、H₂/H₄は20d64c2のwide解析、H₆は4672f3fの既存CPU31点曲線を用いた。図Bの星は各保存格子上の最小で、H₆の追加refined計算を行ったという意味ではない。出典は `figure_B_sources.json`。当初依頼のH₂/H₄/H₅版も `figure_B_H2_H4_H5_reference.*` として保管した。

実行環境は `/home/AbeHiromu/venvs/trotter-common/bin/python`、NumPy 1.26.4、SciPy 1.14.1、CuPy 13.6.0、NVIDIA A100-SXM4-40GB。CuPyは共通環境を変更せず `/tmp/poster-finite-time-deps` に配置した。`TROTTER_QISKIT_DEVICE=GPU`、精度double、BLAS/OMP/MKL各1スレッド。通常は物理GPU7、H₆追加細分化では5/6/7。Qiskit Aerの設定だけで直接行列計算をGPU化したとは主張せず、GPU builderを明示している。各生データの環境設定も参照。

逐次・3GPUスレッド経路の数値一致はH₄の3公式で検証したが、小行列では並列化が遅かった。Pythonの起動処理の競合を避ける `spawn` プロセス経路も追加し、H₆の同じ時刻で数値一致と性能を別途検証した。3GPU別プロセスの実測高速化率は8次1.2843倍、10次2.8643倍、新4次2.8466倍（ワーカー起動と3点の初期化約4.08秒は別）。H₆追加細分化の本データはスレッド方式によるもので、プロセス検証と区別して環境に保存した。各ワーカーは完全な群スペクトルとCUDAコンテキストを持ち、時刻順の枝追跡は結果回収後に親で行う。H₈では全群スペクトルが40 GB GPUを超えるため、ホスト常駐・群ごとの転送方式への対応が必要であり、現runnerはH₈の実行を禁止している。H₈の数値計算は未実行。

再実行例（既存の完了セルはスキップする）：

```bash
PYTHONDONTWRITEBYTECODE=1 \
PYTHONPATH=/tmp/poster-finite-time-deps:src:review_response \
TROTTER_PROJECT_ROOT="$PWD" TROTTER_QISKIT_DEVICE=GPU \
TROTTER_QISKIT_AER_PRECISION=double CUDA_VISIBLE_DEVICES=5,6,7 \
OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 \
/home/AbeHiromu/venvs/trotter-common/bin/python \
  review_response/poster_finite_time.py --systems 2 4 6 5 \
  --logical-gpus 0 1 2 --parallel-backend process
```

現在の作業ツリー・既存worktreeは切り替えていない。基準コミットの追跡ファイルには変更がなく、新規スクリプトと新規結果のみ。この報告の生成時点では未コミットだった。公開時のコミットは作業ブランチの履歴を参照。
