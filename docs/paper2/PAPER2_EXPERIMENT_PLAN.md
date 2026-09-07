# AstraHeal Paper 2 — Scientific Experiment Plan

**Document**: Master Experimental Protocol and Benchmark Specification  
**Project**: AstraHeal — Paper 2  
**Working Title**: *Evidential Uncertainty-Aware Fault Diagnosis for Autonomous Spacecraft Health Management*  
**Date**: 2026  
**Status**: Formal Experiment Plan (Phase 1 Complete)

---

## 1. Experimental Program Architecture

The Paper 2 experimental program comprises five primary scientific studies designed to interrogate the capabilities, failure modes, and boundaries of evidential spacecraft fault diagnosis:

| Study ID | Script Name | Research Theme | Core Question |
|---|---|---|---|
| **EXP-P2-01** | `01_known_fault_diagnosis.py` | Known-Fault Classification & Calibration | Can the evidential engine match or exceed ML/Physics baselines on familiar anomalies without sacrificing calibration? |
| **EXP-P2-02** | `02_uncertainty_analysis.py` | Uncertainty Disentanglement | Does epistemic uncertainty isolate novelty/OOD while aleatoric uncertainty captures noise/entropy? |
| **EXP-P2-03** | `03_ood_detection.py` | Out-Of-Distribution & Compound Failures | Can epistemic gating reliably detect unseen individual faults and compound simultaneous anomalies? |
| **EXP-P2-04** | `04_noise_robustness.py` | Telemetry Noise Robustness | How does progressive sensor noise ($\sigma \in [0.0, 0.25]$) impact diagnosis, calibration, and uncertainty? |
| **EXP-P2-05** | `05_ablation.py` | Systematic Component Ablation | What is the quantitative marginal contribution of each mathematical component in the evidential engine? |

---

## 2. Detailed Experiment Specifications

### Study 1: Known-Fault Classification Benchmark (EXP-P2-01)

- **Experiment Identifier**: `EXP-P2-01`
- **Research Question**: How accurately and reliably can the evidential diagnostic system classify known spacecraft EPS failure modes compared to conventional machine learning and physics-informed baselines?
- **Research Hypothesis (H1)**: The Evidential Dirichlet Engine will achieve a Macro-F1 $\ge 0.90$ with an Expected Calibration Error (ECE) $\le 0.12$, matching or outperforming Random Forest, Multi-Layer Perceptron (Softmax), and Physics Rule baselines on held-out test frames.
- **Independent Variables**:
  - Diagnostic Model:
    1. Proposed: `BayesianEvidentialDiagnosticEngine` (Dirichlet Evidence + Physics Prior Centroids + Mahalanobis Metric)
    2. Baseline 1: `PhysicsRuleDiagnosticEngine` (Deterministic expert rules)
    3. Baseline 2: `RandomForestClassifier` (100 estimators, max depth 8)
    4. Baseline 3: `MLPClassifier` (128-64 hidden units, ReLU, Softmax output)
    5. Baseline 4: `StandardMahalanobisClassifier` (Centroid distance without Dirichlet uncertainty)
- **Dependent Variables**:
  - Accuracy, Balanced Accuracy
  - Macro Precision, Macro Recall, Macro F1
  - Per-class Precision, Recall, F1 (across 5 failure modes + nominal)
  - Expected Calibration Error (ECE, 10 equal-width confidence bins)
  - Brier Score
  - Inference Latency (milliseconds per frame)
- **Dataset & Scenarios**:
  - High-fidelity Spacecraft EPS Digital Twin multi-orbit simulated telemetry + NASA PCoE Battery B0005 benchmark features.
  - 5 Known Failure Modes:
    1. `BATTERY_INTERNAL_RESISTANCE_SPIKE`
    2. `SOLAR_ARRAY_STRING_FAULT`
    3. `THERMAL_RUNAWAY_INITIATION`
    4. `PARASITIC_BUS_OVERLOAD`
    5. `SENSOR_BIAS_DRIFT`
    plus `NOMINAL_OPERATION`.
- **Train / Validation / Test Split**:
  - 60% Train, 20% Validation (for hyperparameter confirmation), 20% Held-out Test.
  - Stratified by fault class. Temporal grouping enforced across scenario trajectories to prevent temporal leakage.
