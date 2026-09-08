# ADR-0004 — No silent fallbacks

**Status:** Accepted  
**Decision scope:** Runtime resolution, transformation, generation, validation, and migration behavior

## Context

OntoBDC relies on explicit semantic contracts. A missing implementation, unresolved dependency, unsupported state, incomplete transformation, or failed invariant can invalidate downstream results even when the outer workflow continues to run.

Silent fallbacks are especially dangerous in this architecture because they can make a partial or degraded implementation appear complete. A loader may fail to find the expected handler and quietly select another path; a transformation may return an empty structure when required data was not produced; a generator may skip an asset and still report success; or a migration may omit behavior while preserving the same outer entry point.

These failures are difficult to distinguish from intentional defaults after the fact. They also undermine statecharts and capability boundaries: an explicit state has little value if the capability that is supposed to achieve it can silently substitute different semantics.

The current architecture already exposes intentionally incomplete stages rather than hiding them. For example, placeholder or stub capabilities may report an unsatisfied check or produce only a state marker while the documentation states that the behavior is not yet implemented.

## Decision

OntoBDC MUST fail explicitly when a required architectural contract cannot be satisfied.

A component MUST NOT silently substitute a different implementation, artifact, data source, execution path, or semantic result merely to allow the workflow to continue.

This rule applies in particular to:

- capability, handler, builder, and loader resolution;
- missing required inputs or dependencies;
- unsupported state transitions;
- generation of required artifacts;
- validation failures;
- migration and refactoring where previous behavior has not yet been reimplemented;
- semantic queries whose required result cannot be established.

When failure prevents the requested operation from being correct, the implementation MUST raise or otherwise surface an explicit failure at the boundary where the contract is violated.

### Explicit defaults are not silent fallbacks

A deterministic default is permitted when the default is part of the documented contract of the operation. Examples include a documented language default or an explicitly defined empty collection representing the semantic absence of optional relations.

The distinction is normative:

- **default:** a specified value or behavior that is valid according to the contract;
- **fallback:** a substitute path used because the intended contract could not be satisfied.

A fallback is prohibited unless it is itself explicitly specified as part of the contract and remains observable to the caller.

### Explicit stubs are not silent fallbacks

Incomplete implementation may be represented by a stub during development when all of the following are true:

1. the stage remains explicit in the state machine or architectural contract;
2. the implementation is documented as incomplete;
3. its satisfaction status does not falsely claim completion;
4. downstream code does not interpret the stub as equivalent to the final behavior.

A stub that silently returns plausible output and allows the system to present the state as complete violates this ADR.

## Consequences

### Positive

- Missing functionality fails near its source instead of corrupting downstream behavior.
- Partial migrations are harder to mistake for complete refactors.
- Loader and capability contracts remain trustworthy.
- Tests can assert failures instead of reverse-engineering degraded output.
- State-machine completeness remains meaningful.
- Operational logs provide evidence of the actual violated contract.

### Negative

- Workflows may stop more often during development instead of producing partial output.
- Existing callers that relied on permissive behavior may require correction.
- Explicit error handling and tests increase implementation work.
- Optional behavior must be specified carefully so that legitimate absence is not confused with failure.

## Rejected alternatives

### Best-effort execution by default

Rejected because the caller cannot reliably distinguish a correct result from a degraded result unless every degradation is separately tracked.

### Empty output on failure

Rejected because an empty object, list, string, or file can also be a valid domain result and therefore hides the distinction between absence and failure.

### Generic implementation fallback

Rejected as a default policy because a generic implementation may not preserve the semantics required by the concrete entity or state. Generic behavior is allowed only when the architecture explicitly defines the generic capability as the correct implementation for that contract.

### Logging a warning and continuing

Rejected when the missing contract is required for correctness. A warning is appropriate only for behavior explicitly defined as optional.

## Compliance

An implementation complies with this ADR when:

1. required resolution failures are surfaced explicitly;
2. required transformations do not return substitute success values after failure;
3. defaults are documented as part of the contract;
4. optional behavior is distinguishable from failed required behavior;
5. stubs remain visibly incomplete;
6. tests cover the expected failure path for required contracts.

## Related documentation

- [ADR-0001 — Statecharts as the canonical execution model](ADR-0001-statecharts-as-canonical-execution-model.md)
- [ADR-0003 — Capability and handler discovery by convention](ADR-0003-capability-discovery-by-convention.md)
- [Page generation architecture](../page-generation.md)
