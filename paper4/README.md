# AstraHeal Paper 4: Robust Multi-Cycle Autonomous Fault Recovery Under Perturbed Spacecraft Conditions

**Part of the AstraHeal Space Research Program**  
*AstraHeal Paper 4 — Capstone Validation*  
**Format**: IEEE Conference Standard Two-Column (`IEEEtran`)  
**Repository**: [https://github.com/madankalyan2211/AstraHeal](https://github.com/madankalyan2211/AstraHeal)  
**Author**: Madan Kalyan Thambisetty (Autonomous Systems & Aerospace Software Research)  

---

## 1. Research Overview

* **The Four-Paper Story**:
  - **Paper 1 (PLAN)**: Counterfactual lookahead planning & Pareto-optimal action selection.
  - **Paper 2 (UNDERSTAND)**: Dirichlet evidential uncertainty estimation & OOD anomaly detection.
  - **Paper 3 (CONSTRAIN)**: Deterministic runtime Safety Governor & immutable physical invariants.
  - **Paper 4 (VALIDATE --- This Work)**: System-level multi-cycle robustness across repeated fault cascades, physical parameter perturbations ($\pm 20\%$), and telemetry sensor noise ($\sigma \in [0.005, 0.080]$).

* **Core Research Question**:
  > *Can an uncertainty-aware autonomous spacecraft health-management system repeatedly diagnose, plan, safely gate, and recover from sequential and perturbed fault conditions without accumulating unsafe behavior or unacceptable degradation in system performance?*

---

## 2. Key Findings & Quantitative Highlights

Across eight controlled experimental regimes evaluating over 1,200 multi-cycle missions:
1. **Sequential Fault Survival**: $96.0\%$ mission survival rate across 100 sequential multi-fault scenarios spanning 3 full LEO orbits ($17,220\,\text{s}$).
2. **Repeated Cycle Stability**: Stable recovery across up to 10 repeated anomaly cycles ($k=10$), demonstrating characterized graceful payload scaling rather than catastrophic collapse.
3. **Physical Parameter Tolerance**: Maintained safety and survival across $\pm 20\%$ perturbations in thermal capacitance ($C_{\text{th}}$), radiator coupling ($h_{\text{rad}}$), internal resistance ($R_0$), and solar array conversion efficiency ($\eta_{\text{solar}}$).
4. **Epistemic Uncertainty Scaling**: Dirichlet evidential uncertainty scaled monotonically with sensor noise ($\sigma = 0.005$ to $0.080$), preventing premature or misdirected actuations under corrupted telemetry.
5. **Zero Unsafe Executions**: Exactly $0.00\%$ unsafe action executions were observed across all evaluated stress scenarios (Clopper-Pearson exact 95% upper bound $< 0.24\%$).
6. **Ablation Demonstration**: Operating without the Safety Governor caused a catastrophic $96.0\%$ unsafe execution rate (McNemar $p = 1.82 \times 10^{-21}$, Cohen's $h = 2.82$).

---

## 3. Package Structure

```
paper4/
├── manuscript.tex          # Primary IEEEtran LaTeX manuscript
├── paper_standard.tex      # Self-contained single-file compilation manuscript
├── references.bib          # IEEE formatted aerospace citations
├── IEEEtran.cls            # Official IEEEtran class file
├── PAPER4.pdf              # Publication-grade compiled PDF manuscript
├── figures/                # Publication-grade figures (300 DPI)
│   ├── fig1_integrated_architecture.png
│   ├── fig2_sequential_timeline.png
│   ├── fig3_repeated_cycles_degradation.png
│   ├── fig4_perturbed_physics_sensitivity.png
│   ├── fig5_telemetry_noise_robustness.png
│   ├── fig6_combined_stress_matrix.png
│   ├── fig7_long_horizon_drift.png
│   └── fig8_ablation_comparison.png
└── README.md               # Package documentation
```

---

## 4. Reproducibility

To re-run the complete benchmark and compile the manuscript:

```bash
# 1. Run all 8 experiments
python experiments/paper4/run_all_paper4.py

# 2. Run statistical analysis
python evaluation/paper4/statistical_analysis.py

# 3. Generate figures
python scripts/paper4/generate_figures.py

# 4. Generate IEEE Conference PDF
python scripts/paper4/generate_paper4_pdf.py
```

---

## 5. Academic Attribution & Disclaimer

*AstraHeal is an independent academic research project. Use of publicly available NASA battery repositories and telemetry schemas does not imply NASA endorsement, partnership, flight validation, or operational deployment.*
