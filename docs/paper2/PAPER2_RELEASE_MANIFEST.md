# AstraHeal Paper 2 — Complete Release Manifest

**Manuscript Title**: *Evidential Uncertainty-Aware Fault Diagnosis for Autonomous Spacecraft Health Management*  
**Release Version**: `Paper 2 — Research Release v1.0`  
**Authors**: AstraHeal Research Group (Autonomous Systems & Aerospace Research)  
**Date**: 2026  
**License**: MIT License / Open Science Public Domain  
**Code Repository**: [https://github.com/madankalyan2211/AstraHeal](https://github.com/madankalyan2211/AstraHeal)  

---

## 1. Research Identity

- **Central Research Question**:  
  *"Can an evidential AI fault-diagnosis system distinguish known spacecraft failure modes from previously unseen or compound failures while explicitly characterizing epistemic and aleatoric uncertainty?"*
- **Primary Scientific Contribution**:  
  A formal evidential Bayesian architecture parameterizing Dirichlet distributions over coupled electro-thermal failure manifolds with closed-form isolation of epistemic (novelty) and aleatoric (noise) uncertainties, supported by five controlled empirical studies and formal statistical tests.
- **Relationship to AstraHeal v1.0**:  
  AstraHeal v1.0 is the frozen platform foundation (counterfactual digital twin planning, Safety Governor, communication blackout arbitration). Paper 2 is an independent, deep scientific investigation of the diagnostic and uncertainty core. AstraHeal v1.0 code, historical benchmarks (01–15), and baseline JSON artifacts were treated as strictly read-only.

---

## 2. Dataset Provenance & Integrity

- **NASA PCoE Battery Data Set (B0005)**:
  - Local File: `data/raw/nasa_pcoe_benchmark_B0005.csv`
  - SHA-256: `4f454d4c083f6ce5e33eb2b6cdbeda3403a633c854a50e6bbce4c18eccdbbfbe`
- **Spacecraft EPS Digital Twin Multi-Orbit Suite**:
  - Local File: `data/processed/mission_run_3orbits_processed.csv`
  - SHA-256: `724bd00cd858452f677716f2ecb93ce5791a1d180d678557c0f34ba72bc22d77`

---

## 3. Verified Main Benchmark Metrics

| Metric Category | Metric Name | Value | 95% Confidence Interval |
|---|---|---|---|
| **Known-Mode Diagnosis** | Accuracy | **95.42%** | $[92.50\%, 97.92\%]$ |
| **Known-Mode Diagnosis** | Macro-F1 | **0.9533** | $[0.9250, 0.9792]$ |
| **Probability Calibration** | Expected Calibration Error (ECE) | **0.0094** ($< 1\%$) | N/A |
| **Out-of-Distribution** | OOD AUROC | **0.9422** | N/A |
| **Out-of-Distribution** | OOD AUPRC | **0.9516** | N/A |
| **OOD Gating (tau = 0.0648)**| True Positive Catch Rate | **76.67%** (FPR = 4.50%) | N/A |
| **Uncertainty Disentanglement** | Epistemic OOD Separation | **10.94x surge** | N/A |
| **Uncertainty Disentanglement** | Aleatoric vs Noise Correlation | $\rho = 0.2955$ ($p = 1.37 \times 10^{-17}$) | N/A |
| **Noise Robustness** | Advantage over Rules Sweep | $+0.3152$ Macro-F1 ($p = 5.77 \times 10^{-6}$) | N/A |

---

## 4. Evaluated Experiments & Code Artifacts

- **Master Runner**: `experiments/paper2/run_all_paper2.py`
- **Experiment 1 (Known Faults)**: `experiments/paper2/01_known_fault_diagnosis.py`
- **Experiment 2 (Uncertainty)**: `experiments/paper2/02_uncertainty_analysis.py`
- **Experiment 3 (OOD & Compound)**: `experiments/paper2/03_ood_detection.py`
- **Experiment 4 (Noise Sweep)**: `experiments/paper2/04_noise_robustness.py`
- **Experiment 5 (Component Ablation)**: `experiments/paper2/05_ablation.py`
- **Statistical Analysis Engine**: `experiments/paper2/compute_statistics.py`
- **Paper 2 Test Suite**: `tests/paper2/test_paper2_pipeline.py` (6 / 6 tests passing)

---

## 5. Frozen Evaluation JSON Artifacts

- `evaluation/paper2/known_fault_results.json` (`d0e2e872...`)
- `evaluation/paper2/uncertainty_results.json` (`0ce19597...`)
- `evaluation/paper2/ood_results.json` (`e41c3bbf...`)
- `evaluation/paper2/noise_robustness_results.json` (`718e7695...`)
- `evaluation/paper2/ablation_results.json` (`46ce971a...`)
- `evaluation/paper2/statistical_results.json` (`090b7a45...`)

---

## 6. Publication Figures

- `docs/paper2/figures/fig1_confusion_matrices.png`: Confusion matrices comparing Random Forest vs Evidential Engine
- `docs/paper2/figures/fig2_calibration_curves.png`: Reliability diagram comparing ECE across 5 models
- `docs/paper2/figures/fig3_uncertainty_disentanglement.png`: 2D scatter plot of Aleatoric vs Epistemic uncertainty
- `docs/paper2/figures/fig4_uncertainty_vs_noise.png`: Selective uncertainty scaling under additive telemetry noise
- `docs/paper2/figures/fig5_ood_roc_pr_curves.png`: ROC and PR curves for OOD detection
- `docs/paper2/figures/fig6_ood_subsystem_breakdown.png`: OOD catch rates by failure mechanism
- `docs/paper2/figures/fig7_noise_robustness_curves.png`: Multi-panel noise degradation curves
- `docs/paper2/figures/fig8_ablation_comparison.png`: Quantitative ablation comparison bar chart

---

## 7. Manuscript & LaTeX Assets

- **Academic Markdown Manuscript**: [docs/paper2/PAPER2_MANUSCRIPT.md](file:///Users/madanthambisetty/Downloads/SPACE%20PROJECT/docs/paper2/PAPER2_MANUSCRIPT.md)
- **Compile-Ready LaTeX Source**: [docs/paper2/latex/main.tex](file:///Users/madanthambisetty/Downloads/SPACE%20PROJECT/docs/paper2/latex/main.tex)
- **BibTeX Bibliography**: [docs/paper2/latex/references.bib](file:///Users/madanthambisetty/Downloads/SPACE%20PROJECT/docs/paper2/latex/references.bib)
- **Compiled PDF Manuscript**: [docs/paper2/latex/PAPER2.pdf](file:///Users/madanthambisetty/Downloads/SPACE%20PROJECT/docs/paper2/latex/PAPER2.pdf) (3.8 MB, vector typography, tables & embedded figures)
- **Complete LaTeX Zip Package**: [astraheal_paper2_latex.zip](file:///Users/madanthambisetty/Downloads/SPACE%20PROJECT/astraheal_paper2_latex.zip) *(Overleaf-ready standalone archive including main.tex, references.bib, README.md, PAPER2.pdf, and all 9 high-resolution figures)*

---

## 8. Documented Failure Modes & Physical Limitations

1. **Compound Fault Centroid Interference**: Simultaneous multi-fault perturbations partially cancel distance metrics in Euclidean/Mahalanobis space, yielding intermediate epistemic scores ($u_{\text{epistemic}} = 0.301$) below isolated single novel faults ($1.000$).
2. **Preprocessing Invariance Blind Spot**: Absolute magnitude current transformation ($|I_{\text{batt}}|$) renders sensor polarity sign inversions undetectable (6.7% catch rate).
3. **No Operational Flight Heritage**: Validated in high-fidelity numerical simulation and NASA empirical battery archives; has not flown on orbit.
4. **Hardware Destruction Unrecoverability**: Software autonomy cannot prevent vehicle loss when exothermic runaway heat exceeds radiator dissipation capability.

---

## 9. Suggested Citation

```bibtex
@article{astraheal2026paper2,
  title={Evidential Uncertainty-Aware Fault Diagnosis for Autonomous Spacecraft Health Management},
  author={AstraHeal Research Group},
  journal={AstraHeal Research Series},
  volume={2},
  year={2026},
  url={https://github.com/madankalyan2211/AstraHeal}
}
```
