# AstraHeal — Stage 8 Research Report: Autonomous Recovery Planner & Deterministic Safety Governor

**Stage**: 8 — Autonomous Recovery Planner & Safety Governor  
**Status**: VERIFIED & COMPLETE  
**Execution Timestamp**: 2026-08-31  

---

## 1. Executive Summary

Stage 8 transitions AstraHeal from an advisory monitoring system into an autonomous decision-making and fault mitigation platform. 

### Critical Safety Invariant
Under the AstraHeal safety doctrine:
> **AI models, heuristic planners, and agentic workflows are strictly prohibited from directly modifying the spacecraft simulation or commanding onboard actuators without explicit, deterministic authorization from the Safety Governor.**

The Deterministic Safety Governor acts as the immutable final authority, verifying that every proposed action satisfies hard physical invariants (thermal runaway limit, undervoltage lockout, overcurrent threshold, and battery reserve floor) across the entire counterfactual prediction horizon.

---

## 2. Architecture & Modules Implemented

- **`src/safety/safety_governor.py`**:
  - `DeterministicSafetyGovernor`: Evaluates predicted counterfactual trajectories against hard safety thresholds:
    - Maximum Battery Temperature: $\le 46.0^\circ\text{C}$
    - Minimum Bus Voltage: $\ge 22.0\text{V}$
    - Maximum Battery Current: $\le 40.0\text{A}$
    - Minimum Battery Reserve SoC: $\ge 15.0\%$
    - Absolute Mission Survival: True
  - Outputs `SafetyDecision` with `APPROVED` or `REJECTED` and explicit physical violation rationale.
- **`src/planner/recovery_planner.py`**:
  - `AutonomousRecoveryPlanner`: Orchestrates counterfactual branch generation, invokes the Safety Governor, filters out rejected candidates, and computes soft multi-objective scores:
    $$\text{Score} = w_{surv} \cdot \text{SurvMargin} + w_{pay} \cdot \text{PayloadAvail} + w_{eng} \cdot \text{EnergyMargin} + w_{rev} \cdot \text{Reversibility} - w_{dis} \cdot \text{Disruption}$$
  - Selects the highest-ranked approved recovery action and executes it on the active digital twin.

---

## 3. Verification & Benchmark Results

### Unit Tests
- `tests/test_safety_governor.py` (3 tests):
  - `test_safety_governor_approves_safe_scenario`: Confirms authorization when all physical margins are positive.
  - `test_safety_governor_rejects_thermal_breach`: Confirms strict rejection when predicted temperature exceeds $46^\circ\text{C}$.
  - `test_safety_governor_rejects_undervoltage`: Confirms strict rejection when voltage collapses below $22\text{V}$.
- `tests/test_recovery_planner.py` (2 tests):
  - `test_planner_end_to_end_decision`: Verifies candidate generation, branching, governor filtering, and ranking.
  - `test_plan_execution_on_digital_twin`: Confirms seamless in-memory execution and state update on the active twin.

### Experiment 06 Execution
- Executed `experiments/06_autonomous_recovery.py`:
  - Successfully demonstrated fault onset $\to$ anomaly detection $\to$ evidential diagnosis $\to$ counterfactual branch evaluation $\to$ Safety Governor gating $\to$ autonomous plan execution $\to$ post-intervention orbital stabilization.
  - Plots generated in `docs/figures/06_autonomous_recovery_plan.png`.
  - Auditable plan JSON saved to `evaluation/06_autonomous_recovery_results.json`.

---

## 4. Next Step

Proceed directly to **Stage 9 (Communication-Aware Autonomy & Ground Delay Arbitration)**.
