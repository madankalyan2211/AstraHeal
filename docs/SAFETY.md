# AstraHeal Safety Doctrine & Invariant Specifications

## 1. Fundamental Safety Invariants

```
                +---------------------------------+
                |      AI / Autonomous Planner    |
                +----------------+----------------+
                                 |
                                 | [PROPOSES ACTION]
                                 v
                +---------------------------------+
                |  Deterministic Safety Governor  |
                +----------------+----------------+
                                 |
                        +--------+--------+
                        |                 |
                   [APPROVED]         [REJECTED]
                        |                 |
                        v                 v
                +---------------+ +---------------+
                | Active Twin / | |  Inhibit &    |
                |  Spacecraft   | | Safe Standby  |
                +---------------+ +---------------+
```

## 2. Immutable Hard Safety Constraints

| Constraint Name | Threshold Limit | Rationale |
| :--- | :--- | :--- |
| **Max Battery Core Temp** | $\le 46.0^\circ\text{C}$ | Prevents exothermic self-accelerating thermal runaway. |
| **Min Bus Voltage** | $\ge 22.0\text{V}$ | Prevents undervoltage lockout and power supply shutdown. |
| **Max Battery Current** | $\le 40.0\text{A}$ | Prevents PDU wire harness overcurrent damage. |
| **Min Reserve State of Charge** | $\ge 15.0\%$ | Preserves emergency power buffer for attitude control and OBC. |
| **Mission Survival Invariant** | True | Guarantees counterfactual branch does not lead to irrecoverable loss. |

## 3. High-Uncertainty Gating Policy
If epistemic uncertainty $u_{epistemic} > 0.50$ (Out-Of-Distribution anomaly), aggressive irreversible actions are inhibited, and the spacecraft enters conservative safe standby.
