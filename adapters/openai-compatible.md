# OpenAI-Compatible Adapter

GameDesignOS now ships a runnable, dependency-light reference host at [`../examples/hosts/openai_compatible.py`](../examples/hosts/openai_compatible.py). It can exercise one Skill against DeepSeek, Qwen, OpenRouter, or another OpenAI-compatible `/chat/completions` endpoint without turning the GameDesignOS core into a model gateway.

## Ownership Boundary

GameDesignOS owns:

- the selected Skill instructions;
- local request preview and response-shape validation;
- a candidate execution receipt with semantic checkpoints;
- explicit output files in a user-selected directory.

The host environment still owns:

- endpoint and model selection;
- credentials, billing, provider terms, and rate limits;
- network and private-material authorization;
- any later workspace diff, writeback, Human Gate, and rollback.

The script reads only these environment variables:

```text
GAMEDESIGNOS_BASE_URL
GAMEDESIGNOS_MODEL
GAMEDESIGNOS_API_KEY
```

The API key is never accepted as a command-line argument and is not written into the preview, receipt, or request body.

## Two-Phase Live Call

First prepare the exact disclosure preview without a network call:

```powershell
python examples/hosts/openai_compatible.py `
  --skill game-concept-architect `
  --task "Turn this lighthouse tactics idea into a bounded validation blueprint" `
  --output-dir outputs/openai-compatible-lighthouse
```

After reviewing `request-preview.private.json`, repeat the same command with `--execute`. Any change to the task, materials, Skill, endpoint, or model invalidates the prior approval and requires a fresh dry-run.

## Recovery Semantics

The receipt deliberately distinguishes:

| Checkpoint | Meaning | Retry guidance |
| --- | --- | --- |
| `request_prepared` | No external request has crossed the dispatch boundary | Safe to correct configuration and prepare again |
| `dispatch_intent_recorded` | A billable/external request is about to be attempted | Treat as `outcome_unknown` until a response is stored |
| `response_received` | Raw provider JSON is durably stored locally | Validate or inspect the stored response; do not pay for another call |
| `artifact_committed` | A non-empty assistant result passed shape validation and was written | Completed; no retry |

If the connection fails after the dispatch checkpoint, the harness records `status: outcome_unknown`, `safe_to_retry: false`, and requires manual verification of provider state or billing. It makes no automatic retry.

## Offline Fixture

CI and local smoke tests use [`../examples/hosts/fixtures/openai-chat-completion.json`](../examples/hosts/fixtures/openai-chat-completion.json). This proves request assembly, response parsing, checkpoints, and artifact commit only; it is not evidence that a real provider or model works.

Full commands, privacy warnings, and current non-goals are in [`../examples/hosts/README.md`](../examples/hosts/README.md).
