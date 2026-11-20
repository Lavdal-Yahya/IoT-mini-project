"""Physical features calculated identically for every bearing class."""

from __future__ import annotations

from collections.abc import Mapping

import numpy as np
import pandas as pd
from scipy.stats import kurtosis

from .signals import (
    _vector,
    bearing_frequencies,
    causal_bandpass,
    closed_window_envelope,
    prepare_signal_with_metadata,
    spectrum,
)

BASE_FEATURES = ("rms", "kurtosis", "crest_factor")
HARMONICS = (1, 2, 3)
FULL_FEATURES = BASE_FEATURES + (
    "spectrum_centroid_hz",
    "spectrum_entropy",
    "envelope_centroid_hz",
    "envelope_entropy",
) + tuple(
    f"envelope_{kind}_h{harmonic}_energy_ratio"
    for kind in ("bpfo", "bpfi") for harmonic in HARMONICS
)


def temporal_features(x: np.ndarray) -> dict[str, float]:
    """RMS, unbiased Pearson kurtosis and crest factor after local centering."""
    values = _vector(x)
    if values.size < 4:
        raise ValueError("at least four samples are needed for unbiased kurtosis")
    centered = values - values.mean()
    rms = float(np.sqrt(np.mean(centered**2)))
    if not np.isfinite(rms) or rms <= np.finfo(float).eps * max(1.0, float(np.max(np.abs(values)))):
        raise ValueError("zero or numerically degenerate window variance")
    pearson = float(kurtosis(centered, fisher=False, bias=False))
    if not np.isfinite(pearson):
        raise ValueError("kurtosis is not finite")
    return {
        "rms": rms,
        "kurtosis": pearson,
        "crest_factor": float(np.max(np.abs(centered)) / rms),
    }


def _spectral_shape(frequency: np.ndarray, amplitude: np.ndarray) -> tuple[float, float]:
    power = np.square(amplitude[1:])
    total = float(power.sum())
    if not np.isfinite(total) or total <= 0:
        raise ValueError("zero spectral energy")
    probabilities = power / total
    positive = probabilities > 0
    centroid = float(np.dot(frequency[1:], probabilities))
    # Dividing by log(number of bins) puts entropy in [0, 1].
    entropy = float(-np.sum(probabilities[positive] * np.log(probabilities[positive])) / np.log(power.size))
    return centroid, entropy


def _band_energy_ratio(
    frequency: np.ndarray, amplitude: np.ndarray, center_hz: float, tolerance_hz: float
) -> float:
    power = np.square(amplitude)
    denominator = float(power[1:].sum())
    if denominator <= 0:
        raise ValueError("zero envelope spectral energy")
    selected = (frequency > 0) & (np.abs(frequency - center_hz) <= tolerance_hz)
    return float(power[selected].sum() / denominator)


def _get(row: Mapping | pd.Series, key: str):
    value = row[key]
    if pd.isna(value):
        raise ValueError(f"missing {key}")
    return value


