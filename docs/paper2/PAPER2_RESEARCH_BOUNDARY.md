# AstraHeal Paper 2 — Scientific Research Boundary & Audit

**Project**: AstraHeal — Autonomous Self-Healing Spacecraft Intelligence Platform  
**Document**: Research Boundary, Scope Audit, and Frozen Baseline Mapping  
**Working Title**: *Evidential Uncertainty-Aware Fault Diagnosis for Autonomous Spacecraft Health Management*  
**Date**: 2026  
**Status**: Formal Research Protocol Initialized (Phase 0 Complete)

---

## 1. Central Research Question

> **"Can an evidential AI fault-diagnosis system distinguish known spacecraft failure modes from previously unseen or compound failures while explicitly characterizing epistemic and aleatoric uncertainty?"**

---

## 2. Motivation

Modern spacecraft operate in extreme radiation and orbital environments during prolonged line-of-sight communication blackouts (up to 45 minutes per 95-minute Low Earth Orbit, and minutes to hours in deep space). Subsystem failures—such as battery internal impedance degradation, solar panel string occlusions, thermal runaway, and electrical bus shorts—can evolve catastrophically before ground flight controllers can diagnose the anomaly.

Conventional aerospace Fault Detection, Isolation, and Recovery (FDIR) architectures rely either on:
1. **Rigid, hand-crafted threshold tables** that cannot reason over subtle multivariate trends or novel compound failures; or
2. **Point-estimate machine learning classifiers** that output overconfident softmax probabilities when exposed to out-of-distribution (OOD) operational regimes or unmodeled physical damage.

When an onboard autonomy system cannot quantify its own ignorance, it risks executing aggressive, irreversible physical commands (such as tripping high-power bus switches or shedding science payloads) based on spurious high-confidence misclassifications. Conversely, default transitions to emergency Safe Mode prematurely abort critical science missions. An evidential diagnosis architecture that mathematically separates **aleatoric uncertainty** (observation noise, telemetry entropy) from **epistemic uncertainty** (lack of physical domain knowledge, novel failure dynamics) provides the formal foundation required for safe, trustworthy onboard decision-making.

---

## 3. Scientific Gap

While evidential deep learning (EDL) and Dirichlet prior networks have demonstrated utility in terrestrial computer vision and synthetic benchmarks, their application to space systems faces distinct physical challenges:
1. **Telemetry Sparsity & High Dynamics**: Orbital telemetry is constrained by low downlink bandwidth, non-stationary thermal and solar illumination cycles, and sensor noise.
2. **Conflation of Noise and Novelty**: Standard Bayesian neural networks or Monte Carlo dropout techniques conflate sensor jitter (aleatoric noise) with genuinely novel failure physics (epistemic novelty), leading to false OOD alarms under noisy communication passes.
3. **Absence of Independent Rigorous Benchmarking**: Prior literature often evaluates fault diagnosis on isolated static test sets without systematically probing compound multi-subsystem failures, continuous noise sweeps, or formal ablation of evidential vs. standard softmax formulations.

---

## 4. Formal Research Hypotheses

- **Hypothesis 1 (H1 — Known-Mode Discriminability)**:  
  An evidential Dirichlet diagnostic engine incorporating physics-informed priors will achieve comparable or superior classification accuracy ($\text{Macro-F1} \ge 0.90$) to standard non-evidential baselines (Random Forest, MLP, Physics Rules) across known spacecraft EPS failure modes.
- **Hypothesis 2 (H2 — Epistemic/Aleatoric Disentanglement)**:  
  Epistemic uncertainty ($u_{\text{epistemic}}$) will significantly increase under novel and compound failure conditions ($\Delta u_{\text{epistemic}} > 0.40$), while aleatoric uncertainty ($u_{\text{aleatoric}}$) will scale monotonically with telemetry sensor noise rather than distributional shift.
- **Hypothesis 3 (H3 — OOD & Compound Failure Detection)**:  
  Gating on epistemic uncertainty will detect unseen individual failure modes and compound multi-subsystem failures with an $\text{AUROC} \ge 0.95$ and $\text{FPR@95\%TPR} \le 0.10$, without requiring exposure to OOD examples during training.
- **Hypothesis 4 (H4 — Noise Robustness)**:  
  Under progressive telemetry noise degradation ($\sigma \in [0.0, 0.25]$ relative variance), the evidential architecture will maintain well-calibrated confidence estimates, with aleatoric uncertainty capturing noise degradation without erroneously triggering epistemic OOD flags.
- **Hypothesis 5 (H5 — Component Contribution via Ablation)**:  
  Ablation of the Dirichlet evidential formulation, Mahalanobis covariance metric, or derivative features ($dV/dt$, $dT/dt$, $R_{\text{int}}$) will result in measurable degradation in either classification F1, calibration error (ECE), or OOD discriminability.

---

## 5. Intended Scientific Contributions

