#!/usr/bin/env python3
"""Rebuild a wheel from the sdist and verify canonical packaged resources."""

from __future__ import annotations

import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path


REQUIRED_WHEEL_FILES = {
    "gamedesignos/application/__init__.py",
    "gamedesignos/application/project_queries.py",
    "gamedesignos/demo.py",
    "gamedesignos/_data/contracts/router.yaml",
    "gamedesignos/_data/contracts/project-workspace.schema.json",
    "gamedesignos/_data/contracts/ul-state.schema.json",
    "gamedesignos/_data/workspace-template/game.designos.yaml",
    "gamedesignos/_data/workspace-template-v1/game.designos.yaml",
    "gamedesignos/_data/workspace-template-v1/00-inbox/README.md",
}


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    sdists = sorted((root / "dist").glob("gamedesignos-*.tar.gz"), key=lambda item: item.stat().st_mtime)
    if not sdists:
        print("sdist smoke failed: build an sdist first with `python -m build`")
        return 1
    with tempfile.TemporaryDirectory() as raw:
        wheel_dir = Path(raw)
        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "pip",
                "wheel",
                "--no-deps",
                "--wheel-dir",
                str(wheel_dir),
                str(sdists[-1]),
            ],
            cwd=root,
            check=False,
        )
        if result.returncode:
            return result.returncode
        wheels = list(wheel_dir.glob("gamedesignos-*.whl"))
        if len(wheels) != 1:
            print(f"sdist smoke failed: expected one wheel, found {len(wheels)}")
            return 1
        with zipfile.ZipFile(wheels[0]) as archive:
            names = set(archive.namelist())
        missing = REQUIRED_WHEEL_FILES - names
        if missing:
            print(f"sdist smoke failed: rebuilt wheel lacks {sorted(missing)}")
            return 1
    print("OK: sdist rebuild preserves canonical wheel resources")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
