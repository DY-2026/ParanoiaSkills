# GameDesignOS Adapters

`GameDesignOS` is not an API service. It does not hold, request, proxy, store, or manage API keys.

The public repository ships:

```text
Markdown skill packages
shared contracts
project workspace template
runtime documentation
adapter notes
validation tools
```

API keys, model credentials, user identity, billing, tool permissions, and runtime policy belong to the host agent or local harness.

## Workspace-Aware Integration Model

1. Open an existing GameDesignOS workspace or create one from [`../runtime/workspace-template/`](../runtime/workspace-template/).
2. Read `game.designos.yaml`.
3. Inspect the design-asset index and accepted decisions.
4. Identify the user's requested decision or output, the real options, and the current default action.
5. Before broad retrieval, memory reads, tests, or extra AI branches, run the VOI Decision Gate: name the target uncertainty, possible signals, action for each signal, total information cost, and stop rule.
6. Use [`../contracts/router.yaml`](../contracts/router.yaml) to choose the smallest suitable skill.
7. Load the selected skill's `SKILL.md`.
8. Read `references/` and `templates/` only when the task needs them.
9. Pass only the required user-provided and workspace materials to the host model.
10. Save outputs to the correct workspace lifecycle directory.
11. Update asset dependencies and review state.
12. Validate Markdown, JSON, and YAML before saving, publishing, or handing off.
13. Stop at a Human Gate when a commitment, publication, scope change, or rollback decision is required.

## Direct Skill Mode

Workspace use is recommended for ongoing projects, but it is optional. A host may still load one skill package directly:

```text
SKILL.md
references/
templates/
examples/
agents/
evals/
```

Direct skill mode should preserve the same evidence, privacy, validation, and unsupported-claim boundaries.

## Runtime Boundary

The host or harness is responsible for:

- model selection and calls;
- credentials and billing;
- local file permissions;
- network and tool permissions;
- private-material disclosure previews;
- retries and rate limits;
- persistence and backups;
- user identity and team permissions.

GameDesignOS provides workflow and artifact contracts; it does not silently upload a workspace or decide host policy.

## Adapter Notes

- [`openai-compatible.md`](./openai-compatible.md): runnable preview-first OpenAI-compatible reference host, offline fixture, and recovery boundary.
- [`codex.md`](./codex.md): local Codex-style skill loading and validation notes.
- [`claude-code.md`](./claude-code.md): using skill folders as Claude Code project instructions or local docs.
- [`local-agent-harness.md`](./local-agent-harness.md): minimum local harness component sketch.

When packaging examples, evals, demos, or public adapter fixtures, follow [`../CONTRIBUTING.md`](../CONTRIBUTING.md).

## FAQ

**Q: 支持 API key 调用吗？**

**A:** GameDesignOS 本身不是 API 服务，也不持有 API key。你可以在 OpenAI-compatible、Claude Code、Codex、OpenCode 或本地 agent harness 中加载 skill 与 workspace，由宿主环境管理 API key、模型调用和权限。

**Q: v0.8.0 是否已经提供完整 CLI？**

**A:** 没有。v0.8.0 提供 Runtime Foundation、workspace 模板和 CLI 命令契约；完整本地 CLI 属于后续能力门。
