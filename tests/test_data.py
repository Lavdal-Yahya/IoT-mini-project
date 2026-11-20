import hashlib
from pathlib import Path

import numpy as np
import pandas as pd
import pytest
from scipy.io import savemat

from bearing_diagnosis.data import load_signal


def test_load_signal_uses_file_own_de_key_and_verifies_hashes(tmp_path: Path):
    path = tmp_path / "data/raw/99.mat"
    path.parent.mkdir(parents=True)
    signal = np.array([1.0, 2.0, 3.0])
    savemat(path, {"X098_DE_time": np.array([42.0]), "X099_DE_time": signal})
    row = {
        "recording_id": "Normal_2", "local_path": "data/raw/99.mat",
        "file_sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
        "mat_key": "X099_DE_time",
        "signal_sha256": hashlib.sha256(signal.astype("<f8").tobytes()).hexdigest(),
    }
    np.testing.assert_array_equal(load_signal(tmp_path, row), signal)
    row["file_sha256"] = "0" * 64
    with pytest.raises(ValueError, match="Empreinte"):
        load_signal(tmp_path, row)
