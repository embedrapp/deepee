from __future__ import annotations

import json
import os
import shlex
import shutil
import subprocess
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional

from .config import load_yaml
from .lint import lint_tasks
from .task import iter_tasks


TOOL_COMMANDS = {
    "python3": ["python3", "--version"],
    "make": ["make", "--version"],
    "gcc": ["gcc", "--version"],
    "kicad-cli": ["kicad-cli", "--version"],
    "pio": ["pio", "--version"],
}

CORE_TOOLS = {"python3", "make", "gcc"}


def _command_version(command: List[str]) -> Dict[str, Any]:
    executable = command[0]
    resolved = shutil.which(executable)
    if not resolved:
        return {"available": False}
    try:
        completed = subprocess.run(
            command,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            timeout=5,
        )
    except (OSError, subprocess.SubprocessError) as exc:
        return {"available": True, "path": resolved, "error": str(exc)}
    lines = (completed.stdout or "").strip().splitlines()
    return {
        "available": True,
        "path": resolved,
        "returncode": completed.returncode,
        "version": lines[0] if lines else "",
    }


def _runner_executable(command: Any) -> Optional[str]:
    if not command:
        return None
    if isinstance(command, list):
        return str(command[0]) if command else None
    parts = shlex.split(str(command))
    return parts[0] if parts else None


def _agent_status(agent_config: Path) -> Dict[str, Any]:
    agent = load_yaml(agent_config)
    runner = agent.get("runner") or {}
    command = runner.get("command")
    executable = _runner_executable(command)
    if not executable:
        return {
            "agent_config": str(agent_config),
            "agent_id": agent.get("id") or agent_config.stem,
            "mode": "manual",
            "available": True,
            "message": "Manual agent: prepare-run creates a bundle, then artifacts must be copied in.",
        }
    container = runner.get("container") or {}
    container_engine = str(container.get("engine", "docker")) if container else None
    container_image = str(container.get("image") or "") if container else None
    verification_image = str(container.get("verification_image") or "") if container else None
    effective_executable = container_engine or executable
    resolved = shutil.which(effective_executable)
    status = {
        "agent_config": str(agent_config),
        "agent_id": agent.get("id") or agent_config.stem,
        "mode": "container" if container else "command",
        "executable": effective_executable,
        "available": bool(resolved),
        "path": resolved,
        "model": agent.get("model"),
        "effort": agent.get("effort"),
    }
    prefix: List[str] = []
    if container and resolved:
        status["container_image"] = container_image
        inspect = subprocess.run(
            [resolved, "image", "inspect", container_image],
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            timeout=30,
        )
        status["image_available"] = inspect.returncode == 0
        status["available"] = status["available"] and status["image_available"]
        prefix = [
            resolved,
            "run",
            "--rm",
            "--network",
            str(container.get("network", "bridge")),
        ]
        for name, value in (container.get("env") or {}).items():
            prefix.extend(["--env", f"{name}={value}"])
        prefix.append(container_image)
        required_env = [str(name) for name in container.get("required_env") or []]
        if required_env:
            missing_env = [name for name in required_env if not os.environ.get(name)]
            status["required_env"] = required_env
            status["missing_env"] = missing_env
            status["available"] = status["available"] and not missing_env
        if container.get("mount_codex_auth"):
            codex_home = Path(os.environ.get("CODEX_HOME", str(Path.home() / ".codex"))).expanduser()
            status["codex_auth_available"] = bool(os.environ.get("CODEX_API_KEY") or (codex_home / "auth.json").is_file())
            status["available"] = status["available"] and status["codex_auth_available"]
        if verification_image:
            verification_inspect = subprocess.run(
                [resolved, "image", "inspect", verification_image],
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                timeout=30,
            )
            status["verification_image"] = verification_image
            status["verification_image_available"] = verification_inspect.returncode == 0
            status["available"] = status["available"] and status["verification_image_available"]
    preflight = runner.get("preflight_command")
    if resolved and preflight:
        command = [str(part) for part in preflight] if isinstance(preflight, list) else shlex.split(str(preflight))
        try:
            completed = subprocess.run(
                prefix + command,
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                timeout=30,
            )
            status["preflight_returncode"] = completed.returncode
            status["preflight_output"] = (completed.stdout or "")[-2000:]
            status["available"] = status["available"] and completed.returncode == 0
        except (OSError, subprocess.SubprocessError) as exc:
            status["available"] = False
            status["preflight_error"] = str(exc)

    if resolved and status["available"] and agent.get("system") == "codex" and agent.get("model"):
        try:
            catalog = subprocess.run(
                prefix + ([executable, "debug", "models", "--bundled"] if container else [resolved, "debug", "models", "--bundled"]),
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                timeout=30,
            )
            payload = json.loads(catalog.stdout or "{}") if catalog.returncode == 0 else {}
            model_ids = {item.get("slug") for item in payload.get("models", []) if isinstance(item, dict)}
            status["model_available"] = agent.get("model") in model_ids
            status["available"] = status["available"] and status["model_available"]
        except (OSError, subprocess.SubprocessError, json.JSONDecodeError) as exc:
            status["model_available"] = False
            status["available"] = False
            status["model_error"] = str(exc)
    if container and resolved and status["available"]:
        try:
            authoring_toolchain = subprocess.run(
                prefix
                + [
                    "sh",
                    "-ec",
                    "python3 --version\nmake --version\ngcc --version\nkicad-cli --version\npio --version\ntest ! -e /opt/deepee/tasks",
                ],
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                timeout=120,
            )
            status["authoring_toolchain_returncode"] = authoring_toolchain.returncode
            status["authoring_toolchain_output"] = (authoring_toolchain.stdout or "")[-4000:]
            status["available"] = status["available"] and authoring_toolchain.returncode == 0
            if verification_image and status["available"]:
                verifier_toolchain = subprocess.run(
                    [resolved, "run", "--rm", "--network", "none", verification_image, "deepee", "doctor", "--strict-tools"],
                    text=True,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    timeout=120,
                )
                status["verifier_toolchain_returncode"] = verifier_toolchain.returncode
                status["verifier_toolchain_output"] = (verifier_toolchain.stdout or "")[-4000:]
                status["available"] = status["available"] and verifier_toolchain.returncode == 0
        except (OSError, subprocess.SubprocessError) as exc:
            status["available"] = False
            status["toolchain_error"] = str(exc)
    return status


