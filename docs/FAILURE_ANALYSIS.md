# AstraHeal — Failure Case Analysis & Taxonomy

**Experiment**: `experiments/11_failure_case_analysis.py`  
**Date**: 2026-08-31  

---

## 1. Failure Taxonomy Matrix

A transparent, honest engineering evaluation of failure modes where AstraHeal reaches physical boundaries, correctly abstains, or encounters sensor corruption.

| Case ID | Scenario Description | Actual System Behavior | Root Cause | Safety Consequence | Mitigation Strategy |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **FAIL-01** | **Uncontainable Severe Thermal Runaway (140W heat)** | Safety Governor rejects all 5 candidates; executes Emergency Safe Mode fallback. | Radiator area ($0.8\text{ m}^2$) thermal rejection capacity ($~65\text{W}$) is overwhelmed by extreme exothermic reaction. | Physical thermal damage occurs despite software intervention. | Hardware-level pyrotechnic circuit breaker or thermal battery disconnection relay. |
| **FAIL-02** | **Compound Multi-Fault (Solar loss + Bus Short)** | Epistemic uncertainty spikes to $1.000$; outputs `UNKNOWN_FAILURE` and enters safe standby. | Concurrent failures project outside all single-fault training manifolds. | Correct abstention: prevents executing an erroneous single-fault remedy. | Queue multi-channel telemetry log for priority ground downlink at next pass. |
| **FAIL-03** | **Corrupted Sensor Bias (-10V offset)** | Anomaly detector triggers; Safety Governor evaluates physical voltage floor across branches. | Sensor hardware drift without corresponding change in physical current/temperature. | Temporary unnecessary safe mode entry. | Analytical redundancy and multi-sensor voting logic across redundant telemetry taps. |
| **FAIL-04** | **Deep Eclipse Starvation (30% initial SoC)** | Battery SoC drops below 15% during 35-minute shadow pass. | Insufficient initial energy storage prior to shadow entry. | Low-voltage bus warning. | Predictive pre-eclipse energy reserve scheduling. |
| **FAIL-05** | **Safety Governor Critical Rejection** | Proposed continuing nominal operations is strictly REJECTED ($T > 46^\circ\text{C}$ predicted). | Counterfactual lookahead predicts thermal runaway in No-Op branch. | System successfully prevents spacecraft burnout by choosing safe throttling. | Automated ranking surfaces verified safe candidate actions. |

---

## 2. Scientific Insights on System Limitations

1. **Software Autonomy Cannot Overcome Severe Physical Deficits**: When internal physical heat generation exceeds maximum radiative dissipation ($Q_{exo} > Q_{rad}$), no software power throttling can prevent temperature rise without physical hardware separation.
2. **Safe Abstention is a Feature, Not a Failure**: High epistemic uncertainty ($u_{epistemic} \to 1.0$) correctly prevents the system from making overconfident guesses on novel compound anomalies.
