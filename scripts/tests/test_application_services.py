from __future__ import annotations

import io
import json
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path

from gamedesignos.application import (
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
from gamedesignos.cli import main
from gamedesignos.demo import create_lighthouse_demo
from gamedesignos.errors import EXIT_OK
from gamedesignos.project_ready import update_decision_status
from gamedesignos.workspace import Workspace


class ApplicationServiceTest(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name) / "lighthouse"
        self.demo = create_lighthouse_demo(self.root)
        self.workspace = Workspace.open(self.root)
        self.decision_id = str(self.demo["decision"]["decision_id"])
        self.evidence_id = str(self.demo["evidence"]["evidence_id"])

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def cli_json(self, *args: str) -> tuple[int, dict[str, object]]:
        stdout = io.StringIO()
        stderr = io.StringIO()
        with redirect_stdout(stdout), redirect_stderr(stderr):
            code = main([*args, "--json"])
        self.assertEqual(stderr.getvalue(), "")
        return code, json.loads(stdout.getvalue())

    def test_project_ready_status_uses_v1_decision_files(self) -> None:
        status = get_project_status(self.workspace)
        self.assertEqual(status["accepted_decisions"], 0)
        self.assertEqual(status["unresolved_human_gates"], 1)
        self.assertEqual(status["current_default_actions"], ["Repair-first route"])
        self.assertEqual(self.workspace.status().unresolved_human_gates, 1)

        code, cli_status = self.cli_json("status", "--workspace", str(self.root))
        self.assertEqual(code, EXIT_OK)
        self.assertEqual(cli_status, status)

    def test_explicit_fixture_acceptance_updates_status_truth(self) -> None:
        update_decision_status(
            self.workspace,
            self.decision_id,
            status="accepted",
            by="fixture-owner",
            reason="Explicit synthetic regression fixture acceptance.",
        )

        status = get_project_status(self.workspace)
        self.assertEqual(status["accepted_decisions"], 1)
        self.assertEqual(status["unresolved_human_gates"], 0)

    def test_read_only_queries_are_serializable_and_gate_preview_does_not_write(self) -> None:
        gate_dir = self.root / ".gamedesignos" / "gate-results"
        before = {path.name for path in gate_dir.glob("*.json")} if gate_dir.exists() else set()

        preview = preview_gate(self.workspace, "commitment", self.decision_id)
        graph = export_project_graph(self.workspace)
        payload = {
            "route": route_project_task("分析试玩录屏", workspace=self.workspace),
            "health": get_project_health(self.workspace),
            "next": get_next_action(self.workspace),
            "preview": preview,
            "graph": graph,
            "graph_node": inspect_project_graph(self.workspace, self.decision_id),
            "decision": inspect_project_decision(self.workspace, self.decision_id),
            "evidence": inspect_project_evidence(self.workspace, self.evidence_id),
            "validation": validate_project_workspace(self.workspace),
        }
        json.dumps(payload, ensure_ascii=False)

        after = {path.name for path in gate_dir.glob("*.json")} if gate_dir.exists() else set()
        self.assertEqual(before, after)
        self.assertEqual(preview["status"], "ask_human")
        self.assertEqual(graph["format"], "mermaid")
        self.assertTrue(graph["graph"].startswith("graph TD\n"))
        self.assertTrue(payload["validation"]["ok"])

    def test_cli_read_only_surfaces_match_application_services(self) -> None:
        expected = {
            "health": get_project_health(self.workspace),
            "next": get_next_action(self.workspace),
            "graph": export_project_graph(self.workspace),
            "validate": validate_project_workspace(self.workspace),
        }
        commands = {
            "health": ("health", "--workspace", str(self.root)),
            "next": ("next", "--workspace", str(self.root)),
            "graph": ("graph", "export", "--workspace", str(self.root)),
            "validate": ("validate", "--workspace", str(self.root)),
        }

        for name, command in commands.items():
            with self.subTest(name=name):
                code, payload = self.cli_json(*command)
                self.assertEqual(code, EXIT_OK)
                self.assertEqual(payload, expected[name])


if __name__ == "__main__":
    unittest.main()
