"""Experiment 09: Full Tri-System Research Benchmark & Adversarial Stress Suite.

Compares:
1. Baseline A: No Autonomous Recovery (Detection Only)
2. Baseline B: Fixed Rule Heuristic (Immediate Blind Safe Mode)
3. AstraHeal: Autonomous Counterfactual Lookahead + Deterministic Safety Governor Gating

Evaluates across 8 adversarial scenarios:
- Mission Survival Rate (%)
- Hard Constraint Violations Count
- Mean Preserved Science Payload Utility (%)
- Usable Energy Margin (Wh)
- Thermal Safety Margin (°C)
"""

import sys
import json
from pathlib import Path

# Ensure repository root is in sys.path
REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from evaluation.scenarios import BenchmarkScenarioGenerator
from evaluation.benchmark import TriSystemBenchmarkRunner


def run_experiment():
    print("=" * 85)
    print("ASTRAHEAL EXPERIMENT 09: Full Tri-System Comparative Benchmark & Stress Test")
    print("=" * 85)

    suite = BenchmarkScenarioGenerator.get_full_evaluation_suite(random_seed=42)
    print(f"[+] Loaded evaluation suite with {len(suite)} diverse adversarial mission scenarios.")

    runner = TriSystemBenchmarkRunner(simulation_step_sec=10.0)
    print("[+] Executing Tri-System benchmark matrix (Baseline A vs Baseline B vs AstraHeal)...")
    summaries = runner.run_full_suite(suite)

    # 1. Print Comparative Summary Table
    print("\n" + "=" * 105)
    print(f"{'System Architecture':<28} | {'Survival %':<11} | {'Hard Viols':<11} | {'Payload %':<11} | {'Final SoC':<10} | {'Max Temp'}")
    print("=" * 105)

    for sys_name, sum_data in summaries.items():
        print(f"{sys_name:<28} | {sum_data.survival_rate_pct:>9.1f}% | {sum_data.total_hard_violations:>11d} | {sum_data.mean_payload_availability_pct:>9.1f}% | {sum_data.mean_final_soc*100:>8.1f}% | {sum_data.mean_max_temperature_c:>6.1f}°C")

    print("=" * 105)

    # 2. Detailed Scenario Breakdown
    print("\nScenario Breakdown (AstraHeal Performance):")
    for res in summaries["ASTRAHEAL"].detailed_results:
        surv_str = "SURVIVED" if res.survived else "FAILED"
        print(f"  • [{res.scenario_id}] {res.scenario_name:<50} -> {surv_str} | Viols={res.hard_constraint_violations_count} | Payload={res.payload_availability_pct:.0f}%")

    # 3. Save Raw JSON Results
    out_json = Path("evaluation/09_full_benchmark_results.json")
    out_json.parent.mkdir(parents=True, exist_ok=True)
    
    serialized_dict = {k: v.model_dump() for k, v in summaries.items()}
    with open(out_json, "w", encoding="utf-8") as f:
        json.dump(serialized_dict, f, indent=2)
    print(f"\n[✓] Raw benchmark data saved to: {out_json}")

    # 4. Publication-Quality Multi-Metric Comparison Plot
    fig, axes = plt.subplots(1, 3, figsize=(15, 5))

    systems = ["Baseline A\n(No Recovery)", "Baseline B\n(Blind Safe Mode)", "AstraHeal\n(Safety-Governed)"]
    sys_keys = ["BASELINE_A", "BASELINE_B", "ASTRAHEAL"]
    colors = ["#d62728", "#ff7f0e", "#2ca02c"]

    # Metric 1: Survival Rate (%)
    surv_rates = [summaries[k].survival_rate_pct for k in sys_keys]
    bars1 = axes[0].bar(systems, surv_rates, color=colors, edgecolor="black", width=0.55)
    axes[0].set_ylabel("Mission Survival Rate [%]", fontweight="bold")
    axes[0].set_ylim(0, 115)
    axes[0].set_title("Mission Survival Rate", fontweight="bold", pad=10)
    axes[0].grid(True, linestyle=":", alpha=0.5, axis="y")
    for bar in bars1:
        yval = bar.get_height()
        axes[0].text(bar.get_x() + bar.get_width()/2.0, yval + 2, f"{yval:.1f}%", ha="center", va="bottom", fontweight="bold")

    # Metric 2: Total Hard Constraint Violations (Lower is better)
    violations = [summaries[k].total_hard_violations for k in sys_keys]
    bars2 = axes[1].bar(systems, violations, color=colors, edgecolor="black", width=0.55)
    axes[1].set_ylabel("Total Hard Constraint Violations", fontweight="bold")
    axes[1].set_title("Hard Safety Constraint Violations", fontweight="bold", pad=10)
    axes[1].grid(True, linestyle=":", alpha=0.5, axis="y")
    for bar in bars2:
        yval = bar.get_height()
        axes[1].text(bar.get_x() + bar.get_width()/2.0, yval + 0.5, f"{int(yval)}", ha="center", va="bottom", fontweight="bold")

    # Metric 3: Preserved Payload Capability (%)
    payloads = [summaries[k].mean_payload_availability_pct for k in sys_keys]
    bars3 = axes[2].bar(systems, payloads, color=colors, edgecolor="black", width=0.55)
    axes[2].set_ylabel("Mean Payload Availability [%]", fontweight="bold")
    axes[2].set_ylim(0, 115)
    axes[2].set_title("Science Payload Capability Preserved", fontweight="bold", pad=10)
    axes[2].grid(True, linestyle=":", alpha=0.5, axis="y")
    for bar in bars3:
        yval = bar.get_height()
        axes[2].text(bar.get_x() + bar.get_width()/2.0, yval + 2, f"{yval:.1f}%", ha="center", va="bottom", fontweight="bold")

    fig.suptitle("AstraHeal Stage 11: Comparative Benchmark Across 8 Stress Scenarios", fontsize=14, fontweight="bold", y=1.02)
    plt.tight_layout()
    plot_path = Path("docs/figures/09_tri_system_benchmark.png")
    plot_path.parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(plot_path, dpi=200, bbox_inches="tight")
    plt.close(fig)
    print(f"[✓] Saved comparative benchmark plots to: {plot_path}")

    print("\n[✓] Stage 11 Research Benchmark & Stress Testing Completed.")


if __name__ == "__main__":
    run_experiment()
