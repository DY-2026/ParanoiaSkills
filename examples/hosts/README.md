# OpenAI-Compatible Reference Host

这个目录提供一个可运行但刻意受限的参考 Harness，服务 DeepSeek、Qwen、OpenRouter 或其他 OpenAI-compatible endpoint 的接入验证。

它不是 GameDesignOS 的内置模型网关，也不会管理账号、密钥、费用、自动重试或工作区写回。核心仍保持确定性、本地优先；宿主负责模型调用。

## 安全执行模型

一次真实请求分成两个显式阶段：

1. 默认 dry-run：把将要发送的完整请求写到 `request-preview.private.json`，不访问网络。
2. 人工检查后加 `--execute`：只有任务、Skill、材料、模型和 endpoint 与原预览完全一致时才发送。

请求跨过网络边界前，Harness 会先落盘 `dispatch_intent_recorded`。如果连接随后中断而没有保存响应，回执状态为 `outcome_unknown`，`safe_to_retry` 为 `false`；请先核对供应商状态或账单，不要盲目重试。

API key 只从 `GAMEDESIGNOS_API_KEY` 读取，不接受命令行参数，也不会写入预览、回执或请求正文。

## 1. 准备环境

PowerShell 示例：

```powershell
$env:GAMEDESIGNOS_BASE_URL = "https://api.deepseek.com"
$env:GAMEDESIGNOS_MODEL = "your-model-name"
$env:GAMEDESIGNOS_API_KEY = "set-locally-never-commit"
```

`GAMEDESIGNOS_BASE_URL` 可以是服务根地址或以 `/v1` 结尾的地址；脚本会追加 `/chat/completions`。DeepSeek 直连当前官方配置使用 `https://api.deepseek.com`，不追加 `/v1`；其他兼容供应商可能要求 `/v1`，以各自文档为准。[DeepSeek 官方配置说明](https://api-docs.deepseek.com/quick_start/agent_integrations/oh_my_pi)

URL 不得携带用户名、密码、query 或 fragment。

## 2. 先生成披露预览

输出目录必须显式提供，并应放在公开仓库外或被忽略的 `outputs/` 下：

```powershell
python examples/hosts/openai_compatible.py `
  --skill game-concept-architect `
  --task "把一句修灯塔策略游戏想法整理成最小可验证蓝图" `
  --output-dir outputs/openai-compatible-lighthouse
```

检查：

- `request-preview.private.json`：将发送的 endpoint、model 和完整 messages；
- `run-receipt.json`：请求哈希、当前检查点、授权状态与安全重试判断。

预览可能包含私有材料，禁止未经审查提交或发布。

## 3. 显式执行同一份预览

确认预览后，原命令追加 `--execute`：

```powershell
python examples/hosts/openai_compatible.py `
  --skill game-concept-architect `
  --task "把一句修灯塔策略游戏想法整理成最小可验证蓝图" `
  --output-dir outputs/openai-compatible-lighthouse `
  --execute
```

成功时新增：

- `response.private.json`：供应商原始 JSON 响应；
- `result.md`：校验后的非空 `choices[0].message.content`；
- 更新后的 `run-receipt.json`：`completed` 与产物 SHA-256。

这个参考版本只生成独立输出，不会直接写入 Project-Ready workspace。未来写回必须另走 schema validation、diff、Review State、Human Gate 和 rollback。

## 4. 无网络回归

下面的 fixture 只证明请求装配、响应解析、检查点和产物提交，不证明真实供应商可用：

```powershell
python examples/hosts/openai_compatible.py `
  --skill game-concept-architect `
  --task "offline fixture" `
  --fixture-response examples/hosts/fixtures/openai-chat-completion.json `
  --output-dir outputs/openai-compatible-fixture
```

## 当前边界

- 只加载目标 Skill 的 `SKILL.md`，不会猜测或批量塞入 `references/` 与 `templates/`。
- 不支持 tool calling、streaming、自动 retry、会话续跑、MCP 或多 Agent。
- HTTP error 不会自动重试；网络边界后的未知结果要求人工核对。
- `--execute` 是对这一份精确预览的一次性授权，不代表发布、写回、接受决策或其他 Human Gate。
