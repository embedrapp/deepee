from __future__ import annotations

import os
import hashlib
import json
import signal
import shutil
import subprocess
import time
import uuid
from pathlib import Path
from typing import Any, Dict, Optional

import yaml

from .config import load_yaml, read_text_if_exists, repo_root, utc_timestamp, write_json
from .task import resolve_task


def _copy_starter(task_path: Path, run_dir: Path) -> None:
    starter = task_path / "starter"
    if starter.exists():
        for item in starter.iterdir():
            destination = run_dir / item.name
            if item.is_dir():
                shutil.copytree(str(item), str(destination), dirs_exist_ok=True)
            else:
                destination.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(str(item), str(destination))


def _format_command(command: Any, variables: Dict[str, str]) -> Any:
    if isinstance(command, list):
        return [str(part).format(**variables) for part in command]
    return str(command).format(**variables)


def _hash_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _command_version(command: Any) -> Optional[str]:
    if not isinstance(command, list) or not command:
        return None
    executable = shutil.which(str(command[0]))
    if not executable:
        return None
    try:
        completed = subprocess.run(
            [executable, "--version"],
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            timeout=5,
        )
    except (OSError, subprocess.SubprocessError):
        return None
    lines = (completed.stdout or "").strip().splitlines()
    return lines[0] if lines else None


def _container_image_id(container: Dict[str, Any], image_key: str = "image") -> Optional[str]:
    engine = str(container.get("engine", "docker"))
    image = str(container.get(image_key) or "")
    if not image or not shutil.which(engine):
        return None
    try:
        completed = subprocess.run(
            [engine, "image", "inspect", "--format", "{{.Id}}", image],
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            timeout=30,
        )
    except (OSError, subprocess.SubprocessError):
        return None
    return (completed.stdout or "").strip() if completed.returncode == 0 else None


def _effective_container(configured: Dict[str, Any]) -> Dict[str, Any]:
    """Apply explicit deployment overrides while retaining them in run metadata."""
    container = dict(configured)
    overrides = {
        "engine": os.environ.get("DEEPEE_CONTAINER_ENGINE"),
        "image": os.environ.get("DEEPEE_AGENT_IMAGE"),
        "verification_image": os.environ.get("DEEPEE_VERIFIER_IMAGE"),
    }
    for key, value in overrides.items():
        if value:
            container[key] = value
    return container


def _container_command_version(container: Dict[str, Any], executable: str) -> Optional[str]:
    engine = str(container.get("engine", "docker"))
    image = str(container.get("image") or "")
    if not image or not shutil.which(engine):
        return None
    try:
        completed = subprocess.run(
            [engine, "run", "--rm", image, executable, "--version"],
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            timeout=60,
        )
    except (OSError, subprocess.SubprocessError):
        return None
    lines = (completed.stdout or "").strip().splitlines()
    return lines[0] if completed.returncode == 0 and lines else None


def _parse_jsonl(output: str) -> Dict[str, Any]:
    usage: Dict[str, int] = {}
    thread_id = None
    event_count = 0
    for line in output.splitlines():
        try:
            event = json.loads(line)
        except (TypeError, json.JSONDecodeError):
            continue
        if not isinstance(event, dict):
            continue
        event_count += 1
        if event.get("type") == "thread.started":
            thread_id = event.get("thread_id") or thread_id
        event_usage = event.get("usage")
        if not isinstance(event_usage, dict):
            continue
        for key, value in event_usage.items():
            if isinstance(value, int):
                usage[key] = usage.get(key, 0) + value
    return {"event_count": event_count, "thread_id": thread_id, "usage": usage}


def _run_process(
    command: Any,
    cwd: Path,
    env: Dict[str, str],
    timeout_seconds: int,
    stdin_text: Optional[str],
) -> Dict[str, Any]:
    shell = isinstance(command, str)
    process = subprocess.Popen(
        command,
        cwd=str(cwd),
        env=env,
        shell=shell,
        text=True,
        stdin=subprocess.PIPE if stdin_text is not None else subprocess.DEVNULL,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        start_new_session=(os.name != "nt"),
    )
    try:
        output, _ = process.communicate(input=stdin_text, timeout=timeout_seconds)
        return {"output": output or "", "returncode": process.returncode, "timed_out": False}
    except subprocess.TimeoutExpired:
        if os.name != "nt":
            os.killpg(process.pid, signal.SIGKILL)
        else:
            process.kill()
        output, _ = process.communicate()
        output = (output or "") + f"\nDeepEE agent run timed out after {timeout_seconds} seconds.\n"
        return {"output": output, "returncode": 124, "timed_out": True}


