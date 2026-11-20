"""Fixed, traceable signal operations for CWRU drive-end vibration."""

from __future__ import annotations

import numpy as np
from scipy import signal


def _vector(x: np.ndarray) -> np.ndarray:
    values = np.asarray(x, dtype=np.float64)
    if values.ndim != 1 or values.size == 0 or not np.all(np.isfinite(values)):
        raise ValueError("signal must be a nonempty finite one-dimensional array")
    return values


def _rates(fs_native: float, fs_analysis: float) -> int:
    if not (np.isfinite(fs_native) and np.isfinite(fs_analysis)) or fs_native <= 0 or fs_analysis <= 0:
        raise ValueError("sampling rates must be positive and finite")
    ratio = fs_native / fs_analysis
    factor = round(ratio)
    if factor < 1 or not np.isclose(ratio, factor, rtol=0, atol=1e-9):
        raise ValueError("only integer-factor downsampling is supported")
    return factor


def prepare_signal_with_metadata(
    x: np.ndarray,
    fs_native: float,
    fs_analysis: float = 12000,
    *,
    warmup_seconds: float = 0.1,
    fir_taps: int = 161,
) -> tuple[np.ndarray, dict]:
    """Causally low-pass every signal, then decimate when needed.

    An explicit initial warmup is discarded. Output sample j (before warmup
    removal) is available after native sample
    j*factor has arrived. The FIR group delay is not compensated by looking
    into future samples. All offsets refer to the original recording.
    """
    values = _vector(x)
    factor = _rates(fs_native, fs_analysis)
    if not np.isfinite(warmup_seconds) or warmup_seconds < 0:
        raise ValueError("warmup_seconds must be nonnegative and finite")
    if fir_taps < 3 or fir_taps % 2 != 1:
        raise ValueError("fir_taps must be an odd integer of at least 3")
    # The reference 161-tap design is at 48 kHz. Scaling the tap count
    # by sample rate keeps its impulse duration approximately fixed. For the
    # CWRU rates this gives 41 taps at 12 kHz and 161 at 48 kHz.
    actual_taps = round((fir_taps - 1) * fs_native / 48000) + 1
    if actual_taps < 3 or actual_taps % 2 != 1:
        raise ValueError("scaled FIR length must be an odd integer of at least 3")
    cutoff_hz = 0.4 * fs_analysis
    taps = signal.firwin(actual_taps, cutoff_hz, fs=fs_native, window="hamming")
    prepared = signal.lfilter(taps, [1.0], values)[::factor]
    delay_native_samples = (actual_taps - 1) / 2
    discard = int(np.ceil(warmup_seconds * fs_analysis))
    if discard >= prepared.size:
        raise ValueError("recording is shorter than the preparation warmup")
    metadata = {
        "fs_native_hz": float(fs_native),
        "fs_analysis_hz": float(fs_analysis),
        "decimation_factor": factor,
        "fir_taps": actual_taps,
        "fir_reference_taps_at_48khz": fir_taps,
        "fir_cutoff_hz": cutoff_hz,
        "fir_group_delay_native_samples": delay_native_samples,
        "fir_group_delay_seconds": delay_native_samples / fs_native,
        "discarded_analysis_samples": discard,
        "discarded_native_samples": discard * factor,
        "input_samples": int(values.size),
        "output_samples": int(prepared.size - discard),
        "output_first_native_sample": discard * factor,
        "causal": True,
    }
    return prepared[discard:], metadata


def prepare_signal(
    x: np.ndarray,
    fs_native: float,
    fs_analysis: float = 12000,
    *,
    warmup_seconds: float = 0.1,
    fir_taps: int = 161,
) -> np.ndarray:
    """Return only prepared samples; use the companion for audit metadata."""
    return prepare_signal_with_metadata(
        x, fs_native, fs_analysis, warmup_seconds=warmup_seconds, fir_taps=fir_taps
    )[0]


def spectrum(x: np.ndarray, fs: float) -> tuple[np.ndarray, np.ndarray]:
    """One-sided peak amplitude spectrum using a periodic Hann window.

    Interior rFFT bins are doubled; DC and Nyquist (when present) are not.
    The coherent-gain correction is the sum of Hann weights. Bin spacing is
    fs/N, while the Hann main lobe is wider than one bin.
    """
    values = _vector(x)
    if values.size < 2 or not np.isfinite(fs) or fs <= 0:
        raise ValueError("spectrum needs at least two samples and a positive rate")
    centered = values - values.mean()
    taper = signal.windows.hann(values.size, sym=False)
    amplitudes = np.abs(np.fft.rfft(centered * taper)) / taper.sum()
    if values.size % 2 == 0:
        amplitudes[1:-1] *= 2
    else:
        amplitudes[1:] *= 2
    return np.fft.rfftfreq(values.size, d=1.0 / fs), amplitudes


def bearing_frequencies(rpm: float) -> dict[str, float]:
    """DE bearing factors from the official CWRU bearing information page."""
    if not np.isfinite(rpm) or rpm <= 0:
        raise ValueError("rpm must be positive and finite")
    rotation = float(rpm) / 60.0
    return {
        "rotation_hz": rotation,
        "bpfo_hz": 3.5848 * rotation,
        "bpfi_hz": 5.4152 * rotation,
    }


