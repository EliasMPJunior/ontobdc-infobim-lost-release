# ADR-0003 — Capability and handler discovery by convention

**Status:** Accepted  
**Decision scope:** Runtime discovery of capabilities, handlers, builders, and related extension points

## Context

OntoBDC is designed to extend through semantic types, capabilities, builders, handlers, and loaders. A central registry that manually maps every supported type or operation to an implementation creates a second source of truth alongside the implementation itself.

Manual registries tend to drift. Adding a class can require editing unrelated mapping code; renaming or moving an implementation can leave stale entries; different registries can encode slightly different views of the same extension surface. This becomes particularly fragile when multiple entity types follow the same architectural pattern.

The current Page subsystem already uses registration-free discovery. For example, a concrete semantic entity type is normalized and resolved to a handler class following the expected naming and package conventions. The loader therefore derives the implementation from the declared convention instead of consulting a manually maintained map.

## Decision

OntoBDC extension points SHOULD be discovered by convention through dedicated loaders rather than through central manual registries.

A loader MAY derive an implementation from information such as:

- the semantic type or entity local name;
- a normalized module or package segment;
- a required class or function naming pattern;
- the capability or handler category expected by the caller.

The convention MUST be deterministic and documented in the corresponding loader reference.

Implementations that participate in convention-based discovery MUST follow the expected package and naming contract. A loader MUST NOT compensate for arbitrary naming by accumulating aliases, hidden special cases, or a fallback registry unless a separate architectural decision explicitly introduces such behavior.

The caller remains responsible for the semantics of an unresolved implementation. If the operation requires a concrete implementation, resolution failure MUST be surfaced explicitly. If the caller's documented contract permits an unsupported semantic type to be skipped, that behavior MUST itself be explicit and observable.

Discovery logic belongs in loaders. Business logic MUST NOT depend directly on hard-coded lists of concrete implementations when those implementations are intended to be extensible by convention.

## Consequences

### Positive

- Adding an implementation normally requires adding the implementation itself, not editing a central registry.
- Package structure and names become an executable extension contract.
- Loader behavior can be tested independently.
- Extension points remain open without accumulating large mapping tables.
- The risk of registry drift is reduced.
- Repeated architectural patterns can scale across entity types with less wiring code.

### Negative

- Naming and package conventions become part of the architecture and must be treated as stable contracts.
- A typo or misplaced implementation can cause discovery failure even when the class exists.
- Refactoring names or module paths may require coordinated changes to loader expectations and tests.
- Convention-based systems can become opaque if the convention is not documented precisely.

## Rejected alternatives

### Central implementation registry

Rejected because the registry duplicates information already encoded by the implementation's type, name, and location and can silently drift from the codebase.

### Registration decorators with global mutable state

Rejected because import order and registration side effects become part of runtime correctness and make discovery harder to inspect deterministically.

### Hard-coded dispatch chains

Rejected because `if`/`elif` or `match` chains over every supported concrete type couple the dispatcher to all implementations and require modification whenever an extension is added.

### Search every module dynamically without naming constraints

Rejected because unconstrained discovery is harder to reason about, can produce ambiguous matches, and weakens the architectural contract.

## Compliance

A discovery mechanism complies with this ADR when:

1. resolution is performed by a dedicated loader;
2. the lookup convention is deterministic and documented;
3. adding a conforming implementation does not require editing a central registry;
4. unresolved required implementations fail explicitly;
5. any permitted skip behavior is part of the caller's documented contract;
6. aliases and special cases do not silently accumulate inside the loader.

## Related documentation

- [ADR-0002 — One capability owns each meaningful processing state](ADR-0002-capability-per-state.md)
- [Page generation architecture](../page-generation.md)
- [Loader reference](../../05-reference/03-loader/index.md)
