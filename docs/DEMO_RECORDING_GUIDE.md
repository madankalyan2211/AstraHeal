# AstraHeal v1.0 — 3–5 Minute Research Demo Recording Guide

**Document**: `docs/DEMO_RECORDING_GUIDE.md`  
**Purpose**: Structured timing, screen sequence, and narrative guide for recording or presenting the AstraHeal v1.0 public demonstration video/screencast.  

---

## Technical Setup Before Recording
1. **Terminal Window**: Sized to 80x24 characters or 1080p width with dark high-contrast theme.
2. **Web Browser Window**: Navigated to `http://localhost:8000` (serving `dashboard/`).
3. **Launch Server**: `python3 -m http.server 8000 --directory dashboard`

---

## 3–5 Minute Presentation Timeline

### [00:00 – 00:30] Problem & Motivation
- **Screen**: Title Slide / Browser showing `AstraHeal Mission Dashboard` with the disclaimer banner.
- **Narrative**:
  > *"Spacecraft operating in Low Earth Orbit and deep-space regimes frequently experience unexpected subsystem anomalies during communication blackouts. Conventional FDIR systems react conservatively by dropping the spacecraft into emergency Safe Mode, prematurely ending science operations. AstraHeal solves this by uniting evidential Bayesian uncertainty, digital twin counterfactual lookahead, and deterministic safety gating."*

---

### [00:30 – 01:15] System Architecture
- **Screen**: Architecture Diagram (`README.md` or `docs/figures/05_digital_twin_orbit_telemetry.png`).
- **Narrative**:
  > *"The architecture processes causal telemetry features, computes Dirichlet epistemic and aleatoric uncertainty, forks the digital twin state into zero-mutation counterfactual branches, evaluates candidate actions against hard physical safety invariants, and arbitrates execution based on ground contact schedules."*

---

### [01:15 – 02:00] In-Flight Fault & Anomaly Detection
- **Screen**: Terminal executing `python3 demo.py` up to Section 2.
- **Narrative**:
  > *"At t = 3500s, while the satellite is in direct sunlight, we inject an in-flight 4.5x battery impedance surge. At t = 3700s, the multivariate anomaly detector triggers on residual impedance (Anomaly Score: 1.000), detecting the physical fault with zero latency."*

---

### [02:00 – 02:45] Evidential Diagnosis & Uncertainty Quantification
- **Screen**: Terminal output Section 2 / Dashboard Evidential Uncertainty Panel.
- **Narrative**:
  > *"The Dirichlet evidential diagnosis engine processes the signature. It estimates an epistemic uncertainty of 1.000, correctly flagging an out-of-distribution anomaly. Because the satellite is in ground occultation with 4,336s until next pass, the communication manager authorizes immediate onboard autonomous recovery (`ACT_AUTONOMOUSLY`)."*

---

### [02:45 – 03:30] Counterfactual Lookahead Simulation
- **Screen**: Terminal output Section 3 / Dashboard Counterfactual Lookahead Table.
- **Narrative**:
  > *"AstraHeal forks the active digital twin into 5 isolated branches, simulating forward across a 3000-second lookahead horizon. It evaluates NOOP, Safe Mode, 50% Payload Throttling, Payload Isolation, and Conservative Standby without mutating active spacecraft memory."*

---

### [03:30 – 04:15] Deterministic Safety Governor Gating
- **Screen**: Terminal output Section 3 & 4.
- **Narrative**:
  > *"The Safety Governor verifies each branch against hard physical limits: temperature below 46°C, bus voltage above 22V, and SoC above 15%. In this sunlight scenario, charge current is zero due to overcharge taper, keeping core temperature at 18.9°C. `ACT-00-NOOP` achieves the highest safe utility score (0.900), avoiding an unnecessary safe mode shutdown and preserving 100% science payload capability."*

---

### [04:15 – 05:00] Recovery & Independent Validation Results
- **Screen**: Terminal output Section 5 & Final Summary / `docs/figures/15_independent_validation/06_action_ranking_accuracy.png`.
- **Narrative**:
  > *"The spacecraft propagates for 2 additional orbits, remaining fully stabilized with zero violations. Across 20 held-out validation scenarios subjected to unmodelled physical parameter perturbations, AstraHeal achieves 95% Top-2 action selection accuracy, sub-degree temperature prediction error, and zero executed unsafe actions. AstraHeal v1.0 establishes a verified, open-source foundation for safe spacecraft autonomy."*
