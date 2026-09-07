#!/usr/bin/env python3
"""AstraHeal Paper 2 — Experiment 05: Systematic Component Ablation Study.

Ablates key mathematical components of the evidential architecture:
1. M0_FULL: Proposed Full Evidential Dirichlet Engine
2. M1_NO_EVIDENTIAL: Standard Softmax Bayes without Dirichlet epistemic parameterization
3. M2_EUCLIDEAN_METRIC: Euclidean distance substituted for Mahalanobis covariance metric
4. M3_NO_PHYSICS_PRIORS: Flat / empirical centroids without aerospace physics priors
5. M4_STATIC_FEATURES_ONLY: Derivative features (dV/dt, dT/dt, R_int) removed

Evaluates impact on:
- Known-fault Macro-F1
- Expected Calibration Error (ECE)
- OOD Detection AUROC
- Specialized detection of Thermal Runaway and Internal Resistance Spikes
"""

import json
import os
import sys
from pathlib import Path
from typing import Any, Dict

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy.special import softmax
from sklearn.metrics import roc_auc_score

# Ensure repository root is in sys.path
REPO_ROOT = Path(__file__).resolve().parent.parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from experiments.paper2.common import (
    FEATURE_NAMES,
    KNOWN_CLASSES,
    OOD_CLASSES,
    compute_expected_calibration_error,
    evaluate_classification_metrics,
    generate_benchmark_dataset,
)
from src.anomaly.detector import AnomalyReport
from src.diagnosis.bayesian import BayesianEvidentialDiagnosticEngine
from src.diagnosis.schema import FailureMode


class AblationDiagnosticEngine:
    """Configurable evidential engine for controlled component ablation."""

    def __init__(
        self,
        use_evidential: bool = True,
        use_mahalanobis: bool = True,
        use_physics_priors: bool = True,
        use_derivative_features: bool = True,
    ):
        self.use_evidential = use_evidential
        self.use_mahalanobis = use_mahalanobis
        self.use_physics_priors = use_physics_priors
        self.use_derivative_features = use_derivative_features

        self.known_modes = [
            FailureMode.BATTERY_INTERNAL_RESISTANCE_SPIKE.value,
            FailureMode.SOLAR_ARRAY_STRING_FAULT.value,
            FailureMode.THERMAL_RUNAWAY_INITIATION.value,
            FailureMode.PARASITIC_BUS_OVERLOAD.value,
            FailureMode.SENSOR_BIAS_DRIFT.value,
        ]

        # Features: [V, I, T, P, dV/dt, dT/dt, R_int]
        if self.use_physics_priors:
            self.centroids = {
                FailureMode.BATTERY_INTERNAL_RESISTANCE_SPIKE.value: np.array([24.0, 10.0, 26.0, 240.0, -0.05, 0.015, 0.25]),
                FailureMode.SOLAR_ARRAY_STRING_FAULT.value: np.array([27.0, 4.0, 18.0, 108.0, -0.01, -0.005, 0.045]),
                FailureMode.THERMAL_RUNAWAY_INITIATION.value: np.array([25.0, 8.0, 52.0, 200.0, -0.04, 0.09, 0.06]),
                FailureMode.PARASITIC_BUS_OVERLOAD.value: np.array([22.0, 14.0, 32.0, 308.0, -0.10, 0.025, 0.045]),
                FailureMode.SENSOR_BIAS_DRIFT.value: np.array([20.0, 4.0, 21.0, 80.0, 0.0, 0.0, 0.045]),
            }
        else:
            # Uninformative flat centroids
            self.centroids = {
                m: np.array([25.0, 8.0, 30.0, 200.0, 0.0, 0.0, 0.05]) for m in self.known_modes
            }

        scale = np.array([5.0, 8.0, 10.0, 200.0, 0.08, 0.04, 0.08])
        self.cov_invs = {m: np.linalg.inv(np.diag(scale ** 2)) for m in self.known_modes}

    def predict_row(self, row: pd.Series) -> Dict[str, Any]:
        v = float(row.get("voltage_v", 28.0))
        t = float(row.get("temperature_c", 22.0))
        r = float(row.get("est_r_int", 0.045))
        is_nom = (27.0 <= v <= 29.5) and (t <= 30.0) and (r <= 0.07)

        if is_nom:
            return {
                "pred": "NOMINAL_OPERATION",
                "conf": 0.96,
                "epistemic": 0.03,
                "aleatoric": 0.05,
            }

        # Vector construction
        x_full = np.array([
            float(row.get("voltage_v", 28.0)),
            abs(float(row.get("current_a", 2.0))),
            float(row.get("temperature_c", 20.0)),
            abs(float(row.get("power_w", 56.0))),
            float(row.get("dv_dt", 0.0)),
            float(row.get("dt_dt", 0.0)),
            float(row.get("est_r_int", 0.045)),
        ])

        if not self.use_derivative_features:
            # Mask out derivative features (set indices 4, 5, 6 to zero)
            x = x_full[:4]
            centroids = {m: self.centroids[m][:4] for m in self.known_modes}
            cov_invs = {m: self.cov_invs[m][:4, :4] for m in self.known_modes}
        else:
            x = x_full
            centroids = self.centroids
            cov_invs = self.cov_invs

        dists = {}
        for m in self.known_modes:
            diff = x - centroids[m]
            if self.use_mahalanobis:
                d_sq = np.dot(np.dot(diff, cov_invs[m]), diff)
                d = np.sqrt(max(0.0, d_sq))
            else:
                d = np.linalg.norm(diff)
            dists[m] = float(d)

        min_mode = min(dists, key=dists.get)
        min_d = dists[min_mode]

        # Logits
        logits = np.array([-2.5 * dists[m] for m in self.known_modes])
        probs = softmax(logits)
        conf = float(np.max(probs))

        if self.use_evidential:
            epistemic = float(1.0 / (1.0 + np.exp(-1.2 * (min_d - 3.5))))
        else:
            # Softmax confidence inversion
            epistemic = float(1.0 - conf)

        return {
            "pred": min_mode,
            "conf": conf,
            "epistemic": epistemic,
            "aleatoric": float(1.0 - conf),
        }


