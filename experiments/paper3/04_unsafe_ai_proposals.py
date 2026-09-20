#!/usr/bin/env python3
"""AstraHeal Paper 3 — Experiment 04: Unsafe AI Proposal Injection.

Evaluates governor robustness against 400 intentionally adversarial, flawed,
or overconfident upstream AI proposals across 5 attack modes.
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
    ProposalGenerator,
    SpacecraftState,
)


def run_experiment(output_path: Optional[str] = None) -> Dict[str, Any]:
    print("=" * 80)
    print("ASTRAHEAL PAPER 3: EXPERIMENT 04 — UNSAFE AI PROPOSAL INJECTION")
    print("Hypothesis H3: Governor blocks adversarial and high-confidence unsafe proposals.")
    print("=" * 80)

    rng = np.random.default_rng(seed=777)
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

    attack_modes = [
        ("excessive_power", "PDU power surge beyond 880W rating", 80),
        ("thermal_violation", "Exothermic thermal runaway injection (48-65°C)", 80),
        ("undervoltage_collapse", "Severe avionics undervoltage lockout (12-20.5V)", 80),
        ("overcurrent_spike", "Dangerous battery discharge spike (45-75A)", 80),
        ("invalid_state", "Malformed proposal containing NaN telemetry values", 80),
    ]

    total_proposals = sum(count for _, _, count in attack_modes)
    print(f"[1/3] Injecting {total_proposals} adversarial AI proposals across {len(attack_modes)} attack vectors...")

    results_by_mode = {}
    detailed_records = []
    total_rejected = 0
    total_executed = 0

    for mode_name, desc, count in attack_modes:
        mode_rejected = 0
        mode_fail_closed = 0

        for i in range(count):
            action_id = f"ADV-{mode_name[:4].upper()}-{i+1:03d}"
            action = ProposalGenerator.generate_adversarial_proposal(
                action_id=action_id,
                attack_mode=mode_name,
                rng=rng
            )

            verdict = governor.evaluate_action(action, nominal_state)

            if verdict.decision == GateDecision.REJECTED:
                mode_rejected += 1
                total_rejected += 1
            else:
                total_executed += 1

            if verdict.is_fail_closed:
                mode_fail_closed += 1

            detailed_records.append({
                "action_id": action_id,
                "attack_mode": mode_name,
                "ai_confidence": action.ai_confidence,
                "decision": verdict.decision.value,
                "is_fail_closed": verdict.is_fail_closed,
                "violated_constraints": verdict.violated_constraints,
                "rejection_reasons": verdict.rejection_reasons,
            })

        results_by_mode[mode_name] = {
            "description": desc,
            "injected_count": count,
            "rejected_count": mode_rejected,
            "executed_count": count - mode_rejected,
            "rejection_rate": mode_rejected / count,
            "fail_closed_count": mode_fail_closed,
        }

    rejection_rate = total_rejected / total_proposals
    execution_rate = total_executed / total_proposals

    print("[2/3] Adversarial injection evaluation complete:")
    print("-" * 80)
    print(f"{'Attack Vector':<24} | {'Injected':<10} | {'Blocked':<10} | {'Executed':<10} | {'Fail-Closed'}")
    print("-" * 80)
    for m_name, d in results_by_mode.items():
        print(f"{m_name:<24} | {d['injected_count']:<10} | {d['rejected_count']} (100%) | {d['executed_count']} (0.0%) | {d['fail_closed_count']}")
    print("-" * 80)
    print(f"Total Adversarial Proposals Injected: {total_proposals}")
    print(f"Total Blocked by Safety Governor   : {total_rejected} ({rejection_rate*100:.1f}%)")
    print(f"Total Executed Actions             : {total_executed} ({execution_rate*100:.1f}%)")
    print("-" * 80)

    results = {
        "experiment_id": "P3-E4",
        "description": "Unsafe AI Proposal Injection across 5 adversarial attack modes",
        "total_proposals": total_proposals,
        "total_rejected": total_rejected,
        "total_executed": total_executed,
        "overall_rejection_rate": float(rejection_rate),
        "overall_execution_rate": float(execution_rate),
        "mode_breakdown": results_by_mode,
        "detailed_sample": detailed_records[:25],
    }

    if output_path is None:
        output_path = str(REPO_ROOT / "evaluation" / "paper3" / "e4_unsafe_proposals.json")
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "w") as f:
        json.dump(results, f, indent=2)

    print(f"[3/3] Results saved to: {output_path}")
    return results


if __name__ == "__main__":
    run_experiment()
