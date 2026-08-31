"""Data structures and enums for spacecraft fault diagnosis and uncertainty quantification."""

from __future__ import annotations

from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class DiagnosisStatus(str, Enum):
    """Diagnostic outcome classification."""
    KNOWN_FAILURE = "KNOWN_FAILURE"
    UNKNOWN_FAILURE = "UNKNOWN_FAILURE"
    INSUFFICIENT_EVIDENCE = "INSUFFICIENT_EVIDENCE"


class FailureMode(str, Enum):
    """Catalog of known spacecraft power-system failure modes."""
    BATTERY_INTERNAL_RESISTANCE_SPIKE = "BATTERY_INTERNAL_RESISTANCE_SPIKE"
    SOLAR_ARRAY_STRING_FAULT = "SOLAR_ARRAY_STRING_FAULT"
    THERMAL_RUNAWAY_INITIATION = "THERMAL_RUNAWAY_INITIATION"
    PARASITIC_BUS_OVERLOAD = "PARASITIC_BUS_OVERLOAD"
    SENSOR_BIAS_DRIFT = "SENSOR_BIAS_DRIFT"
    NOVEL_UNSEEN_ANOMALY = "NOVEL_UNSEEN_ANOMALY"
    NOMINAL_OPERATION = "NOMINAL_OPERATION"


class DiagnosisReport(BaseModel):
    """Standardized fault diagnosis and uncertainty report."""

    timestamp: float = Field(..., description="Timestamp of the evaluated diagnosis")
    status: DiagnosisStatus = Field(..., description="KNOWN_FAILURE, UNKNOWN_FAILURE, or INSUFFICIENT_EVIDENCE")
    primary_failure_mode: str = Field(..., description="Identified failure mode or 'UNKNOWN_ANOMALY' / 'NO_FAULT'")
    affected_subsystem: str = Field(..., description="Affected subsystem e.g. EPS_BATTERY, EPS_SOLAR, EPS_BUS")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence in primary diagnosis [0.0, 1.0]")
    uncertainty: float = Field(..., ge=0.0, le=1.0, description="Total uncertainty [0.0, 1.0]")
    epistemic_uncertainty: float = Field(..., ge=0.0, le=1.0, description="Model/OOD uncertainty (lack of knowledge)")
    aleatoric_uncertainty: float = Field(..., ge=0.0, le=1.0, description="Data noise/entropy uncertainty (ambiguity)")
    hypothesis_distribution: Dict[str, float] = Field(
        default_factory=dict,
        description="Posterior probability or evidential belief across failure modes"
    )
    evidence: List[str] = Field(default_factory=list, description="Physics signatures and telemetry observations supporting the diagnosis")
    method: str = Field(default="BayesianEvidentialEngine", description="Diagnostic methodology used")
    details: Dict[str, Any] = Field(default_factory=dict)
