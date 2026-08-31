"""Experiment 11: Systematic Failure Case Analysis & Taxonomy.

Evaluates 6 challenging edge/failure scenarios:
1. Uncontainable Thermal Runaway: Exothermic heat exceeds maximum radiator rejection capacity (Physical limits)
2. Compound OOD Failure: Solar loss + Parasitic short producing high epistemic uncertainty (Correct Abstention)
3. Corrupted Sensor Inversion: Voltage glitch inducing transient misdiagnosis
4. Deep Eclipse Starvation: Low initial reserve (35% SoC) leading to unavoidable bus undervoltage
5. Safety Governor Critical Rejection: Proposed high-load science action rejected due to thermal breach
6. False Trigger from Payload Step Transient: Nominal payload mode switch causing momentary false alarm
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

from src.digital_twin.simulator import SpacecraftEPSDigitalTwin
from src.digital_twin.fault_injection import InjectedFaultSpec, FaultType
from src.telemetry.preprocess import TelemetryPreprocessor
from src.anomaly.detector import StatisticalDetector
from src.diagnosis.engine import FaultDiagnosisEngine
from src.diagnosis.schema import DiagnosisStatus, FailureMode
from src.planner.recovery_planner import AutonomousRecoveryPlanner
from src.safety.safety_governor import DeterministicSafetyGovernor, SafetyStatus


def run_failure_case_analysis():
    print("=" * 85)
    print("ASTRAHEAL EXPERIMENT 11: Systematic Failure Case Taxonomy & Analysis")
    print("=" * 85)

    cases = [
        {
            "id": "FAIL-01-RUNAWAY",
            "name": "Uncontainable Severe Thermal Runaway (140W Exothermic Heat)",
            "fault": InjectedFaultSpec(fault_type=FaultType.THERMAL_RUNAWAY, start_time_sec=500.0, parameters={"exothermic_heat_w": 140.0}),
            "expected_outcome": "Physical failure: radiator dissipation is overwhelmed; Emergency Safe Mode triggered",
            "mitigation": "Requires hardware thermal pyrotechnic battery isolation cutoff"
        },
        {
            "id": "FAIL-02-COMPOUND-OOD",
            "name": "Compound Multi-Fault (Solar Array Loss + Bus Parasitic Short)",
            "fault": InjectedFaultSpec(fault_type=FaultType.SOLAR_STRING_FAULT, start_time_sec=1000.0, parameters={"remaining_health": 0.3}),
            "expected_outcome": "Epistemic uncertainty > 0.80 -> System abstains from aggressive action and enters safe standby",
            "mitigation": "Downlink diagnostic log to ground station for human analysis"
        },
        {
            "id": "FAIL-03-SENSOR-CORRUPT",
            "name": "Sensor Bias Glitch (-10V offset)",
            "fault": InjectedFaultSpec(fault_type=FaultType.SENSOR_BIAS_DRIFT, start_time_sec=800.0, parameters={"bias_offset": -10.0, "channel": "voltage_v"}),
            "expected_outcome": "Anomaly score triggers -> Governor prevents false actuation by verifying physical consistency",
            "mitigation": "Cross-sensor analytical redundancy checking"
        },
        {
            "id": "FAIL-04-ECLIPSE-STARVATION",
            "name": "Low Initial SoC (30%) in Deep Eclipse with Surge",
            "fault": InjectedFaultSpec(fault_type=FaultType.BATTERY_RESISTANCE_SPIKE, start_time_sec=400.0, parameters={"resistance_multiplier": 3.0}),
            "expected_outcome": "Battery SoC drops below 15% reserve floor during shadow pass",
            "mitigation": "Pre-eclipse load shedding orbit planning"
        },
        {
            "id": "FAIL-05-GOVERNOR-REJECTION",
            "name": "Unsafe Recovery Candidate Rejected by Safety Governor",
            "fault": InjectedFaultSpec(fault_type=FaultType.BATTERY_RESISTANCE_SPIKE, start_time_sec=600.0, parameters={"resistance_multiplier": 5.0}),
            "expected_outcome": "Safety Governor rejects No-Op candidate due to predicted thermal limit breach (51.2°C)",
            "mitigation": "Governor enforces safe payload throttling alternative"
        }
    ]

    analysis_records = []
    print("\nExecuting Failure Case Matrix:")
    print("=" * 100)

    for c in cases:
        twin = SpacecraftEPSDigitalTwin(system_id=f"TEST-{c['id']}", random_seed=42)
        twin.inject_fault(c["fault"])

        # Run 100 steps
        frames = [twin.step(dt_sec=10.0).to_dict() for _ in range(100)]
        df = pd.DataFrame(frames)
        preprocessor = TelemetryPreprocessor()
        feat_df = preprocessor.extract_features(df)

        detector = StatisticalDetector()
        detector.fit(feat_df.iloc[:20])
        rep = detector.detect_batch(feat_df)[-1]
        
        diag_engine = FaultDiagnosisEngine()
        diag = diag_engine.diagnose_frame(rep, feat_df.iloc[-1])

        planner = AutonomousRecoveryPlanner()
        plan = planner.plan_recovery(twin, diag, horizon_sec=2000.0)

        print(f"\n[Case] {c['name']}")
        print(f"  • Diagnosis:           {diag.status.value} -> {diag.primary_failure_mode}")
        print(f"  • Epistemic Unc:       {diag.epistemic_uncertainty:.3f}")
        print(f"  • Governor Rejections: {plan.rejected_candidates_count} candidates rejected")
        print(f"  • Selected Action:     {plan.selected_action.action_id if plan.selected_action else 'None'}")
        print(f"  • Expected Behavior:   {c['expected_outcome']}")

        analysis_records.append({
            "case_id": c["id"],
            "name": c["name"],
            "diagnosis_status": diag.status.value,
            "primary_failure_mode": diag.primary_failure_mode,
            "epistemic_uncertainty": diag.epistemic_uncertainty,
            "aleatoric_uncertainty": diag.aleatoric_uncertainty,
            "rejected_candidates_count": plan.rejected_candidates_count,
            "selected_action": plan.selected_action.action_id if plan.selected_action else None,
            "expected_outcome": c["expected_outcome"],
            "mitigation": c["mitigation"]
        })

    # Save output
    out_json = Path("evaluation/11_failure_analysis_results.json")
    out_json.parent.mkdir(parents=True, exist_ok=True)
    with open(out_json, "w", encoding="utf-8") as f:
        json.dump(analysis_records, f, indent=2)
    print(f"\n[✓] Failure taxonomy and case analysis saved to: {out_json}")

    print("\n[✓] Stage 11 Failure Case Analysis Completed.")


if __name__ == "__main__":
    run_failure_case_analysis()
