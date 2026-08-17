"""Self-contained public-synthetic demo for the GameDesignOS decision loop."""

from __future__ import annotations

import tempfile
from pathlib import Path
from typing import Any
from uuid import uuid4

from .errors import UsageError
from .project_ready import (
    add_evidence,
    add_experiment_result,
    health_scan,
    inspect_decision,
    load_project_ready_state,
    review_experiment,
    run_gate,
    start_project,
    validate_assumption,
    validate_workflow_run,
    workflow_next,
)
from .workspace import Workspace


DEMO_ID = "golden-lighthouse"
DEMO_PROJECT_NAME = "Synthetic Lighthouse Tactics"
DEMO_OWNER = "gamedesignos-golden-fixture"


def _default_demo_destination() -> Path:
    return Path(tempfile.gettempdir()) / f"gamedesignos-demo-{uuid4().hex[:8]}"


def _require_fresh_destination(destination: Path) -> None:
    if not destination.exists():
        return
    if not destination.is_dir():
        raise UsageError(f"Demo destination is not a directory: {destination}")
    if any(destination.iterdir()):
        raise UsageError(
            f"Refusing to overwrite non-empty demo destination {destination}. "
            "Choose a new --destination."
        )


def create_lighthouse_demo(destination: Path | None = None) -> dict[str, Any]:
    """Create a fresh synthetic decision loop and stop before the Human Gate.

    The fixture proves local runtime behavior only. It makes no model calls and
    never accepts the synthetic decision on the user's behalf.
    """

    target = (destination or _default_demo_destination()).expanduser().resolve()
    _require_fresh_destination(target)

    started = start_project(
        project_name=DEMO_PROJECT_NAME,
        destination=target,
        owner=DEMO_OWNER,
        visibility="public-synthetic",
        question="Can players understand the repair-versus-defend tradeoff in three minutes?",
        options=["Repair-first route", "Defense-first route"],
        default_action="Repair-first route",
        assumption="Four of five synthetic testers can explain the tradeoff after three minutes.",
        rollback_trigger="Fewer than four of five can explain the tradeoff.",
    )
    workspace = Workspace.open(target)
    decision_id = str(started["decision"]["decision_id"])
    assumption_id = str(started["assumption"]["assumption_id"])
    experiment_id = str(started["experiment"]["experiment_id"])
    workflow_id = str(started["workflow_run"]["run_id"])

    evidence_result = add_evidence(
        workspace,
        decision_id=decision_id,
        summary="Synthetic fixture: four of five testers explained the tradeoff.",
        source_type="playtest",
        source_status="synthetic",
        confidence="medium",
        decision_impact="Keep repair-first as the next prototype default.",
        unsupported_claims=["Does not establish retention or commercial demand."],
    )
    evidence = evidence_result["evidence"]
    evidence_id = str(evidence["evidence_id"])

    add_experiment_result(
        workspace,
        experiment_id,
        status="passed",
        observations=["Four of five synthetic testers explained the tradeoff."],
        evidence_refs=[evidence_id],
        decision_delta="Repair-first remains the reversible default.",
    )
    reviewed = review_experiment(
        workspace,
        experiment_id,
        by="fixture",
        summary="Synthetic result reviewed; no retention claim allowed.",
    )
    validated_assumption = validate_assumption(
        workspace,
        assumption_id,
        status="tested",
        reason="Covered by the reviewed synthetic experiment.",
    )["assumption"]

    commitment_gate = run_gate(workspace, "commitment", decision_id)
    if commitment_gate["status"] != "ask_human":
        raise UsageError(
            "Demo fixture did not reach the expected Human Gate: "
            f"{commitment_gate['status']} - {commitment_gate['reason']}"
        )

    workflow_progress = workflow_next(workspace, workflow_id)
    workspace_validation = workspace.validate()
    workflow_validation = validate_workflow_run(workspace, workflow_id)
    if not workspace_validation.ok or not workflow_validation["ok"]:
        errors = [*workspace_validation.errors, *workflow_validation["errors"]]
        raise UsageError("Demo validation failed: " + "; ".join(errors))

    state = load_project_ready_state(workspace)
    experiment = state["experiments"][experiment_id]
    decision = inspect_decision(workspace, decision_id)
    unsupported_claims = list(evidence.get("unsupported_claims", []))
    next_hint = (
        f'gamedesignos decision accept {decision_id} --workspace "{workspace.root}" '
        "--by OWNER --reason REASON"
    )

    return {
        "schema_version": "1.0.0",
        "demo_id": DEMO_ID,
        "mode": "public-synthetic",
        "workspace": str(workspace.root),
        "model_calls": 0,
        "credentials_required": False,
        "decision": {
            "decision_id": decision_id,
            "status": decision["status"],
            "question": decision["decision_question"],
            "current_default_action": decision["current_default_action"],
            "rollback_trigger": decision["rollback_trigger"],
        },
        "assumption": {
            "assumption_id": assumption_id,
            "status": validated_assumption["validation_status"],
            "statement": validated_assumption["statement"],
        },
        "evidence": {
            "evidence_id": evidence_id,
            "source_status": evidence["source_status"],
            "summary": evidence["summary"],
            "unsupported_claims": unsupported_claims,
        },
        "experiment": {
            "experiment_id": experiment_id,
            "result_status": experiment.get("result_status"),
            "review_status": experiment.get("review_status"),
            "outcome": reviewed["result"]["status"],
        },
        "workflow": {
            "run_id": workflow_id,
            "status": workflow_progress["run"]["status"],
            "current_node": workflow_progress["run"]["current_node"],
            "next_status": workflow_progress["next"]["status"],
            "next_reason": workflow_progress["next"]["reason"],
            "next_hint": workflow_progress["next"].get("hint"),
        },
        "human_gate": {
            "gate_type": commitment_gate["gate_type"],
            "status": commitment_gate["status"],
            "required": commitment_gate["human_gate_required"],
            "reason": commitment_gate["reason"],
            "required_actions": commitment_gate["required_actions"],
        },
        "blocked_or_gated": [
            {
                "item": "decision_accept",
                "status": "human_gate",
                "reason": commitment_gate["reason"],
            },
            {
                "item": "retention_or_commercial_demand_claim",
                "status": "unsupported",
                "reason": unsupported_claims[0],
            },
        ],
        "next_action": {
            "action": "human_decision",
            "target": decision_id,
            "reason": "Review the synthetic evidence, then explicitly accept, reject, or supersede.",
            "command_hint": next_hint,
        },
        "health": health_scan(workspace),
        "validation": {
            "workspace": workspace_validation.as_dict(),
            "workflow": {
                "ok": workflow_validation["ok"],
                "errors": workflow_validation["errors"],
            },
        },
        "proof_boundary": [
            "This public-synthetic fixture proves deterministic local workflow behavior only.",
            *unsupported_claims,
            "It does not prove model quality, real player outcomes, release readiness, or commercial value.",
        ],
    }
