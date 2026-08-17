# 10 分钟上手 GameDesignOS

这份指南给第一次使用的人。目标不是把所有命令都学完，而是先把一个真实项目的第一轮验证链路跑起来。

## 0. 先看完整 synthetic 链路

```bash
python -m pip install -e .
python -m gamedesignos demo
```

这条命令不调用模型、不需要密钥。它会在系统临时目录生成一份全新的公开 synthetic 工作区，展示 Decision、Assumption、Evidence、已复盘 Experiment、rollback 和下一步，并在 `decision accept` 的 Human Gate 前停住。终端会打印实际路径；需要固定位置时使用 `--destination <空目录>`。

## 1. 直接说一句

拉取项目后，在仓库根目录直接执行：

```bash
python -m gamedesignos "我想做一款修灯塔的策略游戏"
```

它会自动推荐 skill，但默认只做路由和状态审计，不会创建或修改 workspace。要开始长期项目，请显式提供 `--destination` / `--workspace`，或使用下一节的 `start` 命令。

如果想安装成 `gamedesignos` 命令：

```bash
python -m pip install -e .
gamedesignos "我想做一款修灯塔的策略游戏"
```

## 2. 一条命令创建项目

如果你已经知道要创建长期项目，把真实项目 workspace 放到公开仓库外：

```bash
python -m gamedesignos start "My Game" --destination ../my-game-designos --owner your-name
```

`start` 会自动准备：

- v1 Project-Ready workspace；
- 第一条 Decision Object；
- 第一条关键 Assumption；
- 第一份三分钟验证 Experiment Plan；
- 一次 VOI Gate；
- 一个 `idea-to-validation` Workflow Run。

它会在终端输出“下一步只做一件事”。默认就是：做一次 3-5 人/自测的三分钟验证，然后用输出里的 `gamedesignos evidence add ...` 记录观察。

同一个目录再次运行 `start` 时，会复用已有记录，不会重复创建一套新对象。

## 3. 记录第一条观察

完成小测试后，把终端里打印的命令复制执行即可。形态大致是：

```bash
gamedesignos evidence add --workspace "../my-game-designos" --decision DEC-ID --summary "三分钟验证：写下最关键的观察" --source-type playtest --source-status private --confidence medium --decision-impact "决定下一轮默认动作是否调整"
```

先不要急着写长文档。第一条证据只要说清楚：

- 你观察到了什么；
- 来源是自测、访谈、录屏、截图还是数据；
- 它会不会改变下一轮默认动作；
- 它不能证明什么。

## 4. 查看项目状态

```bash
gamedesignos health --workspace ../my-game-designos
gamedesignos workflow next WRUN-ID --workspace ../my-game-designos
```

`health` 看风险，`workflow next` 看当前工作流卡在哪一步。承诺态决策仍然必须由人显式执行，runtime 不会替你接受项目承诺。

## 5. 直接调用 Skill

一次性任务可以不建 workspace，直接点名 skill：

```text
Use $game-experience-analyzer to analyze this gameplay recording into timestamped evidence, sample boundary, diagnosis route, issue cards, and validation recommendations.
```

```text
Use $game-concept-architect to turn this one-line game idea into concept seed extraction, player promise contract, core loop, scope gate, and prototype validation plan.
```

```text
Use $game-experience-density-optimizer to turn this first-session pacing problem into ED diagnosis, weekly variants, instrumentation, decision rules, and rollback gates.
```

## 6. 该选哪个 Skill

| 你手里的材料 | 推荐 Skill | 主要产物 |
| --- | --- | --- |
| 截图、录屏、PV、视频链接 | `$game-experience-analyzer` | 证据边界、体验诊断、问题卡、验证建议 |
| 一句话游戏创意 | `$game-concept-architect` | concept seed、玩家承诺、核心循环、验证计划 |
| 概念、证据、验证和生产约束 | `$game-design-proposal-writer` | 策划案、pitch、决策 memo、vertical slice 文档 |
| prompt、workflow、schema、agent 规则 | `$paranoia-ai-system-evolver` | WOOP/VOI/OODA、eval、Human Gate、rollback |
| 留存、节奏、反馈、具身感、氛围或认知负荷 | `$game-experience-density-optimizer` | ED 诊断、一周实验、埋点字段、回滚门 |
| 英文游戏设计章节或长文 | `$game-design-book-translator` | 专业中文设计翻译 |
| 文章、视频、作者、栏目或网站 | `$game-design-source-curator` | 可追踪、可维护的知识资产 |

## 7. 不越界检查

信任或发布任何输出前，至少检查：

- 强判断是否有证据、时间戳、截图、来源或明确假设；
- 是否写清样本不能证明什么；
- 是否避免在没有数据时声称真实留存、收入、转化、玩家情绪或市场表现；
- private、synthetic、public、cleared、needs_review 是否标对；
- 是否泄露本地路径、客户名、未公开计划、预算或私有素材；
- 是否给出下一步验证，而不是把诊断当成最终结论。

## 8. 校验仓库

在仓库根目录执行：

```bash
python scripts/validate_repo.py
python -m unittest discover -s scripts/tests
```

真实项目资料请留在你自己的私有环境里，不要提交到公开仓库。
