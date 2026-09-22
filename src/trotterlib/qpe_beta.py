from __future__ import annotations

from typing import Sequence

import numpy as np
import matplotlib.pyplot as plt


def eval_Fejer_kernel(T: int, x: np.ndarray) -> np.ndarray:
    """
    Generate the kernel of QPE
    """
    x_avoid = np.abs(x % (2 * np.pi)) < 1e-8
    numer = np.sin(0.5 * T * x) ** 2
    denom = np.sin(0.5 * x) ** 2
    denom += x_avoid
    ret = numer / denom
    ret = (1 - x_avoid) * ret + (T**2) * x_avoid
    return ret / T


def generate_QPE_distribution(
    spectrum: Sequence[float], population: Sequence[float], T: int
) -> np.ndarray:
    """
    Generate the index distribution of QPE
    """
    T = int(T)
    N = len(spectrum)
    dist = np.zeros(T)
    j_arr = 2 * np.pi * np.arange(T) / T - np.pi
    for k in range(N):
        dist += population[k] * eval_Fejer_kernel(T, j_arr - spectrum[k]) / T
    return dist


def draw_with_prob(measure: np.ndarray, N: int) -> np.ndarray:
    """
    Draw N indices independently from a given measure
    """
    L = measure.shape[0]
    cdf_measure = np.cumsum(measure)  # 累積和dis
    normal_fac = cdf_measure[-1]
    U = np.random.rand(N) * normal_fac  # 0-1のランダムな数をN個作製
    index = np.searchsorted(cdf_measure, U)
    return index


def estimate_phase(k: int, T: int) -> float:
    estimate = 2 * np.pi * k / (T) - np.pi
    return estimate


def QPE(
    spectrum: Sequence[float], population: Sequence[float], T: int, N: int
) -> float:
    """
    QPE Main routine
    """
    discrete_energies = 2 * np.pi * np.arange(T) / (T) - np.pi
    index_dist = generate_QPE_distribution(
        spectrum, population, T
    )  # Generate QPE samples
    index_samp = draw_with_prob(index_dist, N)
    values, counts = np.unique(index_samp, return_counts=True)
    index_sort = np.argsort(counts)
    estimate_1 = estimate_phase(values[index_sort[-1]], T)
    ground_state_energy = estimate_1
    return ground_state_energy


def beta_plt(
    T_list_QPE: np.ndarray = np.array(
        [128, 256, 512, 1024, 2048, 4096, 8192, 16384, 32768]
    ),
    N_rep: int = 10,  # 繰り返し回数
    N_QPE: int = 100,  # サンプリング数
    spectrum_F: Sequence[float] = [-1.5],
) -> None:
    error_QPE = np.zeros(len(T_list_QPE), dtype="float")
    T_total_QPE = np.zeros(len(T_list_QPE), dtype="float")

    error_QPE_timeevo_all = np.zeros((N_rep, len(T_list_QPE)), dtype="float")
    for n in range(N_rep):
        for k in range(len(T_list_QPE)):
            T_max = T_list_QPE[k]
            output_energy = QPE([spectrum_F[0]], [1], T_max, N_QPE)
            T_total_QPE[k] += T_max * N_QPE
            ##---measure error--##
            error_QPE[k] += np.abs(spectrum_F[0] - output_energy)
            error_QPE_timeevo_all[n][k] += np.abs(spectrum_F[0] - output_energy)
    T_total_QPE = T_total_QPE / N_rep
    error_QPE = error_QPE / N_rep
    error_QPE_std = np.std(error_QPE_timeevo_all, axis=0)

    C = T_list_QPE  # コスト軸に合わせる
    eps = error_QPE

    # ----- α=1 固定フィット -----
    logC, logEps = np.log(C), np.log(eps)

    log_beta = np.average(logEps + logC)
    beta_fix = np.exp(log_beta)

    print(f"α (fixed) = 1.0")
    print(f"β (fitted) = {beta_fix:.3f}")

    # ----- プロット -----
    plt.figure(dpi=150)
    plt.xscale("log")
    plt.yscale("log")

    # データ点
    plt.errorbar(C, eps, yerr=error_QPE_std, fmt="^-", label="QPE")

    # フィット直線
    plt.loglog(
        C, beta_fix / C, "--", lw=3, label=rf"fit: $\varepsilon = {beta_fix:.2f}/M$"
    )

    plt.xlabel("$T$", fontsize=20)
    plt.ylabel(r"$\varepsilon$(T)", fontsize=20)
    plt.xticks(fontsize=15)
    plt.yticks(fontsize=15)
    plt.xlim(1e2, 1e5)
    plt.tight_layout()
    plt.legend(fontsize=15, loc="best")
    plt.tight_layout()
    plt.show()


