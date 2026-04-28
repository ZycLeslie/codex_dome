# Java Startup Phase Map

Use this reference to classify evidence while analyzing Java microservice startup or restart-to-available latency.

## Timing Model

Cold startup usually follows:

`process/container start -> JVM first log -> Spring starting -> environment prepared -> context refresh -> dependencies ready -> web server listening -> app started -> readiness accepting traffic -> first successful traffic`

Restart-to-available usually adds:

`restart requested -> old instance unready/draining -> old process stop -> scheduler/restart delay -> container created -> process start -> startup path -> readiness -> routing/registry propagation`

Always identify which window the available evidence actually covers.

## Availability Markers

Prefer markers in this order:

1. First successful real traffic or synthetic transaction.
2. Readiness state accepting traffic, successful readiness probe, or actuator health `UP`.
3. Service registry/gateway/mesh marks instance routable.
4. Embedded server listening on the expected port.
5. Spring Boot `Started ... in N seconds`.

Markers 4 and 5 prove the Java process is up, but may not prove the service is externally usable.

## Common Log Markers

Spring Boot:
- `Starting <App> using Java`
- `No active profile set` or `The following profiles are active`
- `Started <App> in <seconds> seconds`
- `Application availability state LivenessState changed to CORRECT`
- `Application availability state ReadinessState changed to ACCEPTING_TRAFFIC`

Embedded servers:
- `Tomcat initialized with port(s)`
- `Tomcat started on port`
- `Netty started on port`
- `Undertow started`
- `Jetty started`
- `gRPC Server started`

Configuration and discovery:
- `Fetching config from server`
- `Located property source`
- `Nacos`, `Apollo`, `ConfigServicePropertySourceLocator`
- `Eureka`, `Consul`, `ServiceRegistry`, `Registered instance`

Database and migrations:
- `HikariPool-... - Starting`
- `HikariPool-... - Start completed`
- `Initialized JPA EntityManagerFactory`
- `Flyway`, `Migrating schema`, `Successfully applied`
- `Liquibase`, `ChangeSet`, `Database is up to date`
- `Hibernate Validator`, `HHH000204`, `HHH000400`

Messaging and external clients:
- Kafka consumer/producer start and metadata fetch
- RabbitMQ connection/channel creation
- Redis connection, Sentinel/Cluster discovery
- Elasticsearch/OpenSearch client initialization
- Feign/RestTemplate/WebClient TLS or DNS failures

Kubernetes and platform:
- Pod `Scheduled`, `Pulled`, `Created`, `Started`
- `Back-off restarting failed container`
- `Readiness probe failed`
- `Liveness probe failed`
- Container `startedAt` and `finishedAt`
- Deployment `Available`, `Progressing`, and rollout events

## Phase Diagnosis

Platform overhead:
- Evidence: gap before first Java log, pod events, image pull, scheduling, restart backoff.
- Common causes: large image, cold node pull, resource pressure, slow preStop, long terminationGracePeriod, crash loop backoff.
- Fix directions: smaller/layered image, pre-pulled images, resource requests, shorter graceful shutdown where safe, fix crash loop root cause.

JVM/process boot:
- Evidence: first process log to Spring `Starting`, Java agent logs, long silence before framework logs.
- Common causes: many Java agents, slow logging init, classpath scanning, container entropy or DNS lookup during init.
- Fix directions: review agents, class data sharing/AppCDS, reduce startup hooks, check JVM flags and logging appenders.

Configuration phase:
- Evidence: config center calls, profile/property source logs, retries/timeouts.
- Common causes: slow Nacos/Apollo/Config Server, DNS/TLS latency, unavailable metadata service, retry backoff.
- Fix directions: cache config, reduce startup-time remote calls, tune timeouts, check DNS and TLS reuse.

Spring context/bean creation:
- Evidence: context refresh logs, bean creation logs when debug enabled, actuator startup endpoint, APM spans.
- Common causes: broad component scan, expensive `@PostConstruct`, eager singletons, AOP/proxy creation, validators.
- Fix directions: narrow scans, move expensive work out of startup, lazy init selectively, Spring Boot startup actuator analysis, AOT/native only when justified.

Database and migrations:
- Evidence: Hikari, Hibernate, Flyway, Liquibase, lock waits, DB logs.
- Common causes: pool min-idle creation, schema validation, long migrations, migration locks, DNS/TLS, DB cold cache.
- Fix directions: split heavy migrations from service boot, reduce startup pool size, tune validation, monitor migration locks.

Warmup and dependency health:
- Evidence: cache preload, dictionary load, search index, MQ startup, downstream health checks.
- Common causes: synchronous cache warmup, health indicators blocking readiness, slow downstreams, large metadata loads.
- Fix directions: make noncritical warmup asynchronous, split readiness from deep dependency checks, cache snapshots, cap timeouts.

Readiness and routing:
- Evidence: readiness probe failures, initialDelay/period/failureThreshold, actuator readiness, registry/gateway timestamps.
- Common causes: conservative probe delays, health checks too strict, service registry propagation, service mesh endpoint update lag.
- Fix directions: tune probes to real startup behavior, expose readiness only after critical dependencies, reduce registry TTLs where safe, verify gateway/mesh endpoint propagation.

Shutdown/drain restart cost:
- Evidence: SIGTERM/preStop logs, old pod readiness false, graceful shutdown, connection drain, terminationGracePeriod.
- Common causes: long request drain, blocking shutdown hooks, message consumer rebalance, slow pool close.
- Fix directions: mark unready before drain, cap shutdown hooks, tune consumer shutdown, observe in-flight request completion.

## Evidence Confidence

High confidence:
- Exact timestamps around both phase boundaries from the same clock source.
- Direct readiness or traffic evidence for availability.

Medium confidence:
- Phase start/end inferred from adjacent framework logs.
- Cross-file timestamps with normalized time zones.

Low confidence:
- Only log order is known.
- Only Spring reported duration is available.
- Availability inferred from port listening or service process survival.
