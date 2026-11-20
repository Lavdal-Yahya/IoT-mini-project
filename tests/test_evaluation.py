import pandas as pd
import pytest

from bearing_diagnosis.evaluation import bootstrap_model_comparison, evaluate_predictions


def test_record_weights_and_probability_aggregation():
    # Recording a has three windows; recording b has one. Raw accuracy is
    # 3/4, equal-recording-weight accuracy is 1/2.
    predictions = pd.DataFrame(
        {
            "recording_id": ["a", "a", "a", "b"],
            "class_label": ["healthy", "healthy", "healthy", "ball"],
            "predicted_label": ["healthy", "healthy", "healthy", "healthy"],
            "proba_healthy": [0.8, 0.8, 0.8, 0.4],
            "proba_ball": [0.2, 0.2, 0.2, 0.6],
        }
    )
    result = evaluate_predictions(predictions, ["healthy", "ball"])
    assert result["raw_window"]["accuracy"] == 0.75
    assert result["weighted_window"]["accuracy"] == 0.5
    assert result["weighted_window"]["confusion"] == [[1.0, 0.0], [1.0, 0.0]]
    assert result["record"]["accuracy"] == 1.0
    assert result["per_record"][1]["predicted_label"] == "ball"


def test_bootstrap_paired_and_single_recording_limit():
    rows = []
    for experiment, labels in [("E1", ["healthy", "healthy", "healthy"]), ("E2", ["healthy", "ball", "ball"])]:
        for index, (recording, truth, prediction) in enumerate(zip(["h", "b1", "b2"], ["healthy", "ball", "ball"], labels)):
            rows.append({"experiment": experiment, "window_id": index, "recording_id": recording, "class_label": truth, "predicted_label": prediction})
    result = bootstrap_model_comparison(pd.DataFrame(rows), ["healthy", "ball"], n_bootstrap=20)
    assert result["single_recording_classes"] == ["healthy"]
    assert result["comparisons"]["E2_minus_E1"]["point_difference"] == 0.5
    assert result["comparisons"]["E2_minus_E1"]["ci95"] == [0.5, 0.5]


def test_bootstrap_rejects_nonpaired_windows():
    rows = pd.DataFrame({"experiment": ["E1", "E2"], "window_id": [1, 2], "recording_id": ["a", "a"], "class_label": ["healthy", "healthy"], "predicted_label": ["healthy", "healthy"]})
    with pytest.raises(ValueError, match="same windows"):
        bootstrap_model_comparison(rows, ["healthy"], n_bootstrap=2)
