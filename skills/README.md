# Engineering Agent Skills

这里存放可复用的工程自动化 skill，面向 AI coding agent、自动化工作流和工程团队使用，不限定某一个具体 AI 工具。

## 当前 Skills

- `migrate-feature-to-v2`：从旧仓恢复功能行为，结合 2.0 设计文档或优化需求，在目标仓实现 AI 友好的新版本能力。
- `java-method-mover`：迁移或抽取 Java 方法，并同步处理依赖、调用点、注入和死代码。
- `progressive-god-class-refactor`：渐进式拆分 God Class，降低大类重构风险。
- `god-class-handler`：处理 God Class 相关分析与拆分任务。
- `java-duplication-checker`：检查 Java 重复代码和可抽象逻辑。
- `java-spring-resilience-reliability-analysis`：分析 Java/Spring 可靠性与韧性问题。
- `pom-version-governance`：治理 Maven POM 依赖版本。

## 功能迁移到 2.0

核心 skill：

- [migrate-feature-to-v2](./migrate-feature-to-v2/SKILL.md)

适用场景：

- 跨仓迁移业务功能。
- 旧系统升级到 2.0。
- 按设计文档实现新版本能力。
- 源代码实现与设计文档并不一一对应。
- 需要在迁移中优化、替换、拆分、合并或废弃旧功能。

关键规则：

- 先从源仓恢复旧功能完整行为基线。
- 再读取 2.0 设计文档、需求、API 规格或验收标准。
- 对每个行为标记 `aligned`、`source-only`、`design-only` 或 `divergent`。
- 设计文档与源代码偏离时，需要用户确认后才能改变旧行为。
- 设计文档与源代码一致时，必须完整迁移，包括边界条件、校验、权限、持久化、副作用、配置、日志、指标、审计和测试。
- 迁移记录默认写入 `.ai-migrations/feature-migrations/<feature-slug>/`；如果目标仓已有自己的约定，则使用目标仓约定。

示例请求：

```text
使用 migrate-feature-to-v2，把旧仓的“订单退款”功能迁移到当前 2.0 仓。
参考 docs/refund-v2-design.md。
如果设计文档和旧仓行为不一致，先列出差异并等待确认；一致的部分要完整迁移。
```
