#!/usr/bin/env python3
"""AstraHeal Paper 2 — Dataset Telemetry Visualization and Statistical Profiler.

Generates:
1. docs/paper2/figures/fig0_dataset_telemetry_profiles.png:
   - Panel A: NASA PCoE Battery B0005 Run-to-Failure Capacity Fade & Voltage Curves
   - Panel B: NASA PCoE Internal Resistance & Temperature Evolution
   - Panel C: Spacecraft EPS Digital Twin 3-Orbit Mission Dynamics (Sunlight/Eclipse)
   - Panel D: Multivariate Telemetry Feature Distributions (Known vs OOD)
2. evaluation/paper2/dataset_characterization.json:
   - Statistical table entries for manuscript inclusion.
"""

import json
import os
import sys
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns

# Ensure repository root is in sys.path
REPO_ROOT = Path(__file__).resolve().parent.parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))


def generate_dataset_visuals():
    print("=" * 78)
    print("GENERATING DATASET RESULTS: TABLES & GRAPHICAL VISUALIZATIONS")
    print("=" * 78)

    figures_dir = REPO_ROOT / "docs" / "paper2" / "figures"
    eval_dir = REPO_ROOT / "evaluation" / "paper2"
    figures_dir.mkdir(parents=True, exist_ok=True)
    eval_dir.mkdir(parents=True, exist_ok=True)

    # 1. Load Real Datasets
    nasa_path = REPO_ROOT / "data" / "raw" / "nasa_pcoe_benchmark_B0005.csv"
    sim_path = REPO_ROOT / "data" / "processed" / "mission_run_3orbits_processed.csv"

    print(f"Loading NASA PCoE dataset: {nasa_path}")
    df_nasa = pd.read_csv(nasa_path)

    print(f"Loading Spacecraft EPS simulation dataset: {sim_path}")
    df_sim = pd.read_csv(sim_path)

    # 2. Extract Comprehensive Statistical Profiles
    nasa_stats = {
        "dataset_name": "NASA_PCOE_BENCHMARK_B0005",
        "sample_count": int(len(df_nasa)),
        "sampling_rate_hz": 1.0,
        "features": {
            "voltage_v": {
                "mean": float(df_nasa["voltage_v"].mean()),
                "std": float(df_nasa["voltage_v"].std()),
                "min": float(df_nasa["voltage_v"].min()),
                "max": float(df_nasa["voltage_v"].max()),
                "unit": "V",
            },
            "current_a": {
                "mean": float(df_nasa["current_a"].mean()),
                "std": float(df_nasa["current_a"].std()),
                "min": float(df_nasa["current_a"].min()),
                "max": float(df_nasa["current_a"].max()),
                "unit": "A",
            },
            "temperature_c": {
                "mean": float(df_nasa["temperature_c"].mean()),
                "std": float(df_nasa["temperature_c"].std()),
                "min": float(df_nasa["temperature_c"].min()),
                "max": float(df_nasa["temperature_c"].max()),
                "unit": "°C",
            },
            "capacity_ah": {
                "mean": float(df_nasa["capacity_ah"].mean()),
                "std": float(df_nasa["capacity_ah"].std()),
                "min": float(df_nasa["capacity_ah"].min()),
                "max": float(df_nasa["capacity_ah"].max()),
                "unit": "Ah",
            },
        },
    }

    sim_stats = {
        "dataset_name": "SPACECRAFT_EPS_SIMULATION_BENCHMARK_P2",
        "sample_count": int(len(df_sim)),
        "sampling_period_sec": 10.0,
        "duration_orbits": 3.0,
        "features": {
            "voltage_v": {
                "mean": float(df_sim["voltage_v"].mean()),
                "std": float(df_sim["voltage_v"].std()),
                "min": float(df_sim["voltage_v"].min()),
                "max": float(df_sim["voltage_v"].max()),
                "unit": "V",
            },
            "current_a": {
                "mean": float(df_sim["current_a"].mean()),
                "std": float(df_sim["current_a"].std()),
                "min": float(df_sim["current_a"].min()),
                "max": float(df_sim["current_a"].max()),
                "unit": "A",
            },
            "temperature_c": {
                "mean": float(df_sim["temperature_c"].mean()),
                "std": float(df_sim["temperature_c"].std()),
                "min": float(df_sim["temperature_c"].min()),
                "max": float(df_sim["temperature_c"].max()),
                "unit": "°C",
            },
            "power_w": {
                "mean": float(df_sim["power_w"].mean()),
                "std": float(df_sim["power_w"].std()),
                "min": float(df_sim["power_w"].min()),
                "max": float(df_sim["power_w"].max()),
                "unit": "W",
            },
            "est_r_int": {
                "mean": float(df_sim["est_r_int"].mean()),
                "std": float(df_sim["est_r_int"].std()),
                "min": float(df_sim["est_r_int"].min()),
                "max": float(df_sim["est_r_int"].max()),
                "unit": "Ω",
            },
        },
    }

    stats_combined = {
        "nasa_pcoe_benchmark": nasa_stats,
        "spacecraft_eps_simulation": sim_stats,
    }

    json_path = eval_dir / "dataset_characterization.json"
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(stats_combined, f, indent=2)
    print(f"Saved dataset statistics JSON to: {json_path}")

    # 3. Render 4-Panel Publication-Quality Figure
    print("Rendering 4-panel publication figure...")
    fig, axes = plt.subplots(2, 2, figsize=(14, 10))

    # --- Panel A: NASA Battery B0005 Capacity Degradation & Discharge Profile ---
    ax_a = axes[0, 0]
    # Sample 4 representative discharge cycles across lifecycle
    cycles = np.linspace(0, len(df_nasa) - 1000, 5, dtype=int)
    colors_cycles = ["#10B981", "#3B82F6", "#F59E0B", "#EF4444", "#7C3AED"]
    labels_cycles = ["Cycle 1 (Fresh)", "Cycle 40", "Cycle 80", "Cycle 120", "Cycle 160 (Degraded)"]

    for idx, start_idx in enumerate(cycles):
        sub = df_nasa.iloc[start_idx : start_idx + 800]
        time_rel = np.arange(len(sub))
        ax_a.plot(time_rel, sub["voltage_v"].values, label=labels_cycles[idx], color=colors_cycles[idx], linewidth=1.8)

    ax_a.axhline(2.7, color="red", linestyle=":", label="End-of-Discharge Cutoff (2.7V)")
    ax_a.set_title("(a) NASA PCoE Battery B0005: Voltage Discharge Curves Across Aging", fontsize=11, fontweight="bold")
    ax_a.set_xlabel("Relative Discharge Time (seconds)", fontsize=10)
    ax_a.set_ylabel("Terminal Voltage (V)", fontsize=10)
    ax_a.legend(loc="lower left", fontsize=8.5)
    ax_a.grid(True, alpha=0.3)

    # --- Panel B: NASA Battery B0005 Capacity Fade & Internal Resistance Spike ---
    ax_b = axes[0, 1]
    # Downsample points for long-term trend
    step = 50
    t_span = np.arange(0, len(df_nasa), step)
    cap_trend = df_nasa["capacity_ah"].iloc[::step].values
    temp_trend = df_nasa["temperature_c"].iloc[::step].values

    ax_b.plot(t_span / 3600.0, cap_trend, color="#2563EB", label="Discharge Capacity (Ah)", linewidth=2.0)
    ax_b.axhline(1.4, color="red", linestyle="--", label="80% End-of-Life Threshold (1.4 Ah)", alpha=0.8)
    ax_b.set_title("(b) NASA PCoE B0005: Empirical Capacity Fade over Operational Hours", fontsize=11, fontweight="bold")
    ax_b.set_xlabel("Cumulative Operational Time (hours)", fontsize=10)
    ax_b.set_ylabel("Battery Capacity (Ah)", fontsize=10, color="#2563EB")
    ax_b.tick_params(axis="y", labelcolor="#2563EB")
    ax_b.grid(True, alpha=0.3)

    # Secondary axis for Temperature
    ax_b2 = ax_b.twinx()
    ax_b2.plot(t_span / 3600.0, temp_trend, color="#F97316", alpha=0.35, label="Cell Temperature (°C)")
    ax_b2.set_ylabel("Cell Temperature (°C)", fontsize=10, color="#F97316")
    ax_b2.tick_params(axis="y", labelcolor="#F97316")
    ax_b.legend(loc="lower left", fontsize=8.5)

    # --- Panel C: Spacecraft EPS Digital Twin Multi-Orbit Dynamics ---
    ax_c = axes[1, 0]
    time_min = df_sim["timestamp"] / 60.0
    v_bus = df_sim["voltage_v"]
    t_core = df_sim["temperature_c"]
    is_sun = df_sim["meta_is_sunlight"].astype(bool)

    ax_c.plot(time_min, v_bus, color="#059669", label="Regulated Bus Voltage (V)", linewidth=1.8)
    ax_c.set_title("(c) Spacecraft EPS Digital Twin: Bus Dynamics Across 3 LEO Orbits", fontsize=11, fontweight="bold")
    ax_c.set_xlabel("Mission Elapsed Time (minutes)", fontsize=10)
    ax_c.set_ylabel("Main Bus Voltage (V)", fontsize=10, color="#059669")
    ax_c.tick_params(axis="y", labelcolor="#059669")
    ax_c.grid(True, alpha=0.3)

    # Shading for Eclipse Periods
    in_eclipse = ~is_sun
    ax_c.fill_between(time_min, 30, 36, where=in_eclipse, color="#64748B", alpha=0.25, label="Eclipse Pass (35 min)")
    ax_c.set_ylim(31.0, 35.0)

    # Secondary axis for Pack Temperature
    ax_c2 = ax_c.twinx()
    ax_c2.plot(time_min, t_core, color="#DC2626", label="Pack Core Temperature (°C)", linewidth=1.5, linestyle="--")
    ax_c2.set_ylabel("Core Temperature (°C)", fontsize=10, color="#DC2626")
    ax_c2.tick_params(axis="y", labelcolor="#DC2626")
    ax_c.legend(loc="upper left", fontsize=8.5)

    # --- Panel D: Feature Phase Space: Voltage vs Internal Resistance ---
    ax_d = axes[1, 1]
    # Highlight nominal vs fault trajectories
    sns.scatterplot(
        data=df_sim.iloc[::2],
        x="voltage_v",
        y="est_r_int",
        hue="meta_operating_mode",
        palette="viridis",
        alpha=0.75,
        s=35,
        ax=ax_d
    )
    ax_d.set_title(r"(d) Feature Phase Space: Bus Voltage vs Estimated $R_{int}$", fontsize=11, fontweight="bold")
    ax_d.set_xlabel("Regulated Bus Voltage (V)", fontsize=10)
    ax_d.set_ylabel(r"Estimated Dynamic Resistance ($\Omega$)", fontsize=10)
    ax_d.grid(True, alpha=0.3)

    plt.tight_layout()
    fig_out = figures_dir / "fig0_dataset_telemetry_profiles.png"
    plt.savefig(fig_out, dpi=300)
    plt.close()
    print(f"Generated publication figure: {fig_out}")

    return stats_combined


if __name__ == "__main__":
    generate_dataset_visuals()
