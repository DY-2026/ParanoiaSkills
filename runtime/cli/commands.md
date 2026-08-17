# 本地 CLI 命令参考

所有命令只操作本地文件。会写入文件的命令在适合时支持 `--dry-run`。CLI 不调用模型、不上传文件、不替人越过 Human Gate。

## 零配置演示

```bash
gamedesignos demo [--destination EMPTY_PATH] [--json]
```

`demo` 创建一份全新的 `public-synthetic` Golden Lighthouse workspace，自动登记 synthetic Evidence、记录并复盘 Experiment、把 Assumption 标记为 `tested`，然后在 Commitment Human Gate 前停住。它的模型调用数为 0，不需要 API key，也不会替用户接受 Decision。未提供路径时使用系统临时目录；目标目录非空时拒绝覆盖。

## 自然语言入口

```bash
python -m gamedesignos "<一句话需求>"
gamedesignos ask <一句话需求> [--destination PATH] [--owner NAME] [--json]
```

`ask` 是最低门槛入口。它会先推荐应该使用的 skill，并给出可复制的 `Use $skill-name ...` 提示词，但置信度不构成写盘授权。提供 `--destination` 或 `--workspace` 才会创建或恢复指定工作区；长期项目也可以明确使用 `start`。

示例：

```bash
python -m gamedesignos "我想做一款修灯塔的策略游戏"
```

## 一键项目入口

```bash
gamedesignos start <project-name> [--destination PATH] [--owner NAME] [--option ACTION] [--default-action ACTION] [--json]
```

`start` 是明确创建长期项目时的入口。它会创建或打开一个 v1 Project-Ready workspace，并自动准备第一条 Decision Object、第一条关键 Assumption、第一份三分钟验证 Experiment Plan、一次 VOI Gate 和一个 `idea-to-validation` Workflow Run。

再次运行同一个目录时，`start` 会复用已有记录，不会重复创建一套新对象。终端输出里只需要看“下一步只做一件事”和“记录时用”的命令。

示例：

```bash
gamedesignos start "My Game" --destination ../my-game-designos --owner your-name
```

## 初始化

```bash
gamedesignos init <project-name> [--destination PATH] [--codename SLUG] [--visibility private|public-synthetic|public-cleared] [--owner NAME] [--workspace-version 1.0.0|0.8.0] [--dry-run]
```

`init` 只负责手动创建空 workspace。默认创建 v1.0 Project-Ready workspace：

```text
00-inbox/
01-decisions/
02-assumptions/
03-evidence/
04-experiments/
05-design-assets/
06-workflows/
07-learning/
08-exports/
.gamedesignos/
```

如需兼容旧项目模板，可显式传入 `--workspace-version 0.8.0`。`--force` 不会覆盖已有 GameDesignOS workspace。

## 状态

```bash
gamedesignos status [--workspace PATH] [--json]
```

读取项目身份、schema/runtime 兼容性、资产数量、已接受决策、未关闭 Human Gate、当前默认动作和缺失目录。

## VOI

```bash
gamedesignos voi DEC-ID --decision QUESTION --default-action ACTION --option ACTION --option ACTION --owner NAME [--boundary undefined|far|near|locked] [--candidate-info ACTION] [--stop-when RULE] [--workspace PATH]
```

创建定性的 Information Value Assessment。每轮最多接受三个候选信息动作。复查已编辑的评估：

```bash
gamedesignos voi --input 01-decisions/information-value-assessment.json --write --workspace PATH
```

复查器会检查选项一致性、不确定性引用、信号到行动映射、停止规则，以及候选信息是否真的可能改变行动。它不会发明概率或货币化 EV。

## 路由

```bash
gamedesignos route <task text> [--workspace PATH] [--json]
```

推荐最小可用 skill，指出缺失的上游资产，并保留最终目标 skill。它只推荐路线，不执行 skill。

## v1 Decision

```bash
gamedesignos decision new --title TITLE --question QUESTION --option A --option B --default-action A [--owner NAME] [--boundary near] [--stakes high] [--reversibility costly_to_reverse] [--rollback-trigger RULE] [--workspace PATH]
gamedesignos decision list [--workspace PATH] [--json]
gamedesignos decision inspect DEC-ID [--workspace PATH] [--json]
gamedesignos decision accept DEC-ID --by OWNER --reason REASON [--workspace PATH]
gamedesignos decision reject DEC-ID --by OWNER --reason REASON [--workspace PATH]
gamedesignos decision supersede DEC-ID --superseded-by DEC-ID --by OWNER --reason REASON [--workspace PATH]
```

`decision accept` 必须显式提供 `--by` 和 `--reason`，并先通过 commitment gate。AI 可以组织证据和门禁结果，但不能替人接受承诺。