- **Sample Count**: $N = 1,200$ balanced frames across 6 classes (200 frames/class).
- **Random Seed**: Fixed at `42` (with verification on `1337` and `2026`).
- **Statistical Methodology**: 5-fold cross-validation on train/val, single evaluation pass on held-out test. Paired Wilcoxon signed-rank test against the best non-evidential baseline.
- **Expected Outputs**:
  - Confusion matrices for all 5 models.
  - Reliability diagrams (predicted confidence vs empirical accuracy).
  - Benchmark comparison table.
- **Failure Conditions**: Macro-F1 $< 0.80$ on held-out test set, or ECE $> 0.20$.
- **Reproducibility Artifact**: `evaluation/paper2/known_fault_results.json`.
- **Figures / Tables**:
  - Figure: `docs/paper2/figures/fig1_confusion_matrices.png`
  - Figure: `docs/paper2/figures/fig2_calibration_curves.png`
  - Table: Table 1 in manuscript.

---

### Study 2: Epistemic vs. Aleatoric Uncertainty Disentanglement (EXP-P2-02)

- **Experiment Identifier**: `EXP-P2-02`
- **Research Question**: Does the evidential formulation provide genuine physical disentanglement between epistemic uncertainty (model ignorance / OOD) and aleatoric uncertainty (data noise / telemetry entropy)?
- **Research Hypothesis (H2)**: Epistemic uncertainty ($u_{\text{epistemic}}$) will exhibit strong positive separation on unfamiliar and out-of-distribution faults ($u_{\text{epistemic}} \ge 0.70$) while remaining low on nominal/known faults ($u_{\text{epistemic}} \le 0.35$). Conversely, aleatoric uncertainty ($u_{\text{aleatoric}}$) will correlate strongly with telemetry noise variance ($\rho_{\text{Spearman}} > 0.75$) and hypothesis entropy, but will not flag out-of-distribution shifts.
- **Independent Variables**:
  - Condition Regimes:
    1. Regime A: Clean Familiar Faults ($\sigma_{\text{noise}} = 0.0$)
    2. Regime B: Familiar Faults + Additive Telemetry Jitter ($\sigma_{\text{noise}} \in \{0.05, 0.10, 0.20\}$)
    3. Regime C: Out-of-Distribution Novel Faults (unseen failure dynamics)
    4. Regime D: Compound Simultaneous Faults
    5. Regime E: Boundary Ambiguity (transient eclipse transitions)
- **Dependent Variables**:
  - Mean and median $u_{\text{epistemic}}$
  - Mean and median $u_{\text{aleatoric}}$
  - Total Uncertainty $u_{\text{total}}$
  - Spearman Rank Correlation ($\rho$) between $u_{\text{epistemic}}$ and Mahalanobis OOD distance
  - Spearman Rank Correlation ($\rho$) between $u_{\text{aleatoric}}$ and observation noise $\sigma$
  - Disentanglement Ratio: $\mathcal{D} = \frac{\mathbb{E}[u_{\text{epistemic}} \mid \text{OOD}] / \mathbb{E}[u_{\text{epistemic}} \mid \text{Known}]}{\mathbb{E}[u_{\text{aleatoric}} \mid \text{OOD}] / \mathbb{E}[u_{\text{aleatoric}} \mid \text{Known}]}$
- **Sample Count**: $N = 1,000$ frames across the 5 test regimes (200 frames/regime).
- **Random Seed**: Fixed at `42`.
- **Expected Outputs**: Bivariate scatter plots, empirical distribution densities, and correlation tables.
- **Failure Conditions**: Epistemic uncertainty failing to elevate under OOD ($u_{\text{epistemic}} < 0.50$ on novel regimes), or aleatoric uncertainty failing to respond to sensor noise.
- **Reproducibility Artifact**: `evaluation/paper2/uncertainty_results.json`.
- **Figures / Tables**:
  - Figure: `docs/paper2/figures/fig3_uncertainty_disentanglement.png`
  - Figure: `docs/paper2/figures/fig4_uncertainty_vs_noise.png`

---

### Study 3: Out-of-Distribution (OOD) & Compound Failure Detection (EXP-P2-03)