def _containerize_command(command: Any, container: Dict[str, Any], run_dir: Path) -> Any:
    if not command or not container or os.environ.get("DEEPEE_NO_CONTAINER") == "1":
        return command
    if not isinstance(command, list):
        raise ValueError("Containerized runners require list-form commands")
    engine = str(container.get("engine", "docker"))
    image = str(container.get("image") or "")
    if not image:
        raise ValueError("Containerized runner is missing an image")
    wrapped = [
        engine,
        "run",
        "--rm",
        "--init",
        "--interactive",
        "--network",
        str(container.get("network", "bridge")),
        "--cpus",
        str(container.get("cpus", 4)),
        "--memory",
        str(container.get("memory", "8g")),
        "--pids-limit",
        str(container.get("pids_limit", 512)),
        "--user",
        str(container.get("user", "root")),
        "--workdir",
        str(container.get("workdir", "/work")),
        "--mount",
        f"type=bind,src={run_dir.resolve()},dst=/work",
        "--env",
        "HOME=/root",
        "--env",
        "CODEX_HOME=/root/.codex",
    ]
    if container.get("mount_codex_home", True):
        codex_home = Path(os.environ.get("CODEX_HOME", str(Path.home() / ".codex"))).expanduser().resolve()
        wrapped.extend(["--mount", f"type=bind,src={codex_home},dst=/root/.codex"])
    elif container.get("mount_codex_auth", False):
        codex_home = Path(os.environ.get("CODEX_HOME", str(Path.home() / ".codex"))).expanduser().resolve()
        auth_file = codex_home / "auth.json"
        if auth_file.is_file():
            wrapped.extend(["--mount", f"type=bind,src={auth_file},dst=/root/.codex/auth.json,readonly"])
    for name in container.get("pass_env") or ["CODEX_API_KEY"]:
        if os.environ.get(str(name)) is not None:
            wrapped.extend(["--env", str(name)])
    for name, value in (container.get("env") or {}).items():
        wrapped.extend(["--env", f"{name}={value}"])
    wrapped.append(image)
    wrapped.extend(str(part) for part in command)
    return wrapped


def prepare_run(agent_config: Path, task_ref: str, runs_root: Optional[Path] = None, root: Optional[Path] = None) -> Dict[str, Any]:
    root = root or repo_root()
    task = resolve_task(task_ref, root)
    agent = load_yaml(agent_config)
    agent_id = str(agent.get("id") or agent_config.stem)
    timestamp = utc_timestamp()
    run_id = f"{timestamp}-{uuid.uuid4().hex[:8]}"
    base_runs = runs_root or (root / "runs")
    run_dir = base_runs / agent_id / task.id / run_id
    latest_link = base_runs / agent_id / task.id / "latest"

    run_dir.mkdir(parents=True, exist_ok=True)
    (run_dir / "artifacts").mkdir(exist_ok=True)
    _copy_starter(task.path, run_dir)

    context_path = root / "agents" / "AGENT_CONTEXT.md"
    context = read_text_if_exists(context_path)
    agent_context = ""
    agent_context_value = agent.get("context_file")
    if agent_context_value:
        configured_context = Path(str(agent_context_value))
        if not configured_context.is_absolute():
            configured_context = root / configured_context
        agent_context = read_text_if_exists(configured_context)
    prompt = read_text_if_exists(task.prompt_path)
    expected_path = task.path / "expected_artifacts.yaml"
    expected = read_text_if_exists(expected_path)
    if not expected:
        expected = yaml.safe_dump(task.manifest.get("required_artifacts", []), sort_keys=False)
    identity = {
        "id": agent_id,
        "system": agent.get("system"),
        "model": agent.get("model"),
        "effort": agent.get("effort"),
    }
    bundle = (
        f"# DeepEE Agent Context\n\n{context}\n\n"
        f"# Agent Configuration\n\n{agent_context}\n\n"
        f"# Run Identity\n\n```json\n{json.dumps(identity, indent=2)}\n```\n\n"
        f"# Task Prompt\n\n{prompt}\n\n"
        f"# Expected Artifacts\n\n```yaml\n{expected.strip()}\n```\n"
    )
    prompt_bundle = run_dir / "prompt_bundle.md"
    prompt_bundle.write_text(bundle, encoding="utf-8")

    host_variables = {
        "repo_root": str(root),
        "run_dir": str(run_dir),
        "task_dir": str(task.path),
        "task_id": task.id,
        "prompt_bundle": str(prompt_bundle),
        "artifacts_dir": str(run_dir / "artifacts"),
    }
    runner = agent.get("runner", {})
    container = _effective_container(runner.get("container") or {})
    command_variables = dict(host_variables)
    if container and os.environ.get("DEEPEE_NO_CONTAINER") != "1":
        command_variables.update(
            {
                "repo_root": "/opt/deepee",
                "run_dir": "/work",
                "prompt_bundle": "/work/prompt_bundle.md",
                "artifacts_dir": "/work/artifacts",
            }
        )
    command = runner.get("command")
    inner_command = _format_command(command, command_variables) if command else None
    formatted_command = _containerize_command(inner_command, container, run_dir)
    stdin_path_value = runner.get("stdin")
    stdin_path = _format_command(stdin_path_value, host_variables) if stdin_path_value else None

    agent_cli_version = _command_version(inner_command)
    if container and isinstance(inner_command, list) and inner_command:
        agent_cli_version = _container_command_version(container, str(inner_command[0]))
    metadata = {
        "schema_version": "1.0",
        "agent": agent,
        "agent_id": agent_id,
        "task_id": task.id,
        "suite": task.suite,
        "created_at": timestamp,
        "run_id": run_id,
        "run_dir": str(run_dir),
        "prompt_bundle": str(prompt_bundle),
        "prompt_hash": _hash_file(prompt_bundle),
        "agent_config": str(agent_config.resolve()),
        "agent_config_hash": _hash_file(agent_config),
        "command": formatted_command,
        "inner_command": inner_command,
        "container": container,
        "container_engine_version": _command_version([str(container.get("engine", "docker"))]) if container else None,
        "agent_container_image_id": _container_image_id(container),
        "verification_container_image_id": _container_image_id(container, "verification_image"),
        "stdin_path": stdin_path,
        "runner_output_format": runner.get("output_format", "text"),
        "agent_cli_version": agent_cli_version,
        "status": "prepared",
    }
    write_json(run_dir / ".deepee" / "run.json", metadata)

    if latest_link.exists() or latest_link.is_symlink():
        if latest_link.is_symlink() or latest_link.is_file():
            latest_link.unlink()
        else:
            shutil.rmtree(str(latest_link))
    latest_link.parent.mkdir(parents=True, exist_ok=True)
    try:
        latest_link.symlink_to(run_dir.resolve(), target_is_directory=True)
    except OSError:
        shutil.copytree(str(run_dir), str(latest_link))

    return metadata


