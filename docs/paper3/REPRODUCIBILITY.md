# AstraHeal Paper 3 — Complete Scientific Reproducibility Guide

**Manuscript Title**: *AstraHeal: Deterministic Safety Gating for Uncertainty-Aware Autonomous Spacecraft Fault Recovery*  
**Standard**: Fully Deterministic, Single-Command End-to-End Replication  
**Date**: September 2026  

---

## 1. System Requirements & Environment

* **Operating System**: macOS (tested on macOS 15.0 Apple Silicon), Linux (Ubuntu 22.04+), Windows (WSL2)
* **Python Environment**: Python 3.12+ (tested with Python 3.12.2)
* **Hardware Requirements**: Standard commodity laptop/workstation (no GPU required)

### Dependency Installation
```bash
# Recommended: Create a clean virtual environment
python3 -m venv venv
source venv/bin/activate

# Install required scientific packages
pip install numpy scipy pydantic pytest matplotlib reportlab pyyaml
```

---

## 2. One-Command Master Execution

To re-run the entire Paper 3 experimental suite, regenerate all JSON evaluation artifacts, compute statistical significance tests, generate publication figures, and recompile the vector PDF manuscript:

```bash
python3 experiments/paper3/run_all_paper3.py
```

*Expected runtime*: **$3.5 - 5.0$ seconds** on modern multi-core hardware.

---

## 3. Individual Execution Commands

### A. Run Individual Experiments
```bash
# Experiment P3-E1: Baseline Safety Enforcement
python3 experiments/paper3/01_baseline_safety_enforcement.py

# Experiment P3-E2: Individual Constraint Coverage
python3 experiments/paper3/02_constraint_coverage.py

# Experiment P3-E3: Compound Constraint Violations
python3 experiments/paper3/03_compound_constraint_violations.py

# Experiment P3-E4: Adversarial AI Proposal Injection
python3 experiments/paper3/04_unsafe_ai_proposals.py

# Experiment P3-E5: Continuous Boundary Testing
python3 experiments/paper3/05_boundary_testing.py

# Experiment P3-E6: Communication-Aware Safety Arbitration
python3 experiments/paper3/06_communication_aware_safety.py

# Experiment P3-E7: Physically Constrained No-Safe-Action Scenarios
python3 experiments/paper3/07_no_safe_action.py

# Experiment P3-E8: Ablation, Fail-Closed Testing & Overhead Profiling
python3 experiments/paper3/08_safety_governor_ablation.py

# Formal Statistical Analysis & Wilson Bounds
python3 experiments/paper3/compute_statistics.py
```

### B. Execute Test Suite
```bash
# Run Paper 3 dedicated unit and safety invariant tests:
python3 -m pytest tests/paper3/ -v

# Run entire repository test suite (51/51 passing):
python3 -m pytest tests/ -v
```

### C. Regenerate Publication Figures
```bash
python3 scripts/paper3/generate_paper3_figures.py
```

### D. Compile Vector PDF Manuscript
```bash
python3 scripts/paper3/generate_paper3_pdf.py
```
Outputs pre-compiled vector PDF manuscript to `docs/paper3/latex/PAPER3.pdf`.
