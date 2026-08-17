from __future__ import annotations

import argparse
import shutil
import tempfile
from pathlib import Path
from typing import Any, Dict, Iterable, Optional

from deepee.config import write_json
from deepee.container import verify_task_in_container
from deepee.task import Task, iter_tasks
from deepee.verifier import verify_task
from validation.reference import ROOT, assemble_reference_run


TOOL_DEPENDENT_CHECKS = {
    "firmware_build",
    "kicad_drc",
    "kicad_erc",
    "kicad_netlist_contract",
}


def _first_existing(run_dir: Path, patterns: Iterable[str]) -> Optional[Path]:
    for pattern in patterns:
        matches = sorted(run_dir.glob(str(pattern)))
        if matches:
            return matches[0]
    return None


def _remove(path: Path) -> None:
    if path.is_dir():
        shutil.rmtree(path)
    elif path.exists():
        path.unlink()


def _overlay_starter_path(task: Task, run_dir: Path, relative: str) -> bool:
    source = task.starter_path / relative
    destination = run_dir / relative
    if not source.exists():
        _remove(destination)
        return False
    destination.parent.mkdir(parents=True, exist_ok=True)
    if source.is_dir():
        shutil.copytree(source, destination, dirs_exist_ok=True)
    else:
        shutil.copy2(source, destination)
    return True


def mutate_requirement(task: Task, requirement: Dict[str, Any], run_dir: Path) -> Dict[str, Any]:
    check_name = str(requirement["check"])
    check = next(
        item for item in task.manifest["checks"]
        if str(item.get("name") or item.get("type")) == check_name
    )
    check_type = str(check["type"])
    details: Dict[str, Any] = {"check": check_name, "check_type": check_type}

    if check_type == "artifact_presence":
        artifact = task.manifest["required_artifacts"][0]
        path = _first_existing(run_dir, [str(artifact["path"])])
        if path is None:
            raise RuntimeError(f"Reference artifact is already missing for {task.id}: {artifact['path']}")
        _remove(path)
        details["mutation"] = f"removed {path.relative_to(run_dir)}"
        return details

    if check_type == "starter_integrity":
        path = _first_existing(run_dir, check.get("protected_globs") or [])
        if path is None or not path.is_file():
            raise RuntimeError(f"No protected file found for {task.id}:{check_name}")
        with path.open("ab") as handle:
            handle.write(b"\n# deepee adequacy mutant\n")
        details["mutation"] = f"modified protected file {path.relative_to(run_dir)}"
        return details

    if check_type == "c_unit_tests":
        changed = []
        for relative in check.get("sources") or []:
            if _overlay_starter_path(task, run_dir, str(relative)):
                changed.append(str(relative))
        if not changed:
            raise RuntimeError(f"No starter source available for {task.id}:{check_name}")
        details["mutation"] = "restored buggy starter implementation"
        details["paths"] = changed
        return details

    if check_type == "firmware_build":
        root = str(check.get("root") or ".")
        required = [f"{root}/{path}" for path in check.get("required_files") or []]
        candidates = [run_dir / path for path in required]
        source = next((path for path in candidates if path.is_file() and path.suffix in {".c", ".cc", ".cpp"}), None)
        if source is None:
            raise RuntimeError(f"No firmware source available for {task.id}:{check_name}")
        with source.open("a", encoding="utf-8") as handle:
            handle.write("\n#error deepee adequacy build mutant\n")
        details["mutation"] = f"injected compile error into {source.relative_to(run_dir)}"
        return details

    if check_type in {"kicad_schematic_structure", "kicad_netlist_contract", "kicad_erc"}:
        relative = str(check.get("schematic") or "")
        target = run_dir / relative if relative else _first_existing(run_dir, ["artifacts/**/*.kicad_sch"])
        if target is None:
            raise RuntimeError(f"No schematic found for {task.id}:{check_name}")
        if check_type == "kicad_erc":
            target.write_text("(kicad_sch\n", encoding="utf-8")
            details["mutation"] = f"corrupted S-expression in {target.relative_to(run_dir)}"
        else:
            component = (check.get("components") or [None])[0]
            expected_value = str((component or {}).get("value") or "")
            marker = f'(property "Value" "{expected_value}"'
            text = target.read_text(encoding="utf-8")
            if not expected_value or marker not in text:
                _overlay_starter_path(task, run_dir, str(target.relative_to(run_dir)))
                details["mutation"] = f"restored incomplete starter schematic {target.relative_to(run_dir)}"
            else:
                target.write_text(text.replace(marker, '(property "Value" "DEEPEE_MUTANT"'), encoding="utf-8")
                details["mutation"] = f"changed declared component value in {target.relative_to(run_dir)}"
        return details

    if check_type in {"kicad_pcb_structure", "kicad_drc"}:
        relative = str(check.get("board") or "")
        target = run_dir / relative if relative else _first_existing(run_dir, ["artifacts/**/*.kicad_pcb"])
        if target is None:
            raise RuntimeError(f"No board found for {task.id}:{check_name}")
        if check_type == "kicad_drc" and task.suite == "pcb-design":
            target.write_text("(kicad_pcb\n", encoding="utf-8")
            details["mutation"] = f"corrupted S-expression in {target.relative_to(run_dir)}"
        else:
            _overlay_starter_path(task, run_dir, str(target.relative_to(run_dir)))
            details["mutation"] = f"restored incomplete starter board {target.relative_to(run_dir)}"
        return details

    raise RuntimeError(f"No adequacy mutation is defined for check type: {check_type}")


