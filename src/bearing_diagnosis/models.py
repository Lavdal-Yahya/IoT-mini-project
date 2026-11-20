"""The four prespecified CWRU model and feature ablations."""

from __future__ import annotations

import json
from itertools import product
from pathlib import Path

import numpy as np
import pandas as pd
from joblib import dump
from sklearn.ensemble import RandomForestClassifier
from sklearn.tree import DecisionTreeClassifier

from .evaluation import evaluate_predictions

BASE_FEATURES = ("rms", "kurtosis", "crest_factor")
EXPERIMENTS = {"E1": "tree", "E2": "tree", "E3": "forest", "E4": "forest"}
METADATA = {"recording_id", "group_id", "window_id", "class_label", "load_hp", "split_role", "fold"}


def _settings(config: dict) -> tuple[list[str], list[int | None], list[int], int, int, int]:
    model = config.get("model_grid", config.get("model", config.get("models", {})))
    classes = list(config.get("classes", config.get("class_labels", [])))
    if not classes:
        raise ValueError("config must declare classes in fixed order")
    depths = list(model.get("max_depth", config.get("max_depth", [3, 6, None])))
    leaves = list(model.get("min_samples_leaf", config.get("min_samples_leaf", [1, 5])))
    n_estimators = int(model.get("n_estimators", config.get("n_estimators", 200)))
    seed = int(config.get("random_state", model.get("random_state", 313)))
    n_jobs = int(model.get("n_jobs", config.get("n_jobs", 2)))
    if not depths or not leaves or any(x is not None and (not isinstance(x, int) or x < 1) for x in depths) or any(not isinstance(x, int) or x < 1 for x in leaves):
        raise ValueError("invalid model grid")
    return classes, depths, leaves, n_estimators, seed, n_jobs


def _feature_sets(features: pd.DataFrame, feature_sets: dict | None) -> dict[str, list[str]]:
    if feature_sets is None:
        try:
            from .features import BASE_FEATURES as imported_base, FULL_FEATURES

            base = list(imported_base)
            full = list(FULL_FEATURES)
        except (ImportError, AttributeError) as error:
            raise ValueError("explicit feature_sets or features.FULL_FEATURES is required") from error
    else:
        base = list(feature_sets["base"])
        full = list(feature_sets["full"])
    if base != list(BASE_FEATURES):
        raise ValueError(f"baseline must be {list(BASE_FEATURES)}")
    if len(full) <= len(base) or not set(base).issubset(full) or len(set(full)) != len(full):
        raise ValueError("full feature set must extend the baseline with unique features")
    if set(full) & METADATA or set(full) - set(features):
        raise ValueError("feature set contains metadata or missing columns")
    if not np.isfinite(features[full].to_numpy(dtype=float)).all():
        raise ValueError("features contain nonfinite values")
    return {"E1": base, "E2": full, "E3": base, "E4": full}


def _validate(features: pd.DataFrame, classes: list[str], role: str) -> None:
    required = METADATA - {"fold"} if role == "final_test" else METADATA
    missing = required - set(features)
    if missing:
        raise ValueError(f"feature columns missing: {sorted(missing)}")
    if features.empty or features.window_id.duplicated().any():
        raise ValueError("features must have unique windows and be nonempty")
    if features[list(required)].isna().any().any():
        raise ValueError("metadata cannot be missing")
    if not features.split_role.eq(role).all():
        raise ValueError(f"expected split_role={role}")
    if not set(features.class_label).issubset(classes):
        raise ValueError("unknown class label")
    if features.groupby("group_id").class_label.nunique().gt(1).any():
        raise ValueError("one group has multiple classes")
    if features.groupby("recording_id").group_id.nunique().gt(1).any():
        raise ValueError("one recording has multiple groups")
    if role == "development":
        if features.groupby("group_id").fold.nunique().gt(1).any():
            raise ValueError("a group crosses folds")
        if features.fold.nunique() < 2:
            raise ValueError("need at least two predefined folds")
        for fold in features.fold.unique():
            train = features.loc[features.fold.ne(fold)]
            valid = features.loc[features.fold.eq(fold)]
            if set(train.group_id) & set(valid.group_id):
                raise ValueError("train and validation groups overlap")
            if set(train.class_label) != set(classes) or set(valid.class_label) != set(classes):
                raise ValueError("every fold must contain all classes in train and validation")


def _estimator(kind: str, params: dict, n_estimators: int, seed: int, n_jobs: int):
    common = dict(max_depth=params["max_depth"], min_samples_leaf=params["min_samples_leaf"], random_state=seed)
    if kind == "tree":
        return DecisionTreeClassifier(**common)
    return RandomForestClassifier(n_estimators=n_estimators, n_jobs=n_jobs, **common)


def _prediction_frame(frame: pd.DataFrame, estimator, columns: list[str], classes: list[str], experiment: str) -> pd.DataFrame:
    probabilities = estimator.predict_proba(frame[columns])
    complete = np.zeros((len(frame), len(classes)))
    for source_index, label in enumerate(estimator.classes_):
        complete[:, classes.index(label)] = probabilities[:, source_index]
    result = frame[["window_id", "recording_id", "group_id", "class_label", "load_hp"]].copy()
    if "fold" in frame:
        result["fold"] = frame.fold.to_numpy()
    result["experiment"] = experiment
    result["predicted_label"] = np.asarray(classes)[np.argmax(complete, axis=1)]
    for index, label in enumerate(classes):
        result[f"proba_{label}"] = complete[:, index]
    return result


