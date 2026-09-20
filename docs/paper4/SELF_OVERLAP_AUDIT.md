# AstraHeal Paper 4 — Phase 2: Self-Overlap & Scientific Differentiation Audit

**Date**: 2026-09-13  
**Status**: COMPLETE  
**Auditor**: AstraHeal Research Group & Autonomous Systems Lab  
**Scope**: Explicit Comparative Analysis Across Papers 1, 2, 3, and 4

---

## 1. Executive Summary

This audit establishes the definitive scientific boundaries between Paper 4 and the prior three papers in the AstraHeal research program. It proves that Paper 4 does not duplicate previous work, but rather provides the necessary **system-level empirical validation** of the complete integrated architecture under repeated and perturbed operational stress.

---

## 2. Four-Paper Architectural & Research Comparison

| Dimension | Paper 1: PLAN | Paper 2: UNDERSTAND | Paper 3: CONSTRAIN | Paper 4: VALIDATE (This Work) |
| :--- | :--- | :--- | :--- | :--- |
| **Central Question** | Can counterfactual digital twins evaluate candidate actions and select Pareto-optimal recovery? | Can evidential neural networks quantify epistemic uncertainty and detect OOD spacecraft anomalies? | Can a deterministic safety governor prevent unsafe AI proposals from reaching execution? | Can the integrated system repeatedly recover across sequential faults and perturbed conditions without performance collapse? |
| **Primary Contribution** | Counterfactual lookahead branching & multi-objective action scoring. | Dirichlet-prior evidential uncertainty & epistemic anomaly separation. | Fail-closed runtime execution gatekeeper & 4-tier invariant hierarchy. | System-level multi-cycle robustness, parameter perturbation limits, and noise resilience. |
| **System Scope** | Standalone Planner & Simulator. | Standalone Diagnostic Engine. | Standalone Safety Governor. | **Fully Integrated End-to-End Pipeline** (Diag $\rightarrow$ Uncertainty $\rightarrow$ Plan $\rightarrow$ Gov $\rightarrow$ Act). |
| **Temporal Horizon** | Single fault event lookahead ($H = 300\,\text{s}$). | Static and windowed telemetry frames ($30\,\text{s}$ window). | Single proposal gating ($< 1\,\text{s}$ decision). | **Multi-Orbit Continuous Operation** ($17,220\,\text{s}$ to $28,700\,\text{s}$, $3$ to $5$ orbits). |
| **Fault Regime** | Single isolated fault injection. | Labeled nominal vs. failure mode classifications. | Adversarial & boundary synthetic proposals. | **Repeated Sequential Cascades** ($k = 1$ to $10$ cycles) and compound interactions. |
| **Environmental Disturbance** | Fixed nominal physics parameters. | Clean vs. noisy static feature vectors. | Fixed threshold boundary testing. | **Continuous Physical Perturbations** ($\pm 5\%$ to $\pm 20\%$) and additive telemetry noise. |
| **Key Metrics** | Lookahead error, Pareto trade-off, recovery latency. | Dirichlet loss, epistemic $u$, OOD AUROC, calibration error. | Unsafe execution rate ($0.00\%$), Clopper-Pearson bound, latency. | **Multi-Cycle Survival Rate, State Drift, Noise Tolerance, Graceful Degradation, Energy Integral (Wh)**. |

---

## 3. Explicit Differentiation of Novelty in Paper 4

### What is Shared (Pre-existing Infrastructure)
* The underlying 12U CubeSat EPS physics models (Thevenin ECM, orbital flux, PDU balance).
* The 5 physical invariants ($T \le 46^\circ\text{C}, V \ge 22\text{V}, I \le 40\text{A}, \text{SoC} \ge 15\%, P \le 880\,\text{W}$).
* The candidate action primitives (`ACT_NOMINAL`, `ACT_SAFE_MODE`, etc.).

### What is EXCLUSIVELY NEW to Paper 4
1. **Multi-Cycle Sequential Coupling**: Evaluates how the state resulting from recovering from Fault A affects the diagnosability, plan feasibility, and safety margins when Fault B occurs subsequently in the same mission.
2. **Physical Parameter Perturbation Sweeps**: Systematic evaluation of model mismatch: when the digital twin's physical parameters ($C_{\text{th}}, h_{\text{rad}}, R_0, \eta_{\text{solar}}$) deviate by $\pm 5\%$ to $\pm 20\%$ from nominal, how well does the system maintain stability?
3. **Telemetry Noise Degradation Curves**: Rigorous mapping of increasing Gaussian noise ($\sigma \in [0.005, 0.08]$) against epistemic uncertainty growth and recovery success.
4. **Long-Horizon Multi-Orbit State Drift**: Characterization of energy balance, Coulomb counting integration, and thermal homeostasis over 5 full LEO orbits ($28,700\,\text{s}$).
5. **End-to-End System Ablations**: Directly comparing the complete 5-stage architecture against partial variants to isolate the exact contribution of evidential uncertainty, lookahead planning, and safety gating.

---

## 4. Overlap Audit Sign-Off

Paper 4 possesses a distinct scientific thesis, unique experimental methodologies, and novel empirical evidence. It completes the logical trajectory of the AstraHeal research program without redundancy.
