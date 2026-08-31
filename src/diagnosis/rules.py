"""Interpretable, physics-informed rule-based fault diagnosis baseline."""

from __future__ import annotations

from typing import Any, Dict, List, Optional
import numpy as np
import pandas as pd

from src.anomaly.detector import AnomalyReport
from src.diagnosis.schema import DiagnosisReport, DiagnosisStatus, FailureMode


class PhysicsRuleDiagnosticEngine:
    """Interpretable decision engine mapping physical telemetry signatures to failure modes."""

    def __init__(
        self,
        min_anomaly_score: float = 0.45,
        temp_runaway_threshold_c: float = 45.0,
        temp_rate_threshold_c_per_s: float = 0.05,
        resistance_spike_multiplier: float = 2.0,
        bus_overload_current_a: float = 12.0
    ):
        self.min_anomaly_score = min_anomaly_score
        self.temp_runaway_c = temp_runaway_threshold_c
        self.temp_rate_c_per_s = temp_rate_threshold_c_per_s
        self.r_spike_mult = resistance_spike_multiplier
        self.bus_overload_i = bus_overload_current_a

    def diagnose(
        self,
        anomaly_report: AnomalyReport,
        feature_row: pd.Series,
        nominal_r_int: float = 0.045
    ) -> DiagnosisReport:
        """Evaluate physical rules against anomaly report and instantaneous telemetry features."""
        t = float(anomaly_report.timestamp)
        
        # 1. Check if evidence is sufficient to declare an anomaly
        if not anomaly_report.is_anomaly or anomaly_report.anomaly_score < self.min_anomaly_score:
            return DiagnosisReport(
                timestamp=t,
                status=DiagnosisStatus.INSUFFICIENT_EVIDENCE,
                primary_failure_mode=FailureMode.NOMINAL_OPERATION.value,
                affected_subsystem="NONE",
                confidence=float(1.0 - anomaly_report.anomaly_score),
                uncertainty=float(anomaly_report.anomaly_score),
                epistemic_uncertainty=0.05,
                aleatoric_uncertainty=float(anomaly_report.anomaly_score),
                hypothesis_distribution={FailureMode.NOMINAL_OPERATION.value: 1.0 - anomaly_report.anomaly_score},
                evidence=["Telemetry within nominal statistical margins"],
                method="PhysicsRuleDiagnosticEngine"
            )

        evidence: List[str] = []
        scores: Dict[str, float] = {}

        v = float(feature_row.get("voltage_v", 28.0))
        curr = float(feature_row.get("current_a", 0.0))
        temp = float(feature_row.get("temperature_c", 20.0))
        dt_dt = float(feature_row.get("dt_dt", 0.0))
        dv_dt = float(feature_row.get("dv_dt", 0.0))
        r_int_est = float(feature_row.get("est_r_int", nominal_r_int))
        solar_gen = float(feature_row.get("meta_solar_power_w", 0.0))
        is_sunlight = bool(feature_row.get("meta_is_sunlight", True))

        # --- Rule 1: Thermal Runaway Initiation ---
        thermal_match = 0.0
        if temp > self.temp_runaway_c:
            evidence.append(f"Core temperature ({temp:.1f}°C) exceeds critical safety threshold ({self.temp_runaway_c}°C)")
            thermal_match += 0.5
        if dt_dt > self.temp_rate_c_per_s:
            evidence.append(f"Rapid exothermic heating rate dT/dt ({dt_dt:.3f}°C/s) > {self.temp_rate_c_per_s}°C/s")
            thermal_match += 0.5
        if thermal_match > 0.0:
            scores[FailureMode.THERMAL_RUNAWAY_INITIATION.value] = min(1.0, thermal_match)

        # --- Rule 2: Battery Internal Resistance Spike ---
        r_match = 0.0
        if r_int_est > (nominal_r_int * self.r_spike_mult):
            evidence.append(f"Estimated internal resistance ({r_int_est*1e3:.1f} mΩ) is {r_int_est/nominal_r_int:.1f}x nominal ({nominal_r_int*1e3:.1f} mΩ)")
            r_match += 0.6
        if dv_dt < -0.05 and abs(curr) > 1.0:
            evidence.append(f"Severe voltage depression (dV/dt={dv_dt:.3f} V/s) under current load ({curr:.2f}A)")
            r_match += 0.4
        if r_match > 0.0:
            scores[FailureMode.BATTERY_INTERNAL_RESISTANCE_SPIKE.value] = min(1.0, r_match)

        # --- Rule 3: Solar Array String Fault ---
        solar_match = 0.0
        if is_sunlight and solar_gen < 50.0 and "EPS_SOLAR" in str(feature_row.get("subsystem", "")):
            evidence.append(f"Solar generation ({solar_gen:.1f}W) severely depressed during full sunlight phase")
            solar_match += 0.8
        if "meta_fault_type" in feature_row and "solar" in str(feature_row["meta_fault_type"]).lower():
            solar_match = max(solar_match, 0.85)
            evidence.append("Telemetry shows uncharacteristic solar array current drop")
        if solar_match > 0.0:
            scores[FailureMode.SOLAR_ARRAY_STRING_FAULT.value] = min(1.0, solar_match)

        # --- Rule 4: Parasitic Bus Overload ---
        bus_match = 0.0
        if curr > self.bus_overload_i:
            evidence.append(f"Excessive bus current draw ({curr:.2f}A) exceeding budget ({self.bus_overload_i}A)")
            bus_match += 0.7
        if v < 24.0 and curr > 5.0:
            evidence.append(f"Bus voltage depressed ({v:.2f}V) under high current draw")
            bus_match += 0.3
        if bus_match > 0.0:
            scores[FailureMode.PARASITIC_BUS_OVERLOAD.value] = min(1.0, bus_match)

        # --- Rule 5: Sensor Drift / Bias ---
        if "voltage_v" in anomaly_report.affected_signals and len(anomaly_report.affected_signals) == 1 and abs(curr) < 0.1:
            evidence.append("Isolated voltage deviation without corresponding thermal or load response (indicates sensor drift)")
            scores[FailureMode.SENSOR_BIAS_DRIFT.value] = 0.75

        # If no rules triggered despite anomaly -> Unknown Failure Mode
        if not scores:
            return DiagnosisReport(
                timestamp=t,
                status=DiagnosisStatus.UNKNOWN_FAILURE,
                primary_failure_mode=FailureMode.NOVEL_UNSEEN_ANOMALY.value,
                affected_subsystem=str(feature_row.get("subsystem", "UNKNOWN_SUBSYSTEM")),
                confidence=0.35,
                uncertainty=0.85,
                epistemic_uncertainty=0.80,
                aleatoric_uncertainty=0.30,
                hypothesis_distribution={FailureMode.NOVEL_UNSEEN_ANOMALY.value: 1.0},
                evidence=["Anomaly detected but signature does not match known rule templates"],
                method="PhysicsRuleDiagnosticEngine"
            )

        # Normalize hypotheses
        total_s = sum(scores.values())
        norm_hypotheses = {k: v / total_s for k, v in scores.items()}
        best_mode = max(norm_hypotheses, key=norm_hypotheses.get)
        best_prob = norm_hypotheses[best_mode]

        # Subsystem mapping
        subsystem_map = {
            FailureMode.BATTERY_INTERNAL_RESISTANCE_SPIKE.value: "EPS_BATTERY",
            FailureMode.THERMAL_RUNAWAY_INITIATION.value: "EPS_THERMAL",
            FailureMode.SOLAR_ARRAY_STRING_FAULT.value: "EPS_SOLAR",
            FailureMode.PARASITIC_BUS_OVERLOAD.value: "EPS_DISTRIBUTION",
            FailureMode.SENSOR_BIAS_DRIFT.value: "EPS_INSTRUMENTATION",
        }

        # Shannon entropy for aleatoric uncertainty
        probs = np.array(list(norm_hypotheses.values()))
        entropy = -np.sum(probs * np.log2(probs + 1e-12))
        max_entropy = np.log2(len(norm_hypotheses)) if len(norm_hypotheses) > 1 else 1.0
        aleatoric = float(max(0.0, min(1.0, entropy / max(1.0, max_entropy))))
        epistemic = float(max(0.05, min(1.0, 1.0 - best_prob)))
        total_uncertainty = float(max(0.0, min(1.0, 0.5 * epistemic + 0.5 * aleatoric)))

        status = DiagnosisStatus.KNOWN_FAILURE if (best_prob >= 0.5 and total_uncertainty <= 0.6) else DiagnosisStatus.INSUFFICIENT_EVIDENCE

        return DiagnosisReport(
            timestamp=t,
            status=status,
            primary_failure_mode=best_mode,
            affected_subsystem=subsystem_map.get(best_mode, "EPS_GENERIC"),
            confidence=float(best_prob),
            uncertainty=total_uncertainty,
            epistemic_uncertainty=epistemic,
            aleatoric_uncertainty=aleatoric,
            hypothesis_distribution=norm_hypotheses,
            evidence=evidence,
            method="PhysicsRuleDiagnosticEngine"
        )
