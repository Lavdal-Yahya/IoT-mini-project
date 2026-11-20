"""Figures et tables dérivées uniquement des sorties sauvegardées du protocole."""

from __future__ import annotations

import json
import shutil
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from .data import load_signal
from .features import BASE_FEATURES, FULL_FEATURES
from .provenance import sha256
from .signals import (
    bearing_frequencies, causal_bandpass, closed_window_envelope,
    prepare_signal_with_metadata, spectrum,
)


EXPERIMENTS = ("E1", "E2", "E3", "E4")
LABELS = {"healthy": "Sain", "inner_race": "Bague interne",
          "outer_race": "Bague externe", "ball": "Bille"}


def _save(fig, path: Path) -> None:
    fig.savefig(path, dpi=180, bbox_inches="tight", facecolor="white")
    plt.close(fig)


def _temporal(features: pd.DataFrame, classes: list[str], path: Path) -> None:
    # One point per original recording prevents long files dominating the plot.
    records = features.groupby(["recording_id", "class_label"], as_index=False)[list(BASE_FEATURES)].median()
    fig, axes = plt.subplots(1, 3, figsize=(12.5, 4), constrained_layout=True)
    rng = np.random.default_rng(313)
    for axis, feature, title in zip(axes, BASE_FEATURES,
                                    ("RMS", "Kurtosis de Pearson", "Facteur de crête")):
        for x, label in enumerate(classes):
            values = records.loc[records.class_label.eq(label), feature].to_numpy()
            axis.scatter(x + rng.uniform(-0.11, 0.11, len(values)), values,
                         color="#2563a6", alpha=0.72, s=29)
            if len(values):
                axis.plot([x - 0.22, x + 0.22], [np.median(values)] * 2,
                          color="#d54b34", lw=2.2)
        axis.set_xticks(range(len(classes)), [LABELS.get(c, c) for c in classes], rotation=25, ha="right")
        axis.set_title(title)
        axis.grid(axis="y", alpha=0.25)
    axes[0].set_ylabel("Valeur sur une fenêtre de 1 s, médiane par enregistrement")
    fig.suptitle("Indicateurs temporels — développement seulement\nPoints : essais ; trait rouge : médiane de la classe", fontsize=12)
    _save(fig, path)


def _spectra(root: Path, config: dict, classes: list[str], path: Path) -> None:
    manifest = pd.read_csv(root / "data/manifest.csv")
    splits = pd.read_csv(root / "data/splits/recordings.csv")
    selected = manifest.merge(splits, on=["recording_id", "group_id"], validate="one_to_one")
    selected = selected[selected.split_role.eq("development")]
    fs = float(config["fs_analysis_hz"])
    window = int(round(fs * float(config["window_seconds"])))
    warmup = float(config["warmup_seconds"])
    band = tuple(config["envelope_band_hz"])
    order = int(config["filter_order"])
    edge = int(round(float(config["envelope_edge_seconds"]) * fs))
    fig, axes = plt.subplots(len(classes), 2, figsize=(12, 11), constrained_layout=True)
    for i, label in enumerate(classes):
        row = selected[selected.class_label.eq(label)].sort_values("recording_id").iloc[0]
        signal = load_signal(root, row)
        prepared, _ = prepare_signal_with_metadata(
            signal, float(row.fs_native_hz), fs, warmup_seconds=warmup,
            fir_taps=int(config.get("fir_taps", 161)),
        )
        filtered = causal_bandpass(prepared, fs, band, order)
        discard = int(np.ceil(warmup * fs))
        raw_window = prepared[discard:discard + window]
        filtered_window = filtered[discard:discard + window]
        if len(raw_window) != window:
            raise ValueError(f"Fenêtre de 1 s absente : {row.recording_id}")
        envelope = closed_window_envelope(filtered_window, edge)
        raw_f, raw_a = spectrum(raw_window, fs)
        env_f, env_a = spectrum(envelope, fs)
        axes[i, 0].plot(raw_f, raw_a, color="#2563a6", lw=0.7)
        axes[i, 0].set_xlim(0, fs / 2)
        axes[i, 0].set_ylabel(f"{LABELS.get(label, label)}\nAmplitude")
        axes[i, 0].grid(alpha=0.2)
        axes[i, 1].plot(env_f, env_a, color="#4d7450", lw=0.8)
        axes[i, 1].set_xlim(0, 600)
        axes[i, 1].grid(alpha=0.2)
        frequencies = bearing_frequencies(float(row.rpm_used))
        for key, color in (("bpfo_hz", "#d54b34"), ("bpfi_hz", "#8a53a8")):
            axes[i, 1].axvline(frequencies[key], color=color, linestyle="--", lw=1.2,
                               label=key.replace("_hz", "").upper())
        axes[i, 1].legend(loc="upper right", fontsize=8)
        axes[i, 1].text(0.02, 0.93, f"{row.recording_id}; {row.rpm_used:.0f} tr/min"
                        + (" (approx.)" if bool(row.rpm_is_approximate) else ""),
                        transform=axes[i, 1].transAxes, fontsize=8, va="top")
    axes[0, 0].set_title("Spectre de vibration DE (Hann)")
    axes[0, 1].set_title("Spectre d'enveloppe (bande 2–5 kHz)")
    axes[-1, 0].set_xlabel("Fréquence (Hz)")
    axes[-1, 1].set_xlabel("Fréquence (Hz)")
    fig.suptitle("Une fenêtre de 1 s par classe — développement uniquement", fontsize=13)
    _save(fig, path)