def run_doctor(
    agent_configs: Optional[Iterable[Path]] = None,
    strict_tools: bool = False,
    root: Optional[Path] = None,
) -> Dict[str, Any]:
    lint = lint_tasks(root)
    tools = {name: _command_version(command) for name, command in TOOL_COMMANDS.items()}
    agents = [_agent_status(path) for path in agent_configs or []]
    task_count = sum(1 for _ in iter_tasks(root))

    missing_core_tools = [name for name in CORE_TOOLS if not tools[name]["available"]]
    declared_tools = {
        str(name)
        for task in iter_tasks(root)
        for name in list(task.manifest.get("required_tools") or [])
    }
    needs_host_toolchain = not agents or any(agent["mode"] == "command" for agent in agents)
    required_tools = CORE_TOOLS | (declared_tools if strict_tools and needs_host_toolchain else set())
    missing_required_tools = [name for name in sorted(required_tools) if name not in tools or not tools[name]["available"]]
    missing_optional_tools = [name for name, status in tools.items() if name not in required_tools and not status["available"]]
    missing_agents = [
        agent["agent_id"]
        for agent in agents
        if agent["mode"] in {"command", "container"} and not agent["available"]
    ]
    ok = lint["ok"] and not missing_required_tools and not missing_agents

    return {
        "ok": ok,
        "task_count": task_count,
        "lint": lint,
        "tools": tools,
        "missing_core_tools": missing_core_tools,
        "missing_required_tools": missing_required_tools,
        "missing_optional_tools": missing_optional_tools,
        "agents": agents,
        "missing_agents": missing_agents,
    }
