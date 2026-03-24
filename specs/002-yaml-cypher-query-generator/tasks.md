# 任务拆解

## 本次任务

- [x] 确认该需求属于新 feature，并创建 `002-yaml-cypher-query-generator`
- [x] 编写 `requirements.md`
- [x] 编写 `design.md`
- [x] 定义 YAML 接口结构与边界
- [x] 实现 YAML DTO 与编译模型
- [x] 实现受限 YAML 解析器与对象映射
- [x] 实现结构校验与异常模型
- [x] 实现 Cypher 生成器与参数命名策略
- [x] 补充单链路、分叉、缺省边类型、过滤与错误场景自检
- [x] 更新 README / docs 使用说明
- [x] 完成自检并提交 git commit

## 完成标准

- [x] 能从 YAML 文本生成 Cypher 与参数 `Map`
- [x] 线性路径与分叉路径都能生成合法查询
- [x] 过滤值全部参数化
- [x] 校验错误可读
- [x] 文档与实现保持一致

## 生产质量补强

- [x] 为 facade、parser、validator、generator、异常与关键模型补齐 Javadoc
- [x] 为路径编译、WHERE/参数命名、path 连续性校验、缺省边类型生成补解释性注释
- [x] 在 `src/graph-query-cypher/` 增加独立 `README.md`
- [x] 清理 `out`、`target`、`.DS_Store` 等构建产物或噪音文件，并补忽略规则
- [x] 明确当前自检/构建方式，保证本次修改完成后仓库状态可审阅
