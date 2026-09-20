"""Sanitized Demonstration Data Exporter for AstraHeal Web Visualization.

Generates interactive demonstration data in results/paper4/web_demo/
Captures:
- Real modeled physical state: battery temperature, bus voltage, current, SoC
- Fault state and event triggers
- Evidential diagnosis and epistemic uncertainty
- Candidate actions, governor evaluation, and executed recovery
"""

import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from evaluation.paper4.scenario_generator import Paper4ScenarioGenerator
from experiments.paper4.common import Paper4ExecutionEngine


def export_demo():
    print("[+] Generating sanitized web demonstration data...")
    # Generate canonical 3-orbit multi-cycle scenario
    suite = Paper4ScenarioGenerator.generate_e1_sequential_suite(count=1, base_seed=41000)
    engine = Paper4ExecutionEngine(step_sec=10.0, cooldown_sec=600.0)
    res = engine.run_scenario("ASTRAHEAL_FULL", suite[0])

    out_dir = REPO_ROOT / "results" / "paper4" / "web_demo"
    out_dir.mkdir(parents=True, exist_ok=True)

    demo_data = {
        "mission_id": "ASTRAHEAL-P4-DEMO-001",
        "description": "Multi-Cycle Autonomous Spacecraft Health Management Interactive Telemetry Trace",
        "orbit_duration_seconds": suite[0].orbit_duration_sec,
        "sample_time_seconds": 10.0,
        "survived": res.survived,
        "total_recovery_cycles": res.total_recovery_cycles,
        "executed_unsafe_actions": res.executed_unsafe_actions,
        "governor_rejections_count": res.governor_rejections_count,
        "recovery_cycles": [c.model_dump() for c in res.recovery_cycles],
        "metadata": {
            "disclaimer": "INTERACTIVE DEMONSTRATION DATA ONLY. NOT A PUBLISHED RESEARCH DATASET.",
            "modeled_subsystems": ["Li-ion Battery ECM", "Thermal Radiator", "Solar Array", "Power Distribution Unit"],
            "attitude_orbit_note": "AstraHeal models coupled electrical and thermal state dynamics; orbital trajectory follows a 550km Sun-Synchronous Keplerian orbit."
        }
    }

    out_file = out_dir / "interactive_trajectory.json"
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(demo_data, f, indent=2)
    print(f"[✓] Successfully exported web demo data to: {out_file}")


if __name__ == "__main__":
    export_demo()
