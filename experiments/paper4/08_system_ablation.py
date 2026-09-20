"""Experiment P4-E8: End-to-End System Ablation Benchmark.

Comparative evaluation of 6 distinct system architectures across 50 standardized scenarios:
1. ASTRAHEAL_FULL: Full 5-stage integrated architecture
2. ABLATION_NO_UNCERTAINTY: Planning without Dirichlet evidential epistemic uncertainty
3. ABLATION_NO_LOOKAHEAD: Static single-step heuristic mapping without digital-twin lookahead
4. ABLATION_NO_GOVERNOR: Ungoverned AI (proposals dispatched without safety governor gating)
5. BASELINE_PASSIVE: Passive observation (unmitigated failure)
6. BASELINE_BLIND_SAFE_MODE: Traditional threshold FDIR dropping unconditionally to Safe Mode

Sample size: 300 total simulation runs (6 systems x 50 scenarios).
Measures: Mission Survival Rate (%), Hard Violations, Executed Unsafe Actions, Delivered Payload (Wh).
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
    print("ASTRAHEAL EXPERIMENT P4-E8: End-to-End System Ablation Matrix")
    print("=" * 80)

    suite = Paper4ScenarioGenerator.generate_e8_ablation_suite(count=50, base_seed=48000)
    print(f"[+] Loaded {len(suite)} standardized multi-cycle ablation scenarios.")

    architectures = [
        "ASTRAHEAL_FULL",
        "ABLATION_NO_UNCERTAINTY",
        "ABLATION_NO_LOOKAHEAD",
        "ABLATION_NO_GOVERNOR",
        "BASELINE_PASSIVE",
        "BASELINE_BLIND_SAFE_MODE"
    ]

    engine = Paper4ExecutionEngine(step_sec=10.0, cooldown_sec=300.0)
    matrix_results: dict[str, list[Paper4ScenarioResult]] = {}

    start_time = time.time()
    for sys_name in architectures:
        print(f"\n[+] Executing Architecture: {sys_name} ({len(suite)} runs)...")
        sys_res_list: list[Paper4ScenarioResult] = []
        for idx, spec in enumerate(suite, 1):
            res = engine.run_scenario(system_type=sys_name, spec=spec)
            sys_res_list.append(res)
            if idx % 25 == 0 or idx == len(suite):
                print(f"    ↳ [{idx:02d}/{len(suite)}] Survived={res.survived}, Viols={res.total_hard_violations_count}, Wh={res.cumulative_delivered_payload_wh:.1f}")
        matrix_results[sys_name] = sys_res_list

    elapsed = time.time() - start_time

    # Compute comparative metrics table
    sys_summaries = {}
    print("\n" + "=" * 110)
    print(f"{'System Architecture':<28} | {'Survival %':<11} | {'Hard Viols':<11} | {'Unsafe Exec':<12} | {'Payload Wh':<12} | {'Payload %'}")
    print("=" * 110)

    for sys_name in architectures:
        r_list = matrix_results[sys_name]
        n = len(r_list)
        surv_count = sum(1 for r in r_list if r.survived)
        surv_pct = surv_count / n * 100.0
        tot_viols = int(sum(r.total_hard_violations_count for r in r_list))
        tot_unsafe_exec = int(sum(r.executed_unsafe_actions for r in r_list))
        mean_wh = float(np.mean([r.cumulative_delivered_payload_wh for r in r_list]))
        mean_avail = float(np.mean([r.mean_payload_availability_pct for r in r_list]))

        sys_summaries[sys_name] = {
            "runs": n,
            "survival_pct": round(surv_pct, 1),
            "survived_count": surv_count,
            "total_hard_violations": tot_viols,
            "executed_unsafe_actions": tot_unsafe_exec,
            "mean_delivered_payload_wh": round(mean_wh, 2),
            "mean_payload_availability_pct": round(mean_avail, 2)
        }
        print(f"{sys_name:<28} | {surv_pct:>9.1f}% | {tot_viols:>11d} | {tot_unsafe_exec:>12d} | {mean_wh:>10.1f}Wh | {mean_avail:>9.1f}%")

    print("=" * 110)

    overall_summary = {
        "experiment_id": "P4-E8",
        "name": "End-to-End System Ablation Matrix",
        "total_runs": len(architectures) * len(suite),
        "elapsed_seconds": round(elapsed, 2),
        "architectures": sys_summaries
    }

    out_file = REPO_ROOT / "results" / "paper4" / "p4_e8_results.json"
    out_file.parent.mkdir(parents=True, exist_ok=True)
    serialized = {sys_k: [r.model_dump() for r in r_list] for sys_k, r_list in matrix_results.items()}
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump({"summary": overall_summary, "results_by_architecture": serialized}, f, indent=2)
    print(f"[✓] Saved P4-E8 results to: {out_file}")
    return overall_summary


if __name__ == "__main__":
    run_experiment()
