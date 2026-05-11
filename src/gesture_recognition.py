"""Feature extraction for gesture recognition.

Computes 60 features (6 IMU channels × 10 statistics each), matching the
C implementation in data/gesture_recognition/main/gesture_inference_template.c
so that Python-trained models and on-device inference use identical features.
"""

from __future__ import annotations

import numpy as np

NUM_CHANNELS = 6        # ax, ay, az, gx, gy, gz
FEATURES_PER_CHANNEL = 10
NUM_FEATURES = NUM_CHANNELS * FEATURES_PER_CHANNEL  # 60


def _zero_crossings_centered(x: np.ndarray) -> float:
    """Count sign changes in the zero-mean signal, skipping exact zeros."""
    centered = x - x.mean()
    signs = np.sign(centered)
    signs_nz = signs[signs != 0]
    if len(signs_nz) < 2:
        return 0.0
    return float(np.sum(signs_nz[1:] != signs_nz[:-1]))


def extract_features(data: np.ndarray) -> np.ndarray:
    """Return a 60-element feature vector from an N×6 IMU array.

    Column order: ax (m/s²), ay, az, gx (deg/s), gy, gz.
    Feature order per channel: mean, std, min, max, range, energy,
    peak_abs, rms, zero_crossings_centered, mean_abs_diff.
    """
    features: list[float] = []
    for c in range(NUM_CHANNELS):
        x = data[:, c].astype(np.float64)
        n = len(x)
        mean = x.mean()
        energy = np.mean(x ** 2)
        std = np.sqrt(max(energy - mean ** 2, 0.0))
        min_v = x.min()
        max_v = x.max()
        features.extend([
            mean,
            std,
            min_v,
            max_v,
            max_v - min_v,                               # range
            energy,
            float(np.max(np.abs(x))),                    # peak_abs
            np.sqrt(energy),                             # rms
            _zero_crossings_centered(x),
            float(np.mean(np.abs(np.diff(x)))) if n > 1 else 0.0,  # mean_abs_diff
        ])
    return np.array(features, dtype=np.float64)
