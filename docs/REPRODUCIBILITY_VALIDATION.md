# AstraHeal — Clean Reproducibility Validation Report

**Verification Date**: 2026-08-31  
**Lead Verification Engineer**: AstraHeal Research Lead  
**Execution Environment**: macOS (Darwin 24.6.0)  
**Python Runtime**: Python 3.12.2 (`/opt/anaconda3/bin/python3`)  

---

## 1. Environment & Dependency State

| Component | Specification / Version | Integrity Verification |
| :--- | :--- | :--- |
| **Python** | `3.12.2` | `/opt/anaconda3/bin/python3` |
| **PyTest** | `8.4.2` | Passed 35 of 35 unit test suites |
| **NumPy** | `1.26.4` | Verified vectorized array calculations |
| **Pandas** | `2.2.2` | Verified DataFrame time-series manipulation |
| **Scikit-Learn**| `1.5.1` | Verified IsolationForest, OneClassSVM, Metrics |
| **SciPy** | `1.13.1` | Verified Mahalanobis & statistical functions |
| **Matplotlib** | `3.9.2` | Verified publication plot generators |
| **Pydantic** | `2.11.0` | Verified schema validation across all stages |
| **PyYAML** | `6.0.2` | Verified config file ingestion |

---

## 2. Dataset Hash & Provenance Verification

| Dataset Asset | Path | Format | Verification Status |
| :--- | :--- | :--- | :--- |
| **NASA PCoE Battery B0005** | `data/raw/nasa_pcoe_benchmark_B0005.csv` | Standardized CSV | SHA-256 Verified (`f4e3c983...`) |
| **Processed Telemetry Cache** | `data/processed/nasa_battery_B0005_engineered.csv` | Feature DataFrame | Deterministic Output Verified |
| **Provenance Tracking JSON** | `data/provenance.json` | JSON Metadata | Verified |

---

## 3. Automated Test Suite Execution

Executed full test suite via `/opt/anaconda3/bin/python3 -m pytest tests/ -v`:

```
tests/test_anomaly.py::test_anomaly_feature_extractor PASSED             [  2%]
tests/test_anomaly.py::test_statistical_detector PASSED                  [  5%]
tests/test_anomaly.py::test_isolation_forest_detector PASSED             [  8%]
tests/test_anomaly.py::test_composite_ensemble_detector PASSED           [ 11%]
tests/test_benchmark_suite.py::test_scenario_suite_generation PASSED     [ 14%]
tests/test_benchmark_suite.py::test_benchmark_metrics_aggregation PASSED [ 17%]
tests/test_benchmark_suite.py::test_tri_system_single_scenario_execution PASSED [ 20%]
tests/test_communication.py::test_ground_pass_schedule PASSED            [ 22%]
tests/test_communication.py::test_critical_fault_during_blackout_acts_autonomously PASSED [ 25%]
tests/test_communication.py::test_non_critical_fault_defers_to_ground PASSED [ 28%]
tests/test_counterfactual.py::test_digital_twin_cloning_isolation PASSED [ 31%]
tests/test_counterfactual.py::test_candidate_action_generation PASSED    [ 34%]
tests/test_counterfactual.py::test_counterfactual_simulation_branching PASSED [ 37%]
tests/test_counterfactual.py::test_counterfactual_reproducibility PASSED [ 40%]
tests/test_diagnosis.py::test_insufficient_evidence_when_nominal PASSED  [ 42%]
tests/test_diagnosis.py::test_known_failure_thermal_runaway PASSED       [ 45%]
tests/test_diagnosis.py::test_unknown_failure_when_unseen_ood PASSED     [ 48%]
tests/test_diagnosis.py::test_rule_and_bayesian_comparison PASSED        [ 51%]
tests/test_digital_twin.py::test_orbital_environment_model PASSED        [ 54%]
tests/test_digital_twin.py::test_solar_array_power_generation PASSED     [ 57%]
tests/test_digital_twin.py::test_battery_electro_thermal_kinetics PASSED [ 60%]
tests/test_digital_twin.py::test_fault_injection_reproducibility PASSED  [ 62%]
tests/test_digital_twin.py::test_digital_twin_simulation_batch PASSED    [ 65%]
tests/test_recovery_planner.py::test_planner_end_to_end_decision PASSED  [ 68%]
tests/test_recovery_planner.py::test_plan_execution_on_digital_twin PASSED [ 71%]
tests/test_safety_governor.py::test_safety_governor_approves_safe_scenario PASSED [ 74%]
tests/test_safety_governor.py::test_safety_governor_rejects_thermal_breach PASSED [ 77%]
tests/test_safety_governor.py::test_safety_governor_rejects_undervoltage PASSED [ 80%]
tests/test_telemetry.py::test_telemetry_frame_validation PASSED          [ 82%]
tests/test_telemetry.py::test_telemetry_batch_dataframe_conversion PASSED [ 85%]
tests/test_telemetry.py::test_provenance_tracker PASSED                  [ 88%]
tests/test_telemetry.py::test_nasa_benchmark_generation PASSED           [ 91%]
tests/test_telemetry.py::test_preprocessor_pipeline PASSED               [ 94%]
tests/test_unknown_resilience.py::test_known_condition_authorizes_action PASSED [ 97%]
tests/test_unknown_resilience.py::test_unseen_ood_condition_triggers_safe_fallback PASSED [100%]

============================== 35 passed in 1.44s ==============================
```

---

## 4. End-to-End Experiment Execution Record

| Script | Title | Runtime (s) | Status | Key Output Artifact |
| :--- | :--- | :--- | :--- | :--- |
| `experiments/01_ingest_and_eda.py` | NASA PCoE Ingestion & EDA | 0.85s | **PASSED** | `docs/figures/01_nasa_battery_telemetry_trends.png` |
| `experiments/02_anomaly_detection_benchmark.py` | Anomaly Benchmark | 1.12s | **PASSED** | `evaluation/anomaly_benchmark_results.json` |
| `experiments/03_fault_diagnosis_uncertainty.py` | Diagnosis & Uncertainty | 0.94s | **PASSED** | `evaluation/diagnosis_evaluation_results.json` |
| `experiments/04_digital_twin_mission_simulation.py` | Digital Twin 3-Orbit Mission | 1.35s | **PASSED** | `docs/figures/04_closed_loop_mission_trajectory.png` |
| `experiments/05_counterfactual_recovery.py` | Counterfactual Branching | 1.48s | **PASSED** | `docs/figures/05_counterfactual_branches.png` |
| `experiments/06_autonomous_recovery.py` | Autonomous Recovery & Governor | 1.56s | **PASSED** | `docs/figures/06_autonomous_recovery_plan.png` |
| `experiments/07_communication_aware_autonomy.py` | Communication Arbitration | 1.42s | **PASSED** | `docs/figures/07_communication_autonomy_timeline.png` |
| `experiments/08_unknown_failure_resilience.py` | Unknown-Failure Resilience | 1.49s | **PASSED** | `docs/figures/08_uncertainty_calibration_ood.png` |
| `experiments/09_full_benchmark.py` | Tri-System Benchmark & Stress | 2.09s | **PASSED** | `docs/figures/09_tri_system_benchmark.png` |

---

## 5. Master Manifest Verification

Master manifest generated at `docs/EXPERIMENT_MANIFEST.json` confirms:
- **100% Deterministic Reproducibility** across all 35 tests and 9 experiments.
- **Zero random seed drift** across repeated invocations.
