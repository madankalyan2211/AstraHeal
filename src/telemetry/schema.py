"""Standardized telemetry schemas and data validation models for AstraHeal."""

from __future__ import annotations

from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field, field_validator
import pandas as pd
import numpy as np


class OperatingState(str, Enum):
    """Spacecraft system operating states."""
    NOMINAL = "NOMINAL"
    DEGRADED = "DEGRADED"
    ANOMALOUS = "ANOMALOUS"
    SAFE_MODE = "SAFE_MODE"
    UNKNOWN = "UNKNOWN"


class TelemetryFrame(BaseModel):
    """Standardized single-timestep telemetry measurement frame."""

    timestamp: float = Field(..., description="Epoch timestamp or elapsed mission time in seconds")
    system_id: str = Field(default="ASTRA-SC-01", description="Identifier of the spacecraft or testbed")
    subsystem: str = Field(default="EPS", description="Subsystem tag e.g. EPS, ADCS, TT&C, Thermal")

    # Core electrical & thermal parameters
    voltage_v: float = Field(..., description="Measured bus or cell voltage in Volts")
    current_a: float = Field(..., description="Measured load or charge current in Amperes (positive=discharge/draw, negative=charge)")
    temperature_c: float = Field(..., description="Component or battery core temperature in Celsius")

    # State & health indicators
    capacity_ah: Optional[float] = Field(default=None, description="Present battery capacity in Ampere-hours")
    state_of_charge: Optional[float] = Field(default=None, ge=0.0, le=1.0, description="State of Charge normalized [0.0, 1.0]")
    health_indicators: Dict[str, float] = Field(
        default_factory=dict,
        description="Dictionary of derived health indicators (e.g. internal_resistance_ohm, dQ_dV, soh)"
    )

    # Operational state
    operating_state: OperatingState = Field(default=OperatingState.NOMINAL, description="System health state")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Contextual tags, orbit phase, cycle ID")

    @field_validator("voltage_v")
    @classmethod
    def validate_voltage_physically_plausible(cls, v: float) -> float:
        if v < -10.0 or v > 500.0:
            raise ValueError(f"Voltage {v}V is outside physically plausible limits (-10V to 500V)")
        return v

    @field_validator("temperature_c")
    @classmethod
    def validate_temperature_physically_plausible(cls, t: float) -> float:
        if t < -273.15 or t > 300.0:
            raise ValueError(f"Temperature {t}C is outside physically plausible limits (-273.15C to 300C)")
        return t

    def to_dict(self) -> Dict[str, Any]:
        """Convert frame to serializable dict."""
        return self.model_dump()


class TelemetryBatch:
    """A batch container for ordered time-series telemetry frames with DataFrame interoperability."""

    def __init__(self, frames: Optional[List[TelemetryFrame]] = None):
        self.frames: List[TelemetryFrame] = frames if frames is not None else []

    def append(self, frame: TelemetryFrame) -> None:
        self.frames.append(frame)

    def __len__(self) -> int:
        return len(self.frames)

    def __getitem__(self, idx: int) -> TelemetryFrame:
        return self.frames[idx]

    def to_dataframe(self) -> pd.DataFrame:
        """Convert batch of telemetry frames into a pandas DataFrame."""
        if not self.frames:
            return pd.DataFrame(columns=[
                "timestamp", "system_id", "subsystem", "voltage_v", "current_a",
                "temperature_c", "capacity_ah", "state_of_charge", "operating_state"
            ])

        records = []
        for f in self.frames:
            rec = {
                "timestamp": f.timestamp,
                "system_id": f.system_id,
                "subsystem": f.subsystem,
                "voltage_v": f.voltage_v,
                "current_a": f.current_a,
                "temperature_c": f.temperature_c,
                "capacity_ah": f.capacity_ah if f.capacity_ah is not None else np.nan,
                "state_of_charge": f.state_of_charge if f.state_of_charge is not None else np.nan,
                "operating_state": f.operating_state.value if isinstance(f.operating_state, OperatingState) else str(f.operating_state),
            }
            # Flatten health indicators
            for k, v in f.health_indicators.items():
                rec[f"hi_{k}"] = v
            # Flatten flat metadata if primitive
            for mk, mv in f.metadata.items():
                if isinstance(mv, (str, int, float, bool)):
                    rec[f"meta_{mk}"] = mv
            records.append(rec)

        df = pd.DataFrame(records)
        df.sort_values(by="timestamp", inplace=True)
        df.reset_index(drop=True, inplace=True)
        return df

    @classmethod
    def from_dataframe(
        cls,
        df: pd.DataFrame,
        system_id: str = "ASTRA-SC-01",
        subsystem: str = "EPS"
    ) -> TelemetryBatch:
        """Create a TelemetryBatch from a pandas DataFrame."""
        batch = cls()
        for _, row in df.iterrows():
            hi = {}
            meta = {}
            for col in df.columns:
                if col.startswith("hi_"):
                    hi[col[3:]] = float(row[col]) if pd.notna(row[col]) else 0.0
                elif col.startswith("meta_"):
                    meta[col[5:]] = row[col]

            op_state_str = str(row.get("operating_state", "NOMINAL"))
            try:
                op_state = OperatingState(op_state_str)
            except ValueError:
                op_state = OperatingState.UNKNOWN

            frame = TelemetryFrame(
                timestamp=float(row["timestamp"]),
                system_id=str(row.get("system_id", system_id)),
                subsystem=str(row.get("subsystem", subsystem)),
                voltage_v=float(row["voltage_v"]),
                current_a=float(row["current_a"]),
                temperature_c=float(row["temperature_c"]),
                capacity_ah=float(row["capacity_ah"]) if "capacity_ah" in row and pd.notna(row["capacity_ah"]) else None,
                state_of_charge=float(row["state_of_charge"]) if "state_of_charge" in row and pd.notna(row["state_of_charge"]) else None,
                health_indicators=hi,
                operating_state=op_state,
                metadata=meta
            )
            batch.append(frame)
        return batch
