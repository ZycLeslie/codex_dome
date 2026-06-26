# JVM 运行时监控 Skill

`monitor-jvm-runtime` 是一个用于监控在线 JVM 进程的 Codex skill，支持本机、虚机、Docker 容器和 Kubernetes Pod。它可以生成可审查的连接与采样命令，指导使用低风险工具采集运行时证据，并把采样结果汇总为监控分析报告。

## 支持能力

- 目标环境：本机、SSH 虚机、Docker 容器、Kubernetes Pod/Container。
- JVM 定位：PID、主类、jar 名称、进程命令匹配、服务名或 Java 用户。
- 监控模式：实时监控、定时监控/巡检、已有采样数据的报告分析。
- 工具类型：Spring Boot Actuator、Micrometer/Prometheus、`jcmd`、`jstat`、VisualVM/JMX、Arthas、限定时长的 JFR。
- 报告证据：Actuator `metrics`/`prometheus`/`threaddump`、GC 使用率、堆/Metaspace 压力、线程状态、Native Memory 标记、JFR 文件、Arthas 快照、容器或主机上下文。

## 目录结构

```text
monitor-jvm-runtime/
├── SKILL.md
├── README.md
├── README.zh-CN.md
├── agents/openai.yaml
├── references/jvm-runtime-monitoring-playbook.md
└── scripts/
    ├── build_monitor_plan.py
    └── summarize_monitor_data.py
```

## 快速开始

生成 Docker 容器的定时监控方案：

```bash
python3 scripts/build_monitor_plan.py \
  --environment docker \
  --container order-api \
  --process-match order-service.jar \
  --mode scheduled \
  --duration 10m \
  --interval 10s \
  --tool auto \
  --actuator-base-url http://127.0.0.1:8080/actuator \
  --out-dir /tmp/jvm-monitor
```

把 Actuator 作为 Spring Boot 服务的推荐监控基线：

```bash
python3 scripts/build_monitor_plan.py \
  --environment kubernetes \
  --namespace prod \
  --pod order-api-abc \
  --kube-container app \
  --mode scheduled \
  --duration 10m \
  --interval 10s \
  --tool actuator \
  --actuator-base-url http://127.0.0.1:8080/actuator \
  --out-dir /tmp/jvm-actuator-monitor
```

对 Kubernetes 中已经采集好的监控材料生成报告分析方案：

```bash
python3 scripts/build_monitor_plan.py \
  --environment kubernetes \
  --namespace prod \
  --pod order-api-abc \
  --kube-container app \
  --mode report-only \
  --out-dir /tmp/jvm-monitor-existing
```

汇总监控采样数据：

```bash
python3 scripts/summarize_monitor_data.py /tmp/jvm-monitor \
  --format markdown \
  --out /tmp/jvm-monitor-report.md
```

## 使用流程

1. 定义目标契约：环境、定位方式、JVM 选择器、监控模式、采样窗口、工具偏好和安全边界。
2. 使用 `build_monitor_plan.py` 生成命令方案。
3. 执行前审查命令，尤其是 attach、JMX、JFR、profiler、class histogram、heap dump 等动作。
4. 在目标环境中执行已确认的命令。
5. 将原始采样材料保存在带时间戳的目录中。
6. 使用 `summarize_monitor_data.py` 生成初步报告，并回到原始材料核实每个异常。
7. 输出最终报告：目标、采样窗口、工具、关键指标、发现、风险和下一步检查。

## 推荐的 Spring Boot Actuator 配置

如果是 Spring Boot 服务，并且需要长期、远程、低侵入监控，推荐安装 Actuator 和 Prometheus registry：

```xml
<dependency>
  <groupId>org.springframework.boot</groupId>
  <artifactId>spring-boot-starter-actuator</artifactId>
</dependency>
<dependency>
  <groupId>io.micrometer</groupId>
  <artifactId>micrometer-registry-prometheus</artifactId>
</dependency>
```

先暴露一组较小且受保护的端点：

```properties
management.endpoints.web.exposure.include=health,info,metrics,prometheus,threaddump
management.endpoint.health.show-details=when-authorized
management.server.port=8081
```

常用端点包括 `/actuator/health`、`/actuator/info`、`/actuator/metrics`、`/actuator/metrics/jvm.memory.used`、`/actuator/metrics/jvm.gc.pause`、`/actuator/metrics/jvm.threads.live`、`/actuator/prometheus` 和 `/actuator/threaddump`。

## 安全注意事项

- 不要在不可信网络上暴露未认证的 JMX。
- 不要公开暴露敏感 Actuator 端点。`env`、`configprops`、`logfile`、`heapdump`、`shutdown` 以及会修改运行状态的端点应限制给可信管理员使用。
- 在生产环境中 attach Arthas、启动 JFR、开启管理代理、触发 class histogram 或生成 heap dump 前，需要明确授权。
- 单次快照只能说明当前状态，不能直接当成趋势。
- 对 thread dump、系统属性、heap 字符串和环境变量中的密钥、token、请求内容、个人信息进行脱敏。
- 监控结束后清理 attach 工具、端口转发、临时隧道和临时采样文件。

## 更多细节

查看 `references/jvm-runtime-monitoring-playbook.md`，里面包含不同环境的命令模式、Arthas 和 VisualVM/JMX 使用建议、定时监控示例、指标解释规则和报告模板。
