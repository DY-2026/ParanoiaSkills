#!/usr/bin/env python3
"""Validate the public GameDesignOS repository, Runtime Foundation, and VOI Decision Gate."""

from __future__ import annotations

import re
import tomllib
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator

from validate_skill import _parse_json, _parse_yaml, validate_skill


REQUIRED_SKILLS = [
    "game-experience-analyzer",
    "game-concept-architect",
    "paranoia-ai-system-evolver",
    "game-design-book-translator",
    "game-design-source-curator",
    "game-experience-density-optimizer",
    "game-design-proposal-writer",
]

REQUIRED_PATHS = [
    ".gitignore",
    "README.md",
    "README.zh-CN.md",
    "README.en.md",
    "AGENTS.md",
    "CHANGELOG.md",
    "CONTRIBUTING.md",
    "LICENSE",
    "SECURITY.md",
    "MANIFEST.in",
    "setup.py",
    "gamedesignos/_version.py",
    "gamedesignos/application/__init__.py",
    "gamedesignos/application/project_queries.py",
    "gamedesignos/demo.py",
    "adapters/README.md",
    "adapters/openai-compatible.md",
    "contracts/README.md",
    "contracts/router.yaml",
    "contracts/intent-work-order.schema.json",
    "contracts/ed-handoff.schema.json",
    "contracts/project-workspace.schema.json",
    "contracts/design-asset-index.schema.json",
    "contracts/decision-log.schema.json",
    "contracts/decision.schema.json",
    "contracts/assumption-registry.schema.json",
    "contracts/evidence-ledger.schema.json",
    "contracts/experiment-plan.schema.json",
    "contracts/experiment-result.schema.json",
    "contracts/learning-record.schema.json",
    "contracts/gate-result.schema.json",
    "contracts/workflow-run.schema.json",
    "contracts/ul-state.schema.json",
    "contracts/information-value-assessment.schema.json",
    "docs/product/README.md",
    "docs/product/vision.md",
    "docs/product/architecture.md",
    "docs/product/mvp-definition.md",
    "docs/product/roadmap.md",
    "docs/product/v1.4-mcp-boundary-rfc.md",
    "docs/how-to-use.zh-CN.md",
    "docs/try-it-in-10-minutes.zh-CN.md",
    "docs/GITHUB_ABOUT.md",
    "docs/github-about-checklist.md",
    "docs/2026-08-15-deepseek-harness-engineering-fit.md",
    "docs/workflows/README.md",
    "docs/workflows/decision-to-information.md",
    "docs/workflows/idea-to-validation.md",
    "docs/workflows/media-to-diagnosis.md",
    "docs/workflows/weekly-ed-experiment.md",
    "docs/workflows/evidence-to-proposal.md",
    "runtime/README.md",
    "runtime/cli/README.md",
    "runtime/cli/commands.md",
    "runtime/workspace-template/README.md",
    "runtime/workspace-template/game.designos.yaml",
    "runtime/workspace-template/design-asset-index.example.json",
    "runtime/workspace-template/06-decisions/decision-brief.template.md",
    "runtime/workspace-template/06-decisions/decision-log.example.json",
    "runtime/workspace-template/06-decisions/information-value-assessment.example.json",
    "runtime/workspace-template-v1/README.md",
    "runtime/workspace-template-v1/game.designos.yaml",
    "runtime/workspace-template-v1/design-asset-index.example.json",
    "runtime/workspace-template-v1/00-inbox/README.md",
    "runtime/workspace-template-v1/01-decisions/DEC-PROTOTYPE-001.example.json",
    "runtime/workspace-template-v1/02-assumptions/assumption-registry.example.json",
    "runtime/workspace-template-v1/03-evidence/evidence-ledger.example.json",
    "runtime/workspace-template-v1/04-experiments/EXP-COMPREHENSION-001/experiment-plan.example.json",
    "docs/product/v1.0-development-plan.md",
    "paranoia-ai-system-evolver/references/value-of-information-playbook.md",
    "paranoia-ai-system-evolver/references/value-of-information-playbook.zh-CN.md",
    "paranoia-ai-system-evolver/references/value-of-information-playbook.en.md",
    "paranoia-ai-system-evolver/references/intent-engineering-work-order.md",
    "paranoia-ai-system-evolver/references/intent-engineering-work-order.zh-CN.md",
    "paranoia-ai-system-evolver/references/intent-engineering-work-order.en.md",
    "paranoia-ai-system-evolver/references/project-workflow-governance.md",
    "paranoia-ai-system-evolver/references/project-workflow-governance.zh-CN.md",
    "paranoia-ai-system-evolver/references/project-workflow-governance.en.md",
    "paranoia-ai-system-evolver/references/uncertainty-ladder-protocol.md",
    "paranoia-ai-system-evolver/references/uncertainty-ladder-protocol.zh-CN.md",
    "paranoia-ai-system-evolver/references/uncertainty-ladder-protocol.en.md",
    "paranoia-ai-system-evolver/templates/voi_decision_gate.md",
    "paranoia-ai-system-evolver/templates/voi_decision_gate.zh-CN.md",
    "paranoia-ai-system-evolver/templates/voi_decision_gate.en.md",
    "paranoia-ai-system-evolver/templates/intent_work_order.md",
    "paranoia-ai-system-evolver/templates/intent_work_order.zh-CN.md",
    "paranoia-ai-system-evolver/templates/intent_work_order.en.md",
    "paranoia-ai-system-evolver/templates/workflow_governance_review.md",
    "paranoia-ai-system-evolver/templates/workflow_governance_review.zh-CN.md",
    "paranoia-ai-system-evolver/templates/workflow_governance_review.en.md",
    "paranoia-ai-system-evolver/templates/uncertainty_ladder_state.md",
    "paranoia-ai-system-evolver/templates/uncertainty_ladder_state.zh-CN.md",
    "paranoia-ai-system-evolver/templates/uncertainty_ladder_state.en.md",
    "paranoia-ai-system-evolver/evals/voi-decision-gate-cases.md",
    "paranoia-ai-system-evolver/evals/voi-decision-gate-cases.en.md",
    "paranoia-ai-system-evolver/evals/uncertainty-ladder-cases.md",
    "paranoia-ai-system-evolver/evals/uncertainty-ladder-cases.en.md",
    "paranoia-ai-system-evolver/examples/ul-state.example.json",
    "releases/v1.2.0.md",
    "releases/v1.1.0.md",
    "releases/v1.0.0.md",
    "releases/v0.8.0.md",
    ".github/workflows/validate.yml",
    "scripts/run_behavior_evals.py",
    "scripts/validate_agent_skills.py",
    "scripts/smoke_installed_wheel.py",
    "scripts/smoke_sdist_rebuild.py",
    "scripts/create_golden_project.py",
    "scripts/tests/test_application_services.py",
    "examples/golden-lighthouse/README.md",
    "examples/hosts/README.md",
    "examples/hosts/openai_compatible.py",
    "examples/hosts/fixtures/openai-chat-completion.json",
]

