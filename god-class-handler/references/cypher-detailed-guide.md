# Cypher Detailed Guide

这份文档专门讲 Cypher。

如果说 Neo4j 是图数据库本体，那么 Cypher 就是你和图数据库沟通的语言。它负责描述：

- 你要找哪些节点和关系
- 你要怎么过滤数据
- 你要如何聚合、排序、分页
- 你要如何创建、更新、删除图数据

这份文档会尽量把 Cypher 讲细，同时结合当前仓库里的 `GraphQueryService.java` 和 `GraphPathQueryDemo.java` 做落地说明。

适合你在这些场景下使用：

- 第一次系统学习 Cypher
- 已经会写简单查询，但经常在 `WITH`、`CALL {}`、`UNION ALL`、路径模式上卡住
- 想把当前仓库里的 Java 查询构造器接到真实 Neo4j 上
- 想写出更稳定、更容易维护的图查询

---

## 1. 先建立一个 Cypher 思维模型

在 SQL 里，你通常会想：

- 表有哪些
- 表和表怎么 join
- where 条件怎么写

在 Cypher 里，你更常想：

- 图里有哪些节点
- 节点之间如何通过关系连接
- 我需要匹配什么样的“图模式”
- 这条路径上哪些节点、哪些关系需要满足条件

Cypher 的核心不是“表”，而是“模式”。

所谓模式，就是：

```cypher
(a:Node)-[r:REL]->(b:Node)
```

这行代码不是在说“从表 A join 表 B”，而是在说：

- 有一个别名叫 `a` 的节点
- 有一个别名叫 `r` 的关系
- 这个关系从 `a` 指向 `b`
- `a` 和 `b` 都带 `Node` 标签
- 这条关系的类型是 `REL`

一旦你适应了这种“按图模式表达查询”的方式，Cypher 会比多表 join 更直观。

---

## 2. Cypher 基础语法长什么样

先看一条最普通的查询：

```cypher
MATCH (n:Node)
WHERE n.status = 'online'
RETURN n
ORDER BY n.id
LIMIT 10
```

这条语句的阅读顺序可以理解为：

1. `MATCH` 匹配模式。
2. `WHERE` 过滤匹配结果。
3. `RETURN` 决定返回什么。
4. `ORDER BY` 对返回结果排序。
5. `LIMIT` 限制返回条数。

Cypher 最常见的子句包括：

- `MATCH`
- `OPTIONAL MATCH`
- `WHERE`
- `RETURN`
- `WITH`
- `CREATE`
- `MERGE`
- `SET`
- `REMOVE`
- `DELETE`
- `DETACH DELETE`
- `UNWIND`
- `CALL {}`
- `UNION`
- `UNION ALL`

---

## 3. 模式匹配是 Cypher 的核心

### 3.1 节点语法

节点的基本写法：

```cypher
(n)
```

带标签：

```cypher
(n:Node)
```

带属性：

```cypher
(n:Node {id: 1, name: 'alpha'})
```

这里每个部分的含义是：

- `n`：变量别名
- `Node`：标签
- `{...}`：属性 map

### 3.2 关系语法

关系的基本写法：

```cypher
()-[r]->()
```

带类型：

```cypher
()-[r:REL]->()
```

带属性：

```cypher
()-[r:REL {type: 'depends'}]->()
```

方向也可以反着写：

```cypher
()<-[r:REL]-()
```

或者忽略方向：

```cypher
()-[r:REL]-()
```

### 3.3 路径模式

最典型的路径模式：

```cypher
(a:Node)-[ab:REL]->(b:Node)-[bc:REL]->(c:Node)
```

这表示一条两跳路径：

- `a -> b`
- `b -> c`

当前仓库里的 `buildPathQuery(...)` 就是在程序里动态生成这种模式。

### 3.4 给整条路径起别名

你可以给整个路径起别名：

```cypher
MATCH p = (a:Node)-[ab:REL]->(b:Node)-[bc:REL]->(c:Node)
RETURN p
```

之后就可以继续使用：

- `nodes(p)`
- `relationships(p)`
- `length(p)`

这在当前仓库中也有直接应用：

```cypher
RETURN p0 AS path,
       [node IN nodes(p0) | properties(node)] AS nodeSummaries,
       [rel IN relationships(p0) | properties(rel)] AS edgeSummaries
```

---

## 4. 变量、标签、类型、属性分别是什么

### 4.1 变量

变量是查询中的临时名字，例如：

- `n`
- `a`
- `b`
- `r`
- `p`

示例：

```cypher
MATCH (a:Node)-[r:REL]->(b:Node)
RETURN a, r, b
```

这里：

- `a` 是起点节点变量
- `r` 是关系变量
- `b` 是终点节点变量

### 4.2 标签

标签用于区分节点类别，例如：

- `:Node`
- `:User`
- `:Service`
- `:Database`

示例：

```cypher
MATCH (u:User)
RETURN u
```

### 4.3 关系类型

关系类型用于区分边的语义，例如：

- `:REL`
- `:DEPENDS_ON`
- `:CALLS`
- `:OWNS`

示例：

```cypher
MATCH (a)-[:DEPENDS_ON]->(b)
RETURN a, b
```

### 4.4 属性

属性是键值对，既可以挂在节点上，也可以挂在关系上。

节点属性示例：

```cypher
(n:Node {id: 1, name: 'alpha', status: 'online'})
```

关系属性示例：

```cypher
(a)-[:REL {type: 'depends', status: 'valid'}]->(b)
```

---

## 5. `MATCH` 是最常用的读取入口

`MATCH` 的意思就是“按照某个图模式去匹配数据”。

### 5.1 最简单的 `MATCH`

```cypher
MATCH (n:Node)
RETURN n
```

含义：

- 找出所有带 `Node` 标签的节点
- 返回这些节点

