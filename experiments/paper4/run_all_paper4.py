"""Master Orchestrator for AstraHeal Paper 4 Experiments.

Sequentially executes the complete Paper 4 experimental suite (P4-E1 to P4-E8),
aggregates cross-experiment metrics, and saves results/paper4/master_benchmark_summary.json.
"""

import importlib
import json
import sys
import time
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

exp1 = importlib.import_module("experiments.paper4.01_sequential_fault_recovery")
exp2 = importlib.import_module("experiments.paper4.02_repeated_recovery_cycles")
exp3 = importlib.import_module("experiments.paper4.03_perturbed_physics")
exp4 = importlib.import_module("experiments.paper4.04_telemetry_noise")
exp5 = importlib.import_module("experiments.paper4.05_combined_stress")
exp6 = importlib.import_module("experiments.paper4.06_compound_faults")
exp7 = importlib.import_module("experiments.paper4.07_long_horizon_operation")
exp8 = importlib.import_module("experiments.paper4.08_system_ablation")


def run_all():
    print("=" * 90)
    print("ASTRAHEAL PAPER 4 — MASTER EXPERIMENTAL SUITE EXECUTION")
    print("AstraHeal: Robust Multi-Cycle Autonomous Fault Recovery Under Perturbed Spacecraft Conditions")
    print("=" * 90)

    start_total = time.time()
    master_summary = {}

    # P4-E1
    print("\n>>> Launching Experiment P4-E1 (Sequential Recovery)...")
    s1 = exp1.run_experiment()
    master_summary["P4-E1"] = s1

    # P4-E2
    print("\n>>> Launching Experiment P4-E2 (Repeated Cycles)...")
    s2 = exp2.run_experiment()
    master_summary["P4-E2"] = s2

    # P4-E3
    print("\n>>> Launching Experiment P4-E3 (Perturbed Physics)...")
    s3 = exp3.run_experiment()
    master_summary["P4-E3"] = s3

    # P4-E4
    print("\n>>> Launching Experiment P4-E4 (Telemetry Noise)...")
    s4 = exp4.run_experiment()
    master_summary["P4-E4"] = s4

    # P4-E5
    print("\n>>> Launching Experiment P4-E5 (Combined Stress)...")
    s5 = exp5.run_experiment()
    master_summary["P4-E5"] = s5

    # P4-E6
    print("\n>>> Launching Experiment P4-E6 (Compound Faults)...")
    s6 = exp6.run_experiment()
    master_summary["P4-E6"] = s6

    # P4-E7
    print("\n>>> Launching Experiment P4-E7 (Long-Horizon Multi-Orbit)...")
    s7 = exp7.run_experiment()
    master_summary["P4-E7"] = s7

    # P4-E8
    print("\n>>> Launching Experiment P4-E8 (System Ablation)...")
    s8 = exp8.run_experiment()
    master_summary["P4-E8"] = s8

    total_time = time.time() - start_total

    master_summary["meta"] = {
        "suite_name": "AstraHeal Paper 4 Complete Benchmark",
        "total_experiments": 8,
        "total_execution_seconds": round(total_time, 2),
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S UTC", time.gmtime())
    }

    out_file = REPO_ROOT / "results" / "paper4" / "master_benchmark_summary.json"
    out_file.parent.mkdir(parents=True, exist_ok=True)
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(master_summary, f, indent=2)

    print("\n" + "=" * 90)
    print("ALL PAPER 4 EXPERIMENTS COMPLETED SUCCESSFULLY!")
    print(f"Total Execution Time: {total_time:.2f} s")
    print(f"Master Benchmark Summary saved to: {out_file}")
    print("=" * 90)


if __name__ == "__main__":
    run_all()