WORKSPACE_TEMPLATE_DIRS = {
    "inbox_dir": "00-inbox",
    "concept_dir": "01-concept",
    "evidence_dir": "02-evidence",
    "analysis_dir": "03-analysis",
    "proposals_dir": "04-proposals",
    "experiments_dir": "05-experiments",
    "decisions_dir": "06-decisions",
    "retrospectives_dir": "07-retrospectives",
}

WORKSPACE_REQUIRED_RULES = {
    "evidence_before_opinion",
    "feasibility_before_scope",
    "workflow_before_one_off_prompts",
    "voi_before_research",
    "eval_before_promotion",
    "rollback_before_confidence",
    "human_gate_for_commitments",
    "decision_before_information",
    "action_change_before_research",
    "sample_before_scale",
    "stop_when_marginal_voi_nonpositive",
    "preserve_local_negative_evidence",
}

SKIP_DIRS = {
    ".git",
    "__pycache__",
    ".pytest_cache",
    ".ruff_cache",
    "_private_translations",
    ".venv",
    "venv",
    "node_modules",
}

PRIVATE_IGNORE_RULES = {"_private_translations/"}


def _iter_data_files(repo_root: Path):
    for path in sorted(repo_root.rglob("*")):
        if not path.is_file():
            continue
        if any(part in SKIP_DIRS for part in path.relative_to(repo_root).parts):
            continue
        if path.suffix == ".json" or path.suffix in {".yaml", ".yml"}:
            yield path


def _check_required_paths(repo_root: Path, errors: list[str]) -> None:
    for relative in REQUIRED_PATHS:
        if not (repo_root / relative).exists():
            errors.append(f"{relative}: required path missing")


def _check_private_ignore_rules(repo_root: Path, errors: list[str]) -> None:
    gitignore = repo_root / ".gitignore"
    if not gitignore.exists():
        return
    rules = {
        line.strip()
        for line in gitignore.read_text(encoding="utf-8").splitlines()
        if line.strip() and not line.lstrip().startswith("#")
    }
    for required in sorted(PRIVATE_IGNORE_RULES):
        accepted = {
            required,
            required.rstrip("/"),
            f"/{required}",
            f"/{required.rstrip('/')}",
        }
        if rules.isdisjoint(accepted):
            errors.append(f".gitignore: missing required private ignore rule {required}")


