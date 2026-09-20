# AstraHeal Paper 4 — Phase 30: Complete Reproducibility Guide

**Date**: 2026-09-13  
**Status**: VERIFIED & REPRODUCIBLE  
**Scope**: Exact Commands, Dependencies, Deterministic Seeds, and Execution Procedures

---

## 1. Environment & Dependencies

* **Operating System**: macOS / Linux (Ubuntu 22.04 LTS recommended)
* **Python Version**: Python 3.12+ (Anaconda / Miniconda)
* **Required Libraries**:
  ```bash
  pip install -r requirements.txt
  pip install pytest reportlab scipy matplotlib pydantic
  ```

---

## 2. Automated Test Suite Verification

Run the unified test suite to verify baseline integrity and Paper 4 components:

```bash
# Verify baseline tests + Paper 4 pipeline tests (56 tests total)
pytest -v
```

---

## 3. Re-Running Paper 4 Experiments

### A. Individual Experiments
```bash
# P4-E1: Sequential Fault Recovery (100 scenarios)
python experiments/paper4/01_sequential_fault_recovery.py

# P4-E2: Repeated Recovery Cycles (120 runs)
python experiments/paper4/02_repeated_recovery_cycles.py

# P4-E3: Perturbed Physics Sensitivity (225 runs)
python experiments/paper4/03_perturbed_physics.py

# P4-E4: Telemetry Noise Robustness (225 runs)
python experiments/paper4/04_telemetry_noise.py

# P4-E5: Combined Stress Benchmark (150 runs)
python experiments/paper4/05_combined_stress.py

# P4-E6: Compound Fault Interactions (150 runs)
python experiments/paper4/06_compound_faults.py

# P4-E7: Long-Horizon Multi-Orbit (50 runs)
python experiments/paper4/07_long_horizon_operation.py

# P4-E8: System Architecture Ablation (300 runs)
python experiments/paper4/08_system_ablation.py
```

### B. Full Suite Orchestration
```bash
python experiments/paper4/run_all_paper4.py
```

---

## 4. Generating Publication Figures & Manuscript PDF

```bash
# Generate all 8 high-DPI figures
python scripts/paper4/generate_figures.py

# Generate two-column IEEE Conference PDF
python scripts/paper4/generate_paper4_pdf.py
```

---

## 5. Compiling with Local TeX Live / Overleaf

```bash
cd paper4
pdflatex manuscript.tex
bibtex manuscript
pdflatex manuscript.tex
pdflatex manuscript.tex
```
