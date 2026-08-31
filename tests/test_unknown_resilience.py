"""Unit tests for Stage 10 Unknown-Failure Resilience."""

import pytest
from src.diagnosis.schema import DiagnosisReport, DiagnosisStatus, FailureMode
from src.diagnosis.resilience import UnknownFailureResilienceEvaluator
from src.planner.recovery_planner import ActionPlanReport
from src.planner.actions import RecoveryAction, RecoveryActionType


def test_known_condition_authorizes_action():
    """Verify known condition with low epistemic uncertainty is authorized without forced fallback."""
    diag = DiagnosisReport(
        timestamp=100.0,
        status=DiagnosisStatus.KNOWN_FAILURE,
        primary_failure_mode=FailureMode.BATTERY_INTERNAL_RESISTANCE_SPIKE.value,
        affected_subsystem="EPS_BATTERY",
        confidence=0.92,
        uncertainty=0.08,
        epistemic_uncertainty=0.04,  # Low OOD distance
        aleatoric_uncertainty=0.06,
        method="Bayesian"
    )

    plan = ActionPlanReport(
        timestamp=100.0,
        diagnosis="BATTERY_RESISTANCE_SPIKE",
        confidence=0.92,
        total_candidates_evaluated=3,
        approved_candidates_count=2,
        rejected_candidates_count=1,
        selected_action=RecoveryAction(action_id="ACT-THROTTLE", action_type=RecoveryActionType.REDUCE_PAYLOAD_LOAD, description=""),
        selection_score=0.88
    )

    evaluator = UnknownFailureResilienceEvaluator(max_epistemic_for_aggressive_action=0.50)
    profile = evaluator.evaluate_gating(diag, plan)

    assert profile.is_known_condition is True
    assert profile.abstained_from_aggressive_action is False
    assert profile.safe_fallback_triggered is False


def test_unseen_ood_condition_triggers_safe_fallback():
    """Verify novel/unseen condition with high epistemic uncertainty inhibits aggressive action."""
    diag = DiagnosisReport(
        timestamp=500.0,
        status=DiagnosisStatus.UNKNOWN_FAILURE,
        primary_failure_mode=FailureMode.NOVEL_UNSEEN_ANOMALY.value,
        affected_subsystem="UNKNOWN",
        confidence=0.30,
        uncertainty=0.95,
        epistemic_uncertainty=0.92,  # Very high OOD distance
        aleatoric_uncertainty=0.40,
        method="Bayesian"
    )

    plan = ActionPlanReport(
        timestamp=500.0,
        diagnosis="NOVEL_UNSEEN_ANOMALY",
        confidence=0.30,
        total_candidates_evaluated=3,
        approved_candidates_count=1,
        rejected_candidates_count=2,
        selected_action=RecoveryAction(action_id="ACT-AGGRESSIVE", action_type=RecoveryActionType.DISABLE_NON_CRITICAL_SUBSYSTEM, description=""),
        selection_score=0.50
    )

    evaluator = UnknownFailureResilienceEvaluator(max_epistemic_for_aggressive_action=0.50)
    profile = evaluator.evaluate_gating(diag, plan)

    assert profile.is_known_condition is False
    assert profile.abstained_from_aggressive_action is True
    assert profile.safe_fallback_triggered is True
    assert "INHIBITED" in profile.rationale