def _check_repo_data_files(repo_root: Path, errors: list[str]) -> None:
    for path in _iter_data_files(repo_root):
        if path.suffix == ".json":
            data = _parse_json(path, errors)
            if path.name.endswith(".schema.json"):
                if not isinstance(data, dict):
                    errors.append(f"{path}: schema file must be a JSON object")
                elif "$schema" not in data:
                    errors.append(f"{path}: *.schema.json must contain $schema")
        else:
            _parse_yaml(path, errors)


def _require_mapping(data: Any, path: Path, label: str, errors: list[str]) -> dict[str, Any]:
    if not isinstance(data, dict):
        errors.append(f"{path}: {label} must be a mapping")
        return {}
    return data


def _check_workspace_example(path: Path, errors: list[str]) -> dict[str, Any]:
    if not path.exists():
        return {}
    data = _parse_json(path, errors)
    if not isinstance(data, dict):
        return {}
    if data.get("schema_version") != "0.8.0":
        errors.append(f"{path}: schema_version must be 0.8.0")
    workspace_id = data.get("workspace_id")
    if not isinstance(workspace_id, str) or not workspace_id.strip():
        errors.append(f"{path}: workspace_id must be non-empty")
    return data


def _check_workspace_template(repo_root: Path, errors: list[str]) -> None:
    workspace_root = repo_root / "runtime" / "workspace-template"
    manifest_path = workspace_root / "game.designos.yaml"

    for directory in WORKSPACE_TEMPLATE_DIRS.values():
        guide = workspace_root / directory / "README.md"
        if not guide.exists():
            errors.append(
                f"runtime/workspace-template/{directory}/README.md: "
                "required workspace guide missing"
            )

    if not manifest_path.exists():
        return

    manifest = _require_mapping(
        _parse_yaml(manifest_path, errors), manifest_path, "workspace manifest", errors
    )
    if not manifest:
        return

    if manifest.get("schema_version") != "0.8.0":
        errors.append(f"{manifest_path}: schema_version must be 0.8.0")
    if manifest.get("workspace_type") != "gamedesignos-project":
        errors.append(f"{manifest_path}: workspace_type must be gamedesignos-project")

    project = _require_mapping(manifest.get("project"), manifest_path, "project", errors)
    for field in ("id", "title", "codename", "status", "visibility", "owner"):
        value = project.get(field)
        if not isinstance(value, str) or not value.strip():
            errors.append(f"{manifest_path}: project.{field} must be non-empty")

    designos = _require_mapping(manifest.get("designos"), manifest_path, "designos", errors)
    if designos.get("version") not in {"0.8.0", "0.9.0"}:
        errors.append(f"{manifest_path}: designos.version must be 0.8.0 or 0.9.0")
    if designos.get("public_base_repo") != "DY-2026/GameDesignOS":
        errors.append(f"{manifest_path}: designos.public_base_repo must be DY-2026/GameDesignOS")
    if not isinstance(designos.get("private_overlay"), bool):
        errors.append(f"{manifest_path}: designos.private_overlay must be boolean")

    assets = _require_mapping(manifest.get("assets"), manifest_path, "assets", errors)
    if not isinstance(assets.get("index"), str) or not assets.get("index", "").strip():
        errors.append(f"{manifest_path}: assets.index must be non-empty")
    for field, expected_directory in WORKSPACE_TEMPLATE_DIRS.items():
        value = assets.get(field)
        if value != expected_directory:
            errors.append(f"{manifest_path}: assets.{field} must be {expected_directory}")
        elif not (workspace_root / value).is_dir():
            errors.append(f"{manifest_path}: assets.{field} points to missing directory {value}")

    rules = _require_mapping(manifest.get("rules"), manifest_path, "rules", errors)
    for field in sorted(WORKSPACE_REQUIRED_RULES):
        if rules.get(field) is not True:
            errors.append(f"{manifest_path}: rules.{field} must be true")

    asset_index = _check_workspace_example(
        workspace_root / "design-asset-index.example.json", errors
    )
    types = {
        item.get("asset_type")
        for item in asset_index.get("assets", [])
        if isinstance(item, dict)
    }
    if asset_index and "information-assessment" not in types:
        errors.append(
            f"{workspace_root / 'design-asset-index.example.json'}: "
            "must include an information-assessment asset"
        )

    decision_log = _check_workspace_example(
        workspace_root / "06-decisions" / "decision-log.example.json", errors
    )
    decisions = decision_log.get("decisions", []) if decision_log else []
    if decisions and not any(
        isinstance(item, dict)
        and item.get("decision_type") == "information"
        and item.get("current_default_action")
        and item.get("information_stop_reason")
        for item in decisions
    ):
        errors.append(
            f"{workspace_root / '06-decisions' / 'decision-log.example.json'}: "
            "must demonstrate an information decision with default action and stop reason"
        )

    voi_example = _check_workspace_example(
        workspace_root / "06-decisions" / "information-value-assessment.example.json",
        errors,
    )
    if voi_example:
        decision = voi_example.get("decision")
        if not isinstance(decision, dict) or not decision.get("current_default_action"):
            errors.append("information-value-assessment example lacks current_default_action")
        actions = voi_example.get("candidate_information_actions")
        if not isinstance(actions, list) or len(actions) > 3:
            errors.append("information-value-assessment example must contain at most 3 actions")
        stop_rule = voi_example.get("stop_rule")
        if not isinstance(stop_rule, dict) or not stop_rule.get("stop_when"):
            errors.append("information-value-assessment example lacks stop_rule.stop_when")


