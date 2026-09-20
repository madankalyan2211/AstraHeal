# AstraHeal Paper 3 — Adversarial Proposal & Safety Barrier Testing

**Manuscript Title**: *AstraHeal: Deterministic Safety Gating for Uncertainty-Aware Autonomous Spacecraft Fault Recovery*  
**Evaluation Date**: September 2026  
**Auditor**: Aerospace Safety Assurance & Formal Verification Team  

---

## 1. Objectives & Threat Model

The central premise of Paper 3 is that **the upstream AI system is fallible**: it may be overconfident, misled by partial observability, corrupted by adversarial telemetry, or hallucinate invalid actuation parameters.

To test whether the Deterministic Safety Governor acts as a truly independent safety barrier, we designed an adversarial threat model with five distinct attack vectors:
1. **Deceptive Load Throttling (`excessive_power`)**: Upstream proposal metadata reports a power reduction, but the actuation parameters command excessive power consumption (950W–1500W), exceeding the 880W PDU limit.
2. **Exothermic Thermal Injection (`thermal_violation`)**: Proposal commands heater or payload activation during elevated battery temperatures, predicting core temperatures of 48.0°C–65.0°C (breaching the 46.0°C barrier).
3. **Severe Undervoltage Depletion (`undervoltage_collapse`)**: Proposal commands heavy power draw during eclipse or degraded solar array states, driving bus voltage down to 12.0V–20.5V (breaching the 22.0V floor).
4. **Harness Overcurrent Surge (`overcurrent_spike`)**: Proposal triggers high-rate charge or cross-strapping, demanding 45.0A–75.0A from battery harnesses rated for 40.0A max.
5. **Telemetry Corruption & Malformed Actions (`invalid_state`)**: Proposals containing `NaN` / `Inf` floating-point values or uncertified flight action identifiers.

---

## 2. Experimental Results (Experiment P3-E4)

Across 400 systematically injected adversarial proposals (80 per attack vector), every proposal was tagged with artificially inflated AI confidence scores ($\ge 0.96$).

| Attack Vector | Injected Count | AI Confidence Range | Governor Rejection Count | Rejection Rate | Unsafe Actions Executed | Fail-Closed Invocations |
|---|---|---|---|---|---|---|
| **Excessive Power Surge** | 80 | $[0.98, 0.99]$ | 80 | **100.0%** | **0 (0.0%)** | 0 |
| **Thermal Runaway Injection** | 80 | $[0.96, 0.98]$ | 80 | **100.0%** | **0 (0.0%)** | 0 |
| **Undervoltage Collapse** | 80 | $[0.95, 0.97]$ | 80 | **100.0%** | **0 (0.0%)** | 0 |
| **Harness Overcurrent** | 80 | $[0.97, 0.99]$ | 80 | **100.0%** | **0 (0.0%)** | 0 |
| **Corrupted Telemetry (NaN)** | 80 | $0.99$ | 80 | **100.0%** | **0 (0.0%)** | 80 |
| **TOTAL** | **400** | **[0.95, 0.99]** | **400** | **100.0%** | **0 (0.0%)** | **80** |

---

## 3. Critical Scientific Findings

1. **Total Decoupling from Upstream AI Confidence**:  
   In traditional heuristic architectures, high confidence ($\text{confidence} > 0.95$) often serves as a proxy for safety authorization. The Safety Governor operates with zero knowledge of or reliance upon AI confidence; regardless of whether an upstream model asserts 99% certainty, the candidate action is strictly evaluated against physics equations and rejected if invariant boundaries are violated.

2. **Fail-Closed Resilience**:  
   Corrupted inputs containing IEEE 754 `NaN` or `Inf` floating-point anomalies do not cause uncaught exceptions or accidental approvals. The governor intercepts invalid numerical states and immediately returns `REJECT (FAIL_CLOSED_CORRUPTED_TELEMETRY)`.

3. **Audit Trail Transparency**:  
   Every rejected proposal yields a human-readable and machine-auditable justification detailing the exact numerical breach and physical margin (e.g., `"Predicted battery discharge current (52.4A) exceeds harness rating (40.0A)"`).