### 5.2 匹配节点和关系

```cypher
MATCH (a:Node)-[r:REL]->(b:Node)
RETURN a, r, b
```

含义：

- 找出所有 `Node -[REL]-> Node` 形式的关系
- 返回起点、边、终点

### 5.3 匹配更长路径

```cypher
MATCH p = (a:Node)-[:REL]->(b:Node)-[:REL]->(c:Node)
RETURN p
```

这会返回长度为 2 的路径。

### 5.4 一个查询里可以写多个模式

```cypher
MATCH (a:Node), (b:Node)
RETURN a, b
```

这在语法上没问题，但要小心。

如果两个模式之间没有关系约束，就容易形成笛卡尔积，也就是：

- 每个 `a`
- 都会和每个 `b`
- 组合成一行

这通常是性能和结果膨胀问题的来源之一。

---

## 6. `WHERE` 负责过滤结果

`WHERE` 一般跟在 `MATCH` 或 `WITH` 后面。

### 6.1 最常见的等值过滤

```cypher
MATCH (n:Node)
WHERE n.name = 'alpha'
RETURN n
```

### 6.2 多条件过滤

```cypher
MATCH (n:Node)
WHERE n.status = 'online'
  AND n.name CONTAINS 'alpha'
RETURN n
```

### 6.3 常见比较运算符

- `=`
- `<>`
- `>`
- `>=`
- `<`
- `<=`

示例：

```cypher
MATCH (n:Node)
WHERE n.id >= 10
RETURN n
```

### 6.4 常见逻辑运算符

- `AND`
- `OR`
- `NOT`

示例：

```cypher
MATCH (n:Node)
WHERE n.status = 'online'
   OR n.priority > 5
RETURN n
```

### 6.5 字符串匹配

Cypher 常用字符串判断有：

- `CONTAINS`
- `STARTS WITH`
- `ENDS WITH`

示例：

```cypher
MATCH (n:Node)
WHERE n.name CONTAINS 'beta'
RETURN n
```

当前仓库的 `Condition.contains(...)` 最终生成的就是这种语法。

### 6.6 `IN` 判断

```cypher
MATCH (n:Node)
WHERE n.status IN ['online', 'warming']
RETURN n
```

### 6.7 `IS NULL` / `IS NOT NULL`

```cypher
MATCH (n:Node)
WHERE n.remark IS NULL
RETURN n
```

或者：

```cypher
MATCH (n:Node)
WHERE n.remark IS NOT NULL
RETURN n
```

### 6.8 关系属性过滤

```cypher
MATCH (a:Node)-[r:REL]->(b:Node)
WHERE r.status = 'valid'
RETURN a, r, b
```

### 6.9 节点和关系一起过滤

```cypher
MATCH p = (a:Node)-[ab:REL]->(b:Node)-[bc:REL]->(c:Node)
WHERE a.name = 'alpha'
  AND b.name CONTAINS 'beta'
  AND c.status = 'online'
  AND ab.type = 'depends'
  AND bc.remark CONTAINS 'core'
RETURN p
```

这就是当前仓库第一条路径查询的核心逻辑。

---

## 7. `RETURN` 决定你真正要拿到什么

### 7.1 返回节点

```cypher
MATCH (n:Node)
RETURN n
```

### 7.2 返回多个变量

```cypher
MATCH (a:Node)-[r:REL]->(b:Node)
RETURN a, r, b
```

### 7.3 返回具体字段

```cypher
MATCH (n:Node)
RETURN n.id, n.name, n.status
```

### 7.4 起别名

```cypher
MATCH (n:Node)
RETURN n.id AS nodeId, n.name AS nodeName
```

### 7.5 返回表达式

```cypher
MATCH (n:Node)
RETURN n.id AS nodeId, size(keys(n)) AS propertyCount
```

### 7.6 返回 map

```cypher
MATCH (n:Node)
RETURN {
  nodeId: n.id,
  nodeName: n.name,
  nodeStatus: n.status
} AS summary
```

当前仓库的全图汇总查询就用到了这种 map 风格：

```cypher
RETURN collect({
  nodeId: n.id,
  nodeProperties: properties(n),
  outEdgeCount: outEdgeCount,
  inEdgeCount: inEdgeCount,
  totalEdgeCount: outEdgeCount + inEdgeCount
}) AS nodes
```

### 7.7 `DISTINCT`

去重：

```cypher
MATCH (n:Node)-[:REL]->(m:Node)
RETURN DISTINCT n
```

### 7.8 排序、分页

```cypher
MATCH (n:Node)
RETURN n
ORDER BY n.id DESC
SKIP 20
LIMIT 10
```

---

## 8. `WITH` 是 Cypher 里最容易卡住、也最重要的子句

`WITH` 可以理解为“把当前结果集传给下一段查询”。

它的作用非常多：

- 控制变量作用域
- 聚合
- 重命名
- 排序
- 分段处理查询
- 在继续匹配前先压缩结果

### 8.1 最基本的 `WITH`

```cypher
MATCH (n:Node)
WITH n
RETURN n
```

这虽然看起来多余，但说明了一件很重要的事：

`WITH` 后面没有带上的变量，后面就不能再用了。

### 8.2 变量作用域重置

```cypher
MATCH (n:Node)-[r:REL]->(m:Node)
WITH n, count(r) AS outEdgeCount
RETURN n, outEdgeCount
```

这里在 `WITH` 后，`m` 不再可见，因为它没有被传下去。

### 8.3 `WITH` + 聚合

```cypher
MATCH (n:Node)-[r:REL]->()
WITH n, count(r) AS outEdgeCount
RETURN n.id, outEdgeCount
```

含义：

- 先匹配所有出边
- 按节点分组
- 统计每个节点的出边数

