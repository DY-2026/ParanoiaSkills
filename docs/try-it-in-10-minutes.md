# Try It in 10 Minutes

This guide helps a new user understand and test `GameDesignOS` without adding private material to the public repository.

## Run The Zero-Configuration Demo

```bash
python -m pip install -e .
python -m gamedesignos demo
```

This command makes no model calls and needs no key. It creates a fresh public-synthetic workspace in the system temporary directory, shows a Decision, Assumption, Evidence, reviewed Experiment, rollback, and next action, then stops before the `decision accept` Human Gate. Use `--destination <empty-path>` when you want a fixed location.

## Who This Project Is For

- Game designers who want evidence-linked diagnosis from screenshots, PVs, trailers, or gameplay recordings.
- Indie developers who want to turn a one-line idea into a testable concept blueprint.
- Agent-workflow builders who want portable Markdown skills with validation gates, not one-off prompts.
- Designers and producers who want to turn retention, pacing, feedback, embodiment, atmosphere, or cognitive-load problems into weekly ED experiments.
- Teams that want to use real projects privately while keeping public examples synthetic, public, or cleared.
- Teams that want a durable project workspace for concepts, evidence, experiments, proposals, decisions, and retrospectives.

## Start A Project Workspace

After cloning the repository, you can start with one sentence:

```bash
python -m pip install -e .
gamedesignos "I want to make a lighthouse tactics game"
```

The natural-language entry recommends the right skill without writing by default. Supply `--destination` / `--workspace`, or use `start`, to prepare the first Decision, Assumption, three-minute validation Experiment, VOI Gate, and workflow.

For a one-off task, you may skip the workspace and call a skill directly.

## Which Skill To Choose

| Your input | Choose this skill | Main output |
| --- | --- | --- |
| PV, trailer, gameplay recording, screenshot, or video link | `$game-experience-analyzer` | Evidence index, diagnosis route, issue cards, validation plan |
| One-line game idea | `$game-concept-architect` | Concept seed, player promise, core loop, scope gate, validation plan |
| Concept, evidence, validation, source, ED, or production assets need a formal document | `$game-design-proposal-writer` | Proposal, pitch, decision memo, or vertical-slice document |
| Research choice, FOMO, information overload, AI branch pruning, prompt, workflow, schema, eval, memory, or agent rule | `$paranoia-ai-system-evolver` | Decision Object, information-value assessment, controlled evolution proposal, Human Gate, and rollback |
| Retention, pacing, feedback, embodiment, atmosphere, or cognitive-load problem | `$game-experience-density-optimizer` | ED diagnosis, weekly A/B variants, instrumentation, dashboard fields, rollback gates |
| Design chapter or long-form English material | `$game-design-book-translator` | Professional Chinese design translation |
| Articles, videos, creators, columns, or websites | `$game-design-source-curator` | Traceable, maintainable knowledge assets |

## Which Folder To Copy

For an ongoing project, prefer `gamedesignos start ...` outside the repository. The raw `runtime/workspace-template-v1/` folder is mostly for maintainers and manual inspection.

For direct skill mode, copy only the skill folder you want to try:

```text
game-experience-analyzer/
game-concept-architect/
game-design-proposal-writer/
paranoia-ai-system-evolver/
game-experience-density-optimizer/
game-design-book-translator/
game-design-source-curator/
```

For a first direct-skill test, copy one folder only. Confirm that `SKILL.md`, `references/`, `templates/`, and `examples/` remain in the same relative layout.

## How To Run A VOI Decision Gate

Use this before broad research, more AI conversations, memory reads, or experiments.

```text
Use $paranoia-ai-system-evolver to decide whether this information action is worth doing.

Decision: <what must be decided>
Options: <real actions still available>
Current default action: <what I will do without more information>
Deadline: <when the decision must be made>
Stakes and reversibility: <cost of being wrong>
Candidate information action: <search / ask / inspect / test>

Return the decision boundary, target uncertainty, possible signals, action for each signal, EVPI ceiling, practical EVSI, total information cost, smallest positive-net-VOI probe, and stop rule.
```

If every plausible signal leads to the same action, stop the research or classify it as model learning / information consumption. For durable projects, save the result as `06-decisions/information-value-assessment.json`.

## How To Trigger `$game-experience-analyzer`

Use this when you have public, synthetic, or private-in-your-own-environment media. Do not submit private media back to this public repository.

```text
Use $game-experience-analyzer to analyze this gameplay recording or PV into timestamped evidence, sample boundary, diagnosis route, Hook/Loop/Link/Surprise diagnosis, issue cards, and validation recommendations.

Input material:
- Source: <public link, local private file, or synthetic sample>
- Sample type: PV / trailer / gameplay recording / screenshot set
- What I want to learn: <early hook, core loop clarity, UX risk, conversion risk, mechanic-transfer boundary>
```

