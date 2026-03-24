# Proposal: migrate existing YAML Cypher query generator work into OpenSpec

## Why

This repository is adopting OpenSpec as the primary spec workflow. The existing YAML -> Cypher query generator work was authored in a legacy `specs/` structure and should be represented in the OpenSpec archive model so future changes can build on a consistent process.

## What changes

- Introduce OpenSpec into the repository
- Preserve the existing completed YAML -> Cypher generator work as an archived OpenSpec change
- Document that future work should use `openspec/changes/`

## Impact

- New contributors and coding agents will follow one primary spec workflow
- Existing implementation history remains intact
- Legacy specs can be migrated gradually rather than rewritten all at once
