# AstraHeal Paper 4 — Phase 8: Recovery Success Definition & Classification Criteria

**Date**: 2026-09-13  
**Status**: COMPLETE  
**Auditor**: AstraHeal Research Group & Autonomous Systems Lab  
**Scope**: Quantitative Definition of Recovery Outcomes, Clearance Horizons, and State Envelope Adherence

---

## 1. Formal Mathematical Criteria for Recovery Success

To eliminate retrospective bias, recovery outcomes are categorized prior to experimental execution according to strict, physically grounded criteria.

Let an anomaly event be triggered at time $t_{\text{fault}}$. The recovery evaluation window is defined as $[t_{\text{action}}, t_{\text{action}} + H_{\text{eval}}]$, where $H_{\text{eval}} = 300\,\text{s}$ ($5.0\,\text{minutes}$).

### A. Full Autonomous Recovery (SUCCESS)
A scenario is classified as **Full Recovery** if and only if all four conditions hold:
1. **Safety Invariant Adherence**: For all $t \in [t_{\text{action}}, t_{\text{action}} + H_{\text{eval}}]$:
   $$T_{\text{core}}(t) \le 46.0^\circ\text{C}, \quad V_{\text{bus}}(t) \ge 22.0\,\text{V}, \quad I_{\text{batt}}(t) \le 40.0\,\text{A}, \quad \text{SoC}(t) \ge 0.15$$
2. **Thermal Stability**: $\frac{dT_{\text{core}}}{dt} \le 0.02^\circ\text{C}/\text{s}$ at $t = t_{\text{action}} + H_{\text{eval}}$ (no self-sustaining exothermic temperature escalation).
3. **Bus Voltage Margin**: $V_{\text{bus}}(t_{\text{action}} + H_{\text{eval}}) \ge 24.0\,\text{V}$ (safe margin above $22.0\,\text{V}$ brownout floor).
4. **Mission Functionality**: Spacecraft maintains active payload delivery ($P_{\text{payload}} > 0$) or scheduled low-power payload operation.

### B. Degraded Recovery (STABILIZED_SAFE_HOLD)
A scenario is classified as **Degraded Recovery** if:
1. All hard physical safety invariants are strictly satisfied (zero breaches); AND
2. The vehicle successfully avoids thermal runaway and brownout, but had to shed scientific payloads completely ($P_{\text{payload}} = 0$, `ACT_SAFE_MODE` or `ACT_SHUTDOWN_PAYLOAD`) to maintain thermal/voltage survival.

### C. Graceful Dead-End (NO_SAFE_ACTION_AVAILABLE)
Under extreme, physically unrecoverable hardware destruction (e.g., permanent $100\%$ solar string severance combined with severe cell shorting), no candidate action can physically prevent an eventual breach.
* **Criterion**: The governor correctly identifies that all $N$ candidate actions breach at least one hard invariant, and transitions cleanly to `NO_SAFE_ACTION_AVAILABLE` without commanding destructive or erratic actuations.

### D. Catastrophic Failure (UNSAFE_FAILURE)
A scenario is classified as an **Unsafe Failure** if any of the following occur:
1. Any hard physical invariant is violated while an action was authorized by the governor ($T > 46^\circ\text{C}$, $V < 22\text{V}$, $I > 40\text{A}$, $\text{SoC} < 0.15$).
2. Spacecraft enters uncommanded power collapse or thermal runaway.
3. The system halts due to an unhandled software exception, `NaN`, or infinite loop.
