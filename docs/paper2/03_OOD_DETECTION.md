# AstraHeal Paper 2 — Study 3: Out-Of-Distribution & Compound Failure Detection

**Experiment Identifier**: `EXP-P2-03`  
**Artifact**: `evaluation/paper2/ood_results.json`  
**Date**: 2026  
**Status**: Executed & Verified (Phase 6 Complete)

---

## 1. Research Question & Hypothesis

> **Research Question**: Can the evidential diagnostic system identify failures outside its training distribution, including novel single failure modes and compound multi-subsystem failures, without generating false alarms on known flight conditions?

- **Hypothesis (H3)**: Thresholding on epistemic uncertainty ($u_{\text{epistemic}} \ge \tau_{\text{locked}}$) will achieve an AUROC $\ge 0.90$ across novel and compound failure modes, drastically outperforming Maximum Softmax Probability (MSP), while exposing explicit boundaries on unmodeled feature transforms.

---

## 2. Experimental Setup

- **Benchmark Partitions**:
  - In-Distribution Training (ID Train): 600 frames across 6 known classes (seed 42).
  - Validation Partition (Threshold Determination): 300 ID frames + 100 OOD frames (seed 1337).
  - Strictly Held-Out Test Partition: 600 ID frames vs. 600 OOD frames (seed 2026).
- **Locked Threshold Policy**:
  - The epistemic gating threshold $\tau_{\text{locked}}$ was calculated strictly on the validation set at the 95th percentile of known-mode epistemic uncertainty: $\tau_{\text{locked}} = 0.0648$.
  - This threshold was frozen and applied blindly to the test set.
- **OOD Evaluation Classes**:
  1. `OOD-1: NOVEL_UNSEEN_MODE`: Catastrophic 500W power bus short-circuit ($V < 12\text{V}$, $dV/dt < -5\text{V/s}$).
  2. `OOD-2: COMPOUND_CONCURRENT_FAULT`: Simultaneous solar string failure (50%) and exothermic thermal runaway (65W heat injection).
  3. `OOD-3: EXTREME_THERMAL_INVERSION`: Deep eclipse cryogenic freeze below $-45^\circ\text{C}$ with severe internal resistance surge.
  4. `OOD-4: SENSOR_SIGN_INVERSION`: Instrumentation polarity reversal on current telemetry.

---

## 3. Comparative OOD Detection Performance

| Method | Metric Basis | AUROC | AUPRC | FPR @ 95% TPR |
|---|---|---|---|---|
| **MLP_Softmax_Inverted** | $1 - \max_c P(y=c)$ (MSP) | 0.4313 | 0.6135 | 1.0000 |
| **RandomForest_Variance** | $1 - \max_c P(y=c)$ | 0.9384 | 0.9426 | 0.3200 |
| **Evidential_Dirichlet (Ours)** | Epistemic Uncertainty ($u_{\text{epistemic}}$) | **0.9422** | **0.9516** | **0.3583** |
| **Isolation_Forest** | One-Class Density Score | **0.9815** | **0.9823** | **0.1150** |

- **Evidential Operational Performance at Locked $\tau = 0.0648$**:
  - True Positive Rate (TPR / OOD Catch Rate): **76.67%**
  - False Positive Rate (FPR / In-Distribution False Alarms): **4.50%** (TNR = 95.50%)
  - False Acceptance Rate (FAR, missed OOD): **23.33%**

---

## 4. Subsystem Breakdown by OOD Anomaly Category

| OOD Category | Evaluated Frames | Mean $u_{\text{epistemic}}$ | Det Rate at $\tau_{\text{locked}} = 0.0648$ | Failure Diagnosis Outcome |
|---|---|---|---|---|
| **NOVEL_UNSEEN_MODE** | 150 | $1.000 \pm 0.000$ | **100.0%** | Accurately flagged `UNKNOWN_FAILURE` |
| **COMPOUND_CONCURRENT_FAULT** | 150 | $0.301 \pm 0.092$ | **100.0%** | Accurately flagged `UNKNOWN_FAILURE` |
| **EXTREME_THERMAL_INVERSION** | 150 | $0.999 \pm 0.000$ | **100.0%** | Accurately flagged `UNKNOWN_FAILURE` |
| **SENSOR_SIGN_INVERSION** | 150 | $0.057 \pm 0.027$ | **6.7%** | **FAILURE CASE**: Misdiagnosed as Known |

---

## 5. Failure Case Analysis: Architectural Blind Spot

> [!CAUTION]
> **Detailed Failure Analysis — SENSOR_SIGN_INVERSION**:
> The evidential engine detected only 6.7% of sensor polarity inversion anomalies. Investigation into `src/diagnosis/bayesian.py` (lines 76 & 78) reveals the root cause:
> ```python
> i_abs = abs(float(row.get("current_a", 2.0)))
> p_abs = abs(float(row.get("power_w", v * i_abs)))
> ```
> The upstream feature extractor intentionally took the absolute value of current and power to achieve sign-invariance across bidirectional orbital battery charge and discharge regimes. Consequently, when an instrumentation failure inverted the current sensor polarity, the absolute value mapping neutralized the anomaly signature, collapsing the Mahalanobis distance back to the nominal operating cluster ($u_{\text{epistemic}} = 0.057 < 0.0648$).
>
> **Scientific Implication**: Domain-specific feature engineering intended to improve model robustness can inadvertently create structural blind spots for novel sensor failure modes. This insight will be explicitly detailed in the manuscript.

---

## 6. Generated Artifacts

- Raw Metrics JSON: [ood_results.json](file:///Users/madanthambisetty/Downloads/SPACE%20PROJECT/evaluation/paper2/ood_results.json)
- ROC and PR Curves: [fig5_ood_roc_pr_curves.png](file:///Users/madanthambisetty/Downloads/SPACE%20PROJECT/docs/paper2/figures/fig5_ood_roc_pr_curves.png)
- Category Breakdown: [fig6_ood_subsystem_breakdown.png](file:///Users/madanthambisetty/Downloads/SPACE%20PROJECT/docs/paper2/figures/fig6_ood_subsystem_breakdown.png)
