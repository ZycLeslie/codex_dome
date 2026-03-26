## ADDED Requirements

### Requirement: Demo change includes implementation-ready artifacts
The repository SHALL allow a demo OpenSpec change to define the standard implementation-ready artifact set for a trial workflow run, including proposal, design, specification, and tasks documents.

#### Scenario: Demo change is fully scaffolded
- **WHEN** a user creates the `demo-openspec-smoke-test` change
- **THEN** the change contains proposal, design, specification, and tasks artifacts under `openspec/changes/demo-openspec-smoke-test/`

### Requirement: Demo change remains isolated from production behavior
The system SHALL keep the workflow smoke test limited to OpenSpec artifacts so that validating the process does not require application code changes or runtime behavior changes.

#### Scenario: Smoke test avoids product code edits
- **WHEN** the demo change is reviewed
- **THEN** its scope is limited to files under `openspec/changes/demo-openspec-smoke-test/`

### Requirement: Demo change can be validated before implementation
The repository SHALL support validating the demo change through the OpenSpec CLI so collaborators can confirm the workflow is ready for future real changes.

#### Scenario: Demo artifacts satisfy CLI validation
- **WHEN** a user runs the OpenSpec validation flow for `demo-openspec-smoke-test`
- **THEN** the CLI reports the change is structurally valid and ready for the next workflow step
