# AstraHeal Paper 3 — Complete Result Provenance & Traceability Ledger

**Manuscript Title**: *AstraHeal: Deterministic Safety Gating for Uncertainty-Aware Autonomous Spacecraft Fault Recovery*  
**Standard**: Cryptographic & File-Level Scientific Metric Provenance  
**Date**: September 2026  

---

## 1. Provenance Ledger Table

Every metric and numerical finding reported in the Paper 3 manuscript, abstract, tables, and figures traces directly to a frozen JSON evaluation artifact:

| Metric / Claim | Numerical Value | Experiment Source | Artifact Path | Artifact Key / Field | Figure / Table | Manuscript Section |
|---|---|---|---|---|---|---|
| **E1 Scenarios Count** | 500 scenarios | P3-E1 | `evaluation/paper3/e1_baseline_safety.json` | `num_scenarios` | Table 3 | Sec. 18 |
| **Ungoverned Unsafe Executions** | 193 / 193 (100.0%) | P3-E1 | `evaluation/paper3/e1_baseline_safety.json` | `system_a_ungoverned.unsafe_actions_executed` | Fig. 1, Tab. 3 | Sec. 18 |
| **Governed Unsafe Executions** | 0 / 193 (0.00%) | P3-E1 | `evaluation/paper3/e1_baseline_safety.json` | `system_b_governed.unsafe_actions_executed` | Fig. 1, Tab. 3 | Sec. 18 |
| **Governed Safe Accepted** | 307 / 307 (100.0%) | P3-E1 | `evaluation/paper3/e1_baseline_safety.json` | `system_b_governed.safe_actions_accepted` | Fig. 1, Tab. 3 | Sec. 18 |
| **Individual Constraint Accuracy** | 100.0% (600/600) | P3-E2 | `evaluation/paper3/e2_constraint_coverage.json` | `coverage_summary.*.accuracy` | Fig. 2, Tab. 4 | Sec. 19 |
| **Compound Breaches Tested** | 300 proposals | P3-E3 | `evaluation/paper3/e3_compound_constraints.json` | `total_scenarios` | Fig. 3, Tab. 3 | Sec. 21 |
| **Compound Rejection Rate** | 100.0% (300/300) | P3-E3 | `evaluation/paper3/e3_compound_constraints.json` | `compound_rejection_rate` | Fig. 3, Tab. 3 | Sec. 21 |
| **Concurrent Violation Recall** | 100.0% (800/800) | P3-E3 | `evaluation/paper3/e3_compound_constraints.json` | `compound_detection_recall` | Fig. 3, Tab. 3 | Sec. 21 |
| **Adversarial Injected Count** | 400 proposals | P3-E4 | `evaluation/paper3/e4_unsafe_proposals.json` | `total_proposals` | Fig. 4, Tab. 5 | Sec. 19 |
| **Adversarial Rejection Rate** | 100.0% (400/400) | P3-E4 | `evaluation/paper3/e4_unsafe_proposals.json` | `overall_rejection_rate` | Fig. 4, Tab. 5 | Sec. 19 |
| **Adversarial Executions** | 0 (0.00%) | P3-E4 | `evaluation/paper3/e4_unsafe_proposals.json` | `total_executed` | Fig. 4, Tab. 5 | Sec. 19 |
| **Boundary Monotonicity** | 1 switch / channel | P3-E5 | `evaluation/paper3/e5_boundary_testing.json` | `boundary_summary.*.is_strictly_monotonic` | Fig. 5, Tab. 6 | Sec. 20 |
| **Communication Bypass Count** | 0 bypasses | P3-E6 | `evaluation/paper3/e6_communication_safety.json` | `hard_safety_bypasses` | Fig. 6, Tab. 3 | Sec. 22 |
| **No-Safe-Action Scenarios** | 150 scenarios | P3-E7 | `evaluation/paper3/e7_no_safe_action.json` | `num_scenarios` | Fig. 8, Tab. 3 | Sec. 23 |
| **Candidates Evaluated in Dead-Ends** | 750 candidates | P3-E7 | `evaluation/paper3/e7_no_safe_action.json` | `total_candidates_evaluated` | Fig. 8, Tab. 3 | Sec. 23 |
| **Dead-End Convergence Rate** | 100.0% (150/150) | P3-E7 | `evaluation/paper3/e7_no_safe_action.json` | `safe_failure_convergence_rate` | Fig. 8, Tab. 3 | Sec. 23 |
| **Forced Unsafe Actions** | 0 (0.00%) | P3-E7 | `evaluation/paper3/e7_no_safe_action.json` | `forced_unsafe_executions` | Fig. 8, Tab. 3 | Sec. 23 |
| **Fail-Closed Rejection Rate** | 100.0% (7/7) | P3-E8 | `evaluation/paper3/fail_closed_results.json` | `fail_closed_rate` | Tab. 8 | Sec. 14 |
| **Mean Evaluation Latency** | 2.99 µs | P3-E8 | `evaluation/paper3/overhead_results.json` | `latency_mean_microseconds` | Fig. 7, Tab. 9 | Sec. 25 |
| **95th Percentile Latency** | 3.13 µs | P3-E8 | `evaluation/paper3/overhead_results.json` | `latency_p95_microseconds` | Fig. 7, Tab. 9 | Sec. 25 |
| **Throughput** | 324,707.4 evals/s | P3-E8 | `evaluation/paper3/overhead_results.json` | `throughput_evals_per_sec` | Fig. 7, Tab. 9 | Sec. 25 |
| **Total Suite Unsafe Proposals** | 1,519 proposals | Stats | `evaluation/paper3/statistical_results.json` | `total_unsafe_proposals_tested_across_suite` | Tab. 3 | Sec. 18 |
| **Clopper-Pearson 95% Bound** | < 0.1970% | Stats | `evaluation/paper3/statistical_results.json` | `clopper_pearson_exact_95_upper_bound` | Text | Sec. 18, 22 |
| **McNemar Chi2 Statistic** | 191.01 (p = 1.92e-43) | Stats | `evaluation/paper3/statistical_results.json` | `mcnemar_test_h1.chi2_statistic` | Text | Sec. 18 |
| **Cohen's h Effect Size** | 3.1416 | Stats | `evaluation/paper3/statistical_results.json` | `mcnemar_test_h1.cohens_h_effect_size` | Text | Sec. 18 |

---

## 2. Integrity Certification
Zero values in the paper are estimated, extrapolated, or transcribed without direct programmatic generation and JSON provenance.
