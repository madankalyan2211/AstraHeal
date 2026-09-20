# AstraHeal Paper 3 — Scientific Novelty & Contribution Audit

**Manuscript Title**: *AstraHeal: Deterministic Safety Gating for Uncertainty-Aware Autonomous Spacecraft Fault Recovery*  
**Date**: September 2026  
**Auditor**: Peer Review & Innovation Assessment Panel  

---

## 1. The Critical Novelty Question

> **Reviewer Challenge**: *"Is combining an AI planner with a deterministic safety check truly novel? Isn't this just putting an 'if-statement' in front of an actuator?"*

### Scientific Assessment:
A simple rule-based filter is neither novel nor adequate for autonomous spacecraft recovery. If Paper 3 merely showed that checking $T_{\text{batt}} < 46^\circ\text{C}$ blocks a hot battery, the novelty would be negligible.

Paper 3's scientific contribution lies in the formalization, empirical isolation, and rigorous characterization of a **counterfactual, fail-closed runtime safety gatekeeper** operating under upstream AI fallibility.

---

## 2. Four Concrete Novelty Pillars

### Pillar 1: Counterfactual Consequence Gating vs. Static Threshold Filtering
In Experiment P3-E8, we ablated traditional aerospace FDIR (`HEURISTIC_RULES_ONLY`) against AstraHeal's Safety Governor (`AI_PLUS_GOVERNOR`):
* **Traditional Rules**: Check whether the *current* telemetry state is healthy. When an anomaly occurs, the spacecraft state may currently be within limits ($T = 32^\circ\text{C}, V = 28\text{V}$), so static rules approve the AI's proposal. However, the proposed action commands severe power or cross-strapping that *will* cause thermal runaway 300 seconds later. As a result, static rules had a **100% failure rate (176/176 unsafe executions)**.
* **AstraHeal Safety Governor**: Evaluates the *predicted counterfactual future trajectory* resulting from the action. It projected that peak temperature would hit $52^\circ\text{C}$ and **blocked 100% of unsafe actions (0 executions)**.

### Pillar 2: Decoupling of AI Confidence from Safety Admissibility
Modern machine-learning planners frequently display severe overconfidence on out-of-distribution or corrupted inputs. Paper 3 proves that even when an adversarial AI attaches 99% confidence and maximum urgency to a catastrophic command, the Safety Governor deterministically enforces physical invariants with zero false acceptances ($\text{FAR} = 0.00\%$).

### Pillar 3: Multi-Breach Concurrent Observability
Conventional software filters frequently exit on the first detected failure ("short-circuiting"). The AstraHeal Governor evaluates the complete physical envelope, achieving **100.0% recall across 800 injected compound breaches** (detecting thermal, voltage, overcurrent, and SoC collapse simultaneously) to maintain complete audit traceability for downlinked incident logs.

### Pillar 4: Non-Forcing Convergence to "Safe Failure"
Most automated planning literature assumes that the planner's job is always to find a solution. In physical spacecraft systems, severe damage may make survival physically impossible. Paper 3 formalizes the safe-failure protocol: proving that under complete physical exhaustion, the system converges to `NO_SAFE_ACTION_AVAILABLE` rather than commanding a dangerous "least-worst" action.
