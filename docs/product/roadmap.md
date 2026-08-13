# GameDesignOS Roadmap

路线图按能力门推进，不承诺空泛日期。一个阶段只有在上一层有可评审案例、稳定契约和回归覆盖后，才进入下一阶段。

## v0.8.0 — Runtime Foundation

主题：从 skill 包走向项目 workspace。

交付：

- 产品愿景与系统架构；
- workspace template 和 manifest；
- decision-information 与 workspace-level contracts；
- decision-to-information 路线和四条核心生产 workflow；
- workspace-aware adapters；
- planned CLI surface；
- validation 和 release integration。

退出门：

- 一个 synthetic project 能被 coherent 地表示成 workspace assets；
- 现有 skills 保持向后兼容；
- repository validation 通过。

## v0.9.0 — Local Runtime Prototype

已交付命令：

```text
gamedesignos init <project>
gamedesignos status
gamedesignos voi <decision-id>
gamedesignos route <task>
gamedesignos new <asset-type>
gamedesignos validate
gamedesignos pack
gamedesignos doctor
```

已交付行为：

- 从模板初始化 workspace；
- 检查 manifest、asset index、accepted decisions 和 current default actions；
- 排序候选信息动作并执行 research stop rule；
- 推荐最小合适 skill；
- 创建 contract-shaped artifact stubs；
- 校验 workspace 结构和引用；
- 生成可评审 pack。

## v1.0.0 — Project-Ready GameDesignOS

详细计划：[v1.0-development-plan.md](./v1.0-development-plan.md)。

v1.0 的目标不是更多命令，而是让真实游戏项目可以连续使用 GameDesignOS 管理完整周期：

```text
想法 -> 假设 -> 证据 -> 实验 -> 决策 -> 复盘 -> 下一轮演化
```

已交付能力：

- v1 workspace structure，默认决策优先目录；
- core models：Decision、Assumption、Evidence、Experiment、Learning、GateResult；
- v1 CLI 分组：`decision`、`assumption`、`evidence`、`experiment`、`workflow`；
- Decision Graph inspect 与 Mermaid export；
- VOI、Evidence、Scope、Experiment、Commitment、Rollback gates；
- Project Health Scan 和 Next Best Action；
- `gamedesignos ask` / `gamedesignos "<一句话>"` 自然语言入口；
- `gamedesignos start` 一键项目入口；
- v0.8/v0.9 workspace 兼容；
- public/private source-status pack 边界。

v1.0 主命令：

```text
gamedesignos ask
gamedesignos "<一句话>"
gamedesignos start
gamedesignos decision new/list/inspect/accept/reject/supersede
gamedesignos assumption new/list/validate
gamedesignos evidence add/list/inspect
gamedesignos experiment plan/result/review
gamedesignos gate run
gamedesignos workflow list/start/status/next/validate
gamedesignos health
gamedesignos next
gamedesignos graph export/inspect
```

退出门：

- 一个真实私有项目可以跨多轮迭代使用 GameDesignOS，而不需要重建上下文；
- accepted decisions、superseded assets、evidence boundaries 和 rollback history 可追踪；
- public/private material boundaries 可操作；
- 行为测试覆盖无 Decision 阻止 research、高影响无 rollback 阻断承诺、未复盘 experiment 不可支撑接受决策、public-synthetic 不导出 private evidence。

## v1.1.0 — RJR-AI Authority Layer

v1.1.0 不迁移 workspace schema，而是把系统定位和工作流演化能力补齐到“剩余判断权”这一层：

- AI 负责扩大可能性；
- Workflow 负责压缩混乱；
- Eval 负责提供反馈；
- 权限系统负责防止越界；
- 知识库负责积累组织记忆；
- 高耦合、低可逆、证据不足、必须下注的问题由人亲自拍板。

已交付范围：

- `paranoia-ai-system-evolver` 吸收 RJR-AI 方法，作为 prompt、workflow、memory、schema、tool-routing、eval 和授权边界升级的入口；
- router、contract、eval 和 validator 增加 RJR-AI 场景覆盖；
- GitHub About 描述、README trio、runtime 文档、package metadata、release note 与 version surface 同步到 `1.1.0`；
- v1 workspace schema 保持 `1.0.0`，不强制迁移既有项目。

## v1.2.0 — Intent Work Order & Workflow Governance

v1.2.0 把意图、授权边界和流程漂移记录带入工作流运行，而不让 `paranoia-ai-system-evolver` 变成接管领域产出的 mega-agent。

已交付范围：

- `intent-work-order.schema.json` 与中文优先的意图工作单 playbook/template；
- `workflow-run.governance`，保存 Decision/VOI、RJR、Human Gate、rollback 与 candidate learning 引用；
- 五条端到端工作流中的 Paranoia Checkpoint；
- 默认 `shadow` enforcement，先观察再决定是否升级为 `warn` 或 `enforce`；
- 面向整体流程、产出质量和工作流治理请求的路由与行为评测覆盖。

当前边界：

- workspace schema 继续保持 `1.0.0`；
- governance 不替代概念、体验诊断、ED 实验或策划案领域 Skill；
- 真实项目长期收益、路由负迁移和 enforcement 晋升仍需要更多证据。

## v1.3.0.dev0 Candidate — Portable Runtime & UL

当前开发候选把可安装 runtime 的自包含能力，与 UL（Uncertainty Ladder，不确定性阶梯）控制层放在同一条候选线上，但不冒充正式发布：

- wheel 自带 canonical contracts、router 和 workspace templates；
- `router.yaml` 保持唯一可编辑路由真源；
- `ul_state` 用 `UL-L0`～`UL-L5` 记录暴露变量、保持变量、支架、后果预算、失败归因、迁移和 fallback；
- `workflow-run.governance.ul_state_ref` 为可选引用，不强迫普通领域 workflow 增加表单；
- `ul-state.schema.json`、示例、回归案例和 validators 构成机器可校验的最小闭环；
- workspace schema 保持 `1.0.0`，无需迁移既有 v1 项目；
- 全局 skill 同步、正式版本、tag、release 与 `shadow -> warn/enforce` 晋升仍需 Human Gate 和真实迁移证据。

候选退出门：

- 至少两个结构不同的 AI 工程任务证明 UL 能改善失败归因或减少混杂修改；
- 至少一个 negative-transfer 用例证明 UL 不会劫持普通游戏学习曲线、体验诊断或领域实验；
- `ul_state` schema、workflow 引用、source checkout、wheel snapshot 和 installed-wheel smoke 全部一致；
- 新增描述成本没有超过其减少返工与错误归因的收益。

本地退出门证据见 [`v1.3-ul-exit-gate-evidence.md`](./v1.3-ul-exit-gate-evidence.md)；正式晋升仍等待跨平台 CI 与 Human Gate。

## Later Exploration

只有 v1.0 foundation 稳定后再探索：

- game-engine adapters；
- playtest / telemetry connectors；
- visual asset graph；
- multi-agent orchestration；
- team permissions 与 review roles；
- reusable studio overlays；
- optional local knowledge retrieval。

这些不是承诺，只是候选。只有当用户证据表明它们改善设计决策的收益大于系统复杂度时，才进入开发。

## 优先级规则

未来工作按这个公式排序：

```text
positive net VOI
x decision value
x frequency of use
x reuse across projects
x evidence quality
÷ implementation and governance cost
```

不要因为 agent 能生成新表面，就把它加入系统。
