#!/usr/bin/env python3
"""Create the public-synthetic Lighthouse golden path with one command."""

from __future__ import annotations

import argparse
from pathlib import Path

from gamedesignos.demo import create_lighthouse_demo
from gamedesignos.project_ready import update_decision_status, workflow_next
from gamedesignos.workspace import Workspace


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--destination", type=Path, required=True)
    args = parser.parse_args()
    destination = args.destination.expanduser().resolve()

    result = create_lighthouse_demo(destination)
    workspace = Workspace.open(destination)
    decision_id = result["decision"]["decision_id"]
    update_decision_status(
        workspace,
        decision_id,
        status="accepted",
        by="fixture",
        reason="Synthetic experiment passed and rollback remains explicit.",
    )
    workflow_next(workspace, result["workflow"]["run_id"])
    report = workspace.validate()
    if not report.ok:
        raise SystemExit("Golden project validation failed: " + "; ".join(report.errors))
    print(f"OK: golden project created at {destination}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
