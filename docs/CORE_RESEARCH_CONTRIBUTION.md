# AstraHeal — Core Research Contribution Statement

**Project Version**: `AstraHeal v1.0 — Research Release`  
**Date**: 2026-08-31  

---

## 1. Central Research Contribution

> **AstraHeal is an uncertainty-aware autonomous spacecraft fault-management architecture that combines Dirichlet evidential uncertainty estimation, a non-mutating digital twin, counterfactual lookahead action evaluation, communication-aware arbitration, and deterministic safety gating.**

---

## 2. What AstraHeal Demonstrates vs What It Does Not

### **DEMONSTRATED (Empirically Supported in Numerical Simulation):**
1. **Multivariate Anomaly Detection**: 0.974 AUROC with 0–30s latency on abrupt and drift telemetry faults.
2. **Evidential Fault Diagnosis**: Dirichlet Bayesian inference classifying failure modes while explicitly separating Epistemic ($u_{epistemic}$) from Aleatoric ($u_{aleatoric}$) uncertainty.
3. **Out-of-Distribution Safety Gating**: 100% detection of novel compound faults ($u_{epistemic} \ge 0.79$), reliably commanding safe standby abstention.
4. **Zero-Leakage Counterfactual Simulation**: Cloned digital twin state branches simulating candidate trajectories over 3000s lookahead horizons with 0% state vector mutation on the active spacecraft.
5. **Deterministic Physical Safety Enforcement**: 609 unsafe candidate proposals blocked across stress benchmarks with **0 executed unsafe actions** and **0 Safety Governor bypasses**.
6. **Communication-Aware Autonomy**: Correctly arbitrates between immediate autonomous execution during ground occultation blackouts and deferring non-critical anomalies to upcoming ground passes.
7. **Multi-Cycle Autonomous Recovery**: 122 discrete recovery cycles logged across 3 full LEO orbits without single-trigger lockup.
8. **Trajectory Prediction Accuracy under Perturbed Physics**: Sub-degree thermal error (MAE = $0.642^\circ\text{C}$) and sub-volt electrical error (MAE = $0.415\text{V}$) across 20 held-out scenarios under parameter mismatch, yielding **95.0% Top-2 action selection accuracy**.

---

### **NOT DEMONSTRATED (Documented Boundaries & Future Work):**
1. **Improved Survival Against Physically Unrecoverable Faults**: Software autonomy cannot prevent loss when physical deficits (such as exothermic runaway heat exceeding radiator dissipation area, $Q_{exo} > 65\text{W}$) render survival physically impossible.
2. **Real Spacecraft Flight Heritage**: Has not flown on an operational orbital mission.
3. **Hardware-in-the-Loop (HIL) Testbed Validation**: Validated extensively in simulation; has not yet been deployed to physical flight avionics coupled with real Li-ion cells in a Thermal Vacuum Chamber (TVAC).
4. **3D Spatial Thermal Gradient Conduction**: Employs a lumped single-node thermal mass model rather than 3D finite-element spatial thermal conduction.
5. **NASA Partnership or Endorsement**: Independent academic research platform with no official agency endorsement.
