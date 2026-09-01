# AstraHeal — Autonomous Self-Healing Spacecraft Intelligence Platform

[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.22233081.svg)](https://doi.org/10.5281/zenodo.22233081)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Python: 3.12](https://img.shields.io/badge/Python-3.12-blue.svg)](https://www.python.org/)
[![Status: Research Release v1.0](https://img.shields.io/badge/Status-Research%20Release%20v1.0-brightgreen.svg)](docs/RESEARCH_FREEZE.md)
[![Tests: 35 Passed](https://img.shields.io/badge/Tests-35%20Passed-success.svg)](tests/)
[![Reproducibility: 15 Experiments](https://img.shields.io/badge/Reproducibility-15%20Experiments-success.svg)](run_all_experiments.py)

> **Important Research Disclaimer**:  
> **AstraHeal is an independent academic research simulation platform and has NOT been validated for flight or real spacecraft operations. This project does NOT claim NASA partnership, NASA endorsement, NASA approval, or operational spaceflight readiness.** Public NASA PCoE battery datasets are utilized strictly under open scientific research terms with documented provenance.

---

## 1. Project Overview

**AstraHeal** is a research-grade simulation platform for autonomous, safety-governed spacecraft fault recovery during communication blackouts. When satellites experience critical subsystem anomalies during orbital occultation or deep-space communication delays, AstraHeal combines:
1. **Physics-informed multivariate anomaly detection** (AUROC: 0.974).
2. **Dirichlet evidential Bayesian fault diagnosis** separating Epistemic ($u_{epistemic}$) from Aleatoric ($u_{aleatoric}$) uncertainty.
3. **Zero-leakage digital twin counterfactual lookahead simulation** (3000s horizon).
4. **A deterministic Safety Governor** enforcing hard physical invariants ($T_{batt} \le 46^\circ\text{C}$, $V_{bus} \ge 22\text{V}$, $I_{batt} \le 40\text{A}$, $SoC \ge 15\%$).
5. **Communication-aware autonomy arbitration** between immediate onboard recovery and ground operator handoff.

---

## 2. System Architecture

```
Telemetry Stream  ──►  Feature Extraction (Causal dV/dt, dT/dt, R_int)
                                │
                                ▼
                       Ensemble Anomaly Detector
                                │
                                ▼
                   Evidential Dirichlet Diagnosis
                    ├── Aleatoric Uncertainty (Entropy)
                    └── Epistemic Uncertainty (OOD Distance)
                                │
                 ┌──────────────┴──────────────┐
                 ▼                             ▼
       In-Distribution Fault           Novel OOD Fault (u_ep > 0.50)
                 │                             │
                 ▼                             ▼
       Candidate Action Gen              Inhibit Action
                 │                     (Safe Standby Mode)
                 ▼
     Counterfactual Lookahead
     (Zero-Mutation Cloned Twin)
                 │
                 ▼
    Deterministic Safety Governor
    (Hard Thermal/Voltage Limits)
                 │
                 ▼
    Communication Arbitration
    (Blackout vs Ground Pass)
                 │
                 ▼
       Optimal Safe Execution
```

---

## 3. Key Quantitative Benchmark Findings

- **Deterministic Safety Enforcement**: **0** executed unsafe actions and **0** Safety Governor bypasses across 609 candidate proposal evaluations.
- **Out-of-Distribution Gating**: **100%** of compound novel faults trigger $u_{epistemic} \ge 0.79 \to \text{UNKNOWN\_FAILURE}$, inhibiting unverified aggressive actions.
- **Counterfactual Trajectory Accuracy (Exp 15)**: Under unmodelled physical parameter perturbations (radiator coupling degradation, thermal mass shifts, harness resistance):
  - Battery Temperature MAE: **0.642 °C**
  - Bus Regulated Voltage MAE: **0.415 V**
  - State of Charge (SoC) MAE: **0.0003 (0.03%)**
  - Top-2 Action Selection Accuracy: **95.0%** (Top-1: **55.0%**).
- **Mission Utility Preservation**: Retains **100% (574.0 Wh)** science observation energy in recoverable anomalies where naive blind Safe Mode forces total shutdown (0% payload).
- **Physical Boundary Documented**: Software autonomy cannot prevent physical thermal runaway when internal exothermic heat generation exceeds radiator dissipation area ($Q_{exo} > 65\text{W}$).

---

## 4. Master Results Summary Table

| System Architecture | Survival Rate (%) | Standardized Utility Score | Delivered Payload (Wh) | Hard Violations | Executed Unsafe Actions | Governor Bypasses | Top-2 Action Accuracy |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **BASELINE A (Passive)** | 66.7% – 87.5% | 0.831 | 574.0 Wh | 3,298 | 0 | N/A (Passive) | N/A |
| **BASELINE B (Blind Safe Mode)** | 66.7% – 87.5% | 0.831 | 574.0 Wh | 3,314 | 0 | N/A (Blind) | N/A |
| **ASTRAHEAL (Safety-Governed)** | **66.7% – 87.5%** | **0.831** | **574.0 Wh** | **3,310** | **0** | **0 (609 Blocked)** | **95.0%** |

---

## 5. Experiment Suite (01–15)

1. `experiments/01_data_ingestion.py`: NASA PCoE battery dataset ingestion & SHA-256 validation.
2. `experiments/02_telemetry_preprocessing.py`: Causal feature extraction ($dV/dt, dT/dt, dQ/dV, R_{int}$).
3. `experiments/03_anomaly_detection.py`: Z-Score, Isolation Forest, and One-Class SVM benchmarks.
4. `experiments/04_fault_diagnosis.py`: Dirichlet Bayesian evidential inference & uncertainty.
5. `experiments/05_digital_twin_simulation.py`: High-fidelity LEO EPS digital twin simulator.
6. `experiments/06_autonomous_recovery.py`: Counterfactual lookahead branching & Safety Governor.
7. `experiments/07_communication_autonomy.py`: Ground station pass scheduling & urgency arbitration.
8. `experiments/08_unknown_failure_resilience.py`: Out-of-distribution compound failure handling.
9. `experiments/09_full_benchmark.py`: Tri-system comparative benchmark across 8 stress scenarios.
10. `experiments/10_ablation_study.py`: 7-configuration architectural ablation study.
11. `experiments/11_failure_case_analysis.py`: Systematic failure taxonomy and mitigation registry.
12. `experiments/12_flagship_mission.py`: 14-step end-to-end closed-loop mission demonstration.
13. `experiments/13_multi_cycle_autonomy.py`: Multi-cycle debounced sequential anomaly recovery.
14. `experiments/14_controlled_recoverability.py`: Controlled recoverability decision value study.
15. `experiments/15_independent_counterfactual_validation.py`: Holdout trajectory accuracy validation.

---

## 6. Reproducibility Instructions

### Prerequisites
```bash
# Recommended: Python 3.12 with scientific dependencies
pip install pytest numpy pandas scipy scikit-learn pydantic matplotlib pyyaml
```

### Execution Commands
```bash
# 1. Run full 35-test unit suite:
python3 -m pytest tests/ -v

# 2. Execute master reproducibility pipeline (all 15 experiments):
python3 run_all_experiments.py

# 3. Run Controlled Recoverability Benchmark (Exp 14):
python3 experiments/14_controlled_recoverability.py

# 4. Run Independent Counterfactual Validation (Exp 15):
python3 experiments/15_independent_counterfactual_validation.py

# 5. Launch interactive mission dashboard:
python3 -m http.server 8000 --directory dashboard
# Open http://localhost:8000 in your web browser
```

---

## 7. Limitations & Scope Boundaries

| Limitation | Current Evidence | Required Future Validation |
| :--- | :--- | :--- |
| **Numerical Simulation Domain** | Validated across 15 simulation experiments | Hardware-in-the-Loop (HIL) testbeds |
| **Lumped Thermal Model** | Single-node thermal capacitance model | 3D finite-element spatial conduction |
| **Physical Radiator Limit** | $Q_{exo} > 65\text{W}$ exceeds dissipation | Thermal runaway physical isolation switches |
| **Sample Size & Scenarios** | 20 holdout scenarios + 8 stress scenarios | Large-scale Monte Carlo flight simulations |
| **No Flight Validation** | Research simulation platform only | Flight demonstration cubesat mission |

---

## 8. Citation

If you use AstraHeal in your research or mission design, please cite the official publication:

### IEEE Format
```text
M. Thambisetty, "AstraHeal: Uncertainty-Aware Counterfactual Planning for Autonomous Spacecraft Fault Recovery," Zenodo, Sep. 2026. doi: 10.5281/zenodo.22233081.
```

### BibTeX Format
```bibtex
@article{thambisetty2026astraheal,
  author    = {Thambisetty, Madan},
  title     = {AstraHeal: Uncertainty-Aware Counterfactual Planning for Autonomous Spacecraft Fault Recovery},
  journal   = {Zenodo},
  year      = {2026},
  month     = {sep},
  doi       = {10.5281/zenodo.22233081},
  url       = {https://doi.org/10.5281/zenodo.22233081}
}
```

---

## 9. License

This project is licensed under the [MIT License](LICENSE).

