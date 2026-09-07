# AstraHeal Paper 2 — Dataset Integrity and Leakage Prevention Audit

**Document**: Dataset Provenance, Feature Definitions, Split Rigor, and Leakage Prevention Protocol  
**Project**: AstraHeal — Paper 2  
**Date**: 2026  
**Status**: Formal Dataset Audit Completed (Phase 2 Complete)

---

## 1. Dataset Provenance & Integrity

Paper 2 utilizes two validated telemetry data sources:

### Source 1: NASA Prognostics Center of Excellence (PCoE) Battery Archive
- **Dataset Name**: `NASA_PCOE_BENCHMARK_B0005`
- **Origin**: NASA Ames Research Center, Prognostics Data Repository
- **License**: NASA Open Science Data Terms (Public Research Use)
- **Local Raw File**: `data/raw/nasa_pcoe_benchmark_B0005.csv`
- **SHA-256 Hash**: `4f454d4c083f6ce5e33eb2b6cdbeda3403a633c854a50e6bbce4c18eccdbbfbe` (Verified)
- **Modality**: Empirical lithium-ion 18650 cell electro-thermal telemetry during repeated orbital charge/discharge/impedance cycles.

### Source 2: Spacecraft EPS Digital Twin Multi-Orbit Simulation Suite
- **Dataset Name**: `SPACECRAFT_EPS_SIMULATION_BENCHMARK_P2`
- **Origin**: AstraHeal High-Fidelity Orbital EPS Simulator (`src/digital_twin/simulator.py`)
- **Physics Models**:
  - Thevenin 1-RC equivalent circuit battery electro-chemistry with temperature-dependent internal resistance ($R_0(T) = R_{\text{ref}} \exp\left[\frac{E_a}{R}\left(\frac{1}{T} - \frac{1}{T_{\text{ref}}}\right)\right]$).
  - Keplerian Low Earth Orbit illumination geometry ($H = 500\text{ km}$, $T_{\text{orbit}} = 5700\text{ s}$, eclipse fraction = $0.368$).
  - Multi-junction photovoltaic array power output ($P_{\text{pv}} = \eta A S_0 \cos\theta$).
  - Spacecraft energy conservation and lumped-capacitance thermal radiation balance ($C_{\text{th}} \frac{dT}{dt} = \dot{Q}_{\text{in}} - \epsilon \sigma A (T^4 - T_{\text{space}}^4)$).
- **Deterministic Random Seeds**: Trajectory simulations use fixed random seeds `42`, `1337`, `2026`.
- **Local Processed File**: `data/processed/mission_run_3orbits_processed.csv`
- **SHA-256 Hash**: `724bd00cd858452f677716f2ecb93ce5791a1d180d678557c0f34ba72bc22d77` (Verified)

---

## 2. Feature & Label Definitions

### Feature Representation Vector ($\mathbf{x} \in \mathbb{R}^7$)
All diagnostic models evaluate an identical standardized 7-dimensional telemetry feature vector:

| Index | Feature Name | Unit | Physical Interpretation |
|---|---|---|---|
| 0 | `voltage_v` | Volts (V) | Regulated spacecraft main power bus voltage |
| 1 | `current_a` | Amperes (A) | Magnitude of battery net charge/discharge current |
| 2 | `temperature_c` | Celsius (°C) | Core battery/PDU pack temperature |
| 3 | `power_w` | Watts (W) | Total electrical instantaneous power consumption |
| 4 | `dv_dt` | V/s | First temporal derivative of bus voltage |
| 5 | `dt_dt` | °C/s | First temporal derivative of temperature (Joule heating rate) |
| 6 | `est_r_int` | Ohms ($\Omega$) | Instantaneous dynamic battery internal resistance |

