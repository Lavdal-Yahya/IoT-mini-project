"""Pipeline reproductible et frontière explicite du test final."""

from __future__ import annotations

import argparse
import json
import shutil
from pathlib import Path

import numpy as np
import pandas as pd

from .data import acquire_and_audit, load_signal
from .evaluation import bootstrap_model_comparison, evaluate_predictions
from .features import BASE_FEATURES, FULL_FEATURES, extract_recording
from .models import final_test, run_development
from .provenance import environment, sha256, source_fingerprints, write_json
from .splits import build_splits


def configuration(root: Path) -> dict:
    config = json.loads((root / "configs/experiment.json").read_text())
    # This cohort is fixed; a changed split declaration must not be ignored.
    expected = {"development_loads_hp": [0, 1, 2], "transfer_load_hp": 3, "n_splits": 3,
                "sensor_location": "DE", "fault_sizes_in": [0.007, 0.014, 0.021]}
    for key, value in expected.items():
        if config.get(key) != value:
            raise ValueError(f"Protocole non pris en charge : {key}={config.get(key)!r}")
    return config


def extract(root: Path, destination: Path, role: str) -> pd.DataFrame:
    config = configuration(root)
    manifest = pd.read_csv(root / "data/manifest.csv")
    splits = pd.read_csv(root / "data/splits/recordings.csv")
    records = manifest.drop(columns=["split_role", "fold"], errors="ignore").merge(
        splits, on=["recording_id", "group_id"], validate="one_to_one"
    )
    records = records.loc[records.split_role.eq(role)].sort_values("recording_id")
    tables, journal = [], []
    for _, row in records.iterrows():
        feature_row = row.copy()
        feature_row["rpm"] = row["rpm_used"]
        table = extract_recording(load_signal(root, row), feature_row, config)
        if table.empty:
            raise ValueError(f"Aucune fenêtre : {row.recording_id}")
        journal.append({"recording_id": row.recording_id, "n_windows": len(table),
                        "rpm_used": float(row.rpm_used), "rpm_source": row.rpm_source,
                        "rpm_is_approximate": bool(row.rpm_is_approximate), **table.attrs["preparation"]})
        table.attrs = {}
        tables.append(table)
    frame = pd.concat(tables, ignore_index=True)
    if frame.window_id.duplicated().any() or not np.isfinite(frame[list(FULL_FEATURES)].to_numpy()).all():
        raise ValueError("Caractéristiques invalides ou fenêtres dupliquées")
    destination.mkdir(parents=True, exist_ok=True)
    frame.to_csv(destination / f"features_{role}.csv", index=False)
    write_json(destination / f"preparation_{role}.json", journal)
    return frame


def scores(predictions: pd.DataFrame, config: dict, destination: Path, prefix: str) -> dict:
    results = {name: evaluate_predictions(part, config["classes"])
               for name, part in predictions.groupby("experiment")}
    write_json(destination / f"{prefix}_metrics.json", results)
    write_json(destination / f"{prefix}_bootstrap.json", bootstrap_model_comparison(
        predictions, config["classes"], n_bootstrap=config["n_bootstrap"], random_state=config["random_state"]))
    return results


def frozen_inputs(root: Path, destination: Path) -> dict:
    paths = ["selection.json", "features_development.csv"]
    return {"scientific_sources": source_fingerprints(root),
            "development": {p: sha256(destination / p) for p in paths},
            "environment": environment()}


def freeze(root: Path, destination: Path) -> None:
    stamp = frozen_inputs(root, destination)
    stamp["test_access"] = "sealed; no final features or scores consulted"
    if (destination / "test_consulted.json").exists():
        old = json.loads((destination / "freeze.json").read_text())
        if old != stamp:
            raise RuntimeError("Test déjà consulté : impossible de remplacer le protocole gelé")
        return
    write_json(destination / "freeze.json", stamp)


def evaluate(root: Path, destination: Path, *, replay: bool = False) -> pd.DataFrame:
    frozen = json.loads((destination / "freeze.json").read_text())
    current = frozen_inputs(root, destination)
    if any(current[key] != frozen[key] for key in current):
        raise RuntimeError("Les sources, données, choix ou versions diffèrent du gel")
    marker = destination / "test_consulted.json"
    if marker.exists() and not replay:
        raise RuntimeError("Test déjà consulté. Seule une reproduction identique est permise (--replay).")
    # Mark access before feature extraction or any final-score calculation.
    if not marker.exists():
        write_json(marker, {"freeze_sha256": sha256(destination / "freeze.json"), "state": "access_started"})
    elif json.loads(marker.read_text())["freeze_sha256"] != sha256(destination / "freeze.json"):
        raise RuntimeError("Le marqueur ne correspond pas au gel")
    config = configuration(root)
    dev = pd.read_csv(destination / "features_development.csv")
    run_dir = root / "outputs/replay_evaluation" if replay else destination
    run_dir.mkdir(parents=True, exist_ok=True)
    previous = pd.read_csv(destination / "final_predictions.csv") if replay and (destination / "final_predictions.csv").exists() else None
    test = extract(root, run_dir, "final_test")
    selected = json.loads((destination / "selection.json").read_text())
    predictions = final_test(dev, test, selected, config, run_dir,
                             feature_sets={"base": list(BASE_FEATURES), "full": list(FULL_FEATURES)})
    if previous is not None:
        pd.testing.assert_frame_equal(previous, predictions.reset_index(drop=True), check_dtype=False, rtol=1e-12, atol=1e-12)
    scores(predictions, config, run_dir, "final")
    if replay and previous is None:
        # Recovery after an interrupted first access: no original prediction
        # exists to overwrite or compare. Publish only after the replay succeeds.
        for name in ("features_final_test.csv", "preparation_final_test.json", "final_predictions.csv",
                     "final_model_provenance.json", "final_metrics.json", "final_bootstrap.json"):
            source = run_dir / name
            if source.exists():
                shutil.copy2(source, destination / name)
        for experiment in ("E1", "E2", "E3", "E4"):
            source = run_dir / f"{experiment}_model.joblib"
            if source.exists():
                shutil.copy2(source, destination / source.name)
    write_json(marker, {"freeze_sha256": sha256(destination / "freeze.json"), "state": "complete",
                        "predictions_sha256": sha256(destination / "final_predictions.csv")})
    return predictions


