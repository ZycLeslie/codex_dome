# Migrate Feature To V2

`migrate-feature-to-v2` 用于把旧仓中的业务功能迁移到 2.0 目标仓。它面向 AI coding agent、自动化工作流和工程团队，不限定某一个具体 AI 工具。

## 适用场景

- 跨仓迁移业务功能。
- 旧系统升级到 2.0。
- 按设计文档、PRD、OpenSpec、API 规格或验收标准实现新版本能力。
- 源代码实现与设计文档不是一比一对应。
- 迁移过程中需要优化、替换、拆分、合并、废弃或兼容旧功能。

## 核心原则

- 先从源仓恢复旧功能完整行为基线。
- 再读取 2.0 设计文档、需求、API 规格或验收标准。
- 对每个行为标记 `aligned`、`source-only`、`design-only` 或 `divergent`。
- 设计文档与源代码偏离时，需要用户确认后才能改变旧行为。
- 设计文档与源代码一致时，必须完整迁移。
- 源仓探索结果必须落盘，保证迁移过程可追溯。
- 源仓探索出的功能点必须拆成独立 Markdown，避免上下文过大。
- 迁移过程必须在目标项目内建立可视化工作区，记录当前阶段、任务状态、证据、审批、下一步和恢复入口。
- 大迁移必须先拆成有边界的任务包，再用 subagent 或串行任务执行，避免一个上下文吞掉全部源仓、目标仓和设计文档。
- 每个任务包开始前都要评估一次性能否完成；不能一次完成的，先拆分再执行。
- 全程维护 `task-checklist.md`，防止上下文压缩或交接时丢功能、丢任务、丢验证。
- 如果功能同时包含前端和后端，必须分开探索、分开设计、分开实现、分开验证，并增加端到端闭环；不能只迁后端。
- 前端任务必须比“前端整体迁移”更细：先做薄索引，再按路由、页面/容器、组件、状态/API、表单校验、可见状态和测试拆微任务。
- 源代码里的丑陋全路径、硬编码环境路径、源仓包名前缀、全限定类名、旧域名和生成代码路径默认都是糟粕；除非是外部契约，否则不能照搬到 2.0。
- 取其精华，去其糟粕：保留业务规则和生产经验，丢掉偶然架构、坏味道和不安全实现。
- 老代码中的简单坏味道要在目标实现中顺手修掉，严重问题必须重构或修复，不能照搬。
- 先基于功能点 Markdown 写迁移设计方案，方案审批后才能开始实现。
- 如果源仓是 CodeHub 地址，必须使用对应的 CodeHub MCP 访问和探索。
- 不盲目复制旧实现；用目标仓现有架构完成实现。

## 项目内可视化迁移工作区

迁移默认在目标项目内建立可恢复、可审计的工作区：

```text
.ai-migrations/feature-migrations/<feature-slug>/
```

如果目标仓已经有自己的 agent、migration、design artifact 目录约定，优先使用目标仓约定。

可用脚本初始化骨架：

```bash
python3 ~/.codex/skills/migrate-feature-to-v2/scripts/init_migration_workspace.py \
  --feature "<feature name>" \
  --source <source-root-or-url>
```

如果不在目标仓根目录执行，再加 `--target <target-root>`。在维护本仓 skill 时，也可以使用仓库内路径 `python3 skills/migrate-feature-to-v2/scripts/init_migration_workspace.py ...`。

工作区核心文件：

- `README.md`：迁移总览、当前 gate、下一步和常用链接。
- `migration-status.md`：阶段、surface、功能点、任务包、审批和验证状态看板。
- `artifact-index.md`：所有迁移 artifact 的位置、用途、状态和更新时间。
- `timeline.md`：追加式记录探索、拆分、审批、实现、验证、暂停和恢复事件。
- `resume.md`：agent 中断或重开后的最小恢复入口，说明先读哪些文件、当前包是什么、下一步做什么。
- `source-exploration/`：源仓行为基线、证据、功能点 Markdown、坏味道和糟粕清单。
- `orchestration/`：任务包、task checklist、subagent 报告、context recovery 和 completion check。

