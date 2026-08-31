# AstraHeal v1.0 — Public Research Release

**Release Tag**: `v1.0.0-research-release`  
**Release Name**: `AstraHeal v1.0 — Autonomous Self-Healing Spacecraft Intelligence Platform`  
**Date**: 2026-08-31  
**License**: MIT License  

---

## 1. Release Description & Research Scope

AstraHeal is a research-grade simulation platform for autonomous, safety-governed spacecraft fault recovery during communication blackouts. The platform integrates Dirichlet evidential Bayesian uncertainty quantification, zero-mutation digital twin counterfactual lookahead simulation, a deterministic physical Safety Governor, and communication-aware autonomy arbitration.

> **Research Simulation Disclaimer**:  
> *AstraHeal is an independent academic research simulation platform and has NOT been validated for flight or real spacecraft operations. This project does NOT claim NASA partnership, NASA endorsement, NASA approval, or operational spaceflight readiness.*

---

## 2. Main Contributions & Validated Capabilities

- **Deterministic Physical Safety Enforcement**: Verified across 609 candidate evaluations with **0 executed unsafe actions** and **0 Safety Governor bypasses**.
- **Calibrated Out-of-Distribution Gating**: 100% detection of compound novel faults ($u_{epistemic} \ge 0.79 \to \text{UNKNOWN\_FAILURE}$), inhibiting unverified aggressive actions.
- **Counterfactual Trajectory Accuracy (Exp 15)**: Under unmodelled physical parameter perturbations (radiator degradation, thermal mass shifts, harness resistance):
  - Battery Temperature MAE: **0.642 °C**
  - Bus Regulated Voltage MAE: **0.415 V**
  - State of Charge (SoC) MAE: **0.0003 (0.03%)**
  - Top-2 Action Selection Accuracy: **95.0%** (Top-1: **55.0%**).
- **Mission Capability Preservation**: Retains **100% (574.0 Wh)** science observation energy in recoverable anomalies where naive blind Safe Mode forces total shutdown.

---

## 3. Repository Organization

```
├── src/                    # Core architecture (digital twin, planner, governor, diagnosis)
├── experiments/            # 15 reproducible research experiments (01–15)
├── evaluation/             # Raw JSON evaluation datasets and metrics
├── tests/                  # 35 automated pytest unit tests
├── configs/                # System configuration and physical thresholds
├── data/                   # NASA PCoE battery dataset & SHA-256 provenance
├── dashboard/              # Interactive Mission Dashboard visualizer
├── docs/                   # Complete research documentation, audits, guides
│   ├── paper/              # Full 24-section IEEE/AIAA formatted research paper
│   └── figures/            # 35+ high-resolution publication figures
├── demo.py                 # Public interactive CLI demonstration entrypoint
├── run_all_experiments.py  # Master 15-experiment reproducibility pipeline
├── VERSION                 # Project version metadata
└── README.md               # Master research documentation
```

---

## 4. How to Run

```bash
# 1. Run full 35-test unit suite:
python3 -m pytest tests/ -v

# 2. Run interactive research demonstration (30 seconds):
python3 demo.py

# 3. Execute master reproducibility pipeline (all 15 experiments):
python3 run_all_experiments.py

# 4. Launch interactive mission dashboard:
python3 -m http.server 8000 --directory dashboard
# Open http://localhost:8000 in your browser
```

---

## 5. Final Release Statement

```
=====================================================================================
ASTRAHEAL v1.0 IS A FROZEN RESEARCH BASELINE READY FOR EXTERNAL RESEARCH REVIEW.
=====================================================================================
```
