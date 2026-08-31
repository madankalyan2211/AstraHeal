# AstraHeal v1.0 — Research Freeze Manifest

**Version**: `v1.0.0-research-release`  
**Date**: 2026-08-31  
**Status**: **FROZEN (No further modifications to architecture, thresholds, or historical results)**  

---

## 1. Scope of the Research Freeze

This document certifies that the **AstraHeal** autonomous spacecraft fault-recovery intelligence platform has reached its formal research freeze. All 15 experiments, 35 unit tests, benchmarks, dataset provenance records, and ablation matrices are locked and archived.

### Summary of Frozen Components:
1. **Dataset Pipeline**: NASA PCoE Li-ion battery dataset ingestion (`data/raw/` immutable storage, `data/provenance.json` with SHA-256 validation).
2. **Telemetry Preprocessing**: Causal causal filter and physics feature engineering ($dV/dt, dT/dt, dQ/dV, R_{int}$).
3. **Anomaly Detection**: Statistical Z-Score/Mahalanobis, Isolation Forest, and One-Class SVM detector ensemble.
4. **Fault Diagnosis**: Dirichlet evidential Bayesian inference separating Epistemic ($u_{epistemic}$) from Aleatoric ($u_{aleatoric}$) uncertainty.
5. **Digital Twin**: Keplerian LEO orbit dynamics, GaAs triple-junction solar array, Thevenin 1-RC battery equivalent circuit model, and 28V regulated PDU.
6. **Counterfactual Lookahead Simulator**: Zero-leakage deep cloning memory branching and multi-branch forward state trajectory simulation.
7. **Deterministic Safety Governor**: Hard physical safety invariant verification ($T \le 46^\circ\text{C}$, $V \ge 22\text{V}$, $I \le 40\text{A}$, $SoC \ge 15\%$).
8. **Communication-Aware Autonomy**: Urgency arbitration between immediate autonomous action and ground deferral.
9. **Experiment Suite (01–15)**: Complete frozen suite from basic telemetry validation to multi-cycle autonomy, controlled recoverability, and holdout counterfactual trajectory validation.

---

## 2. Frozen Environment & Dependencies

- **Python Version**: `Python 3.12.2`
- **Platform**: `macOS 15.0 arm64`
- **Key Packages**:
  - `pytest == 8.4.2`
  - `numpy == 1.26.4`
  - `pandas == 2.2.2`
  - `scipy == 1.13.1`
  - `scikit-learn == 1.5.1`
  - `pydantic == 2.8.2`
  - `matplotlib == 3.9.2`
  - `pyyaml == 6.0.1`
- **Deterministic Random Seeds**: `[42, 43, 44, 45, 46, 47, 101, 102, ..., 120]`

---

## 3. Experiment Artifacts Registry

| Experiment ID | Script Path | Output Data Artifact | Output Figure Artifact |
| :--- | :--- | :--- | :--- |
| **Exp 01** | `experiments/01_data_ingestion.py` | `data/provenance.json` | `docs/figures/01_nasa_battery_telemetry_trends.png` |
| **Exp 02** | `experiments/02_telemetry_preprocessing.py`| `data/processed/` | `docs/figures/02_feature_distributions.png` |
| **Exp 03** | `experiments/03_anomaly_detection.py` | `evaluation/anomaly_benchmark_results.json` | `docs/figures/03_anomaly_roc_curves.png` |
| **Exp 04** | `experiments/04_fault_diagnosis.py` | `evaluation/diagnosis_evaluation.json` | `docs/figures/04_diagnosis_confusion_matrix.png` |
| **Exp 05** | `experiments/05_digital_twin_simulation.py` | `simulations/digital_twin_nominal_orbit.csv`| `docs/figures/05_digital_twin_orbit_telemetry.png` |
| **Exp 06** | `experiments/06_autonomous_recovery.py` | `evaluation/06_recovery_eval_results.json` | `docs/figures/06_recovery_trajectories.png` |
| **Exp 07** | `experiments/07_communication_autonomy.py` | `evaluation/07_communication_autonomy_results.json`| `docs/figures/07_comm_decision_matrix.png` |
| **Exp 08** | `experiments/08_unknown_failure_resilience.py`| `evaluation/08_unknown_resilience_results.json`| `docs/figures/08_ood_uncertainty_separation.png` |
| **Exp 09** | `experiments/09_full_benchmark.py` | `evaluation/09_full_benchmark_results.json` | `docs/figures/09_tri_system_benchmark.png` |
| **Exp 10** | `experiments/10_ablation_study.py` | `evaluation/10_ablation_results.json` | `docs/figures/10_ablation_study.png` |
| **Exp 11** | `experiments/11_failure_case_analysis.py` | `evaluation/11_failure_analysis_results.json` | `docs/figures/11_failure_case_taxonomy.png` |
| **Exp 12** | `experiments/12_flagship_mission.py` | `simulations/flagship_mission_telemetry.csv`| `docs/figures/12_flagship_mission_timeline.png` |
| **Exp 13** | `experiments/13_multi_cycle_autonomy.py` | `evaluation/13_multi_cycle_results.json` | `docs/figures/13_multi_cycle_autonomy.png` |
| **Exp 14** | `experiments/14_controlled_recoverability.py`| `evaluation/14_controlled_results.json` | `docs/figures/14_controlled_recoverability/` |
| **Exp 15** | `experiments/15_independent_counterfactual_validation.py`| `evaluation/15_counterfactual_validation.json`| `docs/figures/15_independent_validation/` |

---

## 4. Key Validated Scientific Findings

1. **Deterministic Invariant Enforcement**: 0 executed unsafe actions, 0 Safety Governor bypasses across all evaluations.
2. **Evidential Uncertainty Gating**: 100% of out-of-distribution compound faults detected ($u_{epistemic} \ge 0.79$), reliably triggering safe standby.
3. **Trajectory Prediction Accuracy (Exp 15)**: Under unmodelled physical parameter perturbations (radiator degradation, thermal mass shifts, harness resistance), the digital twin achieves:
   - Temperature MAE: **0.642 °C**
   - Voltage MAE: **0.415 V**
   - SoC MAE: **0.0003**
   - Current MAE: **0.231 A**
   - Power MAE: **10.101 W**
   - **Top-2 Action Selection Accuracy: 95.0%** (Top-1: 55.0%).

---

## 5. Explicit Limitations & Scope Boundaries

- **Numerical Simulation Only**: The platform is validated exclusively in numerical simulation. It has **NOT** been tested in hardware-in-the-loop (HIL) testbeds, thermal vacuum chambers (TVAC), or flight missions.
- **Physical Thermal Limits**: Software autonomy cannot prevent physical thermal runaway when exothermic heat generation exceeds total radiative dissipation capacity ($Q_{exo} > Q_{rad}$).
- **Attribution**: This is an independent research project. No NASA partnership, endorsement, or approval is claimed.
