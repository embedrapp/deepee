from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from jsonschema import validate

from .config import repo_root, utc_timestamp, write_json


def _result_row(path: Path, payload: Dict[str, Any]) -> Dict[str, Any]:
    required = ("task_id", "suite", "agent", "score", "passed", "metadata")
    missing = [key for key in required if key not in payload]
    if missing:
        raise ValueError(f"Invalid score file {path}: missing {', '.join(missing)}")
    metadata = payload.get("metadata") or {}
    run = metadata.get("run") or {}
    return {
        "task_id": payload["task_id"],
        "suite": payload["suite"],
        "agent": payload.get("agent", {}),
        "score": payload["score"],
        "quality_score": payload.get("quality_score"),
        "score_vector": payload.get("score_vector", {}),
        "critical_requirement_failures": payload.get("critical_requirement_failures", []),
        "passed": bool(payload["passed"]),
        "publishable": bool(payload.get("publishable")),
        "run_id": run.get("run_id"),
        "created_at": run.get("created_at"),
        "wall_time_seconds": run.get("wall_time_seconds"),
        "usage": run.get("usage", {}),
        "cost_estimate": run.get("cost_estimate", {}),
        "network_policy": run.get("network_policy", {}),
        "agent_cli_version": run.get("agent_cli_version"),
        "agent_container_image_id": run.get("agent_container_image_id"),
        "verification_container": metadata.get("verification_container", {}),
        "evidence_archive": metadata.get("evidence_archive", {}),
        "run_dir": payload.get("run_dir"),
        "hashes": metadata.get("hashes", {}),
        "benchmark_task_ids": sorted(str(value) for value in metadata.get("benchmark_task_ids", [])),
        "agent_config_hash": run.get("agent_config_hash"),
        "result_file": str(path),
    }


def _cohort_key(row: Dict[str, Any]) -> Tuple[str, ...]:
    agent = row.get("agent") or {}
    hashes = row.get("hashes") or {}
    return (
        str(agent.get("id") or "unknown"),
        str(agent.get("system") or ""),
        str(agent.get("model") or ""),
        str(agent.get("effort") or ""),
        str(agent.get("tool_profile") or ""),
        str(row.get("agent_config_hash") or ""),
        str(hashes.get("benchmark") or ""),
        str(row.get("agent_container_image_id") or ""),
        str((row.get("verification_container") or {}).get("image_id") or ""),
    )


def _cohort_id(key: Tuple[str, ...]) -> str:
    digest = hashlib.sha256(json.dumps(key, separators=(",", ":")).encode("utf-8")).hexdigest()[:12]
    return f"{key[0]}@{digest}"


def _attempt_key(row: Dict[str, Any]) -> Tuple[str, ...]:
    return (*_cohort_key(row), str(row.get("task_id")))


def collect_results(results_dir: Optional[Path] = None, output: Optional[Path] = None) -> Dict[str, Any]:
    root = repo_root()
    results_dir = results_dir or (root / "results" / "scored")
    rows: List[Dict[str, Any]] = []
    for path in sorted(results_dir.glob("*.json")):
        with path.open("r", encoding="utf-8") as handle:
            payload = json.load(handle)
        rows.append(_result_row(path, payload))

    rows.sort(key=lambda row: (str(row.get("created_at") or ""), str(row.get("run_id") or ""), row["result_file"]))
    attempts: Dict[Tuple[str, ...], int] = {}
    first_attempts: List[Dict[str, Any]] = []
    for row in rows:
        if not row["publishable"]:
            row["attempt_index"] = None
            row["counts_for_pass_at_1"] = False
            continue
        key = _attempt_key(row)
        attempts[key] = attempts.get(key, 0) + 1
        row["attempt_index"] = attempts[key]
        row["counts_for_pass_at_1"] = attempts[key] == 1
        if attempts[key] == 1:
            first_attempts.append(row)

    by_suite: Dict[str, Dict[str, Any]] = {}
    cohort_rows: Dict[Tuple[str, ...], List[Dict[str, Any]]] = {}
    for row in first_attempts:
        suite = row.get("suite") or "unknown"
        bucket = by_suite.setdefault(str(suite), {"tasks": 0, "passed_at_1": 0})
        bucket["tasks"] += 1
        bucket["passed_at_1"] += 1 if row.get("passed") else 0
        cohort_rows.setdefault(_cohort_key(row), []).append(row)

    for bucket in by_suite.values():
        bucket["pass_at_1"] = bucket["passed_at_1"] / bucket["tasks"] if bucket["tasks"] else 0.0

    by_agent: Dict[str, Dict[str, Any]] = {}
    for cohort_key, cohort_first_attempts in cohort_rows.items():
        representative = cohort_first_attempts[0]
        attempted = {str(row["task_id"]) for row in cohort_first_attempts}
        declared_task_sets = {
            tuple(row.get("benchmark_task_ids") or [])
            for row in cohort_first_attempts
        }
        required = set().union(*(set(task_ids) for task_ids in declared_task_sets))
        missing = sorted(required - attempted)
        complete = bool(required) and not missing and len(declared_task_sets) == 1
        passed_at_1 = sum(1 for row in cohort_first_attempts if row.get("passed"))
        by_agent[_cohort_id(cohort_key)] = {
            "agent": representative.get("agent") or {},
            "agent_config_hash": representative.get("agent_config_hash"),
            "network_policy": representative.get("network_policy") or {},
            "benchmark_hash": (representative.get("hashes") or {}).get("benchmark"),
            "agent_container_image_id": representative.get("agent_container_image_id"),
            "verification_container_image_id": (representative.get("verification_container") or {}).get("image_id"),
            "tasks_attempted": len(attempted),
            "tasks_required": len(required),
            "required_task_ids": sorted(required),
            "missing_task_ids": missing,
            "task_list_consistent": len(declared_task_sets) == 1,
            "passed_at_1": passed_at_1,
            "complete": complete,
            "pass_at_1": (passed_at_1 / len(required)) if complete else None,
            "estimated_api_cost_usd": round(
                sum(float((row.get("cost_estimate") or {}).get("total_usd") or 0) for row in cohort_first_attempts),
                6,
            ),
        }

    report = {
        "schema_version": "2.0",
        "generated_at": utc_timestamp(),
        "total_runs": len(rows),
        "total_publishable_runs": sum(1 for row in rows if row["publishable"]),
        "total_first_attempts": len(first_attempts),
        "total_estimated_api_cost_usd": round(
            sum(float((row.get("cost_estimate") or {}).get("total_usd") or 0) for row in rows),
            6,
        ),
        "by_suite": by_suite,
        "by_agent": by_agent,
        "runs": rows,
    }
    schema_path = root / "leaderboard" / "schema.json"
    if schema_path.is_file():
        with schema_path.open("r", encoding="utf-8") as handle:
            validate(instance=report, schema=json.load(handle))
    write_json(output or (root / "leaderboard" / "results.json"), report)
    return report
