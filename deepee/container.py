from __future__ import annotations

import json
import os
import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import Any, Dict, Optional

from .config import write_json


def _image_id(engine: str, image: str) -> str:
    completed = subprocess.run(
        [engine, "image", "inspect", "--format", "{{.Id}}", image],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        timeout=30,
    )
    if completed.returncode != 0:
        raise RuntimeError(f"Verification image is unavailable: {image}\n{completed.stdout[-2000:]}")
    return (completed.stdout or "").strip()


def _engine_version(engine: str) -> str:
    completed = subprocess.run(
        [engine, "--version"],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        timeout=10,
    )
    return (completed.stdout or "").strip() if completed.returncode == 0 else ""


def verify_task_in_container(
    task_ref: str,
    run_dir: Path,
    image: str,
    output: Optional[Path] = None,
    allow_missing_tools: bool = False,
    engine: str = "docker",
) -> Dict[str, Any]:
    if not shutil.which(engine):
        raise RuntimeError(f"Container engine is unavailable: {engine}")
    run_dir = run_dir.resolve()
    if not run_dir.is_dir():
        raise ValueError(f"Run directory does not exist: {run_dir}")
    image_id = _image_id(engine, image)
    with tempfile.TemporaryDirectory(prefix="deepee-verification-") as temporary:
        verification_root = Path(temporary).resolve()
        verification_root.chmod(0o777)
        work_dir = verification_root / "work"
        work_dir.mkdir()
        work_dir.chmod(0o777)
        host_score = verification_root / "score.json"
        command = [
            engine,
            "run",
            "--rm",
            "--init",
            "--network",
            "none",
            "--cap-drop",
            "ALL",
            "--security-opt",
            "no-new-privileges",
            "--pids-limit",
            "512",
            "--cpus",
            "4",
            "--memory",
            "8g",
            "--user",
            "benchmark",
            "--workdir",
            "/submission",
            "--mount",
            f"type=bind,src={run_dir},dst=/submission,readonly",
            "--mount",
            f"type=bind,src={verification_root},dst=/verification",
            "--env",
            "DEEPEE_ROOT=/opt/deepee",
            "--env",
            "DEEPEE_VERIFICATION_CONTAINER=1",
            "--env",
            "DEEPEE_VERIFICATION_WORKDIR=/verification/work",
            "--env",
            "HOME=/home/benchmark",
            "--env",
            "XDG_CONFIG_HOME=/home/benchmark/.config",
            "--env",
            "PLATFORMIO_SETTING_ENABLE_TELEMETRY=no",
            "--env",
            "PLATFORMIO_SETTING_CHECK_PLATFORMIO_INTERVAL=0",
            "--tmpfs",
            "/tmp:rw,nosuid,nodev,size=1g",
            image,
            "sh",
            "-c",
            (
                'verification_status=0; "$@" || verification_status=$?; '
                "find /verification/work -mindepth 1 -exec chmod a+rwX {} +; "
                "chmod a+rw /verification/score.json 2>/dev/null || true; "
                'exit "$verification_status"'
            ),
            "deepee-verifier",
            "deepee",
            "verify",
            "--task",
            task_ref,
            "--run-dir",
            "/submission",
            "--output",
            "/verification/score.json",
        ]
        if allow_missing_tools:
            command.append("--allow-missing-tools")
        completed = subprocess.run(
            command,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            timeout=1800,
        )
        if completed.returncode not in {0, 1} or not host_score.is_file():
            raise RuntimeError(f"Containerized verification failed ({completed.returncode}):\n{(completed.stdout or '')[-12000:]}")
        with host_score.open("r", encoding="utf-8") as handle:
            payload = json.load(handle)

        evidence_dir = run_dir / ".deepee" / "verification"
        if evidence_dir.exists():
            shutil.rmtree(evidence_dir)
        if work_dir.exists():
            shutil.copytree(work_dir, evidence_dir)
            for path in evidence_dir.rglob("*"):
                if path.is_file():
                    os.chmod(path, 0o644)
    payload["run_dir"] = str(run_dir)
    metadata = payload.setdefault("metadata", {})
    metadata["verification_container"] = {
        "engine": engine,
        "engine_version": _engine_version(engine),
        "image": image,
        "image_id": image_id,
        "submission_read_only": True,
        "evidence_dir": str(run_dir / ".deepee" / "verification"),
    }
    if output:
        write_json(output, payload)
    return payload
