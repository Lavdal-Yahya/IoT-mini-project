import pandas as pd
import pytest

from bearing_diagnosis.splits import build_splits


def _manifest():
    rows = []
    for load in range(4):
        for label in ("healthy", "inner_race", "ball", "outer_race"):
            ident = f"{label}_{load}"
            rows.append({"recording_id": ident, "group_id": ident,
                         "class_label": label, "load_hp": load,
                         "inclusion_status": "included"})
    return pd.DataFrame(rows)


def test_each_fold_has_all_classes_and_final_load_is_reserved(tmp_path):
    manifest = _manifest()
    splits = build_splits(manifest, tmp_path)
    assert len(splits) == 16
    assert set(splits.loc[splits.split_role == "final_test", "fold"]) == {-1}
    for fold in range(3):
        validation = manifest.merge(splits[splits.fold == fold], on=["recording_id", "group_id"])
        training = manifest[manifest.load_hp.isin([0, 1, 2]) & ~manifest.recording_id.isin(validation.recording_id)]
        assert set(validation.class_label) == set(training.class_label) == {
            "healthy", "inner_race", "ball", "outer_race"}
        assert not (set(validation.group_id) & set(training.group_id))
        assert validation.load_hp.nunique() == 1
    assert (tmp_path / "data/splits/recordings.csv").exists()


def test_cross_load_group_rejected(tmp_path):
    manifest = _manifest()
    manifest.loc[manifest.recording_id == "ball_1", "group_id"] = "ball_0"
    with pytest.raises(ValueError, match="traverse"):
        build_splits(manifest, tmp_path)
