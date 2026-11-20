"""Synthetic checks of the frozen protocol and final-access boundary."""

import json
import shutil

import pandas as pd
import pytest

from bearing_diagnosis import cli


def protocol_files(tmp_path, monkeypatch):
    root = tmp_path
    destination = root / "outputs/main"
    destination.mkdir(parents=True)
    for name, content in {
        "src/bearing_diagnosis/scientific.py": "VALUE = 1\n",
        "configs/experiment.json": json.dumps({"classes": ["healthy", "ball"],
            "development_loads_hp": [0, 1, 2], "transfer_load_hp": 3,
            "n_splits": 3, "sensor_location": "DE", "fault_sizes_in": [0.007, 0.014, 0.021]}),
        "data/manifest.csv": "recording_id,group_id\na,a\n",
        "data/splits/recordings.csv": "recording_id,fold\na,0\n",
        "requirements.lock.txt": "numpy==1.0\n",
    }.items():
        path = root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content)
    (destination / "features_development.csv").write_text("window_id,class_label\na,healthy\n")
    (destination / "selection.json").write_text(json.dumps({"selected": {"E1": {"params": {"max_depth": 3}}}}))
    monkeypatch.setattr(cli, "environment", lambda: {"python": "synthetic", "packages": {}})
    cli.freeze(root, destination)
    return root, destination


@pytest.mark.parametrize(
    "relative_path",
    ["configs/experiment.json", "src/bearing_diagnosis/scientific.py", "outputs/main/features_development.csv", "outputs/main/selection.json"],
)
def test_changed_frozen_input_rejected_before_final_access(tmp_path, monkeypatch, relative_path):
    root, destination = protocol_files(tmp_path, monkeypatch)
    path = root / relative_path
    path.write_text(path.read_text() + "changed\n")
    monkeypatch.setattr(cli, "extract", lambda *args: pytest.fail("final features were accessed"))
    with pytest.raises(RuntimeError, match="diffèrent du gel"):
        cli.evaluate(root, destination)
    assert not (destination / "test_consulted.json").exists()


def test_access_marker_precedes_final_extraction_and_blocks_second_access(tmp_path, monkeypatch):
    root, destination = protocol_files(tmp_path, monkeypatch)

    def inspect_marker(*args):
        marker = json.loads((destination / "test_consulted.json").read_text())
        assert marker["state"] == "access_started"
        raise LookupError("synthetic extraction stopped")

    monkeypatch.setattr(cli, "extract", inspect_marker)
    with pytest.raises(LookupError, match="synthetic extraction stopped"):
        cli.evaluate(root, destination)
    assert json.loads((destination / "test_consulted.json").read_text())["state"] == "access_started"
    with pytest.raises(RuntimeError, match="déjà consulté"):
        cli.evaluate(root, destination)


def test_final_uses_frozen_selection_without_score_based_choice(tmp_path, monkeypatch):
    root, destination = protocol_files(tmp_path, monkeypatch)
    original_selection = (destination / "selection.json").read_bytes()
    order = []

    def synthetic_extract(*args):
        assert (destination / "test_consulted.json").exists()
        order.append("extract")
        return pd.DataFrame({"window_id": ["final-1"], "class_label": ["ball"]})

    def synthetic_final(dev, test, selection, config, output_dir, feature_sets):
        assert selection == json.loads(original_selection)
        assert len(dev) == 1 and len(test) == 1
        order.append("predict")
        predictions = pd.DataFrame({"experiment": ["E1"], "window_id": ["final-1"], "class_label": ["ball"], "predicted_label": ["healthy"]})
        predictions.to_csv(output_dir / "final_predictions.csv", index=False)
        return predictions

    def synthetic_scores(*args):
        assert order == ["extract", "predict"]
        order.append("score")
        return {}

    monkeypatch.setattr(cli, "extract", synthetic_extract)
    monkeypatch.setattr(cli, "final_test", synthetic_final)
    monkeypatch.setattr(cli, "scores", synthetic_scores)
    cli.evaluate(root, destination)
    assert order == ["extract", "predict", "score"]
    assert (destination / "selection.json").read_bytes() == original_selection
    assert json.loads((destination / "test_consulted.json").read_text())["state"] == "complete"


