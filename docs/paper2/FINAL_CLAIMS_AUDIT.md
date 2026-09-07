# AstraHeal Paper 2 — Final Scientific Claims Audit

**Project**: AstraHeal — Paper 2  
**Document**: Peer-Review Scientific Claims Audit and Epistemic Honesty Verification  
**Date**: 2026  
**Status**: Formally Certified (Phase 12 Complete)

---

## 1. Audit Taxonomy

Every scientific claim made in the manuscript, documentation, and abstracts of Paper 2 is audited and assigned one of three verdicts based strictly on reproducible empirical evidence in `evaluation/paper2/`:
- **SUPPORTED**: Directly verified by reproducible quantitative benchmarks, statistical tests ($p < 0.05$), and artifact traces.
- **PARTIALLY SUPPORTED**: Empirical evidence confirms the core mechanism, but with documented physical boundary conditions or reduced performance on specific edge cases.
- **NOT SUPPORTED**: The empirical data contradicts the claim, or the experiment failed to validate the theoretical expectation.

---

## 2. Systematic Claims Audit Table

| # | Scientific Claim | Evaluated Evidence | Verdict | Evidence Trace |
|---|---|---|---|---|
| **1** | Evidential engine accurately diagnoses known spacecraft EPS failure modes ($\text{Macro-F1} \ge 0.90$). | Achieved **0.9542 accuracy** and **0.9533 Macro-F1** across 6 classes on held-out test frames ($N = 240$). Bootstrap 95% CI: $[0.9250, 0.9792]$. | **SUPPORTED** | `known_fault_results.json` |
| **2** | Evidential Dirichlet engine achieves superior calibration compared to rule-based baselines. | ECE was **0.0094** for Evidential vs. **0.2548** for Physics Rules (a 27x improvement in probability calibration). | **SUPPORTED** | `known_fault_results.json` |
| **3** | Observation noise and distributional novelty occupy separable uncertainty axes. | Aleatoric uncertainty correlated with noise ($\rho = 0.2955, p = 1.37 \times 10^{-17}$), and novel catastrophic faults produced a 10.94x surge in epistemic uncertainty. | **SUPPORTED** | `uncertainty_results.json` |
| **4** | Compound concurrent faults trigger high epistemic uncertainty. | Compound faults produced $u_{\text{epistemic}} = 0.301 \pm 0.092$. While above locked $\tau = 0.0648$, centroid interference kept it well below novel single faults ($1.000$). | **PARTIALLY SUPPORTED** | `uncertainty_results.json` |
| **5** | Epistemic gating reliably detects out-of-distribution (OOD) space anomalies ($\text{AUROC} \ge 0.90$). | Achieved **0.9422 AUROC** and **0.9516 AUPRC** across 600 OOD frames vs. 600 ID frames, catching 100% of catastrophic short and cryogenic freeze faults. | **SUPPORTED** | `ood_results.json` |
| **6** | Epistemic gating detects arbitrary sensor failure modes. | Detected only 6.7% of current sensor polarity reversals due to upstream $|I|$ absolute value invariance. | **NOT SUPPORTED** | `ood_results.json` |
| **7** | Model maintains diagnostic integrity under flight-representative telemetry noise ($\sigma \le 0.05$). | Macro-F1 was 0.8308 at $\sigma = 0.05$ with false OOD alarm rate bounded at 7.7%, significantly outperforming rules ($F1 = 0.5072, p = 5.77 \times 10^{-6}$). | **SUPPORTED** | `noise_robustness_results.json` |
| **8** | Mahalanobis covariance metric is essential for detecting low-magnitude impedance spikes. | Ablating Mahalanobis in favor of Euclidean distance collapsed $R_{\text{int}}$ spike detection from $F1 = 1.0000$ to $0.0000$. | **SUPPORTED** | `ablation_results.json` |
| **9** | Dirichlet evidential parameterization outperforms standard softmax confidence for OOD detection. | Replacing Dirichlet evidence with Softmax confidence inversion dropped OOD AUROC from 0.8692 to 0.7895. | **SUPPORTED** | `ablation_results.json` |
| **10**| The diagnostic framework guarantees complete mission survival under arbitrary anomalies. | Fails under irreversible hardware destruction; diagnostic autonomy cannot prevent loss when exothermic heat exceeds thermal radiator capacity. | **NOT SUPPORTED** (Explicit non-claim) | AstraHeal v1.0 `14_controlled_results.json` |

---

## 3. Explicit Boundaries: What Paper 2 Demonstrates vs. Does Not Demonstrate

### **WHAT PAPER 2 DEMONSTRATES:**
1. **Evidential Dirichlet Formulations Provide Calibrated Spacecraft Fault Diagnosis**: Achieves 0.9533 Macro-F1 with sub-1% Expected Calibration Error ($ECE = 0.0094$) on 28V spacecraft power system telemetry.
2. **Selective Uncertainty Scaling Under Noise vs. Novelty**: Aleatoric uncertainty scales monotonically with sensor variance, while epistemic uncertainty remains bounded below false-alarm thresholds under nominal noise ($\sigma \le 0.05$) and surges by $10.94\times$ on novel operational manifolds.
3. **Superiority Over Maximum Softmax Probability (MSP)**: Evidential epistemic gating achieves 0.9422 AUROC on OOD anomalies, whereas standard Softmax inversion collapses to 0.4313 AUROC due to extreme overconfidence on out-of-distribution inputs.
4. **Physical Essentiality of Mahalanobis Covariance**: In multivariate space telemetry where parameter scales vary from milliohms to hundreds of watts, metric covariance scaling is strictly necessary—without it, battery impedance degradation cannot be detected ($F1 = 0.0000$).

---

### **WHAT PAPER 2 DOES NOT DEMONSTRATE:**
1. **No Operational Flight Validation**: The algorithms have been validated in numerical simulation and on empirical NASA PCoE battery aging archives, but have not flown in Low Earth Orbit.
2. **No NASA Partnership or Endorsement**: AstraHeal is an independent academic research project; it has no formal affiliation, agency contract, or deployment partnership with NASA.
3. **No Omniscient OOD Detection Across Invariant Transforms**: Upstream feature engineering that enforces sign-invariance ($|I|$) creates structural blind spots that mask sensor polarity reversals from metric-based anomaly detectors.
4. **No Immunity to Severe Multi-Fault Cancellation**: Simultaneous compound faults can generate intermediate distance metrics that do not reach the extreme epistemic levels of single-point catastrophic shifts.
5. **No Survival When Hardware Physics Render Survival Impossible**: Software diagnostics cannot prevent vehicle loss when physical thermal dissipation limits ($Q_{\text{exo}} > 65\text{W}$) are breached.

---

## 4. Banned Phrase Audit

The following overclaiming phrases are strictly forbidden and confirmed absent from all Paper 2 claims:
- "guarantees"
- "solves autonomous FDIR"
- "flight-ready"
- "operationally validated"
- "NASA validated"
- "perfect OOD detection"
