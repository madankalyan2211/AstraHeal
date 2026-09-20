# AstraHeal Paper 4 — Phase 1: Repository Audit Report

**Date**: 2026-09-13  
**Status**: COMPLETE  
**Auditor**: AstraHeal Research Group & Autonomous Systems Lab  
**Scope**: AstraHeal Core Repository, Simulation Engine, Decision Stack, Telemetry Schemas, and Historical Frozen Baselines

---

## 1. Executive Summary

This repository audit establishes the empirical, physical, and software baseline for **AstraHeal Paper 4: Robust Multi-Cycle Autonomous Fault Recovery Under Perturbed Spacecraft Conditions**. The audit inspects all software components in `src/`, verifies the frozen state of `v1.0.0-research-release`, catalogs all physically modeled state variables, fault injection vectors, and candidate recovery actions, and defines the exact boundary separating frozen code from Paper 4 implementations.

---

## 2. Frozen Release Boundary Verification

The following components represent the frozen research release of AstraHeal (Papers 1–3) and are designated **STRICTLY READ-ONLY**:

| Component / Path | Release Status | Invariant Constraints |
| :--- | :---: | :--- |
| `src/digital_twin/` | FROZEN (v1.0.0) | Core physics equations, Thevenin ECM, and orbital models must not be altered in-place. |
| `src/safety/safety_governor.py` | FROZEN (v1.0.0) | Hard constraints ($T \le 46^\circ\text{C}, V \ge 22\text{V}, I \le 40\text{A}, \text{SoC} \ge 15\%$) must remain unchanged. |
| `src/diagnosis/` | FROZEN (v1.0.0) | Evidential Dirichlet & Bayesian diagnostic logic must maintain original interfaces. |
| `src/planner/` | FROZEN (v1.0.0) | Action definitions and counterfactual branching engine must maintain backward compatibility. |
| `experiments/01_*.py` through `15_*.py` | FROZEN | Historical experiments 01 through 15 must never be re-executed or modified. |
| `experiments/paper2/` & `docs/paper2/` | FROZEN | Paper 2 artifacts, data, and manuscript are locked. |
| `experiments/paper3/` & `docs/paper3/` | FROZEN | Paper 3 artifacts, data, and manuscript are locked. |
| `tests/test_*.py` (Original 51 tests) | FROZEN | Baseline test suite must maintain 100% pass rate at all times. |

**Paper 4 Isolation Structure**:
All Paper 4 implementations, configurations, experiments, evaluation runners, tests, and documentation are strictly confined to:
* `configs/paper4/`
* `experiments/paper4/`
* `evaluation/paper4/`
* `tests/paper4/`
* `results/paper4/`
* `docs/paper4/`
* `paper4/`

---

## 3. Physical State Modeling Audit

The digital twin models a 12U CubeSat Electrical Power System (EPS) operating in a 550 km Sun-Synchronous Low Earth Orbit ($T_{\text{orbit}} = 5,740\,\text{s} \approx 95.7\,\text{min}$). The physical state vector $s_t$ comprises:

| State Variable | Symbol | Dimension / Unit | Physical Subsystem & Dynamics |
| :--- | :---: | :---: | :--- |
| **Bus Regulated Voltage** | $V_{\text{bus}}$ | Volts ($\text{V}$) | 28V nominal regulated bus; PDU balance with battery terminal voltage and line drop. |
| **Battery Terminal Voltage** | $V_{\text{batt}}$ | Volts ($\text{V}$) | $V_{\text{batt}} = V_{\text{ocv}}(\text{SoC}) - I_{\text{batt}} R_0(T, \text{SoC}) - V_{\text{pol}}$. |
| **Battery Pack Current** | $I_{\text{batt}}$ | Amperes ($\text{A}$) | Discharge ($> 0$) or charge ($< 0$); max rated $40.0\,\text{A}$. |
| **Battery Core Temperature** | $T_{\text{core}}$ | Celsius ($^\circ\text{C}$) | Thermal differential kinetics: $C_{\text{th}} \frac{dT}{dt} = I^2 R_0 + \dot{Q}_{\text{exo}} - h_{\text{rad}}(T^4 - T_{\text{space}}^4)$. |
| **State of Charge** | $\text{SoC}$ | Fraction $[0.0, 1.0]$ | Coulomb counting integral: $\text{SoC}(t) = \text{SoC}_0 - \frac{1}{3600 C_{\text{nom}}} \int I_{\text{batt}} dt$. |
| **State of Health** | $\text{SoH}$ | Fraction $[0.0, 1.0]$ | Capacity fade degradation based on cumulative Ah throughput. |
| **Polarization Voltage** | $V_{\text{pol}}$ | Volts ($\text{V}$) | RC pair dynamic transient: $\frac{dV_{\text{pol}}}{dt} = \frac{I_{\text{batt}}}{C_p} - \frac{V_{\text{pol}}}{R_p C_p}$. |
| **PDU Total Power Delivery** | $P_{\text{pdu}}$ | Watts ($\text{W}$) | Sum of payload active/standby, avionics, ADCS, comms, and heaters ($P \le 880\,\text{W}$). |
| **Solar Generation Power** | $P_{\text{solar}}$ | Watts ($\text{W}$) | $P_{\text{solar}} = \Phi_{\text{solar}}(t) \cdot A_{\text{eff}} \cdot \eta_{\text{cell}} \cdot \cos(\theta_{\text{inc}}) \cdot \text{health}$. |
| **Orbital Angle / State** | $\phi_{\text{orbit}}$ | Radians $[0, 2\pi)$ | True anomaly governing sunlight ($59.6\,\text{min}$) vs. eclipse blackout ($36.1\,\text{min}$). |
| **Communication Link State**| $\lambda_{\text{link}}$ | Enum | `CONTACT` (ground station access window) or `BLACKOUT` (autonomous hold). |

