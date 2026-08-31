"""Telemetry preprocessing pipeline: cleaning, validation, missing value imputation, and feature engineering."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Union
import numpy as np
import pandas as pd
from scipy.signal import medfilt

from src.telemetry.schema import TelemetryBatch, TelemetryFrame, OperatingState


class TelemetryPreprocessor:
    """Preprocesses raw telemetry data through rigorous validation, cleaning, and feature extraction."""

    def __init__(
        self,
        nominal_voltage_range: Tuple[float, float] = (1.5, 40.0),
        nominal_current_range: Tuple[float, float] = (-50.0, 50.0),
        nominal_temp_range: Tuple[float, float] = (-40.0, 100.0),
        rolling_window_size: int = 15,
        processed_dir: str = "data/processed"
    ):
        self.v_min, self.v_max = nominal_voltage_range
        self.i_min, self.i_max = nominal_current_range
        self.t_min, self.t_max = nominal_temp_range
        self.rolling_window = rolling_window_size
        self.processed_dir = Path(processed_dir)
        self.processed_dir.mkdir(parents=True, exist_ok=True)

    def validate_and_clean(self, df: pd.DataFrame) -> Tuple[pd.DataFrame, Dict[str, int]]:
        """Validate ranges, sort by timestamp, reject unphysical outliers, and impute small gaps."""
        cleaned_df = df.copy()
        stats = {
            "initial_rows": len(cleaned_df),
            "missing_values_imputed": 0,
            "outliers_clipped": 0,
            "duplicate_timestamps_dropped": 0
        }

        # 1. Handle multi-cycle timestamp continuity if cycle metadata is present
        dedup_cols = ["meta_cycle_index", "timestamp"] if "meta_cycle_index" in cleaned_df.columns else ["timestamp"]
        cleaned_df.sort_values(by=dedup_cols, inplace=True)
        init_len = len(cleaned_df)
        cleaned_df.drop_duplicates(subset=dedup_cols, keep="first", inplace=True)
        stats["duplicate_timestamps_dropped"] = init_len - len(cleaned_df)

        # Build global cumulative elapsed mission time if cycle index present and timestamp resets
        if "meta_cycle_index" in cleaned_df.columns and (cleaned_df["timestamp"].diff() < 0).any():
            # Offset timestamps by cumulative max time per cycle
            cycle_offsets = {}
            current_offset = 0.0
            new_timestamps = []
            for _, row in cleaned_df.iterrows():
                cyc = row["meta_cycle_index"]
                if cyc not in cycle_offsets:
                    cycle_offsets[cyc] = current_offset
                new_timestamps.append(row["timestamp"] + cycle_offsets[cyc])
                current_offset = max(current_offset, row["timestamp"] + cycle_offsets[cyc] + 10.0)
            cleaned_df["timestamp"] = new_timestamps

        # 2. Missing value handling (Linear interpolation for short gaps, forward-fill trailing)
        for col in ["voltage_v", "current_a", "temperature_c"]:
            if col in cleaned_df.columns:
                nans = cleaned_df[col].isna().sum()
                if nans > 0:
                    stats["missing_values_imputed"] += int(nans)
                    cleaned_df[col] = cleaned_df[col].interpolate(method="linear", limit=10).bfill().ffill()

        # 3. Physically plausible clamping / outlier tagging
        v_outliers = (cleaned_df["voltage_v"] < self.v_min) | (cleaned_df["voltage_v"] > self.v_max)
        i_outliers = (cleaned_df["current_a"] < self.i_min) | (cleaned_df["current_a"] > self.i_max)
        t_outliers = (cleaned_df["temperature_c"] < self.t_min) | (cleaned_df["temperature_c"] > self.t_max)
        
        total_outliers = int((v_outliers | i_outliers | t_outliers).sum())
        stats["outliers_clipped"] = total_outliers

        cleaned_df["voltage_v"] = cleaned_df["voltage_v"].clip(self.v_min, self.v_max)
        cleaned_df["current_a"] = cleaned_df["current_a"].clip(self.i_min, self.i_max)
        cleaned_df["temperature_c"] = cleaned_df["temperature_c"].clip(self.t_min, self.t_max)

        cleaned_df.reset_index(drop=True, inplace=True)
        return cleaned_df, stats

    def extract_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Extract domain-specific physics and statistical features:
        - Thermal rate of change (dT/dt)
        - Voltage slope (dV/dt) and Power (P = V * I)
        - Internal Resistance proxy (R_int = |dV/dI| or V_drop / I)
        - Rolling standard deviations and moving averages
        - Differential Capacity (dQ / dV)
        """
        feat_df = df.copy()

        # Time delta (seconds)
        dt = feat_df["timestamp"].diff().fillna(1.0).replace(0.0, 1.0)

        # Electrical power (Watts)
        feat_df["power_w"] = feat_df["voltage_v"] * feat_df["current_a"]

        # Gradients
        feat_df["dv_dt"] = feat_df["voltage_v"].diff() / dt
        feat_df["di_dt"] = feat_df["current_a"].diff() / dt
        feat_df["dt_dt"] = feat_df["temperature_c"].diff() / dt

        # Fill initial NaNs in derivatives
        feat_df["dv_dt"] = feat_df["dv_dt"].bfill().fillna(0.0)
        feat_df["di_dt"] = feat_df["di_dt"].bfill().fillna(0.0)
        feat_df["dt_dt"] = feat_df["dt_dt"].bfill().fillna(0.0)

        # Estimated instantaneous impedance proxy
        with np.errstate(divide="ignore", invalid="ignore"):
            delta_i = feat_df["current_a"].diff().abs()
            delta_v = feat_df["voltage_v"].diff().abs()
            r_dyn = np.where(delta_i > 0.05, delta_v / delta_i, np.nan)
            feat_df["est_r_int"] = pd.Series(r_dyn, index=feat_df.index).interpolate().bfill().ffill().fillna(0.05)

        # Rolling statistics (mean, std)
        for col in ["voltage_v", "current_a", "temperature_c", "power_w"]:
            feat_df[f"{col}_rolling_mean"] = feat_df[col].rolling(window=self.rolling_window, min_periods=1).mean()
            feat_df[f"{col}_rolling_std"] = feat_df[col].rolling(window=self.rolling_window, min_periods=1).std().fillna(0.0)

        # Differential capacity proxy dQ/dV (where capacity_ah is present)
        if "capacity_ah" in feat_df.columns and feat_df["capacity_ah"].notna().any():
            dq = feat_df["capacity_ah"].diff()
            dv = feat_df["voltage_v"].diff().replace(0.0, 1e-5)
            dq_dv = dq / dv
            feat_df["dq_dv"] = dq_dv.replace([np.inf, -np.inf], np.nan).interpolate().bfill().fillna(0.0)

        return feat_df

    def process_and_save(
        self,
        input_csv_path: Union[str, Path],
        output_filename: str
    ) -> Tuple[pd.DataFrame, Dict[str, Any]]:
        """Complete preprocessing pipeline from raw CSV to processed feature dataset."""
        in_path = Path(input_csv_path)
        if not in_path.exists():
            raise FileNotFoundError(f"Input file not found: {in_path}")

        raw_df = pd.read_csv(in_path)
        cleaned_df, clean_stats = self.validate_and_clean(raw_df)
        feat_df = self.extract_features(cleaned_df)

        out_path = self.processed_dir / output_filename
        feat_df.to_csv(out_path, index=False)

        summary = {
            "input_file": str(in_path),
            "output_file": str(out_path),
            "total_samples": len(feat_df),
            "num_features": len(feat_df.columns),
            "cleaning_stats": clean_stats,
            "feature_columns": list(feat_df.columns)
        }

        # Save pipeline execution metadata
        meta_path = self.processed_dir / f"{output_filename}.meta.json"
        with open(meta_path, "w", encoding="utf-8") as f:
            json.dump(summary, f, indent=2)

        return feat_df, summary