def _check_paranoia_voi(repo_root: Path, errors: list[str]) -> None:
    skill_root = repo_root / "paranoia-ai-system-evolver"
    if not skill_root.is_dir():
        return

    skill = (skill_root / "SKILL.md").read_text(encoding="utf-8")
    for marker in (
        "Decision Object",
        "current_default_action",
        "EVPI",
        "EVSI",
        "candidate_information_actions",
        "RJR-AI",
        "剩余判断权",
        "Intent Work Order",
        "reality_to_change",
        "workflow-run.governance",
        "references/project-workflow-governance",
        "references/value-of-information-playbook",
        "references/intent-engineering-work-order",
        "UL（Uncertainty Ladder",
        "references/uncertainty-ladder-protocol",
    ):
        if marker not in skill:
            errors.append(f"paranoia-ai-system-evolver/SKILL.md: missing VOI marker {marker}")

    intent_ref = skill_root / "references" / "intent-engineering-work-order.zh-CN.md"
    if intent_ref.exists():
        text = intent_ref.read_text(encoding="utf-8")
        for marker in ("我要改变什么现实", "验收者第一眼", "ai_must_not_touch", "retrospective_contract"):
            if marker not in text:
                errors.append(f"{intent_ref}: missing intent-work-order marker {marker}")

    intent_template = skill_root / "templates" / "intent_work_order.zh-CN.md"
    if intent_template.exists():
        text = intent_template.read_text(encoding="utf-8")
        for marker in (
            "reality_to_change",
            "first_impression_must_understand",
            "ai_can_freely_change",
            "ai_must_not_touch",
            "promotion_status",
        ):
            if marker not in text:
                errors.append(f"{intent_template}: missing intent template field {marker}")

    governance_ref = skill_root / "references" / "project-workflow-governance.zh-CN.md"
    if governance_ref.exists():
        text = governance_ref.read_text(encoding="utf-8")
        for marker in (
            "workflow-run.governance",
            "enforcement_mode",
            "shadow",
            "warn",
            "enforce",
            "intent_work_order_ref",
            "voi_gate_ref",
            "rjr_authority_ref",
            "paranoia_review_ref",
            "human_gate_refs",
            "rollback_ref",
            "candidate_learning_refs",
        ):
            if marker not in text:
                errors.append(f"{governance_ref}: missing workflow-governance marker {marker}")

    governance_template = skill_root / "templates" / "workflow_governance_review.zh-CN.md"
    if governance_template.exists():
        text = governance_template.read_text(encoding="utf-8")
        for marker in (
            "workflow_governance_review",
            "enforcement_mode",
            "intent_work_order_ref",
            "decision_ref",
            "voi_gate_ref",
            "rjr_authority_ref",
            "paranoia_review_ref",
            "human_gate_refs",
            "rollback_ref",
            "candidate_learning_refs",
        ):
            if marker not in text:
                errors.append(f"{governance_template}: missing workflow governance template field {marker}")

    playbook = (skill_root / "references" / "value-of-information-playbook.zh-CN.md")
    if playbook.exists():
        text = playbook.read_text(encoding="utf-8")
        for marker in ("信号—行动映射", "AI 疲劳 Gate", "反 AI 味 Gate", "EVPPI"):
            if marker not in text:
                errors.append(f"{playbook}: missing section marker {marker}")

    cases = skill_root / "evals" / "voi-decision-gate-cases.md"
    if cases.exists() and cases.read_text(encoding="utf-8").count("## Case") < 8:
        errors.append(f"{cases}: requires at least 8 VOI behavior cases")
    if cases.exists():
        case_text = cases.read_text(encoding="utf-8")
        for marker in ("RJR-AI", "rjr_authority_gate", "residual_judgment"):
            if marker not in case_text:
                errors.append(f"{cases}: missing RJR behavior marker {marker}")
        if "workflow-run.governance" not in case_text:
            errors.append(f"{cases}: missing workflow governance behavior marker workflow-run.governance")

    ladder_ref = skill_root / "references" / "uncertainty-ladder-protocol.zh-CN.md"
    if ladder_ref.exists():
        text = ladder_ref.read_text(encoding="utf-8")
        for marker in (
            "UL-L0",
            "UL-L3",
            "UL-L5",
            "ul_state",
            "released_this_round",
            "held_constant",
            "confounded",
            "迁移",
            "Human Gate",
        ):
            if marker not in text:
                errors.append(f"{ladder_ref}: missing uncertainty ladder marker {marker}")

    ladder_template = skill_root / "templates" / "uncertainty_ladder_state.zh-CN.md"
    if ladder_template.exists():
        text = ladder_template.read_text(encoding="utf-8")
        for marker in (
            "schema_version",
            "ul_id",
            "current_rung",
            "uncertainty_exposure",
            "released_this_round",
            "held_constant",
            "scaffolds_present",
            "consequence_budget",
            "attribution_gate",
            "graduation_evidence",
            "transfer_checks",
            "fallback_rung",
            "rollback",
            "stop_rule",
            "human_gate",
        ):
            if marker not in text:
                errors.append(f"{ladder_template}: missing uncertainty ladder template field {marker}")

    ladder_cases = skill_root / "evals" / "uncertainty-ladder-cases.md"
    if ladder_cases.exists():
        case_text = ladder_cases.read_text(encoding="utf-8")
        if case_text.count("## Case") < 6:
            errors.append(f"{ladder_cases}: requires at least 6 uncertainty ladder behavior cases")
        for marker in ("confounded", "迁移", "Human Gate", "fallback rung"):
            if marker not in case_text:
                errors.append(f"{ladder_cases}: missing uncertainty ladder behavior marker {marker}")

    ul_schema_path = repo_root / "contracts" / "ul-state.schema.json"
    ul_example_path = skill_root / "examples" / "ul-state.example.json"
    if ul_schema_path.exists() and ul_example_path.exists():
        schema_data = _parse_json(ul_schema_path, errors)
        example_data = _parse_json(ul_example_path, errors)
        if isinstance(schema_data, dict) and isinstance(example_data, dict):
            for error in Draft202012Validator(schema_data).iter_errors(example_data):
                location = ".".join(str(part) for part in error.path) or "<root>"
                errors.append(f"{ul_example_path}:{location}: {error.message}")
            for marker in ("ul_id", "current_rung", "confounded", "negative_transfer", "human_gate"):
                if marker not in ul_example_path.read_text(encoding="utf-8"):
                    errors.append(f"{ul_example_path}: missing UL example marker {marker}")


