#!/usr/bin/env python3
"""Verify an installed wheel from a directory outside the source checkout."""

from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path


def run(args: list[str], *, cwd: Path) -> subprocess.CompletedProcess[str]:
    env = dict(os.environ)
    env["PYTHONIOENCODING"] = "utf-8"
    result = subprocess.run(
        [sys.executable, *args],
        cwd=cwd,
        env=env,
        text=True,
        encoding="utf-8",
        errors="replace",
        capture_output=True,
        check=False,
    )
    if result.returncode:
        raise SystemExit(
            f"Command failed ({result.returncode}): {args}\nSTDOUT:\n{result.stdout}\nSTDERR:\n{result.stderr}"
        )
    return result


def main() -> int:
    repo_root = Path(__file__).resolve().parents[1]
    with tempfile.TemporaryDirectory() as raw:
        outside = Path(raw).resolve()
        location = run(
            ["-c", "import gamedesignos; print(gamedesignos.__file__)"], cwd=outside
        ).stdout.strip()
        if repo_root in Path(location).resolve().parents:
            raise SystemExit(f"Smoke test imported the source checkout instead of the wheel: {location}")

        doctor = json.loads(run(["-m", "gamedesignos", "doctor", "--json"], cwd=outside).stdout)
        if not doctor.get("ok"):
            raise SystemExit(f"Installed doctor failed: {doctor}")
        contracts = next(item for item in doctor["checks"] if item["name"] == "canonical-contracts")
        if "(packaged)" not in contracts["detail"]:
            raise SystemExit(f"Installed runtime did not use packaged contracts: {contracts}")

        workspace = outside / "wheel-smoke"
        run(
            [
                "-m",
                "gamedesignos",
                "init",
                "Wheel Smoke",
                "--destination",
                str(workspace),
                "--owner",
                "ci",
            ],
            cwd=outside,
        )
        run(["-m", "gamedesignos", "validate", "--workspace", str(workspace)], cwd=outside)
        route = run(["-m", "gamedesignos", "route", "分析一段试玩录屏"], cwd=outside).stdout
        if "game-experience-analyzer" not in route:
            raise SystemExit(f"Packaged router returned an unexpected route:\n{route}")
        ul_route = json.loads(run(
            [
                "-c",
                (
                    "import json; from gamedesignos.routing import route_task; "
                    "print(json.dumps(route_task('把不确定性阶梯用于 AI 工程并验证负迁移'), "
                    "ensure_ascii=False))"
                ),
            ],
            cwd=outside,
        ).stdout)
        if (
            ul_route.get("selected_skill") != "paranoia-ai-system-evolver"
            or "ul-state" not in ul_route.get("primary_outputs", [])
        ):
            raise SystemExit(f"Packaged router lost the UL route or output:\n{ul_route}")
    print("OK: installed wheel is self-contained outside the source checkout")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
