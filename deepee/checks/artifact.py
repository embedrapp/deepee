from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List

from .common import resolve_run_path, result


def _exists(run_dir: Path, item: Dict[str, Any]) -> bool:
    kind = item.get("kind", "file")
    path_value = str(item.get("path", ""))
    if kind == "glob":
        return bool(list(run_dir.glob(path_value)))
    path = resolve_run_path(run_dir, path_value)
    if kind == "directory":
        return path.is_dir()
    if kind == "any":
        return path.exists()
    return path.is_file()


def run_artifact_presence(check: Dict[str, Any], task, run_dir: Path, options: Dict[str, Any]) -> Dict[str, Any]:
    artifacts: List[Dict[str, Any]] = list(check.get("artifacts") or task.manifest.get("required_artifacts") or [])
    if not artifacts:
        return result(check.get("name", "artifact_presence"), "artifact_presence", 1.0, "No required artifacts declared")

    required = [item for item in artifacts if item.get("required", True)]
    found = []
    missing = []
    for item in required:
        if _exists(run_dir, item):
            found.append(item)
        else:
            missing.append(item)

    score = len(found) / len(required) if required else 1.0
    return result(
        check.get("name", "artifact_presence"),
        "artifact_presence",
        score,
        f"Found {len(found)}/{len(required)} required artifacts",
        {"found": found, "missing": missing},
        required_failed=bool(check.get("required", True) and missing),
    )
