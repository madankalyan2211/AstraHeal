# AstraHeal Paper 3 — Complete Research Release Manifest

**Manuscript Title**: *AstraHeal: Deterministic Safety Gating for Uncertainty-Aware Autonomous Spacecraft Fault Recovery*  
**Release Version**: `Paper 3 — Research Release v1.0`  
**Author**: Madan Kalyan Thambisetty (Autonomous Systems & Aerospace Software Research)  
**Date**: September 2026  
**License**: MIT License / Open Science Public Domain  
**Code Repository**: [https://github.com/madankalyan2211/AstraHeal](https://github.com/madankalyan2211/AstraHeal)  

---

## 1. Research Identity

* **Central Research Question**:  
  *"Can a deterministic safety governor reliably prevent unsafe autonomous spacecraft recovery actions proposed by an AI-based fault-management system from reaching execution, including under uncertain, incorrect, or deliberately unsafe upstream proposals?"*
* **Primary Scientific Contribution**:  
  A deterministic, fail-closed runtime safety governor intercepting upstream AI recovery proposals and verifying them against immutable physical spacecraft invariants ($T_{\text{batt}} \le 46^\circ\text{C}$, $V_{\text{bus}} \ge 22\text{V}$, $I_{\text{batt}} \le 40\text{A}$, $\text{SoC} \ge 15\%$, $P \le 880\text{W}$) over projected counterfactual horizons, providing an independent safety barrier that decouples action admissibility from AI confidence and safely converges to `NO_SAFE_ACTION_AVAILABLE` during physical unrecoverability.
* **Relationship to AstraHeal Papers 1 and 2**:  
  - **Paper 1**: Counterfactual lookahead planning across 15 LEO simulation benchmarks.
  - **Paper 2**: Evidential Dirichlet Bayesian diagnosis isolating epistemic and aleatoric uncertainty.
  - **Paper 3**: The authoritative runtime safety barrier between AI proposals and command execution.

---

## 2. Verified Main Benchmark Metrics

| Metric Category | Metric Name | Value | Statistical Bound / Test |
|---|---|---|---|
| **Unsafe Action Gating** | Unsafe Action Execution Rate | **0.00%** (0 / 1,519 proposals) | Clopper-Pearson 95% Bound: $< 0.1970\%$ |
| **Unsafe Action Gating** | Unsafe Action Rejection Rate | **100.0%** (1,519 / 1,519 proposals) | Wilson 95% CI: $[0.00\%, 0.25\%]$ |
| **Baseline Enforcement** | Governed vs Ungoverned Execution | **0.0%** vs **100.0%** | McNemar $\chi^2 = 191.01, p = 1.92 \times 10^{-43}$ |
| **Baseline Enforcement** | Cohen's Effect Size | **$h = 3.1416$** ($\pi$) | Exceptionally Large Effect |
| **Constraint Coverage** | 6 Hard Physical Constraints | **100.0%** (600 / 600 tests) | Verified across 4 canonical regimes |
| **Compound Breaches** | Concurrent Multi-Violation Recall | **100.0%** (800 / 800 breaches) | Zero premature short-circuiting |
| **Adversarial Resilience** | Deceptive / Overconfident AI Proposals | **100.0% Rejection** (400 / 400) | 0 Executions across 5 attack vectors |
| **Boundary Precision** | Continuous Parameter Sweeps | **100.0% Monotonic** (1 switch/ch) | 201 points/channel (804 total) |
| **Safety Dominance** | Hard Safety Bypasses | **0 bypasses** (0 / 300 scenarios) | Verified in Contact & Blackout |
| **Safe Failure Protocol** | `NO_SAFE_ACTION_AVAILABLE` Convergence | **100.0%** (150 / 150 scenarios) | 0 forced unsafe actions (750 candidates) |
| **Fail-Closed Robustness**| IEEE 754 NaN / Inf Telemetry Rejection | **100.0%** (7 / 7 edge cases) | Fail-closed validator |
| **Avionics Overhead** | Mean Evaluation Latency | **$2.99\,\mu\text{s}$** ($0.0030\,\text{ms}$) | Throughput: $>324,000$ evals/sec |

---

## 3. Evaluated Experiments & Code Artifacts

* **Master Runner**: `experiments/paper3/run_all_paper3.py`
* **Experiment 1 (Baseline Enforcement)**: `experiments/paper3/01_baseline_safety_enforcement.py`
* **Experiment 2 (Constraint Coverage)**: `experiments/paper3/02_constraint_coverage.py`
* **Experiment 3 (Compound Violations)**: `experiments/paper3/03_compound_constraint_violations.py`
* **Experiment 4 (Adversarial AI Proposals)**: `experiments/paper3/04_unsafe_ai_proposals.py`
* **Experiment 5 (Continuous Boundary Sweeps)**: `experiments/paper3/05_boundary_testing.py`
* **Experiment 6 (Communication Arbitration)**: `experiments/paper3/06_communication_aware_safety.py`
* **Experiment 7 (No-Safe-Action Dead-Ends)**: `experiments/paper3/07_no_safe_action.py`
* **Experiment 8 (Ablation, Fail-Closed, Overhead)**: `experiments/paper3/08_safety_governor_ablation.py`
* **Statistical Significance Engine**: `experiments/paper3/compute_statistics.py`
* **Paper 3 Test Suite**: `tests/paper3/test_paper3_pipeline.py` (10 / 10 tests passing, 51/51 overall)

---

## 4. Frozen Evaluation JSON Artifacts

* `evaluation/paper3/e1_baseline_safety.json`
* `evaluation/paper3/e2_constraint_coverage.json`
* `evaluation/paper3/e3_compound_constraints.json`
* `evaluation/paper3/e4_unsafe_proposals.json`
* `evaluation/paper3/e5_boundary_testing.json`
* `evaluation/paper3/e6_communication_safety.json`
* `evaluation/paper3/e7_no_safe_action.json`
* `evaluation/paper3/e8_ablation.json`
* `evaluation/paper3/fail_closed_results.json`
* `evaluation/paper3/overhead_results.json`
* `evaluation/paper3/statistical_results.json`
* `evaluation/paper3/experiment_manifest.json`

---

## 5. Publication Figures

* `docs/paper3/figures/fig1_safety_enforcement_comparison.png`: Action execution comparison (Ungoverned vs Governed AI)
* `docs/paper3/figures/fig2_constraint_coverage_matrix.png`: Verification accuracy across 6 hard constraints
* `docs/paper3/figures/fig3_compound_violations_breakdown.png`: Concurrent violation detection recall across double, triple, and quad breaches
* `docs/paper3/figures/fig4_adversarial_injection_robustness.png`: Resilience under 5 adversarial proposal attack vectors
* `docs/paper3/figures/fig5_boundary_testing_sweeps.png`: 4-panel fine sweep across continuous constraint margins
* `docs/paper3/figures/fig6_communication_arbitration_hierarchy.png`: Grouped bar chart demonstrating Level 1 safety dominance
* `docs/paper3/figures/fig7_ablation_and_latency.png`: 2-panel figure showing unsafe execution delta and microsecond latency profile
* `docs/paper3/figures/fig8_no_safe_action_convergence.png`: Verification of non-forcing safe failure convergence

---

## 6. Suggested Citation

### BibTeX Format
```bibtex
@article{astraheal2026paper3,
  title     = {AstraHeal: Deterministic Safety Gating for Uncertainty-Aware Autonomous Spacecraft Fault Recovery},
  author    = {AstraHeal Research Group and Thambisetty, Madan},
  journal   = {AstraHeal Research Series},
  volume    = {3},
  year      = {2026},
  url       = {https://github.com/madankalyan2211/AstraHeal}
}
```

### IEEE Format
```text
M. Thambisetty, "AstraHeal: Deterministic Safety Gating for Uncertainty-Aware Autonomous Spacecraft Fault Recovery," AstraHeal Research Series, vol. 3, 2026.
```
