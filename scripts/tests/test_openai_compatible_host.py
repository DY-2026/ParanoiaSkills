from __future__ import annotations

import importlib.util
import json
import os
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from io import StringIO
from pathlib import Path
from unittest.mock import patch
from urllib.error import URLError


REPO_ROOT = Path(__file__).resolve().parents[2]
HOST_PATH = REPO_ROOT / "examples" / "hosts" / "openai_compatible.py"
FIXTURE_PATH = (
    REPO_ROOT
    / "examples"
    / "hosts"
    / "fixtures"
    / "openai-chat-completion.json"
)

SPEC = importlib.util.spec_from_file_location("gamedesignos_openai_compatible_host", HOST_PATH)
assert SPEC is not None and SPEC.loader is not None
HOST = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(HOST)


class OpenAICompatibleHostTest(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)

    def tearDown(self) -> None:
        self.temp.cleanup()

    def _base_args(
        self,
        output: Path,
        *,
        task: str = "Build a bounded concept candidate",
    ) -> list[str]:
        return [
            "--repo",
            str(REPO_ROOT),
            "--skill",
            "game-concept-architect",
            "--task",
            task,
            "--output-dir",
            str(output),
        ]

    def _quiet_main(self, argv: list[str], **kwargs) -> int:
        with redirect_stdout(StringIO()), redirect_stderr(StringIO()):
            return HOST.main(argv, **kwargs)

    def test_offline_fixture_commits_a_bounded_result(self) -> None:
        output = self.root / "fixture"
        result = self._quiet_main(
            [
                *self._base_args(output),
                "--fixture-response",
                str(FIXTURE_PATH),
            ]
        )

        self.assertEqual(result, HOST.EXIT_OK)
        receipt = json.loads((output / HOST.RECEIPT_NAME).read_text(encoding="utf-8"))
        self.assertEqual(receipt["mode"], "fixture")
        self.assertEqual(receipt["status"], "completed")
        self.assertEqual(receipt["checkpoint"], "artifact_committed")
        self.assertEqual(
            [event["kind"] for event in receipt["events"]],
            [
                "request_prepared",
                "response_received",
                "response_validated",
                "artifact_committed",
            ],
        )
        result_text = (output / HOST.RESULT_NAME).read_text(encoding="utf-8")
        self.assertIn("Synthetic candidate", result_text)

    def test_live_call_requires_exact_preview_and_never_persists_api_key(self) -> None:
        output = self.root / "live"
        secret = "fixture-secret-never-write"
        environment = {
            HOST.BASE_URL_ENV: "https://api.deepseek.com/v1",
            HOST.MODEL_ENV: "fixture-model",
            HOST.API_KEY_ENV: secret,
        }
        calls: list[tuple[str, str, dict, float]] = []

        def fake_transport(endpoint: str, api_key: str, payload: dict, timeout: float) -> bytes:
            calls.append((endpoint, api_key, payload, timeout))
            return FIXTURE_PATH.read_bytes()

        with patch.dict(os.environ, environment, clear=False):
            self.assertEqual(self._quiet_main(self._base_args(output)), HOST.EXIT_OK)
            prepared = json.loads((output / HOST.RECEIPT_NAME).read_text(encoding="utf-8"))
            self.assertEqual(prepared["status"], "prepared")
            self.assertTrue(prepared["human_review_required"])

            self.assertEqual(
                self._quiet_main(
                    [*self._base_args(output), "--execute"],
                    transport=fake_transport,
                ),
                HOST.EXIT_OK,
            )

        self.assertEqual(len(calls), 1)
        self.assertEqual(calls[0][0], "https://api.deepseek.com/v1/chat/completions")
        self.assertEqual(calls[0][1], secret)
        receipt = json.loads((output / HOST.RECEIPT_NAME).read_text(encoding="utf-8"))
        self.assertTrue(receipt["approval"]["granted"])
        self.assertEqual(receipt["approval"]["grant_source"], "--execute")
        self.assertEqual(receipt["status"], "completed")
        self.assertIn("dispatch_intent_recorded", [event["kind"] for event in receipt["events"]])

        persisted = b"\n".join(path.read_bytes() for path in output.iterdir())
        self.assertNotIn(secret.encode("utf-8"), persisted)

    def test_changed_task_cannot_reuse_a_reviewed_preview(self) -> None:
        output = self.root / "changed"
        environment = {
            HOST.BASE_URL_ENV: "https://api.example.test/v1",
            HOST.MODEL_ENV: "fixture-model",
            HOST.API_KEY_ENV: "fixture-secret",
        }
        called = False

        def must_not_call(*_args) -> bytes:
            nonlocal called
            called = True
            return FIXTURE_PATH.read_bytes()

        with patch.dict(os.environ, environment, clear=False):
            self.assertEqual(
                self._quiet_main(self._base_args(output, task="original task")),
                HOST.EXIT_OK,
            )
            result = self._quiet_main(
                [*self._base_args(output, task="changed task"), "--execute"],
                transport=must_not_call,
            )

        self.assertEqual(result, HOST.EXIT_ERROR)
        self.assertFalse(called)
        receipt = json.loads((output / HOST.RECEIPT_NAME).read_text(encoding="utf-8"))
        self.assertEqual(receipt["status"], "prepared")

    def test_transport_failure_is_outcome_unknown_and_cannot_blindly_repeat(self) -> None:
        output = self.root / "unknown"
        environment = {
            HOST.BASE_URL_ENV: "https://api.example.test/v1",
            HOST.MODEL_ENV: "fixture-model",
            HOST.API_KEY_ENV: "fixture-secret",
        }
        call_count = 0

        def fail_transport(*_args) -> bytes:
            nonlocal call_count
            call_count += 1
            raise URLError("synthetic connection loss")

        with patch.dict(os.environ, environment, clear=False):
            self.assertEqual(self._quiet_main(self._base_args(output)), HOST.EXIT_OK)
            result = self._quiet_main(
                [*self._base_args(output), "--execute"],
                transport=fail_transport,
            )
            repeated = self._quiet_main(
                [*self._base_args(output), "--execute"],
                transport=fail_transport,
            )

        self.assertEqual(result, HOST.EXIT_OUTCOME_UNKNOWN)
        self.assertEqual(repeated, HOST.EXIT_ERROR)
        self.assertEqual(call_count, 1)
        receipt = json.loads((output / HOST.RECEIPT_NAME).read_text(encoding="utf-8"))
        self.assertEqual(receipt["status"], "outcome_unknown")
        self.assertEqual(receipt["checkpoint"], "dispatch_outcome_unknown")
        self.assertFalse(receipt["safe_to_retry"])
        self.assertTrue(receipt["human_review_required"])
        self.assertEqual(receipt["error"]["code"], "dispatch_outcome_unknown")
        self.assertFalse((output / HOST.RESULT_NAME).exists())

    def test_endpoint_rejects_embedded_credentials_and_query_secrets(self) -> None:
        with self.assertRaises(HOST.HarnessUsageError):
            HOST._chat_endpoint("https://user:secret@example.test/v1")
        with self.assertRaises(HOST.HarnessUsageError):
            HOST._chat_endpoint("https://example.test/v1?api_key=secret")


if __name__ == "__main__":
    unittest.main()
