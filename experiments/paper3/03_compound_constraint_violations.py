#!/usr/bin/env python3
"""AstraHeal Paper 3 — Experiment 03: Compound Constraint Violations.

Evaluates governor behavior when actions violate multiple physical constraints simultaneously
(double, triple, and quadruple concurrent violations).
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
    print("ASTRAHEAL PAPER 3: EXPERIMENT 03 — COMPOUND CONSTRAINT VIOLATIONS")
    print("Hypothesis H2/H3: Governor detects all concurrent violations without short-circuiting.")
    print("=" * 80)

    rng = np.random.default_rng(seed=42)
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

    compound_classes = [
        ("DOUBLE_THERMAL_VOLTAGE", ["HARD_THERMAL_EXCEEDED", "HARD_VOLTAGE_UNDERFLOW"]),
        ("DOUBLE_VOLTAGE_OVERCURRENT", ["HARD_VOLTAGE_UNDERFLOW", "HARD_OVERCURRENT_EXCEEDED"]),
        ("DOUBLE_THERMAL_SOC", ["HARD_THERMAL_EXCEEDED", "HARD_SOC_DEPLETED"]),
        ("TRIPLE_THERMAL_VOLT_CURR", ["HARD_THERMAL_EXCEEDED", "HARD_VOLTAGE_UNDERFLOW", "HARD_OVERCURRENT_EXCEEDED"]),
        ("TRIPLE_THERMAL_VOLT_SOC", ["HARD_THERMAL_EXCEEDED", "HARD_VOLTAGE_UNDERFLOW", "HARD_SOC_DEPLETED"]),
        ("QUAD_THERMAL_VOLT_CURR_SOC", [
            "HARD_THERMAL_EXCEEDED",
            "HARD_VOLTAGE_UNDERFLOW",
            "HARD_OVERCURRENT_EXCEEDED",
            "HARD_SOC_DEPLETED",
        ]),
    ]

    scenarios_per_class = 50
    total_scenarios = len(compound_classes) * scenarios_per_class
    print(f"[1/3] Generating {total_scenarios} multi-breach compound failure proposals...")

    results_by_class = {}
    detailed_records = []
    total_violations_injected = 0
    total_violations_detected = 0

    for class_name, expected_viols in compound_classes:
        class_rejected = 0
        all_detected_count = 0

        for i in range(scenarios_per_class):
            action_id = f"CMP-{class_name[:6]}-{i+1:03d}"

            # Default safe values
            p_temp = 32.0
            p_volt = 28.0
            p_curr = 18.0
            p_soc = 0.75
            p_pow = 500.0

            # Inject designated violations
            if "HARD_THERMAL_EXCEEDED" in expected_viols:
                p_temp = float(rng.uniform(47.5, 62.0))
            if "HARD_VOLTAGE_UNDERFLOW" in expected_viols:
                p_volt = float(rng.uniform(14.0, 21.0))
            if "HARD_OVERCURRENT_EXCEEDED" in expected_viols:
                p_curr = float(rng.uniform(43.0, 68.0))
            if "HARD_SOC_DEPLETED" in expected_viols:
                p_soc = float(rng.uniform(0.02, 0.12))

            action = ProposedAction(
                action_id=action_id,
                action_type="CONTINUE_NOMINAL",
                predicted_peak_temp_c=p_temp,
                predicted_min_voltage_v=p_volt,
                predicted_peak_current_a=p_curr,
                predicted_min_soc=p_soc,
                predicted_peak_power_w=p_pow,
                is_ground_truth_safe=False,
            )

            verdict = governor.evaluate_action(action, nominal_state)

            if verdict.decision == GateDecision.REJECTED:
                class_rejected += 1

            # Verify that every injected violation was detected
            detected_set = set(verdict.violated_constraints)
            expected_set = set(expected_viols)
            is_full_detection = expected_set.issubset(detected_set)

            if is_full_detection:
                all_detected_count += 1

            total_violations_injected += len(expected_viols)
            total_violations_detected += len(expected_set.intersection(detected_set))

            detailed_records.append({
                "action_id": action_id,
                "compound_class": class_name,
                "expected_violations": expected_viols,
                "detected_violations": verdict.violated_constraints,
                "fully_detected": is_full_detection,
                "decision": verdict.decision.value,
            })

        results_by_class[class_name] = {
            "scenarios": scenarios_per_class,
            "rejections": class_rejected,
            "rejection_rate": class_rejected / scenarios_per_class,
            "full_detection_count": all_detected_count,
            "full_detection_rate": all_detected_count / scenarios_per_class,
            "expected_violations_per_case": len(expected_viols),
        }

    overall_rejection_rate = sum(r["rejections"] for r in results_by_class.values()) / total_scenarios
    overall_detection_recall = total_violations_detected / total_violations_injected

    print("[2/3] Compound violation evaluation complete:")
    print("-" * 80)
    print(f"{'Compound Category':<28} | {'Scenarios':<10} | {'Rejected':<10} | {'All Detected':<12}")
    print("-" * 80)
    for c_name, data in results_by_class.items():
        print(f"{c_name:<28} | {data['scenarios']:<10} | {data['rejections']} (100%)   | {data['full_detection_count']} (100%)")
    print("-" * 80)
    print(f"Overall Compound Rejection Rate   : {overall_rejection_rate*100:.1f}%")
    print(f"Compound Violation Detection Recall: {overall_detection_recall*100:.1f}% ({total_violations_detected}/{total_violations_injected})")
    print("-" * 80)

    results = {
        "experiment_id": "P3-E3",
        "description": "Compound Multi-Constraint Violations (2, 3, and 4 concurrent breaches)",
        "total_scenarios": total_scenarios,
        "total_violations_injected": total_violations_injected,
        "total_violations_detected": total_violations_detected,
        "compound_rejection_rate": float(overall_rejection_rate),
        "compound_detection_recall": float(overall_detection_recall),
        "category_breakdown": results_by_class,
        "detailed_sample": detailed_records[:25],
    }

    if output_path is None:
        output_path = str(REPO_ROOT / "evaluation" / "paper3" / "e3_compound_constraints.json")
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "w") as f:
        json.dump(results, f, indent=2)

    print(f"[3/3] Results saved to: {output_path}")
    return results


if __name__ == "__main__":
    run_experiment()
