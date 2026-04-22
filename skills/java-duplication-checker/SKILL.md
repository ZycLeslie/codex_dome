---
name: java-duplication-checker
description: 检测并分析 Java 代码中的重复类与重复方法，并生成可执行、低风险的消减建议。用于本地仓或远程代码仓的 Java 查重、重复逻辑治理、抽取公共实现、减少复制粘贴代码时；先定位重复点并分级，再给出不会破坏行为的去重路径与验证门禁。
---

# Java Duplication Checker

以“行为不变”为第一目标治理重复代码。先识别，再建议，最后在验证门禁下小步落地。

## 快速开始

1. 在目标仓库执行（默认启用增量缓存）：

```bash
python3 scripts/check_java_duplication.py --root . --summary-only --output /tmp/java-dup-report.json
```

2. 远程代码仓示例（建议浅克隆）：

```bash
git clone --depth 1 <repo-url> /tmp/remote-java-repo
python3 scripts/check_java_duplication.py --root /tmp/remote-java-repo --summary-only --output /tmp/java-dup-remote-report.json
```

3. 阅读报告中的：
- `duplicate_classes.exact` / `duplicate_classes.similar`
- `duplicate_methods.exact` / `duplicate_methods.similar`
- 每个分组的 `group_id`、`risk_level`、`strategy`

4. 先处理 `risk_level=low` 的分组，再处理 `medium`，最后才处理 `high`。

## 执行流程

### 1. 先收集边界

在行动前确认：

1. 是否允许新增公共 helper 类。
2. 是否允许调整包结构。
3. 是否允许修改 public API（默认不允许）。
4. 可执行的编译命令和测试命令。
5. 若是远程代码仓，确认仓库地址、目标分支或 commit，以及鉴权方式（SSH/Token）。

若边界不清晰，默认采用保守策略：保持 API 不变，只做内部去重建议。

### 2. 运行重复检测脚本

常用命令：

```bash
python3 scripts/check_java_duplication.py --root .
python3 scripts/check_java_duplication.py --root . --summary-only
python3 scripts/check_java_duplication.py --root . --summary-only --group-id method-similar-1
python3 scripts/check_java_duplication.py --root . --refresh-cache
python3 scripts/check_java_duplication.py --root . --include-tests --output /tmp/java-dup-report.json
```

参数说明：

- `--min-class-lines` / `--min-method-lines`: 控制最小分析规模。
- `--min-class-tokens` / `--min-method-tokens`: 过滤过短代码块，降低噪声。
- `--similarity-threshold`: 相似重复阈值（默认 0.90）。
- `--max-comparisons`: 模糊比较上限，避免大仓库耗时失控。
- `--summary-only`: 只输出分组摘要，避免返回过多成员细节。
- `--group-id`: 与 `--summary-only` 组合，按需展开指定组详情（可重复传参）。
- `--cache-file`: 缓存路径，默认 `<root>/.java-dup-cache.json`。
- `--no-cache`: 禁用缓存，强制全量解析。
- `--refresh-cache`: 忽略旧缓存并重建。

### 3. 控制上下文体积

在大仓库优先采用两段式读取：

1. 先跑 `--summary-only`，只拿分组概览。
2. 再按 `--group-id` 展开目标组，不一次性读取所有组细节。
3. 远程代码仓优先浅克隆并限制目标目录，避免把无关模块拉入分析范围。

### 4. 解释检测结果

对每个重复分组执行：

1. 检查成员位置（文件、类、方法、行号）。
2. 检查 `risk_level` 和 `risk_reasons`。
3. 根据 `strategy` 选择去重路径。
4. 将 `required_checks` 写入改动验收清单。

### 5. 生成可落地的消减建议

输出建议时遵循以下顺序：

1. **同类内 private 完全重复**：优先合并。
2. **同类内 public/protected 重复**：抽 private helper，保留原签名。
3. **跨类低风险重复**：抽组合 helper 或 utility，保留委托桥接。
4. **高风险重复（事务/并发/副作用）**：默认先不直接合并实现。

### 6. 落地前的强制门禁

任何去重改动都必须通过：

1. 编译通过。
2. 受影响测试通过。
3. public/protected 方法签名和注解语义保持一致。
4. 异常语义和副作用顺序保持一致。

不能满足门禁时，只给建议，不落地改代码。

## 不可违背规则

1. 不批量同时改多个重复组。
2. 不在没有测试兜底时删除高风险重复实现。
3. 不为去重而扩大可见性（如 private 改 public）。
4. 不改变事务边界、安全注解和缓存语义。

## 参考资料

- 安全去重策略与门禁清单：
  [references/safe-dedup-guide.md](references/safe-dedup-guide.md)

## 结果输出模板

使用本 skill 时，输出结果至少包含：

1. 重复类分组摘要（exact/similar）。
2. 重复方法分组摘要（exact/similar）。
3. 每组风险等级与原因。
4. 每组去重建议（可执行步骤）。
5. 每组验证清单（编译、测试、语义检查）。
