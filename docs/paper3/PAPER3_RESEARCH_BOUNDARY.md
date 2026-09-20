# AstraHeal Paper 3 — Research Boundary & Scope Specification

**Title**: *AstraHeal: Deterministic Safety Gating for Uncertainty-Aware Autonomous Spacecraft Fault Recovery*  
**Research Series**: Paper 3 (Autonomous Aerospace Systems & Runtime Safety Assurance)  
**Status**: Formal Research Specification & Boundary Lock  
**Date**: September 2026  

---

## 1. Central Research Question

> **Can a deterministic safety governor reliably prevent unsafe autonomous spacecraft recovery actions proposed by an AI-based fault-management system from reaching execution, including under uncertain, incorrect, or deliberately unsafe upstream proposals?**

This paper is **not** primarily about diagnostic classification (the domain of Paper 2), nor is it primarily about generating multi-branch counterfactual trajectories (the domain of Paper 1). Paper 3 isolates and evaluates the **authoritative safety barrier** situated immediately prior to command execution on spacecraft flight avionics:

$$\textbf{The AI proposes; the Deterministic Safety Governor disposes.}$$

---

## 2. Scientific Motivation & Research Gap

1. **The Fallibility of Modern Aerospace AI**: Deep learning, probabilistic evidential reasoning, and reinforcement learning planners increasingly offer high operational utility for spacecraft anomaly response. However, machine-learning models cannot offer hard, mathematically verifiable guarantees: they can become overconfident, hallucinate invalid actuation parameters, or misclassify unfamiliar compound failures.
2. **The Problem of Direct Execution**: In traditional ground-in-the-loop operations, human flight controllers act as the deterministic filter. Under communication blackouts or deep-space latency, autonomous onboard systems risk commanding unvalidated actions directly to actuators, Power Distribution Units (PDUs), or attitude control systems.
3. **The Research Gap**: Prior aerospace literature largely treats safety filters either as informal heuristics embedded inside planners or as rigid rule-based FDIR that preemptively triggers Safe Mode. Missing is a formal empirical evaluation of an **independent, deterministic, fail-closed runtime safety governor** that intercepts arbitrary upstream AI proposals, rigorously validates them against physical invariants across continuous state boundaries, and safely commands `NO_SAFE_ACTION_AVAILABLE` when physical survival constraints cannot be satisfied.

---

## 3. Formal Research Hypotheses

* **Hypothesis 1 (H1 — Execution Reduction)**: A deterministic Safety Governor significantly reduces unsafe action execution compared with an otherwise identical recovery system without deterministic gating.
* **Hypothesis 2 (H2 — Constraint Verification)**: The Safety Governor correctly rejects recovery actions that violate predefined hard spacecraft safety constraints (thermal, voltage, overcurrent, battery reserve, state validity).
* **Hypothesis 3 (H3 — Adversarial Robustness)**: The Safety Governor maintains zero unsafe executions even when presented with deliberately incorrect, flawed, or overconfident upstream AI proposals.
* **Hypothesis 4 (H4 — Boundary Consistency)**: Safety gating decisions remain strictly monotonic and consistent near defined continuous constraint thresholds without discontinuity or floating-point leakage.
* **Hypothesis 5 (H5 — Safety Dominance over Communication)**: Communication-aware arbitration influences action selection and downlink timing without ever overriding a hard physical safety violation.
* **Hypothesis 6 (H6 — Safe Failure Convergence)**: When physical damage or environmental extremes eliminate all valid recovery candidates, the system safely enters a verified `NO_SAFE_ACTION_AVAILABLE` state rather than forcing an unsafe or unverified action.

---

## 4. Core Scientific Contributions

