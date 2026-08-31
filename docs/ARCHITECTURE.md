# AstraHeal System Architecture

## 1. End-to-End Autonomous Pipeline

```
                 +-----------------------------------------------+
                 |              Spacecraft Telemetry             |
                 +-----------------------+-----------------------+
                                         |
                                         v
                 +-----------------------------------------------+
                 |       Stage 4: Baseline Anomaly Detection     |
                 |  - Rolling Z-Score / Mahalanobis Distance     |
                 |  - Isolation Forest / One-Class SVM Baselines |
                 +-----------------------+-----------------------+
                                         |
                                         v
                 +-----------------------------------------------+
                 |    Stage 5: Fault Diagnosis & Uncertainty     |
                 |  - Dirichlet Evidential Bayesian Classifier   |
                 |  - Epistemic (OOD) vs Aleatoric (Entropy) Unc |
                 |  - KNOWN_FAILURE / UNKNOWN_FAILURE / INSUFF.  |
                 +-----------------------+-----------------------+
                                         |
                                         v
                 +-----------------------------------------------+
                 |      Stage 6: Spacecraft EPS Digital Twin     |
                 |  - Orbit Mechanics, PV Arrays, Thevenin ECM   |
                 +-----------------------+-----------------------+
                                         |
                                         v
                 +-----------------------------------------------+
                 |   Stage 7: Counterfactual Branch Simulator    |
                 |  - Deep-Cloned Forward State Evaluation       |
                 +-----------------------+-----------------------+
                                         |
                                         v
                 +-----------------------------------------------+
                 |     Stage 8: Autonomous Recovery Planner      |
                 |  - Multi-Objective Soft Ranking (Surv/Pay/Eng)|
                 +-----------------------+-----------------------+
                                         |
                                         v
                 +-----------------------------------------------+
                 |     Stage 8: Deterministic Safety Governor    |
                 |  - Hard Constraint Invariant Gate (APPROVED)  |
                 +-----------------------+-----------------------+
                                         |
                                         v
                 +-----------------------------------------------+
                 |  Stage 9: Communication Arbitration & Execute |
                 |  - ACT_AUTONOMOUSLY vs WAIT_FOR_GROUND        |
                 |  - Safe Plan Execution on Active Spacecraft   |
                 +-----------------------------------------------+
```

## 2. Core Architectural Invariants

1. **Safety Governor Primacy**: AI models propose candidate actions; the Deterministic Safety Governor is the sole authority authorized to approve execution on active systems.
2. **Pure Branch Isolation**: Counterfactual simulations operate in deep-cloned memory spaces and never mutate primary telemetry or simulator state.
3. **Calibrated Ignorance**: When epistemic uncertainty exceeds $0.50$, the system inhibits aggressive actions and transitions to conservative safe standby.
