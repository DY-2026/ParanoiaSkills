# DeepSeek Harness 对 GameDesignOS 的工程适配审计

- 审计日期：2026-08-15
- 上游对象：[`deepseek-ai/deepseek-harness`](https://github.com/deepseek-ai/deepseek-harness)
- 固定修订：[`47f943859bef60e4160492346772ded9b24f765a`](https://github.com/deepseek-ai/deepseek-harness/tree/47f943859bef60e4160492346772ded9b24f765a)
- 本地结论状态：`candidate`，不是依赖选型或长期规则晋升

## 结论

DeepSeek Harness 对 GameDesignOS 有明确帮助，但帮助来自少量执行安全模式，而不是整套技术栈。

建议吸收：

1. 在外部调用或工具副作用前落盘语义检查点；
2. 明确区分“尚未开始”与“已经越过执行边界、结果未知”；
3. 对未知结果禁止盲目自动重试；
4. 把运行状态、当前工作节点、授权和最终结果拆开观察；
5. 审批失败时默认拒绝，并且一次授权只覆盖一次精确操作。

明确不引入：Cordis 插件树、DeepSeek Harness 运行时依赖、Web UI、通用 Agent Loop、完整会话事件库、动态工作流脚本、Ralph 多轮代理和自动压缩。

因此，本轮改进不是“接入 DeepSeek Harness”，而是以原生 Python 重新实现一个更小的 OpenAI-compatible 参考宿主，并保持 GameDesignOS 的模型与凭证边界不变。

## 已确认事实

- 上游采用 MIT License，但 README 同时将项目标为 developer preview，并明确提示后续会出现 breaking changes。许可证允许复用不等于运行时依赖已经稳定。[README](https://github.com/deepseek-ai/deepseek-harness/blob/47f943859bef60e4160492346772ded9b24f765a/README.md) · [LICENSE](https://github.com/deepseek-ai/deepseek-harness/blob/47f943859bef60e4160492346772ded9b24f765a/LICENSE)
- 它以 Cordis 组合插件树，模型适配器、工具、session、agent loop、持久化、审批和 UI 都是可替换插件。[架构说明](https://github.com/deepseek-ai/deepseek-harness/blob/47f943859bef60e4160492346772ded9b24f765a/docs/architecture.zh.md)
- session 使用仅追加事件日志作为真源，并从日志投影模型历史；持久化、回放、fork 和崩溃修复都从该事件流派生。[Session README](https://github.com/deepseek-ai/deepseek-harness/blob/47f943859bef60e4160492346772ded9b24f765a/packages/core/session/README.md)
- 语义检查点策略会在模型请求分发前和顶层工具执行前持久化意图。崩溃恢复区分 `TOOL_NOT_STARTED` 与 `TOOL_OUTCOME_UNKNOWN`，后者要求先判断只读性、幂等性或外部状态，不能盲目重试。[语义检查点决策](https://github.com/deepseek-ai/deepseek-harness/blob/47f943859bef60e4160492346772ded9b24f765a/.agents/notes/implemented/bug-fix/2026-07-21-semantic-session-checkpoints.md)
- 它把注册生命周期、Agent 活跃状态、Inbox 消息进度和轮次结算视为相互正交的状态维度，避免用一个 `status` 回答所有问题。[可观察状态机决策](https://github.com/deepseek-ai/deepseek-harness/blob/47f943859bef60e4160492346772ded9b24f765a/.agents/notes/implemented/simplification/2026-07-24-agent-loop-observable-state-machine.md)
- 审批结果是闭合集合，只有 `allowed-once` 放行；缺失应答者、异常或非法返回均 fail closed。[审批说明](https://github.com/deepseek-ai/deepseek-harness/blob/47f943859bef60e4160492346772ded9b24f765a/docs/subsystems/approval.zh.md)
- 同会话 Goal 与 fresh-agent Ralph 被设计为两套明确策略，而不是一个万能 Loop；恢复持久状态不会自动恢复执行授权。[Harness-level loop 决策](https://github.com/deepseek-ai/deepseek-harness/blob/47f943859bef60e4160492346772ded9b24f765a/.agents/notes/implemented/feature/2026-07-16-harness-level-loop.md)

## 适配矩阵

| 上游机制 | 对 GameDesignOS 的价值 | 本轮动作 | 原因 |
| --- | --- | --- | --- |
| 语义检查点与未知结果分类 | 高 | 吸收 | 外部模型调用涉及私有材料、费用和远端状态，失败后不能只写“error” |
| 一次性、fail-closed 审批 | 高 | 吸收 | 与 Human Gate 一致，可把 `--execute` 限定为对精确预览的一次授权 |
| 可观察状态维度 | 中高 | 部分吸收 | 先在 host receipt 中拆开 checkpoint、status、approval、retry；暂不迁移核心 workflow schema |
| 服务定义与 provider 分离 | 中高 | 保持现状 | GameDesignOS 已规定宿主管模型与凭证，核心管 Skill、Contract、Workspace 和 Gate |
| 仅追加 Session 事件源 | 中 | 暂不吸收 | 对长期 Agent 恢复有价值，但当前 GameDesignOS 不是聊天运行时，先验证执行回执是否足够 |
| Runtime invariant | 中 | 用测试和 validator 替代 | 当前 Python runtime 的确定性 schema/test 已能覆盖首批不变式 |
| Compaction | 低 | 不吸收 | GameDesignOS 当前瓶颈是产品接入与真实项目证明，不是长会话 token 压力 |
| Cordis 插件树与 Web UI | 低 | 不吸收 | 语言栈和产品边界不匹配，会增加安装、维护和认知成本 |
| Goal/Ralph/多 Agent | 低 | 不吸收 | 单 Agent 跨宿主闭环和真实写回尚未验证，过早并行会放大状态与归因问题 |

## 本轮最小实现

新增 [`../examples/hosts/openai_compatible.py`](../examples/hosts/openai_compatible.py)，只承担一个参考宿主应有的最小职责：

```text
读取一个 SKILL.md
→ 生成精确披露预览
→ 人工检查
→ --execute 一次性授权
→ 执行前写 dispatch 检查点
→ 保存原始响应
→ 校验非空输出
→ 写 result.md 与 run-receipt.json
```

参考请求使用 `system` 与 `user` role，而不是较新的 `developer` role；DeepSeek 当前官方集成说明明确标注其 OpenAI-compatible 路径不支持 `developer` role。[DeepSeek 官方配置说明](https://api-docs.deepseek.com/quick_start/agent_integrations/oh_my_pi)

关键恢复语义：

- `request_prepared`：未越过网络边界，可以修改配置后重新准备；
- `dispatch_intent_recorded`：立刻视为 `outcome_unknown`，直到原始响应已持久化；
- `response_received`：已有本地原始响应，不应再支付一次调用；
- `artifact_committed`：输出已经通过最小结构校验并落盘；
- 网络中断：`safe_to_retry: false`，先核对供应商状态或账单。

这个回执是 `candidate example protocol`，不是新增核心 Contract。它不写 Project-Ready workspace，也不声称 exactly-once。

## 不照搬的理由

### 不把 DeepSeek Harness 加为依赖

GameDesignOS 是 Python、本地决策运行时；DeepSeek Harness 是仍在快速变化的 TypeScript 通用 Agent Harness。直接依赖会同时引入 Node 运行时、插件配置、session 模型、权限体系和发布节奏耦合，但不会自动增加游戏设计领域价值。

### 不新增完整事件源

当前真实问题是“用户没有可运行的 API 接入样例”。为此建立通用 session event store，会让实现成本远高于要消除的失败风险。本轮用原子更新的回执和私有原始响应保留最近语义边界，先验证是否足够。

### 不自动重试模型调用

模型调用可能产生费用，也可能已经在服务端完成但客户端未收到结果。没有 provider idempotency contract 或账单查询证据时，自动重试会把一次通信故障变成重复费用或重复副作用。

### 不把 `--execute` 扩大为写回授权

它只授权把已经预览的请求发送到已经预览的 endpoint。工作区写回、接受决策、发布、删除、权限变更和候选规则晋升仍属于独立 Human Gate。

## 总描述成本审计

本轮增加一个参考脚本、一个离线 fixture、一个使用说明和一组回归测试；没有增加 Skill、workspace schema、核心 CLI 命令或运行时依赖。

新增的用户概念只有三个：

```text
preview
execute
outcome_unknown
```

它们替代的是原伪代码中未表达的私有材料披露、费用授权和失败恢复歧义。当前判断为正净 VOI，但仍需真实接入数据验证。

## 需要更多证据

- 至少用两个不同 OpenAI-compatible provider 完成离线以外的受控调用；
- 验证 Windows、macOS、Linux 的 endpoint、TLS、UTF-8 和错误分类；
- 收集用户从环境配置到第一份可评审输出的中位时间；
- 观察是否真的发生 `outcome_unknown`，以及回执是否帮助避免重复调用；
- 决定未来 Application Service/MCP 是否需要把该状态提升为正式 `run-result` Contract；
- 在任何 workspace 写回前，单独验证 diff、schema validation、Review State 和 rollback。

在这些证据出现前，状态保持 `candidate`，不进入核心 Contract，不声称支持任意 OpenAI-compatible provider。

## 回滚

本轮实现没有迁移数据、修改现有 workspace 或保存凭证。回滚只需删除 `examples/hosts/` 新增文件、对应测试与本审计文档，并把 `adapters/openai-compatible.md` 恢复为说明性边界；现有 CLI、Contract 和 workspace 均不受影响。
