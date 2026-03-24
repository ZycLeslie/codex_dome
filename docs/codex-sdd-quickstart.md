# Codex SDD Quickstart

如果你想让 Codex 在这个仓库里稳定按 SDD 工作，可以直接把下面这段贴给它。

## 推荐起手提示词

```text
你在一个采用 SDD（Specification-Driven Development）的仓库里工作。

工作规则：
1. 先读 docs/sdd-workspace.md。
2. 对当前需求，优先定位对应 specs/<feature>/requirements.md、design.md、tasks.md。
3. 如果改动涉及新能力、配置字段、状态流、错误处理、模块边界，先更新规格文档，再改 src/。
4. 如果只是微小 bug / 文案 / 样式修复，可以直接改代码，但仍需先快速核对规格。
5. 开始前先输出：feature、task、spec changes、code changes。
6. 完成后说明更新了哪些 specs 文档、改了哪些代码、还剩什么未完成事项。
7. 不要把大型设计决策只写在回复里，要同步写进 specs 文档。
8. 不要在根目录散落新文档；需求/设计/任务分别进入 specs，代码只进 src。

当前仓库主功能：分页 API JSON 抓取 Chrome 扩展。
默认先检查：
- specs/001-paged-api-json-collector/requirements.md
- specs/001-paged-api-json-collector/design.md
- specs/001-paged-api-json-collector/tasks.md
```

## 更强一点的版本

你也可以把 `docs/codex-sdd-prompt.md` 整份喂给 Codex，作为长期工作约束。

## 最推荐的实际用法

每次给 Codex 下任务时，用这个格式：

```text
任务：<你要它做什么>
约束：按 docs/codex-sdd-prompt.md 和 docs/codex-sdd-workflow.md 执行。
先不要直接大改代码，先判断是否需要更新 specs。
```

## 一个例子

```text
任务：给分页抓取增加失败页重试能力，最多重试 2 次，并在 UI 中展示失败重试次数。
约束：按 docs/codex-sdd-prompt.md 和 docs/codex-sdd-workflow.md 执行。
先检查 specs/001-paged-api-json-collector/ 下的 requirements/design/tasks，再决定规格更新范围。
```
