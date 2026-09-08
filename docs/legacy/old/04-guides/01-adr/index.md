# Architecture Decision Records

Architecture Decision Records (ADRs) capture significant architectural decisions for OntoBDC and the reasons behind them.

The architecture pages describe how the current system is organized. ADRs describe why a particular organization or constraint was chosen, which alternatives were rejected, and what consequences follow from the decision.

## Status vocabulary

- **Proposed** — under consideration and not yet normative.
- **Accepted** — current architectural rule.
- **Deprecated** — retained for historical context but no longer recommended.
- **Superseded** — replaced by a later ADR, which must be linked from the record.

Accepted ADRs are normative for new implementation work unless a later ADR explicitly supersedes them.

## Records

| ADR | Decision | Status |
| --- | --- | --- |
| [ADR-0001](ADR-0001-statecharts-as-canonical-execution-model.md) | Statecharts as the canonical execution model | Accepted |
| [ADR-0002](ADR-0002-capability-per-state.md) | One capability owns each meaningful processing state | Accepted |
| [ADR-0003](ADR-0003-capability-discovery-by-convention.md) | Capability and handler discovery by convention | Accepted |
| [ADR-0004](ADR-0004-no-silent-fallbacks.md) | No silent fallbacks | Accepted |

## Relationship to other documentation

- [Architecture](../index.md) describes the current runtime organization.
- [Concepts](../../02-concepts/index.md) defines the vocabulary used by the architecture.
- [Reference](../../05-reference/index.md) documents concrete states, capabilities, loaders, handlers, and executable contracts.

An ADR should not duplicate reference documentation. When implementation details change without changing the architectural decision, update the corresponding architecture or reference page rather than rewriting the ADR.