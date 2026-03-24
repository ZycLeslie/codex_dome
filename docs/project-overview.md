# 项目概览

## 项目目标

当前 workspace 同时承载两个独立能力：

- 一个 Chrome 扩展，帮助用户在浏览器当前页面环境中抓取分页 API 数据，并导出为 JSON 文件
- 一个 Java 模块，把 YAML 图查询定义转换成参数化 Cypher 语句

## 当前能力

- 抓取当前页接口数据
- 自动翻页抓取全部页
- 支持通过数据路径抽取目标数组
- 支持通过总页数字段判断何时结束
- 支持导出本次抓取结果
- 支持弹窗关闭后继续在后台执行
- 支持基于 YAML 定义节点、边、路径与返回目标
- 支持生成带参数 `Map` 的 Cypher 查询
- 支持线性路径、共享节点分叉、边类型缺省

## 代码入口

- 扩展清单：[src/extension/manifest.json](/Users/yuechunyuechun/Desktop/codex_demo/codex_dome/src/extension/manifest.json)
- 后台服务：[src/extension/background.js](/Users/yuechunyuechun/Desktop/codex_demo/codex_dome/src/extension/background.js)
- 弹窗界面：[src/extension/popup.html](/Users/yuechunyuechun/Desktop/codex_demo/codex_dome/src/extension/popup.html)
- 弹窗逻辑：[src/extension/popup.js](/Users/yuechunyuechun/Desktop/codex_demo/codex_dome/src/extension/popup.js)
- Java facade：[src/graph-query-cypher/src/main/java/com/codexdome/graphquery/GraphQueryCompiler.java](/Users/yuechunyuechun/Desktop/codex_demo/codex_dome/src/graph-query-cypher/src/main/java/com/codexdome/graphquery/GraphQueryCompiler.java)
- Java 自检入口：[src/graph-query-cypher/src/test/java/com/codexdome/graphquery/GraphQueryCompilerSelfTest.java](/Users/yuechunyuechun/Desktop/codex_demo/codex_dome/src/graph-query-cypher/src/test/java/com/codexdome/graphquery/GraphQueryCompilerSelfTest.java)

## SDD 边界

- `docs/` 负责解释“为什么做、整体是什么”。
- `specs/` 负责描述“这个功能应该怎么做、做到什么程度”。
- `src/` 负责“真正运行的实现代码”。

这样可以避免设计信息散落在源码注释和聊天记录里。
