"""Experiment P4-E2: Repeated Recovery Cycles Stability Benchmark.

Evaluates system stability over varying cycle counts k in {1, 2, 3, 5, 8, 10}.
Sample size: 120 mission runs (20 runs per cycle target).
Measures cumulative state drift, payload degradation, and governor rejection rates.
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
    print("ASTRAHEAL EXPERIMENT P4-E2: Repeated Recovery Cycles Stability")
    print("=" * 80)

    suite = Paper4ScenarioGenerator.generate_e2_repeated_cycles_suite(base_seed=42000)
    print(f"[+] Generated {len(suite)} scenarios across cycle targets k in {{1, 2, 3, 5, 8, 10}}.")

    engine = Paper4ExecutionEngine(step_sec=10.0, cooldown_sec=250.0)
    results: list[Paper4ScenarioResult] = []

    start_time = time.time()
    for idx, spec in enumerate(suite, 1):
        res = engine.run_scenario(system_type="ASTRAHEAL_FULL", spec=spec)
        results.append(res)
        if idx % 20 == 0 or idx == len(suite):
            k_val = spec.metadata.get("target_cycle_count")
            print(f"  [{idx:03d}/{len(suite)}] Processed k={k_val} scenario {spec.scenario_id}: Survived={res.survived}, ExecCycles={res.total_recovery_cycles}")

    elapsed = time.time() - start_time

    # Group by cycle count k
    cycle_groups: dict[int, list[Paper4ScenarioResult]] = {}
    for r, spec in zip(results, suite):
        k = spec.metadata.get("target_cycle_count", 1)
        cycle_groups.setdefault(k, []).append(r)

    group_summaries = {}
    print("\n" + "=" * 90)
    print(f"{'Target Cycles (k)':<18} | {'Runs':<6} | {'Survival %':<11} | {'Delivered Wh':<14} | {'Violations':<11} | {'Unsafe Exec'}")
    print("=" * 90)

    for k in sorted(cycle_groups.keys()):
        group = cycle_groups[k]
        n_k = len(group)
        surv_pct = float(np.mean([1 if r.survived else 0 for r in group]) * 100.0)
        mean_wh = float(np.mean([r.cumulative_delivered_payload_wh for r in group]))
        tot_viols = int(sum(r.total_hard_violations_count for r in group))
        tot_unsafe = int(sum(r.executed_unsafe_actions for r in group))

        group_summaries[k] = {
            "runs": n_k,
            "survival_pct": surv_pct,
            "mean_delivered_payload_wh": round(mean_wh, 2),
            "total_violations": tot_viols,
            "executed_unsafe_actions": tot_unsafe
        }
        print(f"{k:<18d} | {n_k:<6d} | {surv_pct:>9.1f}% | {mean_wh:>11.1f} Wh | {tot_viols:>11d} | {tot_unsafe:>11d}")

    print("=" * 90)

    overall_summary = {
        "experiment_id": "P4-E2",
        "name": "Repeated Recovery Cycles",
        "total_runs": len(results),
        "elapsed_seconds": round(elapsed, 2),
        "cycle_group_results": group_summaries
    }

    out_file = REPO_ROOT / "results" / "paper4" / "p4_e2_results.json"
    out_file.parent.mkdir(parents=True, exist_ok=True)
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump({"summary": overall_summary, "results": [r.model_dump() for r in results]}, f, indent=2)
    print(f"[✓] Saved P4-E2 results to: {out_file}")
    return overall_summary


if __name__ == "__main__":
    run_experiment()
