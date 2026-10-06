"""Reaggregate saved transfer outputs; no PF, H ground, or state calculations."""
import csv
import json
from pathlib import Path

from review_response import run_lab_progress_hchain_transfer_20261007 as base


def run():
    protocol = base.verify_protocol()
    predictions = [json.loads(path.read_text()) for path in sorted(base.OUT.glob("*/prediction_*.json"))]
    truths = [json.loads(path.read_text()) for path in sorted(base.OUT.glob("*/truth_*.json"))]
    expected = {(row["system"], row["formula"]) for row in predictions if row["eligible"]}
    assert {(row["system"], row["formula"]) for row in truths} == expected
    freeze = json.loads((base.OUT / "PREDICTIONS_FROZEN.json").read_text())
    assert len(freeze["prediction_sha256"]) == 16
    assert freeze["full_H_ground_solves_before_freeze"] == 0
    for name, expected_hash in freeze["prediction_sha256"].items():
        assert base.sha(base.OUT / name) == expected_hash
    direct_point_count = 0
    maximum_eigenpair_residual = 0.
    maximum_unitarity = 0.
    for truth in truths:
        path = base.OUT / truth["system"] / f"direct_grid_{truth['formula']}.csv"
        rows = list(csv.DictReader(path.open()))
        prediction = next(row for row in predictions if row["system"] == truth["system"] and row["formula"] == truth["formula"])
        assert len(rows) == 401
        assert [float(row["time"]) for row in rows] == prediction["grid"]
        maximum_eigenpair_residual = max(maximum_eigenpair_residual, max(float(row["eigenpair_residual"]) for row in rows))
        maximum_unitarity = max(maximum_unitarity, max(float(row["unitarity_frobenius"]) for row in rows))
        direct_point_count += len(rows)
    base.summarize(protocol, predictions, truths)
    summary = json.loads((base.OUT / "summary.json").read_text())
    classification = []
    for system in summary["systems"]:
        if system["status"] != "scored":
            status = "abstained_short_time_leading_fit_failed"
        elif not system["branch_reliable"]:
            status = "unconfirmed_continuation_branch_gate_failed"
        elif not system["precision_met"]:
            status = "valid_truth_precision_failed"
        else:
            status = "valid_truth_precision_met"
        classification.append({**system, "formal_precision_status": status,
                               "continuation_failure_not_counted_as_measured_precision_failure": not system.get("branch_reliable", True)})
    canonical_decomposition = []
    frozen_decomposition_difference = 0.
    for truth in truths:
        prediction = next(row for row in predictions if row["system"] == truth["system"] and row["formula"] == truth["formula"])
        for row in truth["decomposition"]:
            corrected = dict(row)
            if row["state"] == "cisd":
                fitted = base.evaluate_fit(prediction["model"], row["time"])
                frozen_decomposition_difference = max(frozen_decomposition_difference, abs(fitted - row["model_shift"]))
                corrected["model_shift"] = fitted
                corrected["fit_term"] = fitted - row["proxy"]
                corrected["closure"] = fitted - row["direct_shift"] - sum(corrected[key] for key in ("fit_term", "state_term", "proxy_term"))
                corrected["operational_model_source"] = "original_frozen_CISD_model"
            else:
                corrected["operational_model_source"] = "post_hoc_matched_state_control"
            corrected["dominant_absolute_term"] = max(("fit_term", "state_term", "proxy_term"), key=lambda key: abs(corrected[key]))
            assert abs(corrected["closure"]) < 1e-12
            canonical_decomposition.append(corrected)
    base.write_csv(base.OUT / "canonical_long_time_error_decomposition.csv", canonical_decomposition)
    correction = json.loads((base.OUT / "IMPLEMENTATION_CORRECTION_FROZEN.json").read_text())
    for name, expected_hash in correction["existing_truth_sha256"].items():
        assert base.sha(base.OUT / name) == expected_hash
    supplemental = json.loads((base.OUT / "supplementary_dominant_phase.json").read_text())
    state_quality = []
    for name in base.SYSTEMS:
        available = [row for row in truths if row["system"] == name]
        if available:
            first = available[0]
            state_quality.append({"system": name,
                                  "CISD_F": first["state_diagnostics"]["cisd"]["exact_overlap_probability"],
                                  "CISDT_F": first["state_diagnostics"]["cisdt"]["exact_overlap_probability"],
                                  "CISDT_subspace_dimension": first["projected_state_preparation"]["cisdt"]["subspace_dimension"],
                                  "sector_dimension": first["projected_state_preparation"]["cisdt"]["full_sector_dimension"]})
    matched_classifications = []
    for row in summary["matched_state_allocations"]:
        status = ("unconfirmed_continuation_branch_gate_failed" if not row["branch_reliable"]
                  else "valid_truth_precision_met" if row["precision_met"] else "valid_truth_precision_failed")
        matched_classifications.append({**row, "formal_precision_status": status,
                                        "confirmed_total_error": row["total_error"] if row["branch_reliable"] else None})
    base.write_csv(base.OUT / "matched_state_scoring.csv", matched_classifications)
    audit = {"schema": "lab_progress_hchain_transfer_audit_v1", "scientific_computation_count": 0,
             "protocol_sha256": base.sha(base.OUT / "protocol.json"),
             "prediction_freeze_sha256": base.sha(base.OUT / "PREDICTIONS_FROZEN.json"),
             "original_runner_sha256_matches_freeze": True, "original_predictions_unchanged": True,
             "existing_truth_before_correction_unchanged": True, "prediction_PF_count": len(predictions),
             "eligible_PF_count": len(expected), "direct_candidate_count": direct_point_count,
             "each_eligible_PF_has_original_401_times": True,
             "maximum_eigenpair_residual": maximum_eigenpair_residual,
             "maximum_unitarity_frobenius": maximum_unitarity,
             "CISD_decomposition_uses_only_frozen_model": True,
             "maximum_frozen_model_vs_block_refit_decomposition_shift_difference": frozen_decomposition_difference,
             "formal_classifications": classification, "state_quality": state_quality,
             "matched_state_formal_classifications": matched_classifications,
             "matched_state_control_PF_set": "PFs passing original CISD leading+training gates; same CISD times for every state",
             "matched_state_signal_gates_rerun": False, "only_CISD_model_choices_frozen_before_full_H_truth": True,
             "state_models_built_by_fixed_protocol_before_each_PF_direct_grid": True,
             "state_models_are_post_hoc_controls_not_an_operationally_validated_new_selector": True,
             "supplementary_phase_does_not_change_formal_classification": True,
             "matrix_vector_publication_count": 0}
    base.write_json(base.OUT / "audit.json", audit)
    report = ["# 別のH-chainでの誤差予測・PF/時刻/予算選択の追加検証", "",
              "2026-10-07。既存のHamiltonian・分割・CISDを再利用し、H4の四PF・5fit時刻・401候補という手順をH2/H3/H5/H6へ広げた。H6は中性singletの400次元sectorであり、旧holdoutの200次元sectorとは異なる。H3/H5は+1価tripletなので、鎖長だけの比較ではない。", "",
              "## 1. 元のCISDによる選択は、精度を満たしたか", "",
              "直接評価で枝追跡の基準が成立した場合にだけ、精度の成功・失敗を判定する。枝の基準に不合格だった点の数式上の誤差値を、確立した基底エネルギー誤差とは扱わない。", "",
              "| 系 | 選んだPF | 時刻 | 精度の正式分類 | 予算/候補最小費用 |", "|---|---|---:|---|---:|"]
    for row in classification:
        labels = {"abstained_short_time_leading_fit_failed": "短時間の四次係数が決まらず棄権",
                  "unconfirmed_continuation_branch_gate_failed": "枝追跡の基準不成立で未確認",
                  "valid_truth_precision_failed": "有効な真値で目標未達",
                  "valid_truth_precision_met": "有効な真値で目標内"}
        ratio = f"{row['budget_over_grid_minimum']:.3f}" if row.get("budget_over_grid_minimum") is not None else "—"
        time_label = f"{row['selected_time']:.6f}" if row.get("selected_time") else "—"
        report.append(f"| {row['system']} | {row.get('selected_formula', '—')} | {time_label} | {labels[row['formal_precision_status']]} | {ratio} |")
    report += ["", "H2/H5/H6で選ばれたm5の長い時刻は、継続追跡したPF枝の基準に不合格だった。これを受けて他PFへ選び直すことや、モデル・範囲を変更して救済することはしていない。費用比の分母は、事前に保存した401候補のうち枝追跡が成立しPF誤差が目標未満だった点の最小費用であり、連続時刻の最適値ではない。この比が1未満でも、元の予算で精度を満たす根拠は得られていないので、資源削減の成果とは解釈しない。", "",
               "## 2. 近似状態を改善した対照", "",
               "各PFで、元のCISDから決めた5つの絶対fit時刻と401候補時刻を共通にし、平均場の一行列式・CISD・CISDT・厳密状態を比べた。CISDTは同じHamiltonianを励起rank≤3の部分空間で解いた状態で、rank≤2から保存CISDを再現できることも確認した。", "",
               "| 系 | CISDと厳密状態の重なり² | CISDTと厳密状態の重なり² | CISDT次元/全sector次元 |", "|---|---:|---:|---:|"]
    for row in state_quality:
        report.append(f"| {row['system']} | {row['CISD_F']:.9f} | {row['CISDT_F']:.9f} | {row['CISDT_subspace_dimension']}/{row['sector_dimension']} |")
    report += ["", "| 系 | モデルへ使った状態 | 選んだPF | 時刻 | 継続枝の基準 | 目標精度 |", "|---|---|---|---:|---|---|"]
    for row in summary["matched_state_allocations"]:
        precision = "未確認" if not row["branch_reliable"] else "満たす" if row["precision_met"] else "満たさない"
        state_label = {"rhf": "ROHF" if row["system"] == "H5" else "RHF", "cisd": "CISD",
                       "cisdt": "CISDT", "exact": "厳密状態"}[row["state"]]
        report.append(f"| {row['system']} | {state_label} | {row['formula']} | {row['time']:.6f} | {'成立' if row['branch_reliable'] else '不成立'} | {precision} |")
    report += ["", "H2ではCISDが全sectorの厳密状態と一致する。H5ではCISDTが全50次元sectorを含み、厳密状態と一致する。それでもm5の選択は長い時刻となり、継続枝の基準は成立しなかった。入力状態を正確にするだけでは解消しない、有限時間のモデル・代理量・枝対応の問題がある。H6でCISDTへ広げた改善は小さく、系とPFを揃えてその影響を判断する必要がある。", "",
               "この状態対照は、CISDで適格だったPF集合を固定したpost-hoc対照である。各状態のtraining signalゲートは再判定していない。CISDの運用予測だけは全Hamiltonianの厳密解より前にfreezeしたが、他状態のモデルは固定仕様に従う診断用の対照であり、運用上の新しい選択法を事前検証した結果ではない。", "",
               "## 3. 長い時刻の三成分", "",
               "同じPF・時刻で、予測との差をモデル当てはめ、入力状態、代理量とPF固有値の差へ分けた。以下は枝追跡が成立した、各系のm5候補内の直接最小費用点である。値は正負を保ったHa。", "",
               "| 系 | 時刻 | モデルの差 f−g | 状態の差 g−g0 | 代理量の差 g0−δ | 最大成分 |", "|---|---:|---:|---:|---:|---|"]
    for row in canonical_decomposition:
        if row["formula"] == "m5_best" and row["state"] == "cisd" and "direct_grid_min" in row["point_role"] and row["branch_reliable"]:
            report.append(f"| {row['system']} | {row['time']:.6f} | {row['fit_term']:.6e} | {row['state_term']:.6e} | {row['proxy_term']:.6e} | {row['dominant_absolute_term']} |")
    report += ["", "状態の差が大きいことと、長い時刻の予測が外れる主因が状態であることは同じではない。厳密状態を使っても代理量はPF固有値のエネルギー差そのものではなく、その差が費用を決める時刻で大きくなり得る。選択点、各PFの最小費用点、各状態の選択点の全成分はcanonical CSVへ保存した。枝の基準に不合格な点では、f−gというモデルと直接proxyの差は計算できるが、δを含む成分から原因を確定しない。", "",
               "## 4. 継続追跡が不成立な選択点の補助診断", "",
               "各系の元のglobal選択点だけで、PF固有ベクトルを厳密Hamiltonianの基底状態との重なりから独立に選び、E0へ最も近い位相へ戻した。元の予算での誤差を補助的に評価した。正式な継続枝の分類は変更していない。", "",
               "| 系 | 独立に選んだ固有ベクトルの重なり² | 補助エネルギーのずれ［Ha］ | 元の予算での合計誤差［Ha］ | 補助判定 |", "|---|---:|---:|---:|---|"]
    for row in supplemental["records"]:
        label = "位相対応が未確認" if not row["supplementary_phase_valid"] else "目標内" if row["supplementary_precision_met"] else "目標未達"
        report.append(f"| {row['system']} | {row['maximum_ground_overlap']:.9f} | {row['dominant_phase_shift']:.6e} | {row['frozen_budget_total_error']:.6e} | {label} |")
    report += ["", "この独立選択も、すべての時刻で同一の枝を追えた証明ではない。大きな重なりでも位相が目標精度内とは限らない。補助結果を使ってPF・時刻・予算を選び直していない。", "",
               "## 5. Freeze・実装確認・範囲", "",
               "全16のCISD予測を保存してから、4系のHamiltonianの厳密解を計算した。適格12PFについて401点ずつ、計4,812点のPF固有値を評価した。H3の全4PFは元のleading-fitゲートに不合格で、追加範囲や閾値の救済は行っていない。BLASは1thread、workerは最大2。", "",
               "H6 Yoshidaの再現検査で、単一vectorと複数state blockのexpm_multiplyのroundoffが小さいfit時刻で係数差へ増幅された。training proxyの差は3.55×10⁻¹⁶ Haである。元のrunner・protocol・予測・完了済み真値は保持し、別の実装訂正freezeの後、未計算のYoshida真値だけを完了した。運用CISDモデルは元の凍結モデルを唯一の正本とする。既存の真値・選択・予算・科学ゲートは変えていない。", "",
               "新しい分子生成・PF探索・basis変更は行っていない。この追加比較だけで未知の分子に対する精度保証や新しい方法の一般的な優位性は主張しない。matrix/vector/exact stateは/tmpにのみ保存し、公開ファイルはscalar・code・metadataに限る。", "",
               "読む順序: [protocol](protocol.json) → [正式分類と監査](audit.json) → [状態対照](matched_state_allocation.csv) → [三成分の正本](canonical_long_time_error_decomposition.csv) → [補助位相](supplementary_dominant_phase.json)。元のimplementationは[runner](../../review_response/run_lab_progress_hchain_transfer_20261007.py)、訂正は[completion runner](../../review_response/complete_lab_progress_hchain_transfer_20261007.py)。"]
    (base.OUT / "report.md").write_text("\n".join(report) + "\n")
    base.write_json(base.OUT / "manifest.json", {"manifest_self_excluded": True,
                                                "files": [{"path": str(path.relative_to(base.OUT)), "sha256": base.sha(path),
                                                           "bytes": path.stat().st_size}
                                                          for path in sorted(base.OUT.rglob("*")) if path.is_file() and path.name != "manifest.json"]})
    print(json.dumps({"classification": [{"system": row["system"], "status": row["formal_precision_status"]} for row in classification],
                      "direct_candidate_count": direct_point_count, "maximum_eigenpair_residual": maximum_eigenpair_residual,
                      "maximum_unitarity": maximum_unitarity, "frozen_model_decomp_difference": frozen_decomposition_difference}), flush=True)


if __name__ == "__main__":
    run()
