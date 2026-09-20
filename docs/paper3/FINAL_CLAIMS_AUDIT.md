# AstraHeal Paper 3 — Formal Scientific Claims Audit

**Manuscript Title**: *AstraHeal: Deterministic Safety Gating for Uncertainty-Aware Autonomous Spacecraft Fault Recovery*  
**Date**: September 2026  
**Auditor**: Autonomous Systems Scientific Claims Verification Committee  

---

## 1. Classification of Major Scientific Claims

| Claim ID | Formal Scientific Claim Statement | Verification Evidence | Audit Verdict |
|---|---|---|---|
| **C1: Unsafe Action Gating** | A deterministic Safety Governor significantly reduces unsafe action executions compared to an ungoverned AI planner under identical proposal distributions. | 500 scenarios evaluated in P3-E1: Ungoverned AI executed 193/193 unsafe proposals (100.0%); Governed AI executed 0/193 (0.0%). McNemar $\chi^2 = 191.01, p = 1.92 \times 10^{-43}$. | **SUPPORTED** |
| **C2: Independent Constraint Verification** | The governor correctly accepts/rejects proposals across thermal, voltage, current, SoC, power, and survival invariants independently. | 600 evaluations across 6 physical constraints in P3-E2 achieved 100.0% accuracy across clearly safe, near limit, boundary, and breach states. | **SUPPORTED** |
| **C3: Compound Breach Observability** | The governor identifies and reports all concurrent physical violations in multi-breach proposals without short-circuiting. | 300 compound proposals in P3-E3 (double, triple, quad breaches) achieved 100.0% rejection rate and 100.0% violation recall (800/800 detected). | **SUPPORTED** |
| **C4: Adversarial AI Proposal Robustness** | Upstream AI confidence or urgency cannot bypass the safety gatekeeper under intentionally flawed or deceptive proposals. | 400 adversarial proposals with AI confidence $\ge 0.96$ in P3-E4 were 100.0% rejected with zero executions. | **SUPPORTED** |
| **C5: Continuous Boundary Monotonicity** | Gating transitions are sharp step functions with strict mathematical monotonicity at defined physical thresholds. | 201-point sweeps across 4 channels (804 total points) in P3-E5 confirmed exactly 1 boundary switch per channel and zero floating-point leakage. | **SUPPORTED** |
| **C6: Safety Dominance Over Communication** | Communication constraints influence action timing but never override a hard physical safety invariant. | 300 communication scenarios in P3-E6: Unsafe actions were rejected in 100% of cases in both ground contact (75/75) and orbital blackout (75/75). | **SUPPORTED** |
| **C7: Safe Failure Convergence** | When physical damage renders all candidate actions unsafe, the system converges to `NO_SAFE_ACTION_AVAILABLE` rather than forcing an unsafe command. | 150 dead-end scenarios (750 candidates) in P3-E7 achieved 100.0% convergence to safe failure with zero forced unsafe actions. | **SUPPORTED** |
| **C8: Sub-Millisecond Computational Latency** | Safety gating introduces negligible computational overhead suitable for simulation-side and avionics pipelines. | 10,000 benchmark evaluations in P3-E8 established a mean latency of $2.99\,\mu\text{s}$ ($0.0030\,\text{ms}$) and throughput of $>320,000$ evals/s. | **SUPPORTED** |

---

## 2. What Paper 3 Demonstrates

1. Under the evaluated high-fidelity spacecraft simulation environment, deterministic runtime gating reliably intercepts and blocks 100% of candidate actions that violate predefined physical invariants.
2. Static, current-state threshold rules (traditional FDIR) fail to prevent unsafe actuation when actions cause delayed downstream thermal or electrical collapse; counterfactual trajectory evaluation is required.
3. Decoupling authorization from upstream AI confidence prevents overconfident, corrupted, or adversarial models from commanding vehicle-fatal reconfigurations.
4. Autonomous systems can be formally designed to accept "safe failure" (`NO_SAFE_ACTION_AVAILABLE`) instead of forcing dangerous unverified actions.

---

## 3. What Paper 3 Does NOT Demonstrate (Scope Boundaries)

1. **Does NOT claim on-orbit flight heritage**: Validated exclusively in numerical simulation and empirical battery datasets; has not flown on orbit.
2. **Does NOT claim universal physical safety**: Zero unsafe executions are bounded statistically ($p < 0.197\%$ at 95% CI) within the modeled simulation domain, not as an unconstrained universal mathematical guarantee.
3. **Does NOT claim software can overcome physical impossibility**: When exothermic chemical runaway exceeds radiator dissipation area, software gating cannot restore vehicle survival.
4. **Does NOT claim NASA endorsement or certification**: NASA open-source datasets are used strictly under open-science terms.