1. **Deterministic Action Admissibility**: A mathematically formal, deterministic execution gatekeeper evaluating candidate recovery actions against multi-domain physical spacecraft invariants.
2. **AI-Independent Safety Barrier**: Complete decoupling of execution authorization from upstream AI confidence, epistemic uncertainty, or planner scores.
3. **Empirical Unsafe-Action Rejection Suite**: Controlled evaluation across 8 experiments and thousands of simulated anomaly frames demonstrating $0.00\%$ unsafe action execution under defined simulation bounds.
4. **Formal Safe-Failure Protocol**: Explicit identification and handling of physical unrecoverability, eliminating the dangerous assumption that autonomous recovery is always possible.

---

## 5. Architectural Safety Hierarchy

Paper 3 formalizes a strict 4-level priority hierarchy where higher levels strictly dominate lower levels:

| Priority Level | Architectural Component | Authorization Authority & Behavior |
|---|---|---|
| **Level 1** | **Hard Physical Safety Constraints** | **Non-negotiable.** Evaluates battery temperature ($T_{\text{batt}} \le 46^\circ\text{C}$), bus voltage ($V_{\text{bus}} \ge 22\text{V}$), PDU current ($I_{\text{batt}} \le 40\text{A}$), state of charge ($\text{SoC} \ge 15\%$), and state validity. Any single breach mandates immediate `REJECT`. |
| **Level 2** | **Communication Constraints** | Arbitrates between immediate execution and ground handoff based on ground station passes and time-to-criticality. **Cannot override Level 1.** |
| **Level 3** | **Mission Recovery Utility** | Evaluates secondary performance (payload preservation, energy margin, reversibility) strictly among Level 1 approved candidates. |
| **Level 4** | **AI / Planner Preference** | Upstream heuristic ranking. AI confidence cannot authorize an action rejected by Level 1 or 2. |

---

## 6. Repository Inventory & Reusability Audit

### Existing Frozen Components (AstraHeal v1.0 — Strictly Read-Only)
- `src/safety/safety_governor.py`: Contains initial `DeterministicSafetyGovernor` class enforcing 5 default hard constraints.
- `src/planner/actions.py`: Standard catalog of 7 spacecraft EPS recovery actions.
- `src/planner/counterfactual.py`: Parallel digital-twin branch evaluator.
- `src/communication/manager.py`: Communication-aware autonomy arbitrator.
- `data/` & `tests/`: 35 baseline unit tests and NASA Ames PCoE battery dataset.

### Reusable Across Research Series
- Spacecraft EPS physical model parameters (GaAs solar array, lithium-ion battery, PDU bus, lumped thermal capacitance).
- Telemetry feature representations ($dV/dt, dT/dt, R_{\text{int}}$).

### New Independent Components for Paper 3 (Isolated Namespace)
- `experiments/paper3/common.py`: Dedicated Paper 3 testbench, adversarial proposal injectors, continuous boundary sweep generators, fail-closed state validators, and safety metrics engines.
- `experiments/paper3/01_baseline_safety_enforcement.py` through `08_safety_governor_ablation.py`: 8 controlled empirical experiments.
- `evaluation/paper3/*.json`: Machine-readable results and raw proposal-level records.
- `tests/paper3/`: Dedicated unit and safety invariant test suite.
- `docs/paper3/`: Complete research audits, experiment plan, provenance tracking, and LaTeX publication package.

---

## 7. Explicit Research Boundaries & Non-Claims

To preserve scientific integrity, Paper 3 explicitly states what it **does not** claim:
* **No Claim of Flight Heritage**: Evaluated in high-fidelity Python simulation and empirical NASA datasets; has not flown on orbit.
* **No Universal Safety Proof**: Zero unsafe executions are certified strictly *within the evaluated simulation scenarios and defined constraint models*, not as a universal mathematical proof covering unmodeled physics.
* **No Unrecoverable Hardware Invariance**: Software safety gating cannot prevent spacecraft loss when physical thermal runaway or irreversible battery cell shorting has already progressed past physical dissipation limits.
* **No NASA Partnership / Endorsement**: NASA PCoE datasets are used under public open-science terms; NASA does not sponsor or endorse this research.
