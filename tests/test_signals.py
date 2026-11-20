import numpy as np
import pytest

from bearing_diagnosis.signals import (
    bearing_frequencies,
    causal_bandpass,
    closed_window_envelope,
    prepare_signal_with_metadata,
    spectrum,
)


def test_spectrum_hann_coherent_gain_and_bin_spacing():
    fs = 12000
    t = np.arange(fs) / fs
    frequency, amplitude = spectrum(2.5 * np.cos(2 * np.pi * 317 * t) + 7, fs)
    assert frequency[1] - frequency[0] == 1
    assert frequency[np.argmax(amplitude)] == 317
    assert amplitude[317] == pytest.approx(2.5, rel=1e-10)


def test_bearing_frequencies_de_factors():
    values = bearing_frequencies(1800)
    assert values["rotation_hz"] == 30
    assert values["bpfo_hz"] == pytest.approx(107.544)
    assert values["bpfi_hz"] == pytest.approx(162.456)
    with pytest.raises(ValueError):
        bearing_frequencies(0)


def test_causal_decimation_attenuates_alias_and_reports_delay():
    fs_native = 48000
    t = np.arange(48000) / fs_native
    x = np.sin(2 * np.pi * 1000 * t) + np.sin(2 * np.pi * 8000 * t)
    prepared, info = prepare_signal_with_metadata(x, fs_native)
    assert info["decimation_factor"] == 4
    assert info["fir_group_delay_native_samples"] == 80
    assert info["discarded_native_samples"] == 4800
    assert prepared.size == 10800
    frequency, amplitude = spectrum(prepared[:6000], 12000)
    assert amplitude[np.argmin(abs(frequency - 1000))] > 0.9
    # An unfiltered 8 kHz component would fold to 4 kHz.
    assert amplitude[np.argmin(abs(frequency - 4000))] < 0.01


def test_closed_window_envelope_recovers_known_modulation():
    fs = 12000
    t = np.arange(24000) / fs
    carrier = (1 + 0.4 * np.cos(2 * np.pi * 100 * t)) * np.cos(2 * np.pi * 3000 * t)
    filtered = causal_bandpass(carrier, fs)
    envelope = closed_window_envelope(filtered[1200:13200], 600)
    frequency, amplitude = spectrum(envelope, fs)
    assert frequency[np.argmax(amplitude)] == pytest.approx(100, abs=0.6)
    assert amplitude.max() > 0.2


def test_invalid_frequency_band_and_input_rejected():
    with pytest.raises(ValueError):
        causal_bandpass(np.ones(100), 12000, (2000, 6500))
    with pytest.raises(ValueError):
        spectrum(np.array([1.0, np.nan]), 12000)


def test_fixed_filter_diagnostics_quantify_response_and_decay():
    from bearing_diagnosis.signals import check_filter_diagnostics

    d = check_filter_diagnostics()
    gain = d["bandpass_gain_db_at_hz"]
    assert gain["3000"] > -0.1
    assert gain["2100"] > -3
    assert gain["4800"] > -3
    assert gain["1000"] < -25
    assert gain["5500"] < -25
    assert 0 < d["bandpass_max_group_delay_s_in_2100_4800_hz"] < 0.001
    assert d["bandpass_impulse_tail_energy_ratio_after_warmup"] < 1e-8
    assert d["fir_worst_stopband_gain_db_at_or_above_output_nyquist"] < -50
    # The FIR does attenuate part of the proposed envelope band for 48 kHz files.
    assert d["fir_gain_db_at_hz"]["5000"] < -10
    assert d["fir_12khz_taps"] == 41
    for difference_db in d["fir_12khz_minus_48khz_gain_db_at_hz"].values():
        assert abs(difference_db) < 0.1


def test_hilbert_edge_trim_reduces_known_boundary_error():
    from scipy.signal import hilbert

    fs = 12000
    t = np.arange(fs) / fs
    ideal = 1 + 0.4 * np.cos(2 * np.pi * 107.544 * t)
    carrier = ideal * np.cos(2 * np.pi * 3033.3 * t)
    untrimmed = np.abs(hilbert(carrier))
    trimmed = closed_window_envelope(carrier, 600)
    centered_ideal = ideal[600:-600] - ideal[600:-600].mean()
    assert np.max(np.abs(untrimmed - ideal)) > 0.1
    assert np.max(np.abs(trimmed - centered_ideal)) < 0.002


def test_12k_native_signal_receives_matched_fir():
    from bearing_diagnosis.signals import prepare_signal_with_metadata

    fs = 12000
    t = np.arange(2 * fs) / fs
    x = np.cos(2 * np.pi * 5000 * t)
    prepared, info = prepare_signal_with_metadata(x, fs)
    assert info["decimation_factor"] == 1
    assert info["fir_taps"] == 41
    assert info["fir_group_delay_native_samples"] == 20
    frequency, amplitude = spectrum(prepared, fs)
    measured = amplitude[np.argmin(np.abs(frequency - 5000))]
    assert 0.15 < measured < 0.2  # about -15 dB, not an unfiltered copy