## How To Trigger `$game-concept-architect`

Use this when you have a rough idea and need a verifiable design blueprint.

```text
Use $game-concept-architect to turn this one-line idea into concept seed extraction, design nucleus options, player promise contract, core loop, scope gate, production feasibility check, and prototype validation plan.

Idea:
A short tactics game about repairing a drifting lighthouse while storms change the map every night.
```

## How To Trigger `$game-experience-density-optimizer`

Use this when you have a playable prototype, live build, test recording, design problem, or telemetry snapshot and want to turn experience concentration into a rollbackable weekly experiment.

```text
Use $game-experience-density-optimizer to turn this first-session retention, pacing, or experience concentration problem into an ED diagnosis, CLP/SF/EB/AR/MD-min levers, a weekly A/B plan, instrumentation, dashboard fields, decision rules, and rollback gates.

Input material:
- Source: <private notes, telemetry snapshot, playtest summary, or evidence report>
- Segment: <first session, return session, fatigue segment, tutorial, combat loop>
- Current problem: <empty, confusing, soft feedback, not embodied, no atmosphere, choices too weak>
```

## Minimal Input Examples

### PV Or Recording Diagnosis

```text
Use $game-experience-analyzer on this public gameplay recording:
<link>

Please focus on the first 3 minutes, visible player verbs, feature exposure, UI density, and what claims are unsupported by this sample.
```

### One-Line Concept Architecture

```text
Use $game-concept-architect:
One-line idea: A cozy roguelite shop game where every item sold changes the town's future problems.
```

### Workflow Evolution

```text
Use $paranoia-ai-system-evolver to upgrade this agent workflow:
When asked for game analysis, first gather evidence, then write conclusions.

Please add VOI, OODA, eval checks, Human Gate, and rollback criteria.
```

### Experience Concentration Experiment

```text
Use $game-experience-density-optimizer:
Our first 8 minutes feel empty. Players understand the controls, but the first meaningful build choice happens too late, combat feedback feels soft, and D1 is weak. We only have a small playtest summary, no telemetry yet.
```

## Expected Output Structure

`$game-experience-analyzer` should usually return:

- Sample boundary and unsupported judgment scope.
- Evidence index with timestamps, screenshots, observed facts, and confidence.
- Diagnosis route or diagnosis pack selection.
- Issue cards with severity, evidence, interpretation, and proposed fix.
- Validation plan that names what would prove or disprove the diagnosis.

`$game-concept-architect` should usually return:

- Concept seed extraction.
- Assumption ledger.
- Design nucleus options.
- Player promise contract.
- Core loop and player verbs.
- Scope or production feasibility gate.
- Prototype validation plan.

`$paranoia-ai-system-evolver` should usually return:

- Current workflow diagnosis.
- Proposed candidate change.
- VOI decision and OODA loop.
- Eval or regression checks.
- Human Gate requirements.
- Rollback plan.

`$game-experience-density-optimizer` should usually return:

- Case boundary and `theory_status: design_hypothesis`.
- ED diagnosis across CLP, SF, EB, AR, and MD/min.
- A "reduce noise -> improve quality -> tune frequency" order.
- Rollbackable A/B variants.
- Instrumentation dictionary and dashboard fields.
- Pre-registered decision and rollback rules.

## How To Check The Output Did Not Go Out Of Bounds

Ask these checks before trusting or publishing an output:

- Does every strong claim point to evidence, a timestamp, a screenshot, a source, or a named assumption?
- Does the output list what the sample cannot prove?
- Does it avoid claiming real retention, revenue, conversion, player sentiment, or market performance unless that data was provided?
- Does it label private, synthetic, public, and cleared material correctly?
- Does it avoid leaking local paths, client names, unreleased project plans, budgets, roadmaps, or private overlays?
- Does it include a validation plan instead of treating diagnosis as final truth?

## How To Run Repository Validation

From the repository root:

```text
python scripts/validate_repo.py
```

For targeted checks:

```text
python scripts/validate_skill.py game-experience-analyzer
python scripts/validate_skill.py game-concept-architect
python scripts/validate_skill.py paranoia-ai-system-evolver
python scripts/validate_skill.py game-experience-density-optimizer
python scripts/validate_skill.py game-design-proposal-writer
```

## How To Avoid Publishing Private Overlay Or Real Project Cases

- Use real projects only in your own private environment.
- Keep private overlays outside this repository.
- Do not commit client work, unreleased roadmaps, internal strategy, local workspace outputs, private screenshots, private recordings, or private examples.
- Public repository examples must be `synthetic`, `public`, or `cleared`.
- If source status is unclear, mark it `needs_review` and do not publish it as a public example.
- Before opening a PR or issue, remove private identifiers, local paths, budgets, dates, launch plans, and any detail that lets readers infer the real project.