def test_replay_mismatch_keeps_original_predictions_and_scores(tmp_path, monkeypatch):
    root, destination = protocol_files(tmp_path, monkeypatch)
    original = pd.DataFrame({"experiment": ["E1"], "window_id": ["final-1"], "class_label": ["ball"], "predicted_label": ["ball"]})
    original.to_csv(destination / "final_predictions.csv", index=False)
    original_bytes = (destination / "final_predictions.csv").read_bytes()
    cli.write_json(destination / "test_consulted.json", {
        "freeze_sha256": cli.sha256(destination / "freeze.json"), "state": "complete",
        "predictions_sha256": cli.sha256(destination / "final_predictions.csv"),
    })
    marker_bytes = (destination / "test_consulted.json").read_bytes()
    monkeypatch.setattr(cli, "extract", lambda *args: pd.DataFrame({"window_id": ["final-1"], "class_label": ["ball"]}))

    def different_prediction(dev, test, selection, config, output_dir, feature_sets):
        assert output_dir == root / "outputs/replay_evaluation"
        changed = original.assign(predicted_label="healthy")
        changed.to_csv(output_dir / "final_predictions.csv", index=False)
        return changed

    monkeypatch.setattr(cli, "final_test", different_prediction)
    monkeypatch.setattr(cli, "scores", lambda *args: pytest.fail("scores must wait for replay comparison"))
    with pytest.raises(AssertionError):
        cli.evaluate(root, destination, replay=True)
    assert (destination / "final_predictions.csv").read_bytes() == original_bytes
    assert (destination / "test_consulted.json").read_bytes() == marker_bytes


def test_reproduction_marks_access_before_final_extraction(tmp_path, monkeypatch):
    root, destination = protocol_files(tmp_path, monkeypatch)
    monkeypatch.setattr(cli, "acquire_and_audit", lambda *args: pd.DataFrame())
    monkeypatch.setattr(cli, "build_splits", lambda *args: None)
    original = pd.read_csv(destination / "features_development.csv")

    def synthetic_extract(root_arg, output_dir, role):
        if role == "development":
            return original
        marker = json.loads((output_dir / "test_consulted.json").read_text())
        assert marker["state"] == "access_started"
        assert marker["freeze_sha256"] == cli.sha256(destination / "freeze.json")
        raise LookupError("synthetic final extraction stopped")

    monkeypatch.setattr(cli, "extract", synthetic_extract)
    with pytest.raises(LookupError, match="synthetic final extraction stopped"):
        cli.reproduce(root, destination)


def test_cold_checkout_reproduction_restores_ledger_without_grid_search(tmp_path, monkeypatch):
    root, destination = protocol_files(tmp_path, monkeypatch)
    reference = pd.DataFrame({"experiment": ["E1"], "window_id": ["final-1"], "class_label": ["ball"], "predicted_label": ["ball"]})
    reference.to_csv(destination / "final_predictions.csv", index=False)
    cli.write_json(destination / "test_consulted.json", {
        "freeze_sha256": cli.sha256(destination / "freeze.json"), "state": "complete",
        "predictions_sha256": cli.sha256(destination / "final_predictions.csv"),
    })
    released_dev = (destination / "features_development.csv").read_bytes()
    released_manifest = (root / "data/manifest.csv").read_bytes()
    released_splits = (root / "data/splits/recordings.csv").read_bytes()
    release = root / "results"
    release.mkdir()
    for name in ("freeze.json", "selection.json", "test_consulted.json", "final_predictions.csv"):
        shutil.copy2(destination / name, release / name)
    shutil.rmtree(destination)
    (root / "data/manifest.csv").unlink()
    (root / "data/splits/recordings.csv").unlink()

    def synthetic_audit(root_arg):
        (root_arg / "data/manifest.csv").write_bytes(released_manifest)
        return pd.DataFrame()

    def synthetic_splits(manifest, root_arg):
        (root_arg / "data/splits/recordings.csv").write_bytes(released_splits)

    def synthetic_extract(root_arg, output_dir, role):
        output_dir.mkdir(parents=True, exist_ok=True)
        if role == "development":
            (output_dir / "features_development.csv").write_bytes(released_dev)
            return pd.read_csv(output_dir / "features_development.csv")
        marker = json.loads((output_dir / "test_consulted.json").read_text())
        assert marker["state"] == "access_started"
        assert cli.sha256(destination / "features_development.csv") == json.loads((destination / "freeze.json").read_text())["development"]["features_development.csv"]
        return pd.DataFrame({"window_id": ["final-1"], "class_label": ["ball"]})

    def synthetic_final(dev, test, selection, config, output_dir, feature_sets):
        assert selection == json.loads((release / "selection.json").read_text())
        reference.to_csv(output_dir / "final_predictions.csv", index=False)
        return reference

    monkeypatch.setattr(cli, "acquire_and_audit", synthetic_audit)
    monkeypatch.setattr(cli, "build_splits", synthetic_splits)
    monkeypatch.setattr(cli, "extract", synthetic_extract)
    monkeypatch.setattr(cli, "final_test", synthetic_final)
    monkeypatch.setattr(cli, "run_development", lambda *args: pytest.fail("grid search is forbidden during reproduction"))
    cli.reproduce(root, destination)
    assert (destination / "final_predictions.csv").read_bytes() == (release / "final_predictions.csv").read_bytes()
    assert json.loads((root / "outputs/reproduction/verification.json").read_text())["status"] == "identical"