只写代码不更新工作区，不算完成迁移步骤。每次任务包完成、方案审批变化、实现切片、验证结果、上下文压缩或交接，都要更新 `migration-status.md`、`artifact-index.md`、`timeline.md` 和 `resume.md`。

## 上下文安全的多 agent 使用

小迁移可以由单 agent 完成；只要出现多入口、多模块、多设计文档、候选文件过多、目标 owner 多、或上下文压力明显，就必须先做任务包分工。

主 agent 只做编排和最终决策：维护用户确认、方案审批、迁移设计、迁移记录和最终集成。subagent 负责局部探索、设计提取、坏味道审计、目标架构映射、单个实现切片或独立验证。

每个 subagent 任务必须有：

- 任务包 ID、角色和目标。
- 一次性完成评估：能否在当前上下文、输入、权限、依赖和写入范围内完成。
- 允许读取的输入 artifact。
- 禁止读取或修改的范围。
- 输出路径和证据格式。
- 停止条件和验收标准。
- checklist 更新规则。
- 上下文回收规则。

subagent 的结果必须落盘到 `orchestration/subagent-reports/` 或对应迁移 artifact。主 agent 最终只基于持久化 artifact、证据 ID 和简短报告继续设计和实现，不基于散落的聊天上下文。

## 任务清单和完成检查

迁移必须维护可恢复、可审计的任务清单：

- `task-package-index.md`：任务包索引和依赖。
- `task-checklist.md`：每个任务的一次性完成评估、状态、负责人、产物、验证和最终 check 状态。
- `completion-check.md`：收尾时的最终核对结果。

任务状态至少包含：`ready`、`needs-split`、`blocked`、`in-progress`、`done`、`verified`、`deferred`、`stale`。

如果任务被标记为 `needs-split`，必须先拆成更小任务包，再交给 subagent 或串行执行。任务完成后要更新 checklist；上下文压缩、任务交接、审批变化、实现变化或验证失败时也要更新。

最终不能只说“代码写完了”。必须检查：

- 每个功能点是否有任务覆盖。
- 每个前端/后端/端到端 surface 是否完成或明确不适用。
- 每个已审批 slice/package 是否完成并验证。
- 每个设计差异、坏味道修复、延期项是否记录。
- 验证命令是否有结果。

## 前后端分层迁移

迁移前先判断功能涉及哪些 surface：

- 前端：路由、页面、组件、表单、状态管理、客户端 API 调用、生成类型、校验展示、加载/空态/错误态、权限展示、埋点和可访问性。
- 后端：API 契约、handler、领域逻辑、持久化、任务、事件、外部集成、权限、校验、事务、幂等和服务端观测。
- 端到端：用户工作流、前后端契约、错误展示、兼容路径、灰度开关、回滚和验收场景。

如果源仓或目标仓存在前端 surface，需要建立独立的 frontend feature point 和 task package；如果存在后端/API surface，也要建立独立的 backend feature point 和 task package。最终设计方案必须说明每个 surface 的迁移决策和验证方式。

只有后端测试通过不能代表全功能迁移完成。当前端存在时，至少要验证页面/组件行为、API 对接、错误态和关键用户路径。

## 前端细粒度任务

前端迁移不能以“先了解完整前端项目”为任务目标。正确顺序是先建立薄索引，再拆微任务：

1. `frontend-route-indexer`：只读路由表、菜单、权限、feature flag、i18n key、测试名和高信号搜索结果，输出 `source-exploration/frontend/frontend-surface-index.md`。
2. `frontend-page-explorer`：只读一个页面或 route container 及其直接 import。
3. `frontend-component-explorer`：只读一个组件簇及有限直接子组件。
4. `frontend-state-api-explorer`：只读一个 store/query/mutation/API client/generated type 路径。
5. `frontend-form-validation-explorer`：只读一个表单、校验、提交或禁用逻辑路径。
6. `frontend-visible-state-explorer`：只读 loading、empty、error、permission、disabled、a11y、埋点或文案状态。
7. `frontend-verification-agent`：只验证一个前端测试层或一个浏览器用户路径。

