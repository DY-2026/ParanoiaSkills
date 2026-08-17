"""Deterministic, read-only queries for CLI and future protocol adapters.

This module is deliberately transport-agnostic. It owns no process lifecycle,
authentication, model call, or workspace mutation. Presentation adapters may
format these dictionaries, but they should not reimplement the domain queries.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from ..errors import UsageError
from ..project_ready import (
    export_graph_mermaid,
    health_scan,
    inspect_decision,
    inspect_evidence,
    inspect_graph,
    next_best_action,
    run_gate,
)
from ..routing import route_task, router_source
from ..workspace import Workspace


def route_project_task(task: str, *, workspace: Workspace | None = None) -> dict[str, Any]:
    """Return the deterministic skill route and its canonical contract source."""

    result = route_task(task, workspace=workspace)
    return {**result, "router_source": router_source(workspace)}


def get_project_status(workspace: Workspace) -> dict[str, Any]:
    """Return workspace status using the active schema's decision source of truth."""

    return workspace.status().as_dict()


def get_project_health(workspace: Workspace) -> dict[str, Any]:
    """Return deterministic Project-Ready risk signals without writing files."""

    return health_scan(workspace)


def get_next_action(workspace: Workspace) -> dict[str, Any]:
    """Return the smallest deterministic next action without executing it."""

    return next_best_action(workspace)


def preview_gate(workspace: Workspace, gate_type: str, target: str) -> dict[str, Any]:
    """Evaluate a gate without persisting a gate-result record."""

    return run_gate(workspace, gate_type, target, write=False)


def export_project_graph(workspace: Workspace, *, format: str = "mermaid") -> dict[str, Any]:
    """Export the local decision graph in a supported read-only format."""

    if format != "mermaid":
        raise UsageError(f"Unsupported graph format: {format}")
    return {"format": format, "graph": export_graph_mermaid(workspace)}


def inspect_project_graph(workspace: Workspace, target: str) -> dict[str, Any]:
    """Inspect one graph node and its local edges."""

    return inspect_graph(workspace, target)


def inspect_project_decision(workspace: Workspace, decision_id: str) -> dict[str, Any]:
    """Inspect one normalized Decision Object."""

    return inspect_decision(workspace, decision_id)


def inspect_project_evidence(workspace: Workspace, evidence_id: str) -> dict[str, Any]:
    """Inspect one evidence record without changing its review state."""

    return inspect_evidence(workspace, evidence_id)


def validate_project_workspace(
    workspace: Workspace,
    *,
    repo_root: Path | None = None,
) -> dict[str, Any]:
    """Return the serializable workspace validation report."""

    return workspace.validate(repo_root=repo_root).as_dict()
