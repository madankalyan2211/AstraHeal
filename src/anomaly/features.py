"""Feature extraction and representation for anomaly detection."""

from __future__ import annotations

from typing import List, Optional, Tuple
import numpy as np
import pandas as pd


class AnomalyFeatureExtractor:
    """Extracts multivariate anomaly features for statistical and ML models."""

    DEFAULT_CHANNELS = ["voltage_v", "current_a", "temperature_c", "power_w", "dt_dt", "dv_dt"]

    def __init__(self, channels: Optional[List[str]] = None, window_size: int = 20):
        self.channels = channels or self.DEFAULT_CHANNELS
        self.window_size = window_size
        self.mean_baseline: Optional[np.ndarray] = None
        self.std_baseline: Optional[np.ndarray] = None
        self.cov_inv: Optional[np.ndarray] = None

    def fit_baseline(self, df: pd.DataFrame) -> None:
        """Fit baseline nominal statistics (mean, std, inverse covariance) on nominal data."""
        avail_channels = [c for c in self.channels if c in df.columns]
        X = df[avail_channels].to_numpy(dtype=float)
        
        self.mean_baseline = np.nanmean(X, axis=0)
        self.std_baseline = np.nanstd(X, axis=0)
        self.std_baseline[self.std_baseline < 1e-6] = 1.0  # Avoid zero-division
        
        # Regularized covariance matrix for Mahalanobis calculation
        cov = np.cov(X, rowvar=False)
        if cov.ndim == 0 or cov.size == 1:
            cov = np.array([[cov]])
        cov += np.eye(cov.shape[0]) * 1e-4  # Regularization ridge
        self.cov_inv = np.linalg.pinv(cov)

    def extract_matrix(self, df: pd.DataFrame) -> Tuple[np.ndarray, List[str]]:
        """Extract numeric 2D array matrix for ML detector input."""
        avail_channels = [c for c in self.channels if c in df.columns]
        X = df[avail_channels].to_numpy(dtype=float)
        # Impute remaining NaNs with column medians
        col_medians = np.nanmedian(X, axis=0)
        inds = np.where(np.isnan(X))
        if len(inds[0]) > 0:
            X[inds] = np.take(col_medians, inds[1])
        return X, avail_channels

    def compute_z_scores(self, df: pd.DataFrame) -> pd.DataFrame:
        """Compute rolling and baseline z-scores for each target telemetry channel."""
        z_df = pd.DataFrame(index=df.index)
        avail_channels = [c for c in self.channels if c in df.columns]

        for col in avail_channels:
            # Rolling statistics
            rolling_mean = df[col].rolling(window=self.window_size, min_periods=3).mean()
            rolling_std = df[col].rolling(window=self.window_size, min_periods=3).std().replace(0.0, 1e-5).fillna(1.0)
            z_df[f"{col}_rolling_z"] = (df[col] - rolling_mean) / rolling_std

            # Global baseline z-score if fitted
            if self.mean_baseline is not None:
                idx = avail_channels.index(col)
                z_df[f"{col}_global_z"] = (df[col] - self.mean_baseline[idx]) / self.std_baseline[idx]

        return z_df.fillna(0.0)

    def compute_mahalanobis_distance(self, df: pd.DataFrame) -> np.ndarray:
        """Calculate multivariate Mahalanobis distance relative to baseline."""
        if self.mean_baseline is None or self.cov_inv is None:
            raise RuntimeError("AnomalyFeatureExtractor baseline must be fitted before computing Mahalanobis distance.")
        
        X, _ = self.extract_matrix(df)
        diff = X - self.mean_baseline
        # D_M = sqrt((x - mu)^T * Sigma^{-1} * (x - mu))
        dist_sq = np.sum(np.dot(diff, self.cov_inv) * diff, axis=1)
        dist_sq = np.maximum(dist_sq, 0.0)
        return np.sqrt(dist_sq)
