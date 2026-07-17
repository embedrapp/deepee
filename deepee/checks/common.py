from __future__ import annotations

import os
import shutil
import subprocess
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional


def result(
    name: str,
    check_type: str,
    score: float,
    message: str,
    details: Optional[Dict[str, Any]] = None,
    required_failed: bool = False,
    skipped: bool = False,
) -> Dict[str, Any]:
    score = max(0.0, min(1.0, float(score)))
    return {
        "name": name,
        "type": check_type,
        "passed": score >= 1.0 and not required_failed and not skipped,
        "score": score,
        "message": message,
        "details": details or {},
        "required_failed": required_failed,
        "skipped": skipped,
    }


def resolve_run_path(run_dir: Path, relative: str) -> Path:
    path = Path(relative)
    base = run_dir.resolve()
    candidate = path.resolve() if path.is_absolute() else (base / path).resolve()
    try:
        candidate.relative_to(base)
    except ValueError as exc:
        raise ValueError(f"Path escapes run directory: {relative}") from exc
    return candidate


def command_available(command: str) -> bool:
    return shutil.which(command) is not None


def run_subprocess(
    command: List[str],
    cwd: Path,
    timeout_seconds: int,
    env: Optional[Dict[str, str]] = None,
) -> Dict[str, Any]:
    merged_env = os.environ.copy()
    if env:
        merged_env.update(env)
    try:
        completed = subprocess.run(
            command,
            cwd=str(cwd),
            env=merged_env,
            timeout=timeout_seconds,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
        )
        return {
            "returncode": completed.returncode,
            "output": completed.stdout[-12000:],
            "timed_out": False,
        }
    except subprocess.TimeoutExpired as exc:
        output = ""
        if exc.stdout:
            output += str(exc.stdout)
        if exc.stderr:
            output += str(exc.stderr)
        return {
            "returncode": 124,
            "output": output[-12000:],
            "timed_out": True,
        }


def text_files(root: Path, globs: Optional[Iterable[str]] = None) -> Iterable[Path]:
    patterns = list(globs or ["**/*"])
    seen = set()
    for pattern in patterns:
        for path in root.glob(pattern):
            if path in seen or not path.is_file():
                continue
            seen.add(path)
            if path.stat().st_size > 2_000_000:
                continue
            yield path
