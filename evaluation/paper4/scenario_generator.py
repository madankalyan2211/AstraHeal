"""Scenario Generator for AstraHeal Paper 4: Robust Multi-Cycle Fault Recovery.

Generates reproducible, parameterized evaluation scenarios with deterministic seeds:
- P4-E1: Sequential Fault Recovery (multi-event fault cascades across 3 LEO orbits)
- P4-E2: Repeated Recovery Cycles (varying cycle counts k in {1, 2, 3, 5, 8, 10})
- P4-E3: Perturbed Physics (sweeps across C_th, h_rad, R_0, eta_solar, P_load at +/-5%, +/-10%, +/-15%, +/-20%)
- P4-E4: Telemetry Noise Robustness (Gaussian noise sigma in [0.005, 0.08] & sensor bias drift)
- P4-E5: Combined Stress Conditions (Sequential + Perturbed Physics + Telemetry Noise)
- P4-E6: Compound Multi-Fault Interactions (concurrent dual/triple physical faults)
- P4-E7: Long-Horizon Operation (5 full LEO orbits = 28,700s continuous mission)
- P4-E8: End-to-End System Ablation Matrix (6 comparative architectures x 50 scenarios)
"""

from __future__ import annotations

import copy
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
import numpy as np
from pydantic import BaseModel, Field

from src.digital_twin.fault_injection import InjectedFaultSpec, FaultType


class Paper4ScenarioSpec(BaseModel):
    """Specification of an isolated, reproducible Paper 4 scenario."""
    scenario_id: str
    experiment_id: str
    name: str
    category: str
    orbit_duration_sec: float = 17220.0  # Default: 3 full LEO orbits (3 x 5740s)
    initial_soc: float = 0.95
    random_seed: int = 42
    
    # Fault specifications
    faults: List[InjectedFaultSpec] = Field(default_factory=list)
    
    # Physics parameter perturbations (multipliers relative to nominal 1.0)
    physics_perturbations: Dict[str, float] = Field(default_factory=lambda: {
        "c_th_mult": 1.0,
        "h_rad_mult": 1.0,
        "r0_mult": 1.0,
        "solar_efficiency_mult": 1.0,
        "parasitic_load_bias_w": 0.0
    })
    
    # Sensor noise specifications
    telemetry_noise_sigma: float = 0.005  # Base sensor sigma
    channel_noise_biases: Dict[str, float] = Field(default_factory=dict)
    
    # Metadata and provenance
    description: str = ""
    metadata: Dict[str, Any] = Field(default_factory=dict)


