# Design

This migration does not redesign the YAML -> Cypher module itself. Instead, it captures the already-completed work in an OpenSpec-compatible archive shape.

## Approach

- Keep the implementation in `src/graph-query-cypher/`
- Preserve the legacy spec set in `specs/002-yaml-cypher-query-generator/` for traceability during transition
- Add OpenSpec repository scaffolding and archive metadata
- Point future work to `openspec/changes/`

## Trade-offs

- This is a pragmatic migration, not a full semantic rewrite of legacy specs into OpenSpec-native spec delta format
- It favors continuity and low risk over perfectly normalized OpenSpec artifacts