def _json(path: Path, value: dict) -> None:
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False, allow_nan=False) + "\n")


def run_development(features: pd.DataFrame, config: dict, output_dir: str | Path, feature_sets: dict | None = None) -> dict:
    """Grid search on saved group folds; score candidates by mean fold score.

    This selected out-of-fold score is optimistic. It is not a nested-CV
    estimate and is never used as a final-test estimate.
    """
    classes, depths, leaves, n_estimators, seed, n_jobs = _settings(config)
    _validate(features, classes, "development")
    columns_by_experiment = _feature_sets(features, feature_sets)
    destination = Path(output_dir)
    destination.mkdir(parents=True, exist_ok=True)
    grid_rows = []
    selected = {}
    selected_oof = []
    for experiment, kind in EXPERIMENTS.items():
        columns = columns_by_experiment[experiment]
        candidates = []
        for depth, leaf in product(depths, leaves):
            params = {"max_depth": depth, "min_samples_leaf": leaf}
            folds = []
            predictions = []
            for fold in sorted(features.fold.unique()):
                train = features.loc[features.fold.ne(fold)]
                valid = features.loc[features.fold.eq(fold)]
                estimator = _estimator(kind, params, n_estimators, seed, n_jobs)
                estimator.fit(train[columns], train.class_label)
                predicted = _prediction_frame(valid, estimator, columns, classes, experiment)
                score = evaluate_predictions(predicted, classes)["weighted_window"]["balanced_accuracy"]
                folds.append({"fold": int(fold), "balanced_accuracy": score, "n_train_groups": int(train.group_id.nunique()), "n_valid_groups": int(valid.group_id.nunique())})
                predictions.append(predicted)
                grid_rows.append({"experiment": experiment, "max_depth": depth, "min_samples_leaf": leaf, **folds[-1]})
            mean = float(np.mean([item["balanced_accuracy"] for item in folds]))
            candidates.append((mean, params, folds, pd.concat(predictions, ignore_index=True)))
        # Equal scores prefer a shallower tree, then a larger minimum leaf.
        # Grid order resolves any remaining exact tie.
        best = max(candidates, key=lambda item: (item[0], -depths.index(item[1]["max_depth"]), item[1]["min_samples_leaf"]))
        selected[experiment] = {
            "estimator": kind,
            "features": columns,
            "params": best[1],
            "mean_fold_balanced_accuracy": best[0],
            "fold_scores": best[2],
        }
        selected_oof.append(best[3])
    oof = pd.concat(selected_oof, ignore_index=True)
    grid = pd.DataFrame(grid_rows)
    winner = max(EXPERIMENTS, key=lambda name: selected[name]["mean_fold_balanced_accuracy"])
    oof.to_csv(destination / "development_oof.csv", index=False)
    grid.to_csv(destination / "grid_scores.csv", index=False)
    _json(destination / "selection.json", {"selected": selected, "winner": winner, "criterion": "mean fold equal-recording-weight balanced accuracy", "tie_break": "smaller depth, then larger minimum leaf; E1 before E2 before E3 before E4", "estimate_limit": "Selected development scores are optimistic; no nested cross-validation."})
    return {"selected": selected, "winner": winner, "oof_predictions": oof, "grid_scores": grid}


def final_test(dev_features: pd.DataFrame, test_features: pd.DataFrame, selection: dict, config: dict, output_dir: str | Path, feature_sets: dict | None = None) -> pd.DataFrame:
    """Fit fixed E1–E4 settings on development; predict final load once.

    Caller is responsible for freeze/consultation marker before this function.
    No test scores are calculated or used to choose a setting here.
    """
    classes, _, _, n_estimators, seed, n_jobs = _settings(config)
    _validate(dev_features, classes, "development")
    _validate(test_features, classes, "final_test")
    if set(dev_features.group_id) & set(test_features.group_id) or set(dev_features.recording_id) & set(test_features.recording_id) or set(dev_features.window_id) & set(test_features.window_id):
        raise ValueError("development and final test overlap")
    if set(dev_features.load_hp) & set(test_features.load_hp):
        raise ValueError("final test load must be absent from development")
    columns_by_experiment = _feature_sets(pd.concat([dev_features, test_features], ignore_index=True), feature_sets)
    chosen = selection.get("selected", selection)
    if set(chosen) != set(EXPERIMENTS):
        raise ValueError("selection must freeze E1–E4")
    destination = Path(output_dir)
    destination.mkdir(parents=True, exist_ok=True)
    predictions = []
    for experiment, kind in EXPERIMENTS.items():
        item = chosen[experiment]
        columns = columns_by_experiment[experiment]
        if item["estimator"] != kind or item["features"] != columns:
            raise ValueError("selected model or features differ from fixed experiments")
        estimator = _estimator(kind, item["params"], n_estimators, seed, n_jobs)
        estimator.fit(dev_features[columns], dev_features.class_label)
        dump(estimator, destination / f"{experiment}_model.joblib")
        predictions.append(_prediction_frame(test_features, estimator, columns, classes, experiment))
    result = pd.concat(predictions, ignore_index=True)
    result.to_csv(destination / "final_predictions.csv", index=False)
    _json(destination / "final_model_provenance.json", {"selected": chosen, "n_train_windows": len(dev_features), "n_train_groups": int(dev_features.group_id.nunique()), "n_test_windows": len(test_features), "n_test_groups": int(test_features.group_id.nunique()), "random_state": seed, "n_estimators": n_estimators})
    return result
