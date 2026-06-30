# Config Center Inventory

Use this guide when a migrated feature reads configuration from a third-party config center or platform-managed external config. Code migration is not complete until required config is listed, mapped, and verified or explicitly deferred.

## Applies To

Treat these as config-center surfaces:

- Nacos
- Apollo
- Spring Cloud Config
- Consul KV
- etcd
- ZooKeeper config nodes
- Vault, KMS-backed secrets, or secret managers
- Kubernetes ConfigMap/Secret
- platform config, feature flag, gray-release, or dynamic-rule systems
- any remote config SDK, annotation, bootstrap config, env indirection, or config refresh listener

## Required Artifact

Write:

```text
source-exploration/config/config-center-inventory.md
```

Required sections:

```markdown
# <Feature> Config Center Inventory

## Summary
- Config center present? yes | no | unknown
- Providers:
- Environments/profiles checked:
- Runtime blocker? yes | no

## Config Entries
| Key | Provider | Namespace/group/app | Profile/env | Source location | Current/default value | Target value/source | Required? | Sensitive? | Owner | Verification |
|---|---|---|---|---|---|---|---|---|---|---|

## Dynamic Behavior
| Key or group | Refresh mode | Listener/effect | Fallback behavior | Evidence |
|---|---|---|---|---|

## Target Mapping
| Source config | Target config | Transformation | Compatibility decision | Approval |
|---|---|---|---|---|

## Missing Or Blocked Config
| Config | Why needed | Blocker | Owner | Next action |
|---|---|---|---|---|

## Verification Plan
| Check | Command/scenario | Expected |
|---|---|---|
```

## Discovery Hints

Search for:

- config annotations and APIs: `@Value`, `@ConfigurationProperties`, `@NacosValue`, `@ApolloConfig`, `Environment`, `ConfigService`, `ConfigurableApplicationContext`
- bootstrap files: `bootstrap.yml`, `bootstrap.properties`, `application-*.yml`, `nacos`, `apollo`, `spring.cloud.config`
- feature flags and dynamic rules: `feature`, `flag`, `gray`, `switch`, `rule`, `limit`, `timeout`, `retry`
- secret and platform config references: `vault`, `secret`, `ConfigMap`, `Secret`, `env`, `process.env`
- frontend remote config, runtime env, generated config, CDN-injected config, and window globals

## Rules

- Do not copy old config center namespaces or groups into 2.0 unless they are an approved compatibility contract.
- Do not hard-code config values in target code just because the config center value is known.
- Mark secrets as sensitive; record existence, owner, and verification without exposing secret values.
- Record dynamic refresh semantics. A config that refreshes at runtime is not equivalent to one read only at startup.
- If a required target config is missing, mark the related package blocked until the config is created, mapped, or explicitly deferred.
