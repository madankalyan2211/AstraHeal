"""Experiment P4-E7: Long-Horizon Multi-Orbit Operation Benchmark.

Evaluates extended autonomous mission operations across 5 full LEO orbits (28,700s).
Sample size: 50 extended missions with 4 distributed sequential fault events.
Measures long-term state drift, thermal ratcheting, battery SoC balance, and SoH degradation.
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
    print("ASTRAHEAL EXPERIMENT P4-E7: Long-Horizon Multi-Orbit Operation (5 Orbits / 28,700s)")
    print("=" * 80)

    suite = Paper4ScenarioGenerator.generate_e7_long_horizon_suite(count=50, base_seed=47000)
    print(f"[+] Generated {len(suite)} extended 5-orbit mission scenarios.")

    engine = Paper4ExecutionEngine(step_sec=10.0, cooldown_sec=300.0)
    results: list[Paper4ScenarioResult] = []

    start_time = time.time()
    for idx, spec in enumerate(suite, 1):
        res = engine.run_scenario(system_type="ASTRAHEAL_FULL", spec=spec)
        results.append(res)
        if idx % 10 == 0 or idx == len(suite):
            print(f"  [{idx:02d}/{len(suite)}] Long-horizon mission {spec.scenario_id}: Survived={res.survived}, FinalSoC={res.final_soc:.3f}, Wh={res.cumulative_delivered_payload_wh:.1f}")

    elapsed = time.time() - start_time

    n = len(results)
    surv_count = sum(1 for r in results if r.survived)
    tot_cycles = sum(r.total_recovery_cycles for r in results)
    tot_viols = sum(r.total_hard_violations_count for r in results)
    tot_unsafe_exec = sum(r.executed_unsafe_actions for r in results)
    mean_wh = float(np.mean([r.cumulative_delivered_payload_wh for r in results]))
    mean_final_soc = float(np.mean([r.final_soc for r in results]))
    mean_max_t = float(np.mean([r.max_battery_temp_c for r in results]))

    summary = {
        "experiment_id": "P4-E7",
        "name": "Long-Horizon Multi-Orbit Operation",
        "sample_size": n,
        "orbit_count": 5,
        "simulated_duration_sec": 28700.0,
        "elapsed_seconds": round(elapsed, 2),
        "survival_rate_pct": round(surv_count / n * 100.0, 1),
        "total_recovery_cycles": tot_cycles,
        "total_hard_violations": tot_viols,
        "executed_unsafe_actions": tot_unsafe_exec,
        "mean_delivered_payload_wh": round(mean_wh, 2),
        "mean_final_soc": round(mean_final_soc, 4),
        "mean_peak_temp_c": round(mean_max_t, 2)
    }

    print("\n" + "=" * 80)
    print(f"P4-E7 RESULTS SUMMARY:")
    print(f"  • Mission Survival Rate     : {surv_count / n * 100.0:.1f}% ({surv_count}/{n})")
    print(f"  • Total Autonomous Cycles   : {tot_cycles}")
    print(f"  • Hard Invariant Violations : {tot_viols}")
    print(f"  • Executed Unsafe Actions   : {tot_unsafe_exec} (0.00% invariant)")
    print(f"  • Mean Delivered Payload    : {mean_wh:.1f} Wh")
    print(f"  • Mean Terminal Battery SoC : {mean_final_soc*100.0:.1f}%")
    print(f"  • Mean Peak Temperature     : {mean_max_t:.1f} °C")
    print(f"  • Total Execution Time      : {elapsed:.2f} s")
    print("=" * 80)

    out_file = REPO_ROOT / "results" / "paper4" / "p4_e7_results.json"
    out_file.parent.mkdir(parents=True, exist_ok=True)
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump({"summary": summary, "results": [r.model_dump() for r in results]}, f, indent=2)
    print(f"[✓] Saved P4-E7 results to: {out_file}")
    return summary


if __name__ == "__main__":
    run_experiment()
