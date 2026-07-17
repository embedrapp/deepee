from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, Optional

from .common import command_available, resolve_run_path, result, run_subprocess


def _first_file(root: Path, suffix: str) -> Optional[Path]:
    matches = sorted(root.glob(f"**/*{suffix}"))
    return matches[0] if matches else None


def run_kicad_erc(check: Dict[str, Any], task, run_dir: Path, options: Dict[str, Any]) -> Dict[str, Any]:
    root = resolve_run_path(run_dir, str(check.get("root", "artifacts")))
    schematic = resolve_run_path(run_dir, str(check["schematic"])) if check.get("schematic") else _first_file(root, ".kicad_sch")
    if not schematic or not schematic.exists():
        return result(
            check.get("name", "kicad_erc"),
            "kicad_erc",
            0.0,
            "No KiCad schematic found",
            {"root": str(root)},
            required_failed=check.get("required", True),
        )
    if not command_available("kicad-cli"):
        skipped = bool(options.get("allow_missing_tools"))
        return result(
            check.get("name", "kicad_erc"),
            "kicad_erc",
            0.0,
            "kicad-cli not available",
            {"schematic": str(schematic)},
            required_failed=not skipped,
            skipped=skipped,
        )

    work_dir = Path(options.get("work_dir") or (run_dir / ".deepee" / "verification"))
    report_path = work_dir / f"{task.id}-erc.rpt"
    report_path.parent.mkdir(parents=True, exist_ok=True)
    command = [
        "kicad-cli",
        "sch",
        "erc",
        "--severity-error",
        "--severity-warning",
        "--exit-code-violations",
        "--output",
        str(report_path),
        str(schematic),
    ]
    proc = run_subprocess(command, run_dir, int(check.get("timeout_seconds", 120)))
    passed = proc["returncode"] == 0
    return result(
        check.get("name", "kicad_erc"),
        "kicad_erc",
        1.0 if passed else 0.0,
        "KiCad ERC passed" if passed else "KiCad ERC failed",
        {"command": command, "report": str(report_path), "run": proc},
        required_failed=check.get("required", True) and not passed,
    )


def run_kicad_drc(check: Dict[str, Any], task, run_dir: Path, options: Dict[str, Any]) -> Dict[str, Any]:
    root = resolve_run_path(run_dir, str(check.get("root", "artifacts")))
    board = resolve_run_path(run_dir, str(check["board"])) if check.get("board") else _first_file(root, ".kicad_pcb")
    if not board or not board.exists():
        return result(
            check.get("name", "kicad_drc"),
            "kicad_drc",
            0.0,
            "No KiCad PCB found",
            {"root": str(root)},
            required_failed=check.get("required", True),
        )
    if not command_available("kicad-cli"):
        skipped = bool(options.get("allow_missing_tools"))
        return result(
            check.get("name", "kicad_drc"),
            "kicad_drc",
            0.0,
            "kicad-cli not available",
            {"board": str(board)},
            required_failed=not skipped,
            skipped=skipped,
        )

    work_dir = Path(options.get("work_dir") or (run_dir / ".deepee" / "verification"))
    report_path = work_dir / f"{task.id}-drc.rpt"
    report_path.parent.mkdir(parents=True, exist_ok=True)
    command = [
        "kicad-cli",
        "pcb",
        "drc",
        "--severity-error",
        "--severity-warning",
        "--exit-code-violations",
        "--refill-zones",
        "--output",
        str(report_path),
        str(board),
    ]
    proc = run_subprocess(command, run_dir, int(check.get("timeout_seconds", 120)))
    passed = proc["returncode"] == 0
    return result(
        check.get("name", "kicad_drc"),
        "kicad_drc",
        1.0 if passed else 0.0,
        "KiCad DRC passed" if passed else "KiCad DRC failed",
        {"command": command, "report": str(report_path), "run": proc},
        required_failed=check.get("required", True) and not passed,
    )