1. **Formal Evidential Spacecraft Diagnostic Formulation**: A complete mathematical formulation parameterizing Dirichlet evidential distributions over spacecraft EPS failure manifolds with closed-form uncertainty decomposition.
2. **Empirical Epistemic vs. Aleatoric Validation**: Rigorous empirical proof that observation noise and distributional novelty occupy separable uncertainty axes in orbital telemetry.
3. **Systematic OOD & Compound Anomaly Benchmark**: A reproducible testbed evaluating 5 known failure modes against 4 distinct out-of-distribution classes (novel single faults, compound simultaneous faults, sensor inversions, and unmodeled physical domain drift).
4. **Comprehensive Comparative Baseline & Ablation Study**: Direct comparison against Physics Rules, Random Forests, Multi-Layer Perceptrons (Softmax), and Standard Mahalanobis Classifiers under identical data splits.
5. **Reproducible Open Research Package**: Deterministic experiment suite, locked configurations, raw JSON evaluation artifacts, and compile-ready publication assets.

---

## 6. Existing AstraHeal Components

The AstraHeal repository contains a modular architecture for autonomous spacecraft operations:
- `src/telemetry/`: Preprocessing, feature engineering ($dQ/dV$, $R_{\text{int}}$, $dV/dt$, $dT/dt$), provenance tracking, and NASA dataset ingestion.
- `src/anomaly/`: Multi-channel anomaly detection (Statistical Z-score/Mahalanobis, Isolation Forest, One-Class SVM).
- `src/diagnosis/`: Evidential Dirichlet diagnostic engine (`bayesian.py`), physics rule engine (`rules.py`), fault catalog schemas (`schema.py`), and resilience evaluator (`resilience.py`).
- `src/digital_twin/`: Spacecraft Electrical Power System simulator (Thevenin 1-RC battery kinetics, LEO orbital eclipse mechanics, photovoltaic power, thermal conduction/radiation, and fault injection).
- `src/planner/` & `src/safety/`: Counterfactual lookahead planner and deterministic Safety Governor.
- `src/communication/`: Ground station contact pass scheduling and blackout arbitration.

---

## 7. Frozen Paper 1 Evidence

AstraHeal v1.0 established baseline platform capability documented in `evaluation/`:
- Multi-cycle orbital autonomy across 3 LEO orbits (`13_multi_cycle_results.json`).
- Physical safety invariant preservation across 609 counterfactual candidates (`06_autonomous_recovery_results.json`, `15_counterfactual_validation.json`).
- High-level OOD detection demonstration on 6 scenarios (`08_unknown_resilience_results.json`).
- Controlled recoverability bounds demonstrating physical limits of autonomy (`14_controlled_results.json`).

*All aforementioned historical files and numbers are strictly FROZEN and will not be altered.*

---

## 8. Potentially Reusable Baseline Evidence

The following mathematical modules from `src/` can be utilized as read-only computational building blocks:
- `src/diagnosis/bayesian.py`: `BayesianEvidentialDiagnosticEngine`
- `src/diagnosis/rules.py`: `PhysicsRuleDiagnosticEngine`
- `src/diagnosis/schema.py`: Data models (`DiagnosisReport`, `FailureMode`, `DiagnosisStatus`)
- `src/telemetry/preprocess.py`: Feature calculation pipelines
- `src/digital_twin/simulator.py`: High-fidelity telemetry generation for physical state ground truth

---

## 9. New Research Required for Paper 2