def _check_project_workflow_governance(repo_root: Path, errors: list[str]) -> None:
    schema = repo_root / "contracts" / "workflow-run.schema.json"
    if schema.exists():
        text = schema.read_text(encoding="utf-8")
        for marker in (
            '"governance"',
            '"evolver_required"',
            '"enforcement_mode"',
            '"intent_work_order_ref"',
            '"voi_gate_ref"',
            '"ul_state_ref"',
            '"rjr_authority_ref"',
            '"paranoia_review_ref"',
            '"human_gate_refs"',
            '"rollback_ref"',
            '"candidate_learning_refs"',
        ):
            if marker not in text:
                errors.append(f"{schema}: missing workflow governance schema marker {marker}")

    workflow_readme = repo_root / "docs" / "workflows" / "README.md"
    if workflow_readme.exists():
        text = workflow_readme.read_text(encoding="utf-8")
        for marker in ("Project Governance Checkpoints", "workflow-run.governance", "ul_state_ref", "paranoia-ai-system-evolver"):
            if marker not in text:
                errors.append(f"{workflow_readme}: missing workflow governance marker {marker}")

    for rel in (
        "docs/workflows/decision-to-information.md",
        "docs/workflows/idea-to-validation.md",
        "docs/workflows/media-to-diagnosis.md",
        "docs/workflows/weekly-ed-experiment.md",
        "docs/workflows/evidence-to-proposal.md",
    ):
        path = repo_root / rel
        if path.exists():
            text = path.read_text(encoding="utf-8")
            if "Paranoia Checkpoint" not in text:
                errors.append(f"{path}: missing Paranoia Checkpoint section")


