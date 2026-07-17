from __future__ import annotations

import argparse
import shutil
import tempfile
from pathlib import Path
from typing import Any, Dict

from deepee.container import verify_task_in_container
from deepee.task import Task, iter_tasks


ROOT = Path(__file__).resolve().parents[1]
SOLUTIONS = ROOT / "validation" / "solutions"


def assemble_reference_run(task: Task, destination: Path) -> Path:
    destination.mkdir(parents=True, exist_ok=True)
    if task.starter_path.is_dir():
        shutil.copytree(task.starter_path, destination, dirs_exist_ok=True)
    solution = SOLUTIONS / task.id
    if not solution.is_dir():
        raise RuntimeError(f"Missing reference solution for {task.id}: {solution}")
    shutil.copytree(solution, destination, dirs_exist_ok=True)
    return destination


def validate_reference_solutions(image: str, engine: str = "docker") -> Dict[str, Dict[str, Any]]:
    tasks = list(iter_tasks(ROOT))
    task_ids = {task.id for task in tasks}
    solution_ids = {path.name for path in SOLUTIONS.iterdir() if path.is_dir()}
    if task_ids != solution_ids:
        missing = sorted(task_ids - solution_ids)
        extra = sorted(solution_ids - task_ids)
        raise RuntimeError(f"Reference-solution coverage mismatch; missing={missing}, extra={extra}")

    scores: Dict[str, Dict[str, Any]] = {}
    with tempfile.TemporaryDirectory(prefix="deepee-reference-") as temporary:
        base = Path(temporary)
        for task in tasks:
            run_dir = assemble_reference_run(task, base / task.id)
            score = verify_task_in_container(task.id, run_dir, image=image, engine=engine)
            scores[task.id] = score
            state = "PASS" if score.get("passed") else "FAIL"
            print(f"{state} {task.id}", flush=True)

    failures = {
        task_id: score
        for task_id, score in scores.items()
        if not score.get("passed") or not score.get("publishable")
    }
    if failures:
        details = []
        for task_id, score in failures.items():
            failed_checks = [
                f"{check.get('name')}: {check.get('message')}"
                for check in score.get("checks") or []
                if not check.get("passed")
            ]
            details.append(f"{task_id}: {'; '.join(failed_checks) or score.get('failures')}")
        raise RuntimeError("Reference validation failed:\n" + "\n".join(details))
    return scores


def main() -> int:
    parser = argparse.ArgumentParser(description="Verify every private reference solution in the release image")
    parser.add_argument("--container-image", required=True)
    parser.add_argument("--engine", default="docker")
    args = parser.parse_args()
    scores = validate_reference_solutions(args.container_image, args.engine)
    print(f"Validated {len(scores)} reference submissions")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
