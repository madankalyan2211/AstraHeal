# AstraHeal Paper 3 — Self-Overlap & Multi-Paper Differentiation Audit

**Manuscript Title**: *AstraHeal: Deterministic Safety Gating for Uncertainty-Aware Autonomous Spacecraft Fault Recovery*  
**Date**: September 2026  
**Auditor**: Academic Integrity & Publication Disentanglement Panel  

---

## 1. Architectural Disentanglement Across the AstraHeal Series

To prevent self-plagiarism, double-dipping, or redundant publishing, each paper in the AstraHeal research series addresses a distinct layer of the spacecraft autonomy stack:

```
[ Telemetry Stream ]
         │
         ▼
[ Paper 2: Diagnostic Core ]  ──► Evidential Bayesian Dirichlet Inference (Epistemic vs Aleatoric Uncertainty)
         │
         ▼
[ Paper 1: Planning Engine ]  ──► Zero-Mutation Digital Twin Counterfactual Tree Search & Horizon Optimization
         │
         ▼
[ Paper 3: Safety Governor ]  ──► Deterministic Gating, Invariant Admissibility & Fail-Closed Execution Barrier
         │
         ▼
[ Command Execution ]
```

---

## 2. Dimensional Comparison Matrix

| Research Dimension | Paper 1 (Foundations & Planning) | Paper 2 (Diagnostic Uncertainty) | Paper 3 (Runtime Safety Assurance) |
|---|---|---|---|
| **Core Research Question** | Can a spacecraft autonomously evaluate alternative recovery trajectories during communication blackout? | Can evidential AI distinguish known faults from novel OOD anomalies with calibrated uncertainty? | Can a deterministic safety governor reliably prevent unsafe AI recovery actions from reaching execution? |
| **Primary Object of Study** | Counterfactual lookahead simulation tree | Dirichlet evidential output layer & Mahalanobis metric | Deterministic safety gatekeeper & physical invariants |
| **Key Mathematical Tools** | State cloning, differential equations of EPS kinetics | Dirichlet distribution, mutual information, ECE calibration | Invariant mapping $G(s,a) \in \{\text{ACCEPT}, \text{REJECT}\}$, Wilson bounds, McNemar test |
| **Primary Experiments** | Experiments 01–15 (LEO orbit cycles, parameter mismatch) | Experiments EXP-P2-01 to 05 (OOD, noise sweeps, ablation) | Experiments P3-E1 to P3-E8 (Adversarial proposals, boundaries, dead-ends) |
| **Primary Metrics** | Delivered Payload (Wh), Survival Rate, Parameter MAE | Macro-F1 (0.9533), ECE (0.0094), OOD AUROC (0.9422) | Unsafe Execution Rate (0.00%), FAR (0.00%), Latency (2.99 µs) |
| **Scope Boundary** | Lookahead planning capability | Diagnostic and uncertainty isolation | Action execution authorization |

---

## 3. Textual & Codebase Overlap Verification

* **Prose Overlap**: Zero verbatim paragraphs shared with Paper 1 or Paper 2. All introduction, problem formulation, methodology, and discussion sections are written independently.
* **Codebase Separation**:
  - Paper 1 lives in frozen `src/planner/`, `src/digital_twin/`, `src/safety/` (v1.0).
  - Paper 2 lives in isolated `experiments/paper2/`, `docs/paper2/`, `evaluation/paper2/`.
  - Paper 3 lives strictly in isolated `experiments/paper3/`, `docs/paper3/`, `evaluation/paper3/`, `tests/paper3/`.
* **Zero Modification Rule**: Certified that zero lines of code in AstraHeal v1.0 or Paper 2 were altered.
