# AstraHeal — Stage 9 Research Report: Communication-Aware Autonomy

**Stage**: 9 — Communication-Aware Autonomy & Ground Latency Arbitration  
**Status**: VERIFIED & COMPLETE  
**Execution Timestamp**: 2026-08-31  

---

## 1. Executive Summary

Stage 9 introduces orbital ground network visibility modeling and autonomous arbitration between onboard execution (`ACT_AUTONOMOUSLY`) and ground operator deferral (`WAIT_FOR_GROUND`).

Spacecraft in Low Earth Orbit (LEO) and deep space spend 70–90% of their operational lifetime outside direct ground station visibility. AstraHeal dynamically balances mission risk against communication latency by computing the time-to-criticality ($T_{crit}$) of unmitigated faults relative to the time-to-ground-intervention ($T_{contact} + T_{ground\_ops} + 2 \cdot T_{latency}$).

---

## 2. Architecture & Modules Implemented

- **`src/communication/channel.py`**:
  - `GroundStationPass`: Scheduled visibility windows over ground stations (Svalbard, White Sands, Wallops).
  - `CommunicationChannel`: Real-time link status evaluator calculating $T_{contact}$, pass duration, propagation latency, and bandwidth constraints.
- **`src/communication/manager.py`**:
  - `CommunicationAwareAutonomyManager`: Evaluates fault urgency vs communication state.
  - **Arbitration Principle**:
    - If $T_{crit} \le (T_{contact} + T_{ops}) \times \text{Margin}$: `ACT_AUTONOMOUSLY` (immediate onboard mitigation).
    - If ground contact occurs safely before failure threshold: `WAIT_FOR_GROUND` (telemetry buffered for downlink).

---

## 3. Verification & Benchmark Results

### Unit Tests
- `tests/test_communication.py` (3 passing tests):
  - `test_ground_pass_schedule`: Verifies contact vs blackout orbital transitions.
  - `test_critical_fault_during_blackout_acts_autonomously`: Verifies that severe thermal/power faults in blackouts trigger autonomous recovery.
  - `test_non_critical_fault_defers_to_ground`: Confirms non-critical faults defer safely to ground operators.

### Experiment 07 Execution
- Executed `experiments/07_communication_aware_autonomy.py`:
  - Evaluated arbitration matrix across blackout, active pass, critical runaway, and gradual degradation scenarios.
  - Saved timeline plot to `docs/figures/07_communication_autonomy_timeline.png`.
  - Saved results to `evaluation/07_communication_autonomy_results.json`.

---

## 4. Next Step

Proceed directly to **Stage 10 (Unknown-Failure Resilience & Adaptive Intelligence)**.
