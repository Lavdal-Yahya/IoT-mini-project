"""Acquisition et audit d'intégrité du sous-ensemble CWRU DE."""

from __future__ import annotations

import hashlib
import json
import re
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlparse

import numpy as np
import pandas as pd
import requests
from scipy.io import loadmat


FAULT_PAGE = "https://engineering.case.edu/bearingdatacenter/12k-drive-end-bearing-fault-data"
NORMAL_PAGE = "https://engineering.case.edu/bearingdatacenter/normal-baseline-data"
PROCEDURE_PAGE = "https://engineering.case.edu/bearingdatacenter/apparatus-and-procedures"
DOWNLOAD_PAGE = "https://engineering.case.edu/bearingdatacenter/download-data-file"
BASELINE_FS_SOURCE = "https://papers.phmsociety.org/index.php/phme/article/download/3329/1947"
CLASSES = ("healthy", "inner_race", "ball", "outer_race")
LOAD_RPM_APPROX = {0: 1797, 1: 1772, 2: 1750, 3: 1730}


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _official_links(page: str) -> dict[str, str]:
    response = requests.get(page, timeout=30)
    response.raise_for_status()
    return {
        label.strip(): url
        for url, label in re.findall(
            r'<a[^>]*href="([^"]+\.mat)"[^>]*>([^<]+)</a>', response.text
        )
        if urlparse(url).netloc == "engineering.case.edu"
    }


def _candidates() -> list[dict]:
    normal = _official_links(NORMAL_PAGE)
    fault = _official_links(FAULT_PAGE)
    expected = [f"Normal_{load}" for load in range(4)]
    expected += [
        f"{prefix}{size}_{load}"
        for size in ("007", "014", "021")
        for load in range(4)
        for prefix in ("IR", "B", "OR")
    ]
    # The official outer-race labels include the position before the load.
    expected = [label.replace("OR", "OR", 1).replace("_", "@6_", 1)
                if label.startswith("OR") else label for label in expected]
    rows = []
    for label in expected:
        page = NORMAL_PAGE if label.startswith("Normal") else FAULT_PAGE
        url = (normal if page == NORMAL_PAGE else fault).get(label)
        if not url:
            raise ValueError(f"Lien officiel absent : {label}")
        load = int(label.rsplit("_", 1)[1])
        if label.startswith("Normal"):
            class_label, diameter, position = "healthy", None, None
        else:
            class_label = ("inner_race" if label.startswith("IR") else
                           "outer_race" if label.startswith("OR") else "ball")
            diameter = int(label[2:5] if label.startswith("OR") else
                           label[2:5] if label.startswith("IR") else label[1:4]) / 1000
            position = "6:00" if class_label == "outer_race" else None
        rows.append({
            "recording_id": label, "group_id": label, "source_url": url,
            "local_path": f"data/raw/{Path(urlparse(url).path).name}",
            "source_page": page, "class_label": class_label,
            "fault_diameter_in": diameter, "outer_race_position": position,
            "load_hp": load, "rpm_table_approx": LOAD_RPM_APPROX[load],
            "sensor_location": "DE", "bearing_location": "DE",
            "fs_native_hz": 48000 if class_label == "healthy" else 12000,
            "metadata_source": f"{page}; {BASELINE_FS_SOURCE if class_label == 'healthy' else FAULT_PAGE}; MAT",
            "units": "acceleration (unit not stated on official pages)",
        })
    if len(rows) != 40 or len({r["source_url"] for r in rows}) != 40:
        raise ValueError("Le sous-ensemble officiel attendu doit avoir 40 fichiers distincts")
    return rows


def _download(row: dict, root: Path, known_hash: str | None) -> tuple[str, str]:
    path = root / row["local_path"]
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists() and path.stat().st_size > 0:
        current = _sha256(path)
        if known_hash and current != known_hash:
            raise ValueError(f"Empreinte du cache non conforme : {path}")
        return row["recording_id"], current
    temp = path.with_suffix(".mat.part")
    try:
        with requests.get(row["source_url"], timeout=(15, 180), stream=True) as response:
            response.raise_for_status()
            with temp.open("wb") as stream:
                for chunk in response.iter_content(1024 * 1024):
                    if chunk:
                        stream.write(chunk)
        if temp.stat().st_size == 0:
            raise ValueError(f"Fichier vide : {row['source_url']}")
        temp.replace(path)
    finally:
        temp.unlink(missing_ok=True)
    return row["recording_id"], _sha256(path)


