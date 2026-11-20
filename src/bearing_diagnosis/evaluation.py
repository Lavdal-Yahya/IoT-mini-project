"""Evaluation by window and by original recording.

The principal window metrics give each recording total weight one. Raw window
metrics are retained because they answer a different question.
"""

from __future__ import annotations

from itertools import combinations

import numpy as np
import pandas as pd
from sklearn.metrics import accuracy_score, confusion_matrix, f1_score


def _metrics(y_true: np.ndarray, y_pred: np.ndarray, classes: list[str], weights=None) -> dict:
    matrix = confusion_matrix(y_true, y_pred, labels=classes, sample_weight=weights)
    row_sums = matrix.sum(axis=1)
    normalized = np.divide(matrix, row_sums[:, None], out=np.zeros_like(matrix, dtype=float), where=row_sums[:, None] != 0)
    support = row_sums > 0
    recall = np.diag(normalized)
    # sklearn's balanced_accuracy_score omits absent classes. The explicit
    # calculation below keeps the declared class order and documents absence.
    return {
        "accuracy": float(accuracy_score(y_true, y_pred, sample_weight=weights)),
        "balanced_accuracy": float(recall[support].mean()) if support.any() else None,
        "macro_f1": float(f1_score(y_true, y_pred, labels=classes, average="macro", sample_weight=weights, zero_division=0)),
        "confusion": matrix.tolist(),
        "confusion_normalized_true": normalized.tolist(),
        "recall_by_class": {label: (float(recall[i]) if support[i] else None) for i, label in enumerate(classes)},
        "support_by_class": {label: float(row_sums[i]) for i, label in enumerate(classes)},
    }


def evaluate_predictions(predictions: pd.DataFrame, classes: list[str]) -> dict:
    """Return raw, equal-recording-weight, and aggregated-record metrics.

    Required columns are recording_id, class_label, and predicted_label.
    Probability columns named ``proba_<class>`` are required for aggregation;
    hard-label predictions cannot reconstruct a probability mean.
    """
    if not classes or len(set(classes)) != len(classes):
        raise ValueError("classes must be a nonempty list of unique labels")
    required = {"recording_id", "class_label", "predicted_label"}
    probability_columns = [f"proba_{label}" for label in classes]
    missing = (required | set(probability_columns)) - set(predictions.columns)
    if missing:
        raise ValueError(f"prediction columns missing: {sorted(missing)}")
    if predictions.empty or predictions[list(required) + probability_columns].isna().any().any():
        raise ValueError("predictions must be nonempty and complete")
    if not set(predictions.class_label).issubset(classes) or not set(predictions.predicted_label).issubset(classes):
        raise ValueError("unknown class label")
    if predictions.groupby("recording_id").class_label.nunique().gt(1).any():
        raise ValueError("one recording has multiple true classes")
    probabilities = predictions[probability_columns].to_numpy(dtype=float)
    if not np.isfinite(probabilities).all() or (probabilities < 0).any() or not np.allclose(probabilities.sum(axis=1), 1, atol=1e-6):
        raise ValueError("probabilities must be finite, nonnegative, and sum to one")

    true = predictions.class_label.to_numpy()
    predicted = predictions.predicted_label.to_numpy()
    weights = 1 / predictions.groupby("recording_id").recording_id.transform("size").to_numpy()
    records = predictions.groupby("recording_id", sort=True)
    per_record = records[probability_columns].mean().reset_index()
    per_record["class_label"] = records.class_label.first().to_numpy()
    per_record["n_windows"] = records.size().to_numpy()
    per_record["predicted_label"] = np.asarray(classes)[np.argmax(per_record[probability_columns].to_numpy(), axis=1)]
    per_record["correct"] = per_record.class_label.eq(per_record.predicted_label)

    return {
        "classes": list(classes),
        "n_windows": int(len(predictions)),
        "n_recordings": int(len(per_record)),
        "raw_window": _metrics(true, predicted, classes),
        "weighted_window": _metrics(true, predicted, classes, weights),
        "record": _metrics(per_record.class_label.to_numpy(), per_record.predicted_label.to_numpy(), classes),
        "per_record": per_record.to_dict(orient="records"),
    }


def bootstrap_model_comparison(
    predictions: pd.DataFrame, classes: list[str], *, n_bootstrap: int = 1000, random_state: int = 313
) -> dict:
    """Paired, class-stratified recording bootstrap of balanced accuracy.

    All experiments must predict the same windows. The draw is shared across
    experiments. Single-recording classes remain fixed in every resample.
    """
    if n_bootstrap < 1 or "experiment" not in predictions:
        raise ValueError("need positive n_bootstrap and experiment column")
    experiments = sorted(predictions.experiment.unique())
    if len(experiments) < 2:
        raise ValueError("need at least two experiments")
    if "window_id" not in predictions:
        raise ValueError("window_id is required for pairing")
    identity = ["window_id", "recording_id", "class_label"]
    first = predictions.loc[predictions.experiment.eq(experiments[0]), identity].sort_values("window_id").reset_index(drop=True)
    if first.window_id.duplicated().any():
        raise ValueError("duplicate window_id within experiment")
    for name in experiments[1:]:
        other = predictions.loc[predictions.experiment.eq(name), identity].sort_values("window_id").reset_index(drop=True)
        if not first.equals(other):
            raise ValueError("experiments do not share the same windows and labels")
    record_labels = first.groupby("recording_id").class_label.first()
    if first.groupby("recording_id").class_label.nunique().gt(1).any():
        raise ValueError("recording has multiple labels")
    missing_classes = set(classes) - set(record_labels)
    if missing_classes:
        raise ValueError(f"classes absent from bootstrap: {sorted(missing_classes)}")

    # A per-record class recall lets a sampled recording contribute exactly
    # once, irrespective of how many windows it contains.
    recalls = {}
    for name in experiments:
        frame = predictions.loc[predictions.experiment.eq(name)]
        recalls[name] = frame.assign(correct=frame.class_label.eq(frame.predicted_label)).groupby("recording_id").correct.mean()
    ids_by_class = {label: record_labels.index[record_labels.eq(label)].to_numpy() for label in classes}
    rng = np.random.default_rng(random_state)
    samples = {name: np.empty(n_bootstrap) for name in experiments}
    for iteration in range(n_bootstrap):
        selected = {label: rng.choice(ids, size=len(ids), replace=True) for label, ids in ids_by_class.items()}
        for name in experiments:
            samples[name][iteration] = np.mean([recalls[name].loc[selected[label]].mean() for label in classes])
    comparisons = {}
    for left, right in combinations(experiments, 2):
        delta = samples[right] - samples[left]
        comparisons[f"{right}_minus_{left}"] = {
            "point_difference": float(np.mean([recalls[right].loc[ids_by_class[label]].mean() - recalls[left].loc[ids_by_class[label]].mean() for label in classes])),
            "ci95": np.quantile(delta, [0.025, 0.975]).tolist(),
        }
    return {
        "metric": "record_equal_window_balanced_accuracy",
        "n_bootstrap": n_bootstrap,
        "random_state": random_state,
        "recordings_per_class": {label: int(len(ids)) for label, ids in ids_by_class.items()},
        "single_recording_classes": [label for label, ids in ids_by_class.items() if len(ids) == 1],
        "limitation": "A class with one recording has no estimated between-recording variability.",
        "comparisons": comparisons,
    }
