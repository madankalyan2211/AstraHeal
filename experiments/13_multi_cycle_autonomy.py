"""Experiment 13: Multi-Cycle Autonomous Recovery Benchmark & Tri-System Comparative Evaluation.

Evaluates:
- Sequential independent in-flight anomalies across 3 full LEO orbits (17,220s)
- Debounced multi-cycle event engine enabling repeated autonomous reasoning
- Full decision traces across cycles (CYCLE_001, CYCLE_002, ...)
- Tri-System comparison: Baseline A (Passive) vs Baseline B (Blind Safe Mode) vs AstraHeal
- Mission survival, energy delivery integral (Wh), hard violation time, and governor rejections
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

from evaluation.multi_cycle_benchmark import MultiCycleBenchmarkSuite, MultiCycleBenchmarkRunner


def run_experiment():
    print("=" * 85)
    print("ASTRAHEAL EXPERIMENT 13: Multi-Cycle Autonomous Recovery Benchmark")
    print("=" * 85)

    suite = MultiCycleBenchmarkSuite.get_standard_multi_cycle_suite()
    print(f"[+] Loaded {len(suite)} multi-cycle sequential mission scenarios across 3-orbit horizons.")

    runner = MultiCycleBenchmarkRunner(simulation_step_sec=10.0, event_cooldown_sec=300.0)
    print("[+] Executing Multi-Cycle Tri-System matrix (Baseline A vs Baseline B vs AstraHeal)...")
    results = runner.run_full_suite(suite)

    # 1. Mission-Level Summary Table
    print("\n" + "=" * 115)
    print(f"{'System Architecture':<24} | {'Survival %':<11} | {'Hard Viols':<11} | {'Payload Wh':<12} | {'Payload %':<11} | {'Cycles':<7} | {'Gov Rejects'}")
    print("=" * 115)

    systems = ["BASELINE_A", "BASELINE_B", "ASTRAHEAL"]
    sys_summaries = {}

    for sys_name in systems:
        metrics_list = results[sys_name]
        n = len(metrics_list)
        surv_pct = float(np.mean([1 if m.survived else 0 for m in metrics_list]) * 100.0)
        tot_viols = int(sum(m.total_hard_violations_count for m in metrics_list))
        mean_wh = float(np.mean([m.cumulative_delivered_payload_wh for m in metrics_list]))
        mean_payload_pct = float(np.mean([m.mean_payload_availability_pct for m in metrics_list]))
        tot_cycles = int(sum(m.total_recovery_cycles for m in metrics_list))
        tot_gov_rejects = int(sum(m.governor_rejections_count for m in metrics_list))

        sys_summaries[sys_name] = {
            "survival_pct": surv_pct,
            "total_violations": tot_viols,
            "mean_delivered_payload_wh": mean_wh,
            "mean_payload_pct": mean_payload_pct,
            "total_cycles": tot_cycles,
            "governor_rejections": tot_gov_rejects
        }

        print(f"{sys_name:<24} | {surv_pct:>9.1f}% | {tot_viols:>11d} | {mean_wh:>10.1f}Wh | {mean_payload_pct:>9.1f}% | {tot_cycles:>7d} | {tot_gov_rejects:>11d}")

    print("=" * 115)

    # 2. Detailed Recovery Cycle Decision Traces for AstraHeal
    print("\nAstraHeal Sequential Recovery Cycle Decision Traces:")
    for scen_m in results["ASTRAHEAL"]:
        print(f"\n[Scenario: {scen_m.scenario_id}] {scen_m.scenario_name}")
        print(f"  • Outcome: {'SURVIVED' if scen_m.survived else 'FAILED'} | Hard Violations: {scen_m.total_hard_violations_count} | Payload Delivered: {scen_m.cumulative_delivered_payload_wh:.1f} Wh ({scen_m.mean_payload_availability_pct:.1f}%)")
        
        if scen_m.recovery_cycles:
            for c in scen_m.recovery_cycles:
                print(f"    ↳ [{c.cycle_id} at t={c.trigger_time_sec:.0f}s] Diag: {c.diagnosis_status}->{c.primary_failure_mode} (u_ep={c.epistemic_uncertainty:.2f}) | Comm: {c.comm_decision} | Action: {c.selected_action_id} | Gov: {c.governor_verdict} (Rejects={c.rejected_candidates_count})")
        else:
            print("    ↳ (No anomaly thresholds breached; nominal flight uninterrupted)")

    # 3. Save Output JSON
    out_json = Path("evaluation/13_multi_cycle_results.json")
    out_json.parent.mkdir(parents=True, exist_ok=True)
    serialized = {sys_k: [m.model_dump() for m in m_list] for sys_k, m_list in results.items()}
    with open(out_json, "w", encoding="utf-8") as f:
        json.dump({"summary": sys_summaries, "scenarios": serialized}, f, indent=2)
    print(f"\n[✓] Multi-cycle benchmark data saved to: {out_json}")

    # 4. Generate Publication-Quality Figure
    fig, axes = plt.subplots(1, 3, figsize=(16, 5))
    sys_labels = ["Baseline A\n(Passive)", "Baseline B\n(Blind Safe Mode)", "AstraHeal\n(Multi-Cycle Autonomy)"]
    colors = ["#d62728", "#ff7f0e", "#2ca02c"]

    # Metric 1: Survival Rate (%)
    surv_rates = [sys_summaries[s]["survival_pct"] for s in systems]
    bars1 = axes[0].bar(sys_labels, surv_rates, color=colors, edgecolor="black", width=0.55)
    axes[0].set_ylabel("Mission Survival Rate [%]", fontweight="bold")
    axes[0].set_ylim(0, 115)
    axes[0].set_title("Mission Survival Rate (Multi-Cycle)", fontweight="bold", pad=10)
    axes[0].grid(True, linestyle=":", alpha=0.5, axis="y")
    for bar in bars1:
        yval = bar.get_height()
        axes[0].text(bar.get_x() + bar.get_width()/2.0, yval + 2, f"{yval:.1f}%", ha="center", va="bottom", fontweight="bold")

    # Metric 2: Total Energy Delivered to Science Payloads (Wh)
    payload_whs = [sys_summaries[s]["mean_delivered_payload_wh"] for s in systems]
    bars2 = axes[1].bar(sys_labels, payload_whs, color=colors, edgecolor="black", width=0.55)
    axes[1].set_ylabel("Delivered Payload Energy [Wh]", fontweight="bold")
    axes[1].set_title("Cumulative Science Payload Energy Delivered", fontweight="bold", pad=10)
    axes[1].grid(True, linestyle=":", alpha=0.5, axis="y")
    for bar in bars2:
        yval = bar.get_height()
        axes[1].text(bar.get_x() + bar.get_width()/2.0, yval + 10, f"{yval:.1f} Wh", ha="center", va="bottom", fontweight="bold")

    # Metric 3: Total Hard Safety Violations (Lower is Better)
    violations = [sys_summaries[s]["total_violations"] for s in systems]
    bars3 = axes[2].bar(sys_labels, violations, color=colors, edgecolor="black", width=0.55)
    axes[2].set_ylabel("Total Hard Constraint Violations", fontweight="bold")
    axes[2].set_title("Hard Safety Violations (Lower is Better)", fontweight="bold", pad=10)
    axes[2].grid(True, linestyle=":", alpha=0.5, axis="y")
    for bar in bars3:
        yval = bar.get_height()
        axes[2].text(bar.get_x() + bar.get_width()/2.0, yval + 10, f"{int(yval)}", ha="center", va="bottom", fontweight="bold")

    fig.suptitle("AstraHeal Stage 13: Multi-Cycle Autonomous Recovery Benchmark Across 3-Orbit Horizons", fontsize=14, fontweight="bold", y=1.02)
    plt.tight_layout()
    plot_path = Path("docs/figures/13_multi_cycle_autonomy.png")
    plot_path.parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(plot_path, dpi=200, bbox_inches="tight")
    plt.close(fig)
    print(f"[✓] Saved multi-cycle benchmark figure to: {plot_path}")

    print("\n[✓] Stage 13 Multi-Cycle Autonomy Experiment Completed.")


if __name__ == "__main__":
    run_experiment()
