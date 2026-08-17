from __future__ import annotations

import json
import re
import tomllib
import unittest
from pathlib import Path

from gamedesignos.constants import (
    PROJECT_READY_LIFECYCLE_DIRS,
    RUNTIME_VERSION,
    VALID_DECISION_TYPES,
)


REPO_ROOT = Path(__file__).resolve().parents[2]
SKILL_DIRS = (
    "game-concept-architect",
    "game-experience-analyzer",
    "game-experience-density-optimizer",
    "game-design-proposal-writer",
    "paranoia-ai-system-evolver",
    "game-design-book-translator",
    "game-design-source-curator",
)
PROOF_CASES = (
    "game-experience-analyzer/examples/survival-33-days-gameplay-experience-report.md",
    "docs/showcases/elliot-experience-density-report/README.md",
)


class TrustworthinessSurfaceTest(unittest.TestCase):
    def test_readme_inventory_counts_match_repository(self) -> None:
        expected = {
            "skills": len([name for name in SKILL_DIRS if (REPO_ROOT / name / "SKILL.md").exists()]),
            "schemas": len(list((REPO_ROOT / "contracts").glob("*.schema.json"))),
            "workspace": len(PROJECT_READY_LIFECYCLE_DIRS),
            "workflows": len(
                [path for path in (REPO_ROOT / "docs" / "workflows").glob("*.md") if path.name != "README.md"]
            ),
            "adapters": len(
                [path for path in (REPO_ROOT / "adapters").glob("*.md") if path.name != "README.md"]
            ),
            "proof_cases": len(PROOF_CASES),
        }
        labels = {
            "README.md": {
                "Specialist skills": "skills",
                "Contract schemas": "schemas",
                "v1 workspace sections": "workspace",
                "Workflow guides": "workflows",
                "Host adapters": "adapters",
                "Public proof cases": "proof_cases",
            },
            "README.en.md": {
                "Specialist skills": "skills",
                "Contract schemas": "schemas",
                "v1 workspace sections": "workspace",
                "Workflow guides": "workflows",
                "Host adapters": "adapters",
                "Public proof cases": "proof_cases",
            },
            "README.zh-CN.md": {
                "专家 skill": "skills",
                "Contract schema": "schemas",
                "v1 workspace 分区": "workspace",
                "端到端工作流": "workflows",
                "宿主 adapter": "adapters",
                "公开 proof case": "proof_cases",
            },
        }
        for relative, row_labels in labels.items():
            text = (REPO_ROOT / relative).read_text(encoding="utf-8")
            for label, key in row_labels.items():
                match = re.search(rf"\|\s*{re.escape(label)}\s*\|\s*(\d+)\s*\|", text)
                self.assertIsNotNone(match, f"{relative} missing inventory row {label}")
                self.assertEqual(int(match.group(1)), expected[key], f"{relative} row {label} drifted")

        for relative in PROOF_CASES:
            self.assertTrue((REPO_ROOT / relative).exists(), f"public proof case missing: {relative}")

    def test_readmes_do_not_use_deprecated_star_history_embed(self) -> None:
        for relative in ("README.md", "README.en.md", "README.zh-CN.md"):
            text = (REPO_ROOT / relative).read_text(encoding="utf-8")
            self.assertNotIn("api.star-history.com", text)
            self.assertNotIn("## Star History", text)

    def test_development_package_does_not_claim_stable_classifier(self) -> None:
        project = tomllib.loads((REPO_ROOT / "pyproject.toml").read_text(encoding="utf-8"))["project"]
        classifiers = set(project.get("classifiers", []))
        if ".dev" in RUNTIME_VERSION:
            self.assertNotIn("Development Status :: 5 - Production/Stable", classifiers)
            self.assertIn("Development Status :: 4 - Beta", classifiers)

    def test_runtime_decision_types_match_decision_schema(self) -> None:
        schema = json.loads((REPO_ROOT / "contracts" / "decision.schema.json").read_text(encoding="utf-8"))
        schema_types = set(schema["properties"]["decision_type"]["enum"])
        missing_from_runtime = schema_types - VALID_DECISION_TYPES
        missing_from_schema = VALID_DECISION_TYPES - schema_types
        self.assertEqual(missing_from_runtime, set())
        self.assertEqual(missing_from_schema, set())

    def test_ask_start_onboarding_parity(self) -> None:
        chinese_guide = (
            REPO_ROOT / "docs" / "try-it-in-10-minutes.zh-CN.md"
        ).read_text(encoding="utf-8")
        self.assertIn("默认只做路由和状态审计", chinese_guide)
        self.assertIn("不会创建或修改 workspace", chinese_guide)
        self.assertNotIn("对项目型请求，还会创建 Project-Ready workspace", chinese_guide)

        english_guide = (REPO_ROOT / "docs" / "try-it-in-10-minutes.md").read_text(
            encoding="utf-8"
        )
        self.assertIn("without writing by default", english_guide)
        self.assertIn("use `start`", english_guide)

        runtime_readme = (REPO_ROOT / "runtime" / "README.md").read_text(encoding="utf-8")
        self.assertIn("默认只推荐 skill，不写盘", runtime_readme)
        self.assertNotIn("对项目型请求，还会创建 v1 workspace", runtime_readme)

    def test_demo_onboarding_surface_preserves_human_gate(self) -> None:
        surfaces = [
            REPO_ROOT / "README.md",
            REPO_ROOT / "README.en.md",
            REPO_ROOT / "README.zh-CN.md",
            REPO_ROOT / "runtime" / "README.md",
            REPO_ROOT / "runtime" / "cli" / "README.md",
            REPO_ROOT / "runtime" / "cli" / "commands.md",
        ]
        for path in surfaces:
            text = path.read_text(encoding="utf-8")
            self.assertIn("gamedesignos demo", text, path)
            self.assertIn("Human Gate", text, path)


if __name__ == "__main__":
    unittest.main()