def _verify(task: Task, run_dir: Path, image: Optional[str], engine: str) -> Dict[str, Any]:
    if image:
        return verify_task_in_container(task.id, run_dir, image=image, engine=engine)
    return verify_task(task.id, run_dir, allow_missing_tools=True, root=ROOT)


def validate_adequacy(
    image: Optional[str] = None,
    engine: str = "docker",
    task_refs: Optional[Iterable[str]] = None,
) -> Dict[str, Any]:
    task_results = []
    requested = set(task_refs or [])
    with tempfile.TemporaryDirectory(prefix="deepee-adequacy-") as temporary:
        base = Path(temporary)
        for task in iter_tasks(ROOT):
            if requested and task.id not in requested:
                continue
            reference_dir = assemble_reference_run(task, base / task.id / "reference")
            reference = _verify(task, reference_dir, image, engine)
            reference_supported = [
                item for item in reference.get("requirements") or []
                if not item.get("skipped")
            ]
            reference_passed = all(item.get("passed") for item in reference_supported)
            mutants = []
            for requirement in task.manifest["requirements"]:
                check = next(
                    item for item in task.manifest["checks"]
                    if str(item.get("name") or item.get("type")) == str(requirement["check"])
                )
                if image is None and check["type"] in TOOL_DEPENDENT_CHECKS:
                    mutants.append({
                        "requirement_id": requirement["id"],
                        "supported": False,
                        "killed": None,
                        "reason": "exact toolchain required",
                    })
                    continue
                mutant_dir = assemble_reference_run(
                    task,
                    base / task.id / "mutants" / str(requirement["id"]),
                )
                mutation = mutate_requirement(task, requirement, mutant_dir)
                score = _verify(task, mutant_dir, image, engine)
                outcome = next(
                    item for item in score.get("requirements") or []
                    if item["id"] == requirement["id"]
                )
                mutants.append({
                    "requirement_id": requirement["id"],
                    "supported": not outcome.get("skipped"),
                    "killed": not outcome.get("passed") and not outcome.get("skipped"),
                    "decision_hash": (score.get("metadata") or {}).get("hashes", {}).get("decision"),
                    **mutation,
                })
            task_passed = reference_passed and all(
                item["killed"] for item in mutants if item["supported"]
            )
            task_results.append({
                "task_id": task.id,
                "reference_passed": reference_passed,
                "reference_decision_hash": (reference.get("metadata") or {}).get("hashes", {}).get("decision"),
                "passed": task_passed,
                "mutants": mutants,
            })
            print(f"{'PASS' if task_passed else 'FAIL'} {task.id} ({sum(1 for item in mutants if item['supported'])} mutants)", flush=True)

    supported = [
        mutant
        for task in task_results
        for mutant in task["mutants"]
        if mutant["supported"]
    ]
    killed = sum(1 for mutant in supported if mutant["killed"])
    return {
        "schema_version": "1.0",
        "exact_toolchain": bool(image),
        "passed": all(task["passed"] for task in task_results) and killed == len(supported),
        "tasks": task_results,
        "summary": {
            "tasks": len(task_results),
            "supported_mutants": len(supported),
            "killed_mutants": killed,
            "mutation_score": killed / len(supported) if supported else 0.0,
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Prove that DeepEE validators reject one mutant per critical requirement")
    parser.add_argument("--container-image")
    parser.add_argument("--engine", default="docker")
    parser.add_argument("--task", action="append", dest="tasks")
    parser.add_argument("--output", type=Path, default=ROOT / "results" / "validation-adequacy.json")
    args = parser.parse_args()
    payload = validate_adequacy(args.container_image, args.engine, args.tasks)
    write_json(args.output, payload)
    print(
        f"Killed {payload['summary']['killed_mutants']}/{payload['summary']['supported_mutants']} supported mutants",
        flush=True,
    )
    return 0 if payload["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
