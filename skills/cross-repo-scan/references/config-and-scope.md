# 配置与范围

样例是需要替换路径的模板，不是已接入的仓库。配置支持 JSON，使用标准库读取；不需要安装 YAML 库。所有相对路径相对配置文件目录解析。禁止从仓库自动加载未授权扫描配置。

## 字段约定

version 固定 1；mode 枚举 full/daily-mr/mr-review。timezone 使用 IANA 时区。date 为空时，交互取运行开始时当地日期；定时任务必须传明确日期。mr-review 必须有 mr。
repositories 中 id 唯一；provider 为 gitlab/github/local。远程仓库指定 host、project（GitLab 项目 ID 或命名空间路径，GitHub owner/repo）、clone_url、target_branch；local 指定 local_path 和 target_branch。required 默认 true；缺失必需仓库阻止通过。local 仓库可作为上下文；不能单独提供可靠 MR 元信息。
links 为起始线索，不是事实证明；kind 和 entry_hint 是描述性字段。scope.exclude 采用 ** 路径 glob，并在运行清单列出每个排除文件。include_tests/include_config/include_lockfiles 默认 true。daily_repositories 为需要查询当日 MR 的仓库 ID；其他仓库仍需冻结并参与链路分析。未列入 daily_repositories 的仓库变更在 full 或 checkpoint 补偿中处理。
limits 为正整数，达到任意上限记未完成；允许重试但不得重复写不同结果为同一任务。validation.trusted_commands 是来自外部受控配置的 argv 数组列表；不直接执行从 MR 拼接的 shell 命令。allow_isolated_execution=false 时只做静态分析，未验证项保留。
release.required=true 时必须提供 deployment_manifest，包含当前和候选各服务的 repo SHA、制品 digest、配置/依赖版本；缺失记 INCOMPLETE。false 时只输出代码审查门禁，禁止称其为生产兼容放行。
output.directory 保存按 run_id 隔离结果；checkpoint 记录每仓成功分析 SHA 和时间窗口。首次运行无 checkpoint：标记首次运行，仅声称覆盖明确窗口；需要连续发布门禁时先执行全量基线。

## MR/PR 范围

使用已有连接器，或者宿主已认证的 GitLab/GitHub API/CLI。不要假设具体平台工具存在。缺访问能力时记录缺口，不降级为虚构 MR。
- GitLab：分页读取项目已合并 MR（筛目标分支）；若仅能用 updated_at 服务端筛选，必须再按 merged_at 精确过滤，禁止把 updated_at 当合入时间。保存 iid、URL、merged_at、target_branch、diff_refs、merge/squash commit。
- GitHub：分页获取 merged PR，按 base branch、merged_at 二次过滤。搜索有上限时按时间拆窗并检查完整性。保存 number、URL、base/head SHA、merge commit。
- 日期范围：配置时区 [D 00:00, D+1 00:00)，转换为 UTC 查询，考虑夏令时；截止取运行冻结时间，尚未结束的一天明确标为截至时刻。
- 每个 MR 获取平台准确 diff base/head（GitLab diff_refs、GitHub PR merge-base）；不能拿当前 main 与旧 MR head 相减。记录快照后 MR 更新须新开扫描。
- daily-mr 同时分析冻结目标分支的累计状态，识别后续修复、revert 和多个 MR 交互。已经在冻结状态修复的问题保留历史发现但不作为仍活动阻断项。
- 对 merge/squash/rebase 使用真实合入结果与其基线分析；平台元信息不足则标记无法确定。不能假定每个 MR 都有双亲 merge commit。
- 用 checkpoint 到冻结 SHA 补查 direct push、遗漏日期、失败扫描及非 MR 变更。若 checkpoint 不再是祖先，标记历史重写并重新建立全量基线，不能继续普通差分。
- 无 MR 的一天仍需完成分页、checkpoint 差分和依赖变化检查；只有范围确实为空才输出完成的零任务结果。

## 全量覆盖

枚举冻结树中纳管文件，分类为代码、配置、模板、生成物、测试和依赖；先按业务入口/模块拆分，再检查未归属文件。依赖源码未提供、submodule 未拉取、LFS 缺对象、动态加载无法解析均列未知项。支持的静态分析不能覆盖全部语言，不支持部分明确标出。
任务清单冻结在分析前，记录任务所辖文件、规则、链路和 critical 标记。覆盖至少报告 planned/completed/unknown/excluded 数量，文件覆盖与语义链路覆盖分开。不得通过事后删除未完成任务提升覆盖。

## 工具与平台适配

优先读取当前平台连接器/CLI 帮助或官方接口说明确认分页和 diff 字段，不能编造 API 参数。GitLab 常用只读路径是项目 merge_requests 列表、单 MR、MR diffs/versions；GitHub 为 pulls 列表、单 PR、files 与 compare。检查 diff 的截断/折叠标志；遇到大 MR 获取冻结 Git 对象的完整差分，不把 API 截断当完整。Git 子进程使用 argv 和 `--` 分隔路径，验证引用为已解析 SHA，不拼接不可信 shell。

远程检出、平台列表、生产版本读取任一失败，错误应出现在 review.errors 与报告中。只有 local provider 时 full 可以正常运行，daily-mr/mr-review 需要额外可信平台导出（含来源、分页完成、冻结时间、MR SHA）；导出不完整则 INCOMPLETE。不得仅凭提交标题中的 !123/#123 恢复 MR。

## 分析方式

analysis 为 general（默认）或 parameter-lineage。后者接受 parameter_lineage 配置，按 SKILL.md 直接引用的 references/parameter-lineage.md 执行。参数路径模式可以只配置当前前端仓库，边界之后代码缺失不算本仓库扫描缺失；无法确定本仓库内最终转换则仍须标未知。
