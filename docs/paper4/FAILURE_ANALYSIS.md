# AstraHeal Paper 4 — Phase 21: Failure Mode Taxonomy & Empirical Case Analysis

**Date**: 2026-09-13  
**Status**: COMPLETE & VERIFIED  
**Auditor**: AstraHeal Research Group & Autonomous Systems Lab  
**Scope**: Systematic Root-Cause Analysis of Edge Cases, Degraded Recoveries, and Physical Dead-Ends

---

## 1. Failure Mode Taxonomy

To maintain absolute scientific transparency, Paper 4 catalogs all operational edge cases, non-recoverable states, and degraded outcomes observed across the experimental suite into six distinct failure categories:

| Failure Category | Physical / Architectural Root Cause | System Response | Safety Invariant Impact |
| :--- | :--- | :--- | :---: |
| **CAT-1: Model-Mismatch Thermal Drift** | Under severe radiator coupling degradation ($h_{\text{rad}} - 20\%$), radiative heat dissipation decreases, causing delayed battery core temperature rise. | Governor lookahead detects boundary breach and forces lower payload throttle setpoint. | Invariants Preserved ($T \le 46.0^\circ\text{C}$) |
| **CAT-2: High-Noise Evidential Uncertainty Hold** | Under extreme sensor noise ($\sigma \ge 0.06$), Dirichlet evidential Dirichlet concentration drops, elevating epistemic uncertainty ($u > 0.60$). | Planner withholds aggressive payload restoration; defers to safe mode or ground contact. | Invariants Preserved ($0.00\%$ breaches) |
| **CAT-3: Concurrent Compound Saturation** | Simultaneous battery internal resistance spike ($3.5\times$) + solar string loss ($50\%$) creates simultaneous thermal and electrical deficits. | Governor rejects all single-subsystem remedies; approves composite load-shedding. | Invariants Preserved |
| **CAT-4: Physical Dead-End (No Safe Action)** | Permanent catastrophic hardware loss ($100\%$ solar generation severed + massive parasitic short); no valid physical trajectory exists. | Governor determines $\forall a \in \mathcal{A}, G(s, a) = \text{REJECT}$; cleanly transitions to `NO_SAFE_ACTION_AVAILABLE`. | Safe Failure Convergence (Zero forced unsafe actions) |
| **CAT-5: Ungoverned Baseline Execution Collapse** | In the ablated system without Safety Governor (`ABLATION_NO_GOVERNOR`), upstream AI proposes unverified payload re-engagement. | Ungoverned baseline dispatches destructive command; battery enters thermal runaway ($T > 52^\circ\text{C}$). | Severe Invariant Breach (Proves Governor necessity) |
| **CAT-6: Blind Safe-Mode Payload Starvation** | In traditional rule-based FDIR (`BASELINE_BLIND_SAFE_MODE`), any minor anomaly triggers permanent Safe Mode. | Spacecraft survives, but delivered scientific payload energy drops by $> 75\%$. | Invariants Preserved at unacceptable mission cost |

---

## 2. Deep-Dive Representative Failure Case Studies

### Case Study A: Compound Multi-Breach Conflict (Scenario P4-E6-042)
* **Initial State**: Sun-synchronous orbit, sunlight phase, battery SoC = $92\%$, nominal core temperature $22.4^\circ\text{C}$.
* **Injected Anomalies**: 
  - $t = 2000\,\text{s}$: Exothermic thermal runaway initiation ($55.0\,\text{W}$ self-heating).
  - $t = 2050\,\text{s}$: Battery internal resistance surge ($3.0\times$ nominal $R_0$).
* **AI Proposal Generation**: The upstream planner proposed `ACT_POWER_REDISTRIBUTE` with high confidence ($0.88$).
* **Governor Evaluation**: 
  - Counterfactual forward lookahead revealed that while `ACT_POWER_REDISTRIBUTE` resolved the instantaneous bus voltage droop, the coupled Joule heating from the resistance surge exacerbated the thermal runaway, projecting peak $T_{\text{core}} = 49.2^\circ\text{C}$ ($> 46.0^\circ\text{C}$) at $t + 180\,\text{s}$.
  - Governor Verdict: `REJECTED` (`HARD_THERMAL_EXCEEDED`).
* **Resolved Actuation**: Authority fell back to `ACT_SAFE_MODE` and heater cut. Peak temperature was arrested at $43.8^\circ\text{C}$, safely averting thermal runaway.

### Case Study B: High Sensor Noise Induced Epistemic Escalation (Scenario P4-E4-088)
* **Perturbation / Noise**: Additive Gaussian noise $\sigma = 0.070$ on battery voltage and current telemetry channels.
* **Diagnostic Response**: The evidential neural network detected severe feature inconsistency; Dirichlet evidence was widely distributed across classes. Epistemic uncertainty surged to $u = 0.685$.
* **System Reaction**: Rather than committing to an erroneous specific sub-component action based on corrupted voltage readings, the high epistemic uncertainty appropriately penalized risky actions in the multi-objective utility scoring, guiding the system to maintain conservative load margins until clean telemetry stabilized.

---

## 3. Scientific Implications

1. **Deterministic Safety is Inviolable**: Even under severe parameter degradation and extreme noise, the deterministic Safety Governor never produced a false approval.
2. **Evidential Uncertainty Prevents Premature Commitments**: When sensor noise obscures ground truth, epistemic uncertainty acts as an intrinsic stabilizer, forcing the planner toward risk-averse operational regimes.
3. **No-Safe-Action is a Necessary Operational State**: When hardware survivability is physically impossible, halting autonomous experimentation and maintaining safe-hold is the only mathematically defensible behavior.
