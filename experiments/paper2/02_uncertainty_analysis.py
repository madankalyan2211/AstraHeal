#!/usr/bin/env python3
"""AstraHeal Paper 2 — Experiment 02: Epistemic vs Aleatoric Uncertainty Disentanglement.

Evaluates:
- Separation of epistemic (model ignorance/OOD) from aleatoric (data noise/entropy) uncertainty
- Correlation between aleatoric uncertainty and telemetry noise variance
- Correlation between epistemic uncertainty and physical domain shift / novel failures
- Correlation between uncertainty metrics and empirical prediction errors
"""

import json
import os
import sys
from pathlib import Path
from typing import Any, Dict

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy.stats import spearmanr

# Ensure repository root is in sys.path
REPO_ROOT = Path(__file__).resolve().parent.parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from experiments.paper2.common import (
    FEATURE_NAMES,
    KNOWN_CLASSES,
    OOD_CLASSES,
    EvidentialDirichletWrapper,
    generate_synthetic_telemetry_frame,
)


def run_experiment() -> Dict[str, Any]:
    print("=" * 78)
    print("ASTRAHEAL PAPER 2: EXPERIMENT 02 — UNCERTAINTY DISENTANGLEMENT ANALYSIS")
    print("=" * 78)

    output_dir = REPO_ROOT / "evaluation" / "paper2"
    figures_dir = REPO_ROOT / "docs" / "paper2" / "figures"
    output_dir.mkdir(parents=True, exist_ok=True)
    figures_dir.mkdir(parents=True, exist_ok=True)

    evidential_wrapper = EvidentialDirichletWrapper()
    rng = np.random.RandomState(42)

    # 1. Define Controlled Test Regimes (200 frames each)
    print("[1/5] Constructing controlled uncertainty regimes...")
    regimes = {
        "Regime_A_Clean_Familiar": {"classes": KNOWN_CLASSES, "noise": 0.00, "is_ood": False},
        "Regime_B1_Familiar_LowNoise": {"classes": KNOWN_CLASSES, "noise": 0.05, "is_ood": False},
        "Regime_B2_Familiar_MedNoise": {"classes": KNOWN_CLASSES, "noise": 0.10, "is_ood": False},
        "Regime_B3_Familiar_HighNoise": {"classes": KNOWN_CLASSES, "noise": 0.20, "is_ood": False},
        "Regime_C_Novel_Unseen": {"classes": ["NOVEL_UNSEEN_MODE"], "noise": 0.01, "is_ood": True},
        "Regime_D_Compound_Fault": {"classes": ["COMPOUND_CONCURRENT_FAULT"], "noise": 0.01, "is_ood": True},
        "Regime_E_Extreme_Shift": {"classes": ["EXTREME_THERMAL_INVERSION", "SENSOR_SIGN_INVERSION"], "noise": 0.01, "is_ood": True},
    }

    regime_records = []
    regime_summaries = {}

    for regime_name, cfg in regimes.items():
        classes = cfg["classes"]
        noise = cfg["noise"]
        is_ood = cfg["is_ood"]
        n_samples = 200

        epistemics = []
        aleatorics = []
        confidences = []
        accuracies = []

        for i in range(n_samples):
            cls = classes[i % len(classes)]
            frame = generate_synthetic_telemetry_frame(cls, noise_sigma=noise, rng=rng)
            row = pd.Series(frame)
            diag = evidential_wrapper.predict_frame(row)

            # Ground truth accuracy: for known, check mode; for OOD, check if flagged UNKNOWN_FAILURE
            if not is_ood:
                acc = 1.0 if diag.primary_failure_mode == cls else 0.0
            else:
                acc = 1.0 if (diag.status == "UNKNOWN_FAILURE" or diag.epistemic_uncertainty > 0.45) else 0.0

            epistemics.append(diag.epistemic_uncertainty)
            aleatorics.append(diag.aleatoric_uncertainty)
            confidences.append(diag.confidence)
            accuracies.append(acc)

            regime_records.append({
                "regime": regime_name,
                "class_label": cls,
                "is_ood": is_ood,
                "noise_sigma": noise,
                "epistemic": diag.epistemic_uncertainty,
                "aleatoric": diag.aleatoric_uncertainty,
                "confidence": diag.confidence,
                "accuracy": acc,
            })

        regime_summaries[regime_name] = {
            "is_ood": is_ood,
            "noise_sigma": noise,
            "n_samples": n_samples,
            "accuracy": float(np.mean(accuracies)),
            "mean_confidence": float(np.mean(confidences)),
            "mean_epistemic": float(np.mean(epistemics)),
            "std_epistemic": float(np.std(epistemics)),
            "mean_aleatoric": float(np.mean(aleatorics)),
            "std_aleatoric": float(np.std(aleatorics)),
        }

    df_records = pd.DataFrame(regime_records)

    # 2. Compute Disentanglement Correlations & Statistical Tests
    print("[2/5] Computing statistical correlations and disentanglement metrics...")
    
    # Correlation between noise_sigma and aleatoric uncertainty (on in-distribution data)
    df_id = df_records[~df_records["is_ood"]]
    rho_noise_aleatoric, p_noise_aleatoric = spearmanr(df_id["noise_sigma"], df_id["aleatoric"])
    rho_noise_epistemic, p_noise_epistemic = spearmanr(df_id["noise_sigma"], df_id["epistemic"])

    # Separation between ID and OOD on Epistemic vs Aleatoric
    id_epistemic = df_records[~df_records["is_ood"]]["epistemic"].values
    ood_epistemic = df_records[df_records["is_ood"]]["epistemic"].values
    id_aleatoric = df_records[~df_records["is_ood"]]["aleatoric"].values
    ood_aleatoric = df_records[df_records["is_ood"]]["aleatoric"].values

    epistemic_separation_ratio = float(np.mean(ood_epistemic) / (np.mean(id_epistemic) + 1e-6))
    aleatoric_separation_ratio = float(np.mean(ood_aleatoric) / (np.mean(id_aleatoric) + 1e-6))

    # Correlation between uncertainty and prediction error (1.0 - accuracy)
    error_indicator = (1.0 - df_id["accuracy"]).values
    rho_error_epistemic, _ = spearmanr(df_id["epistemic"], error_indicator)
    rho_error_aleatoric, _ = spearmanr(df_id["aleatoric"], error_indicator)

    results: Dict[str, Any] = {
        "metadata": {
            "experiment": "EXP-P2-02",
            "title": "Epistemic vs Aleatoric Uncertainty Disentanglement",
            "total_evaluated_frames": len(df_records),
            "random_seed": 42,
        },
        "regime_summaries": regime_summaries,
        "disentanglement_metrics": {
            "noise_vs_aleatoric_spearman_rho": float(rho_noise_aleatoric),
            "noise_vs_aleatoric_p_value": float(p_noise_aleatoric),
            "noise_vs_epistemic_spearman_rho": float(rho_noise_epistemic),
            "noise_vs_epistemic_p_value": float(p_noise_epistemic),
            "mean_id_epistemic": float(np.mean(id_epistemic)),
            "mean_ood_epistemic": float(np.mean(ood_epistemic)),
            "mean_id_aleatoric": float(np.mean(id_aleatoric)),
            "mean_ood_aleatoric": float(np.mean(ood_aleatoric)),
            "epistemic_separation_ratio": epistemic_separation_ratio,
            "aleatoric_separation_ratio": aleatoric_separation_ratio,
            "error_vs_epistemic_rho": float(rho_error_epistemic),
            "error_vs_aleatoric_rho": float(rho_error_aleatoric),
        }
    }

    # 3. Print Summary Table
    print("\n" + "=" * 78)
    print(f"{'Regime':<30} | {'Noise':<6} | {'Accuracy':<9} | {'Epistemic (u_e)':<16} | {'Aleatoric (u_a)':<16}")
    print("-" * 78)
    for r_name, s in regime_summaries.items():
        e_str = f"{s['mean_epistemic']:.3f} ± {s['std_epistemic']:.3f}"
        a_str = f"{s['mean_aleatoric']:.3f} ± {s['std_aleatoric']:.3f}"
        print(f"{r_name:<30} | {s['noise_sigma']:<6.2f} | {s['accuracy']:<9.3f} | {e_str:<16} | {a_str:<16}")
    print("=" * 78)
    print(f"Noise vs Aleatoric Spearman Rho:  {rho_noise_aleatoric:.4f} (p = {p_noise_aleatoric:.2e})")
    print(f"Noise vs Epistemic Spearman Rho:  {rho_noise_epistemic:.4f} (p = {p_noise_epistemic:.2e})")
    print(f"Epistemic Separation (OOD / ID): {epistemic_separation_ratio:.2f}x increase")
    print("=" * 78)

    # 4. Save JSON Artifact
    results_path = output_dir / "uncertainty_results.json"
    with open(results_path, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)
    print(f"[4/5] Saved uncertainty results to: {results_path}")

    # 5. Generate Figures
    print("[5/5] Generating publication figures...")

    # Figure 3: Uncertainty Disentanglement (2D Scatter + Marginal Histograms)
    fig, ax = plt.subplots(figsize=(9, 6))
    colors = {
        "Clean Known": ("#10B981", df_records[df_records["regime"] == "Regime_A_Clean_Familiar"]),
        "Noisy Known (σ=0.20)": ("#3B82F6", df_records[df_records["regime"] == "Regime_B3_Familiar_HighNoise"]),
        "Novel Unseen": ("#EF4444", df_records[df_records["regime"] == "Regime_C_Novel_Unseen"]),
        "Compound Fault": ("#8B5CF6", df_records[df_records["regime"] == "Regime_D_Compound_Fault"]),
        "Extreme Shift": ("#F59E0B", df_records[df_records["regime"] == "Regime_E_Extreme_Shift"]),
    }

    for label, (color, subset) in colors.items():
        ax.scatter(subset["aleatoric"], subset["epistemic"], color=color, label=label, alpha=0.65, edgecolors="none", s=35)

    ax.axhline(0.45, color="red", linestyle="--", linewidth=1.5, label="OOD Safe Gating Threshold (τ = 0.45)")
    ax.set_xlabel("Aleatoric Uncertainty ($u_{aleatoric}$) — Observation Noise / Entropy", fontsize=11)
    ax.set_ylabel("Epistemic Uncertainty ($u_{epistemic}$) — Model Ignorance / OOD", fontsize=11)
    ax.set_title("Uncertainty Disentanglement Across Physical Operational Regimes", fontsize=13)
    ax.legend(loc="upper left", framealpha=0.9)
    ax.grid(True, alpha=0.3)
    plt.tight_layout()
    fig3_path = figures_dir / "fig3_uncertainty_disentanglement.png"
    plt.savefig(fig3_path, dpi=300)
    plt.close()
    print(f"  -> Generated: {fig3_path}")

    # Figure 4: Uncertainty Response to Sensor Noise Level
    noise_subsets = [
        ("Regime_A_Clean_Familiar", 0.00),
        ("Regime_B1_Familiar_LowNoise", 0.05),
        ("Regime_B2_Familiar_MedNoise", 0.10),
        ("Regime_B3_Familiar_HighNoise", 0.20),
    ]
    noises = [item[1] for item in noise_subsets]
    mean_aleatoric = [regime_summaries[item[0]]["mean_aleatoric"] for item in noise_subsets]
    std_aleatoric = [regime_summaries[item[0]]["std_aleatoric"] for item in noise_subsets]
    mean_epistemic = [regime_summaries[item[0]]["mean_epistemic"] for item in noise_subsets]
    std_epistemic = [regime_summaries[item[0]]["std_epistemic"] for item in noise_subsets]

    fig, ax = plt.subplots(figsize=(8, 5))
    ax.errorbar(noises, mean_aleatoric, yerr=std_aleatoric, fmt="-o", color="#3B82F6", label="Aleatoric ($u_{aleatoric}$) — Scales with Noise", linewidth=2, capsize=4)
    ax.errorbar(noises, mean_epistemic, yerr=std_epistemic, fmt="-s", color="#10B981", label="Epistemic ($u_{epistemic}$) — Invariant to Clean Noise", linewidth=2, capsize=4)
    ax.axhline(0.45, color="red", linestyle="--", label="OOD Gating Boundary ($0.45$)", alpha=0.7)
    ax.set_xlabel(r"Telemetry Sensor Noise $\sigma$ (Fraction of Dynamic Range)", fontsize=11)
    ax.set_ylabel("Quantified Uncertainty [0.0, 1.0]", fontsize=11)
    ax.set_title("Selective Uncertainty Scaling under Additive Telemetry Noise", fontsize=13)
    ax.legend(loc="center right")
    ax.grid(True, alpha=0.3)
    plt.tight_layout()
    fig4_path = figures_dir / "fig4_uncertainty_vs_noise.png"
    plt.savefig(fig4_path, dpi=300)
    plt.close()
    print(f"  -> Generated: {fig4_path}")

    return results


if __name__ == "__main__":
    run_experiment()
