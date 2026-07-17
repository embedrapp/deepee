from __future__ import annotations

import hashlib
import os
import zipfile
from pathlib import Path
from typing import Any, Dict


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def package_run(run_dir: Path, output: Path) -> Dict[str, Any]:
    """Create a deterministic evidence ZIP for one frozen run directory."""
    run_dir = run_dir.resolve()
    output = output.resolve()
    if not run_dir.is_dir():
        raise ValueError(f"Run directory does not exist: {run_dir}")
    if output == run_dir or run_dir in output.parents:
        raise ValueError("Evidence archive must be outside the run directory")

    files = sorted(path for path in run_dir.rglob("*") if path.is_file())
    symlinks = [path for path in run_dir.rglob("*") if path.is_symlink()]
    if symlinks:
        relative = ", ".join(str(path.relative_to(run_dir)) for path in symlinks[:10])
        raise ValueError(f"Run directory contains symlinks: {relative}")

    output.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(output, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        for path in files:
            relative = path.relative_to(run_dir).as_posix()
            info = zipfile.ZipInfo(relative, date_time=(1980, 1, 1, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            info.create_system = 3
            mode = 0o755 if os.access(path, os.X_OK) else 0o644
            info.external_attr = mode << 16
            archive.writestr(info, path.read_bytes(), compress_type=zipfile.ZIP_DEFLATED, compresslevel=9)

    return {
        "format": "zip",
        "path": str(output),
        "sha256": _sha256(output),
        "size_bytes": output.stat().st_size,
        "file_count": len(files),
    }
