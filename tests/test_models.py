import pandas as pd
import pytest

from bearing_diagnosis.models import final_test, run_development


CLASSES = ["healthy", "inner_race", "outer_race", "ball"]
FEATURE_SETS = {"base": ["rms", "kurtosis", "crest_factor"], "full": ["rms", "kurtosis", "crest_factor", "spectral_energy"]}
CONFIG = {"classes": CLASSES, "random_state": 313, "model_grid": {"max_depth": [3], "min_samples_leaf": [1]}, "n_estimators": 4, "n_jobs": 1}


def synthetic_features(role="development", load=0):
    rows = []
    for fold in range(3):
        for class_index, label in enumerate(CLASSES):
            recording = f"{role}-{fold}-{label}"
            for window in range(2):
                rows.append({"recording_id": recording, "group_id": recording, "window_id": f"{recording}-{window}", "class_label": label, "load_hp": load, "split_role": role, "fold": fold, "rms": class_index + window * 0.01, "kurtosis": class_index * 2.0, "crest_factor": class_index + 2.0, "spectral_energy": class_index * 3.0})
    return pd.DataFrame(rows)


def test_development_four_experiments_and_final_prediction_only(tmp_path):
    dev = synthetic_features()
    result = run_development(dev, CONFIG, tmp_path / "development", FEATURE_SETS)
    assert set(result["selected"]) == {"E1", "E2", "E3", "E4"}
    assert len(result["oof_predictions"]) == 4 * len(dev)
    assert set(result["oof_predictions"].window_id) == set(dev.window_id)
    assert (tmp_path / "development" / "grid_scores.csv").exists()
    assert all(fold["n_train_groups"] == 8 and fold["n_valid_groups"] == 4 for item in result["selected"].values() for fold in item["fold_scores"])
    test = synthetic_features("final_test", 3)
    predicted = final_test(dev, test, result["selected"], CONFIG, tmp_path / "final", FEATURE_SETS)
    assert len(predicted) == 4 * len(test)
    assert (tmp_path / "final" / "final_predictions.csv").exists()


def test_group_leakage_rejected(tmp_path):
    frame = synthetic_features()
    frame.loc[0, "fold"] = 1
    with pytest.raises(ValueError, match="crosses folds"):
        run_development(frame, CONFIG, tmp_path, FEATURE_SETS)


def test_metadata_cannot_be_feature(tmp_path):
    feature_sets = {"base": FEATURE_SETS["base"], "full": FEATURE_SETS["full"] + ["load_hp"]}
    with pytest.raises(ValueError, match="metadata"):
        run_development(synthetic_features(), CONFIG, tmp_path, feature_sets)


def test_exact_score_tie_prefers_larger_leaf_and_e1(tmp_path):
    frame = synthetic_features()
    frame[FEATURE_SETS["full"]] = 1.0
    config = {**CONFIG, "model_grid": {"max_depth": [3, 6, None], "min_samples_leaf": [1, 5]}}
    result = run_development(frame, config, tmp_path, FEATURE_SETS)
    assert result["winner"] == "E1"
    assert all(item["params"] == {"max_depth": 3, "min_samples_leaf": 5} for item in result["selected"].values())