### 8.4 `WITH` + `ORDER BY`

```cypher
MATCH (n:Node)
WITH n
ORDER BY n.id
RETURN collect(n)
```

### 8.5 `WITH` + `WHERE`

`WHERE` 也可以接在 `WITH` 后面，用于过滤上一段处理后的结果：

```cypher
MATCH (n:Node)-[r:REL]->()
WITH n, count(r) AS outEdgeCount
WHERE outEdgeCount > 2
RETURN n, outEdgeCount
```

### 8.6 为什么当前仓库的汇总查询会多次用 `WITH`

示例：

```cypher
MATCH (n:Node)
OPTIONAL MATCH (n)-[out:REL]->()
WITH n, count(out) AS outEdgeCount
OPTIONAL MATCH ()-[in:REL]->(n)
WITH n, outEdgeCount, count(in) AS inEdgeCount
RETURN ...
```

这里的 `WITH` 用来做两件事：

1. 先把每个节点的出边数统计出来。
2. 再带着这个中间结果继续统计入边数。

没有 `WITH`，你很难优雅地把多阶段聚合串起来。

---

## 9. `OPTIONAL MATCH` 类似左连接

`OPTIONAL MATCH` 表示：

- 如果模式匹配到了，就带上结果
- 如果没匹配到，也保留前面的记录，只是匹配出来的变量为 `null`

### 9.1 示例

```cypher
MATCH (n:Node)
OPTIONAL MATCH (n)-[r:REL]->()
RETURN n, count(r)
```

如果某个节点没有任何出边，它依然会被返回。

### 9.2 为什么统计类查询经常用它

因为你通常不希望“没有边的节点”直接消失。

当前仓库的全图汇总查询就是典型例子：

- 统计出边时用了 `OPTIONAL MATCH`
- 统计入边时也用了 `OPTIONAL MATCH`

这样即使某个节点没有任何关系，仍然能出现在结果中。

---

## 10. 聚合函数怎么用

Cypher 的常见聚合函数包括：

- `count(...)`
- `collect(...)`
- `sum(...)`
- `avg(...)`
- `min(...)`
- `max(...)`

### 10.1 `count`

```cypher
MATCH (n:Node)
RETURN count(n) AS totalNodes
```

### 10.2 `collect`

```cypher
MATCH (n:Node)
RETURN collect(n.name) AS names
```

### 10.3 `sum`

```cypher
MATCH (n:Node)
RETURN sum(n.weight) AS totalWeight
```

### 10.4 分组聚合

```cypher
MATCH (n:Node)-[r:REL]->()
RETURN n.status, count(r) AS edgeCount
```

这里会按 `n.status` 分组。

### 10.5 聚合时最重要的一条规则

在 `RETURN` 或 `WITH` 中：

- 非聚合字段会成为分组键
- 聚合函数会在组内计算

例如：

```cypher
MATCH (n:Node)-[r:REL]->()
RETURN n, count(r)
```

表示“按节点 `n` 分组，统计每个 `n` 的关系数量”。

---

## 11. `CREATE` 用于创建节点和关系

### 11.1 创建节点

```cypher
CREATE (n:Node {id: 1, name: 'alpha', status: 'online'})
RETURN n
```

### 11.2 创建关系

```cypher
MATCH (a:Node {id: 1}), (b:Node {id: 2})
CREATE (a)-[:REL {type: 'depends'}]->(b)
```

### 11.3 一次创建多段图

```cypher
CREATE (a:Node {id: 1, name: 'alpha'})
CREATE (b:Node {id: 2, name: 'beta'})
CREATE (a)-[:REL {type: 'depends'}]->(b)
```

### 11.4 注意

`CREATE` 不会帮你去重。

你执行两次：

```cypher
CREATE (n:Node {id: 1})
```

就会真的产生两个节点。

如果你需要“存在就复用，不存在才创建”，要看 `MERGE`。

---

## 12. `MERGE` 用于按模式确保存在

`MERGE` 的语义是：

- 如果这个模式已经存在，就匹配它
- 如果不存在，就创建它

### 12.1 节点 `MERGE`

```cypher
MERGE (n:Node {id: 1})
RETURN n
```

### 12.2 `MERGE` 后更新属性

```cypher
MERGE (n:Node {id: 1})
SET n.name = 'alpha', n.status = 'online'
RETURN n
```

### 12.3 `ON CREATE` / `ON MATCH`

```cypher
MERGE (n:Node {id: 1})
ON CREATE SET n.createdAt = datetime(), n.name = 'alpha'
ON MATCH SET n.lastSeenAt = datetime()
RETURN n
```

### 12.4 关系 `MERGE`

```cypher
MATCH (a:Node {id: 1}), (b:Node {id: 2})
MERGE (a)-[r:REL]->(b)
ON CREATE SET r.type = 'depends'
RETURN a, r, b
```

### 12.5 `MERGE` 的一个常见坑

这两种写法语义不完全一样：

```cypher
MERGE (a:Node {id: 1})-[:REL]->(b:Node {id: 2})
```

和：

```cypher
MERGE (a:Node {id: 1})
MERGE (b:Node {id: 2})
MERGE (a)-[:REL]->(b)
```

第二种通常更安全，也更容易控制每一段的行为。

---

## 13. `SET` / `REMOVE` 用于更新属性和标签

### 13.1 更新属性

```cypher
MATCH (n:Node {id: 1})
SET n.status = 'offline'
RETURN n
```

### 13.2 一次更新多个属性

```cypher
MATCH (n:Node {id: 1})
SET n.name = 'alpha-v2',
    n.status = 'online',
    n.version = 2
RETURN n
```

### 13.3 追加标签

```cypher
MATCH (n:Node {id: 1})
SET n:CriticalNode
RETURN n
```

### 13.4 删除属性

