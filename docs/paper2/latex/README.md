# AstraHeal Paper 2 — LaTeX Submission Package

**Manuscript Title**: *Evidential Uncertainty-Aware Fault Diagnosis for Autonomous Spacecraft Health Management*  
**Format**: IEEE Conference / Two-Column Standard (`IEEEtran`)  
**Year**: 2026  
**License**: MIT License / Open Access  

---

## 1. Package Contents

This LaTeX package contains all source files, bibliographies, and high-resolution publication figures required to compile the complete paper:

- **`main.tex`**: Complete IEEEtran two-column LaTeX source code with all mathematical formulations, benchmark tables, IEEE citations, and embedded figure references.
- **`references.bib`**: BibTeX bibliography with full citations formatted to IEEE standards.
- **`figures/`**: Directory containing all 9 publication-grade figures:
  - `fig0_dataset_telemetry_profiles.png`: 4-panel dataset telemetry profiles (NASA PCoE & EPS Digital Twin)
  - `fig1_confusion_matrices.png`: Confusion matrices comparing Random Forest vs. Evidential Dirichlet
  - `fig2_calibration_curves.png`: Reliability diagrams and ECE across 5 diagnostic models
  - `fig3_uncertainty_disentanglement.png`: Aleatoric vs. Epistemic uncertainty scatter distribution
  - `fig4_uncertainty_vs_noise.png`: Uncertainty scaling under additive telemetry noise
  - `fig5_ood_roc_pr_curves.png`: OOD detection ROC and Precision-Recall curves
  - `fig6_ood_subsystem_breakdown.png`: OOD catch rate breakdown across physical failure categories
  - `fig7_noise_robustness_curves.png`: 4-panel noise sweep degradation trajectories
  - `fig8_ablation_comparison.png`: Quantitative component ablation performance bars
- **`PAPER2.pdf`**: Pre-compiled publication-grade PDF manuscript (3.8 MB).

---

## 2. Compiling with Local TeX (TeX Live / MacTeX / MikTeX)

Run the standard compilation sequence:

```bash
pdflatex main.tex
bibtex main
pdflatex main.tex
pdflatex main.tex
```

---

## 3. Uploading to Overleaf

1. Upload the entire `docs/paper2/latex/` directory (or the provided `astraheal_paper2_latex.zip` file) to Overleaf:
   - Click **New Project** $\rightarrow$ **Upload Project**.
   - Select `astraheal_paper2_latex.zip`.
2. Confirm that the compiler is set to **pdfLaTeX** and the main document is set to `main.tex`.
3. Click **Recompile**.
