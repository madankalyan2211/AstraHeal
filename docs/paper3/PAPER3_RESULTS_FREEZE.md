# AstraHeal Paper 3 — Results Freeze Certification

**Manuscript Title**: *AstraHeal: Deterministic Safety Gating for Uncertainty-Aware Autonomous Spacecraft Fault Recovery*  
**Freeze Status**: **LOCKED & IMMUTABLE**  
**Date**: September 2026  
**Auditor**: Reproducibility & Research Integrity Controller  

---

## 1. Frozen Experimental Inventory

All empirical evaluations have executed to completion with deterministic random seeds and zero runtime errors. The results recorded below are permanently frozen:

| Experiment ID | Seed | Scenarios Evaluated | Primary Verified Metric | Statistical Bound | Status |
|---|---|---|---|---|---|
| **P3-E1** | 42 | 500 proposals | 0 unsafe executions (0.0%) | McNemar $\chi^2 = 191.01, p = 1.92 \times 10^{-43}$ | **FROZEN** |
| **P3-E2** | 42 | 600 evaluations | 100.0% constraint accuracy | 6/6 constraints verified | **FROZEN** |
| **P3-E3** | 42 | 300 compound | 100.0% compound breach recall | 800/800 violations detected | **FROZEN** |
| **P3-E4** | 777 | 400 adversarial | 0 unsafe executions (0.0%) | 100.0% rejection rate | **FROZEN** |
| **P3-E5** | 999 | 804 points | 1 boundary switch / channel | 100.0% strict monotonicity | **FROZEN** |
| **P3-E6** | 42 | 300 scenarios | 0 hard safety bypasses | 100.0% Level 1 dominance | **FROZEN** |
| **P3-E7** | 101 | 150 dead-ends | 150 `NO_SAFE_ACTION` events | 0 forced unsafe actions | **FROZEN** |
| **P3-E8** | 2026 | 500 ablation | 0.0% unsafe exec (Gov) vs 100% (Rules) | Mean latency: $2.99\,\mu\text{s}$ | **FROZEN** |
| **Fail-Closed** | N/A | 7 edge cases | 7/7 rejections (100.0%) | 100.0% fail-closed rate | **FROZEN** |
| **Profiling** | N/A | 10,000 evals | $324,707.4$ evals / sec | Tail latency p95: $3.13\,\mu\text{s}$ | **FROZEN** |

---

## 2. Frozen Evaluation Artifact Hashes

The following artifact files in `evaluation/paper3/` constitute the official immutable benchmark:
- `e1_baseline_safety.json`
- `e2_constraint_coverage.json`
- `e3_compound_constraints.json`
- `e4_unsafe_proposals.json`
- `e5_boundary_testing.json`
- `e6_communication_safety.json`
- `e7_no_safe_action.json`
- `e8_ablation.json`
- `fail_closed_results.json`
- `overhead_results.json`
- `statistical_results.json`
- `experiment_manifest.json`

Zero post-hoc adjustments or selective filtering may be applied.
