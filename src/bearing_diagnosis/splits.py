"""Partitions fixées sur les charges et les enregistrements, sans scores."""

import json
from pathlib import Path

import pandas as pd
from sklearn.model_selection import GroupKFold

from .data import CLASSES


def build_splits(manifest: pd.DataFrame, root: Path) -> pd.DataFrame:
    """Réserve 3 HP et forme trois plis de développement par charge entière.

    GroupKFold reçoit la charge comme supergroupe. Chaque essai conserve aussi
    son group_id physique, ce qui protège les dérivés et alias ultérieurs.
    """
    required = {"recording_id", "group_id", "class_label", "load_hp", "inclusion_status"}
    missing = required - set(manifest.columns)
    if missing:
        raise ValueError(f"Colonnes manquantes : {sorted(missing)}")
    included = manifest.loc[manifest.inclusion_status == "included"].copy()
    if included.recording_id.duplicated().any():
        raise ValueError("recording_id dupliqué")
    if included.empty or set(included.load_hp) != {0, 1, 2, 3}:
        raise ValueError("Les charges 0, 1, 2 et 3 HP doivent être présentes")
    if (included.groupby("group_id").load_hp.nunique() > 1).any():
        raise ValueError("Un même groupe traverse plusieurs charges")
    development = included[included.load_hp.isin([0, 1, 2])].reset_index(drop=True)
    final = included[included.load_hp == 3].reset_index(drop=True)
    expected = set(CLASSES)
    if set(final.class_label) != expected:
        raise ValueError("Classes incomplètes dans le test final")
    rows = []
    for fold, (train, validation) in enumerate(
        GroupKFold(n_splits=3).split(development, groups=development.load_hp)
    ):
        train_frame = development.iloc[train]
        val_frame = development.iloc[validation]
        if set(train_frame.class_label) != expected or set(val_frame.class_label) != expected:
            raise ValueError(f"Couverture de classes incomplète au pli {fold}")
        if set(train_frame.group_id) & set(val_frame.group_id):
            raise ValueError(f"Fuite de groupe au pli {fold}")
        rows.extend({"recording_id": row.recording_id, "group_id": row.group_id,
                     "split_role": "development", "fold": fold}
                    for row in val_frame.itertuples())
    rows.extend({"recording_id": row.recording_id, "group_id": row.group_id,
                 "split_role": "final_test", "fold": -1}
                for row in final.itertuples())
    splits = pd.DataFrame(rows).sort_values(["split_role", "fold", "recording_id"]).reset_index(drop=True)
    if len(splits) != len(included) or splits.recording_id.duplicated().any():
        raise ValueError("Affectation incomplète ou dupliquée")
    path = Path(root) / "data/splits"
    path.mkdir(parents=True, exist_ok=True)
    splits.to_csv(path / "recordings.csv", index=False)
    plan = {
        "method": "GroupKFold(n_splits=3)",
        "grouping_for_fold_assignment": "load_hp (whole-load supergroups)",
        "physical_record_group_column": "group_id",
        "selection_basis": "source metadata and class coverage only; no signal feature or model score",
        "development_load_hp": [0, 1, 2], "final_test_load_hp": 3,
        "fold_validation_load_hp": {
            str(fold): sorted(included.set_index("recording_id").loc[part.recording_id, "load_hp"].unique().tolist())
            for fold, part in splits[splits.split_role == "development"].groupby("fold")
        },
    }
    (path / "split_plan.json").write_text(json.dumps(plan, indent=2), encoding="utf-8")
    return splits