```cypher
MATCH (n:Node {id: 1})
REMOVE n.remark
RETURN n
```

### 13.5 删除标签

```cypher
MATCH (n:Node {id: 1})
REMOVE n:CriticalNode
RETURN n
```

---

## 14. `DELETE` / `DETACH DELETE` 的区别

### 14.1 `DELETE`

```cypher
MATCH (n:Node {id: 1})
DELETE n
```

如果这个节点还有关系，通常会报错，因为 Neo4j 不允许删掉仍然连接着关系的节点。

### 14.2 `DETACH DELETE`

```cypher
MATCH (n:Node {id: 1})
DETACH DELETE n
```

它会：

1. 先删除该节点关联的所有关系。
2. 再删除节点本身。

### 14.3 清空示例数据时常用

```cypher
MATCH (n:Node)
DETACH DELETE n
```

---

## 15. 参数是写 Cypher 时的基本习惯

推荐写法：

```cypher
MATCH (n:Node)
WHERE n.name = $name
RETURN n
```

参数：

```json
{
  "name": "alpha"
}
```

### 15.1 为什么要参数化

- 避免直接拼字符串
- 降低注入风险
- 更便于日志和调试
- 更容易复用执行计划

### 15.2 哪些内容通常可以参数化

- 属性值
- 条件值
- 创建时的属性 map 内容

### 15.3 哪些内容不能直接靠参数化解决

通常下面这些“结构性内容”不能像普通值那样直接参数化：

- 标签名
- 关系类型名
- 变量名
- 属性 key

这也是为什么当前仓库在 Java 代码里对下面这些字段做了标识符校验：

- `nodeLabel`
- `relationType`
- `alias`
- `property`

因为它们会直接进入 Cypher 结构，而不是作为参数值绑定。

---

## 16. 列表、map 和函数很常用

### 16.1 列表

```cypher
RETURN ['alpha', 'beta', 'gamma'] AS names
```

### 16.2 map

```cypher
RETURN {
  id: 1,
  name: 'alpha',
  status: 'online'
} AS summary
```

### 16.3 `properties(...)`

```cypher
MATCH (n:Node)
RETURN properties(n) AS nodeProperties
```

返回节点完整属性 map。

这在当前仓库里被大量使用：

- `properties(n)`
- `properties(r)`

### 16.4 `type(...)`

```cypher
MATCH ()-[r:REL]->()
RETURN type(r) AS relationType
```

### 16.5 `keys(...)`

```cypher
MATCH (n:Node)
RETURN keys(n) AS propertyKeys
```

### 16.6 `size(...)`

```cypher
RETURN size(['a', 'b', 'c']) AS listSize
```

也可以用于字符串长度或模式统计，具体要结合场景理解。

### 16.7 `coalesce(...)`

```cypher
MATCH (n:Node)
RETURN coalesce(n.remark, 'N/A') AS remark
```

### 16.8 `toLower(...)` / `toUpper(...)`

```cypher
MATCH (n:Node)
WHERE toLower(n.name) CONTAINS toLower($keyword)
RETURN n
```

用于大小写不敏感搜索时很常见。

---

## 17. 列表推导式很适合处理路径结果

Cypher 支持列表推导式，写法类似：

```cypher
[item IN items | expression]
```

示例：

```cypher
MATCH p = (a:Node)-[:REL]->(b:Node)-[:REL]->(c:Node)
RETURN [node IN nodes(p) | node.name] AS nodeNames
```

如果你想拿属性 map：

```cypher
MATCH p = (a:Node)-[r1:REL]->(b:Node)-[r2:REL]->(c:Node)
RETURN [node IN nodes(p) | properties(node)] AS nodeSummaries,
       [rel IN relationships(p) | properties(rel)] AS edgeSummaries
```

这正是当前仓库路径查询返回摘要数组的关键语法。

---

## 18. 路径相关函数是图查询的亮点

### 18.1 `nodes(path)`

```cypher
MATCH p = (a:Node)-[:REL]->(b:Node)-[:REL]->(c:Node)
RETURN nodes(p)
```

返回路径上的节点列表。

### 18.2 `relationships(path)`

```cypher
MATCH p = (a:Node)-[:REL]->(b:Node)-[:REL]->(c:Node)
RETURN relationships(p)
```

返回路径上的关系列表。

### 18.3 `length(path)`

```cypher
MATCH p = (a:Node)-[:REL]->(b:Node)-[:REL]->(c:Node)
RETURN length(p) AS hopCount
```

返回路径的跳数。

### 18.4 `shortestPath(...)`

```cypher
MATCH p = shortestPath((a:Node {id: 1})-[:REL*]->(b:Node {id: 9}))
RETURN p
```

这类查询很有用，但在复杂图里也要注意性能和约束范围。

---

## 19. 可变长度路径要谨慎使用

可变长度路径示例：

```cypher
MATCH p = (a:Node)-[:REL*1..3]->(b:Node)
RETURN p
```

意思是：

- 从 `a` 到 `b`
- 走 `REL` 类型关系
- 路径长度 1 到 3 跳都可以

### 19.1 常见用法

```cypher
MATCH p = (a:Node {id: 1})-[:REL*1..5]->(b:Node)
RETURN p
```

### 19.2 风险

- 结果量容易爆炸
- 可能匹配到很多重复或相似路径
- 图里有环时更要注意

### 19.3 经验建议

- 总是给最大深度
- 尽量给起点或终点加条件
- 先用小范围数据验证
- 必要时加 `LIMIT`

---

## 20. `UNWIND` 可以把列表拆成多行

`UNWIND` 在批量处理和参数列表场景里非常有用。

### 20.1 基本示例

```cypher
UNWIND ['alpha', 'beta', 'gamma'] AS name
RETURN name
```

结果会变成三行。

