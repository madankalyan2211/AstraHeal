# AstraHeal — Autonomous Self-Healing Spacecraft Intelligence Platform

[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.22233081.svg)](https://doi.org/10.5281/zenodo.22233081)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Python: 3.12](https://img.shields.io/badge/Python-3.12-blue.svg)](https://www.python.org/)
[![Status: Research Series](https://img.shields.io/badge/Status-Research%20Series%20(Papers%201%20to%204)-brightgreen.svg)](paper4/README.md)
[![Tests: 51 Passed](https://img.shields.io/badge/Tests-51%20Passed-success.svg)](tests/)
[![Reproducibility: 36 Experiments](https://img.shields.io/badge/Reproducibility-15%20+%205%20+%208%20+%208%20Experiments-success.svg)](paper4/README.md)

> **Important Research Disclaimer**:  
> **AstraHeal is an independent academic research simulation platform and has NOT been validated for flight or real spacecraft operations. This project does NOT claim NASA partnership, NASA endorsement, NASA approval, or operational spaceflight readiness.** Public NASA PCoE battery datasets are utilized strictly under open scientific research terms with documented provenance.

---

## 1. Project Overview

**AstraHeal** is an open-source, research-grade simulation and autonomy platform for autonomous, safety-governed spacecraft fault recovery during communication blackouts. When satellites experience critical subsystem anomalies during orbital occultation or deep-space communication delays, AstraHeal integrates:
1. **Dirichlet evidential Bayesian fault diagnosis** separating Epistemic ($u_{\text{epistemic}}$) from Aleatoric ($u_{\text{aleatoric}}$) uncertainty.
2. **Zero-mutation digital twin counterfactual lookahead simulation** (3000s horizon).
3. **A deterministic Safety Governor** enforcing 5 immutable physical invariants ($T_{\text{batt}} \le 46^\circ\text{C}$, $V_{\text{bus}} \ge 22\text{V}$, $|I_{\text{batt}}| \le 40\text{A}$, $\text{SoC} \ge 15\%$, $P \le 880\text{W}$).
4. **Communication-aware autonomy arbitration** between immediate onboard recovery and ground operator handoff.
5. **Multi-cycle closed-loop validation** under parameter perturbations ($\pm 20\%$) and sensor noise sweeps.

---

## 2. Integrated 5-Stage System Architecture

```
Telemetry Stream  ──►  Causal Feature Extraction (dV/dt, dT/dt, R_int)
                                │
                                ▼
                       Ensemble Anomaly Detector (AUROC: 0.974)
                                │
                                ▼
                   Evidential Dirichlet Diagnosis
                    ├── Aleatoric Uncertainty (Entropy / Noise)
                    └── Epistemic Uncertainty (OOD Distance)
                                │
                 ┌──────────────┴──────────────┐
                 ▼                             ▼
       In-Distribution Fault           Novel OOD Fault (u_ep >= 0.50)
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
    (5 Hard Physical Boundary Invariants)
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

- **Deterministic Safety Assurance**: **0.00%** executed unsafe actions and **0** Safety Governor bypasses across 40,711 candidate evaluations ($p < 10^{-43}$, Clopper-Pearson 95% bound $< 0.197\%$).
- **Out-of-Distribution Gating**: **100%** of compound novel faults trigger $u_{\text{epistemic}} \ge 0.79 \to \text{UNKNOWN\_FAILURE}$, inhibiting unverified aggressive actuations.
- **Counterfactual Trajectory Accuracy**: Under unmodelled physical parameter perturbations (radiator coupling degradation, thermal mass shifts, harness resistance):
  - Battery Temperature MAE: **0.642 °C**
  - Bus Regulated Voltage MAE: **0.415 V**
  - State of Charge (SoC) MAE: **0.0003 (0.03%)**
  - Top-2 Action Selection Accuracy: **95.0%** (Top-1: **55.0%**).
- **Mission Utility Preservation**: Retains **100% (574.0 Wh)** science observation energy in recoverable anomalies where naive blind Safe Mode forces total shutdown (0% payload).
- **Multi-Cycle Stability**: **100%** mission survival maintained across repeated anomaly cycles ($k = 1 \dots 10$) and 1,320 closed-loop multi-orbit runs.
- **Physical Boundary Documented**: Software autonomy cannot prevent physical thermal runaway when internal exothermic heat generation exceeds radiator dissipation area ($Q_{\text{exo}} > 65\text{W}$).

---

## 4. The 4-Part Scientific Research Series

All four papers are fully documented with complete IEEE (`IEEEtran`) and Springer (`llncs`) publication packages, BibTeX references, high-DPI figures, and reproducible execution runners:

### 📄 Paper 1 (PLAN): Platform & Counterfactual Planning
- **Title**: *AstraHeal: Uncertainty-Aware Counterfactual Planning for Autonomous Spacecraft Fault Recovery*
- **Author**: Madan Thambisetty
- **Focus**: Zero-mutation digital twin counterfactual lookahead, deterministic Safety Governor, communication blackout arbitration.
- **DOI**: [10.5281/zenodo.22233081](https://doi.org/10.5281/zenodo.22233081)
- **Manuscript Assets**: [LaTeX Source](docs/paper/latex/) | [BibTeX References](docs/paper/latex/references.bib) | [Overleaf Package (.zip)](docs/paper/astraheal_latex.zip)

### 📄 Paper 2 (UNDERSTAND): Evidential Fault Diagnosis & Uncertainty
- **Title**: *Evidential Uncertainty-Aware Fault Diagnosis for Autonomous Spacecraft Health Management*
- **Author**: Madan Thambisetty
- **Focus**: Dirichlet evidential learning, closed-form epistemic/aleatoric uncertainty isolation, out-of-distribution (OOD) failure detection, noise sweeps.
- **Key Metrics**: Known-Fault Macro-F1: **0.9533** | ECE: **0.0094** | OOD AUROC: **0.9422** | AUPRC: **0.9516**
- **Manuscript Assets**: [LaTeX Source](docs/paper2/latex/) | [BibTeX References](docs/paper2/latex/references.bib) | [Overleaf Package (.zip)](docs/paper2/latex/astraheal_paper2_latex.zip)

### 📄 Paper 3 (CONSTRAIN): Deterministic Safety Gating & Runtime Assurance
- **Title**: *AstraHeal: Deterministic Safety Gating for Uncertainty-Aware Autonomous Spacecraft Fault Recovery*
- **Author**: Madan Thambisetty
- **Focus**: Independent runtime Safety Governor, 5 hard physical invariants, adversarial proposal injection, fail-closed handling, safe failure convergence.
- **Key Metrics**: Unsafe Action Execution: **0.00%** (0 / 1,519 proposals) | McNemar test: $p = 1.92 \times 10^{-43}$ | Latency: **$2.99\,\mu\text{s}$**
- **Manuscript Assets**: [LaTeX Source](docs/paper3/latex/) | [BibTeX References](docs/paper3/latex/references.bib) | [Overleaf Package (.zip)](docs/paper3/latex/astraheal_paper3_latex.zip)

### 📄 Paper 4 (VALIDATE): Multi-Cycle Robustness Under Perturbations
- **Title**: *AstraHeal: Robust Multi-Cycle Autonomous Fault Recovery Under Perturbed Spacecraft Conditions*
- **Author**: Madan Thambisetty
- **Focus**: Closed-loop capstone robustness across 1,320 missions, sequential fault cascades, $\pm 20\%$ parameter perturbations ($C_{\text{th}}, h_{\text{rad}}, R_0, \eta_{\text{sa}}$), telemetry noise sweeps.
- **Key Metrics**: 1,320 missions | 18,000+ recovery cycles | 100% multi-cycle survival | Ablation utility drop: **63.05%** ($p = 3.10 \times 10^{-26}$)
- **Manuscript Assets**: [LaTeX Source](paper4/) | [BibTeX References](paper4/references.bib) | [Documentation Suite](docs/paper4/)

---

## 5. Reproducibility & Test Execution

```bash
# 1. Install dependencies
pip install pytest numpy pandas scipy scikit-learn pydantic matplotlib pyyaml

# 2. Run full 51-test unit and pipeline suite:
python3 -m pytest tests/ -v

# 3. Execute Paper 1 master reproducibility pipeline (Experiments 01–15):
python3 run_all_experiments.py

# 4. Execute Paper 2 master benchmark suite (EXP-P2-01 through 05):
python3 experiments/paper2/run_all_paper2.py

# 5. Execute Paper 3 master safety governor benchmark (EXP-P3-01 through 08):
python3 experiments/paper3/run_all_paper3.py

# 6. Execute Paper 4 capstone validation suite:
python3 experiments/paper4/run_all_paper4.py

# 7. Run Academic Originality & Plagiarism Audit across all 4 papers:
python3 scripts/audit_all_4_papers_plagiarism.py

# 8. Launch interactive mission telemetry dashboard:
python3 -m http.server 8000 --directory dashboard
# Open http://localhost:8000 in your web browser
```

---

## 6. Citations

If you use AstraHeal in your research, software, or mission design, please cite the corresponding publication:

```bibtex
@article{thambisetty2026astraheal_p1,
  author    = {Thambisetty, Madan},
  title     = {AstraHeal: Uncertainty-Aware Counterfactual Planning for Autonomous Spacecraft Fault Recovery},
  journal   = {Zenodo},
  year      = {2026},
  month     = {sep},
  doi       = {10.5281/zenodo.22233081},
  url       = {https://doi.org/10.5281/zenodo.22233081}
}

@article{thambisetty2026astraheal_p2,
  author    = {Thambisetty, Madan},
  title     = {Evidential Uncertainty-Aware Fault Diagnosis for Autonomous Spacecraft Health Management},
  journal   = {AstraHeal Research Series},
  volume    = {2},
  year      = {2026},
  url       = {https://github.com/madankalyan2211/AstraHeal}
}

@article{thambisetty2026astraheal_p3,
  author    = {Thambisetty, Madan},
  title     = {AstraHeal: Deterministic Safety Gating for Uncertainty-Aware Autonomous Spacecraft Fault Recovery},
  journal   = {AstraHeal Research Series},
  volume    = {3},
  year      = {2026},
  url       = {https://github.com/madankalyan2211/AstraHeal}
}

@article{thambisetty2026astraheal_p4,
  author    = {Thambisetty, Madan},
  title     = {AstraHeal: Robust Multi-Cycle Autonomous Fault Recovery Under Perturbed Spacecraft Conditions},
  journal   = {AstraHeal Research Series},
  volume    = {4},
  year      = {2026},
  url       = {https://github.com/madankalyan2211/AstraHeal}
}
```

---

## 7. License

This project is open-source software licensed under the [MIT License](LICENSE).
