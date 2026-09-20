# AstraHeal Paper 3 — Failure-Case Analysis & Physical Operational Boundaries

**Manuscript Title**: *AstraHeal: Deterministic Safety Gating for Uncertainty-Aware Autonomous Spacecraft Fault Recovery*  
**Date**: September 2026  
**Auditor**: Spacecraft Autonomy & Verification Group  

---

## 1. Scientific Philosophy on Failure Analysis

A core tenet of rigorous autonomous systems engineering is that **a safety system must not claim omnipotence**. In real spaceflight operations, physical anomalies can arise where no software command can restore spacecraft equilibrium. 

Documenting where autonomous safety gating succeeds, where it must fail closed, and where physical limits prevent recovery is essential for scientific integrity and flight safety.

---

## 2. Failure Case Taxonomy

| Failure Category | Evaluated Conditions | Governor Behavior & Response | Flight Safety Consequence |
|---|---|---|---|
| **FC-1: Severe Exothermic Thermal Runaway** | Internal chemical heat generation $Q_{\text{exo}} > 65\text{W}$ exceeds radiator dissipation area. | All candidates predict $T_{\text{batt}} > 46^\circ\text{C}$. Governor rejects all candidates $\to$ `NO_SAFE_ACTION_AVAILABLE`. | Safe failure convergence. Prevents software from commanding futile or damaging cycles; alerts vehicle to persist telemetry until fatal loss. |
| **FC-2: Catastrophic Bus Short Circuit** | Hardware short pulls bus voltage down to $<12\text{V}$ instantly. | All candidate configurations fail undervoltage floor ($V_{\text{bus}} < 22\text{V}$) $\to$ `NO_SAFE_ACTION_AVAILABLE`. | Software does not attempt to power payloads on a collapsed bus, protecting remaining avionics. |
| **FC-3: Telemetry Stream Corruption** | Single-event upset (SEU) corrupts sensor registers to `NaN` or `Inf`. | Gatekeeper triggers fail-closed validator $\to$ `FAIL_CLOSED_CORRUPTED_TELEMETRY`. | Command dispatch inhibited; vehicle falls back to passive safe standby rather than acting on garbage data. |
| **FC-4: Uncertified Ground / AI Action Code** | AI proposal generates hallucinated actuation string (e.g. `FIRE_PROPULSION_THRUSTER`). | Catalog membership validator checks certified flight list $\to$ `FAIL_CLOSED_UNCERTIFIED_ACTION_TYPE`. | Protects PDU avionics against unverified commands. |
| **FC-5: Communication Latency Mismatch** | Urgent failure onset ($T_{\text{crit}} < 150\text{s}$) occurring during marginal ground pass window. | Communication manager arbitrates to immediate onboard execution (`ACT_AUTONOMOUSLY`) because ground reaction budget exceeds time to loss. | Averts loss when waiting for human-in-the-loop review would be fatal. |

---

## 3. The "No Safe Action" Physical Regimes (Experiment P3-E7)

In Experiment P3-E7, we evaluated 150 dead-end physical scenarios (750 candidate action evaluations) where severe hardware damage rendered every candidate proposal unsafe.

### Verified Findings
* **Candidate Actions Evaluated**: 750
* **Candidate Actions Approved**: **0 (0.0%)**
* **Candidate Actions Rejected**: **750 (100.0%)**
* **Convergence to `NO_SAFE_ACTION_AVAILABLE`**: **150 / 150 scenarios (100.0%)**
* **Forced Unsafe Actions**: **0 (0.0%)**

### Engineering Significance
In inferior autonomous architectures, planners forced to return an action will select the "least bad" action—for instance, choosing a candidate that exceeds battery temperature by "only" 2°C. In lithium-ion space batteries, exceeding 46°C triggers irreversible exothermic cell decomposition. The AstraHeal Safety Governor strictly refuses to compromise hard invariants, returning an explicit safe-failure declaration instead of commanding catastrophic actions.
