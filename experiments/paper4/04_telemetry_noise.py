"""Experiment P4-E4: Telemetry Sensor Noise Robustness Benchmark.

Evaluates system resilience across escalating additive Gaussian noise sigma in [0.005, 0.080].
Sample size: 225 evaluation runs (9 sigma values x 25 runs).
Measures diagnostic stability, epistemic uncertainty escalation, and recovery survival.
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
    print("ASTRAHEAL EXPERIMENT P4-E4: Telemetry Noise Robustness")
    print("=" * 80)

    suite = Paper4ScenarioGenerator.generate_e4_telemetry_noise_suite(base_seed=44000)
    print(f"[+] Generated {len(suite)} scenarios across 9 noise levels sigma in [0.005, 0.080].")

    engine = Paper4ExecutionEngine(step_sec=10.0, cooldown_sec=300.0)
    results: list[Paper4ScenarioResult] = []

    start_time = time.time()
    for idx, spec in enumerate(suite, 1):
        res = engine.run_scenario(system_type="ASTRAHEAL_FULL", spec=spec)
        results.append(res)
        if idx % 25 == 0 or idx == len(suite):
            sigma_val = spec.metadata.get("noise_sigma")
            print(f"  [{idx:03d}/{len(suite)}] Processed sigma={sigma_val:.3f}: Survived={res.survived}, MeanUncert={res.mean_epistemic_uncertainty:.3f}")

    elapsed = time.time() - start_time

    # Group by noise sigma
    noise_groups: dict[float, list[Paper4ScenarioResult]] = {}
    for r, spec in zip(results, suite):
        sig = float(spec.metadata.get("noise_sigma", 0.005))
        noise_groups.setdefault(sig, []).append(r)

    noise_summaries = {}
    print("\n" + "=" * 90)
    print(f"{'Noise Sigma':<14} | {'Runs':<6} | {'Survival %':<11} | {'Mean Epistemic u':<18} | {'Violations':<11} | {'Unsafe Exec'}")
    print("=" * 90)

    for sig in sorted(noise_groups.keys()):
        group = noise_groups[sig]
        n_sig = len(group)
        surv_pct = float(np.mean([1 if r.survived else 0 for r in group]) * 100.0)
        mean_u = float(np.mean([r.mean_epistemic_uncertainty for r in group]))
        tot_viols = int(sum(r.total_hard_violations_count for r in group))
        tot_unsafe = int(sum(r.executed_unsafe_actions for r in group))

        noise_summaries[f"{sig:.3f}"] = {
            "runs": n_sig,
            "survival_pct": round(surv_pct, 1),
            "mean_epistemic_uncertainty": round(mean_u, 4),
            "total_violations": tot_viols,
            "executed_unsafe_actions": tot_unsafe
        }
        print(f"{sig:<14.3f} | {n_sig:<6d} | {surv_pct:>9.1f}% | {mean_u:>16.4f}   | {tot_viols:>11d} | {tot_unsafe:>11d}")

    print("=" * 90)

    overall_summary = {
        "experiment_id": "P4-E4",
        "name": "Telemetry Noise Robustness",
        "total_runs": len(results),
        "elapsed_seconds": round(elapsed, 2),
        "noise_level_results": noise_summaries
    }

    out_file = REPO_ROOT / "results" / "paper4" / "p4_e4_results.json"
    out_file.parent.mkdir(parents=True, exist_ok=True)
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump({"summary": overall_summary, "results": [r.model_dump() for r in results]}, f, indent=2)
    print(f"[✓] Saved P4-E4 results to: {out_file}")
    return overall_summary


if __name__ == "__main__":
    run_experiment()
