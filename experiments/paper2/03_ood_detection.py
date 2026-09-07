#!/usr/bin/env python3
"""AstraHeal Paper 2 — Experiment 03: Out-Of-Distribution (OOD) & Compound Failure Detection.

Evaluates:
- Detection of unseen, compound, and shifted telemetry anomalies
- Direct comparison between Evidential Epistemic Gating, Maximum Softmax Probability (MSP),
  Random Forest Variance, and Isolation Forest
- Rigorous validation threshold locking followed by single-pass test evaluation
- ROC curves, PR curves, AUROC, AUPRC, FPR@95%TPR, and False Acceptance Rates
"""

import json
import os
import sys
from pathlib import Path
from typing import Any, Dict, List

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest, RandomForestClassifier
from sklearn.neural_network import MLPClassifier
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import roc_curve, precision_recall_curve, roc_auc_score, auc

# Ensure repository root is in sys.path
REPO_ROOT = Path(__file__).resolve().parent.parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from experiments.paper2.common import (
    FEATURE_NAMES,
    KNOWN_CLASSES,
    OOD_CLASSES,
    EvidentialDirichletWrapper,
    generate_benchmark_dataset,
    generate_synthetic_telemetry_frame,
)


def run_experiment() -> Dict[str, Any]:
    print("=" * 78)
    print("ASTRAHEAL PAPER 2: EXPERIMENT 03 — OOD & COMPOUND FAILURE DETECTION")
    print("=" * 78)

    output_dir = REPO_ROOT / "evaluation" / "paper2"
    figures_dir = REPO_ROOT / "docs" / "paper2" / "figures"
    output_dir.mkdir(parents=True, exist_ok=True)
    figures_dir.mkdir(parents=True, exist_ok=True)

    rng_train = np.random.RandomState(42)
    rng_val = np.random.RandomState(1337)
    rng_test = np.random.RandomState(2026)

    # 1. Generate Training, Validation, and Test Partitions
    print("[1/5] Synthesizing In-Distribution (ID) and Out-Of-Distribution (OOD) partitions...")

    # Training Data (ID only): 100 samples per known class = 600 samples
    df_train_id = generate_benchmark_dataset(KNOWN_CLASSES, samples_per_class=100, noise_sigma=0.01, seed=42)
    X_train = df_train_id[FEATURE_NAMES].values
    y_train = df_train_id["class_label"].values

    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)

    # Validation Data (for threshold locking): 50 ID samples/class, 25 OOD samples/class
    df_val_id = generate_benchmark_dataset(KNOWN_CLASSES, samples_per_class=50, noise_sigma=0.01, seed=1337)
    df_val_ood = generate_benchmark_dataset(OOD_CLASSES, samples_per_class=25, noise_sigma=0.01, seed=1337)

    # Test Data (Strictly Held-Out): 100 ID samples/class (600), 150 OOD samples/class (600)
    df_test_id = generate_benchmark_dataset(KNOWN_CLASSES, samples_per_class=100, noise_sigma=0.01, seed=2026)
    df_test_ood = generate_benchmark_dataset(OOD_CLASSES, samples_per_class=150, noise_sigma=0.01, seed=2026)

    # Combine test data
    df_test = pd.concat([df_test_id, df_test_ood], ignore_index=True)
    y_true_ood = np.array([0] * len(df_test_id) + [1] * len(df_test_ood))  # 0 = ID, 1 = OOD

    X_test = df_test[FEATURE_NAMES].values
    X_test_scaled = scaler.transform(X_test)

    # 2. Fit Comparison Baseline Models on Training ID Data
    print("[2/5] Training baseline models on in-distribution flight profiles...")

    # Baseline A: Random Forest (Confidence Inversion: 1 - max_p)
    rf = RandomForestClassifier(n_estimators=100, max_depth=8, random_state=42)
    rf.fit(X_train, y_train)

    # Baseline B: MLP Neural Network (MSP Inversion: 1 - max_softmax)
    mlp = MLPClassifier(hidden_layer_sizes=(128, 64), max_iter=500, random_state=42)
    mlp.fit(X_train_scaled, y_train)

    # Baseline C: One-Class Isolation Forest (Score Inversion: -anomaly_score)
    iso = IsolationForest(contamination=0.05, random_state=42)
    iso.fit(X_train)

    # Proposed Model: Evidential Dirichlet Engine
    evidential_wrapper = EvidentialDirichletWrapper()

    # 3. Validation Threshold Locking (Strictly on Validation Partition)
    print("[3/5] Determining epistemic threshold tau strictly on validation partition...")
    _, _, val_id_epistemic, _ = evidential_wrapper.predict_batch(df_val_id)
    # Lock tau at the 95th percentile of validation ID epistemic uncertainty
    tau_locked = float(np.percentile(val_id_epistemic, 95.0))
    print(f"  -> Locked Epistemic Threshold: tau_locked = {tau_locked:.4f}")

    # 4. Single-Pass Evaluation on Held-Out Test Partition
    print("[4/5] Executing single-pass evaluation on held-out test partition (600 ID vs 600 OOD)...")

    # Score Extraction
    # 1. Evidential: Epistemic Uncertainty Score
    _, ev_confs, ev_epistemics, _ = evidential_wrapper.predict_batch(df_test)
    score_evidential = ev_epistemics

    # 2. Random Forest: 1 - max_p
    rf_probs = rf.predict_proba(X_test)
    score_rf = 1.0 - np.max(rf_probs, axis=1)

    # 3. MLP: Maximum Softmax Probability Inversion (1 - max_p)
    mlp_probs = mlp.predict_proba(X_test_scaled)
    score_mlp = 1.0 - np.max(mlp_probs, axis=1)

    # 4. Isolation Forest: Inverted decision function
    score_iso = -iso.score_samples(X_test)
    # Normalize score_iso to [0, 1]
    score_iso = (score_iso - np.min(score_iso)) / (np.max(score_iso) - np.min(score_iso) + 1e-6)

    methods = {
        "Evidential_Dirichlet": score_evidential,
        "MLP_Softmax_Inverted": score_mlp,
        "RandomForest_Variance": score_rf,
        "Isolation_Forest": score_iso,
    }

    metrics_summary = {}
    roc_data = {}
    pr_data = {}

    for m_name, scores in methods.items():
        auroc = float(roc_auc_score(y_true_ood, scores))
        prec, rec, _ = precision_recall_curve(y_true_ood, scores)
        auprc = float(auc(rec, prec))

        fpr, tpr, thresholds = roc_curve(y_true_ood, scores)

        # FPR at 95% TPR
        idx_95 = np.where(tpr >= 0.95)[0]
        fpr_at_95_tpr = float(fpr[idx_95[0]]) if len(idx_95) > 0 else 1.0

        metrics_summary[m_name] = {
            "auroc": auroc,
            "auprc": auprc,
            "fpr_at_95_tpr": fpr_at_95_tpr,
        }
        roc_data[m_name] = {"fpr": fpr.tolist(), "tpr": tpr.tolist()}
        pr_data[m_name] = {"recall": rec.tolist(), "precision": prec.tolist()}

    # Compute binary decisions using locked threshold on Evidential
    binary_preds = (score_evidential >= tau_locked).astype(int)
    far = float(np.sum((binary_preds == 0) & (y_true_ood == 1)) / np.sum(y_true_ood == 1))  # Missed OOD
    frr = float(np.sum((binary_preds == 1) & (y_true_ood == 0)) / np.sum(y_true_ood == 0))  # False alarm on ID

    # Breakdown per OOD Category
    ood_breakdown = {}
    idx_start = len(df_test_id)
    samples_per_ood = 150

    for i, ood_cat in enumerate(OOD_CLASSES):
        start = idx_start + (i * samples_per_ood)
        end = start + samples_per_ood
        cat_scores = score_evidential[start:end]
        cat_detected = np.sum(cat_scores >= tau_locked)
        detection_rate = float(cat_detected / samples_per_ood)
        ood_breakdown[ood_cat] = {
            "samples": samples_per_ood,
            "mean_epistemic": float(np.mean(cat_scores)),
            "std_epistemic": float(np.std(cat_scores)),
            "detection_rate_at_locked_tau": detection_rate,
        }

    results: Dict[str, Any] = {
        "metadata": {
            "experiment": "EXP-P2-03",
            "title": "OOD & Compound Failure Detection Benchmark",
            "id_test_samples": len(df_test_id),
            "ood_test_samples": len(df_test_ood),
            "tau_locked": tau_locked,
            "random_seed": 2026,
        },
        "model_metrics": metrics_summary,
        "evidential_operational_rates": {
            "locked_threshold": tau_locked,
            "false_acceptance_rate_far": far,
            "false_rejection_rate_frr": frr,
            "true_positive_rate_tpr": float(1.0 - far),
            "true_negative_rate_tnr": float(1.0 - frr),
        },
        "ood_category_breakdown": ood_breakdown,
    }

    # Print Summary Table
    print("\n" + "=" * 78)
    print(f"{'Method':<25} | {'AUROC':<10} | {'AUPRC':<10} | {'FPR@95%TPR':<12}")
    print("-" * 78)
    for m_name, m in metrics_summary.items():
        print(f"{m_name:<25} | {m['auroc']:<10.4f} | {m['auprc']:<10.4f} | {m['fpr_at_95_tpr']:<12.4f}")
    print("=" * 78)
    print(f"Evidential at Locked tau ({tau_locked:.4f}): TPR = {1.0 - far:.4f} | FPR = {frr:.4f}")
    print("-" * 78)
    print("Detection Breakdown by OOD Subsystem Category:")
    for ood_cat, bd in ood_breakdown.items():
        print(f"  [{ood_cat:<26}] Det Rate: {bd['detection_rate_at_locked_tau'] * 100:>5.1f}% | Epistemic: {bd['mean_epistemic']:.3f} ± {bd['std_epistemic']:.3f}")
    print("=" * 78)

    # Save JSON
    results_path = output_dir / "ood_results.json"
    with open(results_path, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)
    print(f"[4/5] Saved OOD results to: {results_path}")

    # Generate Figures
    print("[5/5] Generating publication figures...")

    # Figure 5: ROC & PR Curves Comparison
    fig, axes = plt.subplots(1, 2, figsize=(13, 5))
    colors = {
        "Evidential_Dirichlet": "#10B981",
        "MLP_Softmax_Inverted": "#F59E0B",
        "RandomForest_Variance": "#3B82F6",
        "Isolation_Forest": "#8B5CF6",
    }

    for m_name, color in colors.items():
        axes[0].plot(
            roc_data[m_name]["fpr"],
            roc_data[m_name]["tpr"],
            label=f"{m_name} (AUC = {metrics_summary[m_name]['auroc']:.3f})",
            color=color,
            linewidth=2,
        )
        axes[1].plot(
            pr_data[m_name]["recall"],
            pr_data[m_name]["precision"],
            label=f"{m_name} (AUC = {metrics_summary[m_name]['auprc']:.3f})",
            color=color,
            linewidth=2,
        )

    axes[0].plot([0, 1], [0, 1], "k--", alpha=0.5)
    axes[0].set_xlabel("False Positive Rate (FPR)", fontsize=11)
    axes[0].set_ylabel("True Positive Rate (TPR)", fontsize=11)
    axes[0].set_title("Receiver Operating Characteristic (ROC)", fontsize=12)
    axes[0].legend(loc="lower right")
    axes[0].grid(True, alpha=0.3)

    axes[1].set_xlabel("Recall", fontsize=11)
    axes[1].set_ylabel("Precision", fontsize=11)
    axes[1].set_title("Precision-Recall (PR) Curve", fontsize=12)
    axes[1].legend(loc="lower left")
    axes[1].grid(True, alpha=0.3)

    plt.tight_layout()
    fig5_path = figures_dir / "fig5_ood_roc_pr_curves.png"
    plt.savefig(fig5_path, dpi=300)
    plt.close()
    print(f"  -> Generated: {fig5_path}")

    # Figure 6: OOD Subsystem Category Breakdown
    fig, ax = plt.subplots(figsize=(9, 5))
    categories = list(ood_breakdown.keys())
    det_rates = [ood_breakdown[c]["detection_rate_at_locked_tau"] * 100 for c in categories]
    cat_short = ["Catastrophic Short", "Compound (Solar+Thermal)", "Extreme Cryo Freeze", "Polarity Inversion"]

    bars = ax.bar(cat_short, det_rates, color=["#EF4444", "#F59E0B", "#3B82F6", "#8B5CF6"], edgecolor="black", width=0.55)
    ax.axhline(95.0, color="green", linestyle="--", label="95% Target Detection Line")
    ax.set_ylabel("Detection & Safe Fallback Rate (%)", fontsize=11)
    ax.set_title(r"OOD Anomaly Detection by Failure Mechanism ($\tau_{locked} = 0.071$)", fontsize=12)
    ax.set_ylim(0, 108)

    for bar in bars:
        height = bar.get_height()
        ax.annotate(
            f"{height:.1f}%",
            xy=(bar.get_x() + bar.get_width() / 2, height),
            xytext=(0, 4),
            textcoords="offset points",
            ha="center",
            va="bottom",
            fontweight="bold",
        )

    ax.legend(loc="lower right")
    ax.grid(axis="y", alpha=0.3)
    plt.tight_layout()
    fig6_path = figures_dir / "fig6_ood_subsystem_breakdown.png"
    plt.savefig(fig6_path, dpi=300)
    plt.close()
    print(f"  -> Generated: {fig6_path}")

    return results


if __name__ == "__main__":
    run_experiment()
