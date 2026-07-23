# GitHub About Metadata

这份文件是 GitHub 仓库 About 区域的文案真源。修改公开仓库设置属于 Human Gate：先在这里评审，再由获授权的维护者或自动化更新线上设置。

定位依据见 [2026-07-11 GitHub 首页对标记录](./2026-07-11-github-readme-benchmark.md)，执行检查见 [GitHub About Checklist](./github-about-checklist.md)。

## Description

```text
Local-first game design OS for AI agents: turn sessions into evidence, experiments, reviewable decisions, and durable project memory—Human Gates and rollback.
```

这句话与 README 首屏的“AI output -> verifiable decisions”保持一致，先说用户得到什么，再说明 Human Gate 与 rollback；不写容易漂移的版本号、数量、stars 或未经证明的采用规模。

## Repository URL

```text
https://github.com/DY-2026/GameDesignOS
```

公开文章和历史链接已经依赖这个地址；除非用户明确接受链接迁移成本，否则不改仓库 URL。

## Display Name

- 项目短名：`GameDesignOS`
- 署名需要出现时：`GameDesignOS by Paranoia`

## Website

在有独立产品站或文档站前留空，不重复填写仓库自身 URL。

## Topics

```text
ai-agents
agent-skills
game-design
game-development
game-analysis
game-research
game-design-tools
indie-game
local-first
human-in-the-loop
decision-support
workflow-automation
python
```

Topics 只保留与当前公开能力直接相关的发现词；候选 skill、未来路线和尚未发布能力不进入这里。

## 2026-07-23 线上审计快照

状态：`synced`

### facts

- 线上 Description 已与本文件完全一致，并在公开仓库首页读回验证。
- 线上 Website 已清空；仓库 URL 仍为 `https://github.com/DY-2026/GameDesignOS`。
- 线上 Topics 已同步为上面的 13 项集合，并在公开仓库首页逐项读回。
- 远端已有 `v0.1.0` 至 `v1.2.0` 共 13 个 tag；`v1.2.0` GitHub Release 已公开并标记为 Latest。

### inference

- About 设置与首个正式 GitHub Release 已跟上当前稳定版本；`v1.3.0.dev0` 仍是未发布 candidate。

### needs_more_evidence

- CI 修复仍需推送修复分支并在 GitHub Actions 上完成 Linux/Windows × Python 3.11/3.12/3.13 的线上验证。
- PyPI 仍未发布；是否启用包索引分发需要单独 Human Gate。