def beta_scaling(
    T_list_QPE: np.ndarray = np.array(
        [128, 256, 512, 1024, 2048, 4096, 8192, 16384, 32768]
    ),  # M
    N_rep: int = 10,  # 繰り返し回数
    N_QPE: int = 100,  # サンプリング数
    N_trials: int = 100,  # trial 回数
    seed: int | None = 42,  # 乱数 seed (None で毎回変わる)
    plot: bool = True,  # ε(T) をプロットするか
    savepath: str | None = "beta_scaling.pdf",  # PDF 保存先 (None で保存しない)
    n_bootstrap: int = 1000,  # ブートストラップ回数
) -> None:
    # ---- N_trials 回の trial で beta_fix を求めて平均 ----
    beta_fix_list = []
    error_QPE_all_trials = np.zeros((N_trials, len(T_list_QPE)), dtype="float")

    if seed is not None:
        np.random.seed(seed)
    for trial in range(N_trials):
        # [-pi, pi] から一様ランダムに 1 点選択
        spectrum_F = [np.random.uniform(-np.pi, np.pi)]

        error_QPE = np.zeros(len(T_list_QPE), dtype="float")
        T_total_QPE = np.zeros(len(T_list_QPE), dtype="float")
        error_QPE_timeevo_all = np.zeros((N_rep, len(T_list_QPE)), dtype="float")

        for n in range(N_rep):
            for k in range(len(T_list_QPE)):
                T_max = T_list_QPE[k]
                output_energy = QPE([spectrum_F[0]], [1], T_max, N_QPE)
                T_total_QPE[k] += T_max * N_QPE

                # --- measure error ---
                err = np.abs(spectrum_F[0] - output_energy)
                error_QPE[k] += err
                error_QPE_timeevo_all[n][k] += err

        T_total_QPE = T_total_QPE / N_rep
        error_QPE = error_QPE / N_rep
        error_QPE_std = np.std(error_QPE_timeevo_all, axis=0)

        # ---- α=1 固定フィット（元の式を踏襲）----
        C = T_list_QPE  # コスト軸に合わせる
        eps = error_QPE

        # 数値安定化（log(0)回避）。元の式に +tiny を足す以外は変更しない
        tiny = 1e-300
        logC, logEps = np.log(C), np.log(eps + tiny)
        log_beta = np.average(logEps + logC)
        beta_fix = np.exp(log_beta)

        beta_fix_list.append(beta_fix)
        error_QPE_all_trials[trial] = error_QPE

    beta_fix_array = np.array(beta_fix_list, dtype=float)

    mean = beta_fix_array.mean()
    std = beta_fix_array.std(ddof=1)
    sem = std / np.sqrt(N_trials)
    print(f"Mean beta_fix over {N_trials} trials:", mean)
    print(f"Std  beta_fix over {N_trials} trials:", std)
    print(f"SEM  beta_fix over {N_trials} trials:", sem)

    # --- median ベースの β をブートストラップで推定 ---
    C = T_list_QPE
    eps_median = np.median(error_QPE_all_trials, axis=0)
    beta_med = np.exp(np.average(np.log(eps_median) + np.log(C)))

    rng = np.random.default_rng(seed)
    boot_beta = np.empty(n_bootstrap)
    for b in range(n_bootstrap):
        idx = rng.integers(0, N_trials, size=N_trials)
        eps_med_b = np.median(error_QPE_all_trials[idx], axis=0)
        boot_beta[b] = np.exp(np.average(np.log(eps_med_b) + np.log(C)))
    beta_med_se = boot_beta.std(ddof=1)
    ci_lo, ci_hi = np.percentile(boot_beta, [2.5, 97.5])
    print(
        f"beta_median (median fit) = {beta_med:.4f} "
        f"± {beta_med_se:.4f} (bootstrap SE, {n_bootstrap} resamples)"
    )
    print(f"  95% CI = [{ci_lo:.4f}, {ci_hi:.4f}]")

    if plot:
        with plt.rc_context(
            {
                "font.family": "sans-serif",
                "font.sans-serif": ["Helvetica", "Arial", "DejaVu Sans"],
                "mathtext.fontset": "cm",
                "mathtext.rm": "serif",
                "axes.unicode_minus": False,
                "pdf.fonttype": 42,
                "ps.fonttype": 42,
                "axes.linewidth": 1.0,
                "xtick.direction": "in",
                "ytick.direction": "in",
                "xtick.top": True,
                "ytick.right": True,
                "xtick.minor.visible": True,
                "ytick.minor.visible": True,
                "legend.frameon": False,
            }
        ):
            fig, ax = plt.subplots(figsize=(5.5, 4.0), dpi=150)
            ax.set_xscale("log")
            ax.set_yscale("log")

            # violin plot (log10 空間で作成して対数軸にマッピング)
            log_eps = np.log10(error_QPE_all_trials + 1e-300)
            positions = np.log10(C)
            # 各 T の violin 幅 (対数軸で一定見た目になるよう調整)
            widths = 0.15
            parts = ax.violinplot(
                log_eps,
                positions=positions,
                widths=widths,
                showmeans=False,
                showmedians=False,
                showextrema=False,
            )
            # 対数スケールに合わせて位置を修正する必要があるため、自前で描画
            ax.clear()
            ax.set_xscale("log")
            ax.set_yscale("log")

            for k, T in enumerate(C):
                data = error_QPE_all_trials[:, k]
                data = data[data > 0]
                log_data = np.log10(data)
                # カーネル密度
                from scipy.stats import gaussian_kde
                kde = gaussian_kde(log_data)
                ymin, ymax = log_data.min(), log_data.max()
                ys = np.linspace(ymin, ymax, 200)
                dens = kde(ys)
                dens = dens / dens.max() * 0.15  # 幅正規化 (log T 軸で)
                # 対数軸上で T を中心に左右対称に描画
                left = T * 10 ** (-dens)
                right = T * 10 ** (dens)
                ax.fill_betweenx(10 ** ys, left, right, color="C0", alpha=0.35, lw=0)

            # median 点
            ax.plot(C, eps_median, "o", color="C0", ms=5, label="median")

            # fit 線
            ax.plot(
                C,
                beta_med / C,
                "--",
                color="C3",
                lw=1.8,
                label=rf"$\varepsilon = ({beta_med:.2f} \pm {beta_med_se:.2f})/T$",
            )

            ax.set_xlabel(r"$T$", fontsize=16)
            ax.set_ylabel(r"$\varepsilon(T)$", fontsize=16)
            ax.tick_params(axis="both", which="major", labelsize=12)
            ax.legend(fontsize=12, loc="best")
            fig.tight_layout()
            if savepath is not None:
                fig.savefig(savepath, bbox_inches="tight")
            plt.show()
