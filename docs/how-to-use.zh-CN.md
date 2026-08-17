# GameDesignOS 怎么用

GameDesignOS 有三种用法。新用户只需要先记第一种。

第一次接触时，可以先运行一条零配置演示：

```bash
python -m gamedesignos demo
```

它只生成公开 synthetic 数据，不调用模型、不需要密钥，并在 Commitment Human Gate 前停住。默认使用系统临时目录；指定 `--destination <空目录>` 可保留在固定位置。

## 1. 拉取后随便发一句

如果你在 Codex、Claude Code、OpenCode 这类支持 `AGENTS.md` 的 agent 环境里，直接发一句需求即可。agent 会自己判断该用哪个 skill、是否要开 Project workspace、是否需要追问材料，然后继续产出结果。

下面的命令主要给命令行用户做本地验证和状态审计：

不安装也可以在仓库根目录直接用：

```bash
python -m gamedesignos "我想做一款修灯塔的策略游戏"
```

也可以显式写成：

```bash
python -m gamedesignos ask "我想做一款修灯塔的策略游戏"
```

它会自动判断这句话应该进入哪个 skill，但默认不写盘。只有显式提供 `--destination` / `--workspace`，或明确调用 `start`，才会创建或恢复 Project-Ready workspace，并准备第一条决策、假设、三分钟验证实验和工作流。命令行只负责本地路由和状态；真正的 agent 应继续读取并调用对应 skill，而不是把提示词甩回给用户。

如果想安装成系统命令：

```bash
python -m pip install -e .
gamedesignos "我想做一款修灯塔的策略游戏"
```

## 2. 用整个项目推进长期工作

当你要持续推进一个游戏项目，用项目模式：

```bash
python -m gamedesignos start "My Game" --destination ../my-game-designos --owner your-name
```

它会生成：

- `game.designos.yaml`：项目身份；
- `01-decisions/`：决策；
- `02-assumptions/`：假设；
- `03-evidence/`：证据；
- `04-experiments/`：实验；
- `.gamedesignos/workflow-runs/`：工作流状态。

终端会告诉你“下一步只做一件事”。默认是先做一次 3-5 人/自测的三分钟验证，再记录一条观察。

## 3. 每个 Skill 单独使用

普通用户不需要记住这些 skill 名。只要需求足够具体，agent 应该自己追问缺少的材料，或直接调用对应 skill。

下面这些提示词用于手动点名、调试路由，或在没有 `AGENTS.md` 的环境里复制使用。

### Game Experience Analyzer

用于：截图、录屏、PV、视频、商店页、试玩样本、竞品体验分析。

```text
Use $game-experience-analyzer to analyze this gameplay recording into timestamped evidence, sample boundary, diagnosis route, issue cards, and validation recommendations.
```

### Game Concept Architect

用于：一句话游戏创意、玩法点子、核心循环、立项方向、prototype validation。

```text
Use $game-concept-architect to turn this one-line game idea into concept seed extraction, player promise contract, core loop, scope gate, and prototype validation plan.
```

### Game Experience Density Optimizer

用于：留存、首局、节奏、反馈、具身感、氛围感、认知负荷、A/B、埋点、看板、回滚门。

```text
Use $game-experience-density-optimizer to turn this first-session pacing problem into ED diagnosis, weekly variants, instrumentation, decision rules, and rollback gates.
```

### Game Design Proposal Writer

用于：商业策划案、独游设计案、publisher pitch、投资 pitch、GDD、vertical slice、决策 memo。

```text
Use $game-design-proposal-writer to assemble this concept brief, evidence notes, validation plan, and production constraints into a decision-ready game proposal.
```

### Paranoia AI System Evolver

用于：prompt、workflow、schema、eval、router、memory、skill、automation、agent 规则升级，也用于把 AI 工作单从指令单升级成意图单，并把项目整体流程、产出质量、验收、rollback 和复盘沉淀纳入 workflow governance review。

```text
Use $paranoia-ai-system-evolver to upgrade this workflow or AI work order into an Intent Work Order with WOOP, VOI, OODA, eval checks, Human Gate, rollback, and retrospective candidate learning.
```

### Game Design Book Translator

用于：英文游戏设计书籍、章节、长文、术语表、图注、表格翻译。

```text
Use $game-design-book-translator to translate and polish this game design chapter into professional Chinese, including terminology and figure captions.
```

### Game Design Source Curator

用于：文章、视频、作者、栏目、网站、资料库、知识库整理。

```text
Use $game-design-source-curator to review these game design sources and turn accepted items into a maintainable local knowledge base.
```

## 4. 怎么判断该用项目模式还是单独 skill

| 情况 | 推荐 |
| --- | --- |
| 只是翻译一段、分析一个视频、整理一批资料 | agent 直接调用对应 skill |
| 想长期推进一个游戏项目 | 用 `start` 创建 workspace |
| 不知道该用哪个 skill | agent 用 `python -m gamedesignos ask "<你的原话>"` 路由 |
| 要产出策划案，但还没有概念、证据或验证计划 | agent 先用 `ask` 或 `game-concept-architect` 补上游 |
| 要做留存/节奏实验，但没有证据样本 | agent 先用 `game-experience-analyzer` 建证据层 |

## 5. 安全边界

- 真实项目资料放在公开仓库外。
- private、synthetic、public、cleared、needs_review 要标清楚。
- AI 可以建议和检查，但不能替人接受 Human Gate。
- 没有证据时，不要声称真实留存、收入、转化、玩家情绪或市场表现。