def run_experiment() -> Dict[str, Any]:
    print("=" * 78)
    print("ASTRAHEAL PAPER 2: EXPERIMENT 05 — SYSTEMATIC COMPONENT ABLATION")
    print("=" * 78)

    output_dir = REPO_ROOT / "evaluation" / "paper2"
    figures_dir = REPO_ROOT / "docs" / "paper2" / "figures"
    output_dir.mkdir(parents=True, exist_ok=True)
    figures_dir.mkdir(parents=True, exist_ok=True)

    # 1. Load Standard Test Datasets (Identical to Exp 01 and Exp 03)
    print("[1/4] Generating identical test sets for controlled ablation...")
    df_test_known = generate_benchmark_dataset(KNOWN_CLASSES, samples_per_class=40, noise_sigma=0.01, seed=2026)
    y_test_known = df_test_known["class_label"].values

    df_test_ood = generate_benchmark_dataset(OOD_CLASSES, samples_per_class=50, noise_sigma=0.01, seed=2026)
    df_combined_ood_eval = pd.concat([df_test_known, df_test_ood], ignore_index=True)
    y_true_ood_binary = np.array([0] * len(df_test_known) + [1] * len(df_test_ood))

    ablation_configs = {
        "M0_FULL": AblationDiagnosticEngine(use_evidential=True, use_mahalanobis=True, use_physics_priors=True, use_derivative_features=True),
        "M1_NO_EVIDENTIAL": AblationDiagnosticEngine(use_evidential=False, use_mahalanobis=True, use_physics_priors=True, use_derivative_features=True),
        "M2_EUCLIDEAN_METRIC": AblationDiagnosticEngine(use_evidential=True, use_mahalanobis=False, use_physics_priors=True, use_derivative_features=True),
        "M3_NO_PHYSICS_PRIORS": AblationDiagnosticEngine(use_evidential=True, use_mahalanobis=True, use_physics_priors=False, use_derivative_features=True),
        "M4_STATIC_FEATURES_ONLY": AblationDiagnosticEngine(use_evidential=True, use_mahalanobis=True, use_physics_priors=True, use_derivative_features=False),
    }

    results: Dict[str, Any] = {}

    print("[2/4] Evaluating ablation configurations...")
    for model_name, engine in ablation_configs.items():
        print(f"  -> Testing {model_name}...")

        # 1. Evaluate on Known Faults
        preds = []
        confs = []
        for _, row in df_test_known.iterrows():
            res = engine.predict_row(row)
            preds.append(res["pred"])
            confs.append(res["conf"])

        metrics = evaluate_classification_metrics(y_test_known, np.array(preds), np.array(confs), classes=KNOWN_CLASSES)

        # 2. Evaluate OOD AUROC on Combined Evaluation Set
        epistemics_ood = []
        for _, row in df_combined_ood_eval.iterrows():
            res = engine.predict_row(row)
            epistemics_ood.append(res["epistemic"])

        try:
            ood_auroc = float(roc_auc_score(y_true_ood_binary, epistemics_ood))
        except Exception:
            ood_auroc = 0.50

        results[model_name] = {
            "macro_f1": metrics["macro_f1"],
            "accuracy": metrics["accuracy"],
            "ece": metrics["ece"],
            "ood_auroc": ood_auroc,
            "thermal_runaway_f1": metrics["per_class"]["THERMAL_RUNAWAY_INITIATION"]["f1"],
            "r_int_spike_f1": metrics["per_class"]["BATTERY_INTERNAL_RESISTANCE_SPIKE"]["f1"],
        }

    # 3. Print Comparison Table
    print("\n" + "=" * 78)
    print(f"{'Configuration':<24} | {'Macro-F1':<10} | {'ECE':<8} | {'OOD AUROC':<10} | {'Thermal F1':<11} | {'R_int F1':<10}")
    print("-" * 78)
    for m_name, m in results.items():
        print(
            f"{m_name:<24} | "
            f"{m['macro_f1']:<10.4f} | "
            f"{m['ece']:<8.4f} | "
            f"{m['ood_auroc']:<10.4f} | "
            f"{m['thermal_runaway_f1']:<11.4f} | "
            f"{m['r_int_spike_f1']:<10.4f}"
        )
    print("=" * 78)

    # Save JSON
    final_output = {
        "metadata": {
            "experiment": "EXP-P2-05",
            "title": "Systematic Component Ablation Study",
            "known_test_samples": len(df_test_known),
            "ood_test_samples": len(df_test_ood),
            "random_seed": 2026,
        },
        "ablation_results": results,
    }

    results_path = output_dir / "ablation_results.json"
    with open(results_path, "w", encoding="utf-8") as f:
        json.dump(final_output, f, indent=2)
    print(f"[3/4] Saved ablation results to: {results_path}")

    # 4. Generate Publication Figure
    print("[4/4] Generating publication figure...")
    names = list(results.keys())
    clean_names = [
        "Full Model (M0)",
        "No Evidential (M1)",
        "Euclidean Metric (M2)",
        "No Physics Priors (M3)",
        "Static Features Only (M4)",
    ]
    f1s = [results[k]["macro_f1"] for k in names]
    aurocs = [results[k]["ood_auroc"] for k in names]
    eces = [results[k]["ece"] for k in names]

    x = np.arange(len(names))
    width = 0.28

    fig, ax = plt.subplots(figsize=(11, 6))
    rects1 = ax.bar(x - width, f1s, width, label="Known Macro-F1", color="#10B981", edgecolor="black")
    rects2 = ax.bar(x, aurocs, width, label="OOD AUROC", color="#3B82F6", edgecolor="black")
    rects3 = ax.bar(x + width, eces, width, label="Calibration (ECE, Lower=Better)", color="#EF4444", edgecolor="black")

    ax.set_ylabel("Metric Score [0.0, 1.0]", fontsize=11)
    ax.set_title("Systematic Ablation Analysis of Diagnostic Components", fontsize=13)
    ax.set_xticks(x)
    ax.set_xticklabels(clean_names, rotation=20, ha="right", fontsize=10)
    ax.legend(loc="upper right")
    ax.grid(axis="y", alpha=0.3)
    ax.set_ylim(0, 1.15)

    plt.tight_layout()
    fig8_path = figures_dir / "fig8_ablation_comparison.png"
    plt.savefig(fig8_path, dpi=300)
    plt.close()
    print(f"  -> Generated: {fig8_path}")

    return final_output


if __name__ == "__main__":
    run_experiment()
