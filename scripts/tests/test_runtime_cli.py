from __future__ import annotations

import io
import json
import os
import subprocess
import sys
import tempfile
import unittest
import zipfile
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path
from unittest.mock import patch

from gamedesignos.cli import main
from gamedesignos.constants import RUNTIME_VERSION
from gamedesignos.errors import EXIT_OK, UsageError
from gamedesignos.project_ready import (
    export_graph_mermaid,
    health_scan,
    next_best_action,
    run_gate,
    validate_workflow_run,
)
from gamedesignos.routing import route_task
from gamedesignos.voi import create_assessment, review_assessment
from gamedesignos.workspace import Workspace, init_workspace
from scripts.create_golden_project import main as create_golden_project


class RuntimeCliTest(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def workspace(self, name: str = "Clockwork Garden", visibility: str = "private") -> Workspace:
        target = self.root / name.replace(" ", "-").lower()
        init_workspace(project_name=name, destination=target, codename=None, visibility=visibility, owner="tester")
        return Workspace.open(target)

    def test_01_init_and_validate(self) -> None:
        ws = self.workspace()
        self.assertTrue(ws.validate().ok)
        self.assertEqual(ws.status().runtime_version_declared, RUNTIME_VERSION)
        self.assertTrue(ws.decision_log_path.is_file())

    def test_02_init_refuses_nonempty(self) -> None:
        target = self.root / "occupied"
        target.mkdir()
        keep = target / "keep.txt"
        keep.write_text("keep", encoding="utf-8")
        self.assertNotEqual(main(["init", "Occupied", "--destination", str(target)]), EXIT_OK)
        self.assertEqual(keep.read_text(encoding="utf-8"), "keep")

    def test_03_chinese_name_gets_ascii_id(self) -> None:
        result = init_workspace(project_name="灯塔战术", destination=self.root / "cn", codename=None, visibility="private", owner="tester")
        self.assertRegex(result["project_id"], r"^untitled-[0-9a-f]{8}$")

    def test_04_explicit_missing_workspace_fails(self) -> None:
        self.assertNotEqual(main(["route", "analyze recording", "--workspace", str(self.root / "missing")]), EXIT_OK)

    def test_05_new_asset_registers_file(self) -> None:
        ws = self.workspace()
        result = ws.create_asset("concept", title="Repairing Lighthouse")
        self.assertTrue(Path(result["path"]).is_file())
        self.assertEqual(ws.load_asset_index()["assets"][0]["asset_type"], "concept")

    def test_06_media_routes_to_analyzer(self) -> None:
        result = route_task("请分析这段试玩录屏里的首局体验")
        self.assertEqual(result["selected_skill"], "game-experience-analyzer")
        self.assertFalse(result["executed"])

    def test_07_ed_missing_evidence_routes_upstream(self) -> None:
        result = route_task("设计首局留存和反馈强度的一周 A/B 测试", workspace=self.workspace())
        self.assertEqual(result["selected_skill"], "game-experience-analyzer")
        self.assertEqual(result["target_skill"], "game-experience-density-optimizer")

    def test_08_proposal_after_concept(self) -> None:
        ws = self.workspace()
        ws.create_asset("concept", title="Concept")
        ws.create_asset("validation-plan", title="Validation")
        result = route_task("assemble a publisher pitch proposal", workspace=ws)
        self.assertEqual(result["selected_skill"], "game-design-proposal-writer")
        self.assertEqual(result["missing_upstream"], [])

    def test_09_rjr_ai_routes_to_system_evolver(self) -> None:
        result = route_task(
            "根据剩余判断权优化 RJR-AI：AI 扩大可能性，Workflow 压缩混乱，Eval 提供反馈，"
            "权限系统防止越界，知识库积累组织记忆。"
        )
        self.assertEqual(result["selected_skill"], "paranoia-ai-system-evolver")

    def test_10_intent_work_order_routes_to_system_evolver(self) -> None:
        result = route_task("把 AI 工作单从指令单升级成意图单，让 agent 在边界内循环直到验收")
        self.assertEqual(result["selected_skill"], "paranoia-ai-system-evolver")
        self.assertIn("intent-work-order", result["primary_outputs"])

    def test_10b_workflow_governance_routes_to_system_evolver(self) -> None:
        result = route_task("Improve overall process, workflow governance, and output quality")
        self.assertEqual(result["selected_skill"], "paranoia-ai-system-evolver")
        self.assertIn("workflow-governance-review", result["primary_outputs"])

    def test_10c_uncertainty_ladder_routes_to_system_evolver(self) -> None:
        result = route_task(
            "把不确定性阶梯用于 AI 工程：建立模型、受控组合、暴露失败、诊断瓶颈，再做迁移验证"
        )
        self.assertEqual(result["selected_skill"], "paranoia-ai-system-evolver")
        self.assertIn("ul-state", result["primary_outputs"])

    def test_10d_player_learning_curve_does_not_route_to_system_evolver(self) -> None:
        result = route_task("为新手玩家设计学习曲线、教程节奏和反馈强度实验")
        self.assertNotEqual(result["selected_skill"], "paranoia-ai-system-evolver")

    def test_11_voi_near_selects_probe(self) -> None:
        ws = self.workspace()
        result = create_assessment(
            ws,
            decision_id="DEC-PROTOTYPE-001",
            decision_question="Which prototype receives the next week?",
            options=["Build combat prototype", "Build economy prototype"],
            current_default_action="Build combat prototype",
            owner="tester",
            stakes="high",
            reversibility="reversible",
            boundary="near",
            candidate_information_actions=["Run five-player paper test"],
            stop_when=["Five sessions complete"],
        )
        path = Path(result["path"])
        data = json.loads(path.read_text(encoding="utf-8"))
        data["candidate_information_actions"][0]["costs"] = {
            "acquisition": "low", "latency": "low", "attention": "low", "privacy_or_contamination": "none"
        }
        path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        reviewed = review_assessment(path, write=True)
        self.assertTrue(reviewed["ok"])
        self.assertEqual(reviewed["selected_probe"]["action_id"], "INFO-001")

    def test_12_voi_rejects_invalid_decision(self) -> None:
        with self.assertRaises(UsageError):
            create_assessment(
                self.workspace(), decision_id="bad", decision_question="What?", options=["A", "A"],
                current_default_action="A", owner="tester", stakes="medium", reversibility="reversible",
                boundary="near", candidate_information_actions=[], stop_when=None,
            )

    def test_13_locked_decision_stops_research(self) -> None:
        result = create_assessment(
            self.workspace(), decision_id="DEC-LOCKED-001", decision_question="Reopen scope?",
            options=["Execute", "Reopen"], current_default_action="Execute", owner="tester",
            stakes="medium", reversibility="costly_to_reverse", boundary="locked",
            candidate_information_actions=["Read another trend report"], stop_when=None,
        )
        reviewed = review_assessment(Path(result["path"]))
        self.assertTrue(reviewed["ok"])
        self.assertIsNone(reviewed["selected_probe"])

    def test_14_public_pack_filters(self) -> None:
        ws = self.workspace("Synthetic Lighthouse", "public-synthetic")
        ws.create_asset("concept", title="Synthetic Concept")
        output = self.root / "pack.zip"
        ws.pack(mode="public-synthetic", output=output)
        with zipfile.ZipFile(output) as archive:
            names = set(archive.namelist())
            index = json.loads(archive.read("design-asset-index.json"))
        self.assertIn("05-design-assets/concepts/synthetic-concept.md", names)
        self.assertNotIn("game.designos.yaml", names)
        self.assertEqual(len(index["assets"]), 1)

    def test_15_pack_overwrite_requires_force(self) -> None:
        ws = self.workspace("Pack Guard", "public-synthetic")
        ws.create_asset("concept", title="Synthetic Concept")
        output = self.root / "guard.zip"
        ws.pack(mode="public-synthetic", output=output)
        with self.assertRaises(UsageError):
            ws.pack(mode="public-synthetic", output=output)
        self.assertFalse(ws.pack(mode="public-synthetic", output=output, force=True)["dry_run"])

    def test_16_public_validation_rejects_private_asset(self) -> None:
        ws = self.workspace("Synthetic Broken", "public-synthetic")
        ws.create_asset("concept", title="Synthetic Concept")
        index = ws.load_asset_index()
        index["assets"][0]["source_status"] = "private"
        ws.asset_index_path.write_text(json.dumps(index, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        self.assertTrue(any("non-synthetic" in item for item in ws.validate().errors))

    def test_17_cli_smoke_second_workspace(self) -> None:
        target = self.root / "lighthouse"
        self.assertEqual(main(["init", "Lighthouse Tactics", "--destination", str(target), "--visibility", "public-synthetic", "--owner", "fixture"]), EXIT_OK)
        self.assertEqual(main(["new", "decision", "--workspace", str(target), "--title", "Prototype Direction"]), EXIT_OK)
        self.assertEqual(main(["validate", "--workspace", str(target)]), EXIT_OK)

    def test_18_project_ready_blocks_voi_without_decision(self) -> None:
        result = run_gate(self.workspace(), "voi", "DEC-MISSING-001")
        self.assertEqual(result["status"], "block")
        self.assertIn("Decision Object", result["reason"])

    def test_19_project_ready_commitment_requires_rollback(self) -> None:
        ws = self.workspace()
        log = ws.load_decision_log()
        log["decisions"].append(
            {
                "decision_id": "DEC-PROTOTYPE-001",
                "date": "2026-06-19",
                "decision_type": "experiment",
                "status": "proposed",
                "decision": "Build the combat prototype first.",
                "context": "Two-week sprint direction.",
                "options_considered": ["Combat prototype", "Relationship loop"],
                "evidence_refs": [],
                "assumptions": ["Players can understand the combat loop."],
                "risks": ["Over-scoped combat rules."],
                "owner": "tester",
                "rollback_trigger": "",
                "current_default_action": "Combat prototype",
                "decision_boundary": "near",
                "stakes": "high",
                "reversibility": "costly_to_reverse",
            }
        )
        ws.decision_log_path.write_text(json.dumps(log, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

        result = run_gate(ws, "commitment", "DEC-PROTOTYPE-001")
        self.assertEqual(result["status"], "block")
        self.assertTrue(result["human_gate_required"])
        self.assertIn("rollback", result["reason"])
        self.assertNotEqual(
            main(["gate", "run", "commitment", "DEC-PROTOTYPE-001", "--workspace", str(ws.root)]),
            EXIT_OK,
        )

    def test_20_project_ready_health_next_and_graph(self) -> None:
        ws = self.workspace()
        log = ws.load_decision_log()
        log["decisions"].append(
            {
                "decision_id": "DEC-PROTOTYPE-001",
                "date": "2026-06-19",
                "decision_type": "experiment",
                "status": "proposed",
                "decision": "Pick prototype direction.",
                "context": "Two-week sprint direction.",
                "options_considered": ["Combat prototype", "Relationship loop"],
                "evidence_refs": [],
                "assumptions": ["Players can understand the combat loop."],
                "risks": ["Over-scoped combat rules."],
                "owner": "tester",
                "rollback_trigger": "Two-week slice has no readable three-minute loop.",
                "current_default_action": "Combat prototype",
                "decision_boundary": "near",
                "stakes": "high",
                "reversibility": "costly_to_reverse",
                "assumption_refs": ["ASM-COMPREHENSION-001"],
                "experiment_refs": ["EXP-COMPREHENSION-001"],
            }
        )
        ws.decision_log_path.write_text(json.dumps(log, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

        assumptions = ws.root / "02-assumptions"
        assumptions.mkdir(exist_ok=True)
        (assumptions / "assumption-registry.json").write_text(
            json.dumps(
                {
                    "schema_version": "1.0.0",
                    "workspace_id": ws.workspace_id,
                    "assumptions": [
                        {
                            "assumption_id": "ASM-COMPREHENSION-001",
                            "statement": "Players understand the loop in three minutes.",
                            "type": "player_understanding",
                            "risk_level": "high",
                            "confidence": "low",
                            "linked_decisions": ["DEC-PROTOTYPE-001"],
                            "test_method": "Five-player paper test.",
                            "validation_status": "untested",
                            "kill_condition": "Three of five players cannot explain the win/loss source.",
                        }
                    ],
                },
                ensure_ascii=False,
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )
        experiment_dir = ws.root / "04-experiments" / "EXP-COMPREHENSION-001"
        experiment_dir.mkdir(parents=True)
        (experiment_dir / "experiment-plan.json").write_text(
            json.dumps(
                {
                    "schema_version": "1.0.0",
                    "experiment_id": "EXP-COMPREHENSION-001",
                    "title": "Three-minute comprehension test",
                    "target_decision": "DEC-PROTOTYPE-001",
                    "target_assumptions": ["ASM-COMPREHENSION-001"],
                    "hypothesis": "A small sample can expose readability risk.",
                    "method": "Paper prototype.",
                    "sample_size": 5,
                    "success_criteria": ["Four of five players can explain the loop."],
                    "failure_criteria": ["Most players cannot predict outcomes."],
                    "result_status": "planned",
                },
                ensure_ascii=False,
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )

        health = health_scan(ws)
        self.assertEqual(health["decisions"], 1)
        self.assertEqual(health["high_risk_untested_assumptions"], ["ASM-COMPREHENSION-001"])
        self.assertEqual(next_best_action(ws)["action"], "plan_experiment")
        graph = export_graph_mermaid(ws)
        self.assertIn("DEC_PROTOYPE_001".replace("PROTOYPE", "PROTOTYPE"), graph)
        self.assertIn("ASM_COMPREHENSION_001", graph)
        self.assertIn("EXP_COMPREHENSION_001", graph)

    def test_20b_next_best_action_uses_decision_new_hint(self) -> None:
        ws = self.workspace()
        result = next_best_action(ws)
        self.assertEqual(result["action"], "create_decision_object")
        self.assertIn("gamedesignos decision new", result["command_hint"])
        self.assertNotIn("gamedesignos new decision", result["command_hint"])

    def test_21_project_ready_cli_full_cycle(self) -> None:
        target = self.root / "project-ready"
        self.assertEqual(main(["init", "Project Ready", "--destination", str(target), "--owner", "tester"]), EXIT_OK)
        self.assertEqual(
            main(
                [
                    "decision",
                    "new",
                    "--workspace",
                    str(target),
                    "--title",
                    "Prototype Direction",
                    "--question",
                    "Which prototype should the next sprint validate?",
                    "--option",
                    "Route combat",
                    "--option",
                    "Relationship loop",
                    "--default-action",
                    "Route combat",
                    "--owner",
                    "tester",
                    "--stakes",
                    "high",
                    "--reversibility",
                    "costly_to_reverse",
                    "--rollback-trigger",
                    "No readable three-minute loop after two weeks.",
                ]
            ),
            EXIT_OK,
        )
        ws = Workspace.open(target)
        decision_id = next(path.stem for path in (target / "01-decisions").glob("DEC-*.json"))

        self.assertEqual(
            main(
                [
                    "assumption",
                    "new",
                    "--workspace",
                    str(target),
                    "--decision",
                    decision_id,
                    "--statement",
                    "Players understand route combat in three minutes.",
                    "--risk",
                    "high",
                    "--confidence",
                    "low",
                    "--test-method",
                    "Five-player paper test.",
                    "--kill-condition",
                    "Three of five cannot explain win/loss source.",
                ]
            ),
            EXIT_OK,
        )
        assumption_id = next(path.stem for path in (target / "02-assumptions").glob("ASM-*.json"))
        self.assertEqual(
            main(
                [
                    "experiment",
                    "plan",
                    "--workspace",
                    str(target),
                    "--decision",
                    decision_id,
                    "--assumption",
                    assumption_id,
                    "--title",
                    "Comprehension Test",
                    "--hypothesis",
                    "A small sample exposes route-combat readability risk.",
                    "--method",
                    "Paper prototype.",
                    "--success",
                    "Four of five explain the loop.",
                    "--failure",
                    "Most players cannot predict outcomes.",
                    "--sample-size",
                    "5",
                ]
            ),
            EXIT_OK,
        )
        experiment_id = next(path.name for path in (target / "04-experiments").iterdir() if path.is_dir())
        self.assertEqual(
            main(
                [
                    "evidence",
                    "add",
                    "--workspace",
                    str(target),
                    "--decision",
                    decision_id,
                    "--summary",
                    "Synthetic test notes support route readability but not retention.",
                    "--source-type",
                    "playtest",
                    "--source-status",
                    "synthetic",
                    "--confidence",
                    "medium",
                    "--decision-impact",
                    "Supports route combat for the next sprint.",
                    "--unsupported-claim",
                    "Cannot prove long-term retention.",
                ]
            ),
            EXIT_OK,
        )
        evidence_id = next(path.stem for path in (target / "03-evidence").glob("EVD-*.json"))
        self.assertEqual(
            main(
                [
                    "experiment",
                    "result",
                    experiment_id,
                    "--workspace",
                    str(target),
                    "--status",
                    "passed",
                    "--observation",
                    "Four of five explained the loop.",
                    "--evidence",
                    evidence_id,
                    "--decision-delta",
                    "Route combat remains the default action.",
                ]
            ),
            EXIT_OK,
        )
        self.assertEqual(
            main(
                [
                    "experiment",
                    "review",
                    experiment_id,
                    "--workspace",
                    str(target),
                    "--by",
                    "tester",
                    "--summary",
                    "Result reviewed; no retention claim is allowed.",
                ]
            ),
            EXIT_OK,
        )
        self.assertEqual(
            main(
                [
                    "assumption",
                    "validate",
                    assumption_id,
                    "--workspace",
                    str(target),
                    "--status",
                    "tested",
                    "--reason",
                    "Covered by reviewed experiment.",
                ]
            ),
            EXIT_OK,
        )
        self.assertEqual(
            main(
                [
                    "decision",
                    "accept",
                    decision_id,
                    "--workspace",
                    str(target),
                    "--by",
                    "tester",
                    "--reason",
                    "Experiment reviewed and rollback trigger exists.",
                ]
            ),
            EXIT_OK,
        )
        self.assertTrue(ws.validate().ok)
        self.assertEqual(main(["workflow", "start", "idea-to-validation", "--workspace", str(target)]), EXIT_OK)
        run_id = next(path.stem for path in (target / ".gamedesignos" / "workflow-runs").glob("WRUN-*.json"))
        workflow_data = json.loads((target / ".gamedesignos" / "workflow-runs" / f"{run_id}.json").read_text(encoding="utf-8"))
        self.assertTrue(workflow_data["governance"]["evolver_required"])
        self.assertEqual(workflow_data["governance"]["enforcement_mode"], "shadow")
        self.assertEqual(workflow_data["governance"]["decision_ref"], decision_id)
        self.assertIsNone(workflow_data["governance"]["ul_state_ref"])
        self.assertEqual(workflow_data["governance"]["rollback_ref"], decision_id)
        self.assertEqual(main(["workflow", "validate", run_id, "--workspace", str(target)]), EXIT_OK)

        workflow_path = target / ".gamedesignos" / "workflow-runs" / f"{run_id}.json"
        workflow_data["governance"]["ul_state_ref"] = "UL-MISSING-001"
        workflow_path.write_text(json.dumps(workflow_data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        self.assertFalse(validate_workflow_run(ws, run_id)["ok"])

        example_path = Path(__file__).resolve().parents[2] / "paranoia-ai-system-evolver" / "examples" / "ul-state.example.json"
        ul_data = json.loads(example_path.read_text(encoding="utf-8"))
        ul_path = target / ".gamedesignos" / "workflow-runs" / f"{ul_data['ul_id']}.json"
        ul_path.write_text(json.dumps(ul_data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        workflow_data["governance"]["ul_state_ref"] = ul_data["ul_id"]
        workflow_path.write_text(json.dumps(workflow_data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        self.assertTrue(validate_workflow_run(ws, run_id)["ok"])

    def test_22_start_creates_simple_project_ready_path_once(self) -> None:
        target = self.root / "simple-start"
        command = [
            "start",
            "Simple Start",
            "--destination",
            str(target),
            "--owner",
            "tester",
        ]
        self.assertEqual(main(command), EXIT_OK)
        self.assertTrue((target / "game.designos.yaml").is_file())
        self.assertEqual(len(list((target / "01-decisions").glob("DEC-*.json"))), 1)
        self.assertEqual(len(list((target / "02-assumptions").glob("ASM-*.json"))), 1)
        self.assertEqual(len(list((target / "04-experiments").glob("EXP-*"))), 1)
        self.assertEqual(len(list((target / ".gamedesignos" / "workflow-runs").glob("WRUN-*.json"))), 1)
        self.assertTrue(Workspace.open(target).validate().ok)

        self.assertEqual(main(command), EXIT_OK)
        self.assertEqual(len(list((target / "01-decisions").glob("DEC-*.json"))), 1)
        self.assertEqual(len(list((target / "02-assumptions").glob("ASM-*.json"))), 1)
        self.assertEqual(len(list((target / "04-experiments").glob("EXP-*"))), 1)
        self.assertEqual(len(list((target / ".gamedesignos" / "workflow-runs").glob("WRUN-*.json"))), 1)

    def test_23_freeform_sentence_routes_and_starts_workspace(self) -> None:
        target = self.root / "ask-start"
        self.assertEqual(
            main(
                [
                    "我想做一款修灯塔策略游戏",
                    "--destination",
                    str(target),
                    "--owner",
                    "tester",
                ]
            ),
            EXIT_OK,
        )
        self.assertTrue((target / "game.designos.yaml").is_file())
        self.assertEqual(len(list((target / "01-decisions").glob("DEC-*.json"))), 1)
        self.assertTrue(Workspace.open(target).validate().ok)

    def test_24_ambiguous_review_request_does_not_start_workspace(self) -> None:
        with patch("gamedesignos.cli.start_project") as mocked_start:
            self.assertEqual(main(["整体审查项目，给我一些改进建议"]), EXIT_OK)
        mocked_start.assert_not_called()

    def test_25_project_route_does_not_start_without_destination(self) -> None:
        with patch("gamedesignos.cli.start_project") as mocked_start:
            self.assertEqual(main(["我想做一款修灯塔策略游戏"]), EXIT_OK)
        mocked_start.assert_not_called()

    def test_26_filesystem_error_is_reported_without_traceback(self) -> None:
        stderr = io.StringIO()
        with patch(
            "gamedesignos.cli.start_project",
            side_effect=PermissionError("denied"),
        ), redirect_stderr(stderr):
            result = main(
                [
                    "我想做一款修灯塔策略游戏",
                    "--destination",
                    str(self.root / "blocked"),
                ]
            )

        self.assertNotEqual(result, EXIT_OK)
        self.assertIn("filesystem operation failed", stderr.getvalue())
        self.assertNotIn("Traceback", stderr.getvalue())

    def test_27_cli_reconfigures_legacy_stdout_for_unicode(self) -> None:
        env = dict(os.environ)
        env["PYTHONIOENCODING"] = "cp1252"
        result = subprocess.run(
            [
                sys.executable,
                "-c",
                (
                    "from gamedesignos.cli import main; "
                    "raise SystemExit(main(['ask', '整体审查项目，给我一些改进建议']))"
                ),
            ],
            cwd=Path(__file__).resolve().parents[2],
            env=env,
            capture_output=True,
            check=False,
        )
        self.assertEqual(result.returncode, EXIT_OK, result.stderr.decode("utf-8", errors="replace"))
        self.assertIn("已接住", result.stdout.decode("utf-8"))

    def test_28_demo_reaches_human_gate_without_accepting_decision(self) -> None:
        stdout = io.StringIO()
        with patch(
            "gamedesignos.demo.tempfile.gettempdir",
            return_value=str(self.root),
        ), redirect_stdout(stdout):
            result = main(["demo", "--json"])

        self.assertEqual(result, EXIT_OK)
        payload = json.loads(stdout.getvalue())
        target = Path(payload["workspace"])
        self.assertEqual(target.parent, self.root)
        self.assertTrue(target.name.startswith("gamedesignos-demo-"))
        self.assertEqual(payload["mode"], "public-synthetic")
        self.assertEqual(payload["model_calls"], 0)
        self.assertFalse(payload["credentials_required"])
        self.assertEqual(payload["decision"]["status"], "proposed")
        self.assertEqual(payload["assumption"]["status"], "tested")
        self.assertEqual(payload["experiment"]["outcome"], "passed")
        self.assertEqual(payload["experiment"]["review_status"], "reviewed")
        self.assertEqual(payload["human_gate"]["status"], "ask_human")
        self.assertTrue(payload["human_gate"]["required"])
        self.assertEqual(payload["workflow"]["current_node"], "human_decision")
        self.assertTrue(payload["validation"]["workspace"]["ok"])
        self.assertTrue(payload["validation"]["workflow"]["ok"])
        decision_path = next((target / "01-decisions").glob("DEC-*.json"))
        decision = json.loads(decision_path.read_text(encoding="utf-8"))
        self.assertEqual(decision["status"], "proposed")
        self.assertNotIn("accepted_by", decision)

    def test_29_demo_refuses_nonempty_destination(self) -> None:
        target = self.root / "occupied-demo"
        target.mkdir()
        keep = target / "keep.txt"
        keep.write_text("keep", encoding="utf-8")
        stderr = io.StringIO()
        with redirect_stderr(stderr):
            result = main(["demo", "--destination", str(target)])

        self.assertNotEqual(result, EXIT_OK)
        self.assertIn("Refusing to overwrite", stderr.getvalue())
        self.assertEqual(keep.read_text(encoding="utf-8"), "keep")

    def test_30_golden_generator_uses_explicit_fixture_acceptance(self) -> None:
        target = self.root / "golden-fixture"
        stdout = io.StringIO()
        with patch.object(
            sys,
            "argv",
            ["create_golden_project.py", "--destination", str(target)],
        ), redirect_stdout(stdout):
            result = create_golden_project()

        self.assertEqual(result, EXIT_OK)
        self.assertIn("OK: golden project created", stdout.getvalue())
        workspace = Workspace.open(target)
        decision_path = next((target / "01-decisions").glob("DEC-*.json"))
        decision = json.loads(decision_path.read_text(encoding="utf-8"))
        self.assertEqual(decision["accepted_by"], "fixture")
        run_path = next((target / ".gamedesignos" / "workflow-runs").glob("WRUN-*.json"))
        workflow = json.loads(run_path.read_text(encoding="utf-8"))
        self.assertEqual(workflow["status"], "completed")
        self.assertTrue(workspace.validate().ok)


if __name__ == "__main__":
    unittest.main()
