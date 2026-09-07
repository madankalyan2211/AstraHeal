#!/usr/bin/env python3
"""AstraHeal Paper 2 — Experiment 01: Known-Fault Diagnosis Benchmark.

Evaluates:
- Multiclass classification of known spacecraft EPS failure modes
- Comparison against Physics Rules, Random Forest, MLP, and Mahalanobis baselines
- Expected Calibration Error (ECE) and uncertainty decomposition
- Stratified train/val/test split with zero leakage
"""

import json
import os
import sys
from pathlib import Path
from typing import Any, Dict

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
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
    StandardMahalanobisBaseline,
    compute_expected_calibration_error,
    evaluate_classification_metrics,
    generate_benchmark_dataset,
)


def run_experiment() -> Dict[str, Any]:
    print("=" * 78)
    print("ASTRAHEAL PAPER 2: EXPERIMENT 01 — KNOWN-FAULT DIAGNOSIS BENCHMARK")
    print("=" * 78)

    output_dir = REPO_ROOT / "evaluation" / "paper2"
    figures_dir = REPO_ROOT / "docs" / "paper2" / "figures"
    output_dir.mkdir(parents=True, exist_ok=True)
    figures_dir.mkdir(parents=True, exist_ok=True)

    # 1. Generate Stratified Datasets with Scenario Isolation
    print("[1/5] Generating reproducible synthetic benchmark data across 6 known classes...")
    # 200 samples per class: 120 train (60%), 40 val (20%), 40 test (20%)
    df_train = generate_benchmark_dataset(KNOWN_CLASSES, samples_per_class=120, noise_sigma=0.01, seed=42)
    df_val = generate_benchmark_dataset(KNOWN_CLASSES, samples_per_class=40, noise_sigma=0.01, seed=1337)
    df_test = generate_benchmark_dataset(KNOWN_CLASSES, samples_per_class=40, noise_sigma=0.01, seed=2026)

    X_train = df_train[FEATURE_NAMES].values
    y_train = df_train["class_label"].values
    X_val = df_val[FEATURE_NAMES].values
    y_val = df_val["class_label"].values
    X_test = df_test[FEATURE_NAMES].values
    y_test = df_test["class_label"].values

    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_val_scaled = scaler.transform(X_val)
    X_test_scaled = scaler.transform(X_test)

    results: Dict[str, Any] = {
        "metadata": {
            "experiment": "EXP-P2-01",
            "title": "Known-Fault Diagnosis Benchmark",
            "classes": KNOWN_CLASSES,
            "features": FEATURE_NAMES,
            "train_samples": len(df_train),
            "val_samples": len(df_val),
            "test_samples": len(df_test),
            "random_seeds": {"train": 42, "val": 1337, "test": 2026},
        },
        "models": {},
        "raw_predictions": {},
    }

    # 2. Train & Evaluate Baselines
    print("[2/5] Fitting & evaluating baseline classifiers...")

    # Model A: Physics Rules Baseline
    print("  -> Evaluating Physics Rules Baseline...")
    rules_wrapper = PhysicsRulesWrapper()
    rules_preds, rules_confs = rules_wrapper.predict_batch(df_test)
    rules_metrics = evaluate_classification_metrics(y_test, rules_preds, rules_confs, classes=KNOWN_CLASSES)
    results["models"]["PhysicsRules"] = rules_metrics
    results["raw_predictions"]["PhysicsRules"] = {
        "y_true": y_test.tolist(),
        "y_pred": rules_preds.tolist(),
        "confidences": rules_confs.tolist(),
    }

    # Model B: Random Forest Classifier
    print("  -> Training Random Forest Classifier...")
    rf = RandomForestClassifier(n_estimators=100, max_depth=8, random_state=42)
    rf.fit(X_train, y_train)
    rf_preds = rf.predict(X_test)
    rf_probs = rf.predict_proba(X_test)
    rf_confs = np.max(rf_probs, axis=1)
    rf_metrics = evaluate_classification_metrics(y_test, rf_preds, rf_confs, classes=KNOWN_CLASSES)
    results["models"]["RandomForest"] = rf_metrics
    results["raw_predictions"]["RandomForest"] = {
        "y_true": y_test.tolist(),
        "y_pred": rf_preds.tolist(),
        "confidences": rf_confs.tolist(),
    }

    # Model C: Multi-Layer Perceptron (MLP with Softmax)
    print("  -> Training MLP Classifier (Softmax)...")
    mlp = MLPClassifier(hidden_layer_sizes=(128, 64), max_iter=500, random_state=42)
    mlp.fit(X_train_scaled, y_train)
    mlp_preds = mlp.predict(X_test_scaled)
    mlp_probs = mlp.predict_proba(X_test_scaled)
    mlp_confs = np.max(mlp_probs, axis=1)
    mlp_metrics = evaluate_classification_metrics(y_test, mlp_preds, mlp_confs, classes=KNOWN_CLASSES)
    results["models"]["MLP_Softmax"] = mlp_metrics
    results["raw_predictions"]["MLP_Softmax"] = {
        "y_true": y_test.tolist(),
        "y_pred": mlp_preds.tolist(),
        "confidences": mlp_confs.tolist(),
    }

    # Model D: Standard Mahalanobis Baseline
    print("  -> Evaluating Standard Mahalanobis Classifier...")
    sm = StandardMahalanobisBaseline(KNOWN_CLASSES)
    sm.fit(X_train, y_train)
    sm_preds = sm.predict(X_test)
    sm_probs = sm.predict_proba(X_test)
    sm_confs = np.max(sm_probs, axis=1)
    sm_metrics = evaluate_classification_metrics(y_test, sm_preds, sm_confs, classes=KNOWN_CLASSES)
    results["models"]["StandardMahalanobis"] = sm_metrics
    results["raw_predictions"]["StandardMahalanobis"] = {
        "y_true": y_test.tolist(),
        "y_pred": sm_preds.tolist(),
        "confidences": sm_confs.tolist(),
    }

    # Model E: Proposed Evidential Dirichlet Diagnostic Engine
    print("[3/5] Evaluating Proposed Evidential Dirichlet Engine...")
    evidential_wrapper = EvidentialDirichletWrapper()
    ev_preds, ev_confs, ev_epistemics, ev_aleatorics = evidential_wrapper.predict_batch(df_test)
    ev_metrics = evaluate_classification_metrics(y_test, ev_preds, ev_confs, classes=KNOWN_CLASSES)
    ev_metrics["mean_epistemic_uncertainty"] = float(np.mean(ev_epistemics))
    ev_metrics["mean_aleatoric_uncertainty"] = float(np.mean(ev_aleatorics))
    results["models"]["EvidentialDirichlet"] = ev_metrics
    results["raw_predictions"]["EvidentialDirichlet"] = {
        "y_true": y_test.tolist(),
        "y_pred": ev_preds.tolist(),
        "confidences": ev_confs.tolist(),
        "epistemic_uncertainties": ev_epistemics.tolist(),
        "aleatoric_uncertainties": ev_aleatorics.tolist(),
    }

    # 3. Print Results Summary
    print("\n" + "=" * 78)
    print("KNOWN-FAULT DIAGNOSIS BENCHMARK SUMMARY (HELD-OUT TEST SET)")
    print("-" * 78)
    print(f"{'Model':<24} | {'Accuracy':<10} | {'Macro-F1':<10} | {'ECE':<10} | {'Mean Conf':<10}")
    print("-" * 78)
    for model_name, m in results["models"].items():
        ece_str = f"{m.get('ece', 0.0):.4f}" if "ece" in m else "N/A"
        conf_str = f"{m.get('mean_confidence', 0.0):.4f}" if "mean_confidence" in m else "N/A"
        print(f"{model_name:<24} | {m['accuracy']:<10.4f} | {m['macro_f1']:<10.4f} | {ece_str:<10} | {conf_str:<10}")
    print("=" * 78)

    # 4. Save JSON Results
    results_path = output_dir / "known_fault_results.json"
    with open(results_path, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)
    print(f"[4/5] Saved benchmark results to: {results_path}")

    # 5. Generate Figures
    print("[5/5] Generating publication figures...")
    short_labels = [
        "Nominal",
        "R_int Spike",
        "Solar String",
        "Therm Runaway",
        "Bus Overload",
        "Sensor Bias",
    ]

    # Figure 1: Confusion Matrices Comparison
    fig, axes = plt.subplots(1, 2, figsize=(14, 6))
    sns.heatmap(
        np.array(rf_metrics["confusion_matrix"]),
        annot=True,
        fmt="d",
        cmap="Blues",
        xticklabels=short_labels,
        yticklabels=short_labels,
        ax=axes[0],
    )
    axes[0].set_title("Random Forest Baseline (F1: {:.3f})".format(rf_metrics["macro_f1"]), fontsize=12)
    axes[0].set_ylabel("True Failure Mode", fontsize=11)
    axes[0].set_xlabel("Predicted Mode", fontsize=11)
    axes[0].tick_params(axis="x", rotation=45)

    sns.heatmap(
        np.array(ev_metrics["confusion_matrix"]),
        annot=True,
        fmt="d",
        cmap="Greens",
        xticklabels=short_labels,
        yticklabels=short_labels,
        ax=axes[1],
    )
    axes[1].set_title("Proposed Evidential Dirichlet Engine (F1: {:.3f})".format(ev_metrics["macro_f1"]), fontsize=12)
    axes[1].set_ylabel("True Failure Mode", fontsize=11)
    axes[1].set_xlabel("Predicted Mode", fontsize=11)
    axes[1].tick_params(axis="x", rotation=45)

    plt.tight_layout()
    fig1_path = figures_dir / "fig1_confusion_matrices.png"
    plt.savefig(fig1_path, dpi=300)
    plt.close()
    print(f"  -> Generated: {fig1_path}")

    # Figure 2: Calibration Reliability Diagrams
    fig, ax = plt.subplots(figsize=(8, 6))
    bin_boundaries = np.linspace(0.0, 1.0, 11)

    for m_name, color in [
        ("PhysicsRules", "#64748B"),
        ("RandomForest", "#3B82F6"),
        ("MLP_Softmax", "#F59E0B"),
        ("StandardMahalanobis", "#8B5CF6"),
        ("EvidentialDirichlet", "#10B981"),
    ]:
        confs = np.array(results["raw_predictions"][m_name]["confidences"])
        preds = np.array(results["raw_predictions"][m_name]["y_pred"])
        accs = (preds == y_test).astype(float)
        bin_accs = []
        bin_confs = []
        for i in range(10):
            mask = (confs > bin_boundaries[i]) & (confs <= bin_boundaries[i + 1])
            if np.sum(mask) > 0:
                bin_accs.append(np.mean(accs[mask]))
                bin_confs.append(np.mean(confs[mask]))
        ax.plot(bin_confs, bin_accs, marker="o", label=f"{m_name} (ECE: {results['models'][m_name]['ece']:.3f})", color=color, linewidth=1.8)

    ax.plot([0, 1], [0, 1], "k--", label="Perfect Calibration", alpha=0.7)
    ax.set_xlabel("Mean Predicted Confidence", fontsize=11)
    ax.set_ylabel("Fraction of Correct Predictions", fontsize=11)
    ax.set_title("Reliability Diagram: Calibration Across Diagnostic Models", fontsize=13)
    ax.legend(loc="lower right")
    ax.grid(True, alpha=0.3)
    plt.tight_layout()
    fig2_path = figures_dir / "fig2_calibration_curves.png"
    plt.savefig(fig2_path, dpi=300)
    plt.close()
    print(f"  -> Generated: {fig2_path}")

    return results


if __name__ == "__main__":
    run_experiment()
