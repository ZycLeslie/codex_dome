---
name: pom-version-governance
description: Audit and consolidate duplicated Maven POM version definitions and transitive dependency drift across multi-module projects (SDK, gateway, microservices). Use when users ask to “整理 pom”, “统一依赖版本”, “检查重复定义的 pom”, “治理 Maven 版本漂移”, “排查组件间接引入的依赖”, or need to find duplicate/conflicting dependency, plugin, property, or transitive versions before centralizing them into parent POM/BOM.
---

# POM Version Governance

Identify repeated and conflicting Maven version definitions, then drive them into a centralized governance model (`dependencyManagement`, `pluginManagement`, and shared `properties`).

Use three passes:

1. Static POM audit:
   - Read explicit `dependencies`, `dependencyManagement`, `plugins`, and `properties`.
2. Project component propagation audit:
   - Trace what `gateway`, microservices, or starters inherit indirectly through internal modules such as `sdk`, shared components, or platform libraries.
3. Effective dependency tree audit:
   - Run Maven dependency resolution to catch dependencies that are introduced indirectly through SDKs, gateways, starter modules, and other internal components.

## Workflow

1. Run the scanner to collect repeated definitions, component propagation paths, and resolved dependency trees:

```bash
python3 scripts/audit_pom_versions.py --root <project-root>
```

2. Focus on `Conflicting Version Definitions` first:
   - Same `groupId:artifactId` with multiple versions.
   - Same property key with different values.

3. Then handle `Repeated Identical Definitions`:
   - Same dependency/plugin version repeated in many child POMs.
   - Same property key/value copied across modules.

4. Review `Project Component Propagation Analysis`:
   - Dependencies that are not declared locally but are introduced by another internal component.
   - Paths such as `gateway -> sdk -> some-lib` that explain where the dependency really comes from.

5. Review `Effective Dependency Tree Analysis`:
   - Same artifact resolved to different versions across modules.
   - Dependencies that are not declared locally but are introduced transitively through another component.
   - Maven conflict mediation hints showing where one transitive version was dropped in favor of another.

6. Produce a consolidation change plan:
   - Create or confirm a root parent/BOM.
   - Move shared versions to root `dependencyManagement` and `pluginManagement`.
   - Keep shared version properties in one place.
   - Remove child-level explicit versions that are already managed.
   - Add exclusions or align upstream component versions when indirect imports are the real source of drift.

## Scanner Commands

1. Basic scan:

```bash
python3 scripts/audit_pom_versions.py --root .
```

2. Tighten candidate threshold (only show entries repeated 3+ times):

```bash
python3 scripts/audit_pom_versions.py --root . --min-occurrences 3
```

3. Require Maven transitive scan to succeed:

```bash
python3 scripts/audit_pom_versions.py --root . --transitive-mode required
```

4. Component-only mode when Maven tree resolution is unavailable:

```bash
python3 scripts/audit_pom_versions.py --root . --transitive-mode off
```

5. CI mode (non-zero exit when conflicts exist):

```bash
python3 scripts/audit_pom_versions.py --root . --fail-on-conflict
```

6. Export machine-readable output:

```bash
python3 scripts/audit_pom_versions.py --root . --format json --output pom-version-audit.json
```

## Interpretation Rules

1. Dependency conflict:
   - Same `groupId:artifactId` with different versions across modules.
   - Treat as highest priority because runtime/classpath behavior may diverge.

2. Plugin conflict:
   - Same `groupId:artifactId` plugin with different versions.
   - Treat as build stability risk across services.

3. Property conflict:
   - Same property key appears with different values.
   - Resolve by choosing one source of truth in parent/BOM.

4. Effective dependency conflict:
   - Same dependency resolves to different versions in different modules after Maven applies transitive resolution.
   - Treat as high priority because it reflects the real classpath seen by each component.

5. Indirect dependency drift:
   - A service or gateway does not declare the dependency, but receives it through SDK/starter/internal-component transitive import.
   - Fix at the upstream owner or with BOM/exclusion alignment, not only in the leaf module.

6. Component propagation path:
   - The report shows which internal component introduced the dependency and the full path.
   - Use this to decide whether the fix belongs in `sdk`, a shared starter, or the root BOM.

7. Maven mediation hint:
   - Maven reports an omitted transitive node because another version won conflict resolution.
   - Use this to locate which component is introducing the losing version.

8. Identical repetition:
   - Not an immediate bug, but indicates poor maintainability.
   - Consolidate to reduce upgrade cost and drift risk.

## Consolidation Strategy for SDK + Gateway + Microservices

1. Define one governance root:
   - Root parent POM or dedicated BOM module.
2. Centralize shared libraries:
   - Framework BOM imports and common runtime dependencies.
3. Centralize build plugins:
   - Compiler/surefire/failsafe/jacoco/checkstyle versions.
4. Keep only module-specific versions local:
   - A version should remain local only if truly module-exclusive.
5. Align upstream components:
   - If `gateway` pulls a version through `sdk`, prefer fixing the `sdk` or root BOM rather than overriding each consumer.
6. Re-run scanner after cleanup:
   - Ensure conflicts are gone and repetitive definitions reduced.

## Guardrails

1. Do not remove a child version blindly unless the parent/BOM manages it.
2. Preserve intentionally pinned module-specific versions with a comment/rationale.
3. Prefer `dependencyManagement` over copying versions into each child dependency declaration.
4. Do not “fix” an indirect dependency only in one leaf service if the same drift is introduced by a shared SDK/starter.
5. Use exclusions carefully:
   - Add them only after identifying the upstream path that introduces the unwanted transitive dependency.
6. Prioritize behavior safety: resolve conflicts before deduplicating same-version repetitions.
