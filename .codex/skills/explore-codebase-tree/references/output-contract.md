# Explore Codebase Tree Output Contract

Use this reference when the user needs an explicit artifact shape or when adapting the script output.

## Markdown shape

```markdown
# Codebase Explore Tree

## Summary

- Repository: `/absolute/path`
- Source files scanned: 42
- Callables detected: 318

## Functional Category Tree

- Business Services and Workflows (84)
  - `src/orders/service.ts` (12)
    - L34 `OrderService.createOrder(input)` [method] - Likely business workflow logic.
    - L89 `OrderService.cancelOrder(id)` [method] - Likely business workflow logic.

## Repository File Tree

- `src/`
  - `orders/`
    - `service.ts` (12)
      - L34 `OrderService.createOrder(input)` [Business Services and Workflows]

## Repeated Callable Names

- `validate`: 5 occurrences

## Files Without Detected Callables

- `src/orders/schema.json`
```

## JSON shape

```json
{
  "repository": "/absolute/path",
  "generated_at": "2026-05-19T12:00:00Z",
  "summary": {
    "files_scanned": 42,
    "callables_detected": 318,
    "languages": {"TypeScript": 210},
    "categories": {"Business Services and Workflows": 84}
  },
  "callables": [
    {
      "id": "src/orders/service.ts:34:OrderService.createOrder",
      "name": "createOrder",
      "qualified_name": "OrderService.createOrder",
      "kind": "method",
      "language": "TypeScript",
      "file": "src/orders/service.ts",
      "line": 34,
      "owner": "OrderService",
      "signature": "createOrder(input: CreateOrderInput)",
      "category": "Business Services and Workflows",
      "purpose": "Likely business workflow logic.",
      "tags": ["create", "order", "service"]
    }
  ],
  "files": [
    {
      "file": "src/orders/service.ts",
      "language": "TypeScript",
      "callable_count": 12,
      "dominant_category": "Business Services and Workflows"
    }
  ]
}
```

## Quality expectations

- Prefer complete coverage over perfect semantic classification.
- Preserve source line numbers, signatures, owner/class names, and relative paths.
- Do not omit tests by default; tests are part of the executable behavior map.
- Skip generated, vendored, dependency, build, and cache directories unless the user explicitly asks for them.
- Keep the full generated artifact on disk instead of pasting a very large tree into chat.
