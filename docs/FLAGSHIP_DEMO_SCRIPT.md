# AstraHeal — 14-Step Flagship Demonstration Script

**Document**: `docs/FLAGSHIP_DEMO_SCRIPT.md`  
**Duration**: 3–5 Minutes  
**Scenario**: Closed-Loop In-Flight Fault Detection, Uncertainty Quantification, Counterfactual Lookahead, and Safe Recovery  
**Script Runner**: `python3 experiments/12_flagship_mission.py`  
**Dashboard Visualizer**: `python3 -m http.server 8000 --directory dashboard` -> `http://localhost:8000`  

---

## Demonstration Sequence

### [0:00 – 0:45] Step 1 & 2: Nominal Spacecraft LEO Orbit
- **Narrative**: *"We begin with our satellite operating nominally in a 550 km Sun-synchronous Low Earth Orbit. The spacecraft completes its shadow pass and enters orbital sunlight at $t=2066\text{s}$. The GaAs solar array generates 880W, maintaining the 28V regulated bus and charging the 40Ah battery pack at a nominal core temperature of $18.9^\circ\text{C}$."*
- **Visuals**: Telemetry shows smooth sinusoids; Anomaly Score = $0.012$; Mode = `SCIENCE`.

---

### [0:45 – 1:30] Step 3 & 4: In-Flight Fault Ingestion & Anomaly Detection
- **Narrative**: *"At $t=3500.0\text{s}$, an abrupt physical fault occurs: a 4.5x surge in battery internal resistance ($R_0$ spikes from $0.045\Omega$ to $0.202\Omega$). At $t=3700.0\text{s}$, the multivariate anomaly detector flags anomalous residual impedance, driving the Anomaly Score to $0.988$ (Detection Latency: 0s on step)."*
- **Visuals**: Amber warning indicator flashes; voltage residual rises.

---

### [1:30 – 2:15] Step 5, 6 & 7: Dirichlet Evidential Diagnosis & Blackout Check
- **Narrative**: *"The evidential Bayesian diagnosis engine processes the multi-channel residual signature. It classifies the event with $u_{epistemic} = 1.000$, recognizing an unseen impedance anomaly. Concurrently, the communication manager assesses ground connectivity: the satellite is in deep ground occultation with next contact in 4,336s ($>72$ minutes). Emergency onboard autonomous recovery is authorized (`ACT_AUTONOMOUSLY`)."*
- **Visuals**: Evidential uncertainty gauge displays $u_{epistemic} = 1.000$; Communication Link = `OUT_OF_RANGE`.

---

### [2:15 – 3:30] Step 8, 9, 10 & 11: Counterfactual Lookahead & Safety Governor Gating
- **Narrative**: *"AstraHeal forks the active digital twin into 5 isolated memory branches, simulating candidates forward 3000s (50 minutes):*
  1. *`ACT-00-NOOP`: Predicts $T_{max} = 18.9^\circ\text{C}$, $V_{min} = 31.0\text{V}$, $100\%$ payload.*
  2. *`ACT-01-SAFE-MODE`: Predicts $T_{max} = 18.9^\circ\text{C}$, $V_{min} = 31.4\text{V}$, $0\%$ payload.*
  3. *`ACT-02-THROTTLE-50`: Predicts $T_{max} = 18.9^\circ\text{C}$, $V_{min} = 31.2\text{V}$, $50\%$ payload.*
  4. *`ACT-03-DISABLE-PAYLOAD`: Predicts $T_{max} = 18.9^\circ\text{C}$, $V_{min} = 31.4\text{V}$, $0\%$ payload.*
  5. *`ACT-04-STANDBY`: Predicts $T_{max} = 18.9^\circ\text{C}$, $V_{min} = 31.0\text{V}$, $100\%$ payload.*

  *The deterministic Safety Governor verifies that all 5 candidates satisfy hard safety limits ($T \le 46^\circ\text{C}$, $V \ge 22\text{V}$, $SoC \ge 15\%$). In soft utility ranking, `ACT-00-NOOP` achieves the highest score ($0.900$) because the spacecraft is in sunlight with a fully charged battery (charge taper keeps current at $\approx 0\text{A}$), avoiding unnecessary science disruption."*
- **Visuals**: Counterfactual comparison table populates with predicted trajectories and safety margins.

---

### [3:30 – 4:30] Step 12, 13 & 14: Execution & 2-Orbit Post-Recovery Stabilization
- **Narrative**: *"At $t=3700.0\text{s}$, `ACT-00-NOOP` is authorized and executed. The mission continues for 2 additional orbits (12,000s). The battery temperature remains safe ($18.9^\circ\text{C}$), bus voltage stays regulated at $31.8\text{V}$, and $100\%$ science observation capability is preserved without false safe-mode shutdowns."*
- **Visuals**: Post-recovery telemetry demonstrates thermal and electrical stability through multiple orbits.

---

### [4:30 – 5:00] Physical Limitations & Disclaimer
- **Narrative**: *"We emphasize that AstraHeal is a simulation research platform. In severe uncontainable physical faults (such as exothermic runaway exceeding radiator capacity), software autonomy cannot alter radiative physics. Future work will transition AstraHeal to hardware-in-the-loop CubeSat testbeds."*
