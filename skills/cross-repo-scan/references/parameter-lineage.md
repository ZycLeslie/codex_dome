# 前端场景驱动的参数路径追踪

## 目标与语义

回答“场景 A 的参数 a，经过哪些条件、步骤与转换，到当前仓库 target 时是否仍满足预期；若不满足，在哪一步、因什么条件偏离”。不把同名变量当同一数据，也不把正常改名/单位转换当缺陷。

为每个 source 建立稳定 ID，分别跟踪：值表达式、类型、字段名/路径、来源、编码、单位、缺失/null/undefined、变更历史。最终判定同时检查值、语义、字段契约和目标位置；例如 a→a_b 可以保留值与来源但改变 wire key，是否正确取决于目标契约。a=0 被 a||10 改成10是值变化；是否构成 bug 还需确认 0 是否有效、默认策略是否允许。没有独立预期时只报告事实变更，结论 expectation_unknown，不自动定错。

## 1. 枚举场景、输入和边界

扫描路由、页面、按钮/事件处理器、表单 schema、校验器、store、hooks/composables、请求封装与配置。场景记录 route/action、入口符号、前置状态、权限、开关、操作序列与配置版本。不能把代码分支条件直接当作业务允许条件。

从入口递归枚举参数的属性路径：表单字段、props、路由/query、store、缓存、默认值、环境配置、服务端响应和派生字段；记录隐藏字段、未被使用参数和动态 key。每个发现的参数都要有结论，不得只追被 MR 修改或名字叫 a 的字段。动态对象键和未知 schema 用 unresolved parameter set 表达，不能宣称所有参数已枚举。参数中间新生成也要加入来源清单。

target 默认为本仓库实际边缘：fetch/XHR/HTTP adapter 的最终 URL、method、headers、query、序列化 body；SDK 调用、消息发送、worker/postMessage、持久化写入或导出函数也可配置。不能在业务 service 调用处提前停止：继续检查本仓库内拦截器、transformRequest、请求重试和序列化。第三方 SDK 内部实现不在仓库范围时，记录交给 SDK 的对象为边界，wire bytes 未证实。所有实际出口都要列出，不能只选择一条正确 API；应当未发送的分支也必须记录。

## 2. 构建参数相关的路径

读取调用链，结合可用 AST/类型/符号引用工具建立控制流与 def-use；工具不存在时允许基于代码证据分析，但标记方法与能力限制。前向追踪 source，反向追踪每个 target 输入，取两侧依赖以发现被别的来源覆盖或改走别的 API。普通文本搜索只用于找候选。

必须展开或摘要：if/else、switch 默认分支、三元、&&/||/??、optional chaining、提前 return、throw/catch/finally、循环/递归、回调、Promise/await、重试与取消。跟踪对象别名、解构、引用写入、spread 顺序、Object.assign、delete、pick/omit、数组 filter/map、JSON 序列化和 FormData/query 编码。

记录同时影响多个参数的联合条件。不能只分别测 a、b 而漏掉 `a && b` 的组合。将分支谓词累积成 path_condition；检查冲突与可达性。无可行证据的分支标 feasible_unknown，不随意剔除。用求解器时说明支持的表达式/类型与范围；不能把 SMT 编码结果扩展成完整 JS 语义证明。

对参数无影响的分支，仅在确认不影响可达性、目标、其他相关参数与副作用时合并，并保留原分支 ID 的覆盖映射。最终表达式相同但变更历史不同的路径，保留各自 provenance；不得丢失“先改坏后恢复”的过程。

处理异步时记录参数读取时刻与状态版本。检查闭包捕获旧值、effect 回写、debounce、共享对象变更和请求乱序；不同先后顺序无法枚举时列 unresolved schedule，不假定一次运行顺序代表全部。

## 3. 控制穷举范围

所有输入值通常是无限集。按代码谓词分区，而不是只跑一批随机数。例如 `a > 0`、`a === null` 生成对应符号条件；边界样例只是该路径的复现输入。

为有界循环/递归记录边界依据；可证明摘要需给不变量与适用条件。未知次数循环不以“展开 N 次成功”宣称完整。达到 max_paths_per_scenario、loop_unroll_limit、call_depth_limit 或总预算，保存 frontier 中未探索路径，标 INCOMPLETE。pairwise、采样、fuzz 仅为补充验证，不计全路径完成。

