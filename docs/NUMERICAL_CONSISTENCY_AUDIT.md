# AstraHeal v1.0 — Numerical Consistency & Provenance Audit

**Document**: `docs/NUMERICAL_CONSISTENCY_AUDIT.md`  
**Date**: 2026-08-31  
**Project Version**: `AstraHeal v1.0 — Research Release`  

---

## 1. Executive Summary

This document cross-checks all numerical metrics published across the AstraHeal documentation and traces every value back to its originating experiment script, raw JSON artifact, and scenario scope.

---

## 2. Metric-by-Metric Provenance Matrix

| Metric Name | Published Value | Originating Experiment | Data Artifact Source | Scope / Scenario Boundary | Verified Consistent? |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Anomaly Detection AUROC** | **0.974** | `experiments/03_anomaly_detection.py` | `evaluation/anomaly_benchmark_results.json` | 1440 telemetry frames; abrupt step & drift anomalies | **YES** |
| **Detection Latency** | **0–3 steps (0–30s)** | `experiments/03_anomaly_detection.py` | `evaluation/anomaly_benchmark_results.json` | 10s simulation step size | **YES** |
| **Evidential Diagnosis Accuracy** | **100% (7/7 modes)** | `experiments/04_fault_diagnosis.py` | `evaluation/diagnosis_evaluation.json` | In-distribution single-fault condition matrix | **YES** |
| **Epistemic OOD Uncertainty** | **0.793 – 1.000** | `experiments/08_unknown_failure_resilience.py` | `evaluation/08_unknown_resilience_results.json` | Novel compound multi-faults ($u_{ep} > 0.50$ gating threshold) | **YES** |
| **Executed Unsafe Actions** | **0** | `experiments/06`, `13`, `14`, `15` | All evaluation JSONs | Across 609+ candidate proposal evaluations | **YES** |
| **Safety Governor Bypasses** | **0** | `experiments/06`, `13`, `14`, `15` | All evaluation JSONs | Enforced deterministically across all runs | **YES** |
| **Safety Governor Proposals Blocked** | **609 rejections** | `experiments/13_multi_cycle_autonomy.py` | `evaluation/13_multi_cycle_results.json` | Multi-cycle 3-orbit benchmark across 6 scenarios | **YES** |
| **Delivered Science Payload Energy** | **574.0 Wh (100%)** | `experiments/13_multi_cycle_autonomy.py` | `evaluation/13_multi_cycle_results.json` | Recoverable 3-orbit mission lifetime (120W payload) | **YES** |
| **Survival Rate (Multi-Cycle)** | **50.0% (3/6)** | `experiments/13_multi_cycle_autonomy.py` | `evaluation/13_multi_cycle_results.json` | 3 recoverable (100% survived) + 3 unrecoverable physical limits | **YES** |
| **Survival Rate (Controlled)** | **87.5% (7/8)** | `experiments/14_controlled_recoverability.py` | `evaluation/14_controlled_results.json` | 7 recoverable (100% survived) + 1 unrecoverable thermal runaway | **YES** |
| **Controlled Mission Utility Score** | **0.831** | `experiments/14_controlled_recoverability.py` | `evaluation/14_controlled_results.json` | Fixed utility weights ($w_{surv}=0.45, w_{pay}=0.30, w_{eng}=0.15, w_{viol}=0.10$) | **YES** |
| **Holdout Temperature MAE** | **0.642 °C** | `experiments/15_independent_counterfactual_validation.py` | `evaluation/15_counterfactual_validation.json` | 20 held-out scenarios (100 branches, 3000s lookahead) | **YES** |
| **Holdout Voltage MAE** | **0.415 V** | `experiments/15_independent_counterfactual_validation.py` | `evaluation/15_counterfactual_validation.json` | Under unmodelled parameter shifts ($h_{rad}=1.10, C_{th}\times 0.96$) | **YES** |
| **Holdout SoC MAE** | **0.0003 (0.03%)** | `experiments/15_independent_counterfactual_validation.py` | `evaluation/15_counterfactual_validation.json` | State of charge fraction across 3000s horizon | **YES** |
| **Holdout Battery Current MAE** | **0.231 A** | `experiments/15_independent_counterfactual_validation.py` | `evaluation/15_counterfactual_validation.json` | Battery terminal current trajectory | **YES** |
| **Holdout Battery Power MAE** | **10.101 W** | `experiments/15_independent_counterfactual_validation.py` | `evaluation/15_counterfactual_validation.json` | Net battery power trajectory | **YES** |
| **Top-1 Action Selection Accuracy** | **55.0% (11/20)** | `experiments/15_independent_counterfactual_validation.py` | `evaluation/15_counterfactual_validation.json` | Exact match with ground-truth optimal action under physical shift | **YES** |
| **Top-2 Action Selection Accuracy** | **95.0% (19/20)** | `experiments/15_independent_counterfactual_validation.py` | `evaluation/15_counterfactual_validation.json` | Top-2 predicted ranks contain true ground-truth optimal action | **YES** |

---

## 3. Distinction of Scope Across Benchmark Suites

- **Initial Single-Trigger Suite (`Exp 09`)**: 8 scenarios, 75.0% survival (6 survived / 2 failed). Latched at sunrise current transition.
- **Multi-Cycle Suite (`Exp 13`)**: 6 scenarios over 3-orbit horizons (17,220s), 50.0% survival (3 survived / 3 unrecoverable physical limits). Debounced event engine.
- **Controlled Recoverable Suite (`Exp 14`)**: 8 scenarios, 87.5% survival (7 survived / 1 failed).
- **Independent Holdout Suite (`Exp 15`)**: 20 scenarios, 100 branches, evaluated for trajectory prediction errors and action ranking accuracy under parameter mismatch.

All numbers across all published documents reflect their exact scope without contradiction.