- **Experiment Identifier**: `EXP-P2-03`
- **Research Question**: Can the evidential diagnostic system accurately detect and reject anomalies outside its training distribution, including novel single failure modes and compound multi-subsystem failures, without generating false alarms on known faults?
- **Research Hypothesis (H3)**: Thresholding on $u_{\text{epistemic}}$ (locked on validation data at the 95th percentile of known faults) will achieve an AUROC $\ge 0.95$, AUPRC $\ge 0.90$, and FPR@95%TPR $\le 0.10$ across novel and compound fault scenarios, significantly outperforming maximum softmax probability (MSP) and standard isolation forest baselines.
- **Independent Variables**:
  - In-Distribution (ID): 5 known EPS failure modes + nominal frames ($N_{\text{ID}} = 600$).
  - Out-of-Distribution (OOD) Categories ($N_{\text{OOD}} = 600$):
    1. `OOD-1: NOVEL_UNSEEN_MODE` (e.g. rapid bus catastrophic short-circuit with severe negative inductive transient, unmodeled in training).
    2. `OOD-2: COMPOUND_CONCURRENT_FAULT` (simultaneous solar panel string loss + exothermic runaway heat generation).
    3. `OOD-3: EXTREME_THERMAL_INVERSION` (deep eclipse cryogenic battery freeze below $-40^\circ\text{C}$ with severe internal resistance surge).
    4. `OOD-4: SENSOR_SIGN_INVERSION` (unmodeled instrumentation polarity flip).
  - Detection Gating Criteria:
    - Evidential Epistemic Gating ($u_{\text{epistemic}} > \tau_{\text{locked}}$)
    - Maximum Softmax Probability ($1 - \max_c P(y=c) > \tau$)
    - Standard Isolation Forest Score
- **Dependent Variables**:
  - AUROC (Area Under Receiver Operating Characteristic Curve)
  - AUPRC (Area Under Precision-Recall Curve)
  - True Positive Rate (TPR) at 5% False Positive Rate (FPR)
  - False Acceptance Rate (FAR, mistaking OOD for known)
  - False Rejection Rate (FRR, mistaking known for OOD)
  - Autonomous Safe-Fallback Trigger Rate
- **Threshold Policy**:
  - Threshold $\tau_{\text{locked}}$ is determined strictly on the validation set ($\tau = \text{Percentile}(u_{\text{epistemic}}^{\text{val}}, 95.0) \approx 0.45$).
  - Once determined, $\tau_{\text{locked}}$ is frozen and evaluated strictly on the independent held-out OOD test partition.
- **Sample Count**: $N_{\text{total}} = 1,200$ (600 ID, 600 OOD).
- **Random Seed**: Fixed at `42`.
- **Expected Outputs**: ROC curves, PR curves, and confusion breakdown per OOD category.
- **Failure Conditions**: AUROC $< 0.85$ or False Acceptance Rate on compound faults $> 0.15$.
- **Reproducibility Artifact**: `evaluation/paper2/ood_results.json`.
- **Figures / Tables**:
  - Figure: `docs/paper2/figures/fig5_ood_roc_pr_curves.png`
  - Figure: `docs/paper2/figures/fig6_ood_subsystem_breakdown.png`

---

### Study 4: Telemetry Noise Robustness (EXP-P2-04)

- **Experiment Identifier**: `EXP-P2-04`
- **Research Question**: How resilient is the evidential diagnostic system against progressive sensor degradation, quantization noise, and radiation-induced telemetry jitter?
- **Research Hypothesis (H4)**: Under increasing additive zero-mean Gaussian telemetry noise with standard deviation $\sigma \in \{0.00, 0.02, 0.05, 0.10, 0.15, 0.20, 0.25\}$ (normalized to channel dynamic range):
  - The evidential model will experience a graceful Macro-F1 degradation ($< 15\%$ loss at $\sigma = 0.15$), outperforming brittle rule-based heuristics ($> 30\%$ degradation).
  - Aleatoric uncertainty will scale linearly with $\sigma$, while epistemic uncertainty will remain bounded below the OOD trigger threshold for genuine known faults.
- **Independent Variables**:
  - Noise Level: $\sigma \in [0.00, 0.02, 0.05, 0.10, 0.15, 0.20, 0.25]$ applied additively to normalized telemetry channels ($V, I, T, P, dV/dt, dT/dt, R_{\text{int}}$).
  - Diagnostic Models: Evidential Dirichlet Engine, Random Forest, MLP, Physics Rules.
