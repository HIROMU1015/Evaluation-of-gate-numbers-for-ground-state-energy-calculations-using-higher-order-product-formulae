"""Plot saved scalar diagnostics; no scientific recalculation or model changes."""

from __future__ import annotations

import csv
import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

HERE = Path(__file__).resolve().parent


def main() -> None:
    with (HERE / "state_decomposition_grid.csv").open(newline="") as handle:
        rows = [row for row in csv.DictReader(handle)
                if row["formula_id"] == "m5_best" and row["state_id"] == "cisd"]
    x = np.array([float(r["time_hartree_inverse"]) for r in rows])
    reliable = np.array([r["branch_reliable"] == "True" for r in rows])
    epsilon = json.loads((HERE / "protocol.json").read_text())["constants"]["epsilon_E_hartree"]
    fig, axes = plt.subplots(1, 2, figsize=(11.8, 4.1), constrained_layout=True)
    ax = axes[0]
    for key, label, color in (
        ("model_signed_shift", "CISD two-term prediction", "#3465a4"),
        ("proxy_hartree", "CISD proxy", "#d97706"),
        ("exact_proxy_hartree", "Exact-H-state proxy", "#8b5cf6"),
        ("direct_shift_hartree", "PF eigenphase shift (reliable only)", "#111827"),
    ):
        y = np.array([float(r[key]) for r in rows])
        if key == "direct_shift_hartree":
            y = np.where(reliable, y, np.nan)
        ax.plot(x, y, label=label, color=color, lw=1.8)
    ax.axhline(0, color="#9ca3af", lw=0.7)
    ax.set_yscale("symlog", linthresh=1e-6)
    ax.set_title("What the model and proxy predict")
    ax.set_ylabel("Signed energy shift [Ha]")
    ax.legend(fontsize=8, loc="lower left")
    ax = axes[1]
    for key, label, color in (
        ("fit_component", "Model extension: |f - g(CISD)|", "#3465a4"),
        ("state_component", "State change: |g(CISD) - g0|", "#dc2626"),
        ("proxy_component", "Proxy definition: |g0 - delta(PF)|", "#059669"),
    ):
        y = np.array([abs(float(r[key])) for r in rows])
        ax.plot(x, np.where(reliable, y, np.nan), label=label, color=color, lw=1.8)
    ax.axhline(epsilon, color="#111827", ls="--", lw=1, label="Target energy accuracy")
    ax.set_yscale("log")
    ax.set_ylim(1e-12, 2e-3)
    ax.set_title("Error sources at the same time")
    ax.set_ylabel("Absolute component [Ha]")
    ax.legend(fontsize=8, loc="lower right")
    for ax in axes:
        ax.set_xlabel("Evolution time [Ha$^{-1}$]")
        ax.set_xlim(x[0], x[-1])
        ax.grid(alpha=0.18)
        for t, label in ((2.1466061014866242, "Selected"), (3.5175172132783867, "Direct-grid best")):
            ax.axvline(t, color="#6b7280", ls=":", lw=1)
            ax.text(t, 0.98, label, transform=ax.get_xaxis_transform(),
                    ha="center", va="top", fontsize=8,
                    bbox={"facecolor": "white", "edgecolor": "none", "alpha": 0.85, "pad": 2})
    fig.suptitle("Fixed H4 / m5_best: the original CISD model at finite times", fontsize=12)
    fig.savefig(HERE / "m5_error_components.png", dpi=200)
    fig.savefig(HERE / "m5_error_components.pdf")
    plt.close(fig)


if __name__ == "__main__":
    main()
