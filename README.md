# Paged API JSON Collector

这个 workspace 现在已经接入 **OpenSpec**，并保留了已有 SDD 产物作为迁移来源。后续规范工作流以 `openspec/` 为主，`specs/` 作为过渡期遗留资料。

## Workspace

```text
.
├── .codex/                             # OpenSpec/agent skills & commands
├── docs/                               # 项目说明与历史文档
├── openspec/                           # OpenSpec 主工作流目录
│   ├── changes/
│   └── specs/
├── specs/                              # 过渡期遗留 SDD 规格（待迁移）
├── src/
│   └── extension/                      # Chrome 扩展可运行源码
│   └── graph-query-cypher/             # YAML -> Cypher Java 模块
├── progressive-god-class-refactor/     # 保留的独立资料
└── skills/                             # AI agent / 工程自动化技能目录
```

## 目录约定

- `openspec/`：主规范工作流目录。新需求、新变更优先放这里。
- `openspec/changes/`：进行中的变更。
- `openspec/changes/archive/`：已完成并归档的变更。
- `docs/`：项目概览、迁移说明、辅助文档。
- `specs/`：旧 SDD 资料，作为迁移源保留，不再作为首选入口。
- `src/`：只放可运行实现，不混入需求和设计说明。
- `skills/`：可复用的 AI agent / 自动化工作流技能，面向代码迁移、Java 重构、依赖治理等工程任务。

## 当前功能

当前 workspace 主要包含：

- 扩展源码目录：[src/extension](/Users/yuechunyuechun/Desktop/codex_demo/codex_dome/src/extension)
- Java 模块目录：[src/graph-query-cypher](/Users/yuechunyuechun/Desktop/codex_demo/codex_dome/src/graph-query-cypher)
- 旧版 SDD 规格目录：[specs/002-yaml-cypher-query-generator](/Users/yuechunyuechun/Desktop/codex_demo/codex_dome/specs/002-yaml-cypher-query-generator)
- OpenSpec 迁移归档目录：[openspec/changes/archive/2026-03-24-yaml-cypher-query-generator-migration](/Users/yuechunyuechun/Desktop/codex_demo/codex_dome/openspec/changes/archive/2026-03-24-yaml-cypher-query-generator-migration)

## AI Agent Skills

技能目录位于 [skills](/Users/yuechunyuechun/Desktop/codex_demo/codex_dome/skills)，用于沉淀可复用的工程自动化流程，不限定某一个具体 AI 工具。

重点技能：

- [migrate-feature-to-v2](/Users/yuechunyuechun/Desktop/codex_demo/codex_dome/skills/migrate-feature-to-v2/SKILL.md)：根据旧仓源代码证据和 2.0 设计文档，实现 AI 友好的目标功能。支持非一比一迁移、功能优化、拆分/合并、废弃兼容、设计文档落地。
- [java-method-mover](/Users/yuechunyuechun/Desktop/codex_demo/codex_dome/skills/java-method-mover/SKILL.md)：迁移或抽取 Java 方法，并同步处理依赖、调用点和死代码。
- [progressive-god-class-refactor](/Users/yuechunyuechun/Desktop/codex_demo/codex_dome/skills/progressive-god-class-refactor/SKILL.md)：渐进式拆分 God Class。

功能迁移默认流程：

1. 从源仓恢复旧功能的完整行为基线。
2. 读取 2.0 设计文档、需求或验收标准。
3. 建立“旧行为 vs 目标设计”矩阵。
4. 设计文档与源代码偏离时先确认；一致时保证完整迁移。
5. 在目标仓按现有架构实现、测试和验证。

迁移记录默认写入 `.ai-migrations/feature-migrations/<feature-slug>/`，如果目标仓已有自己的 agent / migration / design artifact 目录约定，则优先遵循目标仓约定。

## 使用方式

1. 打开 Chrome 的 `chrome://extensions/`
2. 开启开发者模式
3. 选择“加载已解压的扩展程序”
4. 载入目录：
   `/Users/yuechunyuechun/Desktop/codex_demo/codex_dome/src/extension`

## Java 模块使用方式

`src/graph-query-cypher` 是一个独立模块，用来把 YAML 图查询定义转换成参数化 Cypher。

标准构建：

```bash
cd /Users/yuechunyuechun/Desktop/codex_demo/codex_dome/src/graph-query-cypher
mvn -DskipTests package
```

本地自检：

```bash
cd /Users/yuechunyuechun/Desktop/codex_demo/codex_dome/src/graph-query-cypher
find src/main/java src/test/java -name '*.java' | sort > /tmp/graph_query_sources.txt
javac --release 17 -d out @/tmp/graph_query_sources.txt
java -cp out com.codexdome.graphquery.GraphQueryCompilerSelfTest
```

YAML 示例文件位于：

- [single-chain.yaml](/Users/yuechunyuechun/Desktop/codex_demo/codex_dome/src/graph-query-cypher/src/test/resources/examples/single-chain.yaml)
- [branching.yaml](/Users/yuechunyuechun/Desktop/codex_demo/codex_dome/src/graph-query-cypher/src/test/resources/examples/branching.yaml)

说明：

- v1 YAML 仅支持 block-style map/list 的受限子集
- 过滤值参数化输出到 `params`
- `id` 语义固定为业务属性 `id`

## 后续开发建议

后续新增功能建议按 OpenSpec 流程推进：

1. 在仓库中使用 OpenSpec 命令提出变更（例如 `/opsx:propose <idea>`）。
2. 在 `openspec/changes/` 中完善 proposal、spec、design、tasks。
3. 再进入 `src/` 实现。
4. 完成后归档到 `openspec/changes/archive/`。

过渡期内，如需参考旧资料，可查看 `specs/` 下的历史 SDD 文档。
