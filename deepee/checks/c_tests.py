from __future__ import annotations

import re
from pathlib import Path
from typing import Any, Dict, List

from .common import command_available, resolve_run_path, result, run_subprocess


def _task_path(task, value: str) -> Path:
    path = Path(value)
    return path if path.is_absolute() else task.path / path


def run_c_unit_tests(check: Dict[str, Any], task, run_dir: Path, options: Dict[str, Any]) -> Dict[str, Any]:
    compiler = str(check.get("compiler", "cc"))
    if not command_available(compiler):
        skipped = bool(options.get("allow_missing_tools"))
        return result(
            check.get("name", "c_unit_tests"),
            "c_unit_tests",
            0.0,
            f"C compiler not available: {compiler}",
            required_failed=bool(check.get("required", True) and not skipped),
            skipped=skipped,
        )

    run_sources = [resolve_run_path(run_dir, str(value)) for value in check.get("sources") or []]
    test_sources = [_task_path(task, str(value)) for value in check.get("test_sources") or []]
    missing = [str(path) for path in run_sources + test_sources if not path.is_file()]
    if missing:
        return result(check.get("name", "c_unit_tests"), "c_unit_tests", 0.0, "C test inputs are missing", {"missing": missing}, required_failed=check.get("required", True))

    include_args: List[str] = []
    for value in check.get("include_dirs") or []:
        raw = str(value)
        if raw.startswith("task:"):
            path = _task_path(task, raw[len("task:"):])
        else:
            path = resolve_run_path(run_dir, raw)
        include_args.extend(["-I", str(path)])

    safe_name = re.sub(r"[^A-Za-z0-9_.-]", "-", str(check.get("name", "c-unit-tests")))
    work_dir = Path(options.get("work_dir") or (run_dir / ".deepee" / "verification"))
    output = work_dir / "build" / safe_name
    output.parent.mkdir(parents=True, exist_ok=True)
    compile_command = [
        compiler,
        "-std=c99",
        "-Wall",
        "-Wextra",
        "-Werror",
        *[str(flag) for flag in check.get("cflags") or []],
        *include_args,
        *[str(path) for path in run_sources + test_sources],
        *[str(flag) for flag in check.get("ldflags") or []],
        "-o",
        str(output),
    ]
    timeout = int(check.get("timeout_seconds", options.get("timeout_seconds", 120)))
    compile_run = run_subprocess(compile_command, run_dir, timeout)
    if compile_run["returncode"] != 0:
        return result(check.get("name", "c_unit_tests"), "c_unit_tests", 0.0, "Verifier-owned C tests did not compile", {"compile": {"command": compile_command, **compile_run}}, required_failed=check.get("required", True))

    test_run = run_subprocess([str(output)], run_dir, timeout)
    passed = test_run["returncode"] == 0
    return result(
        check.get("name", "c_unit_tests"),
        "c_unit_tests",
        1.0 if passed else 0.0,
        "Verifier-owned C tests passed" if passed else "Verifier-owned C tests failed",
        {"compile": {"command": compile_command, **compile_run}, "test": test_run},
        required_failed=bool(check.get("required", True) and not passed),
    )