如果某个前端任务需要阅读整个 `src/pages`、`src/components`、`src/store`、`src/api` 或生成客户端目录，必须标记为 `needs-split`，先拆分再执行。前端实现也要按 route wiring、page/container、component、form validation、state/API、visible states、tests 分包。

## 防止照搬遗留全路径

迁移时要特别拦截这些“看起来能跑，但其实把旧系统污染带进 2.0”的内容：

- 绝对文件系统路径，例如 `/Users/...`、`/home/...`、`/opt/...`、`/var/...`。
- Windows 全路径，例如 `C:\...`。
- `file://` URL。
- 源仓目录结构和生成代码路径。
- 源仓包名前缀、全限定类名或模块路径。
- 旧域名、旧服务地址、硬编码 localhost。
- 老框架绕路、反射字符串、类名字符串、环境特定配置。

默认处理方式：

- 如果它只是实现细节，标记为 `dross-drop`，换成目标仓配置、别名、import、adapter、storage abstraction、路由或生成类型。
- 如果它是外部契约，标记为 `preserve-by-contract`，只能放在清晰边界或兼容 adapter 里，并加测试。
- 如果不确定，标记为 `needs-reconciliation`，进入设计对齐阶段，不能直接实现。

实现后运行遗留污染扫描：

```bash
python3 skills/migrate-feature-to-v2/scripts/scan_legacy_dross.py \
  --target <target-root> \
  --legacy-token <source-package-or-path-prefix> \
  --output-md <target-root>/.ai-migrations/feature-migrations/<feature-slug>/orchestration/legacy-dross-scan.md
```

`legacy-dross-scan.md` 的每个发现都必须处理：修掉、说明是已批准兼容、或记录延期原因。未解释的发现不能进入完成状态。

## 默认流程

1. 确认源仓、目标仓、功能范围、设计文档和验收标准。
2. 识别功能 surface：前端、后端/API、任务、事件、集成、数据、配置和观测。
3. 初始化项目内可视化迁移工作区，生成 `README.md`、`migration-status.md`、`artifact-index.md`、`timeline.md` 和 `resume.md`。
4. 判断迁移规模，创建 `orchestration/task-package-index.md`、`task-checklist.md` 和具体任务包。
5. 对每个任务包评估一次性能否完成；不能完成的先拆分。
6. 用 subagent 或串行任务从源仓恢复旧功能的完整行为基线；前后端存在时分开探索。
7. 将源仓探索结果写入 `.ai-migrations/feature-migrations/<feature-slug>/source-exploration/`。
8. 将功能点拆成 `feature-points/<feature-point-slug>.md`，并维护 `feature-point-index.md`。
9. 提炼源仓精华，识别糟粕和老代码坏味道。
10. 读取 2.0 设计文档，提取目标行为和验收要求。
11. 探索目标仓架构，确认前端 owner、后端/API owner、数据、集成、测试和观测模式。
12. 基于功能点 Markdown、subagent 报告和目标仓架构写 `migration-design.md`，并列出 surface coverage。
13. 方案审批通过后，记录 `design-approval.md`。
14. 在目标仓按已批准方案和任务包实现前端、后端和端到端切片，并修复应处理的坏味道。
15. 跑 `scan_legacy_dross.py`，清理或记录所有遗留全路径、硬编码端点和源仓特定 token。
16. 补齐前端测试、后端测试、集成测试、契约测试或差异对比测试。
17. 写入 `completion-check.md`，核对任务清单、功能点、surface、审批、遗留污染扫描和验证。
18. 输出迁移记录、任务包结果、可视化工作区路径和验证结果。

## CodeHub 源仓

当源仓地址来自 CodeHub，或用户明确说明这是 CodeHub 仓库时：