def develop(root: Path, destination: Path) -> dict:
    if (destination / "test_consulted.json").exists():
        raise RuntimeError("Développement déjà clôturé : utiliser reproduce pour rejouer à l'identique")
    config = configuration(root)
    frame = pd.read_csv(destination / "features_development.csv")
    result = run_development(frame, config, destination,
                             feature_sets={"base": list(BASE_FEATURES), "full": list(FULL_FEATURES)})
    scores(result["oof_predictions"], config, destination, "development")
    write_json(destination / "environment.json", environment())
    return result


def reproduce(root: Path, destination: Path) -> None:
    """Recompute selected protocol without searching or consulting a new test."""
    release = root / "results"
    cold_checkout = not (destination / "freeze.json").exists()
    if cold_checkout:
        # outputs/ is ignored by Git. A release carries the immutable ledger
        # and reference prediction, while features are regenerated from raw MAT.
        required = ("freeze.json", "selection.json", "test_consulted.json", "final_predictions.csv")
        missing = [name for name in required if not (release / name).is_file()]
        if missing:
            raise FileNotFoundError(f"Fichiers de livraison manquants : {missing}")
        destination.mkdir(parents=True, exist_ok=True)
        for name in required:
            shutil.copy2(release / name, destination / name)
        released_marker = json.loads((destination / "test_consulted.json").read_text())
        if (released_marker.get("state") != "complete"
                or released_marker.get("freeze_sha256") != sha256(destination / "freeze.json")
                or released_marker.get("predictions_sha256") != sha256(destination / "final_predictions.csv")):
            raise RuntimeError("Le registre de livraison ne correspond pas aux prédictions finales")
    frozen = json.loads((destination / "freeze.json").read_text())
    if not cold_checkout:
        current = frozen_inputs(root, destination)
        if any(current[k] != frozen[k] for k in current):
            raise RuntimeError("Reproduction impossible : les entrées gelées ont changé")
    replay_dir = root / "outputs/reproduction"
    replay_dir.mkdir(parents=True, exist_ok=True)
    # Re-audit existing hashes, then verify identical partitions and features.
    acquire_and_audit(root)
    manifest = pd.read_csv(root / "data/manifest.csv")
    build_splits(manifest, root)
    new_dev = extract(root, replay_dir, "development")
    if cold_checkout:
        regenerated = replay_dir / "features_development.csv"
        if sha256(regenerated) != frozen["development"]["features_development.csv"]:
            raise RuntimeError("Les caractéristiques de développement diffèrent du gel")
        shutil.copy2(regenerated, destination / "features_development.csv")
    else:
        old_dev = pd.read_csv(destination / "features_development.csv")
        pd.testing.assert_frame_equal(old_dev, new_dev, check_dtype=False, rtol=1e-12, atol=1e-12)
    current = frozen_inputs(root, destination)
    if any(current[k] != frozen[k] for k in current):
        raise RuntimeError("L'audit, les partitions ou les entrées diffèrent du gel")
    selection = json.loads((destination / "selection.json").read_text())
    config = configuration(root)
    reproduction_marker = replay_dir / "test_consulted.json"
    write_json(reproduction_marker, {"freeze_sha256": sha256(destination / "freeze.json"),
                                     "state": "access_started", "source": "reproduction"})
    new_test = extract(root, replay_dir, "final_test")
    predicted = final_test(new_dev, new_test, selection, config, replay_dir,
                           feature_sets={"base": list(BASE_FEATURES), "full": list(FULL_FEATURES)})
    old = pd.read_csv(destination / "final_predictions.csv")
    pd.testing.assert_frame_equal(old, predicted, check_dtype=False, rtol=1e-12, atol=1e-12)
    write_json(reproduction_marker, {"freeze_sha256": sha256(destination / "freeze.json"),
                                     "state": "complete", "source": "reproduction",
                                     "predictions_sha256": sha256(replay_dir / "final_predictions.csv")})
    write_json(replay_dir / "verification.json", {"status": "identical", "n_final_predictions": len(predicted),
               "freeze_sha256": sha256(destination / "freeze.json"), "environment": environment()})


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("stage", choices=["audit", "extract", "develop", "freeze", "evaluate", "report", "reproduce"])
    parser.add_argument("--root", type=Path, default=Path.cwd())
    parser.add_argument("--output", default="outputs/main")
    parser.add_argument("--replay", action="store_true")
    args = parser.parse_args()
    root = args.root.resolve()
    destination = root / args.output
    destination.mkdir(parents=True, exist_ok=True)
    if args.stage == "audit":
        manifest = acquire_and_audit(root)
        build_splits(manifest, root)
    elif args.stage == "extract":
        extract(root, destination, "development")
    elif args.stage == "develop":
        develop(root, destination)
    elif args.stage == "freeze":
        freeze(root, destination)
    elif args.stage == "evaluate":
        evaluate(root, destination, replay=args.replay)
    elif args.stage == "reproduce":
        reproduce(root, destination)
    else:
        from .reporting import make_report
        make_report(root, destination)
    print(f"{args.stage}: terminé ({destination})")


if __name__ == "__main__":
    main()