def _check_public_readme_surface(repo_root: Path, errors: list[str]) -> None:
    proof_cases = (
        repo_root / "game-experience-analyzer" / "examples" / "survival-33-days-gameplay-experience-report.md",
        repo_root / "docs" / "showcases" / "elliot-experience-density-report" / "README.md",
    )
    workspace_manifest_text = (
        repo_root / "runtime" / "workspace-template-v1" / "game.designos.yaml"
    ).read_text(encoding="utf-8")
    assets_block = re.search(r"(?ms)^assets:\n((?:  .*?(?:\n|$))+)", workspace_manifest_text)
    workspace_sections = (
        len(re.findall(r"(?m)^  [A-Za-z_][A-Za-z0-9_]*_dir:\s*", assets_block.group(1)))
        if assets_block
        else 0
    )
    readme_labels = {
        "README.md": {
            "Specialist skills": len(REQUIRED_SKILLS),
            "Contract schemas": len(list((repo_root / "contracts").glob("*.schema.json"))),
            "v1 workspace sections": workspace_sections,
            "Workflow guides": len(
                [path for path in (repo_root / "docs" / "workflows").glob("*.md") if path.name != "README.md"]
            ),
            "Host adapters": len(
                [path for path in (repo_root / "adapters").glob("*.md") if path.name != "README.md"]
            ),
            "Public proof cases": len(proof_cases),
        },
        "README.en.md": {},
        "README.zh-CN.md": {
            "专家 skill": len(REQUIRED_SKILLS),
            "Contract schema": len(list((repo_root / "contracts").glob("*.schema.json"))),
            "v1 workspace 分区": workspace_sections,
            "端到端工作流": len(
                [path for path in (repo_root / "docs" / "workflows").glob("*.md") if path.name != "README.md"]
            ),
            "宿主 adapter": len(
                [path for path in (repo_root / "adapters").glob("*.md") if path.name != "README.md"]
            ),
            "公开 proof case": len(proof_cases),
        },
    }
    readme_labels["README.en.md"] = dict(readme_labels["README.md"])

    for path in proof_cases:
        if not path.exists():
            errors.append(f"public proof case missing: {path.relative_to(repo_root)}")

    markdown_link_pattern = re.compile(r"(?:!\[[^\]]*\]|\[[^\]]+\])\(([^)]+)\)")
    html_link_pattern = re.compile(r"(?:src|srcset|href)=\"([^\"]+)\"")
    for relative, labels in readme_labels.items():
        path = repo_root / relative
        if not path.exists():
            continue
        text = path.read_text(encoding="utf-8")
        if "api.star-history.com" in text or "## Star History" in text:
            errors.append(f"{relative}: deprecated live Star History embed is not allowed")

        for label, expected in labels.items():
            match = re.search(rf"\|\s*{re.escape(label)}\s*\|\s*(\d+)\s*\|", text)
            if not match:
                errors.append(f"{relative}: missing inventory row {label}")
            elif int(match.group(1)) != expected:
                errors.append(f"{relative}: {label} count {match.group(1)} must be {expected}")

        references = markdown_link_pattern.findall(text) + html_link_pattern.findall(text)
        for reference in references:
            reference = reference.strip().strip("<>").split()[0]
            if reference.startswith(("http://", "https://", "mailto:", "#")):
                continue
            reference = reference.split("#", 1)[0]
            if not reference:
                continue
            target = (path.parent / reference).resolve()
            if not target.exists():
                errors.append(f"{relative}: local link target missing: {reference}")


def _check_openai_compatible_host(repo_root: Path, errors: list[str]) -> None:
    host_path = repo_root / "examples" / "hosts" / "openai_compatible.py"
    adapter_path = repo_root / "adapters" / "openai-compatible.md"
    guide_path = repo_root / "examples" / "hosts" / "README.md"
    for path, markers in (
        (
            host_path,
            (
                "GAMEDESIGNOS_API_KEY",
                "request-preview.private.json",
                "dispatch_intent_recorded",
                "outcome_unknown",
                "safe_to_retry",
                "--execute",
            ),
        ),
        (
            adapter_path,
            (
                "runnable",
                "outcome_unknown",
                "no automatic retry",
                "Offline Fixture",
            ),
        ),
        (
            guide_path,
            (
                "默认 dry-run",
                "一次性授权",
                "不会直接写入 Project-Ready workspace",
            ),
        ),
    ):
        if not path.exists():
            continue
        text = path.read_text(encoding="utf-8")
        for marker in markers:
            if marker not in text:
                errors.append(f"{path}: missing OpenAI-compatible host marker {marker}")

    chinese_guide = repo_root / "docs" / "try-it-in-10-minutes.zh-CN.md"
    if chinese_guide.exists():
        text = chinese_guide.read_text(encoding="utf-8")
        if "默认只做路由和状态审计" not in text or "不会创建或修改 workspace" not in text:
            errors.append(f"{chinese_guide}: ask/start behavior parity marker missing")
        if "对项目型请求，还会创建 Project-Ready workspace" in text:
            errors.append(f"{chinese_guide}: still claims implicit workspace creation")