def extract_recording(x: np.ndarray, row: Mapping | pd.Series, config: Mapping) -> pd.DataFrame:
    """Extract fixed features and native-sample provenance from one recording.

    The input is one raw channel, never a concatenation of recordings. Feature
    candidates depend only on the fixed configuration and the recorded rpm.
    """
    recording_id = str(_get(row, "recording_id"))
    group_id = str(_get(row, "group_id"))
    fs_native = float(_get(row, "fs_native_hz"))
    rpm = float(_get(row, "rpm"))
    fs = float(config.get("fs_analysis_hz", 12000))
    window_seconds = float(config.get("window_seconds", 1.0))
    hop_seconds = float(config.get("hop_seconds", 1.0))
    if not np.isclose(window_seconds, 1.0) or not np.isclose(hop_seconds, 1.0):
        raise ValueError("this fixed protocol requires 1 s nonoverlapping windows")
    window_size = int(round(fs * window_seconds))
    hop_size = int(round(fs * hop_seconds))
    if not np.isclose(window_size, fs * window_seconds) or window_size < 4:
        raise ValueError("window length must contain an integral number of samples")
    if tuple(config.get("harmonics", HARMONICS)) != HARMONICS:
        raise ValueError("feature schema requires harmonics 1, 2 and 3")
    band = tuple(config.get("envelope_band_hz", (2000, 5000)))
    order = int(config.get("filter_order", 4))
    edge_seconds = float(config.get("envelope_edge_seconds", 0.05))
    edge_samples = int(round(edge_seconds * fs))
    if edge_seconds < 0 or 2 * edge_samples >= window_size:
        raise ValueError("envelope edge trim must leave a nonempty window")
    tolerance = float(config.get("frequency_tolerance_hz", 3.0))
    if not np.isfinite(tolerance) or tolerance <= 0:
        raise ValueError("frequency tolerance must be positive")
    values, preparation = prepare_signal_with_metadata(
        x,
        fs_native,
        fs,
        warmup_seconds=float(config.get("warmup_seconds", 0.1)),
        fir_taps=int(config.get("fir_taps", 161)),
    )
    filtered = causal_bandpass(values, fs, band, order)
    # The band-pass starts with zero state at this recording boundary. Remove
    # its startup from both paths so the baseline and enriched sets align.
    bandpass_discard = int(np.ceil(float(config.get("warmup_seconds", 0.1)) * fs))
    if bandpass_discard >= values.size:
        raise ValueError("recording is shorter than the band-pass startup trim")
    values = values[bandpass_discard:]
    filtered = filtered[bandpass_discard:]
    bearing = bearing_frequencies(rpm)
    records = []
    factor = preparation["decimation_factor"]
    origin_analysis = preparation["discarded_analysis_samples"] + bandpass_discard
    origin_native = origin_analysis * factor
    for start in range(0, values.size - window_size + 1, hop_size):
        stop = start + window_size
        native_start = origin_native + start * factor
        # stop is exclusive in native-sample coordinates. The final prepared
        # sample corresponds to native_start + (window_size - 1)*factor.
        native_stop = origin_native + (stop - 1) * factor + 1
        raw_window = values[start:stop]
        envelope = closed_window_envelope(filtered[start:stop], edge_samples)
        raw_frequency, raw_amplitude = spectrum(raw_window, fs)
        env_frequency, env_amplitude = spectrum(envelope, fs)
        raw_centroid, raw_entropy = _spectral_shape(raw_frequency, raw_amplitude)
        env_centroid, env_entropy = _spectral_shape(env_frequency, env_amplitude)
        result = {
            "recording_id": recording_id,
            "group_id": group_id,
            "window_id": f"{recording_id}:{native_start}:{native_stop}",
            "start_sample": origin_analysis + start,
            "stop_sample": origin_analysis + stop,
            "native_start_sample": native_start,
            "native_stop_sample": native_stop,
            "fs_analysis_hz": fs,
            "available_at_s": max((origin_analysis + stop) / fs, native_stop / fs_native),
            "class_label": _get(row, "class_label"),
            "load_hp": _get(row, "load_hp"),
            "split_role": _get(row, "split_role"),
            "fold": row.get("fold", pd.NA),
            **temporal_features(raw_window),
            "spectrum_centroid_hz": raw_centroid,
            "spectrum_entropy": raw_entropy,
            "envelope_centroid_hz": env_centroid,
            "envelope_entropy": env_entropy,
        }
        for kind in ("bpfo", "bpfi"):
            for harmonic in HARMONICS:
                result[f"envelope_{kind}_h{harmonic}_energy_ratio"] = _band_energy_ratio(
                    env_frequency,
                    env_amplitude,
                    harmonic * bearing[f"{kind}_hz"],
                    tolerance,
                )
        records.append(result)
    columns = [
        "recording_id", "group_id", "window_id", "start_sample", "stop_sample",
        "native_start_sample", "native_stop_sample",
        "fs_analysis_hz", "available_at_s", "class_label", "load_hp", "split_role", "fold",
        *FULL_FEATURES,
    ]
    table = pd.DataFrame.from_records(records, columns=columns)
    table.attrs["preparation"] = {
        **preparation,
        "bandpass_hz": band,
        "bandpass_order": order,
        "bandpass_discarded_analysis_samples": bandpass_discard,
        "total_discarded_analysis_samples": origin_analysis,
        "total_discarded_native_samples": origin_native,
        "envelope_edge_samples_each_side": edge_samples,
        "envelope_method": "closed-window Hilbert magnitude",
        "window_samples": window_size,
        "hop_samples": hop_size,
        "discarded_terminal_analysis_samples": int((values.size - window_size) % hop_size) if records else int(values.size),
    }
    return table
