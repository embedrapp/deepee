from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List, Optional

from .checks import CHECKS
from .task import Task, iter_tasks


DEPRECATED_KEYS = {
    "category",
    "default_verification_track",
    "pass_threshold",
    "required",
    "tracks",
    "verification_tracks",
    "weight",
}


def _error(errors: List[Dict[str, Any]], task: Task, message: str) -> None:
    errors.append({"task_id": task.id, "path": str(task.path), "message": message})


def _safe_relative(value: Any) -> bool:
    path = Path(str(value))
    return not path.is_absolute() and ".." not in path.parts


def _validate_artifact(task: Task, artifact: Dict[str, Any], errors: List[Dict[str, Any]]) -> None:
    path = artifact.get("path")
    if not path:
        _error(errors, task, "required artifact is missing path")
    elif not _safe_relative(path):
        _error(errors, task, f"required artifact escapes the run directory: {path}")
    kind = artifact.get("kind", "file")
    if kind not in {"any", "directory", "file", "glob"}:
        _error(errors, task, f"unknown artifact kind: {kind}")


def _validate_check(task: Task, check: Dict[str, Any], errors: List[Dict[str, Any]]) -> None:
    check_type = check.get("type")
    name = check.get("name") or check_type
    if not check_type:
        _error(errors, task, "check is missing type")
    elif check_type not in CHECKS:
        _error(errors, task, f"unknown check type: {check_type}")
    for key in sorted(DEPRECATED_KEYS & set(check)):
        _error(errors, task, f"check {name} uses removed key: {key}")
    for key in ("root", "cwd", "path", "board", "schematic", "catalog", "submission"):
        value = check.get(key)
        if value and not _safe_relative(value):
            _error(errors, task, f"check {name} has unsafe {key}: {value}")


def lint_tasks(root: Optional[Path] = None) -> Dict[str, Any]:
    tasks = list(iter_tasks(root))
    errors: List[Dict[str, Any]] = []

    task_ids = [task.id for task in tasks]
    for duplicate in sorted({task_id for task_id in task_ids if task_ids.count(task_id) > 1}):
        for task in tasks:
            if task.id == duplicate:
                _error(errors, task, f"duplicate task id: {duplicate}")

    for task in tasks:
        manifest = task.manifest
        if not task.prompt_path.is_file():
            _error(errors, task, "prompt.md is missing")
        if not manifest.get("id"):
            _error(errors, task, "manifest is missing id")
        if not manifest.get("suite"):
            _error(errors, task, "manifest is missing suite")
        if not task.starter_path.is_dir():
            _error(errors, task, "starter directory is missing")
        if not (task.path / "expected_artifacts.yaml").is_file():
            _error(errors, task, "expected_artifacts.yaml is missing")
        for key in sorted(DEPRECATED_KEYS & set(manifest)):
            _error(errors, task, f"manifest uses removed key: {key}")

        artifacts = manifest.get("required_artifacts")
        if not isinstance(artifacts, list) or not artifacts:
            _error(errors, task, "required_artifacts must be a non-empty list")
        else:
            for artifact in artifacts:
                if not isinstance(artifact, dict):
                    _error(errors, task, "required artifact must be a mapping")
                else:
                    _validate_artifact(task, artifact, errors)

        checks = manifest.get("checks")
        if not isinstance(checks, list) or not checks:
            _error(errors, task, "checks must be a non-empty list")
            continue
        for check in checks:
            if not isinstance(check, dict):
                _error(errors, task, "check must be a mapping")
            else:
                _validate_check(task, check, errors)
        names = [str(check.get("name") or check.get("type")) for check in checks if isinstance(check, dict)]
        for duplicate in sorted({name for name in names if names.count(name) > 1}):
            _error(errors, task, f"duplicate check name: {duplicate}")

        check_types = {str(check.get("type")) for check in checks if isinstance(check, dict)}
        if task.suite == "schematic":
            if not list(task.starter_path.rglob("*.kicad_sch")):
                _error(errors, task, "schematic task needs a starter .kicad_sch")
        if task.suite in {"schematic", "schematic-design"}:
            if not {"kicad_schematic_structure", "kicad_erc"}.issubset(check_types):
                _error(errors, task, "schematic task needs structure and ERC checks")
        if task.suite == "pcb":
            if not list(task.starter_path.rglob("*.kicad_pcb")):
                _error(errors, task, "PCB task needs a starter .kicad_pcb")
        if task.suite in {"pcb", "pcb-design"}:
            if not {"kicad_pcb_structure", "kicad_drc"}.issubset(check_types):
                _error(errors, task, "PCB task needs structure and DRC checks")

    return {"ok": not errors, "task_count": len(tasks), "errors": errors}