### Target Labels & Failure Mode Catalog
Diagnostic classification evaluates 6 distinct operational states:
1. `NOMINAL_OPERATION`: Normal orbital charge/discharge cycles within nominal envelopes ($V \in [26, 30]\text{V}$, $T \le 35^\circ\text{C}$).
2. `BATTERY_INTERNAL_RESISTANCE_SPIKE`: Rapid internal impedance surge ($R_{\text{int}} > 2.0\times$ nominal), elevated $IR$ drop.
3. `SOLAR_ARRAY_STRING_FAULT`: Partial or full solar panel string loss during sunlight ($P_{\text{pv}} < 50\%$).
4. `THERMAL_RUNAWAY_INITIATION`: Uncontrolled exothermic heating ($\dot{Q}_{\text{exo}} > 50\text{W}$, $dT/dt > 0.08^\circ\text{C/s}$).
5. `PARASITIC_BUS_OVERLOAD`: Heavy electrical short-circuit or abnormal payload current draw dragging bus voltage down.
6. `SENSOR_BIAS_DRIFT`: Persistent static telemetry sensor offset without physical thermal/power signature.

---

## 3. Out-Of-Distribution (OOD) Definitions (Pre-Evaluation Lock)

To prevent post-hoc bias, OOD categories are mathematically and physically defined **prior** to experimental execution:

- **Category OOD-1 (Unseen Physical Failure)**: Catastrophic ultra-low impedance bus short-circuit ($P_{\text{load}} = 500\text{W}$, $V_{\text{bus}} < 12\text{V}$, severe transient $dV/dt < -5\text{V/s}$), never present in training data.
- **Category OOD-2 (Simultaneous Compound Anomaly)**: Concurrent multi-subsystem fault combining solar string loss (50% generation loss) and exothermic thermal runaway (65W heat injection) occurring at the exact same orbital timestamp.
- **Category OOD-3 (Extreme Thermal Inversion)**: Severe cryogenic deep-eclipse cold freeze ($T_{\text{core}} < -45^\circ\text{C}$) inducing non-linear electrochemical freezeout and anomalous voltage depression.
- **Category OOD-4 (Sensor Sign / Polarity Inversion)**: Hardware instrumentation wiring failure resulting in inverted current polarity during battery discharge.

---

## 4. Comprehensive Leakage Audit Checklist

| Leakage Dimension | Potential Threat | Audit Finding | Safeguard / Resolution |
|---|---|---|---|
| **Temporal Leakage** | Consecutive time points leaking sequential autocorrelation into test set | **NO LEAKAGE DETECTED** | Dataset is partitioned at the **trajectory scenario level** rather than random point sampling. Test frames originate from separate, independently initialized simulation runs. |
| **Scenario Leakage** | Same scenario seeds or fault onset parameters appearing in both train and test | **NO LEAKAGE DETECTED** | Training, validation, and testing scenarios use distinct non-overlapping random seeds and fault injection start times. |
| **Preprocessing Leakage** | MinMax or Standard scaling parameters computed over full dataset | **NO LEAKAGE DETECTED** | Scaling transformers (mean, standard deviation) are fit strictly on the **training fold** only, and applied to validation and test folds without refitting. |
| **Threshold Leakage** | OOD rejection threshold tuned on the final test set | **NO LEAKAGE DETECTED** | The epistemic threshold $\tau_{\text{locked}}$ is computed strictly as the 95th percentile of validation set epistemic scores and frozen before test evaluation. |
| **Feature Selection Leakage** | Features chosen based on test set feature importance | **NO LEAKAGE DETECTED** | The 7-dimensional feature space was fixed a priori based on aerospace EPS physics. |
| **Hyperparameter Leakage** | Baseline hyperparameters tuned against test set metrics | **NO LEAKAGE DETECTED** | Model hyperparameters (e.g. Random Forest depth, MLP hidden layers) are validated via 5-fold cross validation strictly on the training partition. |

---

## 5. Audit Conclusion

The data infrastructure exhibits **zero leakage**:
- All raw hashes match recorded provenance.
- The separation between training, validation, and held-out test scenarios is complete.
- OOD categories and threshold determination protocols are locked.
- Scientific validity is certified for Phase 3 implementation.
