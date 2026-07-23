# Runtime Foundation 与 Project-Ready 本地运行时

runtime 层定义项目 workspace、contracts、skills、adapters、本地命令和 Human Gate 如何协同工作。

## 当前状态

已可用能力：

- 可执行本地 `gamedesignos` CLI；
- v1.0 Project-Ready workspace 模板；
- v0.8/v0.9 legacy workspace 兼容；
- Decision、Assumption、Evidence、Experiment、Learning、GateResult、WorkflowRun 契约；
- 初始化、状态、路由、对象创建、门禁、工作流、图导出、校验、打包和诊断；
- 确定性 Project Health 与 Next Best Action；
- RJR-AI 剩余判断权边界：AI、Workflow、Eval、权限、知识库和 Human Gate 的职责分层。

从仓库根目录安装：

```bash
python -m pip install -e .
gamedesignos --version
```

最简单的上手方式是直接说一句：

```bash
python -m gamedesignos "我想做一款修灯塔的策略游戏"
```

它会自动推荐 skill。对项目型请求，还会创建 v1 workspace、第一条 Decision、第一条 Assumption、第一份三分钟验证 Experiment、VOI Gate 和 `idea-to-validation` 工作流。完成后只需要做一件事：跑一次 3-5 人/自测的三分钟验证，然后按输出里的 `gamedesignos evidence add ...` 记录观察。

需要精细控制时，再使用 Project-Ready 进阶命令：

```bash
gamedesignos decision new --workspace ../my-game-designos --title "Prototype Direction" --question "下一轮验证哪条玩法？" --option "战斗原型" --option "关系循环" --default-action "战斗原型" --rollback-trigger "两周后无法形成可读三分钟循环"
gamedesignos assumption new --workspace ../my-game-designos --decision DEC-ID --statement "玩家能在三分钟内理解核心循环"
gamedesignos gate run voi DEC-ID --workspace ../my-game-designos
gamedesignos experiment plan --workspace ../my-game-designos --decision DEC-ID --assumption ASM-ID --title "三分钟理解测试" --hypothesis "小样本能暴露理解风险" --method "纸面原型 + 5 人观察" --success "4/5 能解释胜负来源" --failure "多数玩家无法预判结果"
gamedesignos health --workspace ../my-game-designos
```

runtime 不调用模型或网络。API key、模型选择、披露预览和工具权限属于宿主 agent 或 harness。

## 兼容性

当前 `main` 的 runtime 实现版本是 `1.3.0.dev0`，属于 P0 candidate；最新带 tag 的稳定源码版本是 `1.2.0`，对应 [GitHub Release](https://github.com/DY-2026/GameDesignOS/releases/tag/v1.2.0) 已公开并标记为 Latest。

当前候选新增可选 UL（Uncertainty Ladder）契约：workflow 可以通过 `governance.ul_state_ref` 引用 `UL-L0`～`UL-L5` 状态；`UL-*.json` 放在 `.gamedesignos/workflow-runs/` 时会被 `ul-state.schema.json` 校验。普通领域 workflow 不需要创建该文件。

- 新建 workspace 默认使用 schema `1.0.0`。
- 旧 workspace schema `0.8.0` 仍支持。
- 如需创建旧模板，可使用 `gamedesignos init ... --workspace-version 0.8.0`。

v1.0 模板位于 [`workspace-template-v1/`](./workspace-template-v1/)。旧模板仍保留在 [`workspace-template/`](./workspace-template/)。

说明：`schema_version` 仍为 `1.0.0`，因为 UL state 和 governance 引用都是可选、向后兼容的控制面，不要求迁移 workspace 结构，也不扩大 runtime 权限。

## Runtime 生命周期

```text
创建或打开 workspace
  -> 读取 manifest、资产索引和决策
  -> 创建 Decision Object 与默认行动
  -> 登记关键 Assumption
  -> 在广泛获取信息前运行 VOI Gate
  -> 创建最小 Experiment
  -> 登记 Evidence 与 unsupported claims
  -> 复盘 Experiment Result
  -> Human Gate 接受、拒绝或 supersede 决策
  -> 生成 Graph、Health、Next 和 Pack
```

## 非目标

v1.2 runtime 不提供托管服务、模型网关、API-key 管理器、自动 skill 执行、自治搜索、GUI dashboard、云同步、账号权限或游戏引擎生产 adapter。

这些方向要等 Project-Ready 的决策链、证据链、实验链和 Human Gate 经真实项目验证后再进入候选队列。

## 入口文档

- [CLI 命令参考](./cli/commands.md)
- [v1 workspace 模板](./workspace-template-v1/)
- [v0.9 legacy workspace 模板](./workspace-template/)
- [v1.0 开发计划](../docs/product/v1.0-development-plan.md)
- [v1.2 release note](../releases/v1.2.0.md)
