from __future__ import annotations

import hashlib
import json
import os
import platform
import re
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


def _stable_fragment(value: Any) -> str:
    fragment = re.sub(r"[^a-z0-9]+", "-", str(value).lower()).strip("-")
    return fragment or "check"


def _requirement_results(task, checks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    by_name = {str(item.get("name") or item.get("type")): item for item in checks}
    declared = task.manifest.get("requirements") or []
    if not declared:
        declared = [
            {
                "id": _stable_fragment(item.get("name") or item.get("type")),
                "description": str(item.get("name") or item.get("type")),
                "layer": "deliverable",
                "critical": True,
                "check": str(item.get("name") or item.get("type")),
            }
            for item in checks
        ]

    results: List[Dict[str, Any]] = []
    for requirement in declared:
        requirement_id = str(requirement["id"])
        check_name = str(requirement["check"])
        check_result = by_name.get(check_name) or {
            "passed": False,
            "score": 0.0,
            "message": f"Mapped check result is missing: {check_name}",
            "details": {},
        }
        subrequirements = []
        for subcheck in (check_result.get("details") or {}).get("subchecks") or []:
            name = str(subcheck.get("name") or "check")
            evidence = {
                key: value
                for key, value in subcheck.items()
                if key not in {"name", "passed"}
            }
            subrequirements.append({
                "id": f"{requirement_id}.{_stable_fragment(name)}",
                "name": name,
                "passed": bool(subcheck.get("passed")),
                "evidence": evidence,
            })
        results.append({
            "id": requirement_id,
            "description": str(requirement.get("description") or requirement_id),
            "layer": str(requirement.get("layer") or "deliverable"),
            "critical": bool(requirement.get("critical", True)),
            "check": check_name,
            "passed": bool(check_result.get("passed")),
            "skipped": bool(check_result.get("skipped")),
            "score": float(check_result.get("score") or 0.0),
            "message": str(check_result.get("message") or ""),
            "subrequirements": subrequirements,
        })
    return results


def _score_vector(requirements: List[Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
    vector: Dict[str, Dict[str, Any]] = {}
    for layer in sorted({str(item["layer"]) for item in requirements}):
        items = [item for item in requirements if item["layer"] == layer]
        passed = sum(1 for item in items if item["passed"])
        vector[layer] = {
            "passed": passed,
            "total": len(items),
            "pass_rate": passed / len(items) if items else 0.0,
        }
    return vector


def _decision_hash(task_id: str, requirements: List[Dict[str, Any]]) -> str:
    decision = {
        "task_id": task_id,
        "requirements": [
            {
                "id": item["id"],
                "critical": item["critical"],
                "passed": item["passed"],
                "skipped": item["skipped"],
                "score": item["score"],
                "subrequirements": [
                    {"id": subitem["id"], "passed": subitem["passed"]}
                    for subitem in item["subrequirements"]
                ],
            }
            for item in requirements
        ],
    }
    encoded = json.dumps(decision, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


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
    requirements = _requirement_results(task, results)
    critical_requirement_failures = [
        item["id"] for item in requirements if item["critical"] and not item["passed"]
    ]
    passed = bool(results) and not failures and not critical_requirement_failures
    quality_score = (
        sum(1.0 for item in requirements if item["passed"]) / len(requirements)
        if requirements
        else 0.0
    )

    payload: Dict[str, Any] = {
        "schema_version": "2.0",
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
        "quality_score": quality_score,
        "passed": passed,
        "publishable": bool(os.environ.get("DEEPEE_VERIFICATION_CONTAINER") == "1" and not allow_missing_tools),
        "failures": failures,
        "critical_requirement_failures": critical_requirement_failures,
        "requirements": requirements,
        "score_vector": _score_vector(requirements),
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
                "decision": _decision_hash(task.id, requirements),
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
                "cost_estimate": run_metadata.get("cost_estimate", {}),
                "network_policy": run_metadata.get("network_policy", {}),
                "returncode": run_metadata.get("returncode"),
            },
        },
    }
    if output:
        write_json(output, payload)
    return payload