def _check_application_service_and_mcp_boundary(repo_root: Path, errors: list[str]) -> None:
    service_path = repo_root / "gamedesignos" / "application" / "project_queries.py"
    cli_path = repo_root / "gamedesignos" / "cli.py"
    rfc_path = repo_root / "docs" / "product" / "v1.4-mcp-boundary-rfc.md"

    if service_path.exists():
        service = service_path.read_text(encoding="utf-8")
        for marker in (
            "def get_project_status",
            "def route_project_task",
            "def preview_gate",
            "write=False",
            "def validate_project_workspace",
        ):
            if marker not in service:
                errors.append(f"{service_path}: missing read-only Application Service marker {marker}")

    if cli_path.exists():
        cli = cli_path.read_text(encoding="utf-8")
        for marker in (
            "from .application import",
            "get_project_status(_workspace(args))",
            "preview_gate(workspace, args.gate_type, args.target)",
        ):
            if marker not in cli:
                errors.append(f"{cli_path}: CLI does not reuse Application Service marker {marker}")

    if rfc_path.exists():
        rfc = rfc_path.read_text(encoding="utf-8")
        for marker in (
            "状态：`candidate`",
            "MCP `2026-07-28`",
            "stdio-first",
            "Application Service",
            "preview_gate",
            "Human Gate",
            "needs_more_evidence",
            "Rollback",
        ):
            if marker not in rfc:
                errors.append(f"{rfc_path}: missing MCP boundary marker {marker}")


def _check_p0_portability(repo_root: Path, errors: list[str]) -> None:
    pyproject = tomllib.loads((repo_root / "pyproject.toml").read_text(encoding="utf-8"))
    project = pyproject["project"]
    dynamic = set(project.get("dynamic", []))
    version_source = (
        pyproject.get("tool", {})
        .get("setuptools", {})
        .get("dynamic", {})
        .get("version", {})
        .get("attr")
    )
    if "version" not in dynamic or version_source != "gamedesignos._version.VERSION":
        errors.append(
            "pyproject.toml: version must be dynamic from gamedesignos._version.VERSION"
        )
    version_path = repo_root / "gamedesignos" / "_version.py"
    version_match = re.search(
        r'(?m)^VERSION\s*=\s*"([^"]+)"\s*$',
        version_path.read_text(encoding="utf-8"),
    )
    package_version = version_match.group(1) if version_match else ""
    if not package_version:
        errors.append(f"{version_path}: missing canonical VERSION assignment")
    constants_text = (repo_root / "gamedesignos" / "constants.py").read_text(encoding="utf-8")
    if "from ._version import VERSION as RUNTIME_VERSION" not in constants_text:
        errors.append("gamedesignos/constants.py: RUNTIME_VERSION must import canonical VERSION")
    template_path = repo_root / "runtime" / "workspace-template-v1" / "game.designos.yaml"
    template = _parse_yaml(template_path, errors)
    template_runtime = (
        template.get("designos", {}).get("version")
        if isinstance(template, dict) and isinstance(template.get("designos"), dict)
        else None
    )
    if template_runtime != package_version:
        errors.append(
            f"{template_path}: designos.version {template_runtime!r} must match package {package_version!r}"
        )
    template_assets = template.get("assets", {}) if isinstance(template, dict) else {}
    if not isinstance(template_assets, dict):
        errors.append(f"{template_path}: assets must be a mapping")
    else:
        for field, directory in sorted(template_assets.items()):
            if not field.endswith("_dir"):
                continue
            guide = template_path.parent / str(directory) / "README.md"
            if not guide.is_file():
                errors.append(
                    f"{template_path}: assets.{field} must point to a directory with README.md"
                )

    workspace_schema_path = repo_root / "contracts" / "project-workspace.schema.json"
    workspace_schema = _parse_json(workspace_schema_path, errors)
    runtime_versions = (
        workspace_schema.get("properties", {})
        .get("designos", {})
        .get("properties", {})
        .get("version", {})
        .get("enum", [])
        if isinstance(workspace_schema, dict)
        else []
    )
    if package_version not in runtime_versions:
        errors.append(
            f"{workspace_schema_path}: designos.version enum must include {package_version!r}"
        )

    router_path = repo_root / "contracts" / "router.yaml"
    router = _parse_yaml(router_path, errors) if router_path.exists() else None
    rules = router.get("default_rules", []) if isinstance(router, dict) else []
    skills: set[str] = set()
    for rule in rules if isinstance(rules, list) else []:
        if not isinstance(rule, dict):
            continue
        runtime = rule.get("runtime")
        if not isinstance(runtime, dict) or not runtime.get("signals") or not runtime.get("reason_zh"):
            errors.append(f"{router_path}: rule {rule.get('id')} lacks runtime.signals or runtime.reason_zh")
        if isinstance(rule.get("use"), str):
            skills.add(rule["use"])
    if skills != set(REQUIRED_SKILLS):
        errors.append(f"{router_path}: runtime routes cover {sorted(skills)}, expected {sorted(REQUIRED_SKILLS)}")

    for skill_name in REQUIRED_SKILLS:
        skill_root = repo_root / skill_name
        skill_text = (skill_root / "SKILL.md").read_text(encoding="utf-8")
        frontmatter = skill_text.split("---", 2)[1] if skill_text.startswith("---") else ""
        for marker in ("license:", "compatibility:", "version:"):
            if marker not in frontmatter:
                errors.append(f"{skill_name}/SKILL.md: missing Agent Skills metadata {marker}")
        if re.search(r"\.\./(?:contracts|CONTRIBUTING)", skill_text):
            errors.append(f"{skill_name}/SKILL.md: contains non-portable cross-root reference")
        eval_dir = skill_root / "evals"
        evals_path = eval_dir / "behavior_evals.json"
        outputs_path = eval_dir / "synthetic_outputs.json"
        evals = _parse_json(evals_path, errors) if evals_path.exists() else None
        outputs = _parse_json(outputs_path, errors) if outputs_path.exists() else None
        cases = evals.get("evals", []) if isinstance(evals, dict) else []
        required_ids = {"positive", "misroute", "evidence", "human_gate", "rollback"}
        case_ids = {str(item.get("id")) for item in cases if isinstance(item, dict)}
        if case_ids != required_ids:
            errors.append(f"{skill_name}: behavior eval ids must be {sorted(required_ids)}")
        if not isinstance(outputs, dict) or not required_ids.issubset(outputs):
            errors.append(f"{skill_name}: synthetic outputs must cover all P0 behavior eval ids")


