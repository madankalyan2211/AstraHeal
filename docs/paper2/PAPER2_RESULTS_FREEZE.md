# AstraHeal Paper 2 — Formal Results Freeze Certificate

**Project**: AstraHeal — Paper 2  
**Title**: *Evidential Uncertainty-Aware Fault Diagnosis for Autonomous Spacecraft Health Management*  
**Date**: 2026  
**Status**: RESULTS STRICTLY FROZEN (Phase 11 Complete)

---

## 1. Research Freeze Declaration

All empirical experiments, baseline runs, noise sweeps, component ablations, and statistical evaluations for Paper 2 are hereby declared **STRICTLY FROZEN**. 

Under the absolute research freeze protocol:
- No thresholds will be re-tuned.
- No model parameters will be altered.
- No experiments will be selectively re-run to improve metrics.
- No unfavorable results (e.g. compound fault centroid cancellation, sensor polarity inversion failure) will be concealed or altered.
- All evaluation artifacts are immutably hashed with SHA-256 signatures below.

---

## 2. Evaluation Artifact Inventory & Cryptographic Hashes

| Artifact File Path | SHA-256 Checksum | Description |
|---|---|---|
| `evaluation/paper2/known_fault_results.json` | `d0e2e872e83827963481b1704d1126c402a11e475d5227d3815618d7b44dc648` | EXP-P2-01: Multiclass accuracy, macro-F1, confusion matrices, ECE, raw predictions across 5 models |
| `evaluation/paper2/uncertainty_results.json` | `0ce19597c3277bbe58b2eb57a7023276fbe1d96098ca2bf925c9480eb668516b` | EXP-P2-02: Epistemic vs aleatoric uncertainty separation across 7 operational regimes and noise levels |
| `evaluation/paper2/ood_results.json` | `e41c3bbf268588944863db880e4edfd646e16eae81b6d6ff6daf765e383ed0b9` | EXP-P2-03: AUROC, AUPRC, locked validation threshold $\tau = 0.0648$, FAR, FRR, category breakdown |
| `evaluation/paper2/noise_robustness_results.json` | `718e76951061ea8bc4fa60041c119f9e5008a9117092729d4cae11fe0878362c` | EXP-P2-04: Robustness trajectories across $\sigma \in [0.00, 0.25]$, false OOD alarm rates, ECE scaling |
| `evaluation/paper2/ablation_results.json` | `46ce971a027b256c99fa95749068a545caf7413b720ece6e7e2dbc41e5ed51e5` | EXP-P2-05: Quantitative ablations of Evidential, Mahalanobis, Priors, and Derivative features |
| `evaluation/paper2/statistical_results.json` | `090b7a4513101d4b42feb1484ab604fe4cafb5a63676cd7ac816f7829cdb9148` | Phase 9: Bootstrap 95% CIs, Wilcoxon signed-rank tests, Cohen's d, Holm-Bonferroni corrections |

---

## 3. Master Summary of Final Frozen Metrics

| Research Metric | Value | Verification Source |
|---|---|---|
| **Known-Mode Diagnosis Accuracy** | **95.42%** (95% CI: $[92.50\%, 97.92\%]$) | `known_fault_results.json` |
| **Known-Mode Macro-F1** | **0.9533** | `known_fault_results.json` |
| **Expected Calibration Error (ECE)** | **0.0094** ($< 1\%$ calibration error) | `known_fault_results.json` |
| **OOD Detection AUROC** | **0.9422** | `ood_results.json` |
| **OOD Detection AUPRC** | **0.9516** | `ood_results.json` |
| **Locked Threshold ($\tau_{\text{locked}}$)** | **0.0648** (95th percentile of validation ID) | `ood_results.json` |
| **True Positive OOD Catch Rate** | **76.67%** at $\tau = 0.0648$ (FPR = 4.50%) | `ood_results.json` |
| **Epistemic OOD Separation Ratio** | **10.94x** increase on novel vs clean known | `uncertainty_results.json` |
| **Noise vs Aleatoric Correlation** | $\rho = 0.2955$ ($p = 1.37 \times 10^{-17}$) | `uncertainty_results.json` |
| **Advantage over Rules across Noise** | $+0.3152$ Macro-F1 ($p = 5.77 \times 10^{-6}$) | `statistical_results.json` |

---

## 4. Documented Boundary Conditions & Negative Results

1. **Compound Fault Centroid Cancellation**: Simultaneous multi-fault occurrences (solar loss + thermal surge) pull feature points into intermediate metric valleys ($u_{\text{epistemic}} = 0.301 \pm 0.092$). While detected at $\tau = 0.0648$, compound faults do not trigger the extreme epistemic scores observed on novel single faults ($u_{\text{epistemic}} = 1.000$).
2. **Feature Transform Blind Spot**: Absolute value preprocessing of telemetry currents ($|I|$) renders polarity sign inversions undetectable ($u_{\text{epistemic}} = 0.057 < 0.0648$), leading to a 93.3% miss rate on instrumentation polarity flips.
3. **High Noise False Alarms**: When sensor noise exceeds $\sigma \ge 0.15$ (extreme sensor degradation), dimensional dispersion elevates Mahalanobis distance, causing a 35.3% to 64.0% false OOD rejection rate on genuine known faults.

---

## 5. Certification Signature

The experimental results for AstraHeal Paper 2 are certified complete, deterministic, reproducible, and locked against modification.
