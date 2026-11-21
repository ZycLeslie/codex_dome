# 输出契约与接入

每轮保存 manifest.json（版本与选择依据）、coverage.json（冻结任务与覆盖）、review.json（门禁输入）、gate.json、report.md 和 evidence/ 日志。路径相对运行目录。报告说明模式、日期时区、仓库 SHA、MR 列表、完整性、问题证据、未知项、复核方式和验证执行情况。

review.json 最小结构：
```json
{
  "schema_version": 1,
  "mode": "daily-mr",
  "snapshot_id": "host-computed-manifest-sha256",
  "scope_complete": true,
  "evidence_checked": true,
  "release_context_complete": true,
  "empty_scope_verified": false,
  "tasks": [{"id":"java!128-contract","status":"completed"}],
  "errors": [],
  "findings": []
}
```

scope_complete 仅当仓库获取、平台分页、范围枚举和冻结清单核对全部成功才 true。
evidence_checked 由宿主或独立证据校验流程读取快照文件、核对位置、版本、日志后填写；不得只因为模型产出 JSON 就设 true。
release_context_complete 在 release.required=false 时表示本次不要求发布评估，可为 true，但报告必须标明仅代码审查；required=true 时需校验目标版本组合与制品清单。
empty_scope_verified 仅当确实不存在需要分析的任务才 true。full 有代码但 tasks 为空不可通过。
tasks 的 status 枚举 completed/unknown/failed/pending；completed 表示分析已完成，不代表无问题。未适用规则的理由放 coverage.json，不能以“跳过”当完成。

finding 必填字段示例：
```json
{
  "id":"FIELD-001",
  "task_id":"java!128-contract",
  "rule_id":"CONTRACT-FIELD",
  "severity":"high",
  "status":"confirmed",
  "evidence_level":"static",
  "active":true,
  "reviewed":true,
  "fingerprint":"rule+repo+symbol+field",
  "introduced_by":"java!128",
  "baseline":"new",
  "title":"请求字段与消费者不一致",
  "trigger":"请求指定非默认值时",
  "impact":"插件静默使用默认配置",
  "evidence":[{"repo":"java","commit":"actual-sha","path":"src/Task.java","line":42,"observation":"实际代码证据"}],
  "chain":[],
  "validation":{"executed":false,"reason":"无隔离执行环境"},
  "review_method":"same-agent",
  "resolution_evidence":null
}
```

inactive/disproved 必须提供 resolution_evidence，说明已修复冻结版本或实际反证。每个 confirmed 必须有已复核的 static/reproduced 证据。复现不能省略真实日志。不得把此示例作为实际结果。

## 门禁规则

脚本检查核心字段和状态；代码引用真实性、scope 完整性、严重程度和发布版本绑定由宿主验证，不由这个脚本证明。不要将 Agent 可写文件直接作为具有权限的发布令牌。
- confirmed + active + high/critical → BLOCK（即使还有未完成任务也保留阻断）。
- 无确定阻断，但错误/未完成/缺上下文 → INCOMPLETE。
- 完整且仍有 active suspected high/critical → REVIEW。
- 其他完整结果 → PASS；medium/low 仍进入报告及整改。
- 非法输入 → INCOMPLETE，退出码 4。

宿主应将 snapshot_id 绑定仓库 SHA、制品 digest、配置、规则及依赖环境；发布系统独立读取验证记录并拒绝不匹配、过期或未完成状态。门禁脚本不验证签名，也不查询生产，不代表已经接入发布系统。
checkpoint 只能在范围和分析完成、证据已核对后原子更新；发现缺陷的完成扫描可推进分析水位，但必须保留活动缺陷，在后续扫描和发布判定中携带并复核，不能因下一天没有再次改到该文件而消失。部分失败不得推进对应水位。

## 外部调用

在云 Agent 的任务提示中给出完整 config、mode、date/mr 和输出路径。全量和增量使用不同 run_id；相同快照可共享受控缓存，不能相互覆盖结果。仅指定日历日的 review 不自动代表自上次发布以来的完整覆盖。调度器负责实例互斥、超时、恢复；本 Skill 不会自行创建定时任务或发送报告。
