from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, Optional

from .config import load_yaml, repo_root


@dataclass(frozen=True)
class Task:
    id: str
    suite: str
    path: Path
    manifest: Dict

    @property
    def prompt_path(self) -> Path:
        return self.path / "prompt.md"

    @property
    def starter_path(self) -> Path:
        return self.path / "starter"


def tasks_root(root: Optional[Path] = None) -> Path:
    return (root or repo_root()) / "tasks"


def iter_tasks(root: Optional[Path] = None) -> Iterable[Task]:
    base = tasks_root(root)
    for manifest_path in sorted(base.glob("*/*/manifest.yaml")):
        manifest = load_yaml(manifest_path)
        task_id = str(manifest.get("id") or manifest_path.parent.name)
        suite = str(manifest.get("suite") or manifest_path.parent.parent.name)
        yield Task(id=task_id, suite=suite, path=manifest_path.parent, manifest=manifest)


def resolve_task(task_ref: str, root: Optional[Path] = None) -> Task:
    candidate = Path(task_ref).expanduser()
    if candidate.exists():
        path = candidate if candidate.is_dir() else candidate.parent
        manifest = load_yaml(path / "manifest.yaml")
        return Task(
            id=str(manifest.get("id") or path.name),
            suite=str(manifest.get("suite") or path.parent.name),
            path=path.resolve(),
            manifest=manifest,
        )

    matches = [task for task in iter_tasks(root) if task.id == task_ref]
    if not matches:
        raise ValueError(f"Unknown task: {task_ref}")
    if len(matches) > 1:
        raise ValueError(f"Ambiguous task id: {task_ref}")
    return matches[0]

