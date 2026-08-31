# AstraHeal — Stage 7 Research Report: Counterfactual Mission Simulation

**Stage**: 7 — Counterfactual Mission Simulation & Multi-Branching  
**Status**: VERIFIED & COMPLETE  
**Execution Timestamp**: 2026-08-31  

---

## 1. Executive Summary

Stage 7 implements the autonomous counterfactual branching core of AstraHeal. When anomalies and faults are diagnosed, the system no longer outputs passive warnings; instead, it generates domain-specific candidate recovery actions and executes isolated, forward simulations within deep-cloned digital twin states.

The fundamental counterfactual research question is answered:
> *"Given current degraded spacecraft telemetry, what will happen to mission survival, battery temperature, bus voltage, and state-of-charge over the next 1–2 orbits if Action A is executed versus Action B or unmitigated baseline No-Op?"*

---

## 2. Architecture & Modules Implemented

- **`src/planner/actions.py`**:
  - `RecoveryActionType` enum (`CONTINUE_NOMINAL`, `REDUCE_PAYLOAD_LOAD`, `DISABLE_NON_CRITICAL_SUBSYSTEM`, `REDUCE_HEATER_POWER`, `ENTER_SAFE_MODE`, `REDISTRIBUTE_POWER`, `DEFER_NON_CRITICAL_ACTIVITY`).
  - `RecoveryAction`: Structured action container with execution hooks and disruption cost modeling.
  - `ActionGenerator`: Context-aware generator creating candidate recovery sets tailored to the diagnosed failure mode.
- **`src/planner/scenario.py`**:
  - `ScenarioResult`: Standardized schema containing `RiskMetrics`, `MissionImpact`, constraint violations, snapshots, and full trajectory telemetry.
- **`src/planner/counterfactual.py`**:
  - `CounterfactualSimulator`: Isolated simulation orchestrator using non-mutating deep-clones (`twin.clone()`).
- **`src/digital_twin/simulator.py`**:
  - Enhanced with `clone()` method for instant deep copying of orbital, solar, battery, PDU, and fault states.

---

## 3. Verification & Benchmark Results

### Unit Tests
- `tests/test_counterfactual.py` (4 passing tests):
  - `test_digital_twin_cloning_isolation`: Confirms 0% state mutation on primary digital twin when branches are modified.
  - `test_candidate_action_generation`: Verifies candidate diversity across failure archetypes.
  - `test_counterfactual_simulation_branching`: Validates that Safe Mode preserves higher SoC floor during eclipse.
  - `test_counterfactual_reproducibility`: Proves deterministic identical outputs given fixed random seeds.

### Experiment 05 Execution
- Executed `experiments/05_counterfactual_recovery.py`:
  - Injected high impedance fault ($4.5\times$ nominal $R_{int}$).
  - Evaluated candidate actions: `CONTINUE_NOMINAL` vs `ENTER_SAFE_MODE` vs `CONSERVATIVE_STANDBY`.
  - Captured multi-channel lookahead trajectories in `docs/figures/05_counterfactual_branches.png`.
  - Compiled detailed risk and constraint metrics into `evaluation/05_counterfactual_results.json`.

---

## 4. Limitations & Next Step

- **Current Scope**: Evaluates candidate actions at the EPS and PDU subsystem level.
- **Next Step (Stage 8)**: Connect counterfactual predictions to the deterministic **Safety Governor** and **Autonomous Recovery Planner** for automated action authorization and optimal selection.