报告完整性等级：bounded_complete（已声明有限范围内且枚举/可达性证据完整）、partial（有未决路径/动态输入/时序）、observational_only（仅执行样本）。只有 AI 手工阅读没有可核验枚举依据时不能标 bounded_complete。static analysis completed 与 all feasible paths proved 是不同状态。

## 4. 逐步记录与偏离定位

每条路径、每个参数生成步骤：
`序号 → repo/SHA/file:line → 分支条件 → 操作 → 输入符号值/类型/字段 → 输出 → 来源/覆盖原因`。

终态包括 reached、not_sent、thrown、cancelled、diverged、unknown；参数结果包括 preserved、renamed、transformed、overwritten、dropped、defaulted、unused、unknown。可同时记录多个变化，业务正确性为 satisfied/violated/expectation_unknown。

标出三个位置：first_change（首次实际变化，不一定错误）、first_violation（首次违反已确认约束，可为空）、last_effective_write（决定最终结果的最后写入）。约束必须注明检查时点：若契约只要求出口保值，中间暂时变化不算 first_violation，只记 first_change 与最终偏离的候选根因；first_violation 在实际违反义务的出口或受约束步骤定位。暂时改变后恢复要明确标记 recovered，不错误认定最终仍有问题。依赖多步组合时列完整因果链，不强行只归因某一行。

每个 violated 给出最小可复现输入（包含其他控制参数/状态）、路径条件、实际终值与预期、证据和验证方式。若重现未经执行，明确标未执行。对正确转换和校验拒绝路径也输出结果，而非只输出 bug。

## 5. 增量与结果输出

full 枚举所有纳管场景和参数。MR/daily-mr 从改动反向找场景、前向找目标，并重新检查共用 helper、validator、serializer、拦截器、配置影响的全部参数；复用结论必须匹配场景依赖与快照。MR 只检查影响范围，不能称整个前端全量通过。

额外输出：
- scenarios.json：场景/入口/输入来源与预期依据；预期分 confirmed_contract、approved_requirement、implementation_inferred、unknown。
- parameter-paths.json：场景×参数×路径，包括条件、可行性、步骤、出口、终态、终值、三种定位和判定。
- path-coverage.json：分支清单、可行/不可行/未知、合并映射、证明或反例、范围边界、frontier、未解析参数/目标。
- parameter-report.md：每场景参数路径矩阵及偏离明细，区分事实变化与缺陷。

把任务清单绑定上述文件；每个场景参数族和路径完备性检查映射到既有 review.tasks。存在未探索 frontier、无法确定可行性、缺失依赖、未知输入集合、未确认关键预期时，将对应任务记 unknown，review.scope_complete=false。known non-send 是有效终态，不等于 unknown；按契约判断是否正常。现有 gate.py 继续执行，不新增另一个门禁。

PASS 只表示所声明范围满足策略；报告必须同时展示分析完整性等级。发布适用性仍由宿主校验。不得仅凭 Agent 填写的覆盖计数宣称穷举证明。

## 配置

analysis 默认为 general；parameter_lineage 仅在 analysis=parameter-lineage 时使用：
- repository：当前分析仓库 ID，必须存在于 repositories。
- scenarios：`auto` 枚举全部入口，或对象列表（id、entry、preconditions、parameters）；parameters=`*` 包含所有发现参数。指定参数子集时标清子集范围。
- targets：`auto` 或出口描述列表，描述 path/symbol/kind；仍枚举非预期出口。
- expectations_file：受控 JSON 预期表路径或 null。null 时只作数据流变化和实现一致性检查，不假定所有转换都必须保值。
- max_paths_per_scenario、loop_unroll_limit、call_depth_limit：正整数，分别为路径、循环展开、调用深度预算，截断必须标未完成。

预期表按 scenario_id、parameter、target 匹配，记录 relation（identity/rename/transform/omit/reject）、from/to 字段、适用条件、值/类型/单位关系及 source（契约/需求出处与版本）。默认关系不能擅自设 identity；用户明确要求保值时才作为约束。
