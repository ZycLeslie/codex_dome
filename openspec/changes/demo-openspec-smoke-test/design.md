## Context

This change is a repository-level smoke test for the newly installed OpenSpec workflow. The repository already contains an `openspec/` directory and Codex integration, so the goal is to confirm that a new change can move from scaffold to implementation-ready artifacts without touching application code.

## Goals / Non-Goals

**Goals:**
- Prove that this repository can create the standard OpenSpec artifacts for a new change.
- Keep the trial isolated to documentation and workflow validation inside `openspec/changes/`.
- Produce artifacts that can be validated by the OpenSpec CLI and are ready for a later `/opsx:apply` run.

**Non-Goals:**
- Changing runtime behavior in the Chrome extension or Java module.
- Introducing new dependencies, build steps, or deployment changes.
- Defining a long-term product feature beyond this workflow validation exercise.

## Decisions

1. Create a dedicated demo change instead of reusing an existing feature proposal.
   Rationale: This keeps the smoke test low-risk and avoids mixing trial workflow artifacts with active product work.
   Alternative considered: Start with a real product feature. Rejected because the user asked to try OpenSpec itself first.

2. Scope the capability to artifact creation and validation only.
   Rationale: The shortest path to confidence is to verify that proposal, spec, design, and tasks can be generated and accepted by the CLI.
   Alternative considered: Include implementation tasks against product code. Rejected because it would blur workflow verification with feature delivery.

3. Treat successful validation as the completion signal for this demo change.
   Rationale: The change exists to prove process readiness, so CLI-visible readiness is the correct success criterion.
   Alternative considered: Archive immediately after creation. Rejected because the user may want to inspect or apply the demo change first.

## Risks / Trade-offs

- [Risk] Demo artifacts may add noise to the active changes list. -> Mitigation: Use a clearly named `demo-openspec-smoke-test` change so it can be reviewed, applied, or archived deliberately.
- [Risk] Team members may mistake the demo capability for a production requirement. -> Mitigation: Keep the proposal, design, and tasks explicit that this is a workflow-only validation.
- [Risk] CLI validation may pass even though no business code is exercised. -> Mitigation: Treat this as a workflow smoke test only, not a product verification step.
