<p align="center">
  <img src="./assets/gamedesignos-github-hero-v2.png" alt="GameDesignOS 把碎片化 AI 游戏设计输出转成证据、实验、决策和长期项目记忆" width="100%">
</p>

<h1 align="center">GameDesignOS</h1>

<p align="center">
  <strong>把 AI 输出变成可验证的游戏设计决策。</strong><br>
  本地优先 · 证据可追溯 · 决策有人把关
</p>

<p align="center">
  GameDesignOS 是一层 local-first 的 AI 辅助游戏设计操作层。
  你可以带来一句创意、一段试玩、研究资料或流程问题，得到可评审的证据、实验、策划案、决策和项目记忆；涉及承诺与方向改变的判断仍然留在人手里。
</p>

<p align="center">
  <a href="./README.en.md">English</a> ·
  <a href="#快速开始">快速开始</a> ·
  <a href="./docs/workflows/">工作流</a> ·
  <a href="#github-案例">案例</a> ·
  <a href="./docs/product/roadmap.md">路线图</a>
</p>

<p align="center">
  <img alt="Version" src="https://img.shields.io/badge/Version-v1.2.0-31e1d6">
  <img alt="Validation" src="https://github.com/DY-2026/GameDesignOS/actions/workflows/validate.yml/badge.svg">
  <img alt="License" src="https://img.shields.io/badge/License-MIT-2ea44f">
  <img alt="Runtime" src="https://img.shields.io/badge/Runtime-Local--first-8a63d2">
  <img alt="Human Gate" src="https://img.shields.io/badge/Authority-Human--gated-f9a825">
</p>

```text
创意 / 试玩 / 研究 / 流程问题
              ↓
证据 → 实验 → 决策 → 学习
              ↑
       Human Gate + rollback
```

## 快速开始

```bash
git clone https://github.com/DY-2026/GameDesignOS.git
cd GameDesignOS
python -m pip install -e .
python -m gamedesignos ask "我想验证一款修灯塔的策略游戏"
```

`ask` 默认只推荐最小合适 skill，不会静默写盘。需要长期私有项目时，显式创建 workspace：

```bash
python -m gamedesignos start "灯塔战术" --destination ../lighthouse-designos
```

## 为什么需要它

AI 写得越来越快，但团队做决策没有同样变快。游戏设计工作常常散在聊天记录、截图、录屏、竞品笔记、GDD 草稿、实验想法和个人记忆里；更多 AI 输出只会制造更多碎片。

GameDesignOS 补的是中间那层操作系统：把 agent 输出转成有来源、有契约、有质量门、有 rollback 的项目资产，让设计者从创意、证据、实验走到决策时，不用每一轮都重新解释上下文。

决定权仍然在人手里。系统提供的是专家工作流、可交接 contract、本地状态和 Human Gate 前停住的纪律。

## 包含什么

| 类别 | 数量 | 它给你什么 |
| --- | ---: | --- |
| 专家 skill | 7 | 概念架构、体验分析、ED 优化、策划案写作、工作流演化、书籍翻译和资料策展 |
| Contract schema | 19 | 决策、假设、证据、实验、UL 状态、学习记录、质量门、工作流、issue、玩家承诺和项目资产的稳定交接格式 |
| v1 workspace 分区 | 9 | 9 个生命周期目录：Inbox、Decision、Assumption、Evidence、Experiment、Design Asset、Workflow、Learning、Export；runtime 状态独立保存在 `.gamedesignos/` |
| 端到端工作流 | 5 | idea-to-validation、media-to-diagnosis、weekly ED experiment、evidence-to-proposal、decision-to-information |
| 宿主 adapter | 4 | Codex、Claude Code、OpenAI-compatible agent 和本地 harness 接入说明 |
| 公开 proof case | 2 | 带证据边界的游戏体验分析与体验浓度实验案例 |
| Runtime | 1 | 用于路由、创建 workspace、校验、健康扫描、决策图、gate 和可评审 pack 的确定性本地 CLI |

