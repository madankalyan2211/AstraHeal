# AstraHeal Paper 2 — Complete Reproducibility Protocol

**Title**: *Evidential Uncertainty-Aware Fault Diagnosis for Autonomous Spacecraft Health Management*  
**Year**: 2026  
**Status**: 100% Deterministic & Reproducible (Phase 16 Complete)

---

## 1. Environment Setup & Dependencies

Paper 2 runs on standard Python 3.10+ without proprietary or non-public software.

```bash
# 1. Clone repository
git clone https://github.com/madankalyan2211/AstraHeal.git
cd AstraHeal

# 2. Create and activate isolated environment
python3 -m venv venv
source venv/bin/activate

# 3. Install public dependencies
pip install -r requirements.txt
pip install reportlab
```

*Required Dependencies*:
- `numpy >= 1.26.0`
- `pandas >= 2.2.0`
- `scipy >= 1.13.0`
- `scikit-learn >= 1.4.0`
- `matplotlib >= 3.8.0`
- `seaborn >= 0.13.0`
- `pydantic >= 2.5.0`
- `pytest >= 8.0.0`
- `reportlab >= 4.0.0`

---

## 2. Dataset Verification & SHA-256 Hashes

Verify the integrity of input datasets before running experiments:

```bash
# Verify NASA PCoE Battery B0005 benchmark raw dataset:
shasum -a 256 data/raw/nasa_pcoe_benchmark_B0005.csv
# Expected: 4f454d4c083f6ce5e33eb2b6cdbeda3403a633c854a50e6bbce4c18eccdbbfbe

# Verify preprocessed multi-orbit telemetry benchmark:
shasum -a 256 data/processed/mission_run_3orbits_processed.csv
# Expected: 724bd00cd858452f677716f2ecb93ce5791a1d180d678557c0f34ba72bc22d77
```

---

## 3. Running Unit Tests

Verify that both the frozen baseline tests and the Paper 2 test suite pass:

```bash
# 1. Verify frozen baseline (35 / 35 tests passing)
python3 -m pytest tests/test_*.py -v

# 2. Verify Paper 2 test suite (6 / 6 tests passing)
python3 -m pytest tests/paper2/ -v
```

---

## 4. Master One-Command Experiment Reproduction

To execute all Paper 2 experiments, regenerate raw evaluation JSONs, produce figures, run statistical analyses, and recompile the PDF manuscript:

```bash
python3 experiments/paper2/run_all_paper2.py
```

---

## 5. Individual Experiment Execution Commands

Each study can also be executed independently:

```bash
# Study 1: Known-Fault Diagnosis Benchmark
python3 experiments/paper2/01_known_fault_diagnosis.py
# Generates: evaluation/paper2/known_fault_results.json, fig1, fig2

# Study 2: Uncertainty Disentanglement Analysis
python3 experiments/paper2/02_uncertainty_analysis.py
# Generates: evaluation/paper2/uncertainty_results.json, fig3, fig4

# Study 3: Out-Of-Distribution (OOD) & Compound Failure Detection
python3 experiments/paper2/03_ood_detection.py
# Generates: evaluation/paper2/ood_results.json, fig5, fig6

# Study 4: Telemetry Noise Robustness
python3 experiments/paper2/04_noise_robustness.py
# Generates: evaluation/paper2/noise_robustness_results.json, fig7

# Study 5: Systematic Component Ablation
python3 experiments/paper2/05_ablation.py
# Generates: evaluation/paper2/ablation_results.json, fig8

# Phase 9: Formal Statistical Significance Testing
python3 experiments/paper2/compute_statistics.py
# Generates: evaluation/paper2/statistical_results.json

# Phase 15: Recompile Publication PDF
python3 scripts/paper2/generate_paper2_pdf.py
# Generates: docs/paper2/latex/PAPER2.pdf
```

---

## 6. Verification of Frozen Artifact Hashes

Confirm that newly generated JSON artifacts match the frozen hashes:

```bash
shasum -a 256 evaluation/paper2/*.json
```

Expected SHA-256 signatures:
- `known_fault_results.json`: `d0e2e872e83827963481b1704d1126c402a11e475d5227d3815618d7b44dc648`
- `uncertainty_results.json`: `0ce19597c3277bbe58b2eb57a7023276fbe1d96098ca2bf925c9480eb668516b`
- `ood_results.json`: `e41c3bbf268588944863db880e4edfd646e16eae81b6d6ff6daf765e383ed0b9`
- `noise_robustness_results.json`: `718e76951061ea8bc4fa60041c119f9e5008a9117092729d4cae11fe0878362c`
- `ablation_results.json`: `46ce971a027b256c99fa95749068a545caf7413b720ece6e7e2dbc41e5ed51e5`
- `statistical_results.json`: `090b7a4513101d4b42feb1484ab604fe4cafb5a63676cd7ac816f7829cdb9148`

---

## 7. Zero Hardcoded Machine Paths

All scripts dynamically resolve paths relative to `REPO_ROOT = Path(__file__).resolve().parent.parent.parent`, ensuring full portability across macOS, Linux, and containerized Docker environments.