### 20.2 批量创建节点

```cypher
UNWIND [
  {id: 1, name: 'alpha'},
  {id: 2, name: 'beta'},
  {id: 3, name: 'gamma'}
] AS row
CREATE (n:Node {id: row.id, name: row.name})
RETURN count(n)
```

### 20.3 驱动层传入参数列表时很常用

```cypher
UNWIND $rows AS row
MERGE (n:Node {id: row.id})
SET n.name = row.name
RETURN count(n)
```

---

## 21. `CASE` 适合做条件表达式

### 21.1 简单 `CASE`

```cypher
MATCH (n:Node)
RETURN n.name,
       CASE
         WHEN n.status = 'online' THEN 'available'
         ELSE 'unavailable'
       END AS stateLabel
```

### 21.2 用于排序或展示映射

```cypher
MATCH (n:Node)
RETURN n,
       CASE n.priority
         WHEN 1 THEN 'P1'
         WHEN 2 THEN 'P2'
         ELSE 'NORMAL'
       END AS priorityLabel
```

---

## 22. `CALL {}` 是组织复杂查询的关键工具

子查询写法：

```cypher
CALL {
  MATCH (n:Node)
  RETURN count(n) AS totalNodes
}
RETURN totalNodes
```

### 22.1 为什么需要子查询

因为有些逻辑放在一个大查询里会变得：

- 难读
- 容易重复计数
- 很难控制中间结果

`CALL {}` 可以把复杂逻辑拆开。

### 22.2 当前仓库里的典型例子

```cypher
CALL {
  MATCH (n:Node)
  OPTIONAL MATCH (n)-[out:REL]->()
  WITH n, count(out) AS outEdgeCount
  OPTIONAL MATCH ()-[in:REL]->(n)
  WITH n, outEdgeCount, count(in) AS inEdgeCount
  ORDER BY n.id
  RETURN collect({
    nodeId: n.id,
    nodeProperties: properties(n),
    outEdgeCount: outEdgeCount,
    inEdgeCount: inEdgeCount,
    totalEdgeCount: outEdgeCount + inEdgeCount
  }) AS nodes
}
CALL {
  MATCH (from:Node)-[r:REL]->(to:Node)
  WITH from, r, to
  ORDER BY from.id, to.id
  RETURN collect({
    fromNodeId: from.id,
    toNodeId: to.id,
    relationType: type(r),
    edgeProperties: properties(r)
  }) AS edges
}
RETURN nodes, edges
```

这里用两个 `CALL {}` 分开处理：

- 节点汇总
- 边汇总

最后再统一返回。

这比把所有统计揉在一条大查询里更清晰，也更稳。

### 22.3 什么时候适合用 `CALL {}`

- 多阶段聚合
- 多块独立统计
- 想分离节点汇总和边汇总
- 先缩小中间结果再继续查询

---

## 23. `UNION` 和 `UNION ALL` 用于拼接多段查询

### 23.1 `UNION`

会合并结果并去重。

```cypher
MATCH (n:Node)
WHERE n.status = 'online'
RETURN n.name AS name
UNION
MATCH (n:Node)
WHERE n.priority = 1
RETURN n.name AS name
```

### 23.2 `UNION ALL`

会合并结果但不去重。

```cypher
MATCH (n:Node)
WHERE n.status = 'online'
RETURN n.name AS name
UNION ALL
MATCH (n:Node)
WHERE n.priority = 1
RETURN n.name AS name
```

### 23.3 当前仓库为什么用 `UNION ALL`

当前路径查询会为每个 branch 生成一段：

- `MATCH`
- `WHERE`
- `RETURN`

然后通过 `UNION ALL` 拼接。

这样做的好处：

- 保留每个 branch 的独立结果
- 不强行去重
- 能够返回 `branch-1`、`branch-2` 这样的分支名

如果改成 `UNION`，某些本应保留的重复结果可能会被去掉。

---

## 24. `ORDER BY` / `SKIP` / `LIMIT` 的常见用法

### 24.1 排序

```cypher
MATCH (n:Node)
RETURN n
ORDER BY n.id ASC
```

### 24.2 倒序

```cypher
MATCH (n:Node)
RETURN n
ORDER BY n.id DESC
```

### 24.3 分页

```cypher
MATCH (n:Node)
RETURN n
ORDER BY n.id
SKIP 20
LIMIT 10
```

### 24.4 和 `WITH` 一起用

```cypher
MATCH (n:Node)
WITH n
ORDER BY n.id DESC
LIMIT 5
RETURN collect(n.name) AS topNames
```

---

## 25. `RETURN` 和 `WITH` 里都可以做 map 投影

### 25.1 直接构造 map

```cypher
MATCH (n:Node)
RETURN {
  id: n.id,
  name: n.name,
  status: n.status
} AS summary
```

### 25.2 路径结果做摘要

```cypher
MATCH p = (a:Node)-[r:REL]->(b:Node)
RETURN {
  start: properties(a),
  relation: properties(r),
  end: properties(b)
} AS pathSummary
```

### 25.3 当前仓库为什么喜欢这种写法

因为它适合把：

- 图对象
- 中间统计值
- 原始属性 map

组合成一个可直接返回给上层的结构。

---

## 26. 变量作用域是 Cypher 出错高发区

### 26.1 一个最常见的坑

```cypher
MATCH (n:Node)-[r:REL]->(m:Node)
WITH n, count(r) AS outEdgeCount
RETURN n, m, outEdgeCount
```

这里通常会报错，因为 `m` 没有被带过 `WITH`。

### 26.2 正确写法

如果你后面还需要 `m`，就要带上它：

```cypher
MATCH (n:Node)-[r:REL]->(m:Node)
WITH n, m, count(r) AS outEdgeCount
RETURN n, m, outEdgeCount
```