- 必须优先使用对应 CodeHub MCP 获取仓库元数据、分支、文件、搜索结果、历史和评审上下文。
- 不允许静默降级为普通 `git clone`、浏览器抓取或未认证 HTTP。
- 如果当前环境没有可用的 CodeHub MCP，需要先要求用户启用或安装对应 MCP。
- CodeHub MCP 查询、资源标识、分支和证据 ID 需要写入源仓探索记录。

## 完整迁移要求

当设计文档与源代码行为一致时，不能只迁移主流程。完整迁移至少要检查：

- 前端路由、页面、组件、表单、状态、客户端 API 调用、展示文案、错误态和权限展示
- 输入、输出、默认值和错误语义
- 权限、校验、安全约束
- 状态流转、事务和幂等
- 持久化读写和数据结构
- 同步和异步副作用
- 外部集成、超时、重试和降级
- 配置、开关、限制和兼容窗口
- 日志、指标、链路追踪和审计事件
- 关键边界条件和失败路径

## 分歧确认门

| 类型 | 含义 | 处理方式 |
|---|---|---|
| `aligned` | 设计文档与源代码行为一致 | 完整迁移并验证 |
| `source-only` | 源代码有行为，设计文档没提 | 默认保留，除非确认删除或废弃 |
| `design-only` | 设计文档新增能力，源代码没有 | 作为 2.0 新功能实现 |
| `divergent` | 设计文档改变或冲突于源代码行为 | 先确认，再实现改变 |

任何删除、废弃、替换或破坏兼容性的决定，都需要用户明确确认，或引用已批准的设计/需求依据。

## 取其精华，去其糟粕

迁移时要保留的是源仓沉淀出的业务价值，而不是旧实现的形状。

| 类型 | 应该如何处理 |
|---|---|
| 业务规则、领域不变量、公共契约 | 作为目标行为保留 |
| 生产边界条件、历史兼容约束、有效测试 | 转化为测试、契约或迁移记录 |
| 前端用户路径、可见状态、交互约束 | 作为 frontend slice 和端到端验收保留 |
| 日志、指标、审计、运维经验 | 按目标仓规范保留或升级 |
| 偶然类结构、复制粘贴、框架绕路、过时依赖 | 不迁入目标设计 |
| 全路径、硬编码环境路径、源仓包名、旧域名 | 默认丢弃，改成目标侧配置或 adapter |
| 不安全实现、严重坏味道、已知缺陷 | 修复或重构，并补验证 |

## 老代码坏味道处理

迁移不是复制旧实现。源仓探索时需要记录坏味道，并在目标实现中处理：

| 类型 | 例子 | 处理方式 |
|---|---|---|
| `simple-fix` | 局部重复、误导命名、魔法值、小范围长方法、弱日志、明显空值防护缺失 | 在目标实现中直接修复，保持外部行为不变 |
| `severe-fix` | 权限绕过、注入风险、事务泄漏、竞态/幂等缺陷、数据损坏、资源泄漏、硬编码密钥、无界查询、N+1、严重耦合 | 必须重构或修复，并补验证 |
| `defer-with-record` | 超出当前功能切片或修复风险过高的债务 | 记录原因和后续建议，尽量不要带入目标设计 |
| `preserve-by-contract` | 外部依赖的奇怪历史行为 | 保留行为，不保留坏实现 |
| `essence-keep` | 有业务价值或生产经验的源仓行为 | 转化为目标行为、测试或运维要求 |
| `dross-drop` | 无业务价值的旧实现形状或权宜之计 | 明确丢弃，不迁移 |

如果严重问题的修复会改变外部契约、数据兼容或用户可见行为，需要走分歧确认门；但不能因为兼容压力就复制严重坏味道。

## 迁移记录

源仓探索记录默认写入：

```text
.ai-migrations/feature-migrations/<feature-slug>/source-exploration/
```

功能点拆分默认写入：

