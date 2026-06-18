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
- 源仓探索结果必须落盘，保证迁移过程可追溯。
- 取其精华，去其糟粕：保留业务规则和生产经验，丢掉偶然架构、坏味道和不安全实现。
- 老代码中的简单坏味道要在目标实现中顺手修掉，严重问题必须重构或修复，不能照搬。
- 如果源仓是 CodeHub 地址，必须使用对应的 CodeHub MCP 访问和探索。
- 不盲目复制旧实现；用目标仓现有架构完成实现。

## 默认流程

1. 确认源仓、目标仓、功能范围、设计文档和验收标准。
2. 从源仓恢复旧功能的完整行为基线。
3. 将源仓探索结果写入 `.ai-migrations/feature-migrations/<feature-slug>/source-exploration/`。
4. 提炼源仓精华，识别糟粕和老代码坏味道。
5. 读取 2.0 设计文档，提取目标行为和验收要求。
6. 建立“旧行为 vs 目标设计”矩阵。
7. 对设计文档与源代码偏离的行为先确认。
8. 在目标仓按现有架构实现完整纵向切片，并修复应处理的坏味道。
9. 补齐单元测试、集成测试、契约测试或差异对比测试。
10. 输出迁移记录和验证结果。

## CodeHub 源仓

当源仓地址来自 CodeHub，或用户明确说明这是 CodeHub 仓库时：

- 必须优先使用对应 CodeHub MCP 获取仓库元数据、分支、文件、搜索结果、历史和评审上下文。
- 不允许静默降级为普通 `git clone`、浏览器抓取或未认证 HTTP。
- 如果当前环境没有可用的 CodeHub MCP，需要先要求用户启用或安装对应 MCP。
- CodeHub MCP 查询、资源标识、分支和证据 ID 需要写入源仓探索记录。

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

## 取其精华，去其糟粕

迁移时要保留的是源仓沉淀出的业务价值，而不是旧实现的形状。

| 类型 | 应该如何处理 |
|---|---|
| 业务规则、领域不变量、公共契约 | 作为目标行为保留 |
| 生产边界条件、历史兼容约束、有效测试 | 转化为测试、契约或迁移记录 |
| 日志、指标、审计、运维经验 | 按目标仓规范保留或升级 |
| 偶然类结构、复制粘贴、框架绕路、过时依赖 | 不迁入目标设计 |
| 不安全实现、严重坏味道、已知缺陷 | 修复或重构，并补验证 |

## 老代码坏味道处理

迁移不是复制旧实现。源仓探索时需要记录坏味道，并在目标实现中处理：

| 类型 | 例子 | 处理方式 |
|---|---|---|
| `simple-fix` | 局部重复、误导命名、魔法值、小范围长方法、弱日志、明显空值防护缺失 | 在目标实现中直接修复，保持外部行为不变 |
| `severe-fix` | 权限绕过、注入风险、事务泄漏、竞态/幂等缺陷、数据损坏、资源泄漏、硬编码密钥、无界查询、N+1、严重耦合 | 必须重构或修复，并补验证 |
| `defer-with-record` | 超出当前功能切片或修复风险过高的债务 | 记录原因和后续建议，尽量不要带入目标设计 |
| `preserve-by-contract` | 外部依赖的奇怪历史行为 | 保留行为，不保留坏实现 |
| `essence-keep` | 有业务价值或生产经验的源仓行为 | 转化为目标行为、测试或运维要求 |
| `dross-drop` | 无业务价值的旧实现形状或权宜之计 | 明确丢弃，不迁移 |

如果严重问题的修复会改变外部契约、数据兼容或用户可见行为，需要走分歧确认门；但不能因为兼容压力就复制严重坏味道。

## 迁移记录

源仓探索记录默认写入：

```text
.ai-migrations/feature-migrations/<feature-slug>/source-exploration/
```

迁移记录默认写入：

```text
.ai-migrations/feature-migrations/<feature-slug>/migration-record.md
```

如果目标仓已有自己的 agent、migration 或 design artifact 目录约定，则优先遵循目标仓约定。

迁移记录模板见：

- [references/source-exploration-contract.md](./references/source-exploration-contract.md)
- [references/legacy-smell-remediation.md](./references/legacy-smell-remediation.md)
- [references/migration-record-contract.md](./references/migration-record-contract.md)

## 相关文件

- [SKILL.md](./SKILL.md)：agent 执行迁移时使用的核心流程。
- [references/design-driven-modernization.md](./references/design-driven-modernization.md)：设计文档驱动的现代化规则。
- [references/legacy-smell-remediation.md](./references/legacy-smell-remediation.md)：老代码坏味道分级与修复规则。
- [references/ai-friendly-v2.md](./references/ai-friendly-v2.md)：AI 友好 2.0 设计准则。
- [scripts/profile_repositories.py](./scripts/profile_repositories.py)：源仓和目标仓画像脚本。

## 示例请求

```text
使用 migrate-feature-to-v2，把旧仓的“订单退款”功能迁移到当前 2.0 仓。
参考 docs/refund-v2-design.md。
如果设计文档和旧仓行为不一致，先列出差异并等待确认；一致的部分要完整迁移。
```
