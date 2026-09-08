# Entity Events

## Purpose

Entity Events are semantic events produced when the persisted data of an Entity changes.

They are not a fourth Presentation Event scope. The PresentationLayer still has the three historical scopes documented in `Presentation Event Scopes.md`:

- Component Event
- Presentation Global Event
- External Event

Entity Event is a separate event family concerned with Entity data lifecycle and mutation.

## Working definition for Sprint 7

An Entity Event records that an Entity's persisted semantic data changed.

The triggering change may originate from a command, capability, import, editor, synchronization process, deterministic worker or other authorized mutation path. The event describes the resulting Entity occurrence rather than the UI gesture that caused it.

Examples of the intended family include:

- EntityCreated
- EntityUpdated
- EntityDeleted
- EntityPropertyAdded
- EntityPropertyUpdated
- EntityPropertyRemoved
- EntityRelationAdded
- EntityRelationRemoved

The exact normative vocabulary and payload schema remain Sprint 7 work, but the architectural responsibility is clear: a change to Entity data must be capable of producing an Entity Event that other runtime actors can observe without coupling themselves to the mutation implementation.

## Data-change boundary

Entity Events are tied to changes in Entity data. They are distinct from:

- a browser click or input event;
- a Presentation Global Event such as EntitySelected;
- a statechart transition;
- a log record;
- a capability invocation itself.

For example, selecting an Entity in a Tile is a presentation occurrence. Updating one of that Entity's persisted properties is an Entity data occurrence. The latter belongs to the Entity Event family.

## Historical evidence recovered

The current Git index does not expose the exact old CRUD/Entity Event implementation by the literal name `EntityEvent`, but the repository history contains strong evidence that the underlying event architecture existed and was exercised.

### InfoBIM AECO event sourcing

InfoBIM WIP commit `535ed37fcf429b5d8374df5dd1522bb640d29e79`, dated 2026-01-25, is explicitly titled:

`feat(aeco): impl event sourcing, fix wrappers and add ADRs`

This establishes that persisted event-oriented data-change work existed historically. The visible diff returned by GitHub today is not sufficient to reconstruct the complete old event-store contract, so Sprint 7 must not invent details and attribute them to that implementation.

### Capability events and deterministic mutation/orchestration

InfoBIM WIP commit `ee4c3d178d9111fe7f7d9398367d05e11a6433e8` records the architectural decision that capabilities declare semantic output events and that deterministic FSM/workflow transitions react to those events.

The same historical line explicitly separates event from state: an occurrence may be emitted while a semantic state separately records the resulting condition.

### Concrete emitted events

InfoBIM WIP commit `ed76ac94a1c0d304fdbedff1749002b3c2e08d50` contains a working example in which `UHCSizingCapability` declares success and failure events and returns an `events` collection in its result.

That implementation is not itself an Entity Event implementation, but it proves that semantic events were represented as first-class capability outputs and actually emitted by executable code.

### OntoBDC deterministic pipeline event export

OntoBDC WIP commit `017666acba088bb4628907e98eb560675863cc82` explicitly records `event export` as part of the deterministic A3 parsed-to-dispatched pipeline.

Again, this is not proof of the exact Entity Event schema, but it confirms that runtime data processing and event production were already connected historically.

## Relationship to the three Presentation scopes

Entity Event describes what kind of semantic occurrence happened. The Presentation event scopes describe how far an event is relevant within or beyond a PresentationLayer.

Therefore the concepts are orthogonal.

An Entity Event may never reach a PresentationLayer at all.

If a PresentationLayer is interested in an Entity Event, it may translate or project that occurrence into a Presentation Global Event so relevant Tiles refresh or react.

If the Entity Event must cross a dDock boundary, it may be carried as an External Event.

The event must not be promoted merely because transport makes promotion possible. The historical golden rule still applies: the event moves up in scope only when its meaning moves up in scope.

## Expected Entity Event payload concerns

Sprint 7 must define the final contract. At minimum the design must evaluate whether Entity Events need:

- event identity;
- event type;
- Entity URI / stable identifier;
- Entity type/class;
- operation/change kind;
- changed predicate/property or relation when the event is granular;
- previous value when required for audit or reaction;
- resulting value when applicable;
- timestamp;
- producer/source identity;
- container/dataset/context identity;
- correlation/causation identity for a chain of deterministic operations;
- ordering/version information where concurrent or sequential mutations matter.

These fields are design questions, not all mandatory by default.

## Persistence and Event Sourcing

Entity Events do not automatically imply Event Sourcing.

Two separate questions must remain separate:

1. Should an Entity mutation emit a semantic event?
2. Should that event be durably persisted so state can be audited, replayed or reconstructed from events?

Historical InfoBIM work experimented with Event Sourcing, but Sprint 7 must decide persistence requirements explicitly rather than coupling basic Entity Event dispatch to Event Sourcing by default.

## Sprint 7 requirement

Entity Events are now part of the event work that must be resolved before Sprint 7 closes.

Sprint 7 must establish a working contract in which authorized mutations of Entity data can produce semantic Entity Events consistently, and consumers can react without depending directly on the concrete writer/storage/editor implementation.

The historical implementation should continue to be recovered where possible, because the concept existed before and reportedly reached a functioning state. Historical behavior is evidence; the Sprint 7 contract is the normative target.
