# AstraHeal Paper 4 — Phase 4: Literature & Scientific Novelty Audit

**Date**: 2026-09-13  
**Status**: COMPLETE  
**Auditor**: AstraHeal Research Group & Autonomous Systems Lab  
**Scope**: Aerospace Autonomy, Runtime Assurance, Fault Recovery, and Robustness Literature

---

## 1. Literature Baseline Review

### A. Classical Spacecraft Autonomous FDIR
* **Remote Agent Experiment (Deep Space 1)**: Demonstrated model-based propositional reasoning and procedural replanning (Muscettola et al., 1998). *Limitation*: Relied on discrete qualitative states; could not continuously model coupled electro-thermal differential kinetics under parameter drift.
* **Autonomous Sciencecraft Experiment (EO-1)**: Demonstrated onboard automated cloud detection and observation scheduling (Chien et al., 2005). *Limitation*: Focused on science planning rather than electrical power system survival and closed-loop physical invariant enforcement.
* **Livingstone & Model-Based Diagnosis**: Qualitative constraint-satisfaction FDIR (Williams & Nayak, 1996). *Limitation*: Highly sensitive to exact symbolic rule coverage; vulnerable to unknown out-of-distribution physical degradation.

### B. Machine Learning & Neural FDIR
* **Deep Learning for Spacecraft Telemetry**: Anomaly detection using LSTMs, VAEs, and transformers (Hundman et al., 2018; Blázquez-García et al., 2021). *Limitation*: Primarily passive alarms; does not execute autonomous recovery planning or closed-loop actuation.
* **Deep Reinforcement Learning for EPS Management**: RL policies for battery scheduling and power distribution. *Limitation*: Black-box neural policies lack formal safety guarantees; can command catastrophic actuations under sensor corruption or distribution shifts.

### C. Runtime Assurance & Safety Shielding
* **Simplex Architecture & ASTM F3269-17**: Reverts authority to a certified backup controller upon invariant breach (Sha, 2001).
* **Control Barrier Functions (CBFs)**: Enforce forward invariance in continuous control (Ames et al., 2016).
* **Safety Shielding in RL**: Post-hoc temporal logic verification (Alshiekh et al., 2018).

---

## 2. Identified Research Gap

> **The Empirical System-Level Robustness Gap in Aerospace AI**:
> Existing aerospace literature evaluates autonomous fault management almost exclusively under **isolated, single-event benchmarks with idealized nominal physics and clean telemetry**. In real orbital missions, spacecraft encounter:
> 1. Cascading or repeated anomalies across multiple orbits where post-recovery states alter subsequent system headroom;
> 2. Model mismatch between flight software physics estimates and aging hardware (e.g., cell impedance degradation, thermal radiator coating darkening);
> 3. Additive sensor noise and calibration drift.
> 
> There is an acute lack of rigorous empirical research evaluating whether an **uncertainty-aware, safety-gated autonomous architecture** remains stable, non-degrading, and strictly safe across repeated recovery cycles under perturbed physical dynamics.

---

## 3. Paper 4 Novelty Claim Formulation

Paper 4 directly bridges this research gap by providing:
1. **The First End-to-End Multi-Cycle Evaluation** of an uncertainty-aware, safety-gated autonomous EPS recovery architecture across continuous multi-orbit LEO missions ($17,220\,\text{s}$ to $28,700\,\text{s}$).
2. **Empirical Quantification of Parameter Perturbation Tolerance**: Systematically measuring performance boundaries across $\pm 5\%$ to $\pm 20\%$ deviations in thermal mass, radiator emissivity, internal cell resistance, and solar string efficiency.
3. **Telemetry Noise Degradation Boundaries**: Demonstrating how Dirichlet evidential epistemic uncertainty reacts to escalating sensor noise ($\sigma = 0.005$ to $0.08$), preventing premature or misdirected recovery actions.
4. **Validation of Multi-Cycle Fail-Closed Invariant Preservation**: Demonstrating that repeated sequential cycles do not erode or bypass the deterministic Safety Governor's zero-unsafe-execution guarantee ($0.00\%$).