- **Dependent Variables**:
  - Macro-F1 vs. $\sigma$
  - Balanced Accuracy vs. $\sigma$
  - Mean $u_{\text{aleatoric}}$ vs. $\sigma$
  - Mean $u_{\text{epistemic}}$ vs. $\sigma$
  - Expected Calibration Error (ECE) vs. $\sigma$
  - False OOD Trigger Rate (known faults falsely rejected as OOD due to noise alone)
- **Sample Count**: 500 test frames evaluated across 7 noise tiers ($N = 3,500$ frame evaluations).
- **Random Seed**: Fixed at `42`.
- **Expected Outputs**: Multi-line performance degradation trajectories and uncertainty vs. noise curves.
- **Failure Conditions**: False OOD trigger rate exceeding 25% at moderate noise ($\sigma = 0.10$), or Macro-F1 dropping below 0.65 at $\sigma = 0.10$.
- **Reproducibility Artifact**: `evaluation/paper2/noise_robustness_results.json`.
- **Figures / Tables**:
  - Figure: `docs/paper2/figures/fig7_noise_robustness_curves.png`

---

### Study 5: Systematic Component Ablation (EXP-P2-05)

- **Experiment Identifier**: `EXP-P2-05`
- **Research Question**: What are the specific quantitative performance contributions of the Dirichlet evidential formulation, the Mahalanobis covariance metric, physics-informed prior centroids, and dynamic derivative telemetry features?
- **Research Hypothesis (H5)**:
  - Replacing the Mahalanobis metric with Euclidean distance will degrade classification F1 due to ignoring covariance between battery voltage and load current.
  - Removing Dirichlet evidential uncertainty in favor of Softmax entropy will severely degrade OOD AUROC ($\Delta \text{AUROC} > 0.15$).
  - Removing derivative features ($dV/dt$, $dT/dt$, $R_{\text{int}}$) will impair early detection of thermal runaway initiation and internal resistance spikes.
- **Ablation Configurations**:
  1. `M0_FULL`: Full Proposed Evidential Dirichlet Engine (All features, Physics Priors, Mahalanobis metric, Evidential Gating).
  2. `M1_NO_EVIDENTIAL`: Softmax Logits only (Standard Bayesian posterior without Dirichlet epistemic parameterization).
  3. `M2_EUCLIDEAN_METRIC`: Euclidean distance substituted for Mahalanobis covariance metric ($d = \|x - \mu\|_2$).
  4. `M3_NO_PHYSICS_PRIORS`: Uniform / uninformative prior centroids instead of aerospace physics priors.
  5. `M4_STATIC_FEATURES_ONLY`: Derivative features ($dV/dt, dT/dt, R_{\text{int}}$) removed; static channels ($V, I, T, P$) only.
- **Dependent Variables**:
  - Known-fault Macro-F1
  - Known-fault ECE (Calibration)
  - OOD Detection AUROC
  - False Positive Rate at 95% TPR
  - Thermal Runaway F1 Score
- **Evaluation Split**: Evaluated on identical test sets from EXP-P2-01 and EXP-P2-03 to ensure strict comparability.
- **Expected Outputs**: Ablation delta table and comparative bar chart.
- **Failure Conditions**: Ablations failing to exhibit statistically distinct behavior, indicating degenerate or redundant components.
- **Reproducibility Artifact**: `evaluation/paper2/ablation_results.json`.
- **Figures / Tables**:
  - Figure: `docs/paper2/figures/fig8_ablation_comparison.png`
  - Table: Table 4 in manuscript.

---

## 3. Protocol Rules & Scientific Safeguards

1. **No Test-Set Tuning**: All hyper-parameters and threshold boundaries ($\tau_{\text{locked}}$) are determined solely on validation folds.
2. **Fixed Random Seeds**: All stochastic operations (splits, noise addition, bootstrapping) utilize fixed seeds `42`, `1337`, `2026`.
3. **No Metric Cherry-Picking**: Every experiment records both success and failure metrics across all evaluated classes and models.
4. **Data Isolation**: Synthetic digital twin scenarios are generated with isolated random seeds and zero state vector leakage.