class Paper4ScenarioGenerator:
    """Deterministic scenario generator for all Paper 4 experiments."""

    @staticmethod
    def generate_e1_sequential_suite(count: int = 100, base_seed: int = 41000) -> List[Paper4ScenarioSpec]:
        """P4-E1: Sequential fault recovery scenarios across 3 orbits (17,220s)."""
        suite: List[Paper4ScenarioSpec] = []
        rng = np.random.RandomState(base_seed)

        fault_archetypes = [
            # Event 1: Battery Surge -> Event 2: Solar Degradation -> Event 3: Parasitic Surge
            [
                (FaultType.BATTERY_RESISTANCE_SPIKE, 1200.0, {"resistance_multiplier": 3.2}),
                (FaultType.SOLAR_STRING_FAULT, 7200.0, {"remaining_health": 0.50}),
                (FaultType.PARASITIC_LOAD_SURGE, 13000.0, {"extra_load_w": 120.0})
            ],
            # Event 1: Thermal Overheat -> Event 2: Battery Resistance Spike
            [
                (FaultType.THERMAL_RUNAWAY, 1500.0, {"exothermic_heat_w": 55.0}),
                (FaultType.BATTERY_RESISTANCE_SPIKE, 8000.0, {"resistance_multiplier": 3.0})
            ],
            # Event 1: Solar Degradation -> Event 2: Parasitic Load Surge
            [
                (FaultType.SOLAR_STRING_FAULT, 1800.0, {"remaining_health": 0.40}),
                (FaultType.PARASITIC_LOAD_SURGE, 9500.0, {"extra_load_w": 140.0})
            ],
            # Event 1: Sensor Bias -> Event 2: Battery Resistance Surge -> Event 3: Thermal Runaway
            [
                (FaultType.SENSOR_BIAS_DRIFT, 1000.0, {"bias_offset": -3.5, "channel": "voltage_v"}),
                (FaultType.BATTERY_RESISTANCE_SPIKE, 6800.0, {"resistance_multiplier": 3.4}),
                (FaultType.THERMAL_RUNAWAY, 12500.0, {"exothermic_heat_w": 65.0})
            ]
        ]

        for i in range(count):
            seed = base_seed + i
            arch_idx = i % len(fault_archetypes)
            arch = fault_archetypes[arch_idx]
            
            # Apply slight jitter to timings (+/- 200s) and severities (+/- 10%)
            scenario_faults: List[InjectedFaultSpec] = []
            for f_type, base_t, base_params in arch:
                jitter_t = float(base_t + rng.uniform(-180.0, 180.0))
                params = copy.deepcopy(base_params)
                if "resistance_multiplier" in params:
                    params["resistance_multiplier"] = float(params["resistance_multiplier"] * rng.uniform(0.92, 1.10))
                if "remaining_health" in params:
                    params["remaining_health"] = float(max(0.2, min(0.8, params["remaining_health"] * rng.uniform(0.95, 1.05))))
                if "extra_load_w" in params:
                    params["extra_load_w"] = float(params["extra_load_w"] * rng.uniform(0.90, 1.12))
                if "exothermic_heat_w" in params:
                    params["exothermic_heat_w"] = float(params["exothermic_heat_w"] * rng.uniform(0.90, 1.10))
                
                scenario_faults.append(InjectedFaultSpec(
                    fault_type=f_type,
                    start_time_sec=jitter_t,
                    parameters=params
                ))

            spec = Paper4ScenarioSpec(
                scenario_id=f"P4-E1-SEQ-{i+1:03d}",
                experiment_id="P4-E1",
                name=f"Sequential Cascade Scenario #{i+1:03d}",
                category="SEQUENTIAL_RECOVERY",
                orbit_duration_sec=17220.0,
                initial_soc=float(rng.uniform(0.90, 0.98)),
                random_seed=seed,
                faults=scenario_faults,
                description=f"Multi-cycle sequential scenario with {len(scenario_faults)} cascading faults."
            )
            suite.append(spec)
        return suite

    @staticmethod
    def generate_e2_repeated_cycles_suite(base_seed: int = 42000) -> List[Paper4ScenarioSpec]:
        """P4-E2: Stability stress testing over varying cycle counts k in {1, 2, 3, 5, 8, 10}."""
        cycle_targets = [1, 2, 3, 5, 8, 10]
        runs_per_cycle = 20
        suite: List[Paper4ScenarioSpec] = []
        rng = np.random.RandomState(base_seed)

        idx = 0
        for k in cycle_targets:
            # Scale orbit duration if necessary: 3 orbits for k<=3, 5 orbits for k>3
            dur = 17220.0 if k <= 3 else 28700.0
            
            for r in range(runs_per_cycle):
                idx += 1
                seed = base_seed + idx
                faults: List[InjectedFaultSpec] = []
                
                # Space out k events evenly across duration (with 1200s initial buffer and 600s final buffer)
                available_time = dur - 1800.0
                step_interval = available_time / max(1, k)
                
                fault_types_pool = [
                    (FaultType.BATTERY_RESISTANCE_SPIKE, {"resistance_multiplier": 2.8}),
                    (FaultType.PARASITIC_LOAD_SURGE, {"extra_load_w": 110.0}),
                    (FaultType.SOLAR_STRING_FAULT, {"remaining_health": 0.60}),
                    (FaultType.SENSOR_BIAS_DRIFT, {"bias_offset": -2.5, "channel": "voltage_v"}),
                    (FaultType.THERMAL_RUNAWAY, {"exothermic_heat_w": 48.0})
                ]

                for cycle_num in range(k):
                    t_event = float(1200.0 + cycle_num * step_interval + rng.uniform(-60.0, 60.0))
                    ftype, fparams = fault_types_pool[cycle_num % len(fault_types_pool)]
                    faults.append(InjectedFaultSpec(
                        fault_type=ftype,
                        start_time_sec=t_event,
                        duration_sec=float(step_interval * 0.75),  # Clearable / transient window
                        parameters=copy.deepcopy(fparams)
                    ))

                spec = Paper4ScenarioSpec(
                    scenario_id=f"P4-E2-CYCLE{k:02d}-{r+1:02d}",
                    experiment_id="P4-E2",
                    name=f"Repeated Cycle Stability Stress (k={k}, Run #{r+1:02d})",
                    category=f"CYCLES_{k:02d}",
                    orbit_duration_sec=dur,
                    initial_soc=0.95,
                    random_seed=seed,
                    faults=faults,
                    metadata={"target_cycle_count": k, "run_index": r + 1}
                )
                suite.append(spec)
        return suite

    @staticmethod
    def generate_e3_perturbed_physics_suite(base_seed: int = 43000) -> List[Paper4ScenarioSpec]:
        """P4-E3: Physical parameter perturbations at +/-5%, +/-10%, +/-15%, +/-20%."""
        perturbation_deltas = [-0.20, -0.15, -0.10, -0.05, 0.0, 0.05, 0.10, 0.15, 0.20]
        params_to_perturb = [
            "c_th_mult",                # Battery pack thermal capacitance
            "h_rad_mult",               # Radiator radiative coupling
            "r0_mult",                  # Nominal internal resistance
            "solar_efficiency_mult",    # Solar cell photovoltaic conversion efficiency
            "parasitic_load_bias_w"     # Baseline quiescent bus parasitic load
        ]
        runs_per_point = 5
        suite: List[Paper4ScenarioSpec] = []
        idx = 0

        # Standard canonical test fault sequence: Battery resistance surge + solar string degradation
        base_faults = [
            InjectedFaultSpec(fault_type=FaultType.BATTERY_RESISTANCE_SPIKE, start_time_sec=1500.0, parameters={"resistance_multiplier": 3.0}),
            InjectedFaultSpec(fault_type=FaultType.SOLAR_STRING_FAULT, start_time_sec=8000.0, parameters={"remaining_health": 0.50})
        ]

        for p_name in params_to_perturb:
            for delta in perturbation_deltas:
                for r in range(runs_per_point):
                    idx += 1
                    seed = base_seed + idx
                    
                    perturbs = {
                        "c_th_mult": 1.0,
                        "h_rad_mult": 1.0,
                        "r0_mult": 1.0,
                        "solar_efficiency_mult": 1.0,
                        "parasitic_load_bias_w": 0.0
                    }
                    
                    if p_name == "parasitic_load_bias_w":
                        # Parasitic load bias in Watts: -30W to +30W
                        perturbs[p_name] = float(delta * 150.0)
                    else:
                        perturbs[p_name] = float(1.0 + delta)

                    spec = Paper4ScenarioSpec(
                        scenario_id=f"P4-E3-{p_name}-{delta:+.2f}-{r+1:02d}",
                        experiment_id="P4-E3",
                        name=f"Perturbed Physics ({p_name} {delta:+.0%}, Run #{r+1:02d})",
                        category="PERTURBED_PHYSICS",
                        orbit_duration_sec=17220.0,
                        initial_soc=0.95,
                        random_seed=seed,
                        faults=copy.deepcopy(base_faults),
                        physics_perturbations=perturbs,
                        metadata={"perturbed_parameter": p_name, "perturbation_delta": delta}
                    )
                    suite.append(spec)
        return suite

    @staticmethod
    def generate_e4_telemetry_noise_suite(base_seed: int = 44000) -> List[Paper4ScenarioSpec]:
        """P4-E4: Telemetry noise robustness across escalating sigma in [0.005, 0.08]."""
        noise_sigmas = [0.005, 0.010, 0.020, 0.030, 0.040, 0.050, 0.060, 0.070, 0.080]
        runs_per_sigma = 25
        suite: List[Paper4ScenarioSpec] = []
        idx = 0

        base_faults = [
            InjectedFaultSpec(fault_type=FaultType.BATTERY_RESISTANCE_SPIKE, start_time_sec=1400.0, parameters={"resistance_multiplier": 3.2}),
            InjectedFaultSpec(fault_type=FaultType.THERMAL_RUNAWAY, start_time_sec=7600.0, parameters={"exothermic_heat_w": 55.0})
        ]

        for sigma in noise_sigmas:
            for r in range(runs_per_sigma):
                idx += 1
                seed = base_seed + idx
                spec = Paper4ScenarioSpec(
                    scenario_id=f"P4-E4-NOISE-{sigma:.3f}-{r+1:02d}",
                    experiment_id="P4-E4",
                    name=f"Telemetry Noise Study (sigma={sigma:.3f}, Run #{r+1:02d})",
                    category="TELEMETRY_NOISE",
                    orbit_duration_sec=17220.0,
                    initial_soc=0.95,
                    random_seed=seed,
                    faults=copy.deepcopy(base_faults),
                    telemetry_noise_sigma=float(sigma),
                    metadata={"noise_sigma": sigma, "run_index": r + 1}
                )
                suite.append(spec)
        return suite

    @staticmethod
    def generate_e5_combined_stress_suite(count: int = 150, base_seed: int = 45000) -> List[Paper4ScenarioSpec]:
        """P4-E5: Combined Stress Conditions (Sequential + Perturbed Physics + High Noise)."""
        suite: List[Paper4ScenarioSpec] = []
        rng = np.random.RandomState(base_seed)

        for i in range(count):
            seed = base_seed + i
            
            # 3-fault sequence with random severities
            faults = [
                InjectedFaultSpec(
                    fault_type=FaultType.BATTERY_RESISTANCE_SPIKE,
                    start_time_sec=float(1300.0 + rng.uniform(-100, 100)),
                    parameters={"resistance_multiplier": float(rng.uniform(2.8, 3.8))}
                ),
                InjectedFaultSpec(
                    fault_type=FaultType.SOLAR_STRING_FAULT,
                    start_time_sec=float(7200.0 + rng.uniform(-150, 150)),
                    parameters={"remaining_health": float(rng.uniform(0.35, 0.60))}
                ),
                InjectedFaultSpec(
                    fault_type=FaultType.PARASITIC_LOAD_SURGE,
                    start_time_sec=float(12800.0 + rng.uniform(-120, 120)),
                    parameters={"extra_load_w": float(rng.uniform(90.0, 160.0))}
                )
            ]
            
            # Compounded parameter perturbations (+/- 10% to +/- 15%)
            perturbs = {
                "c_th_mult": float(1.0 + rng.uniform(-0.15, 0.15)),
                "h_rad_mult": float(1.0 + rng.uniform(-0.15, 0.15)),
                "r0_mult": float(1.0 + rng.uniform(-0.15, 0.15)),
                "solar_efficiency_mult": float(1.0 + rng.uniform(-0.15, 0.15)),
                "parasitic_load_bias_w": float(rng.uniform(-25.0, 25.0))
            }

            # High sensor noise
            noise_sigma = float(rng.uniform(0.025, 0.055))

            spec = Paper4ScenarioSpec(
                scenario_id=f"P4-E5-COMBINED-{i+1:03d}",
                experiment_id="P4-E5",
                name=f"Combined Stress Scenario #{i+1:03d}",
                category="COMBINED_STRESS",
                orbit_duration_sec=17220.0,
                initial_soc=float(rng.uniform(0.88, 0.96)),
                random_seed=seed,
                faults=faults,
                physics_perturbations=perturbs,
                telemetry_noise_sigma=noise_sigma,
                description="Triple sequential fault with simultaneous parameter perturbations and elevated noise."
            )
            suite.append(spec)
        return suite

    @staticmethod
    def generate_e6_compound_faults_suite(count: int = 150, base_seed: int = 46000) -> List[Paper4ScenarioSpec]:
        """P4-E6: Concurrent Compound Fault Interactions."""
        suite: List[Paper4ScenarioSpec] = []
        rng = np.random.RandomState(base_seed)

        archetypes = [
            # Dual: Thermal Runaway + Resistance Spike (overlapping)
            [
                (FaultType.THERMAL_RUNAWAY, 2000.0, {"exothermic_heat_w": 55.0}),
                (FaultType.BATTERY_RESISTANCE_SPIKE, 2050.0, {"resistance_multiplier": 3.0})
            ],
            # Dual: Solar Loss + Parasitic Load Surge (severe power deficit)
            [
                (FaultType.SOLAR_STRING_FAULT, 6500.0, {"remaining_health": 0.40}),
                (FaultType.PARASITIC_LOAD_SURGE, 6600.0, {"extra_load_w": 140.0})
            ],
            # Triple: Resistance Spike + Voltage Sensor Bias + Thermal Runaway
            [
                (FaultType.BATTERY_RESISTANCE_SPIKE, 3000.0, {"resistance_multiplier": 3.2}),
                (FaultType.SENSOR_BIAS_DRIFT, 3000.0, {"bias_offset": -3.0, "channel": "voltage_v"}),
                (FaultType.THERMAL_RUNAWAY, 3100.0, {"exothermic_heat_w": 50.0})
            ]
        ]

        for i in range(count):
            seed = base_seed + i
            arch = archetypes[i % len(archetypes)]
            faults: List[InjectedFaultSpec] = []
            for ftype, t_base, p_base in arch:
                params = copy.deepcopy(p_base)
                faults.append(InjectedFaultSpec(
                    fault_type=ftype,
                    start_time_sec=float(t_base + rng.uniform(-50.0, 50.0)),
                    parameters=params
                ))

            spec = Paper4ScenarioSpec(
                scenario_id=f"P4-E6-COMPOUND-{i+1:03d}",
                experiment_id="P4-E6",
                name=f"Compound Concurrent Fault Scenario #{i+1:03d}",
                category="COMPOUND_FAULTS",
                orbit_duration_sec=17220.0,
                initial_soc=0.95,
                random_seed=seed,
                faults=faults,
                description=f"Simultaneous compound interaction with {len(faults)} overlapping faults."
            )
            suite.append(spec)
        return suite

    @staticmethod
    def generate_e7_long_horizon_suite(count: int = 50, base_seed: int = 47000) -> List[Paper4ScenarioSpec]:
        """P4-E7: Long-Horizon Operation across 5 full LEO orbits (28,700s)."""
        suite: List[Paper4ScenarioSpec] = []
        rng = np.random.RandomState(base_seed)

        for i in range(count):
            seed = base_seed + i
            # Distributed anomalies across 5 orbits
            faults = [
                InjectedFaultSpec(
                    fault_type=FaultType.BATTERY_RESISTANCE_SPIKE,
                    start_time_sec=float(1500.0 + rng.uniform(-100, 100)),
                    duration_sec=3500.0,
                    parameters={"resistance_multiplier": float(rng.uniform(2.5, 3.2))}
                ),
                InjectedFaultSpec(
                    fault_type=FaultType.SOLAR_STRING_FAULT,
                    start_time_sec=float(8000.0 + rng.uniform(-150, 150)),
                    parameters={"remaining_health": float(rng.uniform(0.45, 0.65))}
                ),
                InjectedFaultSpec(
                    fault_type=FaultType.PARASITIC_LOAD_SURGE,
                    start_time_sec=float(15000.0 + rng.uniform(-120, 120)),
                    duration_sec=4000.0,
                    parameters={"extra_load_w": float(rng.uniform(80.0, 130.0))}
                ),
                InjectedFaultSpec(
                    fault_type=FaultType.THERMAL_RUNAWAY,
                    start_time_sec=float(22000.0 + rng.uniform(-150, 150)),
                    parameters={"exothermic_heat_w": float(rng.uniform(45.0, 60.0))}
                )
            ]

            spec = Paper4ScenarioSpec(
                scenario_id=f"P4-E7-LONG-{i+1:03d}",
                experiment_id="P4-E7",
                name=f"Long-Horizon 5-Orbit Mission #{i+1:03d}",
                category="LONG_HORIZON",
                orbit_duration_sec=28700.0,  # 5 full orbits
                initial_soc=0.95,
                random_seed=seed,
                faults=faults,
                description="Continuous 28,700s (5-orbit) mission with 4 distributed sequential anomalies."
            )
            suite.append(spec)
        return suite

    @staticmethod
    def generate_e8_ablation_suite(count: int = 50, base_seed: int = 48000) -> List[Paper4ScenarioSpec]:
        """P4-E8: Standardized 50-scenario benchmark for 6-system comparative ablation."""
        suite: List[Paper4ScenarioSpec] = []
        rng = np.random.RandomState(base_seed)

        for i in range(count):
            seed = base_seed + i
            # Realistic double-anomaly cascade
            faults = [
                InjectedFaultSpec(
                    fault_type=FaultType.BATTERY_RESISTANCE_SPIKE,
                    start_time_sec=float(1200.0 + rng.uniform(-100, 100)),
                    parameters={"resistance_multiplier": float(rng.uniform(3.0, 3.8))}
                ),
                InjectedFaultSpec(
                    fault_type=FaultType.SOLAR_STRING_FAULT,
                    start_time_sec=float(7500.0 + rng.uniform(-150, 150)),
                    parameters={"remaining_health": float(rng.uniform(0.40, 0.55))}
                )
            ]

            spec = Paper4ScenarioSpec(
                scenario_id=f"P4-E8-ABLATION-{i+1:03d}",
                experiment_id="P4-E8",
                name=f"Ablation Benchmark Scenario #{i+1:03d}",
                category="ABLATION",
                orbit_duration_sec=17220.0,
                initial_soc=0.95,
                random_seed=seed,
                faults=faults,
                description="Standardized multi-cycle scenario for comparative architecture ablation."
            )
            suite.append(spec)
        return suite
