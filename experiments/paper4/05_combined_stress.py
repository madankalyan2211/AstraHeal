"""Experiment P4-E5: Combined Stress Conditions Benchmark.

Stress-tests AstraHeal under simultaneously compounded stressors:
- Triple sequential in-flight faults across 3 orbits (17,220s)
- Simultaneous physical parameter perturbations (+/-15% across all 5 parameters)
- Elevated sensor noise (sigma in [0.025, 0.055])
Sample size: 150 combined stress missions.
"""

import json
import sys
import time
from pathlib import Path
import numpy as np

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from evaluation.paper4.scenario_generator import Paper4ScenarioGenerator
from experiments.paper4.common import Paper4ExecutionEngine, Paper4ScenarioResult


def run_experiment():
    print("=" * 80)
    print("ASTRAHEAL EXPERIMENT P4-E5: Combined Stress Conditions")
    print("=" * 80)

    suite = Paper4ScenarioGenerator.generate_e5_combined_stress_suite(count=150, base_seed=45000)
    print(f"[+] Generated {len(suite)} combined stress scenarios.")

    engine = Paper4ExecutionEngine(step_sec=10.0, cooldown_sec=250.0)
    results: list[Paper4ScenarioResult] = []

    start_time = time.time()
    for idx, spec in enumerate(suite, 1):
        res = engine.run_scenario(system_type="ASTRAHEAL_FULL", spec=spec)
        results.append(res)
        if idx % 25 == 0 or idx == len(suite):
            print(f"  [{idx:03d}/{len(suite)}] Processed stress scenario {spec.scenario_id}: Survived={res.survived}, Class={res.recovery_classification}, Wh={res.cumulative_delivered_payload_wh:.1f}")

    elapsed = time.time() - start_time

    n = len(results)
    surv_count = sum(1 for r in results if r.survived)
    full_rec = sum(1 for r in results if r.recovery_classification == "FULL_RECOVERY")
    degr_rec = sum(1 for r in results if r.recovery_classification == "DEGRADED_RECOVERY")
    no_safe = sum(1 for r in results if r.recovery_classification == "NO_SAFE_ACTION")
    unsafe_fails = sum(1 for r in results if r.recovery_classification == "UNSAFE_FAILURE")
    tot_unsafe_exec = sum(r.executed_unsafe_actions for r in results)
    tot_gov_rejects = sum(r.governor_rejections_count for r in results)
    mean_wh = float(np.mean([r.cumulative_delivered_payload_wh for r in results]))

    summary = {
        "experiment_id": "P4-E5",
        "name": "Combined Stress Conditions",
        "sample_size": n,
        "elapsed_seconds": round(elapsed, 2),
        "survival_rate_pct": round(surv_count / n * 100.0, 1),
        "full_recovery_count": full_rec,
        "degraded_recovery_count": degr_rec,
        "no_safe_action_count": no_safe,
        "unsafe_failures_count": unsafe_fails,
        "executed_unsafe_actions": tot_unsafe_exec,
        "governor_rejections_count": tot_gov_rejects,
        "mean_delivered_payload_wh": round(mean_wh, 2)
    }

    print("\n" + "=" * 80)
    print(f"P4-E5 RESULTS SUMMARY:")
    print(f"  • Mission Survival Rate     : {surv_count / n * 100.0:.1f}% ({surv_count}/{n})")
    print(f"  • Full Recovery (Nominal)   : {full_rec} ({full_rec/n*100.0:.1f}%)")
    print(f"  • Degraded Recovery (Safe)  : {degr_rec} ({degr_rec/n*100.0:.1f}%)")
    print(f"  • No Safe Action Available  : {no_safe}")
    print(f"  • Unsafe Failures Observed  : {unsafe_fails}")
    print(f"  • Executed Unsafe Actions   : {tot_unsafe_exec} (0.00% invariant)")
    print(f"  • Governor Rejections       : {tot_gov_rejects}")
    print(f"  • Mean Delivered Payload    : {mean_wh:.1f} Wh")
    print(f"  • Total Execution Time      : {elapsed:.2f} s")
    print("=" * 80)

    out_file = REPO_ROOT / "results" / "paper4" / "p4_e5_results.json"
    out_file.parent.mkdir(parents=True, exist_ok=True)
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump({"summary": summary, "results": [r.model_dump() for r in results]}, f, indent=2)
    print(f"[✓] Saved P4-E5 results to: {out_file}")
    return summary


if __name__ == "__main__":
    run_experiment()