## v1 Assumption

```bash
gamedesignos assumption new --decision DEC-ID --statement TEXT [--type player_understanding] [--risk high] [--confidence low] [--test-method TEXT] [--kill-condition TEXT] [--workspace PATH]
gamedesignos assumption list [--workspace PATH] [--json]
gamedesignos assumption validate ASM-ID --status tested|validated|invalidated|waived --reason TEXT [--workspace PATH]
```

Assumption 用来防止把设计假设写成结论。高风险假设未测试时，commitment gate 会阻断接受决策。

## v1 Evidence

```bash
gamedesignos evidence add --decision DEC-ID --summary TEXT [--source-type playtest] [--source-status private|synthetic|public|cleared|needs_review] [--confidence medium] [--decision-impact TEXT] [--unsupported-claim TEXT] [--workspace PATH]
gamedesignos evidence list [--workspace PATH] [--json]
gamedesignos evidence inspect EVD-ID [--workspace PATH] [--json]
```

Evidence 不是普通资料，而是对某个判断有影响的证据。每条证据都应该写出不能证明什么。

## v1 Experiment

```bash
gamedesignos experiment plan --decision DEC-ID --assumption ASM-ID --title TITLE --hypothesis TEXT --method TEXT --success TEXT --failure TEXT [--sample-size N] [--workspace PATH]
gamedesignos experiment result EXP-ID --status passed|failed|mixed|inconclusive --observation TEXT [--evidence EVD-ID] [--decision-delta TEXT] [--workspace PATH]
gamedesignos experiment review EXP-ID --by OWNER --summary TEXT [--workspace PATH]
```

Experiment 必须绑定 decision 或 assumption，并写清成功/失败标准。未复盘的实验不能支撑承诺态决策。

## v1 Gate

```bash
gamedesignos gate run voi DEC-ID [--workspace PATH] [--write] [--json]
gamedesignos gate run evidence DEC-ID [--workspace PATH] [--write] [--json]
gamedesignos gate run scope DEC-ID [--workspace PATH] [--write] [--json]
gamedesignos gate run experiment EXP-ID [--workspace PATH] [--write] [--json]
gamedesignos gate run commitment DEC-ID [--workspace PATH] [--write] [--json]
gamedesignos gate run rollback DEC-ID [--workspace PATH] [--write] [--json]
```

Gate 结果可能是 `pass`、`warn`、`block` 或 `ask_human`。阻断会返回校验类退出码。`--write` 会把结果保存到 `.gamedesignos/gate-results/`。

## v1 Workflow

```bash
gamedesignos workflow list [--json]
gamedesignos workflow start idea-to-validation [--workspace PATH] [--json]
gamedesignos workflow status WRUN-ID [--workspace PATH] [--json]
gamedesignos workflow next WRUN-ID [--workspace PATH] [--json]
gamedesignos workflow validate WRUN-ID [--workspace PATH] [--json]
```

当前内置 `idea-to-validation`。它不会自动生成所有产物，而是告诉你当前卡在哪一步、缺哪个资产、下一步最小动作是什么。

## v1 Health / Next

```bash
gamedesignos health [--workspace PATH] [--json]
gamedesignos next [--workspace PATH] [--json]
```

`health` 扫描高风险未测试假设、高影响无 rollback 决策、near-boundary 但缺 gate 的决策和无结果实验。`next` 返回最小下一步建议。

## v1 Graph

```bash
gamedesignos graph export [--workspace PATH] [--format mermaid] [--json]
gamedesignos graph inspect NODE-ID [--workspace PATH] [--json]
```

导出或检查本地决策图。初始图读取 Decision、Assumption、Evidence、Experiment 和 Learning。

## 旧版草稿资产

```bash
gamedesignos new <asset-type> [--title TITLE] [--filename NAME] [--workspace PATH] [--dry-run]
```

保留给 v0.9 兼容。v1 项目的主路径应优先使用 `decision`、`assumption`、`evidence`、`experiment` 和 `workflow` 命令。

## 校验

```bash
gamedesignos validate [--workspace PATH] [--repo-root PATH] [--json]
```

检查 manifest 兼容性、生命周期目录、资产 ID 与路径、依赖引用、决策记录、来源状态边界、JSON 语法和 canonical schemas。

## 打包

```bash
gamedesignos pack [--mode internal-review|publisher|public-synthetic] [--output FILE] [--workspace PATH] [--dry-run] [--force]
```

按来源状态过滤，生成可评审项目快照。`public-synthetic` 不会导出 private 或 needs_review 资产。

## Doctor

```bash
gamedesignos doctor [--workspace PATH] [--json]
```

检查 Python、依赖、仓库 contracts、workspace 兼容性和写入权限，不修改项目资产。
