# Migrate Feature To V2

`migrate-feature-to-v2` 用于把旧仓中的业务功能迁移到 2.0 目标仓。它面向 AI coding agent、自动化工作流和工程团队，不限定某一个具体 AI 工具。

## 适用场景

- 跨仓迁移业务功能。
- 旧系统升级到 2.0。
- 按设计文档、PRD、OpenSpec、API 规格或验收标准实现新版本能力。
- 源代码实现与设计文档不是一比一对应。
- 迁移过程中需要优化、替换、拆分、合并、废弃或兼容旧功能。

## 核心原则

- 先从源仓恢复旧功能完整行为基线。
- 再读取 2.0 设计文档、需求、API 规格或验收标准。
- 对每个行为标记 `aligned`、`source-only`、`design-only` 或 `divergent`。
- 设计文档与源代码偏离时，需要用户确认后才能改变旧行为。
- 设计文档与源代码一致时，必须完整迁移。
- 不盲目复制旧实现；用目标仓现有架构完成实现。

## 默认流程

1. 确认源仓、目标仓、功能范围、设计文档和验收标准。
2. 从源仓恢复旧功能的完整行为基线。
3. 读取 2.0 设计文档，提取目标行为和验收要求。
4. 建立“旧行为 vs 目标设计”矩阵。
5. 对设计文档与源代码偏离的行为先确认。
6. 在目标仓按现有架构实现完整纵向切片。
7. 补齐单元测试、集成测试、契约测试或差异对比测试。
8. 输出迁移记录和验证结果。

## 完整迁移要求

当设计文档与源代码行为一致时，不能只迁移主流程。完整迁移至少要检查：

- 输入、输出、默认值和错误语义
- 权限、校验、安全约束
- 状态流转、事务和幂等
- 持久化读写和数据结构
- 同步和异步副作用
- 外部集成、超时、重试和降级
- 配置、开关、限制和兼容窗口
- 日志、指标、链路追踪和审计事件
- 关键边界条件和失败路径

## 分歧确认门

| 类型 | 含义 | 处理方式 |
|---|---|---|
| `aligned` | 设计文档与源代码行为一致 | 完整迁移并验证 |
| `source-only` | 源代码有行为，设计文档没提 | 默认保留，除非确认删除或废弃 |
| `design-only` | 设计文档新增能力，源代码没有 | 作为 2.0 新功能实现 |
| `divergent` | 设计文档改变或冲突于源代码行为 | 先确认，再实现改变 |

任何删除、废弃、替换或破坏兼容性的决定，都需要用户明确确认，或引用已批准的设计/需求依据。

## 迁移记录

迁移记录默认写入：

```text
.ai-migrations/feature-migrations/<feature-slug>/migration-record.md
```

如果目标仓已有自己的 agent、migration 或 design artifact 目录约定，则优先遵循目标仓约定。

迁移记录模板见：

- [references/migration-record-contract.md](./references/migration-record-contract.md)

## 相关文件

- [SKILL.md](./SKILL.md)：agent 执行迁移时使用的核心流程。
- [references/design-driven-modernization.md](./references/design-driven-modernization.md)：设计文档驱动的现代化规则。
- [references/ai-friendly-v2.md](./references/ai-friendly-v2.md)：AI 友好 2.0 设计准则。
- [scripts/profile_repositories.py](./scripts/profile_repositories.py)：源仓和目标仓画像脚本。

## 示例请求

```text
使用 migrate-feature-to-v2，把旧仓的“订单退款”功能迁移到当前 2.0 仓。
参考 docs/refund-v2-design.md。
如果设计文档和旧仓行为不一致，先列出差异并等待确认；一致的部分要完整迁移。
```
