# GameDesignOS v1.2 本地 CLI

这里是 GameDesignOS 的可执行本地 runtime。

v1.2 的 CLI 不是自动写策划案的工具，而是一个确定性的项目操作层：它帮助真实游戏项目记录 Decision、Assumption、Evidence、Experiment、Gate、Workflow 和 Learning，并把 RJR-AI 剩余判断权停在 Human Gate。

## 安装

在仓库根目录执行：

```bash
python -m pip install -e .
gamedesignos --version
```

## 快速开始

```bash
python -m gamedesignos demo
python -m gamedesignos "我想做一款修灯塔的策略游戏"
```

`demo` 会生成一份全新的 `public-synthetic` 灯塔工作区，补齐证据和已复盘实验，并在 Human Gate 前停住；它不调用模型、不读取密钥，也不替人接受 Decision。默认输出到系统临时目录，也可用 `--destination PATH` 指定空目录。

自然语言命令会自动推荐 skill，但默认不写盘。只有显式提供 `--destination` / `--workspace`，或使用 `start`，才会把项目、第一条决策、第一条假设、三分钟验证实验和工作流一次准备好。

## 主路径

```text
Decision Object
-> Assumption
-> VOI / Evidence / Scope / Experiment / Rollback Gate
-> Experiment Plan
-> Evidence Ledger
-> Experiment Result
-> Experiment Review
-> Human Gate
-> Learning candidate
```

## 兼容

- 默认新建 v1.0 workspace。
- 旧 v0.8/v0.9 workspace 仍可打开和校验。
- 如需创建旧模板，使用 `--workspace-version 0.8.0`。

当前 `main` Runtime 版本为 `1.3.0.dev0`（P0 candidate）；workspace schema 仍为 `1.0.0`，无需迁移旧 v1 workspace。

UL（Uncertainty Ladder）是可选的 workflow 治理产物，不新增 CLI 命令：由 `paranoia-ai-system-evolver` 生成或更新 `ul_state`，runtime 在 `.gamedesignos/workflow-runs/UL-*.json` 中发现后按 canonical schema 校验。权限、发布和真实后果仍由 RJR-AI / Human Gate 控制。

完整命令见 [commands.md](./commands.md)。
