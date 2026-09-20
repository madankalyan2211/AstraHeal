#!/usr/bin/env python3
"""AstraHeal Paper 3 — Experiment 05: Continuous Safety Boundary Testing.

Fine-grained mathematical sweep (201 evaluation points) across continuous constraint
thresholds to verify exact transition boundaries, monotonicity, and lack of floating-point leakage.
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
    GateDecision,
    Paper3SafetyGovernor,
    ProposedAction,
    SpacecraftState,
)


def run_experiment(output_path: Optional[str] = None) -> Dict[str, Any]:
    print("=" * 80)
    print("ASTRAHEAL PAPER 3: EXPERIMENT 05 — CONTINUOUS BOUNDARY TESTING")
    print("Hypothesis H4: Governor gating is monotonic and exact at defined constraint boundaries.")
    print("=" * 80)

    governor = Paper3SafetyGovernor()

    nominal_state = SpacecraftState(
        timestamp=100.0,
        battery_temp_c=28.0,
        bus_voltage_v=28.0,
        battery_current_a=15.0,
        state_of_charge=0.80,
        pdu_power_w=420.0,
        is_survived=True,
    )

    num_points = 201
    sweep_definitions = [
        {
            "channel": "battery_temp_c",
            "threshold": 46.0,
            "direction": "MAX",
            "values": np.linspace(41.0, 51.0, num_points),
            "unit": "°C",
        },
        {
            "channel": "bus_voltage_v",
            "threshold": 22.0,
            "direction": "MIN",
            "values": np.linspace(17.0, 27.0, num_points),
            "unit": "V",
        },
        {
            "channel": "battery_current_a",
            "threshold": 40.0,
            "direction": "MAX",
            "values": np.linspace(35.0, 45.0, num_points),
            "unit": "A",
        },
        {
            "channel": "battery_soc",
            "threshold": 0.15,
            "direction": "MIN",
            "values": np.linspace(0.10, 0.20, num_points),
            "unit": "fraction",
        },
    ]

    print(f"[1/3] Sweeping {len(sweep_definitions)} physical channels across {num_points} continuous points each...")

    boundary_results = {}

    for sweep in sweep_definitions:
        channel = sweep["channel"]
        threshold = sweep["threshold"]
        direction = sweep["direction"]
        values = sweep["values"]

        trajectory = []
        inconsistencies = 0

        for idx, val in enumerate(values):
            val_float = float(val)

            # Baseline nominal parameters
            p_temp = 30.0
            p_volt = 28.0
            p_curr = 20.0
            p_soc = 0.70

            if channel == "battery_temp_c":
                p_temp = val_float
                expected_safe = (val_float <= threshold)
            elif channel == "bus_voltage_v":
                p_volt = val_float
                expected_safe = (val_float >= threshold)
            elif channel == "battery_current_a":
                p_curr = val_float
                expected_safe = (val_float <= threshold)
            elif channel == "battery_soc":
                p_soc = val_float
                expected_safe = (val_float >= threshold)

            action = ProposedAction(
                action_id=f"BND-{channel[:4].upper()}-{idx:03d}",
                action_type="CONTINUE_NOMINAL",
                predicted_peak_temp_c=p_temp,
                predicted_min_voltage_v=p_volt,
                predicted_peak_current_a=p_curr,
                predicted_min_soc=p_soc,
                predicted_peak_power_w=500.0,
                is_ground_truth_safe=expected_safe,
            )

            verdict = governor.evaluate_action(action, nominal_state)
            actual_safe = verdict.is_admissible

            if actual_safe != expected_safe:
                inconsistencies += 1

            margin = (threshold - val_float) if direction == "MAX" else (val_float - threshold)

            trajectory.append({
                "index": idx,
                "value": val_float,
                "margin": float(margin),
                "expected_safe": expected_safe,
                "actual_safe": actual_safe,
                "decision": verdict.decision.value,
                "violated_constraints": verdict.violated_constraints,
            })

        # Monotonicity check: decisions should switch exactly once
        decisions_bool = [p["actual_safe"] for p in trajectory]
        switches = sum(1 for i in range(1, len(decisions_bool)) if decisions_bool[i] != decisions_bool[i - 1])

        boundary_results[channel] = {
            "threshold": threshold,
            "direction": direction,
            "unit": sweep["unit"],
            "total_points": num_points,
            "boundary_switches": switches,
            "is_strictly_monotonic": (switches == 1),
            "inconsistency_count": inconsistencies,
            "accuracy": (num_points - inconsistencies) / num_points,
            "trajectory": trajectory,
        }

    print("[2/3] Continuous boundary testing complete:")
    print("-" * 80)
    print(f"{'Channel':<20} | {'Threshold':<12} | {'Direction':<10} | {'Switches':<10} | {'Monotonic':<12}")
    print("-" * 80)
    for ch, d in boundary_results.items():
        print(f"{ch:<20} | {d['threshold']} {d['unit']:<6} | {d['direction']:<10} | {d['boundary_switches']:<10} | {str(d['is_strictly_monotonic']):<12}")
    print("-" * 80)

    results = {
        "experiment_id": "P3-E5",
        "description": "Continuous Safety Boundary Testing across 4 physical channels (201 points each)",
        "num_points_per_channel": num_points,
        "boundary_summary": {
            k: {
                "threshold": v["threshold"],
                "direction": v["direction"],
                "is_strictly_monotonic": v["is_strictly_monotonic"],
                "accuracy": v["accuracy"],
            }
            for k, v in boundary_results.items()
        },
        "full_trajectories": {k: v["trajectory"] for k, v in boundary_results.items()},
    }

    if output_path is None:
        output_path = str(REPO_ROOT / "evaluation" / "paper3" / "e5_boundary_testing.json")
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "w") as f:
        json.dump(results, f, indent=2)

    print(f"[3/3] Results saved to: {output_path}")
    return results


if __name__ == "__main__":
    run_experiment()