但要注意，这样的分组逻辑也变了，因为现在是按 `n, m` 分组。

### 26.3 记忆法

可以把 `WITH` 理解成一个“新阶段的输入列表”：

- 你不带过去的变量
- 后面就没了

---

## 27. `null` 语义也值得单独注意

### 27.1 `OPTIONAL MATCH` 产生的 `null`

```cypher
MATCH (n:Node)
OPTIONAL MATCH (n)-[r:REL]->()
RETURN n, r
```

如果没有匹配到关系，`r` 就会是 `null`。

### 27.2 `null` 判断方式

```cypher
MATCH (n:Node)
WHERE n.remark IS NULL
RETURN n
```

不要写成：

```cypher
WHERE n.remark = null
```

这种写法通常不是你想要的。

### 27.3 `coalesce`

```cypher
MATCH (n:Node)
RETURN coalesce(n.remark, 'N/A') AS remark
```

---

## 28. 图查询里常见的统计模式

### 28.1 统计总节点数

```cypher
MATCH (n:Node)
RETURN count(n) AS totalNodes
```

### 28.2 统计每个节点的出边数

```cypher
MATCH (n:Node)
OPTIONAL MATCH (n)-[r:REL]->()
RETURN n.id, count(r) AS outEdgeCount
ORDER BY n.id
```

### 28.3 统计每个节点的入边数

```cypher
MATCH (n:Node)
OPTIONAL MATCH ()-[r:REL]->(n)
RETURN n.id, count(r) AS inEdgeCount
ORDER BY n.id
```

### 28.4 同时统计入边和出边

```cypher
MATCH (n:Node)
OPTIONAL MATCH (n)-[out:REL]->()
WITH n, count(out) AS outEdgeCount
OPTIONAL MATCH ()-[in:REL]->(n)
RETURN n.id,
       outEdgeCount,
       count(in) AS inEdgeCount,
       outEdgeCount + count(in) AS totalEdgeCount
ORDER BY n.id
```

这就是当前仓库汇总查询的核心模式之一。

---

## 29. 路径查询的典型写法

### 29.1 固定长度路径

```cypher
MATCH p = (a:Node)-[:REL]->(b:Node)-[:REL]->(c:Node)
RETURN p
```

### 29.2 带条件的路径

```cypher
MATCH p = (a:Node)-[ab:REL]->(b:Node)-[bc:REL]->(c:Node)
WHERE a.name = 'alpha'
  AND b.name CONTAINS 'beta'
  AND c.status = 'online'
  AND ab.type = 'depends'
  AND bc.remark CONTAINS 'core'
RETURN p
```

### 29.3 返回路径摘要，而不直接返回图对象

```cypher
MATCH p = (a:Node)-[ab:REL]->(b:Node)-[bc:REL]->(c:Node)
RETURN [node IN nodes(p) | properties(node)] AS nodes,
       [rel IN relationships(p) | properties(rel)] AS edges
```

这种风格特别适合接口返回。

---

## 30. 看懂当前仓库的结构化路径查询

当前 demo 会生成下面这段查询：

```cypher
MATCH p0 = (a:Node)-[ab:REL]->(b:Node)-[bc:REL]->(c:Node)
WHERE a.name = $branch0_node0_cond0_value
  AND b.name CONTAINS $branch0_node1_cond0_value
  AND c.status = $branch0_node2_cond0_value
  AND ab.type = $branch0_edge0_cond0_value
  AND bc.remark CONTAINS $branch0_edge1_cond0_value
RETURN 'branch-1' AS branch,
       p0 AS path,
       [node IN nodes(p0) | properties(node)] AS nodeSummaries,
       [rel IN relationships(p0) | properties(rel)] AS edgeSummaries
UNION ALL
MATCH p1 = (b:Node)-[bd:REL]->(d:Node)
WHERE b.name CONTAINS $branch1_node0_cond0_value
  AND d.name = $branch1_node1_cond0_value
  AND bd.status = $branch1_edge0_cond0_value
RETURN 'branch-2' AS branch,
       p1 AS path,
       [node IN nodes(p1) | properties(node)] AS nodeSummaries,
       [rel IN relationships(p1) | properties(rel)] AS edgeSummaries
```

你可以把它拆成四层理解：

### 第 1 层：路径模式

- `p0 = (a)-[ab]->(b)-[bc]->(c)`
- `p1 = (b)-[bd]->(d)`

### 第 2 层：节点和边的过滤条件

- 节点条件写在 `a.name`、`b.name`、`c.status`
- 边条件写在 `ab.type`、`bc.remark`、`bd.status`

### 第 3 层：路径结果展开

- `nodes(p0)`
- `relationships(p0)`

### 第 4 层：多分支拼接

- 用 `UNION ALL` 拼成一条查询
- 通过 `branch` 字段标识结果来源

这套设计非常适合“前端或上层配置多个路径模板，然后统一查询”的场景。

---

## 31. `EXISTS`、模式判断和条件表达式

在某些场景下，你不一定要把关系直接返回出来，而只是判断某种模式是否存在。

### 31.1 模式存在性判断

```cypher
MATCH (n:Node)
WHERE EXISTS {
  MATCH (n)-[:REL]->(:Node {status: 'online'})
}
RETURN n
```

这个写法很适合表达：

- “找出至少连接到一个在线节点的节点”

如果你的业务只是判断存在性，而不是拿全量路径，这类语法会更清晰。

---

## 32. `MERGE` 和唯一约束通常要配合考虑

如果你经常这样写：

```cypher
MERGE (n:Node {id: $id})
```

那通常应该考虑给 `id` 增加唯一约束：

```cypher
CREATE CONSTRAINT node_id_unique IF NOT EXISTS
FOR (n:Node)
REQUIRE n.id IS UNIQUE;
```

