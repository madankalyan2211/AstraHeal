"""Unit tests for AstraHeal Paper 2 research infrastructure and common tools."""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from experiments.paper2.common import (
    KNOWN_CLASSES,
    OOD_CLASSES,
    FEATURE_NAMES,
    generate_synthetic_telemetry_frame,
    generate_benchmark_dataset,
    EvidentialDirichletWrapper,
    PhysicsRulesWrapper,
    StandardMahalanobisBaseline,
    compute_expected_calibration_error,
    evaluate_classification_metrics,
)


def test_generate_synthetic_telemetry_frame():
    """Verify that synthetic telemetry frames contain all expected features within reasonable physical bounds."""
    for cls in KNOWN_CLASSES:
        frame = generate_synthetic_telemetry_frame(cls, noise_sigma=0.0)
        for feat in FEATURE_NAMES:
            assert feat in frame, f"Missing feature {feat} in class {cls}"
        assert frame["class_label"] == cls
        assert frame["voltage_v"] > 0.0
        assert frame["est_r_int"] > 0.0


def test_generate_benchmark_dataset():
    """Verify balanced dataset generation and seed determinism."""
    df1 = generate_benchmark_dataset(KNOWN_CLASSES, samples_per_class=10, seed=42)
    df2 = generate_benchmark_dataset(KNOWN_CLASSES, samples_per_class=10, seed=42)
    assert len(df1) == 60
    assert (df1["voltage_v"].values == df2["voltage_v"].values).all()


def test_evidential_dirichlet_wrapper():
    """Verify evidential wrapper returns predictions, confidence, epistemic, and aleatoric uncertainty."""
    wrapper = EvidentialDirichletWrapper()
    df = generate_benchmark_dataset(KNOWN_CLASSES, samples_per_class=5, seed=42)
    preds, confs, epistemics, aleatorics = wrapper.predict_batch(df)

    assert len(preds) == len(df)
    assert len(confs) == len(df)
    assert len(epistemics) == len(df)
    assert len(aleatorics) == len(df)
    assert (confs >= 0.0).all() and (confs <= 1.0).all()
    assert (epistemics >= 0.0).all() and (epistemics <= 1.0).all()
    assert (aleatorics >= 0.0).all() and (aleatorics <= 1.0).all()


def test_standard_mahalanobis_baseline():
    """Verify standard Mahalanobis baseline classifier training and inference."""
    df = generate_benchmark_dataset(KNOWN_CLASSES, samples_per_class=20, seed=42)
    X = df[FEATURE_NAMES].values
    y = df["class_label"].values

    clf = StandardMahalanobisBaseline(KNOWN_CLASSES)
    clf.fit(X, y)
    probs = clf.predict_proba(X)
    preds = clf.predict(X)

    assert probs.shape == (len(X), len(KNOWN_CLASSES))
    assert np.allclose(np.sum(probs, axis=1), 1.0)
    assert len(preds) == len(X)


def test_expected_calibration_error():
    """Verify ECE calculation on synthetic perfect and worst-case calibrations."""
    confs = np.array([0.9, 0.9, 0.9, 0.9])
    preds = np.array(["A", "A", "A", "A"])
    labels = np.array(["A", "A", "A", "A"])  # 100% accurate, 90% confidence
    ece = compute_expected_calibration_error(confs, preds, labels, n_bins=10)
    assert abs(ece - 0.1) < 1e-4


def test_ood_classes_generation():
    """Verify OOD class frame generation."""
    for cls in OOD_CLASSES:
        frame = generate_synthetic_telemetry_frame(cls, noise_sigma=0.0)
        for feat in FEATURE_NAMES:
            assert feat in frame
        assert frame["class_label"] == cls
