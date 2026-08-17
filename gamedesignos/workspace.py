"""Workspace object and deterministic asset lifecycle."""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from .constants import (
    ASSET_SPECS,
    LIFECYCLE_DIRS,
    PROJECT_READY_LIFECYCLE_DIRS,
    PROJECT_READY_WORKSPACE_SCHEMA_VERSION,
    RUNTIME_VERSION,
    SUPPORTED_RUNTIME_VERSIONS,
    SUPPORTED_WORKSPACE_SCHEMAS,
    VALID_SOURCE_STATUSES,
)
from .errors import UsageError, WorkspaceNotFoundError
from .io_utils import ensure_relative_safe, read_json, read_yaml, slugify, write_json, write_text
from .templates import asset_body, empty_asset_index, empty_decision_log
from .resources import find_source_root


@dataclass
class ValidationReport:
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    checks: list[str] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return not self.errors

    def as_dict(self) -> dict[str, Any]:
        return {"ok": self.ok, "errors": self.errors, "warnings": self.warnings, "checks": self.checks}


@dataclass
class WorkspaceStatus:
    project_id: str
    title: str
    codename: str
    project_status: str
    visibility: str
    owner: str
    workspace_schema_version: str
    runtime_version_declared: str
    runtime_version_current: str
    compatible: bool
    asset_counts_by_type: dict[str, int]
    asset_counts_by_review_state: dict[str, int]
    accepted_decisions: int
    unresolved_human_gates: int
    current_default_actions: list[str]
    missing_directories: list[str]

    def as_dict(self) -> dict[str, Any]:
        return self.__dict__.copy()


def find_repo_root(start: Path | None = None) -> Path | None:
    """Backward-compatible alias for callers that specifically need a checkout."""

    return find_source_root(start)


def find_workspace(start: Path | None = None) -> Path:
    current = (start or Path.cwd()).expanduser().resolve()
    if current.is_file():
        current = current.parent
    for candidate in [current, *current.parents]:
        if (candidate / "game.designos.yaml").is_file():
            return candidate
    raise WorkspaceNotFoundError(
        f"No GameDesignOS workspace found from {current}. Run `gamedesignos init <project>` first."
    )


