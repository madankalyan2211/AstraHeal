# AstraHeal v1.0 — Publication Figure Index & Provenance Map

**Document**: `docs/FIGURE_INDEX.md`  
**Date**: 2026-08-31  

---

## Complete Publication Figures Index

| Figure Path | Originating Experiment | Source Data Artifact | Scientific Claim / Purpose |
| :--- | :--- | :--- | :--- |
| `docs/figures/01_nasa_battery_telemetry_trends.png` | `Exp 01` | `data/raw/nasa_battery_pcoe/` | NASA PCoE battery aging dataset degradation curves |
| `docs/figures/02_feature_distributions.png` | `Exp 02` | `data/processed/` | Causal feature engineering ($dV/dt, dT/dt, R_{int}$) distributions |
| `docs/figures/03_anomaly_roc_curves.png` | `Exp 03` | `evaluation/anomaly_benchmark_results.json` | Anomaly detector ROC/AUROC comparison (AUROC = 0.974) |
| `docs/figures/04_diagnosis_confusion_matrix.png` | `Exp 04` | `evaluation/diagnosis_evaluation.json` | Evidential Bayesian fault diagnosis confusion matrix |
| `docs/figures/05_digital_twin_orbit_telemetry.png` | `Exp 05` | `simulations/digital_twin_nominal_orbit.csv`| Closed-loop LEO orbital EPS nominal telemetry profile |
| `docs/figures/06_recovery_trajectories.png` | `Exp 06` | `evaluation/06_recovery_eval_results.json` | Counterfactual lookahead trajectory branching comparison |
| `docs/figures/07_comm_decision_matrix.png` | `Exp 07` | `evaluation/07_communication_autonomy_results.json`| Communication-aware urgency arbitration decision matrix |
| `docs/figures/08_ood_uncertainty_separation.png` | `Exp 08` | `evaluation/08_unknown_resilience_results.json`| Epistemic vs Aleatoric uncertainty separation on OOD faults |
| `docs/figures/09_tri_system_benchmark.png` | `Exp 09` | `evaluation/09_full_benchmark_results.json` | Tri-system comparative benchmark across 8 stress scenarios |
| `docs/figures/10_ablation_study.png` | `Exp 10` | `evaluation/10_ablation_results.json` | 7-configuration component ablation comparison |
| `docs/figures/11_failure_case_taxonomy.png` | `Exp 11` | `evaluation/11_failure_analysis_results.json`| Failure mode taxonomy and physical boundary classification |
| `docs/figures/12_flagship_mission_timeline.png` | `Exp 12` | `simulations/flagship_mission_telemetry.csv`| 14-step flagship closed-loop mission demonstration timeline |
| `docs/figures/13_multi_cycle_autonomy.png` | `Exp 13` | `evaluation/13_multi_cycle_results.json` | Multi-cycle 3-orbit recovery benchmark (122 cycles) |
| `docs/figures/14_controlled_recoverability/01_mission_utility_comparison.png` | `Exp 14` | `evaluation/14_controlled_results.json` | Standardized mission utility score across architectures |
| `docs/figures/14_controlled_recoverability/02_payload_retention_comparison.png` | `Exp 14` | `evaluation/14_controlled_results.json` | Cumulative delivered science payload energy (Wh) |
| `docs/figures/14_controlled_recoverability/03_recovery_success_comparison.png` | `Exp 14` | `evaluation/14_controlled_results.json` | Mission survival rate in controlled recoverable scenarios |
| `docs/figures/14_controlled_recoverability/04_counterfactual_prediction_error.png` | `Exp 14` | `evaluation/14_controlled_results.json` | Predictor error across controlled scenarios |
| `docs/figures/14_controlled_recoverability/05_uncertainty_vs_intervention.png` | `Exp 14` | `evaluation/14_controlled_results.json` | Evidential uncertainty distribution across scenarios |
| `docs/figures/14_controlled_recoverability/06_communication_arbitration.png` | `Exp 14` | `evaluation/14_controlled_results.json` | Communication arbitration outcomes |
| `docs/figures/14_controlled_recoverability/07_safety_governor_rejection_matrix.png` | `Exp 14` | `evaluation/14_controlled_results.json` | Safety Governor candidate proposal rejections |
| `docs/figures/14_controlled_recoverability/08_ablation_comparison.png` | `Exp 14` | `evaluation/14_controlled_results.json` | Full architectural ablation multi-metric comparison |
| `docs/figures/15_independent_validation/01_temp_pred_vs_actual.png` | `Exp 15` | `evaluation/15_counterfactual_validation.json`| Predicted vs ground-truth peak temperature trajectory |
| `docs/figures/15_independent_validation/02_voltage_pred_vs_actual.png` | `Exp 15` | `evaluation/15_counterfactual_validation.json`| Predicted vs ground-truth minimum bus voltage trajectory |
| `docs/figures/15_independent_validation/03_soc_pred_vs_actual.png` | `Exp 15` | `evaluation/15_counterfactual_validation.json`| Predicted vs ground-truth minimum SoC trajectory |
| `docs/figures/15_independent_validation/04_error_vs_horizon.png` | `Exp 15` | `evaluation/15_counterfactual_validation.json`| Prediction error scaling over 600s, 1800s, 3000s horizons |
| `docs/figures/15_independent_validation/05_mae_rmse_comparison.png` | `Exp 15` | `evaluation/15_counterfactual_validation.json`| MAE and RMSE across all 5 telemetry channels |
| `docs/figures/15_independent_validation/06_action_ranking_accuracy.png` | `Exp 15` | `evaluation/15_counterfactual_validation.json`| Top-1 (55.0%) and Top-2 (95.0%) action selection accuracy |
| `docs/figures/15_independent_validation/07_uncertainty_vs_error.png` | `Exp 15` | `evaluation/15_counterfactual_validation.json`| Epistemic uncertainty vs trajectory error correlation |
| `docs/figures/15_independent_validation/08_worst_case_error.png` | `Exp 15` | `evaluation/15_counterfactual_validation.json`| Worst-case candidate prediction error per scenario |
