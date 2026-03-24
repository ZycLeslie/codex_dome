# OpenSpec in This Repository

This repository now uses **OpenSpec** as its primary specification workflow.

## What changed

- OpenSpec was initialized with Codex support.
- New work should use `openspec/changes/` instead of the old ad-hoc `specs/` workflow.
- Existing feature specs are being migrated into OpenSpec-style artifacts.

## Default workflow

1. Propose a change
2. Refine proposal / specs / design / tasks
3. Implement
4. Archive the change

Typical command flow with Codex:

- `/opsx:propose <idea>`
- `/opsx:apply`
- `/opsx:archive`

## Repository-specific guidance

- Use `openspec/changes/` for active changes.
- Use `openspec/changes/archive/` for completed and archived changes.
- Treat legacy `specs/` content as migration source material, not the long-term source of truth.

## Current migrated feature

The YAML → Cypher query generator feature currently has legacy material under:

- `specs/002-yaml-cypher-query-generator/`

It should be treated as a candidate for migration into an OpenSpec change/archive structure.