> **开发候选版本：v1.3.0.dev0。** 候选 wheel 已自带 contracts/templates，`router.yaml` 是唯一可编辑路由真源；UL（Uncertainty Ladder，不确定性阶梯）现在拥有 `ul_state` schema、UL-L0～UL-L5、workflow 可选引用与失败归因/迁移回归。7/7 skill 通过 Agent Skills 规范，现有行为夹具仍为 11 suites / 72 evals。最新带 tag 的稳定源码版本是 v1.2.0，对应 [GitHub Release](https://github.com/DY-2026/GameDesignOS/releases/tag/v1.2.0) 已公开并标记为 Latest。

## v1.2.0 Project-Ready Runtime

v1.2.0 保持本地 `gamedesignos` runtime 的 Project-Ready 主链路，并加入 Intent Work Order 与 `workflow-run.governance`：AI 工作先说明要改变什么现实，每条 workflow 都可以保留 intent / VOI / RJR / Human Gate / rollback / candidate learning 引用，领域 skill 仍然负责自己的主产出。CLI 是确定性、本地优先的：它能创建 v1 项目 workspace，管理 Decision、Assumption、Evidence、Experiment、Gate、Workflow 和 Learning，导出决策图，扫描项目健康，并生成可评审 pack，不会调用模型。

| 层级 | 作用 | 入口 |
| --- | --- | --- |
| **Skill Kernel** | 七个边界清楚的专家工作流 | [`当前 Skill`](#当前-skill) |
| **Contract Layer** | 稳定交接、schema 与路由边界 | [`contracts/`](./contracts/) |
| **Project Workspace** | 长期保存概念、证据、分析、实验、策划案与决策 | [`runtime/workspace-template-v1/`](./runtime/workspace-template-v1/) |
| **Runtime Interface** | 可执行本地命令与宿主 agent 接入边界 | [`runtime/`](./runtime/) / [`gamedesignos/`](./gamedesignos/) |

拉取项目后，如果是在 Codex、Claude Code、OpenCode 这类支持 `AGENTS.md` 的 agent 环境里，用户直接发一句需求即可；agent 会自己路由、追问缺失材料或调用具体 skill，并在需要时创建 Project-Ready workspace。

命令行用户可以不安装，直接在仓库根目录验证同一条入口：

```bash
python -m gamedesignos "我想做一款修灯塔的策略游戏"
```

如果想显式创建长期项目空间：

```bash
python -m gamedesignos start "My Game" --destination ../my-game-designos --owner your-name
```

`ask` 默认只做路由，不会因为置信度高就写盘；只有显式提供 `--destination` / `--workspace`，或明确调用 `start`，才准备 workspace、第一条决策、第一条假设、三分钟验证实验和工作流。CLI 负责本地路由和状态审计；宿主 agent 负责继续读取并执行选中的 skill，不把提示词再丢给用户。原有 skill 仍可独立安装；runtime 保持 v0.8/v0.9 workspace 兼容。

详细内容见 [怎么用](./docs/how-to-use.zh-CN.md)、[v1.0 基线开发计划](./docs/product/v1.0-development-plan.md)、[CLI 指南](./runtime/cli/README.md)、[命令参考](./runtime/cli/commands.md)、[v1.2 release note](./releases/v1.2.0.md) 和 [路线图](./docs/product/roadmap.md)。

决策优先的信息审计提示词：

```text
Use $paranoia-ai-system-evolver to audit this research or AI workflow with a Decision Object, current default action, decision boundary, EVPI/EVSI, signal-to-action map, the smallest high-VOI probe, and a stop rule.
```

RJR-AI 升级提示词：

```text
Use $paranoia-ai-system-evolver to turn this AI workflow into an RJR-AI system: list what AI can search or draft, what workflow must constrain, what evals must test, what permissions block overreach, what knowledge should persist, and which residual judgments must stay with a human.
```

意图工作单提示词：

```text
Use $paranoia-ai-system-evolver to upgrade this AI work order from an instruction sheet into an Intent Work Order: define the reality to change, project goal, desired outside-world state, verifier, first-glance acceptance, non-sacrifice boundaries, AI freedom, AI no-touch boundary, direction-change principles, delivery failure signals, and retrospective candidate learning.
```

## 这个项目是什么

`GameDesignOS` 是一套 local-first 的 AI 辅助游戏设计操作系统。它把 AI-agent session 转成可持续使用的设计资产：Decision、Assumption、Evidence、Experiment、Proposal、Workflow 和 Learning Record。

它的公开基础层由 **Skill Kernel**、**Contract Layer**、**Project Workspace** 和可执行 **Runtime Interface** 组成，用于立项验证、体验诊断、策划案写作和工作流演化。

skill 提供边界清楚的专家能力，contract 让产物可以交接，workspace 保存长期项目上下文，runtime 则给宿主 agent 或本地 CLI 提供确定性的读取、路由、写回、校验、打包和 Human Gate 停止能力。

它不是一张零散 skill 清单，也不是一堆提示词合集。它更像一套小型游戏设计操作系统，并用契约让不同 skill 之间能交接工作，而不是各自输出孤立长文：

```text
媒体证据 -> evidence index -> issue cards -> ED handoff -> 一周实验
一句话创意 -> player-promise contract -> validation plan -> 后续媒体诊断
概念/证据/生产约束 -> 可评审策划案 -> pitch 或 milestone gate
workflow 改动 -> WOOP Task Card -> VOI/OODA probe -> eval -> Human Gate -> rollback
书籍与资料 -> 结构化知识资产 -> 未来任务可复用 reference
```

## 它哪里不一样

- **Evidence-first:** 判断尽量绑定到来源、截图区域、时间戳、样本证据或验证指标。
- **Contract-driven:** concept brief、evidence index、issue card、ED handoff 和 validation plan 可以跨 skill 流转。
- **Workspace-native:** 概念、证据、分析、实验、策划案、决策和复盘保存在同一个项目上下文中。
- **Human-gated:** agent 可以提出和组织方案，但改变项目承诺的决策必须由人记录。
- **剩余判断权边界：** 高耦合、低可逆、证据不足的选择仍由人拥有；AI、workflow、eval、权限和记忆只负责围绕方向对齐。
- **决策优先的信息门：** 在广泛调研前，先声明决策、当前默认行动、决策边界、信号—行动映射、信息成本和停止规则。
- **Concept-to-validation:** 不把“绝妙点子”直接扩写成 GDD，而是拆成 seed、玩家承诺、核心循环、scope gate 和原型验证计划。
- **Workflow-governed:** 不追求一次漂亮回答，而是把可复用流程沉淀到 `SKILL.md`、`references/`、`templates/`、eval、Human Gate 和 rollback。
- **Agent portable:** Codex、Claude Code、OpenCode 或其他能读取 Markdown skill 的 agent 环境都可以迁移。
- **Public/private safe:** 公开示例只使用 synthetic、public、cleared 或 `needs_review` 材料；真实项目留在你自己的环境中。

## Try It in 5 Prompts

```text
Use $game-experience-analyzer to diagnose this PV or gameplay recording into sample boundary, timestamped evidence, Hook/Loop/Link/Surprise diagnosis, issue cards, and validation recommendations.
```

```text
Use $game-concept-architect to turn this one-line game idea into concept seed extraction, design nucleus options, player promise contract, core loop, scope gate, and prototype validation plan.
```

```text
Use $game-design-proposal-writer to turn this concept brief, validation plan, evidence notes, and production constraints into a decision-ready commercial proposal, indie dossier, publisher pitch, or vertical-slice document.
```

```text
Use $paranoia-ai-system-evolver to upgrade this workflow or AI work order into an Intent Work Order with a WOOP Task Card, VOI, OODA, eval checks, Human Gate, rollback, and retrospective candidate learning.
```

```text
Use $game-experience-density-optimizer to turn this first-session retention, pacing, or experience density problem into an ED diagnosis, CLP/SF/EB/AR/MD-min levers, a weekly A/B plan, instrumentation, dashboard fields, decision rules, and rollback gates.
```

完整上手路径见 [10 分钟上手 GameDesignOS](./docs/try-it-in-10-minutes.zh-CN.md)。

## 60 秒 Demo

输入一张截图、一段录屏、一个 PV/宣传片或视频链接，让 skill 直接输出证据化设计报告：

<p align="center">
  <img src="./assets/demo-game-experience-before-after.png" alt="60 秒 demo：Game Experience Analyzer 把 PV 输入转成证据化报告" width="100%">
</p>

```text
Use $game-experience-analyzer to analyze this gameplay recording into timestamped evidence, feature exposure/unlock/first-use ledger, Hook/Loop/Link/Surprise diagnosis, and actionable fixes.
```

具体 proof path 统一放在下面的案例表里。上面的 demo 展示最快交互方式；下面的案例展示可复查输出和证据边界。

## GitHub 案例

如果只是打开 GitHub 页面想快速判断项目是否有实际产物，先看这两个案例即可：第一个展示单条录屏如何进入 Game Experience Analyzer 报告；第二个展示公开视频证据如何继续进入体验浓度实验包。

| 案例 | Skill 路线 | 重点看什么 | 链接 |
| --- | --- | --- | --- |
| `《生存33天》41 分钟试玩录屏` | `$game-experience-analyzer` | 录屏样本如何变成时间戳证据、截图证据卡、功能暴露/解锁/首用账本、前期循环诊断、UI/引导风险和可验证修改建议。来源状态：`needs_review`。 | [打开报告](./game-experience-analyzer/examples/survival-33-days-gameplay-experience-report.md) |
| `《冒险家艾略特的千年奇谭》Demo` | `$game-experience-analyzer -> $game-experience-density-optimizer` | 公开视频关键帧如何变成 ED 证据门、指标周期、截图证据卡、变体矩阵、埋点和回滚规则。 | [打开案例](./docs/showcases/elliot-experience-density-report/README.md) |

## 轻松上手

持续项目建议先创建 workspace，让上下文长期保留；一次性任务仍可直接调用单个 skill。

### 1. 创建项目 Workspace

```bash
python -m gamedesignos "我想做一款修灯塔的策略游戏"
```

如果要明确指定 workspace 位置：

```bash
python -m gamedesignos start "My Game" --destination ../my-game-designos --owner your-name
```

把真实项目保存在公开仓库外。自然语言入口默认只给出路由建议；显式提供目标路径或调用 `start` 才会搭建第一轮验证链路。

### 2. 不知道选哪个？先看这张表

| 你手里的材料 | 该用哪个 skill | 你会得到什么 |
| --- | --- | --- |
| 截图、录屏、PV、视频链接 | `$game-experience-analyzer` | 带时间戳/证据/问题优先级的体验报告，或游戏拆解、机制迁移和验证计划 |
| 一句话游戏创意 | `$game-concept-architect` | concept seed、玩家动词、动作-目标对齐、玩家承诺、核心循环、scope gate、验证计划 |
| 概念案、证据、验证计划或生产约束 | `$game-design-proposal-writer` | 可评审的商业策划案、独游设计案、发行 pitch、一页决策 memo 或 vertical slice 文档 |
| 一段 prompt、workflow、schema、agent 规则或项目流程 | `$paranoia-ai-system-evolver` | Intent Work Order、workflow governance review，以及带 WOOP/VOI/OODA/eval/Human Gate/rollback 的系统演化提案 |
| 英文游戏设计章节或长文 | `$game-design-book-translator` | 专业、自然、可复查的中文设计翻译 |
| 一批文章、视频、作者或网站 | `$game-design-source-curator` | 可长期维护的游戏设计知识库条目 |
| 留存、节奏、反馈、具身感、氛围感或认知负荷问题 | `$game-experience-density-optimizer` | ED 诊断、一周 A/B 变体、埋点字典、看板字段和回滚门 |

### 3. 复制一句最小提示词

在支持 skill 的 agent 环境里，直接点名对应 skill：

```text
Use $game-experience-analyzer to analyze this gameplay recording into timestamped evidence, design lenses, heat potential, foresight windows, Go/No-Go, and validation recommendations.
```

```text
Use $game-experience-analyzer to dissect this game into player verbs, action-goal alignment, uncertainty sources, system dynamics, content flow, audience desire, transfer boundaries, and validation recommendations.
```

```text
Use $paranoia-ai-system-evolver to upgrade this prompt/workflow/schema/work order into an Intent Work Order with WOOP, VOI, OODA, evals, Human Gate, rollback, and retrospective candidate learning.
```

```text
Use $game-design-book-translator to translate and polish this game design chapter into professional Chinese, including terminology and figure captions.
```

```text
Use $game-design-source-curator to review these game design sources and turn accepted items into a maintainable local knowledge base.
```

```text
Use $game-concept-architect to turn this one-line game idea into a concept seed, player verbs, action-goal alignment, player promise, core loop, scope gate, production feasibility check, and prototype validation plan.
```

```text
Use $game-design-proposal-writer to assemble this research, concept brief, evidence index, validation plan, and team constraints into a publisher pitch outline with proof of play, scope gate, budget assumptions, risks, and decision request.
```

```text
Use $game-experience-density-optimizer to turn this first-session experience density problem into CLP/SF/EB/AR/MD-min diagnosis, rollbackable weekly variants, telemetry events, dashboard fields, and pre-registered decision rules.
```

### 4. 安装 Skill 到自己的 agent 环境

如果你的工具支持本地 skill / Markdown skill package，把对应目录复制或同步到它的 skill 目录即可。常见宿主可以是 Codex、Claude Code、OpenCode，或其他能读取 Markdown skill 的 agent 环境：

```text
game-experience-analyzer/
paranoia-ai-system-evolver/
game-design-book-translator/
game-design-source-curator/
game-concept-architect/
game-experience-density-optimizer/
game-design-proposal-writer/
```

安装后确认两件事：`SKILL.md` frontmatter 的 `name` 和目录名一致；`references/`、`templates/`、`examples/` 里的相对路径还能打开。

## 图文展示

7 个有边界的入口覆盖 GameDesignOS 的主要工作路径：概念架构、证据与诊断、策划案组装、体验浓度迭代、工作流治理、设计文本翻译和资料策展。

<table>
  <tr>
    <td width="25%">
      <a href="./game-concept-architect/"><img src="./assets/showcase-game-concept-architect.png" alt="Game Concept Architect 展示图"></a>
    </td>
    <td width="25%">
      <a href="./game-experience-analyzer/"><img src="./assets/showcase-game-experience-analyzer.png" alt="Game Experience Analyzer 展示图"></a>
    </td>
    <td width="25%">
      <a href="./game-design-proposal-writer/"><img src="./assets/showcase-game-design-proposal-writer.png" alt="Game Design Proposal Writer 展示图"></a>
    </td>
    <td width="25%">
      <a href="./game-experience-density-optimizer/"><img src="./assets/showcase-game-experience-density-optimizer.png" alt="Game Experience Density Optimizer 展示图"></a>
    </td>
  </tr>
  <tr>
    <td><a href="./game-concept-architect/"><b>架构游戏概念</b></a><br>把一句话创意拆成 seed、玩家动词、动作-目标、玩家承诺、核心循环、scope gate 和验证计划。</td>
    <td><a href="./game-experience-analyzer/"><b>分析游戏体验</b></a><br>把截图、录屏、宣传片和视频链接，转成证据优先的体验诊断、游戏拆解和机制迁移判断。</td>
    <td><a href="./game-design-proposal-writer/"><b>撰写策划案</b></a><br>把调研、概念契约、证据、验证计划和生产约束，整理成可评审的 proposal、pitch 或 vertical slice 文档。</td>
    <td><a href="./game-experience-density-optimizer/"><b>优化体验浓度</b></a><br>把留存、节奏、反馈、具身感、氛围感和认知负荷问题，转成一周可验证的 ED 实验。</td>
  </tr>
</table>

<table>
  <tr>
    <td width="33%">
      <a href="./paranoia-ai-system-evolver/"><img src="./assets/showcase-voi-ooda.png" alt="Paranoia AI System Evolver 展示图"></a>
    </td>
    <td width="33%">
      <a href="./game-design-book-translator/"><img src="./assets/showcase-book-translator.png" alt="Game Design Book Translator 展示图"></a>
    </td>
    <td width="33%">
      <a href="./game-design-source-curator/"><img src="./assets/showcase-source-curator.png" alt="Game Design Source Curator 展示图"></a>
    </td>
  </tr>
  <tr>
    <td><a href="./paranoia-ai-system-evolver/"><b>演化工作流</b></a><br>用 WOOP、VOI、OODA、eval、Human Gate 和 rollback 升级 prompt、schema、memory 和 tool routing。</td>
    <td><a href="./game-design-book-translator/"><b>翻译设计知识</b></a><br>把严肃的游戏设计书籍和章节，变成自然、专业、可复查的中文设计写作。</td>
    <td><a href="./game-design-source-curator/"><b>策展资料</b></a><br>把散落在文章、视频、作者、专栏和网站里的内容，变成可长期维护的游戏设计知识库。</td>
  </tr>
</table>

更小的 proof-path 列表见 [showcase index](./docs/showcases/README.md)。

## System Architecture

`GameDesignOS` 由四层产品结构与贯穿全局的治理面组成；当前 v1.3 candidate 在 Intent Work Order、VOI 与 RJR-AI 之间加入可选 UL 控制层，但不迁移 v1 workspace schema：

- **Skill Kernel**
  - [`game-concept-architect/`](./game-concept-architect/)：一句话创意 -> 可验证概念蓝图。
  - [`game-experience-analyzer/`](./game-experience-analyzer/)：媒体/样本 -> 证据化诊断。
  - [`game-experience-density-optimizer/`](./game-experience-density-optimizer/)：明确体验问题 -> 一周实验。
  - [`game-design-proposal-writer/`](./game-design-proposal-writer/)：概念/证据/约束 -> 可决策策划案。
  - [`paranoia-ai-system-evolver/`](./paranoia-ai-system-evolver/)：workflow/schema/eval 改动 -> 受控演化。
  - [`game-design-book-translator/`](./game-design-book-translator/)：设计文本 -> 专业中文设计写作。
  - [`game-design-source-curator/`](./game-design-source-curator/)：散落资料 -> 长期知识资产。
- **Contract Layer**
  - [`contracts/`](./contracts/)：路由、skill 交接、`ul-state.schema.json`、项目 manifest、资产索引与决策日志。
- **Project Workspace**
  - [`runtime/workspace-template-v1/`](./runtime/workspace-template-v1/)：项目身份、生命周期目录、资产 registry、学习记录、导出物与 Human Gate。
- **Runtime Interface**
  - [`gamedesignos/`](./gamedesignos/)、[`runtime/`](./runtime/) 与 [`adapters/`](./adapters/)：本地 CLI 命令、workspace 生命周期、宿主接入和命令契约。
- **Governance**
  - 证据边界、公开/私有隔离、VOI、可选 UL、RJR-AI、eval、Human Gate 与 rollback 贯穿每一层。

私有项目数据、客户材料、凭据与工作室本地规则应留在公开仓库外。用户也仍然可以不使用 workspace，直接调用任一 skill。

## 当前 Skill

| Skill | 一句话用途 | 适合场景 | 包目录 |
| --- | --- | --- | --- |
| **Game Experience Analyzer** | 把截图、录屏、PV/宣传片和视频链接拆成证据优先的中文游戏设计报告。 | 体验分析、玩法机制、游戏拆解、机制迁移、整体项目、MDA、系统叙事、单机流程、热度预测、前瞻窗口、商业化、UX。 | [`game-experience-analyzer/`](./game-experience-analyzer/) |
| **Paranoia AI System Evolver** | 把 AI 工作单、prompt、workflow、memory、schema、tool routing、eval 和 RJR-AI 授权边界改动变成受控系统演化。 | Intent Work Order、WOOP、VOI、UL、OODA、剩余判断权、失败归因、迁移验证、Human Gate、rollback。 | [`paranoia-ai-system-evolver/`](./paranoia-ai-system-evolver/) |
| **Game Design Book Translator** | 把英文游戏设计/研发材料翻译成真正像中文设计写作的专业文本。 | 术语、章节、图注、表格、QA、来源边界检查。 | [`game-design-book-translator/`](./game-design-book-translator/) |
| **Game Design Source Curator** | 把散落资料变成可长期维护的游戏设计知识库。 | 来源筛选、评分、HTML 归档、registry、update history、设计实验卡。 | [`game-design-source-curator/`](./game-design-source-curator/) |
| **Game Concept Architect** | 把一句话游戏创意扩展为可验证的概念设计案，包含 seed extraction、玩家动词、动作-目标对齐、玩家承诺、核心循环、scope gate 和原型验证计划。 | 独游创意、立项 pitch、外部可行性、平台/商业适配、MVP/Vertical Slice 规划、生产约束。 | [`game-concept-architect/`](./game-concept-architect/) |
| **Game Experience Density Optimizer** | 把体验浓度、留存、节奏、反馈、具身感、氛围感和认知负荷问题转成一周 ED 实验。 | 首局调优、原型手感、LiveOps 小实验、A/B 变体、埋点字典、看板规格、回滚门。 | [`game-experience-density-optimizer/`](./game-experience-density-optimizer/) |
| **Game Design Proposal Writer** | 把调研、概念契约、证据、验证计划、生产约束和商业目标整理成可决策的游戏策划案。 | 商业游戏策划案、独游设计案、发行/投资 pitch、一页决策 memo、Demo/Vertical Slice 规划。 | [`game-design-proposal-writer/`](./game-design-proposal-writer/) |

## 典型用例

- **竞品体验复盘:** 给一段录屏，输出时间轴、功能账本、玩法循环、问题优先级和修改建议。
- **游戏拆解与机制迁移:** 按玩家动词、目标层级、不确定性、系统动态、内容流、受众动机和可玩主题，判断哪些结构可迁移、哪些表层不能照搬。
- **PV 热度预测:** 给宣传片链接，判断首秒钩子、卖点复述、可玩性证明、平台适配、转化承接和验证计划。
- **前瞻机会判断:** 判断题材/玩法是否还有窗口；休闲轻度默认 1-3 个月，微小中重度默认 3-6 个月。
- **资料策展:** 把文章、视频、作者、专栏和网站沉淀成可检索、可引用、可实验的知识库。
- **专业翻译:** 把游戏设计书籍或长文翻成自然中文，同时保留术语、论证结构和图表语境。
- **工作流升级:** 把一次有用的 agent 行为升级成候选规则，并用 eval、Human Gate 和 rollback 控制风险。
- **跨 skill 交接:** 用共享 contract 从概念承诺走到媒体诊断，再走到 ED 实验，而不是每一步都重新解释上下文。
- **创意可行性:** 把一句话创意拆成 concept seed、玩家动词、动作-目标对齐、玩家承诺、核心循环、scope gate、生产可行性和原型验证计划。
- **策划案成案:** 把已验证概念、资料、证据、风险和生产约束整理成可评审的商业策划案、独游设计案、pitch outline 或 vertical slice 文档。
- **体验浓度实验:** 把首局、节奏、反馈、具身感、氛围感或认知负荷问题，转成带指标和回滚门的一周 ED 实验。

## 项目结构

可以把这个仓库理解成 GameDesignOS 的公开基础层，而不是普通素材目录。

| 层级 | 路径 | 作用 |
| --- | --- | --- |
| Skill Kernel | `game-experience-analyzer/`, `game-concept-architect/`, `game-design-proposal-writer/`, `paranoia-ai-system-evolver/`, `game-design-book-translator/`, `game-design-source-curator/`, `game-experience-density-optimizer/` | 可独立安装的专家能力包。 |
| Contract Layer | `contracts/` | skill 交接、路由、项目 manifest、资产索引和决策日志 schema。 |
| Runtime / CLI | `gamedesignos/`, `runtime/` | 可执行本地命令、workspace 模板、生命周期规则和 CLI 命令契约。 |
| Product 与 workflows | `docs/product/`, `docs/workflows/` | 产品边界、架构、路线图和端到端项目路径。 |
| 公开 onboarding 与 proof | `README*`, `docs/`, `releases/` | 上手、版本历史、公开安全案例和 proof path。 |
| Adapters 与 validation | `adapters/`, `.github/`, `scripts/` | 宿主接入、CI、仓库校验与行为 eval。 |
| Governance 与 media | `CONTRIBUTING.md`, `LICENSE`, `assets/` | 贡献边界、授权和公开视觉素材。 |

每个 skill 通常使用同一套结构：

```text
SKILL.md      -> agent 入口、触发条件、核心流程、边界
references/  -> 方法、评分规则、路由、质量门、验证 playbook
templates/   -> 可复制到真实任务中的表单和输出结构
examples/    -> 可复查的示例输出
agents/      -> 支持对应元数据的 agent 环境可读取
evals/       -> 用于回归检查的提示和预期行为
```

## 安装与使用

GameDesignOS 支持两种兼容模式。

### Project Workspace 模式

不安装时，在仓库根目录可以直接用 `python -m gamedesignos "<一句话需求>"`。如果想安装成本地命令，再执行：

```bash
python -m pip install -e .
gamedesignos "我想做一款修灯塔的策略游戏"
```

### 直接使用 Skill

1. 将某个 skill 目录复制或同步到 agent skill 目录。
2. 确认 `SKILL.md` frontmatter 的 `name` 与目录名一致。
3. 用 `$skill-name` 或自然语言触发。
4. 按 README 或 `SKILL.md` 检查 JSON/YAML、引用路径和示例。

使用 workspace 不会破坏原有 skill 的独立调用方式。

## 验证

在仓库根目录运行：

```text
python scripts/validate_repo.py
python scripts/validate_skill.py game-experience-analyzer
python scripts/validate_skill.py game-concept-architect
python scripts/validate_skill.py game-experience-density-optimizer
python scripts/validate_skill.py game-design-proposal-writer
python -m unittest discover -s scripts/tests
gamedesignos --version
gamedesignos doctor
```

## 路线图

- **v0.8.0 — Runtime Foundation：** workspace 模板、workspace contract、产品架构、工作流和校验。
- **v0.9.0 — Local Runtime Prototype：** 初始化、查看、路由、创建、校验和打包本地 workspace。
- **v1.0.0 — Project-Ready GameDesignOS：** 带 tag 的稳定基线，包含 Decision/Assumption/Evidence/Experiment/Gate/Workflow/Learning 主链路、决策图、健康扫描、Human Gate 与 v1 workspace。
- **v1.1.0 — RJR-AI Authority Layer：** 剩余判断权边界、GitHub 定位、版本同步，以及 AI/workflow/eval/权限/记忆系统的 workflow-evolution 覆盖。
- **v1.2.0 — Intent Work Order & Workflow Governance：** AI 工作单、workflow-run 治理引用、Paranoia checkpoint、release tag 补齐，以及 runtime/package 版本同步。
- **v1.3.0.dev0 candidate — Portable Runtime & UL：** wheel 自包含资源、唯一 router 真源、`ul_state` schema、UL-L0～UL-L5、可选 workflow 引用与迁移门；尚未打 tag 或公开发布。
- **v1.x — Proof and adoption：** 补更多公开案例、强化 adapter、推进 runtime dashboard，并沉淀真实项目 playbook。

完整路线见按能力门推进的 [产品 Roadmap](./docs/product/roadmap.md)。

## 支持项目

如果 GameDesignOS 对你有帮助，可以为[仓库点亮 Star](https://github.com/DY-2026/GameDesignOS)，或提交一个具体的工作流、proof case、adapter 需求。Star 和可执行反馈会帮助我们安排下一批公开案例与可迁移性改进。

## License

本仓库的 skill documents and tooling 使用 [MIT License](./LICENSE) 发布。

Paranoia 名称、logo、视觉识别和项目品牌不作为商标授权。examples 可能有各自的 `source_status`、`case_type` 或来源元数据，复用前请检查对应文件 frontmatter。

## Skill 包约定

每个 skill 都是一个可独立安装的包：`SKILL.md` 放运行入口，`references/` 放方法说明，`templates/` 放可复用表单，`examples/` 和 `evals/` 用于展示与回归检查。

## 贡献

提交公开 examples、evals、assets、showcases 或 release notes 前，请确保材料为 synthetic、公开材料或明确 cleared material。具体规则见 [CONTRIBUTING.md](./CONTRIBUTING.md)。

## 设计原则

```text
Evidence before opinion.
Feasibility before scope.
Workflow before one-off prompts.
VOI before research.
Eval before promotion.
Rollback before confidence.
```

## 未来 Skill

未来根据社区反馈和 skill 成熟度，可能继续加入 AI + 独游实战全流程方向的包，例如：

- `indie-game-production-master`：覆盖独游从想法验证、GDD/Gate、原型、playtest、AI 资产流水线、Steam/发布策略到复盘沉淀的全流程制作 skill。
- `godot-ai-game-production`：覆盖 Godot + AI 项目搭建、设计真源、数据契约、资源流水线、headless/keyshot 验证、Demo/Release Gate 和工程复盘的生产 skill。
