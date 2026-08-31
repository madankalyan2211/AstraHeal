"""Baseline anomaly detection models: Statistical (Z-Score, Mahalanobis), Isolation Forest, and One-Class SVM."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Union
import numpy as np
import pandas as pd
from pydantic import BaseModel, Field
from sklearn.ensemble import IsolationForest
from sklearn.svm import OneClassSVM
from sklearn.preprocessing import StandardScaler

from src.anomaly.features import AnomalyFeatureExtractor


class AnomalyReport(BaseModel):
    """Standardized anomaly detection output frame."""
    timestamp: float = Field(..., description="Timestamp of the evaluated frame")
    anomaly_score: float = Field(..., ge=0.0, le=1.0, description="Normalized anomaly score [0.0 = nominal, 1.0 = severe anomaly]")
    is_anomaly: bool = Field(..., description="Binary anomaly trigger decision")
    affected_signals: List[str] = Field(default_factory=list, description="Specific telemetry channels identified as anomalous")
    detector_name: str = Field(..., description="Algorithm used for detection")
    details: Dict[str, Any] = Field(default_factory=dict, description="Diagnostic metrics, channel z-scores, distance values")


class BaseAnomalyDetector(ABC):
    """Abstract base class for all spacecraft anomaly detection models."""

    def __init__(self, name: str):
        self.name = name

    @abstractmethod
    def fit(self, df_nominal: pd.DataFrame) -> BaseAnomalyDetector:
        """Fit detector on nominal baseline telemetry."""
        pass

    @abstractmethod
    def detect_frame(self, row: pd.Series, history_window: Optional[pd.DataFrame] = None) -> AnomalyReport:
        """Detect anomaly on a single incoming telemetry frame."""
        pass

    @abstractmethod
    def detect_batch(self, df: pd.DataFrame) -> List[AnomalyReport]:
        """Detect anomalies across an entire time series batch."""
        pass


class StatisticalDetector(BaseAnomalyDetector):
    """Interpretable statistical detector using Rolling Z-Score, IQR, and Mahalanobis distance."""

    def __init__(
        self,
        channels: Optional[List[str]] = None,
        z_threshold: float = 3.0,
        mahalanobis_threshold: float = 3.5,
        window_size: int = 20
    ):
        super().__init__(name="StatisticalDetector_ZScore_Mahalanobis")
        self.channels = channels or ["voltage_v", "current_a", "temperature_c", "power_w"]
        self.z_threshold = z_threshold
        self.mahalanobis_threshold = mahalanobis_threshold
        self.feature_extractor = AnomalyFeatureExtractor(channels=self.channels, window_size=window_size)
        self.fitted = False

    def fit(self, df_nominal: pd.DataFrame) -> StatisticalDetector:
        self.feature_extractor.fit_baseline(df_nominal)
        self.fitted = True
        return self

    def detect_frame(self, row: pd.Series, history_window: Optional[pd.DataFrame] = None) -> AnomalyReport:
        t = float(row.get("timestamp", 0.0))
        affected_signals = []
        scores_by_channel = {}

        if not self.fitted and history_window is None:
            return AnomalyReport(
                timestamp=t,
                anomaly_score=0.0,
                is_anomaly=False,
                affected_signals=[],
                detector_name=self.name,
                details={"status": "unfitted"}
            )

        # Evaluate per-channel deviations
        max_abs_z = 0.0
        avail_channels = [c for c in self.channels if c in row]

        for c in avail_channels:
            val = float(row[c])
            # Check against history window or baseline
            if history_window is not None and len(history_window) >= 5 and c in history_window:
                mu = history_window[c].mean()
                sigma = history_window[c].std()
                sigma = sigma if sigma > 1e-5 else 1.0
                z = abs(val - mu) / sigma
            elif self.fitted:
                idx = self.channels.index(c)
                z = abs(val - self.feature_extractor.mean_baseline[idx]) / self.feature_extractor.std_baseline[idx]
            else:
                z = 0.0

            scores_by_channel[c] = float(z)
            if z > self.z_threshold:
                affected_signals.append(c)
            max_abs_z = max(max_abs_z, z)

        # Normalize score into [0.0, 1.0] using sigmoid-like scaling
        norm_score = float(1.0 / (1.0 + np.exp(-0.8 * (max_abs_z - self.z_threshold))))
        is_anomaly = len(affected_signals) > 0 or (norm_score >= 0.5)

        return AnomalyReport(
            timestamp=t,
            anomaly_score=norm_score,
            is_anomaly=is_anomaly,
            affected_signals=affected_signals,
            detector_name=self.name,
            details={"channel_z_scores": scores_by_channel, "max_z": max_abs_z}
        )

    def detect_batch(self, df: pd.DataFrame) -> List[AnomalyReport]:
        if not self.fitted:
            self.fit(df.iloc[:max(30, int(len(df) * 0.2))])

        reports = []
        mahal_dists = self.feature_extractor.compute_mahalanobis_distance(df)
        z_df = self.feature_extractor.compute_z_scores(df)
        avail_channels = [c for c in self.channels if c in df.columns]

        for i in range(len(df)):
            t = float(df.iloc[i]["timestamp"])
            d_m = float(mahal_dists[i])
            
            affected = []
            z_scores = {}
            for c in avail_channels:
                z_col = f"{c}_rolling_z"
                if z_col in z_df.columns:
                    z_val = abs(float(z_df.iloc[i][z_col]))
                    z_scores[c] = z_val
                    if z_val > self.z_threshold:
                        affected.append(c)

            # Combined normalized score
            mahal_ratio = d_m / self.mahalanobis_threshold
            max_z_ratio = (max(z_scores.values()) / self.z_threshold) if z_scores else 0.0
            combined_ratio = max(mahal_ratio, max_z_ratio)
            
            norm_score = float(1.0 / (1.0 + np.exp(-1.5 * (combined_ratio - 1.0))))
            is_anom = (len(affected) > 0) or (d_m > self.mahalanobis_threshold) or (norm_score >= 0.5)

            reports.append(AnomalyReport(
                timestamp=t,
                anomaly_score=min(1.0, max(0.0, norm_score)),
                is_anomaly=is_anom,
                affected_signals=affected,
                detector_name=self.name,
                details={"mahalanobis_dist": d_m, "channel_z_scores": z_scores}
            ))

        return reports


class IsolationForestDetector(BaseAnomalyDetector):
    """Machine Learning baseline: Isolation Forest with feature attribution."""

    def __init__(
        self,
        channels: Optional[List[str]] = None,
        contamination: float = 0.05,
        n_estimators: int = 100,
        random_state: int = 42
    ):
        super().__init__(name="IsolationForestDetector")
        self.channels = channels or ["voltage_v", "current_a", "temperature_c", "power_w", "dv_dt", "dt_dt"]
        self.contamination = contamination
        self.n_estimators = n_estimators
        self.random_state = random_state
        self.model = IsolationForest(
            contamination=self.contamination,
            n_estimators=self.n_estimators,
            random_state=self.random_state
        )
        self.scaler = StandardScaler()
        self.feature_extractor = AnomalyFeatureExtractor(channels=self.channels)
        self.fitted = False

    def fit(self, df_nominal: pd.DataFrame) -> IsolationForestDetector:
        X, avail = self.feature_extractor.extract_matrix(df_nominal)
        self.feature_extractor.fit_baseline(df_nominal)
        X_scaled = self.scaler.fit_transform(X)
        self.model.fit(X_scaled)
        self.fitted = True
        return self

    def detect_frame(self, row: pd.Series, history_window: Optional[pd.DataFrame] = None) -> AnomalyReport:
        df_single = pd.DataFrame([row])
        reports = self.detect_batch(df_single)
        return reports[0]

    def detect_batch(self, df: pd.DataFrame) -> List[AnomalyReport]:
        if not self.fitted:
            self.fit(df.iloc[:max(30, int(len(df) * 0.2))])

        X, avail = self.feature_extractor.extract_matrix(df)
        X_scaled = self.scaler.transform(X)
        
        # decision_function gives negative score for outliers, positive for inliers
        raw_scores = self.model.decision_function(X_scaled)
        preds = self.model.predict(X_scaled)  # -1 = anomaly, 1 = nominal

        # Normalize score into [0.0, 1.0] where higher = more anomalous
        # decision_function typically spans [-0.5, 0.5]
        norm_scores = 1.0 / (1.0 + np.exp(6.0 * raw_scores))

        reports = []
        for i in range(len(df)):
            t = float(df.iloc[i]["timestamp"])
            is_anom = bool(preds[i] == -1)
            score = float(norm_scores[i])

            # Signal attribution via single-feature standardized deviation
            affected = []
            if is_anom:
                for j, col in enumerate(avail):
                    if abs(X_scaled[i, j]) > 2.5:
                        affected.append(col)
                if not affected:
                    # Fallback to feature with maximum absolute standardized deviation
                    max_idx = int(np.argmax(np.abs(X_scaled[i])))
                    affected.append(avail[max_idx])

            reports.append(AnomalyReport(
                timestamp=t,
                anomaly_score=min(1.0, max(0.0, score)),
                is_anomaly=is_anom,
                affected_signals=affected,
                detector_name=self.name,
                details={"raw_decision_score": float(raw_scores[i])}
            ))

        return reports


class OneClassSVMDetector(BaseAnomalyDetector):
    """Machine Learning baseline: One-Class Support Vector Machine."""

    def __init__(
        self,
        channels: Optional[List[str]] = None,
        nu: float = 0.05,
        kernel: str = "rbf",
        gamma: str = "scale"
    ):
        super().__init__(name="OneClassSVMDetector")
        self.channels = channels or ["voltage_v", "current_a", "temperature_c", "power_w"]
        self.nu = nu
        self.kernel = kernel
        self.gamma = gamma
        self.model = OneClassSVM(nu=self.nu, kernel=self.kernel, gamma=self.gamma)
        self.scaler = StandardScaler()
        self.feature_extractor = AnomalyFeatureExtractor(channels=self.channels)
        self.fitted = False

    def fit(self, df_nominal: pd.DataFrame) -> OneClassSVMDetector:
        X, _ = self.feature_extractor.extract_matrix(df_nominal)
        self.feature_extractor.fit_baseline(df_nominal)
        X_scaled = self.scaler.fit_transform(X)
        self.model.fit(X_scaled)
        self.fitted = True
        return self

    def detect_frame(self, row: pd.Series, history_window: Optional[pd.DataFrame] = None) -> AnomalyReport:
        df_single = pd.DataFrame([row])
        return self.detect_batch(df_single)[0]

    def detect_batch(self, df: pd.DataFrame) -> List[AnomalyReport]:
        if not self.fitted:
            self.fit(df.iloc[:max(30, int(len(df) * 0.2))])

        X, avail = self.feature_extractor.extract_matrix(df)
        X_scaled = self.scaler.transform(X)
        
        raw_scores = self.model.decision_function(X_scaled)
        preds = self.model.predict(X_scaled)
        norm_scores = 1.0 / (1.0 + np.exp(4.0 * raw_scores))

        reports = []
        for i in range(len(df)):
            t = float(df.iloc[i]["timestamp"])
            is_anom = bool(preds[i] == -1)
            score = float(norm_scores[i])

            affected = []
            if is_anom:
                for j, col in enumerate(avail):
                    if abs(X_scaled[i, j]) > 2.5:
                        affected.append(col)
                if not affected:
                    max_idx = int(np.argmax(np.abs(X_scaled[i])))
                    affected.append(avail[max_idx])

            reports.append(AnomalyReport(
                timestamp=t,
                anomaly_score=min(1.0, max(0.0, score)),
                is_anomaly=is_anom,
                affected_signals=affected,
                detector_name=self.name,
                details={"svm_decision_distance": float(raw_scores[i])}
            ))

        return reports


class CompositeAnomalyDetector(BaseAnomalyDetector):
    """Ensemble detector aggregating statistical and ML models via weighted score fusion."""

    def __init__(self, detectors: Optional[List[BaseAnomalyDetector]] = None, weights: Optional[List[float]] = None):
        super().__init__(name="CompositeEnsembleDetector")
        self.detectors = detectors or [StatisticalDetector(), IsolationForestDetector()]
        self.weights = weights or [0.5, 0.5]
        if len(self.detectors) != len(self.weights):
            raise ValueError("Detectors and weights must have identical length")
        total_w = sum(self.weights)
        self.weights = [w / total_w for w in self.weights]

    def fit(self, df_nominal: pd.DataFrame) -> CompositeAnomalyDetector:
        for d in self.detectors:
            d.fit(df_nominal)
        return self

    def detect_frame(self, row: pd.Series, history_window: Optional[pd.DataFrame] = None) -> AnomalyReport:
        sub_reports = [d.detect_frame(row, history_window) for d in self.detectors]
        fused_score = sum(r.anomaly_score * w for r, w in zip(sub_reports, self.weights))
        is_anom = fused_score >= 0.5 or any(r.is_anomaly for r in sub_reports)

        affected = sorted(list(set(sig for r in sub_reports for sig in r.affected_signals)))
        return AnomalyReport(
            timestamp=float(row.get("timestamp", 0.0)),
            anomaly_score=float(fused_score),
            is_anomaly=is_anom,
            affected_signals=affected,
            detector_name=self.name,
            details={"sub_detector_scores": {r.detector_name: r.anomaly_score for r in sub_reports}}
        )

    def detect_batch(self, df: pd.DataFrame) -> List[AnomalyReport]:
        all_batch_reports = [d.detect_batch(df) for d in self.detectors]
        num_samples = len(df)
        fused_reports = []

        for i in range(num_samples):
            sub_reports = [all_batch_reports[k][i] for k in range(len(self.detectors))]
            fused_score = sum(r.anomaly_score * w for r, w in zip(sub_reports, self.weights))
            is_anom = fused_score >= 0.5 or (sum(1 for r in sub_reports if r.is_anomaly) >= (len(self.detectors) // 2 + 1))
            affected = sorted(list(set(sig for r in sub_reports for sig in r.affected_signals)))

            fused_reports.append(AnomalyReport(
                timestamp=sub_reports[0].timestamp,
                anomaly_score=float(fused_score),
                is_anomaly=is_anom,
                affected_signals=affected,
                detector_name=self.name,
                details={"sub_detector_scores": {r.detector_name: r.anomaly_score for r in sub_reports}}
            ))

        return fused_reports
