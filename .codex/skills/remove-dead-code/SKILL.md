---
name: remove-dead-code
description: Safely identify and remove dead or unused code, orphaned methods, and cascading unreachable call chains in source repositories. Use when Codex needs to delete 废弃代码/死代码, build a reachability/call graph, protect public APIs, framework callbacks, generated endpoints, and interfaces declared in YAML/OpenAPI/Swagger/RPC configs before editing code.
---

# Remove Dead Code

Remove only code that is proven unreachable from every protected entry point. Treat missing textual callers as a clue, not proof.

## Quick Start

1. Treat the current workspace as the repository unless the user gives another path.
2. Scan YAML/JSON-declared interfaces:
   `python3 .codex/skills/remove-dead-code/scripts/find_api_roots.py . --output .codex/dead-code/api-roots.json --markdown .codex/dead-code/api-roots.md`
3. Build or refresh a method/function inventory. If available, use `$index-repo-methods` first, then inspect likely callers in source.
4. Build a call graph from code search, language tooling, IDE/language-server output, or project-native static-analysis tools.
5. Compute reachability from protected roots. For a hand-built graph, use:
   `python3 .codex/skills/remove-dead-code/scripts/reachability.py .codex/dead-code/call-graph.json --markdown .codex/dead-code/reachability.md`
6. Delete only evidence-backed candidates in small batches, then run compile/tests/linters after each batch.

## Protected Roots

Always mark these as live roots before calculating dead code:

- API endpoints declared in source annotations or route tables.
- Interfaces declared in YAML/JSON files, including OpenAPI, Swagger, AsyncAPI, gateway route files, RPC descriptors, and generated API specs.
- Source methods that match YAML `operationId`, `x-handler`, `x-controller`, route paths, generated `*Api` interfaces, or implementations of generated interfaces.
- Framework callbacks and reflection entry points: schedulers, message listeners, event handlers, lifecycle hooks, dependency-injection factories, serializers/deserializers, ORM hooks, migrations, CLI/main entry points, plugin/SPIs, and template/view handlers.
- Public/exported library APIs when external consumers may call them.
- Symbols referenced from configs, scripts, templates, XML/properties/YAML, dependency injection by name, or generated code.

If a YAML-declared interface cannot be mapped to one source method confidently, keep the likely controller/interface/service code and mark it `uncertain`, not dead.

For framework-specific root patterns, read `references/protected-roots.md` only when the repository language/framework is unclear or the first scan finds risky candidates.

## Cascade Rule

Use reachability, not simple caller counts:

- Model each method/function/constructor as a node and each call as `caller -> callee`.
- Compute `live = transitive_closure(protected_roots)`.
- A node is a delete candidate only when it is outside `live` and is not protected or uncertain.
- If `a` calls `b`, and `a` is not reachable from any protected root, both `a` and `b` are dead unless `b` is also reachable from another live root.
- Shared helpers are live when at least one live caller reaches them.
- Cycles are dead only when the whole strongly connected component has no path from protected roots.

When deleting incrementally, remove dead callers before their dead callees, or remove an entire dead component in one patch.

## Evidence Checklist

For every candidate, record:

- Symbol, file, line, and containing class/module.
- Why it is unreachable from protected roots.
- All known callers, grouped as live, dead, test-only, or unresolved.
- YAML/interface evidence checked: operation IDs, paths, generated API interfaces, handler/controller references.
- Config/reflection searches checked with `rg` for symbol names, route paths, operation IDs, bean names, and string references.
- Verification command to run after deletion.

Do not delete candidates with unresolved dynamic callers unless the user explicitly accepts that risk.

## Deletion Workflow

1. Create a short deletion plan grouped by confidence: `safe`, `cascade`, and `uncertain/keep`.
2. Edit only `safe` and high-confidence `cascade` groups first.
3. Prefer deleting whole unreachable classes/modules when all members are dead and no config/serialization/framework reference exists.
4. Update tests, generated snapshots, imports, dependency injection registrations, docs, and configs only when they directly reference deleted code.
5. Run the narrowest compile/test command that proves the touched area still works, then broaden when shared code or public APIs changed.
6. If verification fails, inspect the failure before restoring anything; it may reveal a hidden root that should be protected.

## Output Expectations

Report deleted symbols and files, protected roots discovered from YAML/interfaces, candidates intentionally kept as uncertain, and verification results. If no safe deletion exists, return the evidence and a conservative recommendation instead of forcing a patch.