def _metrics_rows(stage: str, metrics: dict) -> list[dict]:
    rows = []
    for experiment in EXPERIMENTS:
        result = metrics[experiment]
        weighted = result["weighted_window"]
        record = result["record"]
        rows.append({"stage": stage, "experiment": experiment,
                     "balanced_accuracy": weighted["balanced_accuracy"],
                     "accuracy": weighted["accuracy"], "macro_f1": weighted["macro_f1"],
                     "record_accuracy": record["accuracy"],
                     "n_recordings": result["n_recordings"],
                     "n_windows": result["n_windows"]})
    return rows


def _development_scores(summary: pd.DataFrame, path: Path) -> None:
    rows = summary[summary.stage.eq("development")].set_index("experiment").loc[list(EXPERIMENTS)]
    fig, axis = plt.subplots(figsize=(7, 4.2), constrained_layout=True)
    x = np.arange(len(EXPERIMENTS))
    width = 0.25
    for offset, column, label, color in (
        (-width, "balanced_accuracy", "Exactitude équilibrée", "#2563a6"),
        (0, "accuracy", "Exactitude pondérée", "#4d7450"),
        (width, "macro_f1", "Macro-F1", "#d58d2e"),
    ):
        axis.bar(x + offset, rows[column], width, label=label, color=color)
    axis.set_xticks(x, EXPERIMENTS)
    axis.set_ylim(0, 1.05)
    axis.set_ylabel("Score hors pli")
    axis.set_title("Développement — fenêtres pondérées également par essai")
    axis.legend(fontsize=8)
    axis.grid(axis="y", alpha=0.2)
    _save(fig, path)


def _final_confusion(metrics: dict, classes: list[str], path: Path) -> None:
    fig, axes = plt.subplots(2, 2, figsize=(9.5, 8.5), constrained_layout=True)
    for axis, experiment in zip(axes.flat, EXPERIMENTS):
        result = metrics[experiment]["record"]
        matrix = np.asarray(result["confusion"], dtype=int)
        axis.imshow(matrix, cmap="Blues", vmin=0, vmax=max(1, matrix.max()))
        for (i, j), value in np.ndenumerate(matrix):
            axis.text(j, i, str(value), ha="center", va="center", fontsize=10)
        axis.set_xticks(range(len(classes)), [LABELS.get(c, c) for c in classes], rotation=35, ha="right")
        axis.set_yticks(range(len(classes)), [LABELS.get(c, c) for c in classes])
        axis.set_title(experiment)
        axis.set_xlabel("Classe prédite")
        axis.set_ylabel("Classe réelle")
    fig.suptitle("Test final 3 HP — confusion par enregistrement", fontsize=13)
    _save(fig, path)


