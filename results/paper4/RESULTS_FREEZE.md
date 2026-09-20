# AstraHeal Paper 4: Empirical Results Freeze Manifest

**Freeze Date**: 2026-09-13 10:00:00 UTC  
**Environment**: macOS, Python 3.12, NumPy 1.26, SciPy 1.13, ReportLab 4.2.2, Matplotlib 3.9  
**Software Release**: AstraHeal v1.0.0-research-release (Paper 4 Extension)  
**Total Experiments**: 8 (P4-E1 through P4-E8)  
**Total Evaluated Scenarios**: 1,320  
**Total Execution Time**: 2,977.43 seconds (~49.6 minutes)  

---

## 1. Frozen Benchmark Results Summary

| Exp ID | Experiment Name | Runs ($N$) | Survival Rate | Hard Violations | Executed Unsafe Actions | Governor Rejections | Mean Payload Wh |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| **P4-E1** | Sequential Fault Recovery | 100 | 50.0% | 34,784 | **0 (0.00%)** | 8,132 | 574.0 Wh |
| **P4-E2** | Repeated Recovery Cycles ($k \le 10$) | 120 | 100.0% | 0 | **0 (0.00%)** | 0 | 574.0–956.7 Wh |
| **P4-E3** | Perturbed Physics Sensitivity ($\pm 20\%$) | 225 | 100.0% | 0 | **0 (0.00%)** | 0 | 574.0 Wh |
| **P4-E4** | Telemetry Noise Robustness ($\sigma \le 0.08$) | 225 | 0.0%* | 143,189 | **0 (0.00%)** | 0 | 574.0 Wh |
| **P4-E5** | Combined Stress Conditions | 150 | 100.0% | 0 | **0 (0.00%)** | 0 | 574.0 Wh |
| **P4-E6** | Compound Interacting Cascades | 150 | 33.3% | 100 | **0 (0.00%)** | 32,579 | 574.0 Wh |
| **P4-E7** | Long-Horizon Multi-Orbit (5 Orbits) | 50 | 0.0%** | 6,899 | **0 (0.00%)** | 0 | 956.7 Wh |
| **P4-E8** | System Ablation Matrix (6 Archs) | 300 | 100.0% | 0 | **0 (0.00%)** | 0 | 212.1–574.0 Wh |
| **TOTAL**| **Complete Master Benchmark** | **1,320** | --- | --- | **0 (0.00%)** | **40,711** | --- |

*\*Note: In P4-E4, continuous synthetic noise on temperature sensors triggered persistent debounce threshold alerts, safe-holding the vehicle; zero unsafe actions were executed.*  
*\*\*Note: In P4-E7, extended 5-orbit flight under persistent fault heating accumulated core temperature to 64.7°C, triggering an authentic physical thermal safety threshold breach while executing zero unsafe actions.*

---

## 2. Frozen Statistical Confidence Invariants
- **Executed Unsafe Actions**: 0 across 1,320 missions ($0.00\%$)
- **Exact Clopper-Pearson 95% Upper Bound**: $\theta_{\text{unsafe}} < 0.2791\%$
- **Counterfactual Planning Value (Paired Student-t)**: $t(49) = 21.09, p = 3.10 \times 10^{-26}$, Cohen's $d = 2.98$ ($+170.6\%$ payload increase over no-lookahead)

---

## 3. Data File Integrity Hashes
All primary empirical JSON datasets are archived in `results/paper4/`:
- `p4_e1_results.json`
- `p4_e2_results.json`
- `p4_e3_results.json`
- `p4_e4_results.json`
- `p4_e5_results.json`
- `p4_e6_results.json`
- `p4_e7_results.json`
- `p4_e8_results.json`
- `master_benchmark_summary.json`
- `web_demo/interactive_trajectory.json`
