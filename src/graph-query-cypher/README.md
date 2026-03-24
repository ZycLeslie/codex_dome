# graph-query-cypher

## 模块用途

`graph-query-cypher` 是一个独立 Java 模块，用来把受限 YAML 图查询定义编译成参数化 Cypher。

它负责四件事：

- 解析 YAML 文本
- 校验节点、边、路径、返回项和 limit
- 把路径定义编译成生成器可直接消费的模型
- 输出 `query + params`，供图库驱动直接执行

模块本身不负责连库、执行查询或映射结果集。

## YAML 接口说明

顶层结构如下：

```yaml
version: 1
query:
  nodes:
    <nodeAlias>:
      labels:
        - <Label>
      id: <scalar>
      properties:
        <property>: <scalar>
  edges:
    <edgeAlias>:
      from: <nodeAlias>
      to: <nodeAlias>
      direction: OUTBOUND | INBOUND | UNDIRECTED
      type: <Type>
      id: <scalar>
      properties:
        <property>: <scalar>
  paths:
    - alias: <pathAlias>
      edges:
        - <edgeAlias>
  return:
    items:
      - kind: PATH | NODE | EDGE
        ref: <pathAlias | nodeAlias | edgeAlias>
        alias: <outputAlias>
  limit: <positive integer>
```

说明：

- `version` 当前只支持 `1`
- `nodes`、`edges`、`paths` 必填且不能为空
- `id` 统一按业务属性处理，生成 `alias.id = $param`
- `properties` 只支持标量值：字符串、数字、布尔、`null`
- `type` 可省略；省略时仍生成合法关系模式，例如 `-[ab]->`
- `return.items` 可省略；省略时默认返回全部命名路径
- 所有标识符都必须满足 `[A-Za-z_][A-Za-z0-9_]*`

## 最小示例

```yaml
version: 1
query:
  nodes:
    A:
      labels:
        - Account
      id: account-1
    B:
      labels:
        - Service
  edges:
    ab:
      from: A
      to: B
      direction: OUTBOUND
      properties:
        enabled: true
  paths:
    - alias: path_ab
      edges:
        - ab
  limit: 10
```

生成结果示意：

```cypher
MATCH path_ab = (A:Account)-[ab]->(B:Service)
WHERE A.id = $node_A_id
  AND ab.enabled = $edge_ab_prop_enabled
RETURN path_ab AS path_ab
LIMIT 10
```

## Java 使用示例

```java
import com.codexdome.graphquery.GeneratedCypherQuery;
import com.codexdome.graphquery.GraphQueryCompiler;

public class Demo {
    public static void main(String[] args) {
        String yaml = """
                version: 1
                query:
                  nodes:
                    A:
                      labels:
                        - Account
                    B:
                      labels:
                        - Service
                  edges:
                    ab:
                      from: A
                      to: B
                      direction: OUTBOUND
                  paths:
                    - alias: path_ab
                      edges:
                        - ab
                """;

        GraphQueryCompiler compiler = new GraphQueryCompiler();
        GeneratedCypherQuery generated = compiler.compileYamlToCypher(yaml);

        System.out.println(generated.query());
        System.out.println(generated.params());
    }
}
```

如果你已经自己完成了解析或校验，也可以分别调用：

- `parseYaml(...)`
- `compile(...)`
- `generate(...)`

## 限制与边界

- 当前解析器只支持受限 block-style YAML，不支持 inline map、inline list、anchor、alias、merge key、自定义 tag、多行标量
- 只支持 `PATH`、`NODE`、`EDGE` 三种返回项，不支持任意 Cypher 表达式
- 不支持可变长路径、`OPTIONAL MATCH`、复杂布尔表达式、边类型集合或多标签逻辑运算
- `paths` 中的边必须连续，上一条边的 `to` 必须等于下一条边的 `from`
- 边 `type` 可缺省；缺省时不会补默认类型，只生成无类型关系模式
- 过滤值全部参数化，但标签、类型、别名、属性名属于 Cypher 结构位，必须通过标识符校验
- `id` 不映射 Neo4j `id()` / `elementId()` 语义，只表示业务属性 `id`

## 如何运行自检/构建

环境要求：

- JDK 17
- Maven 3.x

构建模块：

```bash
cd src/graph-query-cypher
mvn -q clean package -DskipTests
```

运行当前自检：

```bash
cd src/graph-query-cypher
mvn -q test-compile
java -cp target/classes:target/test-classes com.codexdome.graphquery.GraphQueryCompilerSelfTest
```

说明：

- 当前仓库没有引入新的测试框架；自检入口是 `src/test/java/com/codexdome/graphquery/GraphQueryCompilerSelfTest.java`
- 自检覆盖单链路、分叉、缺省边类型、过滤参数化、非法路径连续性和非法返回引用
- 在类 Unix 环境中使用上面的 classpath 分隔符 `:`；如果在 Windows 上运行，需要改为 `;`
