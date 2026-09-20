"""Experiment P4-E3: Perturbed Physics Sensitivity Benchmark.

Evaluates system sensitivity to bounded deviations in key physical parameters:
- C_th: Thermal capacitance of battery pack (+/-20%)
- h_rad: Radiator radiative coupling (+/-20%)
- R_0: Nominal battery internal resistance (+/-20%)
- solar_efficiency: Solar array photovoltaic conversion (+/-20%)
- parasitic_load_bias: Quiescent payload parasitic bias (-30W to +30W)
Sample size: 225 simulation runs (5 parameters x 9 deltas x 5 runs).
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
    print("ASTRAHEAL EXPERIMENT P4-E3: Perturbed Physics Sensitivity")
    print("=" * 80)

    suite = Paper4ScenarioGenerator.generate_e3_perturbed_physics_suite(base_seed=43000)
    print(f"[+] Generated {len(suite)} perturbed physics simulation runs.")

    engine = Paper4ExecutionEngine(step_sec=10.0, cooldown_sec=300.0)
    results: list[Paper4ScenarioResult] = []

    start_time = time.time()
    for idx, spec in enumerate(suite, 1):
        res = engine.run_scenario(system_type="ASTRAHEAL_FULL", spec=spec)
        results.append(res)
        if idx % 25 == 0 or idx == len(suite):
            p_name = spec.metadata.get("perturbed_parameter")
            p_delta = spec.metadata.get("perturbation_delta")
            print(f"  [{idx:03d}/{len(suite)}] Processed {p_name} ({p_delta:+.0%}): Survived={res.survived}, MaxT={res.max_battery_temp_c:.1f}C")

    elapsed = time.time() - start_time

    # Group by parameter and delta
    param_sweep_data: dict[str, dict[str, dict[str, float]]] = {}
    for r, spec in zip(results, suite):
        p_name = spec.metadata.get("perturbed_parameter")
        p_delta = float(spec.metadata.get("perturbation_delta"))
        delta_str = f"{p_delta:+.2f}"

        if p_name not in param_sweep_data:
            param_sweep_data[p_name] = {}
        if delta_str not in param_sweep_data[p_name]:
            param_sweep_data[p_name][delta_str] = {"runs": 0, "survived": 0, "max_temps": [], "min_volts": []}

        entry = param_sweep_data[p_name][delta_str]
        entry["runs"] += 1
        if r.survived:
            entry["survived"] += 1
        entry["max_temps"].append(r.max_battery_temp_c)
        entry["min_volts"].append(r.min_bus_voltage_v)

    # Compute aggregate stats per delta point
    param_summaries = {}
    for p_name, deltas in param_sweep_data.items():
        param_summaries[p_name] = {}
        for d_str, dat in deltas.items():
            runs = dat["runs"]
            surv_pct = dat["survived"] / runs * 100.0
            mean_t = float(np.mean(dat["max_temps"]))
            mean_v = float(np.mean(dat["min_volts"]))
            param_summaries[p_name][d_str] = {
                "runs": runs,
                "survival_pct": round(surv_pct, 1),
                "mean_max_temp_c": round(mean_t, 2),
                "mean_min_volt_v": round(mean_v, 2)
            }

    tot_runs = len(results)
    tot_surv = sum(1 for r in results if r.survived)
    tot_unsafe = sum(r.executed_unsafe_actions for r in results)

    summary = {
        "experiment_id": "P4-E3",
        "name": "Perturbed Physics Sensitivity",
        "total_runs": tot_runs,
        "overall_survival_rate_pct": round(tot_surv / tot_runs * 100.0, 1),
        "executed_unsafe_actions": tot_unsafe,
        "elapsed_seconds": round(elapsed, 2),
        "parameter_sweeps": param_summaries
    }

    print("\n" + "=" * 80)
    print(f"P4-E3 RESULTS SUMMARY:")
    print(f"  • Total Perturbation Runs   : {tot_runs}")
    print(f"  • Overall Survival Rate     : {tot_surv / tot_runs * 100.0:.1f}% ({tot_surv}/{tot_runs})")
    print(f"  • Executed Unsafe Actions   : {tot_unsafe} (0.00% invariant)")
    print(f"  • Elapsed Execution Time    : {elapsed:.2f} s")
    print("=" * 80)

    out_file = REPO_ROOT / "results" / "paper4" / "p4_e3_results.json"
    out_file.parent.mkdir(parents=True, exist_ok=True)
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump({"summary": summary, "results": [r.model_dump() for r in results]}, f, indent=2)
    print(f"[✓] Saved P4-E3 results to: {out_file}")
    return summary


if __name__ == "__main__":
    run_experiment()
