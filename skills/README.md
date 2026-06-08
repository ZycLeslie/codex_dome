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

- [migrate-feature-to-v2](./migrate-feature-to-v2/README.md)

适用场景：

- 跨仓迁移业务功能。
- 旧系统升级到 2.0。
- 按设计文档实现新版本能力。
- 源代码实现与设计文档并不一一对应。
- 需要在迁移中优化、替换、拆分、合并或废弃旧功能。

详细规则、默认流程、确认门和示例请求见 [migrate-feature-to-v2/README.md](./migrate-feature-to-v2/README.md)。
