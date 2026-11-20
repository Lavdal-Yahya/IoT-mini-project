import numpy as np
import pytest
from scipy.stats import kurtosis

from bearing_diagnosis.features import BASE_FEATURES, FULL_FEATURES, extract_recording, temporal_features
from bearing_diagnosis.signals import bearing_frequencies


def test_temporal_features_centering_and_unbiased_pearson():
    x = np.array([0.0, 1.0, 2.0, 4.0, 7.0, 9.0])
    result = temporal_features(x + 100)
    centered = x - x.mean()
    assert result["rms"] == pytest.approx(np.sqrt(np.mean(centered**2)))
    assert result["kurtosis"] == pytest.approx(kurtosis(x, fisher=False, bias=False))
    assert result["crest_factor"] == pytest.approx(np.max(abs(centered)) / result["rms"])
    assert tuple(result) == BASE_FEATURES


def test_temporal_features_reject_degenerate_and_nonfinite():
    for x in (np.ones(12), np.array([1.0, 2.0, np.nan, 4.0]), np.arange(3.0)):
        with pytest.raises(ValueError):
            temporal_features(x)


def test_extract_recording_provenance_and_fixed_label_independent_features():
    fs = 12000
    rpm = 1800
    bpfo = bearing_frequencies(rpm)["bpfo_hz"]
    t = np.arange(2 * fs + 3000) / fs
    x = (1 + 0.6 * np.cos(2 * np.pi * bpfo * t)) * np.cos(2 * np.pi * 3000 * t)
    row = {
        "recording_id": "recA", "group_id": "groupA", "fs_native_hz": fs,
        "rpm": rpm, "class_label": "healthy", "load_hp": 0, "split_role": "development", "fold": 1,
    }
    config = {"fs_analysis_hz": 12000, "window_seconds": 1.0, "hop_seconds": 1.0}
    table = extract_recording(x, row, config)
    assert len(table) == 2
    assert list(table["start_sample"]) == [2400, 14400]
    assert list(table["stop_sample"]) == [14400, 26400]
    assert list(table["native_start_sample"]) == [2400, 14400]
    assert list(table["available_at_s"]) == pytest.approx([14400 / fs, 26400 / fs])
    assert table["window_id"].is_unique
    assert table["envelope_bpfo_h1_energy_ratio"].min() > table["envelope_bpfi_h1_energy_ratio"].max()
    assert np.isfinite(table[list(FULL_FEATURES)].to_numpy()).all()
    assert table.attrs["preparation"]["discarded_terminal_analysis_samples"] == 600
    other = extract_recording(x, {**row, "class_label": "ball"}, config)
    np.testing.assert_allclose(table[list(FULL_FEATURES)], other[list(FULL_FEATURES)])


def test_extract_empty_table_keeps_feature_schema():
    x = np.sin(2 * np.pi * 100 * np.arange(6000) / 12000)
    row = {"recording_id": "short", "group_id": "short", "fs_native_hz": 12000,
           "rpm": 1800, "class_label": "healthy", "load_hp": 0, "split_role": "development"}
    table = extract_recording(x, row, {})
    assert table.empty
    assert all(name in table.columns for name in FULL_FEATURES)


def test_extract_48k_native_bounds_and_availability():
    fs_native = 48000
    t = np.arange(int(1.5 * fs_native)) / fs_native
    x = (1 + 0.3 * np.cos(2 * np.pi * 107.544 * t)) * np.cos(2 * np.pi * 3000 * t)
    row = {"recording_id": "native48", "group_id": "g48", "fs_native_hz": fs_native,
           "rpm": 1800, "class_label": "outer_race", "load_hp": 0,
           "split_role": "development"}
    table = extract_recording(x, row, {})
    assert len(table) == 1
    item = table.iloc[0]
    assert item["start_sample"] == 2400
    assert item["stop_sample"] == 14400
    assert item["native_start_sample"] == 9600
    assert item["native_stop_sample"] == 57597
    assert item["available_at_s"] == pytest.approx(1.2)