def causal_bandpass(x: np.ndarray, fs: float, band_hz: tuple[float, float] = (2000, 5000), order: int = 4) -> np.ndarray:
    """Filter a recording in forward time with SOS state reset at its start."""
    values = _vector(x)
    low, high = band_hz
    if not (np.isfinite(fs) and fs > 0 and 0 < low < high < fs / 2):
        raise ValueError("band must be inside (0, Nyquist)")
    if not isinstance(order, int) or order < 1:
        raise ValueError("order must be a positive integer")
    sos = signal.butter(order, [low, high], btype="bandpass", fs=fs, output="sos")
    return signal.sosfilt(sos, values)


def closed_window_envelope(filtered_window: np.ndarray, edge_samples: int) -> np.ndarray:
    """Hilbert magnitude on a closed window, excluding both affected edges."""
    values = _vector(filtered_window)
    if not isinstance(edge_samples, int) or edge_samples < 0 or 2 * edge_samples >= values.size:
        raise ValueError("edge_samples must leave at least one sample")
    envelope = np.abs(signal.hilbert(values))
    if edge_samples:
        envelope = envelope[edge_samples:-edge_samples]
    return envelope - envelope.mean()


def check_filter_diagnostics(config: dict | None = None) -> dict:
    """Measure fixed filter responses and startup decay without recording data.

    Values are deterministic design diagnostics, not a validation of a chosen
    resonance or diagnostic accuracy on CWRU recordings.
    """
    settings = {} if config is None else config
    fs = float(settings.get("fs_analysis_hz", 12000))
    band = tuple(settings.get("envelope_band_hz", (2000, 5000)))
    order = int(settings.get("filter_order", 4))
    warmup = float(settings.get("warmup_seconds", 0.1))
    fir_taps = int(settings.get("fir_taps", 161))
    fs_native = 4 * fs
    _rates(fs_native, fs)
    if not (0 < band[0] < band[1] < fs / 2 and warmup > 0):
        raise ValueError("invalid band or startup duration")
    if fir_taps < 3 or fir_taps % 2 != 1:
        raise ValueError("fir_taps must be an odd integer of at least 3")
    sos = signal.butter(order, band, btype="bandpass", fs=fs, output="sos")
    freq, response = signal.sosfreqz(sos, worN=65536, fs=fs)
    gain_db = 20 * np.log10(np.maximum(np.abs(response), np.finfo(float).tiny))
    sample_hz = (1000, 2100, 3000, 4800, 5500)
    sampled_gain = {str(hz): float(gain_db[np.argmin(np.abs(freq - hz))]) for hz in sample_hz}
    phase = np.unwrap(np.angle(response))
    delay_s = -np.gradient(phase, 2 * np.pi * freq)
    passband = (freq >= max(band[0] + 100, 0)) & (freq <= band[1] - 200)
    if not np.any(passband):
        raise ValueError("band too narrow for group delay diagnostic")
    warmup_samples = int(np.ceil(warmup * fs))
    impulse = np.zeros(max(2 * warmup_samples, 2048))
    impulse[0] = 1
    impulse_response = signal.sosfilt(sos, impulse)
    impulse_energy = np.square(impulse_response)
    tail_ratio = float(impulse_energy[warmup_samples:].sum() / impulse_energy.sum())
    fir = signal.firwin(fir_taps, 0.4 * fs, fs=fs_native, window="hamming")
    fir_frequency, fir_response = signal.freqz(fir, worN=65536, fs=fs_native)
    fir_gain_db = 20 * np.log10(np.maximum(np.abs(fir_response), np.finfo(float).tiny))
    fir_passband_hz = (3000, 4500, 4800, 5000)
    fir_sampled = {
        str(hz): float(fir_gain_db[np.argmin(np.abs(fir_frequency - hz))])
        for hz in fir_passband_hz
    }
    stopband = fir_frequency >= fs / 2
    native_12k_taps = round((fir_taps - 1) * fs / 48000) + 1
    if native_12k_taps < 3 or native_12k_taps % 2 != 1:
        raise ValueError("scaled 12 kHz FIR length must be odd and at least 3")
    fir_12k = signal.firwin(native_12k_taps, 0.4 * fs, fs=fs, window="hamming")
    fir_12k_frequency, fir_12k_response = signal.freqz(fir_12k, worN=65536, fs=fs)
    fir_12k_gain_db = 20 * np.log10(np.maximum(np.abs(fir_12k_response), np.finfo(float).tiny))
    fir_12k_sampled = {
        str(hz): float(fir_12k_gain_db[np.argmin(np.abs(fir_12k_frequency - hz))])
        for hz in fir_passband_hz
    }
    fir_gain_difference_db = {
        str(hz): fir_12k_sampled[str(hz)] - fir_sampled[str(hz)]
        for hz in fir_passband_hz
    }
    return {
        "analysis_rate_hz": fs,
        "bandpass_hz": list(band),
        "bandpass_order": order,
        "bandpass_gain_db_at_hz": sampled_gain,
        "bandpass_max_group_delay_s_in_2100_4800_hz": float(np.max(delay_s[passband])),
        "bandpass_impulse_tail_energy_ratio_after_warmup": tail_ratio,
        "bandpass_warmup_s": warmup,
        "fir_native_rate_hz": fs_native,
        "fir_taps": fir_taps,
        "fir_12khz_taps": native_12k_taps,
        "fir_gain_db_at_hz": fir_sampled,
        "fir_12khz_gain_db_at_hz": fir_12k_sampled,
        "fir_12khz_minus_48khz_gain_db_at_hz": fir_gain_difference_db,
        "fir_worst_stopband_gain_db_at_or_above_output_nyquist": float(np.max(fir_gain_db[stopband])),
        "fir_group_delay_s": (fir_taps - 1) / (2 * fs_native),
    }
