from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from gamedesignos.errors import UsageError
from gamedesignos.project_ready import (
    export_graph_mermaid,
    graph_edges,
    health_scan,
    inspect_graph,
    next_best_action,
    run_gate,
)
from gamedesignos.workspace import Workspace, init_workspace


def _decision(**overrides: object) -> dict[str, object]:
    """Return a decision record that passes every gate unless overridden."""

    record: dict[str, object] = {
        "decision_id": "DEC-GATE-001",
        "title": "Pick prototype direction",
        "decision_question": "Which prototype direction should we validate first?",
        "owner": "tester",
        "status": "proposed",
        "decision_type": "prototype_direction",
        "boundary_status": "near",
        "stakes": "medium",
        "reversibility": "reversible",
        "current_default_action": "Build the combat prototype",
        "options_considered": ["Combat prototype", "Relationship loop"],
        "evidence_refs": [],
        "assumption_refs": [],
        "experiment_refs": [],
        "gate_refs": [],
        "rollback_trigger": "Two-week slice has no readable three-minute loop.",
    }
    record.update(overrides)
    return record


class ProjectReadyGateTestBase(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        target = self.root / "gate-lab"
        init_workspace(
            project_name="Gate Lab",
            destination=target,
            codename=None,
            visibility="private",
            owner="tester",
        )
        self.ws = Workspace.open(target)

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def write_decision(self, record: dict[str, object]) -> None:
        directory = self.ws.root / "01-decisions"
        directory.mkdir(exist_ok=True)
        path = directory / f"{record['decision_id']}.json".lower()
        path.write_text(json.dumps(record, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    def write_assumption(self, record: dict[str, object]) -> None:
        directory = self.ws.root / "02-assumptions"
        directory.mkdir(exist_ok=True)
        path = directory / f"{record['assumption_id']}.json".lower()
        path.write_text(json.dumps(record, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    def write_evidence(self, record: dict[str, object]) -> None:
        directory = self.ws.root / "03-evidence"
        directory.mkdir(exist_ok=True)
        path = directory / f"{record['evidence_id']}.json".lower()
        path.write_text(json.dumps(record, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    def write_experiment(self, record: dict[str, object]) -> None:
        directory = self.ws.root / "04-experiments"
        directory.mkdir(exist_ok=True)
        path = directory / f"{record['experiment_id']}.json".lower()
        path.write_text(json.dumps(record, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    def write_learning(self, record: dict[str, object]) -> None:
        directory = self.ws.root / "07-learning"
        directory.mkdir(exist_ok=True)
        path = directory / f"{record['learning_id']}.json".lower()
        path.write_text(json.dumps(record, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


class VoiGateTest(ProjectReadyGateTestBase):
    def test_locked_boundary_blocks_research(self) -> None:
        self.write_decision(_decision(boundary_status="locked"))
        result = run_gate(self.ws, "voi", "DEC-GATE-001")
        self.assertEqual(result["status"], "block")
        self.assertIn("research", result["blocked_actions"])
        self.assertIn("locked", result["reason"])

    def test_single_option_blocks(self) -> None:
        self.write_decision(_decision(options_considered=["Combat prototype"]))
        result = run_gate(self.ws, "voi", "DEC-GATE-001")
        self.assertEqual(result["status"], "block")
        self.assertIn("two real options", result["reason"])

    def test_missing_default_action_blocks(self) -> None:
        self.write_decision(_decision(current_default_action=""))
        result = run_gate(self.ws, "voi", "DEC-GATE-001")
        self.assertEqual(result["status"], "block")

    def test_near_boundary_passes(self) -> None:
        self.write_decision(_decision(boundary_status="near"))
        result = run_gate(self.ws, "voi", "DEC-GATE-001")
        self.assertEqual(result["status"], "pass")

    def test_far_boundary_warns(self) -> None:
        self.write_decision(_decision(boundary_status="far"))
        result = run_gate(self.ws, "voi", "DEC-GATE-001")
        self.assertEqual(result["status"], "warn")
        self.assertIn("stop rule", " ".join(result["required_actions"]).lower())


class CommitmentGateTest(ProjectReadyGateTestBase):
    def test_missing_decision_blocks(self) -> None:
        result = run_gate(self.ws, "commitment", "DEC-NONE-001")
        self.assertEqual(result["status"], "block")

    def test_untested_high_risk_assumption_blocks(self) -> None:
        self.write_decision(_decision(assumption_refs=["ASM-GATE-001"]))
        self.write_assumption(
            {
                "assumption_id": "ASM-GATE-001",
                "statement": "Players understand the loop in three minutes.",
                "risk_level": "high",
                "validation_status": "untested",
                "linked_decisions": ["DEC-GATE-001"],
            }
        )
        result = run_gate(self.ws, "commitment", "DEC-GATE-001")
        self.assertEqual(result["status"], "block")
        self.assertTrue(result["human_gate_required"])
        self.assertIn("ASM-GATE-001", " ".join(result["required_actions"]))

    def test_unreviewed_linked_experiment_blocks(self) -> None:
        self.write_decision(_decision(experiment_refs=["EXP-GATE-001"]))
        self.write_experiment(
            {
                "experiment_id": "EXP-GATE-001",
                "title": "Three-minute comprehension test",
                "target_decision": "DEC-GATE-001",
                "hypothesis": "A small sample exposes readability risk.",
                "success_criteria": ["Most players explain the loop."],
                "failure_criteria": ["Most players cannot predict outcomes."],
                "result_status": "planned",
            }
        )
        result = run_gate(self.ws, "commitment", "DEC-GATE-001")
        self.assertEqual(result["status"], "block")
        self.assertIn("EXP-GATE-001", " ".join(result["required_actions"]))

    def test_reviewed_experiment_reaches_human_gate(self) -> None:
        self.write_decision(_decision(experiment_refs=["EXP-GATE-001"]))
        self.write_experiment(
            {
                "experiment_id": "EXP-GATE-001",
                "title": "Three-minute comprehension test",
                "target_decision": "DEC-GATE-001",
                "hypothesis": "A small sample exposes readability risk.",
                "success_criteria": ["Most players explain the loop."],
                "failure_criteria": ["Most players cannot predict outcomes."],
                "result_status": "reviewed",
            }
        )
        result = run_gate(self.ws, "commitment", "DEC-GATE-001")
        self.assertEqual(result["status"], "ask_human")
        self.assertTrue(result["human_gate_required"])

    def test_clean_low_impact_decision_still_asks_human(self) -> None:
        self.write_decision(_decision())
        result = run_gate(self.ws, "commitment", "DEC-GATE-001")
        self.assertEqual(result["status"], "ask_human")
        self.assertTrue(result["human_gate_required"])


class RollbackGateTest(ProjectReadyGateTestBase):
    def test_missing_decision_blocks(self) -> None:
        result = run_gate(self.ws, "rollback", "DEC-NONE-001")
        self.assertEqual(result["status"], "block")

    def test_high_stakes_without_trigger_blocks(self) -> None:
        self.write_decision(_decision(stakes="high", rollback_trigger=""))
        result = run_gate(self.ws, "rollback", "DEC-GATE-001")
        self.assertEqual(result["status"], "block")
        self.assertTrue(result["human_gate_required"])
        self.assertIn("commitment", result["blocked_actions"])

    def test_high_stakes_with_trigger_passes(self) -> None:
        self.write_decision(_decision(stakes="high"))
        result = run_gate(self.ws, "rollback", "DEC-GATE-001")
        self.assertEqual(result["status"], "pass")


class EvidenceGateTest(ProjectReadyGateTestBase):
    def test_missing_decision_blocks(self) -> None:
        result = run_gate(self.ws, "evidence", "DEC-NONE-001")
        self.assertEqual(result["status"], "block")

    def test_no_evidence_refs_warns(self) -> None:
        self.write_decision(_decision(evidence_refs=[]))
        result = run_gate(self.ws, "evidence", "DEC-GATE-001")
        self.assertEqual(result["status"], "warn")

    def test_unsupported_claims_warn_with_boundary(self) -> None:
        self.write_decision(_decision(evidence_refs=["EVD-GATE-001"]))
        self.write_evidence(
            {
                "evidence_id": "EVD-GATE-001",
                "summary": "Five-player paper test notes.",
                "unsupported_claims": ["Long-term retention will improve."],
            }
        )
        result = run_gate(self.ws, "evidence", "DEC-GATE-001")
        self.assertEqual(result["status"], "warn")
        self.assertIn("EVD-GATE-001", " ".join(result["required_actions"]))

    def test_bounded_evidence_passes(self) -> None:
        self.write_decision(_decision(evidence_refs=["EVD-GATE-001"]))
        self.write_evidence(
            {
                "evidence_id": "EVD-GATE-001",
                "summary": "Five-player paper test notes.",
                "unsupported_claims": [],
            }
        )
        result = run_gate(self.ws, "evidence", "DEC-GATE-001")
        self.assertEqual(result["status"], "pass")


class ExperimentGateTest(ProjectReadyGateTestBase):
    def test_missing_experiment_blocks(self) -> None:
        result = run_gate(self.ws, "experiment", "EXP-NONE-001")
        self.assertEqual(result["status"], "block")

    def test_experiment_without_target_blocks(self) -> None:
        self.write_experiment(
            {
                "experiment_id": "EXP-GATE-002",
                "title": "Unbound probe",
                "hypothesis": "Something interesting happens.",
                "success_criteria": ["Signal observed."],
                "failure_criteria": ["No signal."],
            }
        )
        result = run_gate(self.ws, "experiment", "EXP-GATE-002")
        self.assertEqual(result["status"], "block")
        self.assertIn("target decision", result["reason"])

    def test_experiment_without_criteria_blocks(self) -> None:
        self.write_experiment(
            {
                "experiment_id": "EXP-GATE-003",
                "title": "Half-specified probe",
                "target_decision": "DEC-GATE-001",
                "hypothesis": "A small sample exposes readability risk.",
                "success_criteria": [],
                "failure_criteria": [],
            }
        )
        result = run_gate(self.ws, "experiment", "EXP-GATE-003")
        self.assertEqual(result["status"], "block")
        self.assertIn("criteria", result["reason"])

    def test_complete_experiment_passes(self) -> None:
        self.write_experiment(
            {
                "experiment_id": "EXP-GATE-004",
                "title": "Fully specified probe",
                "target_decision": "DEC-GATE-001",
                "hypothesis": "A small sample exposes readability risk.",
                "success_criteria": ["Most players explain the loop."],
                "failure_criteria": ["Most players cannot predict outcomes."],
            }
        )
        result = run_gate(self.ws, "experiment", "EXP-GATE-004")
        self.assertEqual(result["status"], "pass")


class ScopeGateTest(ProjectReadyGateTestBase):
    def test_missing_decision_blocks(self) -> None:
        result = run_gate(self.ws, "scope", "DEC-NONE-001")
        self.assertEqual(result["status"], "block")

    def test_critical_irreversible_asks_human(self) -> None:
        self.write_decision(_decision(stakes="critical", reversibility="irreversible"))
        result = run_gate(self.ws, "scope", "DEC-GATE-001")
        self.assertEqual(result["status"], "ask_human")
        self.assertTrue(result["human_gate_required"])

    def test_default_scope_passes(self) -> None:
        self.write_decision(_decision())
        result = run_gate(self.ws, "scope", "DEC-GATE-001")
        self.assertEqual(result["status"], "pass")

    def test_unknown_gate_type_raises(self) -> None:
        with self.assertRaises(UsageError):
            run_gate(self.ws, "velocity", "DEC-GATE-001")


class GateResultPersistenceTest(ProjectReadyGateTestBase):
    def test_write_persists_gate_result(self) -> None:
        self.write_decision(_decision())
        result = run_gate(self.ws, "voi", "DEC-GATE-001", write=True)
        out_dir = self.ws.root / ".gamedesignos" / "gate-results"
        files = list(out_dir.glob("*.json"))
        self.assertEqual(len(files), 1)
        stored = json.loads(files[0].read_text(encoding="utf-8"))
        self.assertEqual(stored["gate_id"], result["gate_id"])
        self.assertEqual(stored["schema_version"], "1.0.0")


class NextBestActionPriorityTest(ProjectReadyGateTestBase):
    def test_missing_rollback_outranks_other_findings(self) -> None:
        self.write_decision(_decision(stakes="high", rollback_trigger=""))
        self.write_assumption(
            {
                "assumption_id": "ASM-GATE-002",
                "statement": "High-risk untested assumption.",
                "risk_level": "high",
                "validation_status": "untested",
                "linked_decisions": ["DEC-GATE-001"],
            }
        )
        result = next_best_action(self.ws)
        self.assertEqual(result["action"], "define_rollback_trigger")
        self.assertEqual(result["target"], "DEC-GATE-001")

    def test_near_decision_without_gate_requests_voi(self) -> None:
        self.write_decision(_decision(boundary_status="near", gate_refs=[]))
        result = next_best_action(self.ws)
        self.assertEqual(result["action"], "run_voi_gate")
        self.assertIn("gate run voi", result["command_hint"])

    def test_pending_experiment_requests_review(self) -> None:
        self.write_decision(_decision(boundary_status="far", gate_refs=["GATE-EXISTING-001"]))
        self.write_experiment(
            {
                "experiment_id": "EXP-GATE-005",
                "title": "Pending probe",
                "target_decision": "DEC-GATE-001",
                "hypothesis": "A small sample exposes readability risk.",
                "success_criteria": ["Most players explain the loop."],
                "failure_criteria": ["Most players cannot predict outcomes."],
                "result_status": "planned",
            }
        )
        result = next_best_action(self.ws)
        self.assertEqual(result["action"], "review_experiment")
        self.assertEqual(result["target"], "EXP-GATE-005")

    def test_health_ok_flag_tracks_blockers(self) -> None:
        self.write_decision(_decision(boundary_status="far", gate_refs=["GATE-EXISTING-001"]))
        self.assertTrue(health_scan(self.ws)["ok"])
        self.write_decision(_decision(decision_id="DEC-GATE-002", stakes="critical", rollback_trigger=""))
        health = health_scan(self.ws)
        self.assertFalse(health["ok"])
        self.assertIn("DEC-GATE-002", health["high_impact_decisions_without_rollback"])


class DecisionGraphTest(ProjectReadyGateTestBase):
    def _seed_linked_records(self) -> None:
        self.write_decision(
            _decision(
                evidence_refs=["EVD-GATE-001"],
                assumption_refs=["ASM-GATE-001"],
                experiment_refs=["EXP-GATE-001"],
            )
        )
        self.write_assumption(
            {
                "assumption_id": "ASM-GATE-001",
                "statement": "Players understand the loop.",
                "risk_level": "medium",
                "validation_status": "untested",
                "linked_decisions": ["DEC-GATE-001"],
            }
        )
        self.write_evidence(
            {
                "evidence_id": "EVD-GATE-001",
                "summary": "Paper test notes.",
                "used_by_decisions": ["DEC-GATE-001"],
                "used_by_assumptions": ["ASM-GATE-001"],
            }
        )
        self.write_experiment(
            {
                "experiment_id": "EXP-GATE-001",
                "title": "Comprehension probe",
                "target_decision": "DEC-GATE-001",
                "target_assumptions": ["ASM-GATE-001"],
                "hypothesis": "A small sample exposes readability risk.",
                "success_criteria": ["Most players explain the loop."],
                "failure_criteria": ["Most players cannot predict outcomes."],
            }
        )
        self.write_learning(
            {
                "learning_id": "LRN-GATE-001",
                "statement": "Three-minute readability is the first risk.",
                "source": "EXP-GATE-001",
            }
        )

    def test_graph_edges_link_all_record_types_without_duplicates(self) -> None:
        self._seed_linked_records()
        graph = graph_edges(self.ws)
        self.assertEqual(
            {node["type"] for node in graph["nodes"].values()},
            {"decision", "assumption", "evidence", "experiment", "learning"},
        )
        markers = [(edge["from"], edge["to"], edge["type"]) for edge in graph["edges"]]
        self.assertEqual(len(markers), len(set(markers)))
        self.assertIn(("EVD-GATE-001", "DEC-GATE-001", "supports"), markers)
        self.assertIn(("DEC-GATE-001", "ASM-GATE-001", "depends_on"), markers)
        self.assertIn(("EXP-GATE-001", "DEC-GATE-001", "tests"), markers)
        self.assertIn(("EXP-GATE-001", "LRN-GATE-001", "produces"), markers)

    def test_mermaid_export_contains_all_nodes(self) -> None:
        self._seed_linked_records()
        mermaid = export_graph_mermaid(self.ws)
        self.assertTrue(mermaid.startswith("graph TD"))
        for marker in ("DEC_GATE_001", "ASM_GATE_001", "EVD_GATE_001", "EXP_GATE_001", "LRN_GATE_001"):
            self.assertIn(marker, mermaid)

    def test_inspect_graph_returns_incoming_and_outgoing(self) -> None:
        self._seed_linked_records()
        result = inspect_graph(self.ws, "DEC-GATE-001")
        incoming_types = {edge["type"] for edge in result["incoming"]}
        outgoing_types = {edge["type"] for edge in result["outgoing"]}
        self.assertIn("supports", incoming_types)
        self.assertIn("tests", incoming_types)
        self.assertIn("depends_on", outgoing_types)

    def test_inspect_graph_unknown_target_raises(self) -> None:
        with self.assertRaises(UsageError):
            inspect_graph(self.ws, "DEC-UNKNOWN-999")


if __name__ == "__main__":
    unittest.main()
