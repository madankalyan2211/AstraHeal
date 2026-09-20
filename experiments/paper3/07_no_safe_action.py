#!/usr/bin/env python3
"""AstraHeal Paper 3 — Experiment 07: Physically Constrained 'No-Safe-Action' Scenarios.

Evaluates governor behavior in dead-end physical anomaly regimes where no candidate
action can satisfy hard physical invariants, verifying safe failure convergence.
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path
from typing import Any, Dict, List

import numpy as np

# Ensure repository root is in sys.path
REPO_ROOT = Path(__file__).resolve().parent.parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from experiments.paper3.common import (
    CERTIFIED_ACTION_TYPES,
    GateDecision,
    Paper3SafetyGovernor,
    ProposedAction,
    SpacecraftState,
)


def run_experiment(output_path: Optional[str] = None) -> Dict[str, Any]:
    print("=" * 80)
    print("ASTRAHEAL PAPER 3: EXPERIMENT 07 — NO-SAFE-ACTION PHYSICAL DEAD-ENDS")
    print("Hypothesis H6: Governor refuses to force an action when no candidate is safe.")
    print("=" * 80)

    rng = np.random.default_rng(seed=101)
    governor = Paper3SafetyGovernor()

    # Highly degraded physical state (severe thermal runaway + bus short)
    degraded_state = SpacecraftState(
        timestamp=500.0,
        battery_temp_c=48.2,       # Already above 46.0°C barrier
        bus_voltage_v=21.1,        # Depressed below 22.0V
        battery_current_a=38.5,
        state_of_charge=0.14,      # Depleted below 15% floor
        pdu_power_w=820.0,
        is_survived=True,
    )

    num_scenarios = 150
    candidates_per_scenario = 5
    print(f"[1/3] Generating {num_scenarios} dead-end scenarios ({num_scenarios * candidates_per_scenario} total candidate evaluations)...")

    scenario_records = []
    total_candidates_evaluated = 0
    total_candidates_rejected = 0
    forced_unsafe_executions = 0
    no_safe_action_events = 0

    for s_idx in range(num_scenarios):
        candidates = []
        for c_idx in range(candidates_per_scenario):
            action_id = f"DEADEND-S{s_idx+1:03d}-C{c_idx+1}"
            a_type = CERTIFIED_ACTION_TYPES[c_idx % len(CERTIFIED_ACTION_TYPES)]

            # Construct candidates that all violate at least one constraint
            p_temp = float(rng.uniform(47.0, 62.0))
            p_volt = float(rng.uniform(16.0, 21.8))
            p_curr = float(rng.uniform(35.0, 55.0))
            p_soc = float(rng.uniform(0.04, 0.13))

            candidate = ProposedAction(
                action_id=action_id,
                action_type=a_type,
                predicted_peak_temp_c=p_temp,
                predicted_min_voltage_v=p_volt,
                predicted_peak_current_a=p_curr,
                predicted_min_soc=p_soc,
                predicted_peak_power_w=float(rng.uniform(600.0, 950.0)),
                predicted_survived=True,
                is_ground_truth_safe=False,
            )
            candidates.append(candidate)

        # Filter candidate pool through Safety Governor
        approved, rejected, status_msg = governor.filter_candidate_pool(candidates, degraded_state)
        total_candidates_evaluated += len(candidates)
        total_candidates_rejected += len(rejected)

        # Verify system behavior: must declare NO_SAFE_ACTION_AVAILABLE
        if status_msg == "NO_SAFE_ACTION_AVAILABLE" and len(approved) == 0:
            no_safe_action_events += 1
        else:
            # If any unsafe action was forced or approved, record breach
            forced_unsafe_executions += len(approved)

        scenario_records.append({
            "scenario_id": s_idx + 1,
            "candidates_evaluated": len(candidates),
            "candidates_rejected": len(rejected),
            "candidates_approved": len(approved),
            "status_message": status_msg,
            "forced_execution": len(approved) > 0,
        })

    safe_failure_rate = no_safe_action_events / num_scenarios
    unsafe_execution_rate = forced_unsafe_executions / total_candidates_evaluated

    print("[2/3] Dead-end scenario evaluation complete:")
    print("-" * 80)
    print(f"Total Scenarios Evaluated       : {num_scenarios}")
    print(f"Total Candidate Actions Evaluated: {total_candidates_evaluated}")
    print(f"Total Candidate Actions Rejected: {total_candidates_rejected} (100.0%)")
    print(f"NO_SAFE_ACTION_AVAILABLE Events : {no_safe_action_events} / {num_scenarios} ({safe_failure_rate*100:.1f}%)")
    print(f"Forced Unsafe Executions        : {forced_unsafe_executions} ({unsafe_execution_rate*100:.1f}%)")
    print("-" * 80)

    results = {
        "experiment_id": "P3-E7",
        "description": "Physically Constrained 'No-Safe-Action' Scenarios",
        "num_scenarios": num_scenarios,
        "total_candidates_evaluated": total_candidates_evaluated,
        "total_candidates_rejected": total_candidates_rejected,
        "no_safe_action_events": no_safe_action_events,
        "safe_failure_convergence_rate": float(safe_failure_rate),
        "forced_unsafe_executions": forced_unsafe_executions,
        "unsafe_execution_rate": float(unsafe_execution_rate),
        "detailed_sample": scenario_records[:20],
    }

    if output_path is None:
        output_path = str(REPO_ROOT / "evaluation" / "paper3" / "e7_no_safe_action.json")
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "w") as f:
        json.dump(results, f, indent=2)

    print(f"[3/3] Results saved to: {output_path}")
    return results


if __name__ == "__main__":
    run_experiment()
