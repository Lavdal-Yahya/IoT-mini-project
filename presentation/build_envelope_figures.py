"""Large scientific figure from two development recordings for the oral deck."""
from __future__ import annotations

import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from bearing_diagnosis.data import load_signal
from bearing_diagnosis.signals import (
    bearing_frequencies, causal_bandpass, closed_window_envelope,
    prepare_signal_with_metadata, spectrum,
)

ROOT = Path(__file__).resolve().parents[1]
config = json.loads((ROOT / "configs/experiment.json").read_text())
manifest = pd.read_csv(ROOT / "data/manifest.csv")
splits = pd.read_csv(ROOT / "data/splits/recordings.csv")
rows = manifest.merge(splits, on=["recording_id", "group_id"], validate="one_to_one")
fs = float(config["fs_analysis_hz"])
warmup = float(config["warmup_seconds"])
window = int(round(fs * float(config["window_seconds"])))
edge = int(round(fs * float(config["envelope_edge_seconds"])))

fig, axes = plt.subplots(1, 2, figsize=(13.4, 4.5), constrained_layout=True)
for ax, recording_id, heading in zip(
    axes,
    ("IR007_0", "OR007@6_0"),
    ("Défaut de bague interne", "Défaut de bague externe"),
):
    row = rows.loc[rows.recording_id.eq(recording_id)].iloc[0]
    if row.split_role != "development":
        raise ValueError(f"{recording_id} is not a development recording")
    x = load_signal(ROOT, row)
    prepared, _ = prepare_signal_with_metadata(
        x, float(row.fs_native_hz), fs, warmup_seconds=warmup,
        fir_taps=int(config.get("fir_taps", 161)),
    )
    filtered = causal_bandpass(
        prepared, fs, tuple(config["envelope_band_hz"]), int(config["filter_order"])
    )
    startup = int(np.ceil(warmup * fs))
    windowed = filtered[startup:startup + window]
    if len(windowed) != window:
        raise ValueError(f"short window for {recording_id}")
    envelope = closed_window_envelope(windowed, edge)
    frequency, amplitude = spectrum(envelope, fs)
    bp = bearing_frequencies(float(row.rpm_used))
    ax.plot(frequency, amplitude, color="#38664d", lw=1.0)
    ax.axvline(bp["bpfo_hz"], color="#d54b34", ls="--", lw=1.5, label="BPFO")
    ax.axvline(bp["bpfi_hz"], color="#8453a0", ls="--", lw=1.5, label="BPFI")
    ax.set_xlim(0, 350)
    ax.set_xlabel("Fréquence (Hz)", fontsize=13)
    ax.set_title(f"{heading}\n{recording_id} · {row.rpm_used:.0f} tr/min", fontsize=15)
    ax.tick_params(labelsize=11)
    ax.grid(alpha=0.2)
    ax.legend(fontsize=11, loc="upper right")
axes[0].set_ylabel("Amplitude (unité source non précisée)", fontsize=12)
fig.suptitle("Enveloppe 2–5 kHz, une fenêtre par essai · développement uniquement", fontsize=16)
out = ROOT / "presentation/envelope_examples.png"
fig.savefig(out, dpi=180, facecolor="white", bbox_inches="tight")
plt.close(fig)
print(out)