Paper 2 requires independent research modules, experimental scripts, and evaluation pipelines that did not exist in AstraHeal v1.0:
1. **Isolated Multi-Model Diagnostic Testbed**: Systematic evaluation comparing the Evidential Dirichlet Engine against Machine Learning baselines (`RandomForestClassifier`, `MLPClassifier`, `StandardMahalanobisClassifier`, `PhysicsRules`) under uniform cross-validation and held-out test splits.
2. **Rigorous Uncertainty Calibration & Decomposition Study**: Quantitative tracking of Expected Calibration Error (ECE), Brier score, Shannon entropy, and Dirichlet epistemic variance.
3. **Multi-Class OOD Metric Suite**: Standardized AUROC, AUPRC, FPR@95%TPR, and false-alarm characterization across pre-defined out-of-distribution failure classes.
4. **Systematic Telemetry Noise Robustness Experiment**: Dynamic evaluation across controlled additive Gaussian sensor noise levels $\sigma \in [0.0, 0.25]$.
5. **Component Ablation Pipeline**: Systematic removal of evidential gating, physics priors, covariance metrics, and temporal features.
6. **Statistical Significance Testing**: Formal paired tests, effect sizes (Cohen's $d$), and bootstrap confidence intervals.

---

## 10. Data Sources

1. **NASA Prognostics Center of Excellence (PCoE) Battery Aging Archive**:
   - Source: NASA Ames Research Center, Battery Data Set (B0005).
   - Provenance Hash: SHA-256 verified in `data/provenance.json`.
   - Modality: Real electro-thermal battery charge/discharge cycles under ambient temperature.
2. **High-Fidelity Spacecraft EPS Digital Twin Telemetry**:
   - Deterministic physics simulator modeling 28V regulated power bus, solar array orbital illumination (90-min orbit, 35-min eclipse), Thevenin 1-RC battery impedance kinetics, and radiative thermal equilibrium.
   - Fixed random seeds to ensure 100% deterministic reproducibility.

---

## 11. Evaluation Boundaries

- **Subsystem Focus**: Electrical Power System (EPS), including energy storage, generation, power distribution, and thermal coupling. Attitude Determination and Control Systems (ADCS) and propulsion dynamics are explicitly out of scope.
- **Thermal Model**: Lumped single-node thermal capacitance model ($C_{\text{th}} = 4500\text{ J/K}$) rather than a full 3D finite-element thermal mesh.
- **Orbital Regime**: Circular Low Earth Orbit (LEO, 500 km altitude, 95-minute period).

---

## 12. Threats to Validity

1. **Synthetic Telemetry Fidelity**: While the digital twin enforces conservation of energy and physical differential equations, simulated telemetry cannot capture all unmodeled high-frequency noise modes present on actual flight hardware.
2. **Class Imbalance in Flight Archives**: In real space operations, nominal frames outnumber anomaly frames by orders of magnitude. The experimental evaluation must explicitly report balanced accuracy and macro-F1 to prevent majority-class bias.
3. **Threshold Sensitivity**: OOD decision boundaries must be selected on validation folds and strictly locked prior to test-set scoring.

---

## 13. Explicit Non-Claims

To preserve absolute scientific honesty:
- We **DO NOT** claim operational flight heritage or on-orbit flight validation.
- We **DO NOT** claim NASA endorsement, partnership, approval, or agency deployment.
- We **DO NOT** claim that the evidential diagnostic system guarantees zero misclassifications under arbitrary unmodeled physics.
- We **DO NOT** claim that software diagnostics can compensate for physically unrecoverable hardware destruction.

---

## 14. Namespace & Component Boundary Lists

### FROZEN FILES (STRICTLY READ-ONLY):
- `src/` (all existing algorithms, classes, and methods)
- `experiments/01_ingest_and_eda.py` through `experiments/15_independent_counterfactual_validation.py`
- `evaluation/*.json` (all historical baseline artifacts)
- `tests/test_*.py` (the 35 passing AstraHeal v1.0 unit tests)
- `configs/*.yaml` (all v1.0 configuration files)
- `docs/paper/` (all Paper 1 LaTeX, Markdown, and PDF assets)

### REUSABLE COMPONENTS (CALLED AS READ-ONLY LIBRARIES):
- `src.diagnosis.bayesian.BayesianEvidentialDiagnosticEngine`
- `src.diagnosis.rules.PhysicsRuleDiagnosticEngine`
- `src.diagnosis.schema.DiagnosisReport`, `FailureMode`, `DiagnosisStatus`
- `src.telemetry.preprocess.TelemetryPreprocessor`
- `src.digital_twin.simulator.SpacecraftEPSDigitalTwin`
- `src.digital_twin.fault_injection.InjectedFaultSpec`, `FaultType`

### NEW PAPER 2 COMPONENTS REQUIRED:
- `experiments/paper2/`
  - `01_known_fault_diagnosis.py`
  - `02_uncertainty_analysis.py`
  - `03_ood_detection.py`
  - `04_noise_robustness.py`
  - `05_ablation.py`
  - `run_all_paper2.py`
- `evaluation/paper2/` (all new JSON metrics and raw prediction records)
- `configs/paper2/paper2_config.yaml`
- `tests/paper2/test_paper2_pipeline.py`
- `docs/paper2/`
  - `PAPER2_RESEARCH_BOUNDARY.md`
  - `PAPER2_EXPERIMENT_PLAN.md`
  - `DATASET_AND_LEAKAGE_AUDIT.md`
  - `01_KNOWN_FAULT_DIAGNOSIS.md`
  - `02_UNCERTAINTY_ANALYSIS.md`
  - `03_OOD_DETECTION.md`
  - `04_NOISE_ROBUSTNESS.md`
  - `05_ABLATION.md`
  - `STATISTICAL_ANALYSIS.md`
  - `RESULT_PROVENANCE.md`
  - `PAPER2_RESULTS_FREEZE.md`
  - `FINAL_CLAIMS_AUDIT.md`
  - `PAPER2_MANUSCRIPT.md`
  - `PEER_REVIEW_SELF_AUDIT.md`
  - `REPRODUCIBILITY.md`
  - `PUBLIC_RELEASE_AUDIT.md`
  - `PAPER2_RELEASE_MANIFEST.md`
  - `PUBLICATION_READINESS.md`
- `docs/paper2/figures/` (all publication-grade SVG/PNG plots)
- `docs/paper2/latex/` (`main.tex`, `references.bib`, `PAPER2.pdf`)