---

## 4. Injected Fault Catalog Audit

Inspected from `src/digital_twin/fault_injection.py`:

| Fault Identifier | Physical Mechanism | Affecting Parameters | Reversibility in Twin |
| :--- | :--- | :--- | :---: |
| `BATTERY_RESISTANCE_SPIKE` | Internal cell electrode cracking / SEI layer breakdown | $R_0 \leftarrow R_0 \times \text{multiplier}$ (default $3.0\times$) | Parameterized |
| `SOLAR_STRING_FAULT` | Micro-meteoroid impact or string open-circuit | $\text{health\_factor} \leftarrow \max(0, 1.0 - 0.7 \times \text{sev})$ | Persistent |
| `THERMAL_RUNAWAY` | Exothermic self-sustaining separator breakdown | $\dot{Q}_{\text{exo}} \leftarrow 60.0\,\text{W} \times \text{sev}$ | Continuous |
| `PARASITIC_LOAD_SURGE` | Subsystem short or latch-up in scientific instrument | $P_{\text{parasitic}} \leftarrow 150.0\,\text{W} \times \text{sev}$ | Controllable |
| `SENSOR_BIAS_DRIFT` | ADC drift or calibration loss on telemetry channel | $V_{\text{meas}} \leftarrow V_{\text{meas}} + \Delta V$ (default $-3.5\,\text{V}$) | Sensor only |

---

## 5. Candidate Recovery Action Catalog Audit

Inspected from `src/planner/actions.py`:

| Action Identifier | Action Type | Actuation Impact on Spacecraft | Resource Cost |
| :--- | :--- | :--- | :---: |
| `ACT_NOMINAL` | `CONTINUE_NOMINAL` | Maintain current operational setpoints (baseline monitor). | $0.00$ |
| `ACT_THROTTLE_PAYLOAD_50` | `REDUCE_PAYLOAD_LOAD` | Reduce instrument payload consumption by 50% ($P_{\text{pay}} \times 0.5$). | $0.25$ |
| `ACT_SHUTDOWN_PAYLOAD` | `DISABLE_NON_CRITICAL_SUBSYSTEM`| Fully shed payload power ($P_{\text{pay}} \leftarrow 0\,\text{W}$). | $0.50$ |
| `ACT_REDUCE_HEATERS_50` | `REDUCE_HEATER_POWER` | Curtail active thermal heaters by 50% ($P_{\text{heat}} \times 0.5$). | $0.35$ |
| `ACT_SAFE_MODE` | `ENTER_SAFE_MODE` | Isolate non-essential loads, shed payload & heaters, lock ADCS to sun-point. | $0.85$ |
| `ACT_POWER_REDISTRIBUTE` | `REDISTRIBUTE_POWER` | Power down non-critical bus switches, drop comms to receive-only. | $0.40$ |
| `ACT_DEFER_ACTIVITY` | `DEFER_NON_CRITICAL_ACTIVITY`| Suspend upcoming observation sequence until ground pass. | $0.15$ |

---

## 6. System Capabilities & Limitations for Paper 4

### A. Fully Supported Capabilities (Verified)
1. **Multi-Orbit Continuous Propagation**: The digital twin seamlessly propagates continuous mission timelines over arbitrary durations ($> 28,000\,\text{s}$, $5+$ orbits).
2. **Debounced Multi-Cycle Event Handling**: The event engine (`MultiCycleBenchmarkRunner`) supports successive fault injections, sequential anomaly detection triggers, and post-action telemetry re-evaluation.
3. **Compound Concurrent Fault Injection**: `FaultInjectionEngine` evaluates multiple active fault specs simultaneously without conflict.
4. **Calibrated Physical Parameter Perturbations**: Parameters including $C_{\text{th}}, h_{\text{rad}}, R_0, \eta_{\text{solar}}, P_{\text{parasitic}}$ can be perturbed independently during initialization without altering the frozen code.
5. **Sensor Noise Modeling**: `SpacecraftEPSDigitalTwin` provides `sensor_noise_sigma` natively, and telemetry feeds can accept additive noise distributions.
6. **Deterministic Safety Enforcement**: `DeterministicSafetyGovernor` executes in $< 3\,\mu\text{s}$, rejects invalid proposals unconditionally, and enforces fail-closed containment.

### B. Limitations & Non-Supported Scope
1. **No Hardware-in-the-Loop (HIL)**: The system executes purely in high-fidelity Python numerical simulation; no physical spacecraft hardware or FPGA testbench is connected.
2. **No Orbital Trajectory Thruster Maneuvers**: The orbital model is a Keplerian propagator with J2 perturbation and eclipse projection. The spacecraft attitude/orbit control does not model chemical or electric thruster delta-v trajectories. State recovery is strictly electrical, thermal, and operational.
3. **No Closed-Loop Real-World Flight Data**: While calibrated against NASA Ames battery degradation profiles, multi-cycle recovery traces are generated within the digital twin simulator.

---

## 7. Audit Sign-Off

The AstraHeal repository provides an exceptionally solid, verified, and complete foundation for Paper 4. The isolation rules are strictly defined, and the software is ready for Phase 2 (Literature & Overlap Audit).
