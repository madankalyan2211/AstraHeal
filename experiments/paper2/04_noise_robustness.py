#!/usr/bin/env python3
"""AstraHeal Paper 2 — Experiment 04: Telemetry Noise Robustness Benchmark.

Evaluates:
- Graceful degradation of diagnostic accuracy and Macro-F1 across sensor noise sweep sigma in [0.00, 0.25]
- Selective inflation of aleatoric uncertainty vs stability of epistemic gating
- Expected Calibration Error (ECE) degradation trajectories
- False OOD rejection rate on known faults under noise
"""

import json
import os
import sys
from pathlib import Path
from typing import Any, Dict, List

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.neural_network import MLPClassifier
from sklearn.preprocessing import StandardScaler

# Ensure repository root is in sys.path
REPO_ROOT = Path(__file__).resolve().parent.parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from experiments.paper2.common import (
    FEATURE_NAMES,
    KNOWN_CLASSES,
    EvidentialDirichletWrapper,
    PhysicsRulesWrapper,
    compute_expected_calibration_error,
    evaluate_classification_metrics,
    generate_benchmark_dataset,
)


def run_experiment() -> Dict[str, Any]:
    print("=" * 78)
    print("ASTRAHEAL PAPER 2: EXPERIMENT 04 — TELEMETRY NOISE ROBUSTNESS")
    print("=" * 78)

    output_dir = REPO_ROOT / "evaluation" / "paper2"
    figures_dir = REPO_ROOT / "docs" / "paper2" / "figures"
    output_dir.mkdir(parents=True, exist_ok=True)
    figures_dir.mkdir(parents=True, exist_ok=True)

    noise_levels = [0.00, 0.02, 0.05, 0.10, 0.15, 0.20, 0.25]
    n_samples_per_class = 50  # 300 test frames per noise level

    # 1. Fit Train Baseline Models on Clean Data (Seed 42)
    print("[1/4] Training baseline classifiers on clean telemetry (sigma = 0.00)...")
    df_train = generate_benchmark_dataset(KNOWN_CLASSES, samples_per_class=100, noise_sigma=0.00, seed=42)
    X_train = df_train[FEATURE_NAMES].values
    y_train = df_train["class_label"].values

    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)

    rf = RandomForestClassifier(n_estimators=100, max_depth=8, random_state=42)
    rf.fit(X_train, y_train)

    mlp = MLPClassifier(hidden_layer_sizes=(128, 64), max_iter=500, random_state=42)
    mlp.fit(X_train_scaled, y_train)

    rules_wrapper = PhysicsRulesWrapper()
    evidential_wrapper = EvidentialDirichletWrapper()

    # Epistemic OOD threshold locked from Exp 03
    tau_locked = 0.0648

    results_by_noise: Dict[str, Any] = {}

    print("[2/4] Sweeping sensor noise levels across models...")
    for sigma in noise_levels:
        sigma_key = f"sigma_{sigma:.2f}"
        print(f"  -> Testing sigma = {sigma:.2f}...")

        df_test = generate_benchmark_dataset(KNOWN_CLASSES, samples_per_class=n_samples_per_class, noise_sigma=sigma, seed=2026)
        X_test = df_test[FEATURE_NAMES].values
        y_test = df_test["class_label"].values
        X_test_scaled = scaler.transform(X_test)

        # 1. Physics Rules
        rules_preds, rules_confs = rules_wrapper.predict_batch(df_test)
        rules_m = evaluate_classification_metrics(y_test, rules_preds, rules_confs, classes=KNOWN_CLASSES)

        # 2. Random Forest
        rf_preds = rf.predict(X_test)
        rf_probs = rf.predict_proba(X_test)
        rf_confs = np.max(rf_probs, axis=1)
        rf_m = evaluate_classification_metrics(y_test, rf_preds, rf_confs, classes=KNOWN_CLASSES)

        # 3. MLP Softmax
        mlp_preds = mlp.predict(X_test_scaled)
        mlp_probs = mlp.predict_proba(X_test_scaled)
        mlp_confs = np.max(mlp_probs, axis=1)
        mlp_m = evaluate_classification_metrics(y_test, mlp_preds, mlp_confs, classes=KNOWN_CLASSES)

        # 4. Evidential Engine
        ev_preds, ev_confs, ev_epistemics, ev_aleatorics = evidential_wrapper.predict_batch(df_test)
        ev_m = evaluate_classification_metrics(y_test, ev_preds, ev_confs, classes=KNOWN_CLASSES)

        # False OOD rate: fraction of known faults triggering epistemic OOD flag
        false_ood_rate = float(np.mean(ev_epistemics >= tau_locked))

        results_by_noise[sigma_key] = {
            "sigma": sigma,
            "models": {
                "PhysicsRules": {"accuracy": rules_m["accuracy"], "macro_f1": rules_m["macro_f1"], "ece": rules_m["ece"]},
                "RandomForest": {"accuracy": rf_m["accuracy"], "macro_f1": rf_m["macro_f1"], "ece": rf_m["ece"]},
                "MLP_Softmax": {"accuracy": mlp_m["accuracy"], "macro_f1": mlp_m["macro_f1"], "ece": mlp_m["ece"]},
                "EvidentialDirichlet": {
                    "accuracy": ev_m["accuracy"],
                    "macro_f1": ev_m["macro_f1"],
                    "ece": ev_m["ece"],
                    "mean_epistemic": float(np.mean(ev_epistemics)),
                    "mean_aleatoric": float(np.mean(ev_aleatorics)),
                    "false_ood_rate": false_ood_rate,
                },
            },
        }

    # Summary table
    print("\n" + "=" * 78)
    print(f"{'Sigma':<8} | {'Rules F1':<10} | {'RF F1':<10} | {'MLP F1':<10} | {'Evidential F1':<14} | {'False OOD %':<12}")
    print("-" * 78)
    for sigma_key, data in results_by_noise.items():
        s = data["sigma"]
        m = data["models"]
        print(
            f"{s:<8.2f} | "
            f"{m['PhysicsRules']['macro_f1']:<10.4f} | "
            f"{m['RandomForest']['macro_f1']:<10.4f} | "
            f"{m['MLP_Softmax']['macro_f1']:<10.4f} | "
            f"{m['EvidentialDirichlet']['macro_f1']:<14.4f} | "
            f"{m['EvidentialDirichlet']['false_ood_rate'] * 100:<12.1f}%"
        )
    print("=" * 78)

    # Save JSON
    final_output = {
        "metadata": {
            "experiment": "EXP-P2-04",
            "title": "Telemetry Noise Robustness Benchmark",
            "noise_levels": noise_levels,
            "samples_per_noise_level": len(KNOWN_CLASSES) * n_samples_per_class,
            "random_seed": 2026,
            "tau_locked": tau_locked,
        },
        "results_by_noise": results_by_noise,
    }

    results_path = output_dir / "noise_robustness_results.json"
    with open(results_path, "w", encoding="utf-8") as f:
        json.dump(final_output, f, indent=2)
    print(f"[3/4] Saved noise robustness results to: {results_path}")

    # Generate Publication Figures
    print("[4/4] Generating publication figure...")
    sigmas = noise_levels

    f1_rules = [results_by_noise[f"sigma_{s:.2f}"]["models"]["PhysicsRules"]["macro_f1"] for s in sigmas]
    f1_rf = [results_by_noise[f"sigma_{s:.2f}"]["models"]["RandomForest"]["macro_f1"] for s in sigmas]
    f1_mlp = [results_by_noise[f"sigma_{s:.2f}"]["models"]["MLP_Softmax"]["macro_f1"] for s in sigmas]
    f1_ev = [results_by_noise[f"sigma_{s:.2f}"]["models"]["EvidentialDirichlet"]["macro_f1"] for s in sigmas]

    u_aleatoric = [results_by_noise[f"sigma_{s:.2f}"]["models"]["EvidentialDirichlet"]["mean_aleatoric"] for s in sigmas]
    u_epistemic = [results_by_noise[f"sigma_{s:.2f}"]["models"]["EvidentialDirichlet"]["mean_epistemic"] for s in sigmas]
    false_oods = [results_by_noise[f"sigma_{s:.2f}"]["models"]["EvidentialDirichlet"]["false_ood_rate"] * 100 for s in sigmas]
    eces = [results_by_noise[f"sigma_{s:.2f}"]["models"]["EvidentialDirichlet"]["ece"] for s in sigmas]

    fig, axes = plt.subplots(2, 2, figsize=(13, 10))

    # Panel A: Macro-F1 vs Noise
    axes[0, 0].plot(sigmas, f1_ev, "-o", color="#10B981", label="Evidential Dirichlet (Ours)", linewidth=2.2)
    axes[0, 0].plot(sigmas, f1_rf, "-s", color="#3B82F6", label="Random Forest", linewidth=1.8)
    axes[0, 0].plot(sigmas, f1_mlp, "-^", color="#F59E0B", label="MLP Softmax", linewidth=1.8)
    axes[0, 0].plot(sigmas, f1_rules, "-x", color="#64748B", label="Physics Rules", linewidth=1.8)
    axes[0, 0].set_title("(a) Diagnostic Macro-F1 Degradation vs Noise", fontsize=12)
    axes[0, 0].set_xlabel(r"Sensor Noise Level $\sigma$ (Rel. Variance)", fontsize=10)
    axes[0, 0].set_ylabel("Macro-F1 Score", fontsize=10)
    axes[0, 0].legend(loc="lower left")
    axes[0, 0].grid(True, alpha=0.3)

    # Panel B: Uncertainty Disentanglement vs Noise
    axes[0, 1].plot(sigmas, u_aleatoric, "-o", color="#3B82F6", label="Aleatoric ($u_{aleatoric}$)", linewidth=2.2)
    axes[0, 1].plot(sigmas, u_epistemic, "-s", color="#10B981", label="Epistemic ($u_{epistemic}$)", linewidth=2.2)
    axes[0, 1].axhline(tau_locked, color="red", linestyle="--", label=f"Locked OOD Boundary ({tau_locked:.4f})", alpha=0.8)
    axes[0, 1].set_title(r"(b) Uncertainty Response to Sensor Noise $\sigma$", fontsize=12)
    axes[0, 1].set_xlabel(r"Sensor Noise Level $\sigma$", fontsize=10)
    axes[0, 1].set_ylabel("Mean Quantified Uncertainty", fontsize=10)
    axes[0, 1].legend(loc="center left")
    axes[0, 1].grid(True, alpha=0.3)

    # Panel C: Expected Calibration Error vs Noise
    axes[1, 0].plot(sigmas, eces, "-d", color="#8B5CF6", linewidth=2.0)
    axes[1, 0].set_title(r"(c) Evidential Expected Calibration Error (ECE) vs $\sigma$", fontsize=12)
    axes[1, 0].set_xlabel(r"Sensor Noise Level $\sigma$", fontsize=10)
    axes[1, 0].set_ylabel("ECE [0.0, 1.0]", fontsize=10)
    axes[1, 0].grid(True, alpha=0.3)

    # Panel D: False OOD Alarm Rate vs Noise
    axes[1, 1].bar([f"{s:.2f}" for s in sigmas], false_oods, color="#EF4444", alpha=0.8, edgecolor="black", width=0.55)
    axes[1, 1].axhline(10.0, color="black", linestyle=":", label="10% Tolerance Ceiling")
    axes[1, 1].set_title(r"(d) False OOD Trigger Rate on Known Faults vs $\sigma$", fontsize=12)
    axes[1, 1].set_xlabel(r"Sensor Noise Level $\sigma$", fontsize=10)
    axes[1, 1].set_ylabel("False OOD Alarm Rate (%)", fontsize=10)
    axes[1, 1].legend(loc="upper left")
    axes[1, 1].grid(axis="y", alpha=0.3)

    plt.tight_layout()
    fig7_path = figures_dir / "fig7_noise_robustness_curves.png"
    plt.savefig(fig7_path, dpi=300)
    plt.close()
    print(f"  -> Generated: {fig7_path}")

    return final_output


if __name__ == "__main__":
    run_experiment()
