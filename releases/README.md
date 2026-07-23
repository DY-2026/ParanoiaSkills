# 发布与标签规范（Release & Versioning）

本仓库采用公开开源项目常见的 `SemVer + GitHub Release + 变更日志` 方式管理版本，避免“版本说明写了但标签没发”的情况。

## 版本规则（SemVer）

- `MAJOR.MINOR.PATCH`
- `MAJOR`：对公共能力、输入输出结构、核心行为有不兼容改动。
- `MINOR`：新增 skill、流程、公开能力、非破坏性行为提升。
- `PATCH`：修复错误、文档/校验脚本改进、兼容性细化。

## 四层发布状态

本仓库把下面四层分开记录，不能再用“已存在”模糊代替：

1. `source_prepared`：版本号、CHANGELOG、release note 和验证器已经同步。
2. `tag_present`：远端存在指向已评审 release commit 的 Git tag。
3. `github_release_published`：GitHub Release 页面已基于该 tag 公开，并完成读回验证。
4. `package_published`：包索引或其他分发渠道已经实际可安装，并完成仓库外 smoke。

Tag 不等于 GitHub Release；本地 wheel 也不等于包已经公开发布。

## 新增正式 Skill 的发布检查

新增或正式接入一个 public skill 时，不要只改 skill 目录和 README。必须同步检查：

- `CHANGELOG.md` 是否新增对应版本段。
- `releases/vX.Y.Z.md` 是否新增 release note。
- README trio 的 skill 数量、Skill 表格、展示图和安装路径是否更新。
- `docs/try-it-in-10-minutes.md`、`docs/showcases/README.md` 是否补入口。
- `scripts/validate_repo.py` 是否把新 skill 纳入 required skills。
- release commit 完成后，Git tag 是否应该新增或更新到对应版本。

## Runtime / Workspace 发布检查

新增或改变 Runtime Foundation 时，还必须检查：

- `runtime/workspace-template/` 是否仍可独立复制。
- `runtime/workspace-template-v1/` 是否仍可独立复制。
- `game.designos.yaml` 与 workspace schema 是否同步。
- v0.8/v0.9 workspace 是否仍可兼容打开和校验。
- `contracts/README.md` 是否区分 skill-level 与 workspace-level contract。
- `docs/product/`、`docs/workflows/` 与 README trio 是否同步。
- `scripts/validate_repo.py` 是否覆盖新增必需路径与 workspace 约定。
- 是否明确兼容现有 skill 直接安装方式。
- 是否避免把 private workspace、客户材料或真实项目输出提交到公开仓库。

## 发布文件约定

- 发布说明文件放在 `releases/vX.Y.Z.md`
- 统一版本历史放在 `CHANGELOG.md`
- 根目录/仓库说明可从 `CHANGELOG.md` 引导到对应 release note

推荐的 release note 结构（参考流行开源项目）：

```md
# vX.Y.Z - Release Name

## Highlights
- 核心价值点

### Added
- 新增能力

### Changed
- 行为/流程变更

### Fixed
- 修复点

### Safety
- 合规与边界

### Validation
- 校验命令
```

## 推荐发布流程

1. 准备发布内容
   - 更新对应的 `releases/vX.Y.Z.md`
   - 更新 `CHANGELOG.md`
2. 运行仓库基础校验
   - `python scripts/validate_repo.py`
   - `python scripts/validate_skill.py game-concept-architect`
   - `python scripts/validate_skill.py game-experience-analyzer`
   - `python scripts/validate_skill.py game-experience-density-optimizer`
   - `python scripts/validate_skill.py game-design-proposal-writer`
3. 提交 release commit
   - `git commit -m "chore(release): prepare vX.Y.Z"`
4. 创建 Git tag（示例）
   - `git tag -a vX.Y.Z <commit> -m "Release vX.Y.Z"`
   - 如果是当前提交：`git tag -a v0.3.0 HEAD -m "Release v0.3.0"`
5. 推送到 GitHub
   - `git push origin main`
   - `git push origin vX.Y.Z`
6. 在 GitHub Release 页面创建对应 tag 的 Release，并粘贴 `releases/vX.Y.Z.md` 内容。

## 当前发布状态

最后核验：`2026-07-23`。

| Surface | 当前事实 | 状态 |
| --- | --- | --- |
| 最新正式源码版本 | `v1.2.0`，release note 与 CHANGELOG 已存在 | `source_prepared` |
| 远端 tag | `v0.1.0` 至 `v1.2.0` 共 13 个；`v1.2.0` 指向 `7eeb6f5` | `tag_present` |
| GitHub Releases | [`v1.2.0`](https://github.com/DY-2026/GameDesignOS/releases/tag/v1.2.0) 已公开并读回验证为 Latest | `github_release_published` |
| 包索引 | PyPI 的 `gamedesignos` 项目返回 404 | `not_published` |
| `main` 开发线 | `1.3.0.dev0`：portable runtime 与可选 UL 控制层 | `candidate` |
| Workspace schema | `1.0.0`，保持 v1 向后兼容 | `stable_contract` |

### 下一次公开发布建议

1. 推送 CI 修复分支，并通过 Linux/Windows × Python 3.11/3.12/3.13 的完整线上验证。
2. `v1.2.0` 的第一个 GitHub Release 已完成发布与页面读回，不需要重建 tag。
3. `v1.3.0.dev0` 继续保持 candidate；只有 roadmap 的 UL 迁移证据与 package/CI 退出门满足后，才准备 `v1.3.0` release commit、tag 和 GitHub Release。
4. PyPI 发布不是当前默认动作；只有明确需要 `pip install gamedesignos` 的公开分发承诺时再增加该渠道和凭据治理。

## 非目标约束

- `CHANGELOG.md` 记录全部公开变更；`releases/vX.Y.Z.md` 记录该版本详情。
- 不在仓库内保留“只改文档名、未同步 tag/发布入口”的半发布状态。