```text
.ai-migrations/feature-migrations/<feature-slug>/source-exploration/feature-point-index.md
.ai-migrations/feature-migrations/<feature-slug>/source-exploration/feature-points/<feature-point-slug>.md
```

迁移设计和审批记录默认写入：

```text
.ai-migrations/feature-migrations/<feature-slug>/migration-design.md
.ai-migrations/feature-migrations/<feature-slug>/design-approval.md
```

任务包和 subagent 交付物默认写入：

```text
.ai-migrations/feature-migrations/<feature-slug>/orchestration/task-package-index.md
.ai-migrations/feature-migrations/<feature-slug>/orchestration/task-checklist.md
.ai-migrations/feature-migrations/<feature-slug>/orchestration/task-packages/TP-###-<name>.md
.ai-migrations/feature-migrations/<feature-slug>/orchestration/subagent-reports/TP-###-<name>.md
.ai-migrations/feature-migrations/<feature-slug>/orchestration/context-recovery.md
.ai-migrations/feature-migrations/<feature-slug>/orchestration/completion-check.md
```

迁移记录默认写入：

```text
.ai-migrations/feature-migrations/<feature-slug>/migration-record.md
```

中断后恢复时，优先读取：

```text
.ai-migrations/feature-migrations/<feature-slug>/resume.md
.ai-migrations/feature-migrations/<feature-slug>/migration-status.md
.ai-migrations/feature-migrations/<feature-slug>/artifact-index.md
.ai-migrations/feature-migrations/<feature-slug>/orchestration/task-checklist.md
```

如果目标仓已有自己的 agent、migration 或 design artifact 目录约定，则优先遵循目标仓约定。

迁移记录模板见：

- [references/source-exploration-contract.md](./references/source-exploration-contract.md)
- [references/subagent-coordination.md](./references/subagent-coordination.md)
- [references/migration-design-approval.md](./references/migration-design-approval.md)
- [references/legacy-smell-remediation.md](./references/legacy-smell-remediation.md)
- [references/migration-record-contract.md](./references/migration-record-contract.md)

## 相关文件

- [SKILL.md](./SKILL.md)：agent 执行迁移时使用的核心流程。
- [references/subagent-coordination.md](./references/subagent-coordination.md)：大迁移的 subagent 分工、任务包和上下文回收规则。
- [references/frontend-task-slicing.md](./references/frontend-task-slicing.md)：前端薄索引、微任务拆分和上下文预算规则。
- [references/design-driven-modernization.md](./references/design-driven-modernization.md)：设计文档驱动的现代化规则。
- [references/migration-design-approval.md](./references/migration-design-approval.md)：迁移设计方案和审批门。
- [references/legacy-smell-remediation.md](./references/legacy-smell-remediation.md)：老代码坏味道分级与修复规则。
- [references/ai-friendly-v2.md](./references/ai-friendly-v2.md)：AI 友好 2.0 设计准则。
- [scripts/init_migration_workspace.py](./scripts/init_migration_workspace.py)：初始化项目内迁移工作区、可视化看板和恢复入口。
- [scripts/profile_repositories.py](./scripts/profile_repositories.py)：源仓和目标仓画像脚本。
- [scripts/scan_legacy_dross.py](./scripts/scan_legacy_dross.py)：扫描目标实现中疑似照搬的遗留全路径、旧 token 和硬编码实现细节。

## 示例请求

```text
使用 migrate-feature-to-v2，把旧仓的“订单退款”功能迁移到当前 2.0 仓。
参考 docs/refund-v2-design.md。
如果源仓或目标仓上下文太大，先拆任务包并使用 subagent 探索入口、提取设计、映射目标架构和验证。
每个任务包先评估一次性能否完成，维护 task-checklist，最终输出 completion-check。
先把源仓探索出的功能点拆成 Markdown，再基于这些 Markdown 给出迁移设计方案。
如果设计文档和旧仓行为不一致，先列出差异并等待确认；方案审批通过后再开始实现。
```
