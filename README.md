# Paged API JSON Collector

这个 workspace 已整理为 SDD（Specification-Driven Development）结构：先沉淀规格与设计，再在 `src/` 中实现。

## Workspace

```text
.
├── docs/                               # 项目说明与 SDD 工作方式
├── specs/                              # 功能规格、设计、任务拆解
│   └── 001-paged-api-json-collector/
│   └── 002-yaml-cypher-query-generator/
├── src/
│   └── extension/                      # Chrome 扩展可运行源码
│   └── graph-query-cypher/             # YAML -> Cypher Java 模块
├── progressive-god-class-refactor/     # 保留的独立资料
└── skills/                             # 保留的独立工作区
```

## 目录约定

- `docs/`：放项目概览、架构说明、工作方式说明。
- `specs/<feature>/`：每个功能一组规格文档，至少包含 `requirements.md`、`design.md`、`tasks.md`。
- `src/`：只放可运行实现，不混入需求和设计说明。

## 当前功能

当前 workspace 包含两个功能：

- 扩展源码目录：[src/extension](/Users/yuechunyuechun/Desktop/codex_demo/codex_dome/src/extension)
- 功能规格目录：[specs/001-paged-api-json-collector](/Users/yuechunyuechun/Desktop/codex_demo/codex_dome/specs/001-paged-api-json-collector)
- Java 模块目录：[src/graph-query-cypher](/Users/yuechunyuechun/Desktop/codex_demo/codex_dome/src/graph-query-cypher)
- Java 模块规格目录：[specs/002-yaml-cypher-query-generator](/Users/yuechunyuechun/Desktop/codex_demo/codex_dome/specs/002-yaml-cypher-query-generator)

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

新增功能时建议按下面顺序推进：

1. 在 `specs/` 下新建功能编号目录。
2. 先写 `requirements.md` 明确输入、输出和约束。
3. 再写 `design.md` 明确数据流、模块边界和异常处理。
4. 最后在 `tasks.md` 拆成可执行的小任务，再进入 `src/` 实现。
