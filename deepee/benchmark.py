from __future__ import annotations

import re
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional

from .archive import package_run
from .config import repo_root, write_json
from .container import verify_task_in_container
from .lint import lint_tasks
from .report import collect_results
from .runner import prepare_run, run_agent
from .task import iter_tasks, resolve_task
from .verifier import verify_task


def _safe_name(value: str) -> str:
    return re.sub(r"[^A-Za-z0-9_.-]+", "-", value).strip("-") or "run"


def _task_refs(task_refs: Optional[Iterable[str]], all_tasks: bool, root: Optional[Path]) -> List[str]:
    refs = list(task_refs or [])
    if all_tasks:
        refs.extend(task.id for task in iter_tasks(root))
    seen = set()
    unique = []
    for ref in refs:
        if ref in seen:
            continue
        seen.add(ref)
        unique.append(ref)
    if not unique:
        raise ValueError("Select at least one task with --task or use --all-tasks")
    return unique


def _score_output_path(results_dir: Path, metadata: Dict[str, Any]) -> Path:
    run_id = _safe_name(str(metadata.get("run_id") or "run"))
    agent_id = _safe_name(str(metadata.get("agent_id") or "agent"))
    task_id = _safe_name(str(metadata.get("task_id") or "task"))
    return results_dir / f"{run_id}__{agent_id}__{task_id}.json"


def run_benchmark_suite(
    agent_configs: Iterable[Path],
    task_refs: Optional[Iterable[str]] = None,
    all_tasks: bool = False,
    runs_root: Optional[Path] = None,
    results_dir: Optional[Path] = None,
    allow_missing_tools: bool = False,
    prepare_only: bool = False,
    update_report: bool = True,
    verification_image: Optional[str] = None,
    root: Optional[Path] = None,
) -> Dict[str, Any]:
    lint = lint_tasks(root)
    if not lint["ok"]:
        return {"ok": False, "stage": "lint", "lint": lint, "runs": []}

    results_dir = results_dir or (repo_root() / "results" / "scored")
    results_dir.mkdir(parents=True, exist_ok=True)
    runs: List[Dict[str, Any]] = []
    refs = _task_refs(task_refs, all_tasks, root)

    for agent_config in agent_configs:
        for task_ref in refs:
            task = resolve_task(task_ref, root)
            if prepare_only:
                metadata = prepare_run(agent_config, task.id, runs_root, root)
            else:
                metadata = run_agent(agent_config, task.id, runs_root, root)

            entry: Dict[str, Any] = {
                "agent_config": str(agent_config),
                "agent_id": metadata.get("agent_id"),
                "task_id": task.id,
                "run_dir": metadata.get("run_dir"),
                "status": metadata.get("status", "prepared" if prepare_only else "unknown"),
                "verified": False,
            }

            if prepare_only or not metadata.get("command"):
                entry["next_step"] = "Populate artifacts, then run deepee verify against run_dir."
                runs.append(entry)
                continue

            output = _score_output_path(results_dir, metadata)
            container = metadata.get("container") or {}
            image = verification_image or container.get("verification_image")
            if image:
                score = verify_task_in_container(
                    task.id,
                    Path(str(metadata["run_dir"])),
                    image=str(image),
                    output=output,
                    allow_missing_tools=allow_missing_tools,
                    engine=str(container.get("engine", "docker")),
                )
            else:
                score = verify_task(
                    task.id,
                    Path(str(metadata["run_dir"])),
                    output=output,
                    allow_missing_tools=allow_missing_tools,
                    root=root,
                )
            entry.update(
                {
                    "verified": True,
                    "score": score["score"],
                    "passed": score["passed"],
                    "score_file": str(output),
                }
            )
            archive_name = output.with_suffix(".zip").name
            archive_output = results_dir.parent / "artifacts" / archive_name
            archive = package_run(Path(str(metadata["run_dir"])), archive_output)
            score.setdefault("metadata", {})["evidence_archive"] = archive
            write_json(output, score)
            entry["evidence_archive"] = archive
            runs.append(entry)

    report = None
    if update_report:
        report = collect_results(results_dir)

    return {
        "ok": True,
        "stage": "complete",
        "lint": lint,
        "runs": runs,
        "report": report,
    }
