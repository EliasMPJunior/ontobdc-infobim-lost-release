# ADR-0001 — Statecharts as the canonical execution model

**Status:** Accepted  
**Decision scope:** Multi-step OntoBDC processing and generation pipelines

## Context

OntoBDC performs transformations whose correctness depends not only on the final artifact but also on an ordered sequence of meaningful intermediate conditions. Examples include Surface generation, Page-data generation, Page publication, and Page runtime script generation.

Historically, orchestration was frequently embedded inside large adapters and procedural functions. In that form, ordering, intermediate state, retries, incomplete stages, and transition ownership were difficult to inspect independently. The code path itself became the only practical description of the process.

That model makes several failures easy to hide:

- a later step can execute even when a prerequisite has not actually been satisfied;
- intermediate behavior can disappear during refactoring without a visible change to the outer entry point;
- tests tend to exercise a large end-to-end adapter instead of a single transition;
- an implementation can appear complete even when only part of the original processing surface has been restored;
- orchestration logic becomes coupled to payload construction, rendering, I/O, and runtime bundling.

OntoBDC already models current Page-data and Page-script flows as explicit state machines, and the architecture documentation treats those machines as part of the executable contract.

## Decision

Every OntoBDC workflow that contains multiple semantically meaningful processing stages MUST express its orchestration as an explicit statechart.

The statechart is the canonical source of truth for:

- the valid states of the workflow;
- the ordering of processing stages;
- the transitions that may occur between those states;
- the point at which a workflow is considered complete.

States MUST describe observable processing outcomes or lifecycle conditions rather than incidental implementation steps.

Transition execution MUST be delegated to the capability or transition handler responsible for achieving the target condition. The state machine coordinates work; it MUST NOT absorb the substantive transformation logic that belongs to those components.

A workflow MUST NOT rely on an undocumented procedural sequence that exists only because functions happen to call one another in a particular order.

Incomplete states are permitted during development, but they MUST remain explicit. A stubbed state MUST be documented as incomplete and MUST NOT masquerade as a satisfied final implementation.

## Consequences

### Positive

- The pipeline becomes inspectable independently from implementation details.
- Missing stages are visible in the machine rather than hidden inside large functions.
- Each transition can be tested in isolation.
- State names provide a stable vocabulary for documentation, logs, tests, and debugging.
- Migration and refactoring can compare old and new behavior stage by stage.
- The system can represent intentionally incomplete work without pretending that the whole workflow is complete.

### Negative

- More explicit types, files, and transition definitions are required.
- Small workflows may appear more verbose than an equivalent procedural function.
- Changes to workflow semantics can require coordinated updates to state definitions, handlers, tests, and documentation.
- A statechart can still be incomplete; explicit orchestration does not by itself guarantee functional parity with a previous implementation.

## Rejected alternatives

### Procedural orchestration inside adapters

Rejected because control flow, transformation logic, I/O, and rendering become coupled and difficult to verify independently.

### A single generic pipeline with implicit ordered steps

Rejected because the sequence remains descriptive rather than executable and cannot express machine-specific lifecycle differences clearly.

### Inferring lifecycle only from generated files

Rejected because artifact existence alone cannot reliably represent all meaningful processing states, especially stubs, partial transformations, validation boundaries, and operations whose result is not a file.

## Compliance

A new multi-stage workflow complies with this ADR when:

1. its meaningful lifecycle states are explicitly declared;
2. valid transitions are represented in a statechart;
3. substantive work is delegated outside the machine definition;
4. incomplete states are visible rather than silently skipped;
5. tests can address individual transitions or states without requiring the entire outer workflow to run.

## Related documentation

- [State machines](../../02-concepts/state-machines.md)
- [Page generation architecture](../page-generation.md)
- [Page-data and Page-script state machine reference](../../05-reference/04-state-machines/index.md)
