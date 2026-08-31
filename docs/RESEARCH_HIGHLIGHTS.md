# AstraHeal v1.0 — Research Highlights & Quantitative Factsheet

**Document**: `docs/RESEARCH_HIGHLIGHTS.md`  
**Date**: 2026-08-31  

---

## 1. Verified Key Results & Experiment Provenance

Every metric listed below is derived from deterministic, reproducible code and logged in frozen JSON evaluation artifacts:

| Verified Research Metric | Value | Originating Experiment | Primary Data Artifact |
| :--- | :--- | :--- | :--- |
| **Executed Unsafe Actions** | **0** | `Exp 06, 13, 14, 15` | `evaluation/*.json` |
| **Safety Governor Bypasses** | **0** | `Exp 06, 13, 14, 15` | `evaluation/*.json` |
| **Unsafe Proposals Blocked by Governor** | **609 rejections** | `Exp 13` | `evaluation/13_multi_cycle_results.json` |
| **Recovery Cycles Logged (3-Orbit)** | **122 cycles** | `Exp 13` | `evaluation/13_multi_cycle_results.json` |
| **Holdout Temperature Prediction MAE** | **0.642 °C** | `Exp 15` | `evaluation/15_counterfactual_validation.json` |
| **Holdout Bus Voltage Prediction MAE** | **0.415 V** | `Exp 15` | `evaluation/15_counterfactual_validation.json` |
| **Holdout State of Charge (SoC) MAE** | **0.0003 (0.03%)** | `Exp 15` | `evaluation/15_counterfactual_validation.json` |
| **Top-2 Action Selection Accuracy** | **95.0% (19/20)** | `Exp 15` | `evaluation/15_counterfactual_validation.json` |
| **Top-1 Action Selection Accuracy** | **55.0% (11/20)** | `Exp 15` | `evaluation/15_counterfactual_validation.json` |
| **Held-Out Validation Scenarios** | **20 scenarios** | `Exp 15` | `evaluation/15_counterfactual_validation.json` |
| **Reproducible Research Experiments** | **15 experiments** | `Exp 01–15` | `run_all_experiments.py` |
| **Passing Automated Unit Tests** | **35 / 35 (100%)** | `tests/` | `pytest tests/ -v` |
| **Multivariate Anomaly AUROC** | **0.974** | `Exp 03` | `evaluation/anomaly_benchmark_results.json` |
| **Delivered Science Energy Retained** | **574.0 Wh (100%)** | `Exp 13` | `evaluation/13_multi_cycle_results.json` |

---

## 2. Core Architectural Pillars

1. **Evidential Dirichlet Bayesian UQ**: Explicitly separates Epistemic ($u_{epistemic} \ge 0.79$ on OOD faults) from Aleatoric ($u_{aleatoric}$) uncertainty.
2. **Zero-Leakage Digital Twin Counterfactuals**: Explores candidate branches over 3000s horizons without state vector contamination.
3. **Deterministic Safety Gating**: Evaluates hard thermal ($T \le 46^\circ\text{C}$), voltage ($V \ge 22\text{V}$), current ($I \le 40\text{A}$), and storage ($SoC \ge 15\%$) physical constraints.
4. **Communication-Aware Arbitration**: Prevents premature onboard intervention during active ground station passes.