class Workspace:
    def __init__(self, root: Path):
        self.root = root.expanduser().resolve()
        self.manifest_path = self.root / "game.designos.yaml"
        if not self.manifest_path.is_file():
            raise WorkspaceNotFoundError(f"Missing workspace manifest: {self.manifest_path}")
        manifest = read_yaml(self.manifest_path)
        if not isinstance(manifest, dict):
            raise UsageError(f"Workspace manifest must be a mapping: {self.manifest_path}")
        self.manifest = manifest

    @classmethod
    def open(cls, path: Path | None = None) -> "Workspace":
        root = find_workspace(path) if path is None else path.expanduser().resolve()
        if root.is_file():
            root = root.parent
        return cls(root)

    @property
    def project(self) -> dict[str, Any]:
        value = self.manifest.get("project")
        return value if isinstance(value, dict) else {}

    @property
    def designos(self) -> dict[str, Any]:
        value = self.manifest.get("designos")
        return value if isinstance(value, dict) else {}

    @property
    def assets_config(self) -> dict[str, Any]:
        value = self.manifest.get("assets")
        return value if isinstance(value, dict) else {}

    @property
    def workspace_id(self) -> str:
        return str(self.project.get("id") or "unknown-workspace")

    @property
    def visibility(self) -> str:
        return str(self.project.get("visibility") or "private")

    @property
    def asset_index_path(self) -> Path:
        return ensure_relative_safe(self.root, str(self.assets_config.get("index") or "design-asset-index.json"))

    @property
    def decision_log_path(self) -> Path:
        directory = str(self.assets_config.get("decisions_dir") or "06-decisions")
        return ensure_relative_safe(self.root, f"{directory}/decision-log.json")

    def lifecycle_path(self, key: str) -> Path:
        fallback = PROJECT_READY_LIFECYCLE_DIRS.get(key) or LIFECYCLE_DIRS.get(key)
        if fallback is None:
            raise UsageError(f"Unknown lifecycle directory key: {key}")
        return ensure_relative_safe(self.root, str(self.assets_config.get(key) or fallback))

    def load_asset_index(self) -> dict[str, Any]:
        schema = str(self.manifest.get("schema_version") or PROJECT_READY_WORKSPACE_SCHEMA_VERSION)
        data = read_json(self.asset_index_path) if self.asset_index_path.exists() else empty_asset_index(self.workspace_id, schema_version=schema)
        if not isinstance(data, dict) or not isinstance(data.get("assets"), list):
            raise UsageError(f"Invalid asset index: {self.asset_index_path}")
        return data

    def load_decision_log(self) -> dict[str, Any]:
        schema = str(self.manifest.get("schema_version") or PROJECT_READY_WORKSPACE_SCHEMA_VERSION)
        data = read_json(self.decision_log_path) if self.decision_log_path.exists() else empty_decision_log(self.workspace_id, schema_version=schema)
        if not isinstance(data, dict) or not isinstance(data.get("decisions"), list):
            raise UsageError(f"Invalid decision log: {self.decision_log_path}")
        return data

    def next_asset_id(self, prefix: str) -> str:
        marker = f"ASSET-{prefix}-"
        used = {
            int(str(item.get("asset_id"))[len(marker):])
            for item in self.load_asset_index()["assets"]
            if isinstance(item, dict)
            and str(item.get("asset_id") or "").startswith(marker)
            and str(item.get("asset_id"))[len(marker):].isdigit()
        }
        sequence = 1
        while sequence in used:
            sequence += 1
        return f"{marker}{sequence:03d}"

    def register_asset(self, entry: dict[str, Any], *, dry_run: bool = False) -> None:
        index = self.load_asset_index()
        if any(item.get("asset_id") == entry["asset_id"] for item in index["assets"] if isinstance(item, dict)):
            raise UsageError(f"Asset ID already exists: {entry['asset_id']}")
        if any(item.get("path") == entry["path"] for item in index["assets"] if isinstance(item, dict)):
            raise UsageError(f"Asset path already exists: {entry['path']}")
        index["assets"].append(entry)
        if not dry_run:
            write_json(self.asset_index_path, index)

    def create_asset(
        self,
        command_name: str,
        *,
        title: str | None = None,
        filename: str | None = None,
        created_by: str = "human-agent",
        source_status: str | None = None,
        dry_run: bool = False,
    ) -> dict[str, Any]:
        if command_name not in ASSET_SPECS:
            raise UsageError(f"Unknown asset type {command_name!r}")
        spec = ASSET_SPECS[command_name]
        title = (title or spec.default_title).strip()
        if not title:
            raise UsageError("Asset title must not be empty")
        asset_id = self.next_asset_id(spec.id_prefix)
        supplied = Path(filename or title)
        stem = supplied.stem if filename and supplied.suffix else str(supplied)
        directory = self.assets_config.get(spec.directory_key)
        if directory is None and self.manifest.get("schema_version") == PROJECT_READY_WORKSPACE_SCHEMA_VERSION:
            directory = {
                "concept_dir": "05-design-assets/concepts",
                "analysis_dir": "05-design-assets/analysis",
                "proposals_dir": "05-design-assets/proposals",
                "experiments_dir": PROJECT_READY_LIFECYCLE_DIRS["experiments_dir"],
                "decisions_dir": PROJECT_READY_LIFECYCLE_DIRS["decisions_dir"],
                "retrospectives_dir": PROJECT_READY_LIFECYCLE_DIRS["learning_dir"],
                "evidence_dir": PROJECT_READY_LIFECYCLE_DIRS["evidence_dir"],
            }.get(spec.directory_key)
        if directory is None:
            directory = LIFECYCLE_DIRS[spec.directory_key]
        relative = f"{directory}/{slugify(stem, fallback=command_name)}.{spec.extension}"
        target = ensure_relative_safe(self.root, relative)
        if target.exists():
            raise UsageError(f"Refusing to overwrite existing asset: {relative}")
        if source_status is None:
            source_status = {"private": "private", "public-synthetic": "synthetic", "public-cleared": "cleared"}.get(self.visibility, "needs_review")
        if source_status not in VALID_SOURCE_STATUSES:
            raise UsageError(f"Invalid source status: {source_status}")
        body = asset_body(command_name, asset_id=asset_id, title=title, workspace_id=self.workspace_id)
        if not dry_run:
            write_json(target, body) if spec.extension == "json" else write_text(target, str(body))
        entry: dict[str, Any] = {
            "asset_id": asset_id,
            "asset_type": spec.index_type,
            "title": title,
            "path": relative,
            "format": "json" if spec.extension == "json" else "markdown",
            "created_by": created_by,
            "source_status": source_status,
            "review_status": "draft",
            "upstream_assets": [],
            "downstream_assets": [],
            "notes": "Runtime-generated draft; replace placeholders with evidence or explicit assumptions.",
        }
        if spec.source_skill:
            entry["source_skill"] = spec.source_skill
        self.register_asset(entry, dry_run=dry_run)
        return {"asset": entry, "path": str(target), "dry_run": dry_run}

    def status(self) -> WorkspaceStatus:
        assets = [item for item in self.load_asset_index()["assets"] if isinstance(item, dict)]
        schema = str(self.manifest.get("schema_version") or "")
        if schema == PROJECT_READY_WORKSPACE_SCHEMA_VERSION:
            # Import locally to keep Workspace usable without a module cycle.
            from .project_ready import load_project_ready_state

            decisions = list(load_project_ready_state(self)["decisions"].values())
        else:
            decisions = [item for item in self.load_decision_log()["decisions"] if isinstance(item, dict)]
        runtime = str(self.designos.get("version") or "")
        return WorkspaceStatus(
            project_id=self.workspace_id,
            title=str(self.project.get("title") or ""),
            codename=str(self.project.get("codename") or ""),
            project_status=str(self.project.get("status") or ""),
            visibility=self.visibility,
            owner=str(self.project.get("owner") or ""),
            workspace_schema_version=schema,
            runtime_version_declared=runtime,
            runtime_version_current=RUNTIME_VERSION,
            compatible=schema in SUPPORTED_WORKSPACE_SCHEMAS and runtime in SUPPORTED_RUNTIME_VERSIONS,
            asset_counts_by_type=dict(Counter(str(item.get("asset_type") or "unknown") for item in assets)),
            asset_counts_by_review_state=dict(Counter(str(item.get("review_status") or "unknown") for item in assets)),
            accepted_decisions=sum(item.get("status") == "accepted" for item in decisions),
            unresolved_human_gates=sum(item.get("status") == "proposed" for item in decisions),
            current_default_actions=list(dict.fromkeys(str(item["current_default_action"]) for item in decisions if item.get("current_default_action"))),
            missing_directories=[
                str(self.assets_config.get(key) or default)
                for key, default in (
                    PROJECT_READY_LIFECYCLE_DIRS.items()
                    if schema == PROJECT_READY_WORKSPACE_SCHEMA_VERSION
                    else LIFECYCLE_DIRS.items()
                )
                if key != "exports_dir" and not self.lifecycle_path(key).is_dir()
            ],
        )

    def validate(self, *, repo_root: Path | None = None) -> ValidationReport:
        from .workspace_validation import validate_workspace

        return validate_workspace(self, repo_root=repo_root)

    def pack(self, *, mode: str, output: Path | None = None, dry_run: bool = False, force: bool = False) -> dict[str, Any]:
        from .workspace_pack import pack_workspace

        return pack_workspace(self, mode=mode, output=output, dry_run=dry_run, force=force)


from .workspace_init import doctor, init_workspace  # noqa: E402,F401
