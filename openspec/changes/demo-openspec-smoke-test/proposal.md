## Why

This repository has OpenSpec initialized, but we have not yet verified the full artifact-guided workflow from change creation through validation. A small smoke-test change lets us confirm the project can create proposal, spec, design, and task artifacts cleanly before we use OpenSpec for real feature work.

## What Changes

- Add a demo OpenSpec change that exercises the standard proposal, design, specs, and tasks flow in this repository.
- Define a minimal capability for validating that a change can be scaffolded, documented, and marked ready for implementation.
- Keep the scope limited to workflow artifacts only, with no production code or runtime behavior changes.

## Capabilities

### New Capabilities
- `workflow-smoke-test`: Define the minimum artifact set and validation expectations for a trial OpenSpec change in this repository.

### Modified Capabilities

None.

## Impact

- Affects the OpenSpec workflow artifacts under `openspec/changes/`.
- Confirms the repository can use the installed OpenSpec CLI and Codex integration as expected.
- Does not affect application code, APIs, runtime dependencies, or shipped behavior.
