# Golden Lighthouse

这是 GameDesignOS 的公开 synthetic 黄金路径，用来证明运行时不只会生成文档，而能把 Decision、Assumption、Evidence、Experiment、Human Gate 和 rollback 串成可验证闭环。

## 直接浏览检入的样例

`workspace/` 是一份已生成、已通过 `gamedesignos validate` 的完整 v1 workspace，不需要安装任何东西就能查看：

| 看什么 | 打开哪里 |
| --- | --- |
| 已接受的 Decision（含 rollback trigger 与 `--by/--reason` 记录） | [`workspace/01-decisions/DEC-20260727-001.json`](./workspace/01-decisions/DEC-20260727-001.json) |
| 被实验验证过的 Assumption（`validation_status: tested`） | [`workspace/02-assumptions/ASM-20260727-001.json`](./workspace/02-assumptions/ASM-20260727-001.json) |
| 带 `unsupported_claims` 边界的 Evidence | [`workspace/03-evidence/EVD-20260727-001.json`](./workspace/03-evidence/EVD-20260727-001.json) |
| 实验计划与已复盘结果 | [`workspace/04-experiments/EXP-20260727-001/`](./workspace/04-experiments/EXP-20260727-001/) |
| VOI Gate 运行结果 | [`workspace/.gamedesignos/gate-results/`](./workspace/.gamedesignos/gate-results/) |
| Workflow Run 状态 | [`workspace/.gamedesignos/workflow-runs/WRUN-20260727-001.json`](./workspace/.gamedesignos/workflow-runs/WRUN-20260727-001.json) |

完整链路：`start` 创建 Decision/Assumption/Experiment → 登记带边界的 Evidence → 记录并复盘实验结果 → 假设标记 tested → Decision 以显式 `--by/--reason` 接受 → workspace validation 通过。

## 自己重新生成一份

在仓库根目录运行：

```bash
python scripts/create_golden_project.py --destination ../gamedesignos-golden-lighthouse
```

脚本只创建一个全新的 `public-synthetic` workspace；目标目录非空时会拒绝覆盖。完成后会自动执行 workspace validation。检入的 `workspace/` 就是用同一脚本生成的，未经手工修改。

黄金案例明确不证明真实留存、商业需求或发行表现。它只验证产品工作流、契约和安全门能够闭环运行。
