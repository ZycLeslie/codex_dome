# 设计说明

## 模块目标

提供一个独立 Java 模块，把受限 YAML 查询定义转换成：

- 一条可执行的 Cypher 语句
- 一个参数 `Map<String, Object>`

设计重点不是执行查询，而是稳定、可校验地生成查询。

## 模块结构

建议目录：

- `parser`：YAML 文本解析与 DTO 映射
- `model`：YAML DTO 与校验后的编译模型
- `validation`：结构校验与错误聚合
- `generator`：Cypher 语句与参数生成
- 根包 facade：对外暴露从 YAML 到查询的统一入口

## YAML 接口

### 顶层结构

```yaml
version: 1
query:
  nodes:
    A:
      labels:
        - Account
      id: account-1
      properties:
        tenantId: tenant-01
    B:
      labels:
        - Service
      properties:
        env: prod
    C:
      id: data-9
    D:
      properties:
        region: cn
  edges:
    ab:
      from: A
      to: B
      direction: OUTBOUND
      id: rel-ab
      properties:
        enabled: true
    bc:
      from: B
      to: C
      direction: OUTBOUND
      type: CALLS
      properties:
        latencyTier: gold
    bd:
      from: B
      to: D
      direction: OUTBOUND
      properties:
        optional: true
  paths:
    - alias: path_abc
      edges:
        - ab
        - bc
    - alias: path_bd
      edges:
        - bd
  return:
    items:
      - kind: PATH
        ref: path_abc
        alias: primaryPath
      - kind: PATH
        ref: path_bd
        alias: branchPath
      - kind: NODE
        ref: B
        alias: sharedNode
      - kind: EDGE
        ref: bd
        alias: branchEdge
  limit: 25
```

## 关键设计决策

### 1. 用“命名边 + 命名路径”表达分支

v1 不采用递归树状 YAML，而采用：

- 顶层 `edges` 描述边
- 顶层 `paths` 用边别名数组描述路径

这样做的原因：

- 分支通过共享边或共享节点表达，语义明确
- 路径连通性更容易校验
- 返回项可以直接引用路径别名
- 节点和边定义只写一次，避免分支重复定义造成漂移

### 2. `id` 视为业务属性

`id` 统一生成为 `alias.id = $param`，不绑定 Neo4j 内部元素 ID 语义。这样可避免版本耦合，也更符合业务图模型常见实践。

### 3. 结构位只允许安全标识符

以下字段进入 Cypher 结构位，必须做严格校验：

- 节点别名
- 边别名
- 路径别名
- 返回列别名
- 标签
- 边类型
- 属性名

规则统一为普通标识符：`[A-Za-z_][A-Za-z0-9_]*`

### 4. limit 使用校验后的字面量

过滤值全部参数化；`LIMIT` 使用校验通过的正整数直接写入语句，以避免不同 Cypher 方言对参数化 `LIMIT` 的兼容差异。

### 5. 解析器采用受限 YAML 子集

当前 workspace 无稳定可用的 YAML 依赖缓存，因此 v1 实现一个受限 YAML 解析器，仅支持本接口所需的 block-style 语法：

- 缩进映射
- 缩进数组
- 标量值

明确不支持：

- inline map / inline list
- anchors / aliases / merge keys
- 自定义 tag
- 多行标量

该限制会在 README 与 spec 中明确说明。

## 数据流

1. `YamlGraphQueryParser` 把 YAML 文本解析为通用树结构
2. 解析层把通用树映射到 YAML DTO
3. `GraphQueryCompiler` 对 DTO 做完整校验并生成编译模型
4. `CypherQueryGenerator` 根据编译模型输出 Cypher 与参数

## 编译模型

编译模型需要解决两类问题：

- 引用解析：路径里的边别名、返回项里的引用，全部解析成已知对象
- 结构约束：路径连续性、返回项合法性、别名唯一性

核心对象：

- `QueryDocument`
- `QuerySpec`
- `NodeSpec`
- `EdgeSpec`
- `PathSpec`
- `ReturnSpec`
- `ReturnItemSpec`
- `CompiledGraphQuery`
- `CompiledPath`

## 校验规则

### 文档级

- `version` 目前只能是 `1`
- `query` 必须存在
- `nodes`、`edges`、`paths` 必须非空
- 节点别名、边别名、路径别名共享同一 Cypher 变量命名空间，不能互相冲突

### 节点级

- 节点别名必须合法
- `labels` 中每个标签必须合法
- `properties` 的 key 必须合法
- `properties` 中禁止再次出现 `id`，避免与顶层 `id` 语义冲突

### 边级

- 边别名必须合法
- `from`、`to` 必须引用已定义节点
- `direction` 必须是支持值
- `type` 如存在必须合法
- `properties` 的 key 必须合法
- `properties` 中禁止再次出现 `id`

### 路径级

- 路径别名必须合法且唯一
- 每个路径至少包含一条边
- 路径中的边别名必须存在
- 路径必须连续，即前一条边的 `to` 节点必须等于后一条边的 `from` 节点

### 返回项级

- `kind` 仅支持 `PATH`、`NODE`、`EDGE`
- `ref` 必须引用对应类型的已定义对象
- 输出别名必须合法
- 输出别名必须唯一

### limit

- 如提供，必须为大于 0 的整数

## Cypher 生成策略

### 1. MATCH 子句

每条路径生成一个命名路径：

```cypher
MATCH path_abc = (A:Account)-[ab]->(B:Service)-[bc:CALLS]->(C)
MATCH path_bd = (B:Service)-[bd]->(D)
```

共享节点或共享边通过相同别名自然约束到同一实体。

### 2. WHERE 子句

节点与边过滤统一汇总到一个 `WHERE` 段中，每个定义只生成一次谓词，避免共享对象在多条路径里重复附加条件。

示例：

```cypher
WHERE A.id = $node_A_id
  AND A.tenantId = $node_A_prop_tenantId
  AND ab.id = $edge_ab_id
  AND bd.optional = $edge_bd_prop_optional
```

### 3. RETURN 子句

若 `return.items` 为空，则默认返回全部命名路径：

```cypher
RETURN path_abc AS path_abc, path_bd AS path_bd
```

若显式声明，则按声明顺序输出。

### 4. LIMIT 子句

如有 `limit`，在 `RETURN` 后追加：

```cypher
LIMIT 25
```

## 参数命名策略

参数命名必须稳定、可读、无冲突：

- 节点 `id`：`node_<alias>_id`
- 节点属性：`node_<alias>_prop_<property>`
- 边 `id`：`edge_<alias>_id`
- 边属性：`edge_<alias>_prop_<property>`

示例：

- `node_A_id`
- `node_A_prop_tenantId`
- `edge_ab_id`
- `edge_bc_prop_latencyTier`

## 异常策略

- YAML 语法问题：抛出 `YamlParseException`
- 结构校验失败：抛出 `GraphQueryValidationException`
- 生成前状态异常：抛出 `GraphQueryException`

校验异常需尽量聚合多条错误，便于一次性修复。

## 可测试性方案

至少提供以下自检覆盖：

- 单链路 `A-B-C`
- 分叉 `A-B-C` 与 `B-D`
- 边 `type` 缺省
- 节点与边 `id + properties` 过滤
- 非法路径不连续
- 非法返回引用

## 不支持范围

- 复杂布尔表达式
- 边类型集合
- 多标签逻辑运算
- OPTIONAL MATCH 生成
- 自定义函数与任意返回表达式
