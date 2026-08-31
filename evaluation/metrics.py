"""Comprehensive benchmark evaluation metrics for anomaly, diagnosis, safety, and autonomy."""

from __future__ import annotations

from typing import Any, Dict, List, Optional
import numpy as np
import pandas as pd
from pydantic import BaseModel, Field


class ComparativeScenarioMetrics(BaseModel):
    """Execution metrics for a single scenario under a specific autonomy system."""
    system_name: str  # "BASELINE_A_NO_RECOVERY", "BASELINE_B_FIXED_HEURISTIC", "ASTRAHEAL_AUTONOMOUS"
    scenario_id: str
    scenario_name: str
    survived: bool
    hard_constraint_violations_count: int
    max_battery_temp_c: float
    min_bus_voltage_v: float
    min_soc: float
    final_soc: float
    payload_availability_pct: float
    energy_margin_wh: float
    autonomous_actions_executed: int


class BenchmarkSuiteSummary(BaseModel):
    """Aggregate comparative performance summary across an entire benchmark suite."""
    system_name: str
    total_scenarios: int
    survival_rate_pct: float
    total_hard_violations: int
    mean_payload_availability_pct: float
    mean_final_soc: float
    mean_max_temperature_c: float
    detailed_results: List[ComparativeScenarioMetrics] = Field(default_factory=list)


class BenchmarkMetricsCalculator:
    """Computes rigorous statistical comparisons across benchmark runs."""

    @staticmethod
    def aggregate_suite(system_name: str, results: List[ComparativeScenarioMetrics]) -> BenchmarkSuiteSummary:
        """Compute aggregate statistical metrics for a single system across scenarios."""
        n = len(results)
        if n == 0:
            return BenchmarkSuiteSummary(
                system_name=system_name,
                total_scenarios=0,
                survival_rate_pct=0.0,
                total_hard_violations=0,
                mean_payload_availability_pct=0.0,
                mean_final_soc=0.0,
                mean_max_temperature_c=0.0
            )

        surv_count = sum(1 for r in results if r.survived)
        tot_viols = sum(r.hard_constraint_violations_count for r in results)
        mean_payload = float(np.mean([r.payload_availability_pct for r in results]))
        mean_soc = float(np.mean([r.final_soc for r in results]))
        mean_temp = float(np.mean([r.max_battery_temp_c for r in results]))

        return BenchmarkSuiteSummary(
            system_name=system_name,
            total_scenarios=n,
            survival_rate_pct=float(surv_count / n * 100.0),
            total_hard_violations=tot_viols,
            mean_payload_availability_pct=mean_payload,
            mean_final_soc=mean_soc,
            mean_max_temperature_c=mean_temp,
            detailed_results=results
        )
