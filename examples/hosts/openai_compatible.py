#!/usr/bin/env python3
"""Safe, runnable OpenAI-compatible reference host for one GameDesignOS skill.

The default action is a local disclosure preview. A live request requires a
second invocation with ``--execute`` against the exact same preview directory.
No API key is accepted on the command line or written to disk.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sys
import tempfile
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable
from urllib.error import HTTPError, URLError
from urllib.parse import urlsplit, urlunsplit
from urllib.request import Request, urlopen


BASE_URL_ENV = "GAMEDESIGNOS_BASE_URL"
API_KEY_ENV = "GAMEDESIGNOS_API_KEY"
MODEL_ENV = "GAMEDESIGNOS_MODEL"

RECEIPT_NAME = "run-receipt.json"
PREVIEW_NAME = "request-preview.private.json"
RAW_RESPONSE_NAME = "response.private.json"
RESULT_NAME = "result.md"
RECEIPT_VERSION = "0.1.0-candidate"
MAX_RESPONSE_BYTES = 5 * 1024 * 1024

EXIT_OK = 0
EXIT_ERROR = 2
EXIT_OUTCOME_UNKNOWN = 3

Transport = Callable[[str, str, dict[str, Any], float], bytes]


class HarnessUsageError(ValueError):
    """A deterministic local validation failure."""


def _now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _atomic_write_bytes(path: Path, content: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    try:
        with os.fdopen(fd, "wb") as handle:
            handle.write(content)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
    except Exception:
        try:
            os.unlink(temporary)
        except OSError:
            pass
        raise


def _atomic_write_json(path: Path, value: Any) -> None:
    content = json.dumps(value, ensure_ascii=False, indent=2).encode("utf-8") + b"\n"
    _atomic_write_bytes(path, content)


def _read_json(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise HarnessUsageError(f"required file is missing: {path.name}") from exc
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise HarnessUsageError(f"cannot read valid JSON from {path.name}") from exc


def _sha256_bytes(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()


def _sha256_json(value: Any) -> str:
    canonical = json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return _sha256_bytes(canonical)


def _chat_endpoint(raw_base_url: str) -> str:
    raw = raw_base_url.strip()
    if not raw:
        raise HarnessUsageError(f"{BASE_URL_ENV} is required")
    parsed = urlsplit(raw)
    if parsed.scheme not in {"http", "https"} or not parsed.hostname:
        raise HarnessUsageError(f"{BASE_URL_ENV} must be an http(s) URL")
    if parsed.username or parsed.password or parsed.query or parsed.fragment:
        raise HarnessUsageError(
            f"{BASE_URL_ENV} must not contain credentials, a query, or a fragment"
        )
    try:
        port = parsed.port
    except ValueError as exc:
        raise HarnessUsageError(f"{BASE_URL_ENV} contains an invalid port") from exc

    hostname = parsed.hostname
    if ":" in hostname and not hostname.startswith("["):
        hostname = f"[{hostname}]"
    netloc = f"{hostname}:{port}" if port is not None else hostname
    path = parsed.path.rstrip("/")
    if not path.endswith("/chat/completions"):
        path = f"{path}/chat/completions"
    return urlunsplit((parsed.scheme, netloc, path, "", ""))


def _skill_text(repo_root: Path, skill_name: str) -> str:
    if not re.fullmatch(r"[a-z0-9][a-z0-9-]*", skill_name):
        raise HarnessUsageError("--skill must be a canonical folder name")
    resolved_root = repo_root.resolve()
    path = (resolved_root / skill_name / "SKILL.md").resolve()
    try:
        path.relative_to(resolved_root)
    except ValueError as exc:
        raise HarnessUsageError("--skill escapes the repository root") from exc
    if not path.is_file():
        raise HarnessUsageError(f"skill not found: {skill_name}")
    try:
        return path.read_text(encoding="utf-8")
    except (OSError, UnicodeError) as exc:
        raise HarnessUsageError(f"cannot read {skill_name}/SKILL.md") from exc


def _materials(args: argparse.Namespace) -> str:
    if args.materials_file is None:
        return args.materials or ""
    try:
        return args.materials_file.read_text(encoding="utf-8")
    except (OSError, UnicodeError) as exc:
        raise HarnessUsageError("cannot read --materials-file as UTF-8 text") from exc


def _request_preview(args: argparse.Namespace, *, fixture: bool) -> dict[str, Any]:
    if fixture:
        endpoint = "fixture://offline/chat/completions"
        model = "fixture-model"
    else:
        endpoint = _chat_endpoint(os.environ.get(BASE_URL_ENV, ""))
        model = os.environ.get(MODEL_ENV, "").strip()
        if not model:
            raise HarnessUsageError(f"{MODEL_ENV} is required")

    skill = _skill_text(args.repo, args.skill)
    materials = _materials(args)
    user_content = args.task.strip()
    if not user_content:
        raise HarnessUsageError("--task must not be empty")
    if materials:
        user_content = f"{user_content}\n\nMaterials:\n{materials}"

    payload = {
        "model": model,
        "stream": False,
        "messages": [
            {
                "role": "system",
                "content": (
                    "Execute the selected GameDesignOS skill as a bounded task. "
                    "Keep facts, inference, and unsupported claims distinct; do not "
                    "accept Human Gates or claim evidence that was not provided.\n\n"
                    f"Selected skill: {args.skill}\n\n{skill}"
                ),
            },
            {"role": "user", "content": user_content},
        ],
    }
    return {
        "preview_version": "0.1.0-candidate",
        "private_material_warning": (
            "This file contains the exact local prompt and may contain private material. "
            "Do not commit or publish it without review."
        ),
        "endpoint": endpoint,
        "skill": args.skill,
        "payload": payload,
    }


def _new_receipt(preview: dict[str, Any], *, mode: str) -> dict[str, Any]:
    return {
        "receipt_version": RECEIPT_VERSION,
        "run_id": f"HOSTRUN-{uuid.uuid4().hex.upper()}",
        "mode": mode,
        "status": "prepared",
        "checkpoint": "request_prepared",
        "safe_to_retry": True,
        "human_review_required": mode == "dry-run",
        "request_sha256": _sha256_json(preview),
        "endpoint": preview["endpoint"],
        "model": preview["payload"]["model"],
        "skill": preview["skill"],
        "approval": {
            "network_required": mode != "fixture",
            "granted": mode == "fixture",
            "grant_source": "offline-fixture" if mode == "fixture" else None,
        },
        "artifacts": {
            "request_preview": PREVIEW_NAME,
            "raw_response": None,
            "result": None,
        },
        "error": None,
        "events": [],
        "updated_at": _now(),
    }


def _checkpoint(
    output_dir: Path,
    receipt: dict[str, Any],
    *,
    kind: str,
    status: str,
    safe_to_retry: bool,
    human_review_required: bool,
    error: dict[str, Any] | None = None,
) -> None:
    timestamp = _now()
    receipt.update(
        {
            "status": status,
            "checkpoint": kind,
            "safe_to_retry": safe_to_retry,
            "human_review_required": human_review_required,
            "error": error,
            "updated_at": timestamp,
        }
    )
    receipt["events"].append(
        {
            "seq": len(receipt["events"]) + 1,
            "kind": kind,
            "status": status,
            "at": timestamp,
        }
    )
    _atomic_write_json(output_dir / RECEIPT_NAME, receipt)


def _prepare_new_run(
    output_dir: Path,
    preview: dict[str, Any],
    *,
    mode: str,
) -> dict[str, Any]:
    output_dir.mkdir(parents=True, exist_ok=True)
    conflicts = [
        name
        for name in (RECEIPT_NAME, PREVIEW_NAME, RAW_RESPONSE_NAME, RESULT_NAME)
        if (output_dir / name).exists()
    ]
    if conflicts:
        joined = ", ".join(conflicts)
        raise HarnessUsageError(
            f"output directory already contains harness artifacts ({joined}); "
            "choose a new directory"
        )
    _atomic_write_json(output_dir / PREVIEW_NAME, preview)
    receipt = _new_receipt(preview, mode=mode)
    _checkpoint(
        output_dir,
        receipt,
        kind="request_prepared",
        status="prepared",
        safe_to_retry=True,
        human_review_required=mode == "dry-run",
    )
    return receipt


def _load_approved_run(
    output_dir: Path,
    expected_preview: dict[str, Any],
) -> dict[str, Any]:
    preview = _read_json(output_dir / PREVIEW_NAME)
    receipt = _read_json(output_dir / RECEIPT_NAME)
    if not isinstance(preview, dict) or not isinstance(receipt, dict):
        raise HarnessUsageError("preview and receipt must be JSON objects")
    if receipt.get("receipt_version") != RECEIPT_VERSION:
        raise HarnessUsageError("receipt version is not supported by this example")
    if receipt.get("status") != "prepared" or receipt.get("checkpoint") != "request_prepared":
        raise HarnessUsageError(
            "this preview is no longer executable; inspect its receipt and create a new dry-run"
        )
    stored_hash = receipt.get("request_sha256")
    if stored_hash != _sha256_json(preview) or stored_hash != _sha256_json(expected_preview):
        raise HarnessUsageError(
            "task, model, endpoint, skill, or materials changed after preview; "
            "create a new dry-run"
        )
    return receipt


def _http_transport(
    endpoint: str,
    api_key: str,
    payload: dict[str, Any],
    timeout: float,
) -> bytes:
    request = Request(
        endpoint,
        data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "User-Agent": "GameDesignOS-reference-host/0.1",
        },
        method="POST",
    )
    with urlopen(request, timeout=timeout) as response:  # noqa: S310 - explicit user endpoint.
        content = response.read(MAX_RESPONSE_BYTES + 1)
    if len(content) > MAX_RESPONSE_BYTES:
        raise HarnessUsageError("response exceeds the 5 MiB reference-host limit")
    return content


def _validated_content(raw_response: bytes) -> str:
    try:
        response = json.loads(raw_response.decode("utf-8"))
    except (UnicodeError, json.JSONDecodeError) as exc:
        raise HarnessUsageError("response is not valid UTF-8 JSON") from exc
    try:
        content = response["choices"][0]["message"]["content"]
    except (KeyError, IndexError, TypeError) as exc:
        raise HarnessUsageError(
            "response does not contain choices[0].message.content"
        ) from exc
    if not isinstance(content, str) or not content.strip():
        raise HarnessUsageError("response content must be a non-empty string")
    return content.strip() + "\n"


def _finish_response(
    output_dir: Path,
    receipt: dict[str, Any],
    raw_response: bytes,
    *,
    fixture: bool,
) -> int:
    _atomic_write_bytes(output_dir / RAW_RESPONSE_NAME, raw_response)
    receipt["artifacts"]["raw_response"] = {
        "path": RAW_RESPONSE_NAME,
        "sha256": _sha256_bytes(raw_response),
    }
    _checkpoint(
        output_dir,
        receipt,
        kind="response_received",
        status="in_progress",
        safe_to_retry=False,
        human_review_required=False,
    )
    try:
        content = _validated_content(raw_response)
    except HarnessUsageError:
        _checkpoint(
            output_dir,
            receipt,
            kind="response_invalid",
            status="failed",
            safe_to_retry=fixture,
            human_review_required=not fixture,
            error={
                "code": "invalid_response",
                "message": f"inspect {RAW_RESPONSE_NAME}; no model output was committed",
            },
        )
        return EXIT_ERROR

    _checkpoint(
        output_dir,
        receipt,
        kind="response_validated",
        status="in_progress",
        safe_to_retry=False,
        human_review_required=False,
    )
    _atomic_write_bytes(output_dir / RESULT_NAME, content.encode("utf-8"))
    receipt["artifacts"]["result"] = {
        "path": RESULT_NAME,
        "sha256": _sha256_bytes(content.encode("utf-8")),
    }
    _checkpoint(
        output_dir,
        receipt,
        kind="artifact_committed",
        status="completed",
        safe_to_retry=False,
        human_review_required=False,
    )
    return EXIT_OK


def _run_fixture(args: argparse.Namespace, preview: dict[str, Any]) -> int:
    receipt = _prepare_new_run(args.output_dir, preview, mode="fixture")
    try:
        raw_response = args.fixture_response.read_bytes()
    except OSError:
        _checkpoint(
            args.output_dir,
            receipt,
            kind="fixture_unavailable",
            status="failed",
            safe_to_retry=True,
            human_review_required=False,
            error={"code": "fixture_unavailable", "message": "cannot read fixture response"},
        )
        return EXIT_ERROR
    return _finish_response(args.output_dir, receipt, raw_response, fixture=True)


def _run_live(
    args: argparse.Namespace,
    preview: dict[str, Any],
    transport: Transport,
) -> int:
    api_key = os.environ.get(API_KEY_ENV, "").strip()
    if not api_key:
        raise HarnessUsageError(
            f"{API_KEY_ENV} is required for --execute and is never written to disk"
        )
    receipt = _load_approved_run(args.output_dir, preview)
    receipt["mode"] = "live"
    receipt["approval"] = {
        "network_required": True,
        "granted": True,
        "grant_source": "--execute",
    }

    # This conservative checkpoint lands before the billable/external effect.
    # Until a response is durably stored, the remote outcome is unknown.
    _checkpoint(
        args.output_dir,
        receipt,
        kind="dispatch_intent_recorded",
        status="outcome_unknown",
        safe_to_retry=False,
        human_review_required=True,
    )
    try:
        raw_response = transport(
            preview["endpoint"],
            api_key,
            preview["payload"],
            args.timeout,
        )
    except HTTPError as exc:
        _checkpoint(
            args.output_dir,
            receipt,
            kind="http_rejected",
            status="failed",
            safe_to_retry=False,
            human_review_required=True,
            error={
                "code": "http_rejected",
                "http_status": exc.code,
                "message": "the server returned an HTTP error; no automatic retry was attempted",
            },
        )
        return EXIT_ERROR
    except (URLError, TimeoutError, OSError) as exc:
        _checkpoint(
            args.output_dir,
            receipt,
            kind="dispatch_outcome_unknown",
            status="outcome_unknown",
            safe_to_retry=False,
            human_review_required=True,
            error={
                "code": "dispatch_outcome_unknown",
                "error_type": type(exc).__name__,
                "message": (
                    "the request crossed the dispatch boundary but no response was stored; "
                    "verify provider state or billing before any new attempt"
                ),
            },
        )
        return EXIT_OUTCOME_UNKNOWN
    except Exception as exc:  # noqa: BLE001 - preserve conservative effect classification.
        _checkpoint(
            args.output_dir,
            receipt,
            kind="dispatch_outcome_unknown",
            status="outcome_unknown",
            safe_to_retry=False,
            human_review_required=True,
            error={
                "code": "dispatch_outcome_unknown",
                "error_type": type(exc).__name__,
                "message": (
                    "the request crossed the dispatch boundary but no response was stored; "
                    "verify provider state or billing before any new attempt"
                ),
            },
        )
        return EXIT_OUTCOME_UNKNOWN
    return _finish_response(args.output_dir, receipt, raw_response, fixture=False)


def _positive_timeout(value: str) -> float:
    try:
        parsed = float(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError("timeout must be a number") from exc
    if not 0 < parsed <= 300:
        raise argparse.ArgumentTypeError("timeout must be greater than 0 and at most 300")
    return parsed


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Run one GameDesignOS skill through an OpenAI-compatible endpoint. "
            "The default is preview-only; --execute requires that exact prior preview."
        )
    )
    parser.add_argument("--skill", required=True, help="Skill folder name")
    parser.add_argument("--task", required=True, help="Bounded user task")
    materials = parser.add_mutually_exclusive_group()
    materials.add_argument("--materials", help="Inline materials")
    materials.add_argument("--materials-file", type=Path, help="UTF-8 materials file")
    parser.add_argument("--output-dir", type=Path, required=True, help="Explicit private output")
    parser.add_argument(
        "--repo",
        type=Path,
        default=Path(__file__).resolve().parents[2],
        help="GameDesignOS repository root",
    )
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument(
        "--execute",
        action="store_true",
        help="Send the exact existing preview; requires a prior dry-run",
    )
    mode.add_argument(
        "--fixture-response",
        type=Path,
        help="Offline OpenAI-compatible response fixture; never uses the network",
    )
    parser.add_argument("--timeout", type=_positive_timeout, default=60.0)
    return parser


def main(argv: list[str] | None = None, *, transport: Transport | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        fixture = args.fixture_response is not None
        preview = _request_preview(args, fixture=fixture)
        if fixture:
            result = _run_fixture(args, preview)
        elif args.execute:
            result = _run_live(args, preview, transport or _http_transport)
        else:
            _prepare_new_run(args.output_dir, preview, mode="dry-run")
            result = EXIT_OK
    except HarnessUsageError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return EXIT_ERROR
    except OSError as exc:
        print(f"error: local filesystem operation failed ({type(exc).__name__})", file=sys.stderr)
        return EXIT_ERROR

    if args.execute and result == EXIT_OK:
        print(f"Completed. Review {args.output_dir / RESULT_NAME}")
    elif args.execute and result == EXIT_OUTCOME_UNKNOWN:
        print(
            f"Outcome unknown. Inspect {args.output_dir / RECEIPT_NAME} before any new attempt.",
            file=sys.stderr,
        )
    elif fixture and result == EXIT_OK:
        print(f"Offline fixture completed. Review {args.output_dir / RESULT_NAME}")
    elif not args.execute and not fixture and result == EXIT_OK:
        print(
            f"Preview prepared at {args.output_dir / PREVIEW_NAME}. "
            "Review it, then repeat the same command with --execute."
        )
    return result


if __name__ == "__main__":
    raise SystemExit(main())
