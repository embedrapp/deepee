from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Any, Dict, List

from .common import result


def _digest(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def run_starter_integrity(check: Dict[str, Any], task, run_dir: Path, options: Dict[str, Any]) -> Dict[str, Any]:
    starter = task.path / "starter"
    patterns = check.get("protected_globs") or []
    expected: Dict[str, Path] = {}
    for pattern in patterns:
        for path in starter.glob(str(pattern)):
            if path.is_file():
                expected[str(path.relative_to(starter))] = path

    missing: List[str] = []
    changed: List[str] = []
    for relative, source in sorted(expected.items()):
        candidate = run_dir / relative
        if not candidate.is_file():
            missing.append(relative)
        elif _digest(candidate) != _digest(source):
            changed.append(relative)

    score = 1.0 if expected and not missing and not changed else 0.0
    return result(
        check.get("name", "starter_integrity"),
        "starter_integrity",
        score,
        f"Protected {len(expected)} starter file(s); {len(missing)} missing and {len(changed)} changed",
        {"protected": sorted(expected), "missing": missing, "changed": changed},
        required_failed=bool(check.get("required", True) and score < 1.0),
    )
