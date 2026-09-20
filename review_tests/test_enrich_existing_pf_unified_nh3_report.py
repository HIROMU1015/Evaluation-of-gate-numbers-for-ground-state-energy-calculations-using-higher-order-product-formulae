from __future__ import annotations

import enrich_existing_pf_unified_nh3_report as enrich


def test_report_appendix_identifies_fixed_model_result():
    summary = {
        "formula_summary": [
            {
                "formula": "yoshida4",
                "mean_direct_minimum_cost_ratio_to_m5": 3.1,
                "worst_direct_minimum_cost_ratio_to_m5": 3.6,
            },
            {
                "formula": "yoshida6_m3",
                "mean_direct_minimum_cost_ratio_to_m5": 3.5,
                "worst_direct_minimum_cost_ratio_to_m5": 4.1,
            },
        ]
    }
    diagnostics = {
        "stage1_records": 32,
        "stage1_complete": 30,
        "stage1_short_time_fit_failed": 2,
        "stage2_tasks": 26,
        "stage2_new_direct_points": 1023,
        "stage2_reused_stage1_times": 320,
        "elapsed_seconds_stage2": 2000,
        "summed_direct_point_wall_seconds": 10000,
        "maximum_cpu_rss_gib": 1.5,
        "maximum_gpu_used_mib": 2600,
        "maximum_gpu_peak_increment_mib": 2500,
        "maximum_eigenpair_residual_all_new_points": 1e-13,
        "formal_passing_model_rows": 50,
        "minimum_ground_overlap_formal_passing_rows": 0.999,
        "minimum_adjacent_overlap_formal_passing_new_points": 0.998,
        "maximum_eigenpair_residual_formal_passing_rows": 2e-13,
        "maximum_training_design_condition_number": 6000,
        "branch_warnings": [],
        "stage1_code_commits": ["a"],
        "stage2_code_commits": ["b"],
        "environment": {
            "python": "3.12",
            "packages": {"numpy": "1", "scipy": "1", "pyscf": "2", "cupy-cuda12x": "13"},
        },
    }
    text = enrich.report_appendix(summary, diagnostics)
    assert "Yoshida 4th passes" in text
    assert "unused molecular" in text
    assert enrich.MARKER in text
