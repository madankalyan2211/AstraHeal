# AstraHeal Paper 3 — Comprehensive Scientific Experiment Plan

**Manuscript Title**: *AstraHeal: Deterministic Safety Gating for Uncertainty-Aware Autonomous Spacecraft Fault Recovery*  
**Scope**: Experimental Methodology, Scenario Design, Hypotheses Mapping, and Execution Pipeline  
**Date**: September 2026  

---

## 1. Experimental Overview

Paper 3 provides the first isolated, empirical evaluation of an autonomous runtime Safety Governor acting as the final, immutable gatekeeper between upstream AI action proposals and flight command dispatch.

The evaluation is structured into eight controlled experiments (P3-E1 through P3-E8), accompanied by adversarial injection, fail-closed stress testing, and computational overhead measurements.

```
       [ Upstream AI Proposal ]  ──► (Action Candidate + Confidence)
                  │
                  ▼
   ┌───────────────────────────────┐
   │  DETERMINISTIC SAFETY GATES   │
   │                               │
   │  Gate 1: State Validity Check │ (Fail closed on NaN / Inf / Missing)
   │  Gate 2: Thermal Barrier      │ (T_batt <= 46.0°C)
   │  Gate 3: Undervoltage Floor   │ (V_bus >= 22.0V)
   │  Gate 4: Overcurrent Limit    │ (I_batt <= 40.0A)
   │  Gate 5: Battery Reserve Floor│ (SoC >= 0.15)
   │  Gate 6: Power Ceiling        │ (P_total <= 880W)
   │  Gate 7: Survival Invariant   │ (No unrecoverable loss)
   └──────────────┬────────────────┘
                  │
         ┌────────┴────────┐
         ▼                 ▼
     [ REJECT ]        [ ACCEPT ]
         │                 │
    Inhibit Command   Dispatch to PDU
    (Safe Fallback)
```

---

## 2. Detailed Experiment Specifications

### P3-E1 — Baseline Safety Enforcement
* **Objective**: Evaluate whether adding a deterministic safety governor eliminates unsafe action executions compared to an ungoverned AI planner under identical proposal distributions.
* **Hypothesis Tested**: **H1**
* **Configurations**:
  - **System A (Ungoverned AI)**: Upstream recovery proposal is directly commanded to the spacecraft simulation without intermediate safety verification.
  - **System B (Governed AI)**: Upstream recovery proposal is intercepted and filtered through the Deterministic Safety Governor.
* **Sample Size**: 500 controlled fault scenarios.
* **Key Metrics**: Unsafe Action Execution Rate ($0\%$ expected in System B vs $>0\%$ in System A), Unsafe Rejection Rate, False Acceptance Rate (FAR), Governor Bypass Count.
* **Artifact**: `evaluation/paper3/e1_baseline_safety.json`.

---

### P3-E2 — Individual Constraint Coverage
* **Objective**: Systematically isolate and verify each hard physical constraint independently across 4 canonical operational states:
  1. Clearly Safe (well within limits)
  2. Near Limit (within 5% of threshold)
  3. Exact Boundary (at the numerical limit)
  4. Explicit Breach (exceeding threshold)
* **Constraints Evaluated**:
  - **Thermal**: $T_{\text{batt}} \le 46.0^\circ\text{C}$
  - **Voltage**: $V_{\text{bus}} \ge 22.0\text{V}$
  - **Current**: $I_{\text{batt}} \le 40.0\text{A}$
  - **Battery Reserve**: $\text{SoC} \ge 0.15$
  - **Power Ceiling**: $P \le 880.0\text{W}$
  - **State Validity**: Non-NaN, finite, physical bounds
* **Hypothesis Tested**: **H2**
* **Sample Size**: 100 evaluations per constraint (500 total).
* **Artifact**: `evaluation/paper3/e2_constraint_coverage.json`.

---

### P3-E3 — Compound Constraint Violations
* **Objective**: Investigate multi-failure scenarios where candidate proposals breach two, three, or four physical constraints concurrently.
* **Hypothesis Tested**: **H2**, **H3**
* **Failure Combinations**:
  - Double Breach: Thermal + Undervoltage, Voltage + Overcurrent, Thermal + SoC Depletion.
  - Triple Breach: Thermal + Voltage + Overcurrent.
  - Quadruple Breach: Thermal + Voltage + Overcurrent + SoC Depletion.
* **Verification Criterion**: Governor must detect and report *all* concurrent violations in its audit trail, not merely short-circuit on the first encountered.
* **Sample Size**: 300 compound proposal evaluations.
* **Artifact**: `evaluation/paper3/e3_compound_constraints.json`.