def _mat_audit(path: Path, recording_id: str) -> tuple[dict, np.ndarray]:
    mat = loadmat(path)
    stem = path.stem
    key = f"X{stem.zfill(3)}_DE_time"
    if key not in mat:
        raise ValueError(f"Clé DE propre au fichier {recording_id} absente : {key}")
    signal = np.asarray(mat[key]).reshape(-1)
    if not np.issubdtype(signal.dtype, np.number) or signal.size == 0:
        raise ValueError(f"Signal numérique non vide requis : {path}")
    rpm_key = f"X{stem.zfill(3)}RPM"
    rpm = float(np.asarray(mat[rpm_key]).reshape(-1)[0]) if rpm_key in mat else None
    bits = np.asarray(signal, dtype="<f8").tobytes()
    finite = np.isfinite(signal)
    equal_neighbor = np.asarray(signal[1:] == signal[:-1])
    changes = np.flatnonzero(~equal_neighbor)
    run_lengths = np.diff(np.r_[-1, changes, signal.size - 1])
    info = {
        "mat_key": key, "mat_keys": sorted(k for k in mat if not k.startswith("__")),
        "rpm_key": rpm_key if rpm_key in mat else None, "rpm": rpm,
        "n_samples": int(signal.size), "nonfinite_count": int((~finite).sum()),
        "longest_constant_run": int(run_lengths.max()),
        "min": float(np.min(signal[finite])) if finite.any() else None,
        "max": float(np.max(signal[finite])) if finite.any() else None,
        "min_count": int(np.sum(signal == np.min(signal[finite]))) if finite.any() else None,
        "max_count": int(np.sum(signal == np.max(signal[finite]))) if finite.any() else None,
        "signal_sha256": hashlib.sha256(bits).hexdigest(),
    }
    return info, signal


def load_signal(root: Path, row: pd.Series | dict) -> np.ndarray:
    """Lit uniquement le canal DE du fichier original identifié par une ligne du manifeste."""
    path = Path(root) / str(row["local_path"])
    if not path.is_file():
        raise FileNotFoundError(path)
    if pd.notna(row.get("file_sha256")) and _sha256(path) != row["file_sha256"]:
        raise ValueError(f"Empreinte du fichier non conforme : {path}")
    info, signal = _mat_audit(path, str(row["recording_id"]))
    if pd.notna(row.get("mat_key")) and info["mat_key"] != row["mat_key"]:
        raise ValueError(f"Clé MAT non conforme : {path}")
    if pd.notna(row.get("signal_sha256")) and info["signal_sha256"] != row["signal_sha256"]:
        raise ValueError(f"Empreinte du signal non conforme : {path}")
    return signal


def acquire_and_audit(root: Path) -> pd.DataFrame:
    """Télécharge, vérifie et audite les 40 enregistrements sans entraînement."""
    root = Path(root)
    rows = _candidates()
    manifest_path = root / "data/manifest.csv"
    previous = pd.read_csv(manifest_path).set_index("recording_id") if manifest_path.exists() else None
    known = {}
    if previous is not None and "file_sha256" in previous:
        known = previous["file_sha256"].dropna().to_dict()
    with ThreadPoolExecutor(max_workers=6) as pool:
        hashes = dict(pool.map(lambda row: _download(row, root, known.get(row["recording_id"])), rows))
    audits = []
    for row in rows:
        info, _ = _mat_audit(root / row["local_path"], row["recording_id"])
        row.update({key: info[key] for key in (
            "mat_key", "rpm_key", "rpm", "n_samples", "nonfinite_count",
            "longest_constant_run", "min", "max", "min_count", "max_count", "signal_sha256"
        )})
        row["rpm_used"] = info["rpm"] if info["rpm"] is not None else row["rpm_table_approx"]
        row["rpm_source"] = "MAT measured" if info["rpm"] is not None else "official table approximate"
        row["rpm_is_approximate"] = info["rpm"] is None
        row["file_sha256"] = hashes[row["recording_id"]]
        row["duration_s"] = row["n_samples"] / row["fs_native_hz"]
        row["inclusion_status"] = "included" if info["nonfinite_count"] == 0 else "excluded"
        row["exclusion_reason"] = None if info["nonfinite_count"] == 0 else "non-finite samples"
        audits.append({"recording_id": row["recording_id"], "mat_keys": info["mat_keys"],
                       "file_sha256": row["file_sha256"], "signal_sha256": info["signal_sha256"],
                       "nonfinite_count": info["nonfinite_count"],
                       "longest_constant_run": info["longest_constant_run"],
                       "min": info["min"], "max": info["max"],
                       "min_count": info["min_count"], "max_count": info["max_count"]})
    frame = pd.DataFrame(rows)
    # Union connected aliases, including transitive file/signal matches.
    parent = {record: record for record in frame.recording_id}

    def find(record: str) -> str:
        while parent[record] != record:
            parent[record] = parent[parent[record]]
            record = parent[record]
        return record

    for column in ("file_sha256", "signal_sha256"):
        for _, members in frame.groupby(column):
            records = members.recording_id.tolist()
            for record in records[1:]:
                a, b = find(records[0]), find(record)
                parent[max(a, b)] = min(a, b)
    frame["group_id"] = frame.recording_id.map(find)
    frame.to_csv(manifest_path, index=False)
    coverage = frame.groupby(["class_label", "load_hp"], dropna=False).agg(
        n_recordings=("recording_id", "nunique"), n_groups=("group_id", "nunique")
    ).reset_index()
    coverage.to_csv(root / "data/classcoverage.csv", index=False)
    audit = {
        "audited_at_utc": datetime.now(timezone.utc).isoformat(),
        "n_recordings": len(frame), "n_groups": int(frame.group_id.nunique()),
        "fs_evidence": {"faults": FAULT_PAGE, "healthy": BASELINE_FS_SOURCE,
                        "healthy_note": "Official normal page does not state a native frequency; independent primary research identifies 48 kHz baseline"},
        "units_status": "Official pages do not explicitly state acceleration unit",
        "records": audits,
    }
    (root / "data/audit.json").write_text(json.dumps(audit, indent=2), encoding="utf-8")
    return frame
