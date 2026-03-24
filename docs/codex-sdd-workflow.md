# Codex SDD Workflow

这份文档是给 Codex / 其他编码代理的落地工作流，不是抽象理念。

## 一、接到需求后的默认流程

### 0. 先分类
先判断请求属于哪一类：

- **微小修复**：文案、样式、小 bug
- **功能迭代**：新增/修改用户可见能力
- **结构性重构**：模块拆分、状态流调整、路径语法扩展

---

### 1. 定位 feature
优先找到对应 feature 目录：

- 现有功能：进入对应 `specs/<feature>/`
- 新功能：创建新的顺序编号目录，例如 `specs/002-.../`

如果是当前主功能，默认先检查：
- `specs/001-paged-api-json-collector/requirements.md`
- `specs/001-paged-api-json-collector/design.md`
- `specs/001-paged-api-json-collector/tasks.md`

---

### 2. 对齐规格
开始编码前，先回答这 4 个问题：

1. 这次改动改变了什么用户能力？
2. 这次改动有没有改变模块职责或数据流？
3. 这次改动是否引入新的状态、配置项、错误策略？
4. 现有 `tasks.md` 是否已经覆盖这次工作？

判断规则：

- **4 个问题都基本是 no** → 可以直接实现
- 任意一个明显是 **yes** → 先更新规格文档

---

### 3. 写入任务
开始改代码前，在 `tasks.md` 里体现本次工作，形式任选：

- 勾选一个已有任务
- 新增一个待办任务
- 给阶段性任务补充子项

要求：**不要只在聊天里说计划，不落文档。**

---

### 4. 实现最小闭环
编码时遵守：

- 优先最小改动面
- 优先保留现有结构稳定性
- 只把可运行代码放在 `src/`
- 文档、规格、实现三者保持一致

---

### 5. 自检
至少检查：

- 主要用户路径是否仍然通
- 新增配置项是否有默认行为
- popup 与 background 的消息交互是否匹配
- 持久化字段是否前后一致
- 导出数据格式是否被意外破坏

---

### 6. 收尾
完成后给出：

- 改了什么
- 为什么这么改
- 哪些规格文档同步了
- 还有什么未完成（若有）

如果没做完，把剩余事项写回 `tasks.md`。

## 二、针对这个仓库的推荐执行模板

每次开始前，建议 Codex 先输出：

```text
Plan
- feature: 001-paged-api-json-collector
- task: add retry strategy for failed pages
- spec changes: requirements + design + tasks
- code changes: src/extension/background.js, src/extension/popup.js
```

完成后输出：

```text
Done
- updated specs/001-paged-api-json-collector/requirements.md
- updated specs/001-paged-api-json-collector/design.md
- updated specs/001-paged-api-json-collector/tasks.md
- implemented retry flow in src/extension/background.js
- added retry config handling in popup
- self-check: request loop / stop / export paths reviewed
```

## 三、常见场景处理

### 场景 1：只是修一个明显 bug
动作：

- 读相关规格
- 直接修实现
- 如果这个 bug 暴露出规格遗漏，再回补文档

### 场景 2：新增配置项
动作：

- 先改 `requirements.md`
- 再改 `design.md` 里的配置对象 / 数据流
- 再改 `tasks.md`
- 最后改 UI + background

### 场景 3：抽离公共逻辑
动作：

- 如果只是纯实现内聚提升，且不改边界，可直接做
- 如果抽离会改变模块职责、依赖方向或未来扩展方式，先补 `design.md`

### 场景 4：引入更复杂路径语法
动作：

- 这不是“小改动”
- 先写清语法规则、兼容策略、失败行为
- 再实现

## 四、给 Codex 的一句话操作口诀

**Read spec → align design → update tasks → implement minimal slice → self-check → sync docs.**