---

### P3-E4 — Unsafe AI Proposal Injection
* **Objective**: Evaluate governor resilience against deliberately adversarial, flawed, or overconfident upstream AI proposals designed to stress the safety barrier.
* **Hypothesis Tested**: **H3**
* **Injected Proposal Classes**:
  1. Excessive Payload Re-activation during low bus voltage.
  2. Maximum Heater Activation during elevated battery core temperature.
  3. High-Rate Science Downlink during battery depletion in eclipse.
  4. Aggressive Fast Charge commanding battery overcurrent.
  5. Hallucinated / Invalid Action Parameters.
* **Sample Size**: 400 adversarial proposals.
* **Key Metric**: $100\%$ rejection rate of unsafe proposals; zero executions.
* **Artifact**: `evaluation/paper3/e4_unsafe_proposals.json`.

---

### P3-E5 — Continuous Safety Boundary Testing
* **Objective**: Characterize the exact mathematical transition of governor authorization across continuous state parameters to detect off-by-one errors, floating-point leakage, or non-monotonic behavior.
* **Hypothesis Tested**: **H4**
* **Sweep Resolution**: 201 finely spaced evaluation points spanning $[-5.0, +5.0]$ margin relative to each threshold.
* **Parameters Swept**:
  - $T_{\text{batt}} \in [41.0^\circ\text{C}, 51.0^\circ\text{C}]$ around $46.0^\circ\text{C}$
  - $V_{\text{bus}} \in [17.0\text{V}, 27.0\text{V}]$ around $22.0\text{V}$
  - $I_{\text{batt}} \in [35.0\text{A}, 45.0\text{A}]$ around $40.0\text{A}$
  - $\text{SoC} \in [0.10, 0.20]$ around $0.15$
* **Artifact**: `evaluation/paper3/e5_boundary_testing.json`.

---

### P3-E6 — Communication-Aware Safety Arbitration
* **Objective**: Verify that communication geometry (active pass vs orbital blackout) informs action urgency and downlink scheduling without ever overriding Level 1 hard safety invariants.
* **Hypothesis Tested**: **H5**
* **Test Regimes**:
  - Unsafe Action + Active Ground Contact $\to$ Must REJECT action (defer to ground).
  - Unsafe Action + Total Blackout $\to$ Must REJECT action (cannot bypass safety simply because ground is absent).
  - Safe Action + Active Ground Contact $\to$ Defer or Execute based on time-to-criticality budget.
  - Safe Action + Total Blackout $\to$ Authorize autonomous execution.
* **Sample Size**: 300 communication scenarios.
* **Artifact**: `evaluation/paper3/e6_communication_safety.json`.

---

### P3-E7 — Physically Constrained "No-Safe-Action" Scenarios
* **Objective**: Construct extreme physical anomaly regimes where severe physical degradation renders *every* candidate recovery action unsafe.
* **Hypothesis Tested**: **H6**
* **Expected Behavior**: Governor safely rejects all candidates and returns `NO_SAFE_ACTION_AVAILABLE`, refusing to force an action or command a dangerous recovery.
* **Sample Size**: 150 dead-end scenarios.
* **Artifact**: `evaluation/paper3/e7_no_safe_action.json`.

---

### P3-E8 — Safety Governor Ablation & Computational Overhead
* **Objective**: Quantify the algorithmic cost and latency of deterministic safety gating across 500 candidate proposals.
* **Measured Metrics**: Mean latency (milliseconds), peak memory, constraint evaluation count, survival rate delta.
* **Artifact**: `evaluation/paper3/e8_ablation.json` and `evaluation/paper3/overhead_results.json`.

---

## 3. Fail-Closed Protocol & Invariant Testing

The safety gatekeeper adheres to an immutable **Fail-Closed** rule:
* If input telemetry contains `NaN` or `Inf` $\to$ `REJECT (FAIL_CLOSED_CORRUPTED_TELEMETRY)`
* If proposed action is unknown or malformed $\to$ `REJECT (FAIL_CLOSED_INVALID_ACTION)`
* If internal constraint evaluator encounters an exception $\to$ `REJECT (FAIL_CLOSED_EVALUATOR_EXCEPTION)`
* If state history is missing $\to$ `REJECT (FAIL_CLOSED_INCOMPLETE_STATE)`

Verification of these edge cases is stored in `evaluation/paper3/fail_closed_results.json`.
