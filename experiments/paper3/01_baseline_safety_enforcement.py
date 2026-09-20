#!/usr/bin/env python3
"""AstraHeal Paper 3 — Experiment 01: Baseline Safety Enforcement.

Comparative evaluation of Ungoverned AI (System A) vs Governed AI (System B)
under identical upstream proposal distributions.
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
    Paper3SafetyGovernor,
    ProposalGenerator,
    SpacecraftState,
    compute_safety_metrics,
)


def run_experiment(output_path: Optional[str] = None) -> Dict[str, Any]:
    print("=" * 80)
    print("ASTRAHEAL PAPER 3: EXPERIMENT 01 — BASELINE SAFETY ENFORCEMENT")
    print("Hypothesis H1: Deterministic safety governor eliminates unsafe executions.")
    print("=" * 80)

    rng = np.random.default_rng(seed=42)
    governor = Paper3SafetyGovernor()

    nominal_state = SpacecraftState(
        timestamp=100.0,
        battery_temp_c=28.5,
        bus_voltage_v=28.2,
        battery_current_a=18.4,
        state_of_charge=0.82,
        pdu_power_w=450.0,
        is_survived=True,
    )

    num_scenarios = 500
    print(f"[1/3] Generating {num_scenarios} controlled recovery proposal scenarios...")

    system_a_records = []  # Ungoverned AI (direct execution)
    system_b_records = []  # Governed AI (intercepted by safety governor)

    for i in range(num_scenarios):
        # 60% safe proposals, 40% unsafe/flawed proposals
        is_safe = bool(rng.random() < 0.60)
        action = ProposalGenerator.generate_nominal_candidate(
            action_id=f"PROP-{i+1:04d}",
            rng=rng,
            is_safe=is_safe
        )

        # System A: Ungoverned AI proposes -> directly executes
        system_a_records.append({
            "scenario_id": i + 1,
            "action_id": action.action_id,
            "action_type": action.action_type,
            "is_ground_truth_safe": action.is_ground_truth_safe,
            "ai_confidence": action.ai_confidence,
            "governor_admitted": True,  # Ungoverned: always admitted
            "was_executed": True,       # Directly commands execution
            "governor_bypassed": False, # No governor present
            "latency_ms": 0.0,
        })

        # System B: Governed AI proposes -> intercepted by Governor -> only safe actions execute
        verdict = governor.evaluate_action(action, nominal_state)
        system_b_records.append({
            "scenario_id": i + 1,
            "action_id": action.action_id,
            "action_type": action.action_type,
            "is_ground_truth_safe": action.is_ground_truth_safe,
            "ai_confidence": action.ai_confidence,
            "governor_admitted": verdict.is_admissible,
            "was_executed": verdict.is_admissible,  # Only executes if governor approved
            "governor_bypassed": False,
            "violated_constraints": verdict.violated_constraints,
            "rejection_reasons": verdict.rejection_reasons,
            "safety_margins": verdict.safety_margins,
            "latency_ms": verdict.evaluation_latency_ms,
        })

    print("[2/3] Computing formal comparative safety metrics...")
    metrics_a = compute_safety_metrics(system_a_records)
    metrics_b = compute_safety_metrics(system_b_records)

    results = {
        "experiment_id": "P3-E1",
        "description": "Baseline Safety Enforcement (Ungoverned vs Governed)",
        "num_scenarios": num_scenarios,
        "system_a_ungoverned": metrics_a,
        "system_b_governed": metrics_b,
        "delta_unsafe_executions": metrics_a["unsafe_actions_executed"] - metrics_b["unsafe_actions_executed"],
        "delta_unsafe_execution_rate": metrics_a["unsafe_action_execution_rate"] - metrics_b["unsafe_action_execution_rate"],
        "governor_bypass_rate": 0.0,
        "system_b_raw_records": system_b_records[:25],  # Sample audit trace
    }

    print("\n" + "-" * 80)
    print(f"Total Scenarios Evaluated: {num_scenarios}")
    print(f"Safe Proposals: {metrics_b['safe_proposals']} | Unsafe Proposals: {metrics_b['unsafe_proposals']}")
    print("-" * 80)
    print(f"System A (Ungoverned AI):")
    print(f"  Unsafe Actions Executed: {metrics_a['unsafe_actions_executed']} / {metrics_a['unsafe_proposals']} ({metrics_a['unsafe_action_execution_rate']*100:.1f}%)")
    print(f"  Safe Actions Executed  : {metrics_a['safe_actions_accepted']} / {metrics_a['safe_proposals']} ({metrics_a['safe_action_acceptance_rate']*100:.1f}%)")
    print(f"System B (Governed AI):")
    print(f"  Unsafe Actions Executed: {metrics_b['unsafe_actions_executed']} / {metrics_b['unsafe_proposals']} ({metrics_b['unsafe_action_execution_rate']*100:.1f}%)")
    print(f"  Unsafe Actions Rejected: {metrics_b['unsafe_actions_rejected']} / {metrics_b['unsafe_proposals']} ({metrics_b['unsafe_action_rejection_rate']*100:.1f}%)")
    print(f"  Safe Actions Accepted  : {metrics_b['safe_actions_accepted']} / {metrics_b['safe_proposals']} ({metrics_b['safe_action_acceptance_rate']*100:.1f}%)")
    print(f"  Governor Bypass Count  : {metrics_b['governor_bypasses']}")
    print(f"  Mean Evaluation Latency: {metrics_b['latency_mean_ms']:.4f} ms")
    print("-" * 80)

    if output_path is None:
        output_path = str(REPO_ROOT / "evaluation" / "paper3" / "e1_baseline_safety.json")
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "w") as f:
        json.dump(results, f, indent=2)

    print(f"[3/3] Results saved to: {output_path}")
    return results


if __name__ == "__main__":
    run_experiment()
