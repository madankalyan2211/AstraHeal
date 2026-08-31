"""Telemetry visualization, exploratory data analysis (EDA), and degradation plotting."""

from __future__ import annotations

from pathlib import Path
from typing import List, Optional, Union
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns


class TelemetryVisualizer:
    """Generates informative, scientific telemetry plots and diagnostics."""

    def __init__(self, output_dir: str = "docs/figures"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        # Configure clean scientific aesthetic
        plt.style.use("seaborn-v0_8-whitegrid" if "seaborn-v0_8-whitegrid" in plt.style.available else "default")
        plt.rcParams["font.sans-serif"] = "DejaVu Sans"
        plt.rcParams["font.family"] = "sans-serif"

    def plot_telemetry_trends(
        self,
        df: pd.DataFrame,
        filename: str = "telemetry_trends.png",
        title: str = "Spacecraft EPS Telemetry Time Series"
    ) -> Path:
        """Plot multi-channel time-series of Voltage, Current, Temperature, and Power."""
        fig, axes = plt.subplots(4, 1, figsize=(12, 10), sharex=True)

        t = df["timestamp"]

        # 1. Voltage
        axes[0].plot(t, df["voltage_v"], color="#2b5c8f", lw=1.5, label="Voltage (V)")
        axes[0].set_ylabel("Voltage [V]", fontweight="bold")
        axes[0].legend(loc="upper right")
        axes[0].grid(True, linestyle="--", alpha=0.6)

        # 2. Current
        axes[1].plot(t, df["current_a"], color="#d95f02", lw=1.5, label="Current (A)")
        axes[1].set_ylabel("Current [A]", fontweight="bold")
        axes[1].legend(loc="upper right")
        axes[1].grid(True, linestyle="--", alpha=0.6)

        # 3. Temperature
        axes[2].plot(t, df["temperature_c"], color="#7570b3", lw=1.5, label="Temperature (°C)")
        axes[2].set_ylabel("Temp [°C]", fontweight="bold")
        axes[2].legend(loc="upper right")
        axes[2].grid(True, linestyle="--", alpha=0.6)

        # 4. Power / Derivatives
        if "power_w" in df.columns:
            axes[3].plot(t, df["power_w"], color="#1b9e77", lw=1.5, label="Electrical Power (W)")
            axes[3].set_ylabel("Power [W]", fontweight="bold")
        elif "dt_dt" in df.columns:
            axes[3].plot(t, df["dt_dt"], color="#e7298a", lw=1.5, label="dT/dt (°C/s)")
            axes[3].set_ylabel("dT/dt [°C/s]", fontweight="bold")
        axes[3].set_xlabel("Elapsed Time [s]", fontweight="bold")
        axes[3].legend(loc="upper right")
        axes[3].grid(True, linestyle="--", alpha=0.6)

        fig.suptitle(title, fontsize=14, fontweight="bold", y=0.99)
        plt.tight_layout()
        out_path = self.output_dir / filename
        plt.savefig(out_path, dpi=200, bbox_inches="tight")
        plt.close(fig)
        return out_path

    def plot_correlation_matrix(
        self,
        df: pd.DataFrame,
        filename: str = "telemetry_correlations.png"
    ) -> Path:
        """Plot feature correlation matrix."""
        numeric_cols = [c for c in [
            "voltage_v", "current_a", "temperature_c", "power_w",
            "dv_dt", "di_dt", "dt_dt", "est_r_int", "state_of_charge"
        ] if c in df.columns]

        corr = df[numeric_cols].corr()

        fig, ax = plt.subplots(figsize=(8, 6))
        sns.heatmap(corr, annot=True, fmt=".2f", cmap="vlag", vmin=-1.0, vmax=1.0, ax=ax, cbar_kws={"label": "Pearson Correlation"})
        ax.set_title("Telemetry Multi-Signal Cross-Correlation Matrix", fontweight="bold", pad=12)
        plt.tight_layout()
        out_path = self.output_dir / filename
        plt.savefig(out_path, dpi=200, bbox_inches="tight")
        plt.close(fig)
        return out_path

    def plot_degradation_trajectory(
        self,
        df: pd.DataFrame,
        filename: str = "battery_degradation.png"
    ) -> Path:
        """Plot capacity degradation and internal resistance growth across cycle history."""
        if "meta_cycle_index" not in df.columns:
            # Group by 1000s blocks if cycle index not present
            df["meta_cycle_index"] = (df["timestamp"] // 1000).astype(int)

        cycle_summary = df.groupby("meta_cycle_index").agg({
            "capacity_ah": "first",
            "hi_soh": "first",
            "hi_r_int": "mean" if "hi_r_int" in df.columns else "first"
        }).dropna()

        fig, ax1 = plt.subplots(figsize=(10, 5))
        color = "#1f77b4"
        ax1.set_xlabel("Cycle Number", fontweight="bold")
        ax1.set_ylabel("Capacity (Ah) / SoH", color=color, fontweight="bold")
        if "capacity_ah" in cycle_summary.columns:
            ax1.plot(cycle_summary.index, cycle_summary["capacity_ah"], color=color, lw=2, label="Capacity (Ah)")
        if "hi_soh" in cycle_summary.columns:
            ax1.plot(cycle_summary.index, cycle_summary["hi_soh"] * 2.0, color="#2ca02c", linestyle="--", label="SoH Trajectory")
        ax1.tick_params(axis="y", labelcolor=color)
        ax1.grid(True, linestyle=":", alpha=0.5)

        if "hi_r_int" in cycle_summary.columns and not cycle_summary["hi_r_int"].isna().all():
            ax2 = ax1.twinx()
            color = "#d62728"
            ax2.set_ylabel("Internal Resistance (Ω)", color=color, fontweight="bold")
            ax2.plot(cycle_summary.index, cycle_summary["hi_r_int"], color=color, lw=2, linestyle="-.", label="Internal Resistance (Ω)")
            ax2.tick_params(axis="y", labelcolor=color)

        fig.suptitle("NASA PCoE Battery Run-to-Failure Degradation Trajectory", fontsize=13, fontweight="bold")
        plt.tight_layout()
        out_path = self.output_dir / filename
        plt.savefig(out_path, dpi=200, bbox_inches="tight")
        plt.close(fig)
        return out_path