def run_agent(agent_config: Path, task_ref: str, runs_root: Optional[Path] = None, root: Optional[Path] = None) -> Dict[str, Any]:
    task = resolve_task(task_ref, root)
    metadata = prepare_run(agent_config, task_ref, runs_root, root)
    command = metadata.get("command")
    if not command:
        metadata["status"] = "prepared"
        return metadata

    run_dir = Path(metadata["run_dir"])
    env = os.environ.copy()
    env.update(
        {
            "DEEPEE_TASK_ID": metadata["task_id"],
            "DEEPEE_RUN_DIR": str(run_dir),
            "DEEPEE_ARTIFACTS_DIR": str(run_dir / "artifacts"),
            "DEEPEE_PROMPT_BUNDLE": str(run_dir / "prompt_bundle.md"),
        }
    )
    started = utc_timestamp()
    started_monotonic = time.monotonic()
    timeout_seconds = int(task.manifest.get("timeout_minutes", 60)) * 60
    stdin_text = None
    stdin_path = metadata.get("stdin_path")
    if stdin_path:
        stdin_text = Path(str(stdin_path)).read_text(encoding="utf-8")
    try:
        process_result = _run_process(command, run_dir, env, timeout_seconds, stdin_text)
        output = process_result["output"]
        returncode = process_result["returncode"]
        timed_out = process_result["timed_out"]
    except OSError as exc:
        output = f"DeepEE could not start agent command: {exc}\n"
        returncode = 127
        timed_out = False

    metadata["status"] = "timed_out" if timed_out else ("completed" if returncode == 0 else "failed")
    metadata["started_at"] = started
    metadata["completed_at"] = utc_timestamp()
    metadata["wall_time_seconds"] = round(time.monotonic() - started_monotonic, 6)
    metadata["timeout_seconds"] = timeout_seconds
    metadata["timed_out"] = timed_out
    metadata["returncode"] = returncode
    (run_dir / ".deepee").mkdir(exist_ok=True)
    (run_dir / ".deepee" / "agent.log").write_text(output, encoding="utf-8")
    if metadata.get("runner_output_format") == "jsonl":
        (run_dir / ".deepee" / "events.jsonl").write_text(output, encoding="utf-8")
        metadata.update(_parse_jsonl(output))
    write_json(run_dir / ".deepee" / "run.json", metadata)
    return metadata
