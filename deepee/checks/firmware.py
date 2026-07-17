from __future__ import annotations

import shutil
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from .common import command_available, resolve_run_path, result, run_subprocess


def _detect_build(root: Path, check: Dict[str, Any]) -> Optional[Tuple[str, List[List[str]]]]:
    if (root / "platformio.ini").exists():
        return "platformio", [["pio", "run"]]
    return None


def run_firmware_build(check: Dict[str, Any], task, run_dir: Path, options: Dict[str, Any]) -> Dict[str, Any]:
    root = resolve_run_path(run_dir, str(check.get("root", "artifacts/firmware")))
    if not root.exists():
        return result(
            check.get("name", "firmware_build"),
            "firmware_build",
            0.0,
            f"Firmware root does not exist: {root}",
            required_failed=check.get("required", True),
        )

    detected = _detect_build(root, check)
    if not detected:
        return result(
            check.get("name", "firmware_build"),
            "firmware_build",
            0.0,
            "No supported firmware build file found",
            {"root": str(root.relative_to(run_dir))},
            required_failed=check.get("required", True),
        )

    build_system, commands = detected
    allowed = [str(value) for value in check.get("allowed_build_systems") or []]
    if allowed and build_system not in allowed:
        return result(
            check.get("name", "firmware_build"),
            "firmware_build",
            0.0,
            f"Detected build system {build_system}; expected one of {allowed}",
            required_failed=check.get("required", True),
        )
    missing_files = [str(value) for value in check.get("required_files") or [] if not (root / str(value)).is_file()]
    if missing_files:
        return result(
            check.get("name", "firmware_build"),
            "firmware_build",
            0.0,
            "Required firmware source files are missing",
            {"missing": missing_files},
            required_failed=check.get("required", True),
        )

    timeout_seconds = int(check.get("timeout_seconds", options.get("timeout_seconds", 180)))
    work_dir = Path(options.get("work_dir") or (run_dir / ".deepee" / "verification"))
    build_root = work_dir / "firmware" / str(check.get("name", "firmware_build"))
    if build_root.exists():
        shutil.rmtree(build_root)
    shutil.copytree(root, build_root)
    runs = []
    for command in commands:
        if not command_available(command[0]):
            skipped = bool(options.get("allow_missing_tools"))
            return result(
                check.get("name", "firmware_build"),
                "firmware_build",
                0.0,
                f"Firmware tool not available: {command[0]}",
                {"command": command, "root": str(root)},
                required_failed=not skipped,
                skipped=skipped,
            )
        proc = run_subprocess(command, build_root, timeout_seconds)
        runs.append({"command": command, **proc})
        if proc["returncode"] != 0:
            return result(
                check.get("name", "firmware_build"),
                "firmware_build",
                0.0,
                f"Firmware build failed: {' '.join(command)}",
                {"runs": runs},
                required_failed=check.get("required", True),
            )

    output_globs = [str(value) for value in check.get("output_globs") or []]
    missing_outputs = [pattern for pattern in output_globs if not any(path.is_file() for path in build_root.glob(pattern))]
    if missing_outputs:
        return result(
            check.get("name", "firmware_build"),
            "firmware_build",
            0.0,
            "Firmware build produced no required output",
            {"build_system": build_system, "runs": runs, "missing_outputs": missing_outputs},
            required_failed=check.get("required", True),
        )

    return result(
        check.get("name", "firmware_build"),
        "firmware_build",
        1.0,
        "Firmware build completed",
        {"build_system": build_system, "runs": runs},
    )
