# AstraHeal Paper 3 — LaTeX Submission Package

**Manuscript Title**: *AstraHeal: Deterministic Safety Gating for Uncertainty-Aware Autonomous Spacecraft Fault Recovery*  
**Format**: IEEE Conference / Two-Column Standard (`IEEEtran`)  
**Year**: 2026  
**License**: MIT License / Open Access  

---

## 1. Package Contents

- **`main.tex`**: Complete IEEEtran two-column LaTeX source code with all mathematical formulations, benchmark tables, citations, and embedded figure references.
- **`paper_standard.tex`**: Self-contained IEEEtran standard LaTeX manuscript with embedded bibliography for immediate, single-file compilation without external BibTeX dependencies.
- **`references.bib`**: BibTeX bibliography formatted to IEEE standards.
- **`figures/`**: Directory containing all 8 publication-grade figures:
  - `fig1_safety_enforcement_comparison.png`: Action execution comparison (Ungoverned vs Governed AI)
  - `fig2_constraint_coverage_matrix.png`: Verification accuracy across 6 hard constraints
  - `fig3_compound_violations_breakdown.png`: Concurrent violation detection recall across double, triple, and quad breaches
  - `fig4_adversarial_injection_robustness.png`: Resilience under 5 adversarial proposal attack vectors
  - `fig5_boundary_testing_sweeps.png`: 4-panel fine sweep across continuous constraint margins
  - `fig6_communication_arbitration_hierarchy.png`: Grouped bar chart demonstrating Level 1 safety dominance
  - `fig7_ablation_and_latency.png`: 2-panel figure showing unsafe execution delta and microsecond latency profile
  - `fig8_no_safe_action_convergence.png`: Verification of non-forcing safe failure convergence
- **`PAPER3.pdf`**: Pre-compiled publication-grade PDF manuscript.

---

## 2. Compiling with Local TeX (TeX Live / MacTeX / MikTeX)

Run the standard compilation sequence:

```bash
pdflatex main.tex
bibtex main
pdflatex main.tex
pdflatex main.tex
```

Or for single-file immediate compilation without BibTeX:
```bash
pdflatex paper_standard.tex
```

---

## 3. Uploading to Overleaf

1. Upload `astraheal_paper3_latex.zip` to Overleaf:
   - Click **New Project** $\rightarrow$ **Upload Project**.
   - Select `astraheal_paper3_latex.zip`.
2. Confirm compiler is set to **pdfLaTeX** and main document is set to `main.tex` (or `paper_standard.tex`).
3. Click **Recompile**.