这样有几个好处：

- 避免重复数据
- 提高定位效率
- 保证 `MERGE` 的行为更稳定

---

## 33. 索引和约束会直接影响查询体验

### 33.1 常见索引

```cypher
CREATE INDEX node_name_idx IF NOT EXISTS
FOR (n:Node)
ON (n.name);
```

```cypher
CREATE INDEX node_status_idx IF NOT EXISTS
FOR (n:Node)
ON (n.status);
```

### 33.2 常见唯一约束

```cypher
CREATE CONSTRAINT node_id_unique IF NOT EXISTS
FOR (n:Node)
REQUIRE n.id IS UNIQUE;
```

### 33.3 哪些字段适合建索引

通常是你经常用于：

- `WHERE`
- `MERGE`
- 节点定位
- 登录或查详情

的字段，例如：

- `id`
- `name`
- `status`

---

## 34. `EXPLAIN` 和 `PROFILE` 是性能排查入口

### 34.1 `EXPLAIN`

```cypher
EXPLAIN
MATCH (n:Node)
WHERE n.name = $name
RETURN n
```

它会告诉你执行计划，但不会真正执行查询。

### 34.2 `PROFILE`

```cypher
PROFILE
MATCH (n:Node)
WHERE n.name = $name
RETURN n
```

它会真正执行，并告诉你：

- 实际命中的行数
- 各阶段开销
- 是否走了索引

### 34.3 什么时候应该看执行计划

- 查询明显变慢
- 多跳路径结果量不受控
- 统计类查询出现意外膨胀
- 怀疑写成了笛卡尔积

---

## 35. Cypher 中几类高频坑

### 35.1 笛卡尔积

错误风险示例：

```cypher
MATCH (a:Node), (b:Node)
RETURN a, b
```

如果没有明确关联条件，就可能得到大量组合结果。

### 35.2 `WITH` 丢变量

示例：

```cypher
MATCH (n:Node)-[r:REL]->(m:Node)
WITH n, count(r) AS edgeCount
RETURN m
```

`m` 已经不在作用域里了。

### 35.3 把没有边的节点过滤掉

如果你用：

```cypher
MATCH (n:Node)-[r:REL]->()
RETURN n
```

那么没有出边的节点根本不会出现。

如果你要保留它们，通常要改成：

```cypher
MATCH (n:Node)
OPTIONAL MATCH (n)-[r:REL]->()
RETURN n, count(r)
```

### 35.4 无界可变路径

这类查询要格外小心：

```cypher
MATCH p = (a:Node)-[:REL*]->(b:Node)
RETURN p
```

在大图上可能非常重。

### 35.5 误用 `CREATE` 造成重复数据

如果是“幂等写入”，优先考虑 `MERGE`，不要盲目 `CREATE`。

### 35.6 直接拼接结构性内容

比如：

- 标签名
- 关系类型
- 属性名

如果这些来自外部输入，又没有做白名单校验，就会有风险。

当前仓库的 `validateIdentifier(...)` 就是在处理这个问题。

---

## 36. 一个更实用的“读查询模板”

很多业务查询都可以按这个模板想：

```cypher
MATCH p = (start:Node)-[r:REL]->(end:Node)
WHERE start.status = $startStatus
  AND r.type = $relationType
RETURN {
  start: properties(start),
  relation: properties(r),
  end: properties(end)
} AS row
ORDER BY start.id
LIMIT 20
```

思维顺序就是：

1. 先定义模式。
2. 再写过滤。
3. 决定输出结构。
4. 最后排序和限制条数。

---

## 37. 一个更实用的“统计查询模板”

```cypher
MATCH (n:Node)
OPTIONAL MATCH (n)-[out:REL]->()
WITH n, count(out) AS outEdgeCount
OPTIONAL MATCH ()-[in:REL]->(n)
WITH n, outEdgeCount, count(in) AS inEdgeCount
RETURN {
  nodeId: n.id,
  outEdgeCount: outEdgeCount,
  inEdgeCount: inEdgeCount,
  totalEdgeCount: outEdgeCount + inEdgeCount
} AS summary
ORDER BY summary.nodeId
```

这是非常典型的：

- 全量节点
- 分阶段统计
- 统一摘要输出

---

## 38. 一个更实用的“批量写入模板”

```cypher
UNWIND $rows AS row
MERGE (n:Node {id: row.id})
SET n.name = row.name,
    n.status = row.status
RETURN count(n) AS affectedRows
```

适合：

- 驱动层传入批量节点
- 做幂等写入
- 避免一条一条提交

---

## 39. 当前仓库里的 Java 对象如何映射到 Cypher

| Java 对象 | Cypher 对应物 | 作用 |
| --- | --- | --- |
| `GraphQueryService` | 查询构造器 | 负责组装 `statement` |
| `CypherQuery` | 查询结果封装 | 承载 `statement + params` |
| `PathQueryRequest` | 多分支查询请求 | 承载多个 branch |
| `Branch` | 一段路径模板 | 生成一段 `MATCH/WHERE/RETURN` |
| `NodeRef` | 节点模式片段 | 决定 `(a:Node)` 和节点条件 |
| `EdgeRef` | 关系模式片段 | 决定 `[ab:REL]` 和边条件 |
| `Condition` | 条件表达式 | 决定 `=` 或 `CONTAINS` 等 |

### 39.1 `NodeRef`

```java
GraphQueryService.NodeRef.of("a", GraphQueryService.Condition.eq("name", "alpha"))
```

会影响：

- 节点别名 `a`
- 过滤条件 `a.name = $...`

### 39.2 `EdgeRef`

```java
GraphQueryService.EdgeRef.of("ab", GraphQueryService.Condition.eq("type", "depends"))
```

会影响：

