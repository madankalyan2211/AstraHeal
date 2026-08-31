# AstraHeal — Stage 10 Research Report: Unknown-Failure Resilience & OOD Calibration

**Stage**: 10 — Unknown-Failure Resilience & Out-Of-Distribution (OOD) Gating  
**Status**: VERIFIED & COMPLETE  
**Execution Timestamp**: 2026-08-31  

---

## 1. Executive Summary

Stage 10 addresses a critical vulnerability in autonomous aerospace systems: **overconfident misdiagnosis when encountering unseen, novel, or compound failure modes.**

Under AstraHeal's uncertainty-gated architecture:
1. When faults match known physical clusters, epistemic uncertainty is low ($u_{epistemic} \le 0.45$), enabling authorized autonomous recovery.
2. When faults present novel compounding signatures, extreme severity, or sensor corruption ($u_{epistemic} > 0.50$), the system **refuses to guess** (`UNKNOWN_FAILURE`), inhibits high-risk aggressive actions, and transitions the spacecraft to a conservative, reversible safe standby state while queuing diagnostic logs for Earth review.

---

## 2. Architecture & Modules Implemented

- **`src/diagnosis/resilience.py`**:
  - `ResilienceProfile`: Standardized uncertainty evaluation container.
  - `UnknownFailureResilienceEvaluator`: Enforces policy gating between authorized execution and conservative safe fallback.
- **Uncertainty Calibration Matrix**:
  - Distinguishes **Epistemic Uncertainty** ($u_{epistemic} \in [0.0, 1.0]$, representing model ignorance / OOD distance) from **Aleatoric Uncertainty** ($u_{aleatoric} \in [0.0, 1.0]$, representing hypothesis ambiguity).

---

## 3. Verification & Benchmark Results

### Unit Tests
- `tests/test_unknown_resilience.py` (2 passing tests):
  - `test_known_condition_authorizes_action`: Verifies known in-distribution failure is authorized without unnecessary fallback.
  - `test_unseen_ood_condition_triggers_safe_fallback`: Verifies unseen OOD anomaly triggers abstention and safe standby fallback.

### Experiment 08 Execution
- Executed `experiments/08_unknown_failure_resilience.py`:
  - Evaluated 6 diverse stress scenarios across known archetypes and compound/unseen anomalies.
  - Generated uncertainty distribution scatter plot in `docs/figures/08_uncertainty_calibration_ood.png`.
  - Saved metric results to `evaluation/08_unknown_resilience_results.json`.

---

## 4. Next Step

Proceed directly to **Stage 11 (Research Benchmark & Adversarial Stress Testing)**.
