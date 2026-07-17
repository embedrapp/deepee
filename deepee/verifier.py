from __future__ import annotations

import hashlib
import json
import os
import platform
import shutil
import subprocess
from pathlib import Path
from typing import Any, Dict, List, Optional

from .checks import CHECKS
from .config import utc_timestamp, write_json
from .task import iter_tasks, resolve_task


VERSION_COMMANDS = {
    "gcc": ["gcc", "--version"],
    "kicad-cli": ["kicad-cli", "--version"],
    "make": ["make", "--version"],
    "platformio": ["pio", "--version"],
}


def _hash_file(path: Path, digest: "hashlib._Hash", label: str) -> None:
    digest.update(label.encode("utf-8"))
    digest.update(b"\0")
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    digest.update(b"\0")


def _hash_paths(paths: List[Path], base: Path) -> str:
    digest = hashlib.sha256()
    for path in sorted(path for path in paths if path.exists() and path.is_file()):
        try:
            label = str(path.relative_to(base))
        except ValueError:
            label = path.name
        _hash_file(path, digest, label)
    return digest.hexdigest()


def _task_hash(task) -> str:
    paths = [
        path
        for path in task.path.rglob("*")
        if path.is_file() and "__pycache__" not in path.parts and path.suffix != ".pyc"
    ]
    return _hash_paths(paths, task.path)


def _artifacts_hash(run_dir: Path) -> Optional[str]:
    artifacts = run_dir / "artifacts"
    return _hash_paths(list(artifacts.rglob("*")), artifacts) if artifacts.exists() else None


def _submission_hash(task, run_dir: Path) -> Optional[str]:
    paths: List[Path] = []
    for pattern in task.manifest.get("submission_paths") or ["artifacts/**/*"]:
        candidate = run_dir / str(pattern)
        if not any(char in str(pattern) for char in "*?["):
            if candidate.is_file():
                paths.append(candidate)
            elif candidate.is_dir():
                paths.extend(candidate.rglob("*"))
        else:
            paths.extend(run_dir.glob(str(pattern)))
    files = [path for path in paths if path.is_file()]
    return _hash_paths(files, run_dir) if files else None


def _benchmark_hash(root: Path) -> str:
    paths: List[Path] = []
    for relative in ("deepee", "tasks"):
        base = root / relative
        if base.exists():
            paths.extend(
                path
                for path in base.rglob("*")
                if path.is_file() and "__pycache__" not in path.parts and path.suffix != ".pyc"
            )
    for relative in ("benchmark.yaml", "pyproject.toml", "agents/AGENT_CONTEXT.md", "docker/tool-versions.lock"):
        path = root / relative
        if path.is_file():
            paths.append(path)
    return _hash_paths(paths, root)


def _tool_versions() -> Dict[str, Any]:
    versions: Dict[str, Any] = {}
    for name, command in VERSION_COMMANDS.items():
        resolved = shutil.which(command[0])
        if not resolved:
            versions[name] = {"available": False}
            continue
        try:
            completed = subprocess.run(command, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, timeout=5)
            lines = (completed.stdout or "").strip().splitlines()
            versions[name] = {
                "available": True,
                "path": resolved,
                "returncode": completed.returncode,
                "version": lines[0] if lines else "",
            }
        except (OSError, subprocess.SubprocessError) as exc:
            versions[name] = {"available": True, "path": resolved, "error": str(exc)}
    return versions


def verify_task(
    task_ref: str,
    run_dir: Path,
    output: Optional[Path] = None,
    allow_missing_tools: bool = False,
    root: Optional[Path] = None,
) -> Dict[str, Any]:
    task = resolve_task(task_ref, root)
    run_dir = run_dir.resolve()
    if not run_dir.is_dir():
        raise ValueError(f"Run directory does not exist: {run_dir}")

    run_metadata: Dict[str, Any] = {}
    run_metadata_path = run_dir / ".deepee" / "run.json"
    if run_metadata_path.is_file():
        with run_metadata_path.open("r", encoding="utf-8") as handle:
            run_metadata = json.load(handle)
    agent = run_metadata.get("agent") or {}
    verification_work_dir = Path(
        os.environ.get("DEEPEE_VERIFICATION_WORKDIR", str(run_dir / ".deepee" / "verification"))
    ).expanduser().resolve()
    verification_work_dir.mkdir(parents=True, exist_ok=True)
    options = {
        "allow_missing_tools": allow_missing_tools,
        "timeout_seconds": task.manifest.get("default_timeout_seconds", 180),
        "agent": agent,
        "work_dir": verification_work_dir,
    }

    results: List[Dict[str, Any]] = []
    failures: List[str] = []
    for check in task.manifest.get("checks") or []:
        check_type = str(check.get("type") or "")
        name = str(check.get("name") or check_type)
        handler = CHECKS.get(check_type)
        if handler is None:
            check_result = {
                "name": name,
                "type": check_type,
                "passed": False,
                "score": 0.0,
                "message": f"Unknown check type: {check_type}",
                "details": {},
                "required_failed": True,
                "skipped": False,
            }
        else:
            check_result = handler(check, task, run_dir, options)
        if not check_result.get("passed"):
            failures.append(name)
        results.append(check_result)

    automated_run = bool((agent.get("runner") or {}).get("command"))
    if automated_run and run_metadata.get("status") != "completed":
        failures.append("agent_run_completed")
    failures = list(dict.fromkeys(failures))
    passed = bool(results) and not failures

    payload: Dict[str, Any] = {
        "schema_version": "1.0",
        "task_id": task.id,
        "suite": task.suite,
        "agent": {
            "id": run_metadata.get("agent_id") or agent.get("id"),
            "display_name": agent.get("display_name"),
            "system": agent.get("system"),
            "model": agent.get("model"),
            "effort": agent.get("effort"),
            "tool_profile": agent.get("tool_profile"),
        },
        "run_dir": str(run_dir),
        "score": 1.0 if passed else 0.0,
        "passed": passed,
        "publishable": bool(os.environ.get("DEEPEE_VERIFICATION_CONTAINER") == "1" and not allow_missing_tools),
        "failures": failures,
        "checks": results,
        "metadata": {
            "verified_at": utc_timestamp(),
            "python": platform.python_version(),
            "platform": platform.platform(),
            "hashes": {
                "task": _task_hash(task),
                "benchmark": _benchmark_hash(task.path.parents[2]),
                "artifacts": _artifacts_hash(run_dir),
                "submission": _submission_hash(task, run_dir),
            },
            "benchmark_task_ids": sorted(item.id for item in iter_tasks(task.path.parents[2])),
            "tool_versions": _tool_versions(),
            "run": {
                "created_at": run_metadata.get("created_at"),
                "run_id": run_metadata.get("run_id"),
                "status": run_metadata.get("status"),
                "command": run_metadata.get("command"),
                "agent_cli_version": run_metadata.get("agent_cli_version"),
                "agent_container_image_id": run_metadata.get("agent_container_image_id"),
                "configured_verification_container_image_id": run_metadata.get("verification_container_image_id"),
                "agent_config_hash": run_metadata.get("agent_config_hash"),
                "prompt_hash": run_metadata.get("prompt_hash"),
                "wall_time_seconds": run_metadata.get("wall_time_seconds"),
                "usage": run_metadata.get("usage", {}),
                "returncode": run_metadata.get("returncode"),
            },
        },
    }
    if output:
        write_json(output, payload)
    return payload
