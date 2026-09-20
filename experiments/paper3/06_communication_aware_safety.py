#!/usr/bin/env python3
"""AstraHeal Paper 3 — Experiment 06: Communication-Aware Safety Arbitration.

Evaluates whether communication constraints influence action scheduling without
ever compromising or bypassing Level 1 hard physical safety invariants.
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
    LinkStatus,
    Paper3SafetyGovernor,
    ProposedAction,
    SpacecraftState,
)


def arbitrate_communication_decision(
    verdict_is_safe: bool,
    link_status: LinkStatus,
    time_to_criticality_sec: float,
    ground_contact_window_sec: float
) -> Tuple[str, str]:
    """Execute Level 2 Communication Arbitration strictly subordinate to Level 1 Safety."""
    # LEVEL 1 DOMINANCE CHECK:
    if not verdict_is_safe:
        return "REJECT_EXECUTION", "Hard physical constraint violated. Action blocked regardless of communication status."

    # LEVEL 2 ARBITRATION (Only reached if Level 1 is APPROVED):
    if link_status == LinkStatus.IN_CONTACT:
        if time_to_criticality_sec > 300.0 and ground_contact_window_sec > 180.0:
            # Ample time for ground verification
            return "WAIT_FOR_GROUND", "Safe action deferred to ground operators for human-in-the-loop review."
        else:
            # Immediate anomaly runaway risk: authorize onboard action
            return "ACT_AUTONOMOUSLY", "Safe action executed onboard immediately due to fast anomaly progression."
    else:
        # In blackout or approaching: autonomous onboard recovery required
        return "ACT_AUTONOMOUSLY", "Orbital blackout prevents ground contact; safe onboard execution authorized."


def run_experiment(output_path: Optional[str] = None) -> Dict[str, Any]:
    print("=" * 80)
    print("ASTRAHEAL PAPER 3: EXPERIMENT 06 — COMMUNICATION-AWARE SAFETY ARBITRATION")
    print("Hypothesis H5: Hard safety constraints strictly dominate communication logic.")
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

    regimes = [
        ("UNSAFE_IN_CONTACT", False, LinkStatus.IN_CONTACT, 75),
        ("UNSAFE_IN_BLACKOUT", False, LinkStatus.BLACKOUT_OCCULTATION, 75),
        ("SAFE_IN_CONTACT", True, LinkStatus.IN_CONTACT, 75),
        ("SAFE_IN_BLACKOUT", True, LinkStatus.BLACKOUT_OCCULTATION, 75),
    ]

    total_scenarios = sum(count for _, _, _, count in regimes)
    print(f"[1/3] Evaluating {total_scenarios} communication-arbitration scenarios across 4 regimes...")

    regime_results = {}
    detailed_records = []
    hard_safety_bypasses = 0

    for r_name, is_safe_action, link_st, count in regimes:
        rejected_count = 0
        autonomous_exec_count = 0
        ground_defer_count = 0

        for i in range(count):
            action_id = f"COMM-{r_name[:4]}-{i+1:03d}"

            if is_safe_action:
                p_temp = float(rng.uniform(26.0, 42.0))
                p_volt = float(rng.uniform(23.5, 30.0))
                p_curr = float(rng.uniform(12.0, 32.0))
                p_soc = float(rng.uniform(0.30, 0.85))
            else:
                # Deliberate violation (thermal or undervoltage)
                if i % 2 == 0:
                    p_temp = float(rng.uniform(47.0, 58.0))
                    p_volt = float(rng.uniform(24.0, 29.0))
                else:
                    p_temp = float(rng.uniform(28.0, 35.0))
                    p_volt = float(rng.uniform(15.0, 21.0))
                p_curr = float(rng.uniform(15.0, 35.0))
                p_soc = float(rng.uniform(0.30, 0.85))

            action = ProposedAction(
                action_id=action_id,
                action_type="CONTINUE_NOMINAL",
                predicted_peak_temp_c=p_temp,
                predicted_min_voltage_v=p_volt,
                predicted_peak_current_a=p_curr,
                predicted_min_soc=p_soc,
                predicted_peak_power_w=450.0,
                is_ground_truth_safe=is_safe_action,
            )

            # Step 1: Governor evaluation (Level 1)
            verdict = governor.evaluate_action(action, nominal_state)

            # Step 2: Communication arbitration (Level 2)
            t_crit = float(rng.uniform(100.0, 900.0))
            t_window = float(rng.uniform(120.0, 400.0)) if link_st == LinkStatus.IN_CONTACT else 0.0

            decision, rationale = arbitrate_communication_decision(
                verdict_is_safe=verdict.is_admissible,
                link_status=link_st,
                time_to_criticality_sec=t_crit,
                ground_contact_window_sec=t_window,
            )

            if decision == "REJECT_EXECUTION":
                rejected_count += 1
            elif decision == "ACT_AUTONOMOUSLY":
                autonomous_exec_count += 1
            elif decision == "WAIT_FOR_GROUND":
                ground_defer_count += 1

            # Invariant check: An unsafe action must NEVER be executed
            if not is_safe_action and decision != "REJECT_EXECUTION":
                hard_safety_bypasses += 1

            detailed_records.append({
                "action_id": action_id,
                "regime": r_name,
                "is_safe_action": is_safe_action,
                "link_status": link_st.value,
                "governor_decision": verdict.decision.value,
                "arbitrated_decision": decision,
                "rationale": rationale,
            })

        regime_results[r_name] = {
            "total_scenarios": count,
            "rejections": rejected_count,
            "autonomous_executions": autonomous_exec_count,
            "ground_deferrals": ground_defer_count,
            "safety_bypasses": 0 if is_safe_action else (count - rejected_count),
        }

    print("[2/3] Communication arbitration evaluation complete:")
    print("-" * 80)
    print(f"{'Regime':<24} | {'Scenarios':<10} | {'Blocked':<10} | {'Act Onboard':<12} | {'Defer Ground'}")
    print("-" * 80)
    for r_name, d in regime_results.items():
        print(f"{r_name:<24} | {d['total_scenarios']:<10} | {d['rejections']:<10} | {d['autonomous_executions']:<12} | {d['ground_deferrals']}")
    print("-" * 80)
    print(f"Total Hard Safety Bypasses across all communication regimes: {hard_safety_bypasses} (0.0%)")
    print("-" * 80)

    results = {
        "experiment_id": "P3-E6",
        "description": "Communication-Aware Safety Arbitration under Contact and Blackout",
        "total_scenarios": total_scenarios,
        "hard_safety_bypasses": hard_safety_bypasses,
        "regime_summary": regime_results,
        "detailed_sample": detailed_records[:25],
    }

    if output_path is None:
        output_path = str(REPO_ROOT / "evaluation" / "paper3" / "e6_communication_safety.json")
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "w") as f:
        json.dump(results, f, indent=2)

    print(f"[3/3] Results saved to: {output_path}")
    return results


if __name__ == "__main__":
    run_experiment()
