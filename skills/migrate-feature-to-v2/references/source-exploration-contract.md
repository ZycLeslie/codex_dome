# Source Exploration Contract

Persist source exploration results before implementing the target feature. The goal is traceability: another agent or engineer should be able to understand how the legacy behavior was recovered without redoing the whole search.

## Default Location

Use the target repository's existing artifact convention when one exists. Otherwise write to:

```text
.ai-migrations/feature-migrations/<feature-slug>/source-exploration/
```

## Required Artifacts

### source-exploration.md

Human-readable summary of the source investigation.

Required sections:

```markdown
# <Feature> Source Exploration

## Source Access
- Repository:
- Access method: local checkout | generic git | CodeHub MCP | other
- Branch/ref/commit:
- Exploration timestamp:

## Entry Points
| Entry point | Type | Evidence | Notes |
|---|---|---|---|

## Behavior Baseline
| Scenario | Inputs/triggers | Outputs/results | Side effects | Evidence |
|---|---|---|---|---|

## Implementation Trace
| Layer/responsibility | Files/symbols | Callers/callees | Evidence |
|---|---|---|---|

## Data And Integration Evidence
| Concern | Evidence | Notes |
|---|---|---|

## Essence And Dross
| Item | Classification | Evidence | Migration decision |
|---|---|---|---|

## Legacy Smells
| Smell | Severity | Evidence | Migration decision |
|---|---|---|---|

## Open Questions
| Question | Why it matters | Proposed next step |
|---|---|---|
```

### source-evidence.json

Machine-readable evidence index. Keep it compact and deterministic.

Recommended shape:

```json
{
  "feature": "<feature-slug>",
  "source": {
    "repository": "<path-or-url>",
    "accessMethod": "local checkout | generic git | CodeHub MCP | other",
    "ref": "<branch-or-commit>"
  },
  "evidence": [
    {
      "id": "EV-001",
      "claim": "Short behavior or implementation claim",
      "kind": "code | test | schema | config | history | codehub-mcp | runtime | docs | essence | dross | bad-smell",
      "location": "repo-relative/path:line or MCP resource identifier",
      "symbol": "optional symbol name",
      "notes": "brief explanation"
    }
  ]
}
```

### feature-point-index.md

Required navigation map for split feature point files. Use it to avoid carrying the full source exploration context in memory.

Required sections:

```markdown
# <Feature> Feature Point Index

## Overview
- Source:
- Ref:
- Feature:

## Feature Points
| ID | Feature point | Markdown file | Status | Notes |
|---|---|---|---|---|

## Design Inputs
| Topic | Feature point files | Design impact |
|---|---|---|

## Open Questions
| Question | Related feature points | Decision needed |
|---|---|---|
```

### feature-points/<feature-point-slug>.md

Required for every coherent feature point discovered during source exploration. Keep each file focused and small enough to load independently.

Required sections:

```markdown
# <Feature Point>

## Summary
- ID:
- Status:
- Owner/domain:

## Entry Points
| Entry point | Evidence |
|---|---|

## Behavior
| Scenario | Inputs/triggers | Expected result | Side effects | Evidence |
|---|---|---|---|---|

## Data And Integration
| Concern | Evidence | Notes |
|---|---|---|

## Essence And Dross
| Item | Classification | Evidence | Migration decision |
|---|---|---|---|

## Legacy Smells
| Smell/problem | Classification | Evidence | Target decision |
|---|---|---|---|

## Target Design Hints
| Hint | Reason | Evidence |
|---|---|---|

## Open Questions
| Question | Why it matters | Needed before implementation? |
|---|---|---|
```

### legacy-smells.md

Required smell inventory. If no relevant smells are found, write `none found` with the evidence scope checked.

Required sections:

```markdown
# <Feature> Legacy Smells

## Summary
- Overall risk:
- Scope checked:

## Smell Inventory
| Smell/problem | Classification | Source evidence | Target decision | Verification |
|---|---|---|---|---|

## Deferred Items
| Item | Reason deferred | Risk | Follow-up |
|---|---|---|---|
```

### Supporting Artifacts

Create only when useful:

- `search-log.md`: high-signal searches and why they mattered.
- `candidate-files.txt`: files inspected or rejected.
- `call-trace.md`: entry point to domain/persistence/integration call chain.
- `codehub-mcp-evidence.md`: CodeHub MCP queries, resources, branch/ref details, and evidence IDs.

## CodeHub MCP Evidence Rules

When the source repository is a CodeHub URL or the user identifies it as CodeHub:

- Use the matching CodeHub MCP for source discovery.
- Record the MCP server/tool identity, repository identifier, branch/ref, and resource IDs or query parameters needed to reproduce the evidence.
- Do not replace CodeHub MCP evidence with generic Git, browser scraping, or raw HTTP unless the user explicitly approves a fallback.
- If CodeHub MCP is unavailable, stop before source exploration and ask the user to enable or install the correct MCP.

## Quality Bar

- Every recovered behavior in the migration record should point to at least one evidence item.
- Every meaningful feature point should have one focused Markdown file and an entry in `feature-point-index.md`.
- The migration design should cite feature point Markdown files rather than raw search output whenever possible.
- Every important essence/dross decision should point to evidence and a migration decision.
- Every severe smell or defect discovered in the feature path should be recorded with a remediation or deferral decision.
- Label uncertain claims as assumptions.
- Prefer source tests, schemas, configs, and externally visible entry points over comments.
- Keep raw source excerpts short; cite locations instead of copying large blocks.
