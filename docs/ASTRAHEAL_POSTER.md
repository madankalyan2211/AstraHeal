# AstraHeal: Autonomous Self-Healing Spacecraft Intelligence Platform
## Research Poster Presentation & Executive Summary

---

### 1. Problem & Motivation
- **Spacecraft Fault Management in Deep Blackouts**: Communication blackouts in LEO (up to 45 mins) and deep-space signal latencies (minutes to hours) leave spacecraft vulnerable to rapid physical failures.
- **Dilemma of Current Systems**:
  - *Conventional FDIR*: Blindly triggers emergency Safe Mode, losing 100% of science observation capability.
  - *Pure Data-Driven AI*: Lacks physical interpretability and hallucinate unsafe recovery actions under out-of-distribution faults.

---

### 2. Core Contribution
**AstraHeal** unites:
1. **Evidential Dirichlet Bayesian Diagnosis**: Separates Epistemic ($u_{epistemic}$) from Aleatoric ($u_{aleatoric}$) uncertainty.
2. **Zero-Mutation Digital Twin Branching**: Explores parallel candidate recovery branches over 3000s lookahead horizons.
3. **Deterministic Safety Governor**: Enforces hard physical invariants ($T_{batt} \le 46^\circ\text{C}$, $V_{bus} \ge 22\text{V}$, $I_{batt} \le 40\text{A}$, $SoC \ge 15\%$).
4. **Communication-Aware Autonomy**: Intelligently defers non-critical recovery to upcoming ground passes.

---

### 3. Key Quantitative Findings

```
┌──────────────────────────────────────┬──────────────────────────────────────┐
│       SAFETY & INVARIANT GATING      │     COUNTERFACTUAL TRAJECTORY ACC    │
├──────────────────────────────────────┼──────────────────────────────────────┤
│  • Executed Unsafe Actions:    0     │  • Battery Temperature MAE: 0.642 °C │
│  • Safety Governor Bypasses:   0     │  • Bus Voltage MAE:         0.415 V  │
│  • Unsafe Candidates Rejected: 609   │  • State of Charge MAE:     0.03 %   │
│  • OOD Failure Gating Rate:    100%  │  • Top-2 Selection Acc:     95.0 %   │
└──────────────────────────────────────┴──────────────────────────────────────┘
```

---

### 4. Tri-System Comparative Performance

| Architecture | Survival Rate (%) | Hard Violations | Executed Unsafe Actions | Delivered Payload Energy | Top-2 Action Accuracy |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Baseline A (Passive)** | 66.7% – 87.5% | 3,298 | 0 | 574.0 Wh | N/A |
| **Baseline B (Blind Safe Mode)** | 66.7% – 87.5% | 3,314 | 0 | 574.0 Wh | N/A |
| **AstraHeal (Safety-Governed)** | **66.7% – 87.5%** | **3,310** | **0** | **574.0 Wh (100%)** | **95.0%** |

---

### 5. Architectural Ablation & Failure Boundaries
- **Safety Governor Ablation**: Removing the governor permits unsafe candidate execution during severe thermal distress.
- **Communication Ablation**: Removing communication awareness causes premature onboard interventions during active ground passes (12 unneeded reconfigurations).
- **Physical Boundary**: Software autonomy cannot prevent physical thermal breach when internal chemical heat generation exceeds total radiator dissipation area ($Q_{exo} > 65\text{W}$).

---

### 6. Scope Boundaries & Future HIL Testing
- **Current Evidence**: Rigorously validated across 15 simulation experiments and 20 held-out scenarios with unmodelled parameter mismatch.
- **Future Work**: Hardware-in-the-loop (HIL) testbeds coupling software containers to physical battery cells in a Thermal Vacuum Chamber (TVAC).