def _ablation(summary: pd.DataFrame, path: Path) -> None:
    fig, axis = plt.subplots(figsize=(7, 4.4), constrained_layout=True)
    for stage, marker, color in (("development", "o", "#2563a6"), ("final", "s", "#d54b34")):
        part = summary[summary.stage.eq(stage)].set_index("experiment")
        if part.empty:
            continue
        axis.plot(EXPERIMENTS, part.loc[list(EXPERIMENTS), "balanced_accuracy"],
                  marker=marker, color=color, lw=1.5, label=stage)
    axis.set_ylim(0, 1.05)
    axis.set_ylabel("Exactitude équilibrée, poids égal par essai")
    axis.set_title("Ablation E1–E4 : caractéristiques et classifieur")
    axis.grid(alpha=0.2)
    axis.legend()
    _save(fig, path)


def make_report(root: Path, destination: Path) -> Path:
    """Génère les artefacts `results/` depuis une exécution enregistrée.

    La figure des spectres lit quatre essais du développement seulement. Les
    résultats de test ne sont copiés et tracés qu'après leur sortie complète.
    """
    root, destination = Path(root), Path(destination)
    release = root / "results"
    figures = release / "figures"
    figures.mkdir(parents=True, exist_ok=True)
    config_path = root / "configs/experiment.json"
    config = json.loads(config_path.read_text(encoding="utf-8"))
    feature_path = destination / "features_development.csv"
    development_path = destination / "development_metrics.json"
    if not feature_path.exists():
        raise FileNotFoundError("Caractéristiques de développement requises")
    features = pd.read_csv(feature_path)
    if not features.split_role.eq("development").all():
        raise ValueError("La figure physique ne peut lire que le développement")
    classes = config["classes"]
    _temporal(features, classes, figures / "temporal_features.png")
    _spectra(root, config, classes, figures / "spectra_envelope.png")
    dictionary = pd.DataFrame({
        "feature": FULL_FEATURES,
        "set": ["baseline" if name in BASE_FEATURES else "enriched" for name in FULL_FEATURES],
        "description": [
            "RMS de la vibration centrée", "Kurtosis de Pearson sans biais", "Maximum absolu / RMS",
            "Centre de gravité du spectre de vibration (Hz)", "Entropie normalisée du spectre de vibration",
            "Centre de gravité du spectre d'enveloppe (Hz)", "Entropie normalisée du spectre d'enveloppe",
            *[f"Part d'énergie d'enveloppe près de {kind.upper()}, harmonique {harmonic}"
              for kind in ("bpfo", "bpfi") for harmonic in (1, 2, 3)],
        ],
    })
    dictionary.to_csv(release / "feature_dictionary.csv", index=False)
    required = [config_path, destination / "preparation_development.json",
                destination / "filter_diagnostics.json"]
    final_ready = False
    if development_path.exists():
        development = json.loads(development_path.read_text(encoding="utf-8"))
        rows = _metrics_rows("development", development)
        final_path = destination / "final_metrics.json"
        marker_path = destination / "test_consulted.json"
        final_ready = (final_path.exists() and marker_path.exists() and
                       json.loads(marker_path.read_text(encoding="utf-8")).get("state") == "complete")
        if final_ready:
            final = json.loads(final_path.read_text(encoding="utf-8"))
            rows += _metrics_rows("final", final)
            _final_confusion(final, classes, figures / "final_confusion.png")
        summary = pd.DataFrame(rows)
        summary.to_csv(release / "summary.csv", index=False)
        _development_scores(summary, figures / "development_scores.png")
        _ablation(summary, figures / "ablation.png")
        required += [development_path, destination / "development_bootstrap.json",
                     destination / "development_oof.csv", destination / "selection.json",
                     destination / "environment.json"]
    if (destination / "freeze.json").exists():
        required.append(destination / "freeze.json")
    if final_ready:
        required += [final_path, destination / "final_bootstrap.json",
                     destination / "final_predictions.csv", marker_path,
                     destination / "preparation_final_test.json"]
    provenance = []
    for source in required:
        if not source.exists():
            raise FileNotFoundError(source)
        target = release / source.name
        shutil.copy2(source, target)
        provenance.append({"source": str(source.resolve()), "released": str(target.relative_to(root)),
                           "sha256": sha256(source)})
    (release / "source_paths.json").write_text(json.dumps(provenance, indent=2), encoding="utf-8")
    return release
