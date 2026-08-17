"""Command-line interface for the GameDesignOS local runtime."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Sequence

from .application import (
    export_project_graph,
    get_next_action,
    get_project_health,
    get_project_status,
    inspect_project_decision,
    inspect_project_evidence,
    inspect_project_graph,
    preview_gate,
    route_project_task,
    validate_project_workspace,
)
from .constants import ASSET_SPECS, RUNTIME_VERSION, VALID_VISIBILITIES
from .demo import create_lighthouse_demo
from .errors import EXIT_INCOMPATIBLE_VERSION, EXIT_OK, EXIT_VALIDATION, GameDesignOSError, UsageError
from .project_ready import (
    GATE_TYPES,
    add_evidence,
    add_experiment_result,
    create_assumption,
    create_decision,
    list_assumptions,
    list_decisions,
    list_evidence,
    list_workflows,
    plan_experiment,
    review_experiment,
    run_gate,
    start_project,
    start_workflow,
    update_decision_status,
    validate_assumption,
    validate_workflow_run,
    workflow_next,
    workflow_status,
)
from .voi import create_assessment, review_assessment
from .workspace import Workspace, doctor, init_workspace

KNOWN_COMMANDS = {
    "demo",
    "ask",
    "init",
    "start",
    "status",
    "validate",
    "doctor",
    "route",
    "health",
    "next",
    "gate",
    "graph",
    "decision",
    "assumption",
    "evidence",
    "experiment",
    "workflow",
    "new",
    "voi",
    "pack",
}
def _path(value: str | None) -> Path | None:
    return Path(value).expanduser() if value else None


def _configure_utf8_stdio() -> None:
    """Keep Unicode CLI output portable across redirected Windows streams."""

    for stream in (sys.stdout, sys.stderr):
        reconfigure = getattr(stream, "reconfigure", None)
        if not callable(reconfigure):
            continue
        try:
            reconfigure(encoding="utf-8", errors="backslashreplace")
        except (OSError, ValueError):
            # Test doubles and host-managed streams may forbid reconfiguration.
            continue


def _emit(data: Any, *, as_json: bool, text: str) -> None:
    print(json.dumps(data, ensure_ascii=False, indent=2) if as_json else text)


def _workspace(args: argparse.Namespace) -> Workspace:
    return Workspace.open(_path(getattr(args, "workspace", None)))


def _joined(value: str | list[str]) -> str:
    return " ".join(value) if isinstance(value, list) else value


def _title_from_sentence(text: str) -> str:
    cleaned = " ".join(text.replace("\r", " ").replace("\n", " ").split()).strip()
    for prefix in ("我想做", "我想要做", "想做", "做一个", "做一款", "帮我做", "帮我"):
        if cleaned.startswith(prefix):
            cleaned = cleaned[len(prefix) :].strip(" ：:，,。")
            break
    return (cleaned[:42].rstrip() or "GameDesignOS Project")


def _single_skill_prompt(skill: str | None, text: str) -> str:
    if not skill:
        return f"请先说明这句话最终想产出什么：{text}"
    return f"Use ${skill} to handle this request:\n{text}"


def _open_workspace_safely(path: Path | None) -> Workspace | None:
    try:
        return Workspace.open(path)
    except GameDesignOSError:
        return None


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="gamedesignos",
        description="Local deterministic GameDesignOS runtime. No model calls, API keys, uploads, or Human Gate decisions.",
    )
    parser.add_argument("--version", action="version", version=f"%(prog)s {RUNTIME_VERSION}")
    sub = parser.add_subparsers(dest="command", required=True)

    p = sub.add_parser(
        "demo",
        help="Create a synthetic end-to-end decision loop",
        description=(
            "Create a fresh public-synthetic Lighthouse workspace, validate the decision loop, "
            "and stop before the Commitment Human Gate. No model or API key is used."
        ),
    )
    p.add_argument(
        "--destination",
        help="Fresh empty directory; defaults to a unique system temporary directory",
    )
    p.add_argument("--json", action="store_true", help="Emit the complete machine-readable summary")

    p = sub.add_parser("ask", help="Use one sentence to route or start GameDesignOS work")
    p.add_argument("text", nargs="+")
    p.add_argument("--workspace")
    p.add_argument("--destination")
    p.add_argument("--owner", default="designer")
    p.add_argument("--visibility", default="private", choices=sorted(VALID_VISIBILITIES))
    p.add_argument("--json", action="store_true")

    p = sub.add_parser("init", help="Create a workspace")
    p.add_argument("project_name")
    p.add_argument("--destination")
    p.add_argument("--codename")
    p.add_argument("--visibility", default="private", choices=["private", "public-synthetic", "public-cleared"])
    p.add_argument("--owner", default="designer")
    p.add_argument("--workspace-version", default="1.0.0", choices=["1.0.0", "0.8.0"])
    p.add_argument("--force", action="store_true")
    p.add_argument("--dry-run", action="store_true")
    p.add_argument("--json", action="store_true")

    p = sub.add_parser("start", help="One-command Project-Ready setup")
    p.add_argument("project_name", nargs="+")
    p.add_argument("--destination")
    p.add_argument("--owner", default="designer")
    p.add_argument("--visibility", default="private", choices=sorted(VALID_VISIBILITIES))
    p.add_argument("--question", default="下一轮最应该验证什么，才能决定是否继续投入？")
    p.add_argument("--option", action="append", default=[])
    p.add_argument("--default-action")
    p.add_argument("--assumption", default="玩家能在三分钟内理解并感受到核心玩法的乐趣。")
    p.add_argument("--test-method", default="三分钟核心循环原型 + 3-5 人观察。")
    p.add_argument("--success", action="append", default=[])
    p.add_argument("--failure", action="append", default=[])
    p.add_argument("--rollback-trigger", default="一周内无法形成可试玩的三分钟核心循环。")
    p.add_argument("--sample-size", type=int, default=5)
    p.add_argument("--json", action="store_true")

    for name, help_text in (("status", "Summarize workspace state"), ("validate", "Validate a workspace"), ("doctor", "Diagnose runtime readiness")):
        p = sub.add_parser(name, help=help_text)
        p.add_argument("--workspace")
        if name == "validate":
            p.add_argument("--repo-root")
        p.add_argument("--json", action="store_true")

    p = sub.add_parser("route", help="Recommend the smallest suitable skill")
    p.add_argument("task", nargs="+")
    p.add_argument("--workspace")
    p.add_argument("--json", action="store_true")

    for name, help_text in (
        ("health", "Scan Project-Ready decision, assumption, experiment, and rollback risks"),
        ("next", "Recommend the next deterministic Project-Ready action"),
    ):
        p = sub.add_parser(name, help=help_text)
        p.add_argument("--workspace")
        p.add_argument("--json", action="store_true")

    p_gate = sub.add_parser("gate", help="Run Project-Ready gates")
    gate_sub = p_gate.add_subparsers(dest="gate_command", required=True)
    p = gate_sub.add_parser("run", help="Run a deterministic gate for a target")
    p.add_argument("gate_type", choices=sorted(GATE_TYPES))
    p.add_argument("target")
    p.add_argument("--workspace")
    p.add_argument("--write", action="store_true")
    p.add_argument("--json", action="store_true")

    p_graph = sub.add_parser("graph", help="Inspect or export the local decision graph")
    graph_sub = p_graph.add_subparsers(dest="graph_command", required=True)
    p = graph_sub.add_parser("export", help="Export the graph")
    p.add_argument("--workspace")
    p.add_argument("--format", default="mermaid", choices=["mermaid"])
    p.add_argument("--json", action="store_true")
    p = graph_sub.add_parser("inspect", help="Inspect a graph node")
    p.add_argument("target")
    p.add_argument("--workspace")
    p.add_argument("--json", action="store_true")

    p_decision = sub.add_parser("decision", help="Manage v1 Decision Objects")
    decision_sub = p_decision.add_subparsers(dest="decision_command", required=True)
    p = decision_sub.add_parser("new", help="Create a v1 Decision Object")
    p.add_argument("--title", required=True)
    p.add_argument("--question", required=True)
    p.add_argument("--option", action="append", required=True)
    p.add_argument("--default-action", required=True)
    p.add_argument("--owner", default="designer")
    p.add_argument("--type", dest="decision_type", default="prototype_direction")
    p.add_argument("--boundary", default="near", choices=["undefined", "far", "near", "locked"])
    p.add_argument("--stakes", default="medium", choices=["low", "medium", "high", "critical"])
    p.add_argument("--reversibility", default="reversible", choices=["reversible", "costly_to_reverse", "irreversible"])
    p.add_argument("--rollback-trigger", default="")
    p.add_argument("--workspace")
    p.add_argument("--json", action="store_true")
    for name in ("list",):
        p = decision_sub.add_parser(name, help="List v1 decisions")
        p.add_argument("--workspace")
        p.add_argument("--json", action="store_true")
    p = decision_sub.add_parser("inspect", help="Inspect a v1 decision")
    p.add_argument("decision_id")
    p.add_argument("--workspace")
    p.add_argument("--json", action="store_true")
    for name in ("accept", "reject"):
        p = decision_sub.add_parser(name, help=f"{name.title()} a v1 decision")
        p.add_argument("decision_id")
        p.add_argument("--by", required=True)
        p.add_argument("--reason", required=True)
        p.add_argument("--workspace")
        p.add_argument("--json", action="store_true")
    p = decision_sub.add_parser("supersede", help="Mark a v1 decision as superseded")
    p.add_argument("decision_id")
    p.add_argument("--by", required=True)
    p.add_argument("--reason", required=True)
    p.add_argument("--superseded-by", required=True)
    p.add_argument("--workspace")
    p.add_argument("--json", action="store_true")

    p_assumption = sub.add_parser("assumption", help="Manage v1 assumptions")
    assumption_sub = p_assumption.add_subparsers(dest="assumption_command", required=True)
    p = assumption_sub.add_parser("new", help="Create an assumption linked to a decision")
    p.add_argument("--decision", required=True)
    p.add_argument("--statement", required=True)
    p.add_argument("--type", default="design")
    p.add_argument("--risk", default="medium", choices=["low", "medium", "high", "critical"])
    p.add_argument("--confidence", default="low", choices=["low", "medium", "high"])
    p.add_argument("--test-method", default="")
    p.add_argument("--kill-condition", default="")
    p.add_argument("--workspace")
    p.add_argument("--json", action="store_true")
    p = assumption_sub.add_parser("list", help="List assumptions")
    p.add_argument("--workspace")
    p.add_argument("--json", action="store_true")
    p = assumption_sub.add_parser("validate", help="Update assumption validation status")
    p.add_argument("assumption_id")
    p.add_argument("--status", required=True, choices=["untested", "planned", "tested", "validated", "invalidated", "waived"])
    p.add_argument("--reason", required=True)
    p.add_argument("--workspace")
    p.add_argument("--json", action="store_true")

    p_evidence = sub.add_parser("evidence", help="Manage v1 evidence ledger entries")
    evidence_sub = p_evidence.add_subparsers(dest="evidence_command", required=True)
    p = evidence_sub.add_parser("add", help="Add evidence linked to a decision")
    p.add_argument("--decision", required=True)
    p.add_argument("--summary", required=True)
    p.add_argument("--source-type", default="other", choices=["screenshot", "video", "playtest", "interview", "data", "benchmark", "inference", "experience", "other"])
    p.add_argument("--source-status", default="private", choices=["private", "synthetic", "public", "cleared", "needs_review"])
    p.add_argument("--confidence", default="medium", choices=["low", "medium", "high"])
    p.add_argument("--decision-impact", default="")
    p.add_argument("--unsupported-claim", action="append", default=[])
    p.add_argument("--workspace")
    p.add_argument("--json", action="store_true")
    p = evidence_sub.add_parser("list", help="List evidence entries")
    p.add_argument("--workspace")
    p.add_argument("--json", action="store_true")
    p = evidence_sub.add_parser("inspect", help="Inspect evidence")
    p.add_argument("evidence_id")
    p.add_argument("--workspace")
    p.add_argument("--json", action="store_true")

    p_experiment = sub.add_parser("experiment", help="Manage v1 experiments")
    experiment_sub = p_experiment.add_subparsers(dest="experiment_command", required=True)
    p = experiment_sub.add_parser("plan", help="Create an experiment plan")
    p.add_argument("--decision", required=True)
    p.add_argument("--assumption", action="append", required=True)
    p.add_argument("--title", required=True)
    p.add_argument("--hypothesis", required=True)
    p.add_argument("--method", required=True)
    p.add_argument("--success", action="append", required=True)
    p.add_argument("--failure", action="append", required=True)
    p.add_argument("--sample-size", type=int)
    p.add_argument("--workspace")
    p.add_argument("--json", action="store_true")
    p = experiment_sub.add_parser("result", help="Record an experiment result")
    p.add_argument("experiment_id")
    p.add_argument("--status", required=True, choices=["passed", "failed", "mixed", "inconclusive"])
    p.add_argument("--observation", action="append", required=True)
    p.add_argument("--evidence", action="append", default=[])
    p.add_argument("--decision-delta", default="")
    p.add_argument("--workspace")
    p.add_argument("--json", action="store_true")
    p = experiment_sub.add_parser("review", help="Review an experiment result")
    p.add_argument("experiment_id")
    p.add_argument("--by", required=True)
    p.add_argument("--summary", required=True)
    p.add_argument("--workspace")
    p.add_argument("--json", action="store_true")

    p_workflow = sub.add_parser("workflow", help="Run v1 project workflows")
    workflow_sub = p_workflow.add_subparsers(dest="workflow_command", required=True)
    p = workflow_sub.add_parser("list", help="List built-in workflows")
    p.add_argument("--json", action="store_true")
    p = workflow_sub.add_parser("start", help="Start a workflow run")
    p.add_argument("workflow_id")
    p.add_argument("--workspace")
    p.add_argument("--json", action="store_true")
    for name in ("status", "next", "validate"):
        p = workflow_sub.add_parser(name, help=f"{name.title()} a workflow run")
        p.add_argument("run_id")
        p.add_argument("--workspace")
        p.add_argument("--json", action="store_true")

    p = sub.add_parser("new", help="Create and register an asset stub")
    p.add_argument("asset_type", choices=sorted(ASSET_SPECS))
    p.add_argument("--title")
    p.add_argument("--filename")
    p.add_argument("--created-by", default="human-agent", choices=["human", "agent", "human-agent", "import"])
    p.add_argument("--source-status", choices=["private", "synthetic", "public", "cleared", "needs_review"])
    p.add_argument("--workspace")
    p.add_argument("--dry-run", action="store_true")
    p.add_argument("--json", action="store_true")

    p = sub.add_parser("voi", help="Create or review a Decision-to-Information gate")
    p.add_argument("decision_id", nargs="?")
    p.add_argument("--input")
    p.add_argument("--write", action="store_true")
    p.add_argument("--decision", dest="decision_question")
    p.add_argument("--default-action")
    p.add_argument("--option", action="append", default=[])
    p.add_argument("--owner")
    p.add_argument("--deadline")
    p.add_argument("--stakes", default="medium", choices=["low", "medium", "high", "critical"])
    p.add_argument("--reversibility", default="reversible", choices=["reversible", "costly_to_reverse", "irreversible"])
    p.add_argument("--boundary", default="undefined", choices=["undefined", "far", "near", "locked"])
    p.add_argument("--candidate-info", action="append", default=[])
    p.add_argument("--stop-when", action="append", default=[])
    p.add_argument("--output")
    p.add_argument("--workspace")
    p.add_argument("--dry-run", action="store_true")
    p.add_argument("--json", action="store_true")

    p = sub.add_parser("pack", help="Create a review-safe bundle")
    p.add_argument("--mode", default="internal-review", choices=["internal-review", "publisher", "public-synthetic"])
    p.add_argument("--output")
    p.add_argument("--workspace")
    p.add_argument("--dry-run", action="store_true")
    p.add_argument("--force", action="store_true")
    p.add_argument("--json", action="store_true")
    return parser


def _run(args: argparse.Namespace) -> int:
    if args.command == "demo":
        result = create_lighthouse_demo(_path(args.destination))
        decision = result["decision"]
        assumption = result["assumption"]
        evidence = result["evidence"]
        experiment = result["experiment"]
        human_gate = result["human_gate"]
        text = (
            f"GameDesignOS demo 已生成：{result['workspace']}\n"
            "模式：public-synthetic｜模型调用：0｜无需密钥\n"
            f"Decision：{decision['decision_id']} [{decision['status']}] "
            f"{decision['current_default_action']}\n"
            f"Assumption：{assumption['assumption_id']} [{assumption['status']}] "
            f"{assumption['statement']}\n"
            f"Evidence：{evidence['evidence_id']} [{evidence['source_status']}] "
            f"{evidence['summary']}\n"
            f"Experiment：{experiment['experiment_id']} "
            f"[{experiment['outcome']}/{experiment['review_status']}]\n"
            f"Human Gate：{human_gate['status']} — {human_gate['reason']}\n"
            f"下一步：{result['next_action']['reason']}\n"
            f"命令提示：{result['next_action']['command_hint']}\n"
            "证据边界：synthetic fixture 不证明真实留存、商业需求、模型质量或发布准备度。"
        )
        _emit(result, as_json=args.json, text=text)
        return EXIT_OK

    if args.command == "ask":
        sentence = " ".join(args.text).strip()
        workspace = _open_workspace_safely(_path(args.workspace))
        route = route_project_task(sentence, workspace=workspace)
        selected = route.get("selected_skill")
        start_result = None
        # Routing confidence describes match quality, not authorization to write.
        # `ask` creates or resumes a workspace only when the user supplies a path.
        should_start = bool(args.destination or args.workspace)
        if should_start:
            destination = (
                _path(args.destination)
                or (workspace.root if workspace else None)
                or _path(args.workspace)
            )
            start_result = start_project(
                project_name=_title_from_sentence(sentence),
                destination=destination,
                owner=args.owner,
                visibility=args.visibility,
                question=f"围绕这句话，第一轮最应该验证什么，才能决定是否继续投入？{sentence}",
                assumption="这个想法的核心体验能在三分钟内被理解，并产生继续尝试的动机。",
            )
            workspace = Workspace.open(Path(start_result["workspace"]))
            route = route_project_task(sentence, workspace=workspace)
            selected = route.get("selected_skill")

        result = {
            "input": sentence,
            "route": route,
            "workspace": start_result,
            "single_skill_prompt": _single_skill_prompt(selected, sentence),
            "agent_instruction": (
                "宿主 agent 应直接读取并执行推荐 skill；不要让用户复制提示词。"
                "只有需求不清或触发 Human Gate 时才追问。"
            ),
        }
        text = f"已接住：{sentence}\n推荐 skill：{selected or '暂未匹配'}\n原因：{route['reason']}"
        if start_result:
            text += (
                f"\n项目工作区：{start_result['workspace']}"
                f"\n下一步只做一件事：{start_result['next_step']}"
                f"\n记录时用：{start_result['record_evidence_command']}"
            )
        text += f"\n执行规则：{result['agent_instruction']}"
        text += f"\n手动单独用 skill 时可发：\n{result['single_skill_prompt']}"
        _emit(result, as_json=args.json, text=text)
        return EXIT_OK

    if args.command == "init":
        destination = _path(args.destination) or (Path.cwd() / args.project_name)
        result = init_workspace(
            project_name=args.project_name,
            destination=destination,
            codename=args.codename,
            visibility=args.visibility,
            owner=args.owner,
            workspace_version=args.workspace_version,
            force=args.force,
            dry_run=args.dry_run,
        )
        text = f"{'Would create' if args.dry_run else 'Created'} workspace: {result['workspace']}\nProject ID: {result['project_id']}"
        if not args.dry_run:
            text += "\nNext: review game.designos.yaml, define a Decision Object, then run `gamedesignos route <task>`."
        _emit(result, as_json=args.json, text=text)
        return EXIT_OK

    if args.command == "start":
        project_name = _joined(args.project_name)
        result = start_project(
            project_name=project_name,
            destination=_path(args.destination),
            owner=args.owner,
            visibility=args.visibility,
            question=args.question,
            options=args.option,
            default_action=args.default_action,
            assumption=args.assumption,
            test_method=args.test_method,
            success_criteria=args.success,
            failure_criteria=args.failure,
            rollback_trigger=args.rollback_trigger,
            sample_size=args.sample_size,
        )
        text = (
            f"已准备好：{result['workspace']}\n"
            f"决策：{result['decision']['decision_id']}\n"
            f"假设：{result['assumption']['assumption_id']}\n"
            f"实验：{result['experiment']['experiment_id']}\n"
            f"工作流：{result['workflow_run']['run_id']}\n"
            f"下一步只做一件事：{result['next_step']}\n"
            f"记录时用：{result['record_evidence_command']}"
        )
        _emit(result, as_json=args.json, text=text)
        return EXIT_OK

    if args.command == "status":
        status = get_project_status(_workspace(args))
        text = (
            f"{status['title']} [{status['project_id']}]\nStatus: {status['project_status']} | Visibility: {status['visibility']}\n"
            f"Workspace schema: {status['workspace_schema_version']} | Declared runtime: {status['runtime_version_declared']} | Current CLI: {status['runtime_version_current']}\n"
            f"Assets: {sum(status['asset_counts_by_type'].values())} | Accepted decisions: {status['accepted_decisions']} | Open Human Gates: {status['unresolved_human_gates']}\n"
            f"Compatibility: {'OK' if status['compatible'] else 'FAILED'}"
        )
        _emit(status, as_json=args.json, text=text)
        return EXIT_OK if status["compatible"] else EXIT_INCOMPATIBLE_VERSION

    if args.command == "route":
        workspace = _workspace(args) if args.workspace else None
        if not args.workspace:
            try:
                workspace = Workspace.open()
            except GameDesignOSError:
                pass
        result = route_project_task(" ".join(args.task), workspace=workspace)
        selected = result.get("selected_skill") or "no stable route"
        text = f"Route: {selected}"
        if result.get("target_skill") and result["target_skill"] != selected:
            text += f" -> then {result['target_skill']}"
        text += f"\nReason: {result['reason']}"
        if result.get("missing_upstream"):
            text += "\nMissing upstream: " + ", ".join(result["missing_upstream"])
        text += "\nThis command recommends a route; it does not execute a skill."
        _emit(result, as_json=args.json, text=text)
        return EXIT_OK

    if args.command == "health":
        result = get_project_health(_workspace(args))
        blockers = []
        if result["high_impact_decisions_without_rollback"]:
            blockers.append(
                "High-impact decisions without rollback: "
                + ", ".join(result["high_impact_decisions_without_rollback"])
            )
        if result["high_risk_untested_assumptions"]:
            blockers.append(
                "High-risk untested assumptions: "
                + ", ".join(result["high_risk_untested_assumptions"])
            )
        text = (
            f"Decisions: {result['decisions']} | Assumptions: {result['assumptions']} | "
            f"Evidence: {result['evidence_items']} | Experiments: {result['experiments']}\n"
            f"Project-Ready health: {'OK' if result['ok'] else 'NEEDS ATTENTION'}"
        )
        if blockers:
            text += "\n- " + "\n- ".join(blockers)
        _emit(result, as_json=args.json, text=text)
        return EXIT_OK if result["ok"] else EXIT_VALIDATION

    if args.command == "next":
        result = get_next_action(_workspace(args))
        text = f"Next: {result['action']}"
        if result.get("target"):
            text += f" -> {result['target']}"
        text += f"\nReason: {result['reason']}\nHint: {result['command_hint']}"
        _emit(result, as_json=args.json, text=text)
        return EXIT_OK

    if args.command == "gate":
        if args.gate_command == "run":
            workspace = _workspace(args)
            result = (
                run_gate(workspace, args.gate_type, args.target, write=True)
                if args.write
                else preview_gate(workspace, args.gate_type, args.target)
            )
            text = f"{result['gate_type']} gate for {result['target']}: {result['status']}\n{result['reason']}"
            if result["required_actions"]:
                text += "\nRequired actions:\n- " + "\n- ".join(result["required_actions"])
            if result["blocked_actions"]:
                text += "\nBlocked actions:\n- " + "\n- ".join(result["blocked_actions"])
            if result["human_gate_required"]:
                text += "\nHuman Gate required."
            _emit(result, as_json=args.json, text=text)
            return EXIT_VALIDATION if result["status"] == "block" else EXIT_OK

    if args.command == "graph":
        if args.graph_command == "export":
            result = export_project_graph(_workspace(args), format=args.format)
            _emit(result, as_json=args.json, text=result["graph"])
            return EXIT_OK
        if args.graph_command == "inspect":
            result = inspect_project_graph(_workspace(args), args.target)
            text = (
                f"{result['target']['id']} [{result['target']['type']}]\n"
                f"Incoming: {len(result['incoming'])} | Outgoing: {len(result['outgoing'])}"
            )
            _emit(result, as_json=args.json, text=text)
            return EXIT_OK

    if args.command == "decision":
        workspace = _workspace(args)
        if args.decision_command == "new":
            result = create_decision(
                workspace,
                title=args.title,
                question=args.question,
                options=args.option,
                default_action=args.default_action,
                owner=args.owner,
                decision_type=args.decision_type,
                boundary=args.boundary,
                stakes=args.stakes,
                reversibility=args.reversibility,
                rollback_trigger=args.rollback_trigger,
            )
            text = (
                f"已创建 Decision Object: {result['decision']['decision_id']}\n"
                f"下一步: 登记关键假设，或运行 `gamedesignos gate run voi {result['decision']['decision_id']}`。"
            )
            _emit(result, as_json=args.json, text=text)
            return EXIT_OK
        if args.decision_command == "list":
            result = {"decisions": list_decisions(workspace)}
            text = "\n".join(
                f"{item['decision_id']} [{item['status']}] {item['title']}"
                for item in result["decisions"]
            ) or "暂无 Decision Object。"
            _emit(result, as_json=args.json, text=text)
            return EXIT_OK
        if args.decision_command == "inspect":
            result = inspect_project_decision(workspace, args.decision_id)
            text = f"{result['decision_id']} [{result['status']}]\n{result['decision_question']}"
            _emit(result, as_json=args.json, text=text)
            return EXIT_OK
        if args.decision_command in {"accept", "reject"}:
            status = "accepted" if args.decision_command == "accept" else "rejected"
            result = update_decision_status(
                workspace,
                args.decision_id,
                status=status,
                by=args.by,
                reason=args.reason,
            )
            _emit(result, as_json=args.json, text=f"Decision {args.decision_id} 已标记为 {status}。")
            return EXIT_OK
        if args.decision_command == "supersede":
            result = update_decision_status(
                workspace,
                args.decision_id,
                status="superseded",
                by=args.by,
                reason=args.reason,
                supersedes=args.superseded_by,
            )
            _emit(result, as_json=args.json, text=f"Decision {args.decision_id} 已标记为 superseded。")
            return EXIT_OK

    if args.command == "assumption":
        workspace = _workspace(args)
        if args.assumption_command == "new":
            result = create_assumption(
                workspace,
                decision_id=args.decision,
                statement=args.statement,
                assumption_type=args.type,
                risk_level=args.risk,
                confidence=args.confidence,
                test_method=args.test_method,
                kill_condition=args.kill_condition,
            )
            _emit(
                result,
                as_json=args.json,
                text=f"已创建 Assumption: {result['assumption']['assumption_id']}",
            )
            return EXIT_OK
        if args.assumption_command == "list":
            result = {"assumptions": list_assumptions(workspace)}
            text = "\n".join(
                f"{item.get('assumption_id')} [{item.get('validation_status')}] {item.get('statement')}"
                for item in result["assumptions"]
            ) or "暂无 Assumption。"
            _emit(result, as_json=args.json, text=text)
            return EXIT_OK
        if args.assumption_command == "validate":
            result = validate_assumption(
                workspace,
                args.assumption_id,
                status=args.status,
                reason=args.reason,
            )
            _emit(result, as_json=args.json, text=f"Assumption {args.assumption_id} 已更新为 {args.status}。")
            return EXIT_OK

    if args.command == "evidence":
        workspace = _workspace(args)
        if args.evidence_command == "add":
            result = add_evidence(
                workspace,
                decision_id=args.decision,
                summary=args.summary,
                source_type=args.source_type,
                source_status=args.source_status,
                confidence=args.confidence,
                decision_impact=args.decision_impact,
                unsupported_claims=args.unsupported_claim,
            )
            _emit(result, as_json=args.json, text=f"已登记 Evidence: {result['evidence']['evidence_id']}")
            return EXIT_OK
        if args.evidence_command == "list":
            result = {"evidence": list_evidence(workspace)}
            text = "\n".join(
                f"{item.get('evidence_id')} [{item.get('confidence')}] {item.get('summary')}"
                for item in result["evidence"]
            ) or "暂无 Evidence。"
            _emit(result, as_json=args.json, text=text)
            return EXIT_OK
        if args.evidence_command == "inspect":
            result = inspect_project_evidence(workspace, args.evidence_id)
            _emit(result, as_json=args.json, text=f"{result['evidence_id']}\n{result['summary']}")
            return EXIT_OK

    if args.command == "experiment":
        workspace = _workspace(args)
        if args.experiment_command == "plan":
            result = plan_experiment(
                workspace,
                decision_id=args.decision,
                assumption_ids=args.assumption,
                title=args.title,
                hypothesis=args.hypothesis,
                method=args.method,
                success_criteria=args.success,
                failure_criteria=args.failure,
                sample_size=args.sample_size,
            )
            _emit(result, as_json=args.json, text=f"已创建 Experiment Plan: {result['experiment']['experiment_id']}")
            return EXIT_OK
        if args.experiment_command == "result":
            result = add_experiment_result(
                workspace,
                args.experiment_id,
                status=args.status,
                observations=args.observation,
                evidence_refs=args.evidence,
                decision_delta=args.decision_delta,
            )
            _emit(result, as_json=args.json, text=f"已记录 Experiment Result: {args.experiment_id}")
            return EXIT_OK
        if args.experiment_command == "review":
            result = review_experiment(
                workspace,
                args.experiment_id,
                by=args.by,
                summary=args.summary,
            )
            _emit(result, as_json=args.json, text=f"已复盘 Experiment: {args.experiment_id}")
            return EXIT_OK

    if args.command == "workflow":
        if args.workflow_command == "list":
            result = {"workflows": list_workflows()}
            text = "\n".join(
                f"{item['workflow_id']} ({item['title']})" for item in result["workflows"]
            )
            _emit(result, as_json=args.json, text=text)
            return EXIT_OK
        workspace = _workspace(args)
        if args.workflow_command == "start":
            result = start_workflow(workspace, args.workflow_id)
            _emit(result, as_json=args.json, text=f"已启动 Workflow Run: {result['workflow_run']['run_id']}")
            return EXIT_OK
        if args.workflow_command == "status":
            result = workflow_status(workspace, args.run_id)
            _emit(result, as_json=args.json, text=f"{result['run_id']} [{result['status']}] 当前节点: {result.get('current_node')}")
            return EXIT_OK
        if args.workflow_command == "next":
            result = workflow_next(workspace, args.run_id)
            hint = result["next"].get("hint")
            text = f"{result['next']['status']}: {result['next']['reason']}"
            if hint:
                text += f"\nHint: {hint}"
            _emit(result, as_json=args.json, text=text)
            return EXIT_OK if result["next"]["status"] != "blocked" else EXIT_VALIDATION
        if args.workflow_command == "validate":
            result = validate_workflow_run(workspace, args.run_id)
            text = "Workflow validation passed." if result["ok"] else "Workflow validation failed:\n- " + "\n- ".join(result["errors"])
            _emit(result, as_json=args.json, text=text)
            return EXIT_OK if result["ok"] else EXIT_VALIDATION

    if args.command == "new":
        result = _workspace(args).create_asset(
            args.asset_type,
            title=args.title,
            filename=args.filename,
            created_by=args.created_by,
            source_status=args.source_status,
            dry_run=args.dry_run,
        )
        _emit(result, as_json=args.json, text=f"{'Would create' if args.dry_run else 'Created'} {args.asset_type}: {result['asset']['asset_id']}\nPath: {result['asset']['path']}")
        return EXIT_OK

    if args.command == "validate":
        report = validate_project_workspace(_workspace(args), repo_root=_path(args.repo_root))
        text = "Workspace validation passed." if report["ok"] else "Workspace validation failed:\n- " + "\n- ".join(report["errors"])
        if report["warnings"]:
            text += "\nWarnings:\n- " + "\n- ".join(report["warnings"])
        _emit(report, as_json=args.json, text=text)
        incompatible = any("Unsupported workspace schema" in item or "incompatible with runtime" in item for item in report["errors"])
        return EXIT_OK if report["ok"] else (EXIT_INCOMPATIBLE_VERSION if incompatible else EXIT_VALIDATION)

    if args.command == "voi":
        if args.input:
            input_path = Path(args.input).expanduser()
            if not input_path.is_absolute() and args.workspace:
                input_path = Path(args.workspace).expanduser() / input_path
            result = review_assessment(input_path, write=args.write)
            text = "VOI assessment review passed." if result["ok"] else "VOI assessment review failed:\n- " + "\n- ".join(result["errors"])
            if result["recommendations"]:
                text += "\nRecommendations:\n- " + "\n- ".join(result["recommendations"])
            _emit(result, as_json=args.json, text=text)
            return EXIT_OK if result["ok"] else EXIT_VALIDATION
        required = {"decision_id": args.decision_id, "decision": args.decision_question, "default action": args.default_action, "owner": args.owner}
        missing = [name for name, value in required.items() if not value]
        if missing:
            raise UsageError("Missing VOI fields: " + ", ".join(missing))
        result = create_assessment(
            _workspace(args),
            decision_id=args.decision_id,
            decision_question=args.decision_question,
            options=args.option,
            current_default_action=args.default_action,
            owner=args.owner,
            deadline=args.deadline,
            stakes=args.stakes,
            reversibility=args.reversibility,
            boundary=args.boundary,
            candidate_information_actions=args.candidate_info,
            stop_when=args.stop_when or None,
            output=_path(args.output),
            dry_run=args.dry_run,
        )
        _emit(result, as_json=args.json, text=f"{'Would create' if args.dry_run else 'Created'} VOI assessment: {result['path']}\n{result['next_action']}")
        return EXIT_OK

    if args.command == "pack":
        result = _workspace(args).pack(mode=args.mode, output=_path(args.output), dry_run=args.dry_run, force=args.force)
        _emit(result, as_json=args.json, text=f"{'Would create' if args.dry_run else 'Created'} pack: {result['output']}\nIncluded assets: {len(result['included_assets'])}")
        return EXIT_OK

    if args.command == "doctor":
        result = doctor(_path(args.workspace))
        lines = [f"GameDesignOS runtime {result['runtime_version']}"] + [f"{'OK' if item['ok'] else 'FAIL'} {item['name']}: {item['detail']}" for item in result["checks"]]
        _emit(result, as_json=args.json, text="\n".join(lines))
        return EXIT_OK if result["ok"] else EXIT_VALIDATION
    raise UsageError(f"Unknown command: {args.command}")


def main(argv: Sequence[str] | None = None) -> int:
    _configure_utf8_stdio()
    parser = build_parser()
    raw_args = list(sys.argv[1:] if argv is None else argv)
    if raw_args and raw_args[0] not in KNOWN_COMMANDS and not raw_args[0].startswith("-"):
        raw_args = ["ask", *raw_args]
    try:
        return _run(parser.parse_args(raw_args))
    except GameDesignOSError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return exc.exit_code
    except OSError as exc:
        print(f"error: filesystem operation failed: {exc}", file=sys.stderr)
        return EXIT_VALIDATION
    except KeyboardInterrupt:
        print("error: interrupted", file=sys.stderr)
        return 130


if __name__ == "__main__":
    raise SystemExit(main())