TRILINGUAL_SUFFIXES = (".md", ".zh-CN.md", ".en.md")


def _trilingual_stem(name: str) -> str:
    for suffix in (".zh-CN.md", ".en.md"):
        if name.endswith(suffix):
            return name[: -len(suffix)]
    return name[: -len(".md")]


def _check_trilingual_mirrors(repo_root: Path, errors: list[str]) -> None:
    """Trilingual packages must keep every topic in all three language files.

    The default `.md` file may be a thin pointer and the English file may use
    independent wording, so only completeness is enforced, not structure.
    """

    skill_root = repo_root / "paranoia-ai-system-evolver"
    for folder in ("references", "templates"):
        directory = skill_root / folder
        if not directory.is_dir():
            errors.append(f"{directory}: trilingual directory missing")
            continue
        stems = {_trilingual_stem(path.name) for path in directory.glob("*.md")}
        for stem in sorted(stems):
            missing = [
                suffix
                for suffix in TRILINGUAL_SUFFIXES
                if not (directory / f"{stem}{suffix}").is_file()
            ]
            if missing:
                errors.append(
                    f"{directory / stem}: trilingual mirror incomplete, missing {', '.join(missing)}"
                )

    for readme in ("README.md", "README.zh-CN.md", "README.en.md"):
        if not (skill_root / readme).is_file():
            errors.append(f"{skill_root / readme}: trilingual README trio incomplete")


def main() -> int:
    repo_root = Path(__file__).resolve().parents[1]
    all_errors: list[str] = []

    _check_required_paths(repo_root, all_errors)
    _check_private_ignore_rules(repo_root, all_errors)
    _check_workspace_template(repo_root, all_errors)

    for skill_name in REQUIRED_SKILLS:
        skill_dir = repo_root / skill_name
        if not skill_dir.exists():
            all_errors.append(f"{skill_name}: required skill folder missing")
            continue
        all_errors.extend(validate_skill(skill_dir))

    _check_paranoia_voi(repo_root, all_errors)
    _check_project_workflow_governance(repo_root, all_errors)
    _check_public_readme_surface(repo_root, all_errors)
    _check_openai_compatible_host(repo_root, all_errors)
    _check_application_service_and_mcp_boundary(repo_root, all_errors)
    _check_p0_portability(repo_root, all_errors)
    _check_repo_data_files(repo_root, all_errors)
    _check_trilingual_mirrors(repo_root, all_errors)

    if all_errors:
        print("Repository validation failed:")
        for error in all_errors:
            print(f"- {error}")
        return 1

    print("OK: repository")
    print("Validated Runtime Foundation:")
    print("- product docs")
    print("- workflow docs")
    print("- project workspace")
    print("- workspace contracts")
    print("- self-contained wheel resources")
    print("- router.yaml runtime source")
    print("- public README counts, local links, and stable support surface")
    print("Validated VOI Decision Gate:")
    print("- decision object and current default action")
    print("- EVPI / EVSI and signal-to-action mapping")
    print("- information-cost and stop-rule fields")
    print("- behavior-eval cases")
    print("- 7/7 portable skill suites")
    print("Validated skills:")
    for skill_name in REQUIRED_SKILLS:
        print(f"- {skill_name}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
