"""Empreintes et sérialisation des exécutions."""

from __future__ import annotations

import hashlib
import importlib.metadata
import json
import platform
from pathlib import Path


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_json(path: Path, value) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + "\n")


def source_fingerprints(root: Path) -> dict[str, str]:
    # Presentation changes cannot modify the frozen scientific computation.
    paths = [p for p in sorted((root / "src").rglob("*.py")) if p.name != "reporting.py"]
    paths += [root / "configs/experiment.json", root / "data/manifest.csv", root / "data/splits/recordings.csv"]
    paths += [root / "requirements.lock.txt"]
    return {str(p.relative_to(root)): sha256(p) for p in paths if p.exists()}


def environment() -> dict:
    packages = ["numpy", "scipy", "pandas", "scikit-learn", "matplotlib", "requests", "beautifulsoup4", "joblib"]
    return {"python": platform.python_version(), "packages": {p: importlib.metadata.version(p) for p in packages}}
