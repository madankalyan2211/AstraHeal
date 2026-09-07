# AstraHeal Paper 2 — Study 4: Telemetry Noise Robustness Benchmark

**Experiment Identifier**: `EXP-P2-04`  
**Artifact**: `evaluation/paper2/noise_robustness_results.json`  
**Date**: 2026  
**Status**: Executed & Verified (Phase 7 Complete)

---

## 1. Research Question & Hypothesis

> **Research Question**: How resilient is the evidential diagnostic system against progressive telemetry noise degradation, sensor jitter, and radiation-induced measurement variance?

- **Hypothesis (H4)**: The evidential model will exhibit graceful performance degradation under additive Gaussian sensor noise $\sigma \in [0.00, 0.25]$, with aleatoric uncertainty absorbing observation noise while epistemic uncertainty remains bounded below false-alarm thresholds under moderate noise ($\sigma \le 0.05$).

---

## 2. Experimental Setup

- **Noise Protocol**: Zero-mean Gaussian noise $\mathcal{N}(0, \sigma^2)$ injected additively into normalized telemetry channels:
  $$\sigma \in \{0.00, 0.02, 0.05, 0.10, 0.15, 0.20, 0.25\}$$
- **Sample Count**: 300 held-out test frames evaluated per noise level (50 per class $\times$ 6 known classes; $N = 2,100$ total frame evaluations).
- **Compared Architectures**:
  - `PhysicsRules`: Expert deterministic threshold rules
  - `RandomForest`: 100 decision trees (depth 8)
  - `MLP_Softmax`: Multi-layer perceptron with Softmax output
  - `EvidentialDirichlet`: Proposed evidential Bayesian model

---

## 3. Comparative Degradation Across Noise Tiers

| Noise Level ($\sigma$) | Physics Rules Macro-F1 | Random Forest Macro-F1 | MLP Softmax Macro-F1 | Evidential Engine Macro-F1 | Evidential ECE | False OOD Alarm Rate |
|---|---|---|---|---|---|---|
| **0.00 (Clean)** | 0.5472 | 1.0000 | 1.0000 | **0.9311** | 0.0163 | **4.3%** |
| **0.02 (Low)** | 0.5406 | 0.9933 | 1.0000 | **0.9040** | 0.0204 | **4.7%** |
| **0.05 (Nominal Jitter)** | 0.5072 | 0.9766 | 0.9733 | **0.8308** | 0.0465 | **7.7%** |
| **0.10 (Moderate Noise)** | 0.4952 | 0.8894 | 0.8824 | **0.8265** | 0.0768 | **18.3%** |
| **0.15 (Heavy Jitter)** | 0.4736 | 0.8159 | 0.8231 | **0.7681** | 0.1118 | **35.3%** |
| **0.20 (Severe Degradation)**| 0.4476 | 0.7810 | 0.7557 | **0.7458** | 0.1340 | **50.7%** |
| **0.25 (Extreme Noise)** | 0.4115 | 0.7435 | 0.6888 | **0.6231** | 0.1593 | **64.0%** |

---

## 4. Uncertainty & Calibration Dynamics

1. **Aleatoric Inflation**: Mean aleatoric uncertainty expanded monotonically from $0.081 \pm 0.05$ at $\sigma = 0.00$ to $0.218 \pm 0.14$ at $\sigma = 0.25$, reflecting increased predictive entropy and class overlap as signals become noisy.
2. **False OOD Boundary Breakdown at $\sigma > 0.10$**:
   - For flight-representative sensor noise ($\sigma \le 0.05$, corresponding to $\pm 1.4\text{V}$ bus jitter and $\pm 1.2^\circ\text{C}$ thermistor noise), the False OOD alarm rate remained safely bounded below $8\%$ ($4.3\%$ to $7.7\%$).
   - However, when noise exceeded $\sigma \ge 0.15$, dimensional variance inflated the Euclidean and Mahalanobis norm of known feature vectors, pushing points outside the learned cluster boundaries and triggering the epistemic OOD fallback in $35.3\%$ to $64.0\%$ of known frames.

---

## 5. Non-Equivalence Statement

> [!NOTE]
> **Synthetic Noise vs. Flight Sensor Dynamics**:
> While additive Gaussian perturbations systematically test mathematical stability under variance sweeps, synthetic noise cannot replicate all complex physical phenomena encountered in spaceflight—such as radiation Single Event Upsets (SEU bit-flips), sensor brownouts, or thermal latch-up. These empirical results establish algorithmic noise bounds rather than flight-certified qualification.

---

## 6. Generated Artifacts

- Raw Noise JSON: [noise_robustness_results.json](file:///Users/madanthambisetty/Downloads/SPACE%20PROJECT/evaluation/paper2/noise_robustness_results.json)
- Multi-Panel Degradation Plot: [fig7_noise_robustness_curves.png](file:///Users/madanthambisetty/Downloads/SPACE%20PROJECT/docs/paper2/figures/fig7_noise_robustness_curves.png)