- 边别名 `ab`
- 过滤条件 `ab.type = $...`

### 39.3 `Condition.contains`

```java
GraphQueryService.Condition.contains("remark", "core")
```

最终会生成：

```cypher
remark CONTAINS $param
```

具体落在哪个变量上，则由节点或边别名决定。

---

## 40. 看懂 `statement + params` 这种封装

当前仓库不是直接把最终字符串一口气拼死，而是输出：

- `statement`
- `params`

这是非常标准的做法。

示例思路：

```java
CypherQuery query = service.buildPathQuery(request);
session.run(query.statement(), query.params());
```

这样有几个好处：

- 查询结构和查询值分开
- 更安全
- 更易调试
- 更适合驱动层执行

---

## 41. Cypher 详细学习时最值得记住的 10 条经验

1. 先想“模式”，再想“字段”。
2. `MATCH` 是图模式匹配，不是表扫描加 join 的翻版。
3. `WITH` 会重置作用域，没带过去的变量后面就没了。
4. 统计类查询经常需要 `OPTIONAL MATCH`，否则零关系节点会丢失。
5. 参数化值，白名单控制结构性内容。
6. 路径查询很强，但可变长度路径必须控深度。
7. `CALL {}` 适合拆复杂统计和独立逻辑块。
8. `UNION ALL` 适合保留多分支结果，不要默认换成 `UNION`。
9. `MERGE` 用于幂等存在性保证，`CREATE` 用于明确创建。
10. 性能问题先看 `EXPLAIN` / `PROFILE`，不要只凭感觉猜。

---

## 42. 一个最小练习脚本

你可以在 Neo4j Browser 里先执行这段数据：

```cypher
MATCH (n:Node)
DETACH DELETE n;

CREATE (a:Node {id: 1, name: 'alpha', status: 'online'})
CREATE (b:Node {id: 2, name: 'beta-service', status: 'online'})
CREATE (c:Node {id: 3, name: 'gamma', status: 'online'})
CREATE (d:Node {id: 4, name: 'delta', status: 'offline'})

CREATE (a)-[:REL {type: 'depends', remark: 'core-service', status: 'valid'}]->(b)
CREATE (b)-[:REL {type: 'flows', remark: 'core-chain', status: 'valid'}]->(c)
CREATE (b)-[:REL {type: 'sync', remark: 'edge-to-delta', status: 'valid'}]->(d);
```

然后依次试这些查询。

### 练习 1：查所有节点

```cypher
MATCH (n:Node)
RETURN n
ORDER BY n.id
```

### 练习 2：查所有关系

```cypher
MATCH (a:Node)-[r:REL]->(b:Node)
RETURN a.name, type(r), r.type, b.name
ORDER BY a.id, b.id
```

### 练习 3：查第一条路径

```cypher
MATCH p = (a:Node)-[ab:REL]->(b:Node)-[bc:REL]->(c:Node)
WHERE a.name = 'alpha'
  AND b.name CONTAINS 'beta'
  AND c.status = 'online'
  AND ab.type = 'depends'
  AND bc.remark CONTAINS 'core'
RETURN p
```

### 练习 4：把路径展开为摘要

```cypher
MATCH p = (a:Node)-[ab:REL]->(b:Node)-[bc:REL]->(c:Node)
WHERE a.name = 'alpha'
  AND b.name CONTAINS 'beta'
  AND c.status = 'online'
  AND ab.type = 'depends'
  AND bc.remark CONTAINS 'core'
RETURN [node IN nodes(p) | properties(node)] AS nodeSummaries,
       [rel IN relationships(p) | properties(rel)] AS edgeSummaries
```

### 练习 5：做一份节点入出边汇总

```cypher
MATCH (n:Node)
OPTIONAL MATCH (n)-[out:REL]->()
WITH n, count(out) AS outEdgeCount
OPTIONAL MATCH ()-[in:REL]->(n)
RETURN n.id,
       outEdgeCount,
       count(in) AS inEdgeCount,
       outEdgeCount + count(in) AS totalEdgeCount
ORDER BY n.id
```

---

## 43. 最后给一个速查版

### 读取

```cypher
MATCH (n:Label)
WHERE n.name = $name
RETURN n
```

### 关系读取

```cypher
MATCH (a:LabelA)-[r:REL]->(b:LabelB)
RETURN a, r, b
```

### 创建

```cypher
CREATE (n:Label {id: $id, name: $name})
```

### 幂等写入

```cypher
MERGE (n:Label {id: $id})
SET n.name = $name
```

### 删除节点

```cypher
MATCH (n:Label {id: $id})
DETACH DELETE n
```

### 统计

```cypher
MATCH (n:Label)
RETURN count(n)
```

### 多阶段聚合

```cypher
MATCH (n:Label)
OPTIONAL MATCH (n)-[r:REL]->()
WITH n, count(r) AS edgeCount
RETURN n, edgeCount
```

### 子查询

```cypher
CALL {
  MATCH (n:Label)
  RETURN count(n) AS total
}
RETURN total
```

### 列表拆行

```cypher
UNWIND $rows AS row
RETURN row
```

### 路径摘要

```cypher
MATCH p = (a)-[r]->(b)
RETURN [n IN nodes(p) | properties(n)],
       [rel IN relationships(p) | properties(rel)]
```

---

这份文档的重点不是让你背所有语法，而是帮你建立一种判断方式：

- 当前需求更像“找节点”、还是“找路径”、还是“做统计”？
- 需要 `MATCH` 还是 `OPTIONAL MATCH`？
- 需要直接 `RETURN`，还是先 `WITH` 做中间聚合？
- 需要一个查询块，还是拆成多个 `CALL {}`？
- 需要单路径，还是多分支 `UNION ALL`？

一旦这个判断模型清楚了，Cypher 会变得非常好用。
