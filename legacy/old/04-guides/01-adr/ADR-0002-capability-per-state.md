# ADR-0002 — One capability owns each meaningful processing state

**Status:** Accepted  
**Decision scope:** OntoBDC state-machine transitions and transformation responsibilities

## Context

Statecharts make workflow order explicit, but they do not by themselves prevent the implementation from collapsing back into large transition handlers or adapters.

OntoBDC needs a decomposition rule that keeps orchestration separate from transformation logic and makes each meaningful processing outcome independently executable, testable, and replaceable.

Large adapters historically accumulated unrelated responsibilities such as semantic graph traversal, payload assembly, HTML rendering, runtime script generation, annotation wiring, and schedule-board behavior. Even when those responsibilities were executed in a valid order, their co-location made change risky and obscured which code was responsible for producing a specific state.

The current Page architecture instead uses small transformation capabilities and thin handlers. Generic capabilities may be reused by different entity machines through context adapters when the behavior is genuinely the same.

## Decision

Each meaningful processing state that requires work to be achieved MUST have one capability that owns the responsibility for producing and checking that state.

The capability is the unit of transformation. It SHOULD:

- have one clearly stated responsibility;
- receive the context required for that responsibility;
- perform the transformation or side effect associated with the state;
- expose whether the target condition is satisfied when the capability contract supports checking;
- return or expose the artifacts necessary for the following transition;
- be testable without executing unrelated states of the outer machine.

State-machine transition handlers MUST remain thin. They may resolve the appropriate capability, adapt context, invoke it, and translate its result into the machine transition, but they MUST NOT become an alternative location for substantive business logic.

A capability MAY be generic and reused by multiple machines when its semantics are identical. Entity- or workflow-specific data MUST then be supplied through an explicit context adapter or equivalent boundary rather than by copying the capability.

A state that is intentionally marker-only or purely structural MAY omit substantive transformation behavior, but that fact MUST be explicit in the state and capability contract. A placeholder MUST NOT be presented as a fully satisfied implementation.

## Consequences

### Positive

- Responsibility is traceable from state to implementation.
- Capabilities remain small enough to test and reason about independently.
- Generic behavior can be reused without duplicating workflow-specific implementations.
- State-machine handlers remain orchestration code rather than growing into new god-adapters.
- Missing functionality is easier to identify because a missing state owner is visible.
- Documentation and tests can map directly to the capability that implements a requirement.

### Negative

- The number of capability classes and files increases.
- Poorly chosen state boundaries can create capabilities that are artificially small or excessively coupled through context.
- Reuse requires careful separation between generic semantics and entity-specific configuration.
- A capability-per-state structure can still omit legacy behavior if parity is not tracked separately.

## Rejected alternatives

### One capability per complete workflow

Rejected because it recreates the monolithic adapter problem under a different class name and makes individual states difficult to verify.

### Business logic in transition handlers

Rejected because handlers then become a second, less visible implementation layer and the state-to-capability mapping stops being reliable.

### Duplicate entity-specific capabilities for identical behavior

Rejected because duplication causes behavior to diverge between machines and increases the surface that must be migrated and tested.

## Compliance

A state-machine implementation complies with this ADR when:

1. every state that represents substantive work has an identifiable owning capability;
2. the capability has a single dominant responsibility;
3. transition handlers contain orchestration rather than business logic;
4. reusable behavior is shared rather than copied when semantics are identical;
5. workflow-specific configuration is supplied through an explicit context boundary;
6. marker-only or stub behavior is declared as such.

## Related documentation

- [ADR-0001 — Statecharts as the canonical execution model](ADR-0001-statecharts-as-canonical-execution-model.md)
- [Page generation architecture](../page-generation.md)
- [Page transformation capability reference](../../05-reference/02-capabilities/page/transformation/index.md)
