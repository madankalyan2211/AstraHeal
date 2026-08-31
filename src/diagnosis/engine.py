"""Fault diagnosis engine combining physics rules and Bayesian evidential inference."""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple, Union
import pandas as pd

from src.anomaly.detector import AnomalyReport
from src.diagnosis.schema import DiagnosisReport, DiagnosisStatus, FailureMode
from src.diagnosis.rules import PhysicsRuleDiagnosticEngine
from src.diagnosis.bayesian import BayesianEvidentialDiagnosticEngine


class FaultDiagnosisEngine:
    """Orchestrator for spacecraft fault diagnosis and uncertainty quantification."""

    def __init__(
        self,
        primary_method: str = "bayesian",
        confidence_cutoff: float = 0.60
    ):
        self.primary_method = primary_method
        self.rule_engine = PhysicsRuleDiagnosticEngine()
        self.bayesian_engine = BayesianEvidentialDiagnosticEngine(confidence_cutoff=confidence_cutoff)

    def diagnose_frame(
        self,
        anomaly_report: AnomalyReport,
        feature_row: pd.Series
    ) -> DiagnosisReport:
        """Diagnose a single anomaly frame using the configured engine."""
        if self.primary_method == "rules":
            return self.rule_engine.diagnose(anomaly_report, feature_row)
        else:
            return self.bayesian_engine.diagnose(anomaly_report, feature_row)

    def compare_methods(
        self,
        anomaly_report: AnomalyReport,
        feature_row: pd.Series
    ) -> Dict[str, DiagnosisReport]:
        """Run both physics rule and Bayesian evidential engines side-by-side for validation."""
        return {
            "physics_rule": self.rule_engine.diagnose(anomaly_report, feature_row),
            "bayesian_evidential": self.bayesian_engine.diagnose(anomaly_report, feature_row)
        }

    def diagnose_batch(
        self,
        anomaly_reports: List[AnomalyReport],
        feature_df: pd.DataFrame
    ) -> List[DiagnosisReport]:
        """Diagnose an entire sequence of anomaly reports."""
        if len(anomaly_reports) != len(feature_df):
            raise ValueError("Length of anomaly reports must match feature DataFrame")

        diagnoses = []
        for i in range(len(anomaly_reports)):
            rep = anomaly_reports[i]
            row = feature_df.iloc[i]
            diag = self.diagnose_frame(rep, row)
            diagnoses.append(diag)

        return diagnoses
