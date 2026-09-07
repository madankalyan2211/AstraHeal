# AstraHeal Paper 2 — Complete Result Provenance Map

**Project**: AstraHeal — Paper 2  
**Date**: 2026  
**Status**: Formally Certified (Phase 10 Complete)

---

## 1. Provenance Integrity Protocol

Every quantitative claim, metric, and finding presented in Paper 2 originates directly from a frozen, reproducible execution artifact in `evaluation/paper2/`. This bidirectional provenance map guarantees 100% auditable traceability:

$$\text{CLAIM} \longrightarrow \text{EXPERIMENT SCRIPT} \longrightarrow \text{CONFIGURATION} \longrightarrow \text{RAW JSON ARTIFACT} \longrightarrow \text{FIGURE / TABLE}$$

---

## 2. Master Claim-to-Artifact Provenance Table

| Claim ID | Quantitative Statement | Experiment File | Configuration | Raw JSON Artifact & Key | Target Presentation |
|---|---|---|---|---|---|
| **C-01** | Evidential Engine achieves 0.9542 accuracy and 0.9533 Macro-F1 on held-out known faults | `experiments/paper2/01_known_fault_diagnosis.py` | `configs/paper2/paper2_config.yaml` (`exp01_known_faults`) | `evaluation/paper2/known_fault_results.json` -> `models.EvidentialDirichlet.macro_f1` (0.9533) | Table 1, Manuscript Section 17 |
| **C-02** | Evidential Expected Calibration Error (ECE) is 0.0094 | `experiments/paper2/01_known_fault_diagnosis.py` | `configs/paper2/paper2_config.yaml` (`exp01_known_faults`) | `evaluation/paper2/known_fault_results.json` -> `models.EvidentialDirichlet.ece` (0.0094) | Table 1, Fig. 2 (`fig2_calibration_curves.png`) |
| **C-03** | Bootstrap 95% Confidence Interval on Evidential accuracy is [0.9250, 0.9792] | `experiments/paper2/compute_statistics.py` | 1,000 bootstrap iterations, Seed 42 | `evaluation/paper2/statistical_results.json` -> `bootstrap_confidence_intervals_95.EvidentialDirichlet.ci_95` | Table 1, Section 22 |
| **C-04** | Epistemic uncertainty increases 10.94x on novel OOD regimes vs clean in-distribution data | `experiments/paper2/02_uncertainty_analysis.py` | `configs/paper2/paper2_config.yaml` (`exp02_uncertainty`) | `evaluation/paper2/uncertainty_results.json` -> `disentanglement_metrics.epistemic_separation_ratio` (10.94) | Fig. 3 (`fig3_uncertainty_disentanglement.png`), Section 18 |
| **C-05** | Aleatoric uncertainty correlates with telemetry noise level ($\rho = 0.2955, p = 1.37 \times 10^{-17}$) | `experiments/paper2/02_uncertainty_analysis.py` | `configs/paper2/paper2_config.yaml` (`exp02_uncertainty`) | `evaluation/paper2/uncertainty_results.json` -> `disentanglement_metrics.noise_vs_aleatoric_spearman_rho` | Fig. 4 (`fig4_uncertainty_vs_noise.png`), Section 18 |
| **C-06** | Compound concurrent faults yield lower epistemic uncertainty ($0.303 \pm 0.099$) due to centroid interference | `experiments/paper2/02_uncertainty_analysis.py` | `configs/paper2/paper2_config.yaml` (`exp02_uncertainty`) | `evaluation/paper2/uncertainty_results.json` -> `regime_summaries.Regime_D_Compound_Fault.mean_epistemic` | Section 18, 23 |
| **C-07** | Evidential Epistemic Gating achieves 0.9422 AUROC and 0.9516 AUPRC on OOD detection | `experiments/paper2/03_ood_detection.py` | `configs/paper2/paper2_config.yaml` (`exp03_ood`) | `evaluation/paper2/ood_results.json` -> `model_metrics.Evidential_Dirichlet.auroc` (0.9422) | Table 2, Fig. 5 (`fig5_ood_roc_pr_curves.png`) |
| **C-08** | MLP Softmax Inversion fails on OOD detection (AUROC = 0.4313) due to overconfidence | `experiments/paper2/03_ood_detection.py` | `configs/paper2/paper2_config.yaml` (`exp03_ood`) | `evaluation/paper2/ood_results.json` -> `model_metrics.MLP_Softmax_Inverted.auroc` (0.4313) | Table 2, Section 19 |
| **C-09** | Locked validation threshold ($\tau_{\text{locked}} = 0.0648$) yields 76.67% TPR at 4.50% FPR | `experiments/paper2/03_ood_detection.py` | Validation 95th percentile, Seed 1337 | `evaluation/paper2/ood_results.json` -> `evidential_operational_rates` | Section 19, Fig. 6 |
| **C-10** | Sensor polarity sign inversion was detected in only 6.7% of frames due to absolute value feature transform | `experiments/paper2/03_ood_detection.py` | `configs/paper2/paper2_config.yaml` (`exp03_ood`) | `evaluation/paper2/ood_results.json` -> `ood_category_breakdown.SENSOR_SIGN_INVERSION.detection_rate_at_locked_tau` (0.0667) | Fig. 6 (`fig6_ood_subsystem_breakdown.png`), Section 23 |
| **C-11** | Evidential model maintains significant Macro-F1 advantage over rules across noise sweep ($p = 5.77 \times 10^{-6}$) | `experiments/paper2/04_noise_robustness.py` & `compute_statistics.py` | $\sigma \in [0.00, 0.25]$ | `evaluation/paper2/statistical_results.json` -> `noise_robustness_hypothesis_test.evidential_vs_rules_noise_paired_t` | Table 3, Fig. 7 (`fig7_noise_robustness_curves.png`) |
| **C-12** | False OOD alarm rate remains $< 8\%$ for flight-representative noise ($\sigma \le 0.05$) | `experiments/paper2/04_noise_robustness.py` | $\sigma = 0.05$ | `evaluation/paper2/noise_robustness_results.json` -> `results_by_noise.sigma_0.05.models.EvidentialDirichlet.false_ood_rate` (0.0767) | Fig. 7(d), Section 20 |
| **C-13** | Ablating Mahalanobis metric collapses $R_{\text{int}}$ detection ($F1 = 0.0000$) and drops Macro-F1 by 24% | `experiments/paper2/05_ablation.py` | `M2_EUCLIDEAN_METRIC` | `evaluation/paper2/ablation_results.json` -> `ablation_results.M2_EUCLIDEAN_METRIC.r_int_spike_f1` (0.0) | Table 4, Fig. 8 (`fig8_ablation_comparison.png`) |
| **C-14** | Ablating Evidential Dirichlet drops OOD AUROC by 8.0 percentage points (0.8692 to 0.7895) | `experiments/paper2/05_ablation.py` | `M1_NO_EVIDENTIAL` | `evaluation/paper2/ablation_results.json` -> `ablation_results.M1_NO_EVIDENTIAL.ood_auroc` (0.7895) | Table 4, Fig. 8 (`fig8_ablation_comparison.png`) |
| **C-15** | Removing derivative features increases Expected Calibration Error by 7.4x (0.0179 to 0.1317) | `experiments/paper2/05_ablation.py` | `M4_STATIC_FEATURES_ONLY` | `evaluation/paper2/ablation_results.json` -> `ablation_results.M4_STATIC_FEATURES_ONLY.ece` (0.1317) | Table 4, Fig. 8 (`fig8_ablation_comparison.png`) |

---

## 3. Dataset & Environmental Provenance

- **NASA PCoE Battery B0005 Raw Telemetry**:
  - Path: `data/raw/nasa_pcoe_benchmark_B0005.csv`
  - SHA-256: `4f454d4c083f6ce5e33eb2b6cdbeda3403a633c854a50e6bbce4c18eccdbbfbe`
- **Spacecraft EPS Digital Twin Multi-Orbit Processed Telemetry**:
  - Path: `data/processed/mission_run_3orbits_processed.csv`
  - SHA-256: `724bd00cd858452f677716f2ecb93ce5791a1d180d678557c0f34ba72bc22d77`
- **Execution Python Environment**: Python 3.12.2, Scikit-Learn 1.4.0, NumPy 1.26.4, SciPy 1.13.1.
