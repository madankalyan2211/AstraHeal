# AstraHeal Paper 2 — Study 2: Epistemic vs. Aleatoric Uncertainty Disentanglement

**Experiment Identifier**: `EXP-P2-02`  
**Artifact**: `evaluation/paper2/uncertainty_results.json`  
**Date**: 2026  
**Status**: Executed & Verified (Phase 5 Complete)

---

## 1. Research Question & Hypothesis

> **Research Question**: Does the evidential formulation provide genuine physical disentanglement between epistemic uncertainty (model ignorance / OOD) and aleatoric uncertainty (data noise / telemetry entropy)?

- **Hypothesis (H2)**: Epistemic uncertainty ($u_{\text{epistemic}}$) will exhibit significant separation between in-distribution ($u_{\text{epistemic}} \le 0.10$) and novel out-of-distribution regimes ($u_{\text{epistemic}} \ge 0.50$). Aleatoric uncertainty ($u_{\text{aleatoric}}$) will scale with telemetry observation noise and hypothesis entropy, without falsely triggering OOD alarms under sensor noise.

---

## 2. Experimental Setup

- **Regimes Evaluated** ($N = 1,400$ total telemetry frames, 200 per regime):
  1. `Regime A (Clean Familiar)`: In-distribution known faults with zero noise ($\sigma = 0.00$).
  2. `Regime B1 (Low Noise)`: In-distribution known faults with $\sigma = 0.05$.
  3. `Regime B2 (Medium Noise)`: In-distribution known faults with $\sigma = 0.10$.
  4. `Regime B3 (High Noise)`: In-distribution known faults with $\sigma = 0.20$.
  5. `Regime C (Novel Unseen)`: Catastrophic 500W power bus short-circuit ($V < 12\text{V}$, transient $dV/dt < -5\text{V/s}$).
  6. `Regime D (Compound Fault)`: Concurrent solar array string loss (50%) and exothermic thermal runaway (65W heat injection).
  7. `Regime E (Extreme Domain Shift)`: Cryogenic deep freeze ($-52^\circ\text{C}$) and sensor polarity sign inversions.

---

## 3. Empirical Results Across Operational Regimes

| Operational Regime | Noise ($\sigma$) | Ground Truth Type | Diagnosis Accuracy | Epistemic ($u_{\text{epistemic}}$) | Aleatoric ($u_{\text{aleatoric}}$) |
|---|---|---|---|---|---|
| **Regime A (Clean Familiar)** | 0.00 | Known (ID) | 0.950 | $0.039 \pm 0.016$ | $0.085 \pm 0.055$ |
| **Regime B1 (Low Noise)** | 0.05 | Known (ID) | 0.850 | $0.043 \pm 0.018$ | $0.114 \pm 0.098$ |
| **Regime B2 (Med Noise)** | 0.10 | Known (ID) | 0.845 | $0.049 \pm 0.023$ | $0.146 \pm 0.131$ |
| **Regime B3 (High Noise)** | 0.20 | Known (ID) | 0.740 | $0.092 \pm 0.071$ | $0.194 \pm 0.146$ |
| **Regime C (Novel Unseen)** | 0.01 | Novel (OOD) | 1.000 | **$1.000 \pm 0.000$** | $0.573 \pm 0.006$ |
| **Regime D (Compound Fault)** | 0.01 | Compound (OOD) | 0.090 | **$0.303 \pm 0.099$** | $0.120 \pm 0.060$ |
| **Regime E (Extreme Shift)** | 0.01 | Shift (OOD) | 0.500 | **$0.528 \pm 0.471$** | $0.379 \pm 0.281$ |

---

## 4. Disentanglement Statistics & Correlation Analysis

- **Epistemic Separation Factor**: OOD regimes produced an average epistemic uncertainty **10.94x higher** than clean in-distribution data ($\mathbb{E}[u_{\text{epistemic}}^{\text{OOD}}] = 0.610$ vs. $\mathbb{E}[u_{\text{epistemic}}^{\text{ID}}] = 0.056$).
- **Noise Sensitivity**:
  - Noise vs. Aleatoric Correlation: $\rho_{\text{Spearman}} = 0.2955$ ($p = 1.37 \times 10^{-17}$), confirming aleatoric uncertainty systematically expands under noisy measurement channels.
  - Noise vs. Epistemic Gating: Epistemic uncertainty remained tightly bounded below the $0.45$ safety gating threshold even under severe $\sigma = 0.20$ noise ($u_{\text{epistemic}} = 0.092 \ll 0.45$), successfully preventing false OOD trips from sensor jitter alone.

---

## 5. Critical Scientific Finding: The Compound Fault Dilemma

> [!WARNING]
> **Compound Fault Boundary Effect**: In `Regime D (Compound Fault)`, simultaneous solar array loss + thermal runaway resulted in a mean epistemic uncertainty of $0.303 \pm 0.099$. Because each component fault pulled the feature vector partially toward its respective known centroid, the composite Mahalanobis distance fell into an intermediate valley below the hard $0.45$ threshold. Consequently, only 9.0% of compound frames were flagged as `UNKNOWN_FAILURE` at $\tau = 0.45$; the remainder were misdiagnosed as standard `SOLAR_ARRAY_STRING_FAULT` with moderate confidence.
>
> This demonstrates an essential theoretical limit: **Evidential centroid distance in metric space can experience partial cancellation when opposing fault signatures superpositionally interfere**, requiring joint multi-label hypothesis testing rather than single-point centroid gating.

---

## 6. Generated Artifacts

- Raw Uncertainty JSON: [uncertainty_results.json](file:///Users/madanthambisetty/Downloads/SPACE%20PROJECT/evaluation/paper2/uncertainty_results.json)
- Bivariate Scatter Plot: [fig3_uncertainty_disentanglement.png](file:///Users/madanthambisetty/Downloads/SPACE%20PROJECT/docs/paper2/figures/fig3_uncertainty_disentanglement.png)
- Noise Scaling Trajectory: [fig4_uncertainty_vs_noise.png](file:///Users/madanthambisetty/Downloads/SPACE%20PROJECT/docs/paper2/figures/fig4_uncertainty_vs_noise.png)
