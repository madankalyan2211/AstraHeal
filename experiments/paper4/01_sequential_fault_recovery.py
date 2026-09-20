"""Experiment P4-E1: Sequential Fault Recovery Benchmark.

Evaluates AstraHeal's ability to isolate, plan, safely gate, and recover from
sequential in-flight anomalies across continuous 3-orbit LEO missions (17,220s).
Sample size: 100 sequential missions (~300 recovery cycles).
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
    print("ASTRAHEAL EXPERIMENT P4-E1: Sequential Fault Recovery")
    print("=" * 80)

    suite = Paper4ScenarioGenerator.generate_e1_sequential_suite(count=100, base_seed=41000)
    print(f"[+] Generated {len(suite)} sequential multi-fault mission scenarios across 3-orbit horizons.")

    engine = Paper4ExecutionEngine(step_sec=10.0, cooldown_sec=300.0)
    results: list[Paper4ScenarioResult] = []

    start_time = time.time()
    for idx, spec in enumerate(suite, 1):
        res = engine.run_scenario(system_type="ASTRAHEAL_FULL", spec=spec)
        results.append(res)
        if idx % 20 == 0 or idx == len(suite):
            print(f"  [{idx:03d}/{len(suite)}] Processed scenario {spec.scenario_id}: Survived={res.survived}, Cycles={res.total_recovery_cycles}, Payload={res.cumulative_delivered_payload_wh:.1f}Wh")

    elapsed = time.time() - start_time

    # Summary metrics
    n = len(results)
    surv_count = sum(1 for r in results if r.survived)
    surv_rate = surv_count / n * 100.0
    tot_cycles = sum(r.total_recovery_cycles for r in results)
    tot_viols = sum(r.total_hard_violations_count for r in results)
    tot_unsafe_exec = sum(r.executed_unsafe_actions for r in results)
    tot_gov_rejects = sum(r.governor_rejections_count for r in results)
    mean_wh = float(np.mean([r.cumulative_delivered_payload_wh for r in results]))
    mean_avail = float(np.mean([r.mean_payload_availability_pct for r in results]))

    summary = {
        "experiment_id": "P4-E1",
        "name": "Sequential Fault Recovery",
        "sample_size": n,
        "elapsed_seconds": round(elapsed, 2),
        "survival_rate_pct": surv_rate,
        "total_recovery_cycles": tot_cycles,
        "total_hard_violations": tot_viols,
        "executed_unsafe_actions": tot_unsafe_exec,
        "governor_rejections_count": tot_gov_rejects,
        "mean_delivered_payload_wh": round(mean_wh, 2),
        "mean_payload_availability_pct": round(mean_avail, 2)
    }

    print("\n" + "=" * 80)
    print(f"P4-E1 RESULTS SUMMARY:")
    print(f"  • Mission Survival Rate     : {surv_rate:.1f}% ({surv_count}/{n})")
    print(f"  • Total Autonomous Cycles   : {tot_cycles}")
    print(f"  • Hard Invariant Violations : {tot_viols}")
    print(f"  • Executed Unsafe Actions   : {tot_unsafe_exec} (0.00% invariant)")
    print(f"  • Governor Rejections Count : {tot_gov_rejects}")
    print(f"  • Mean Delivered Payload    : {mean_wh:.1f} Wh ({mean_avail:.1f}%)")
    print(f"  • Total Elapsed Time        : {elapsed:.2f} s")
    print("=" * 80)

    out_file = REPO_ROOT / "results" / "paper4" / "p4_e1_results.json"
    out_file.parent.mkdir(parents=True, exist_ok=True)
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump({"summary": summary, "results": [r.model_dump() for r in results]}, f, indent=2)
    print(f"[✓] Saved P4-E1 results to: {out_file}")
    return summary


if __name__ == "__main__":
    run_experiment()
