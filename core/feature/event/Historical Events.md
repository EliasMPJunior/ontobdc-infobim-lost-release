# Historical Events — OntoBDC WIP and InfoBIM WIP

This document records event-related architecture and implementations found in the Git history of:

- `EliasMPJunior/ontobdc-wip`
- `EliasMPJunior/infobim-wip`

It complements `feature/Events/README.md`, which describes the event mechanisms currently visible in the active OntoBDC / OntoBDC View implementation.

The material below is historical evidence. It must not be copied blindly into Sprint 7. Some concepts are clearly architectural precursors worth recovering; others were experiments or explicitly identified later as legacy coupling.

## 1. Presentation Layer / dDock: three-scope event model

A significant historical architecture record exists in OntoBDC WIP commit:

- `257becfe863d942677718f9c80f7593e8efcdc09`
- message: `docs: capture dDock/PresentationLayer/Tile architecture from domain conversations`
- date: 2026-08-08

The commit states explicitly that the documented dDock / PresentationLayer architecture includes a **three-scope event model** together with Dock, dDock, Agent, Bus, Bridge, Presentation Surface and Tile.

This is important because it shows that the current `Presentation Global Event` concept did not appear from nowhere. A broader event-scope model had already been discussed as part of the intended Presentation Layer architecture.

The historical documentation synthesized conversations from 2026-08-02, 2026-08-07 and 2026-08-08 and treated events as part of the communication contract among presentation actors rather than as browser callbacks.

### Architectural implication

The Sprint 7 event design should recover and verify the original three scopes before defining a new taxonomy. The current browser-level `entity-selected` and `show-details-requested` events should be compared against that earlier model instead of being treated as the entire event architecture.

The historical model is especially relevant to the distinction between:

- interaction internal to one Tile/component;
- communication among Tiles inside one Presentation Surface;
- communication beyond one Surface through Dock / dDock / Bus / Bridge actors.

The exact names and final semantics of the three historical scopes must be recovered from the historical document/code before being made normative again.

## 2. Presentation-event observability / debug log

OntoBDC WIP commit:

- `5600a23047fadfdcf03f031cf089149b7ceac8c5`
- message begins `feat(mobile)`
- date: 2026-08-10

The commit explicitly reports a **presentation-event debug log** in the mobile work together with the Presentation Surface and other interaction capabilities.

This is relevant independently of the mobile implementation itself. It demonstrates that presentation events were considered observable runtime objects worthy of explicit debugging/inspection, rather than ephemeral callbacks that disappear after execution.

### Architectural implication

Sprint 7 should consider event observability as part of the event contract: at minimum events should be inspectable enough to identify type, source, target/scope and payload. Whether events are persisted is a separate decision; debug observability does not imply event sourcing.

## 3. Legacy `infobim:project-opened` presentation event

OntoBDC WIP commit:

- `a7a0b6f1f5ee3ef00f1a7a5dc56fb3172f572577`
- message: `docs: add 2026-08-13 presentation layer technical debt audit report`
- date: 2026-08-13

The audit records an older custom event API named:

- `infobim:project-opened`

It existed only in legacy/reference material and was explicitly classified as a HIGH legacy anti-pattern because it coupled generic OntoBDC presentation code to an InfoBIM-specific event that the generic Surface did not declare.

Historical locations recorded by the audit were:

- `workstream_5w2h.js.parts/001.js` — emission/use of `infobim:project-opened`;
- `annotation_query_integration.js` — listener for the same event.

### Architectural implication

The event itself is historical evidence that cross-component/project-open interaction had already been attempted, but its namespace and ownership were wrong.

Do **not** resurrect `infobim:project-opened` as a generic event. If a project/container-opened event is required in Sprint 7, it must belong to the generic event vocabulary/contract at the correct scope, with domain-specific consumers listening to it rather than owning its definition.

## 4. A3 pipeline: event export associated with deterministic state progression

OntoBDC WIP commit:

- `017666acba088bb4628907e98eb560675863cc82`
- message: `feat(a3): complete pipeline from parsed to dispatched with validation, event export and error persistence`
- date: 2026-05-19

The commit message explicitly records **event export** as part of the A3 pipeline from parsed state through dispatched state, alongside validation and persisted errors.

The visible implementation in the commit is strongly state-machine oriented: the A3 flow uses a Sismic transition handler, checks whether state transitions are allowed and persists error information when processing cannot continue.

The retrieved diff does not expose enough of the event-export implementation itself to treat its old storage or serialization shape as authoritative. What is authoritative as historical evidence is that event production/export was already considered part of deterministic processing rather than merely UI interaction.

### Architectural implication

Sprint 7 events must not be designed as a View-only concept. Historical OntoBDC work already associated events with deterministic pipeline execution. Presentation events and execution/domain events may share an envelope or vocabulary, but they have different lifecycle and scope semantics.

## 5. InfoBIM capability events and deterministic orchestration

InfoBIM WIP contains a concrete historical capability-event model.

A particularly important commit is:

- `ee4c3d178d9111fe7f7d9398367d05e11a6433e8`
- message: `feat(UHC): sugestão de dimensionamento via capability, evento e nova flag de CLI`
- date: 2026-02-14

The ADR added in this commit states that capabilities were becoming formal graph nodes with explicit metadata including **output events**. It proposed granular events rather than only generic success/error and connected event production directly to deterministic FSM/workflow transitions.

The architecture described:

- capabilities declare output events;
- capabilities declare dependencies/prerequisites;
- an ontological context bus supplies semantic values;
- state transitions are driven by triggered events;
- LLMs interpret intent but do not control step-by-step deterministic execution.

Examples in the ADR include capability-specific success/failure events causing deterministic transitions to the next capability or to error handling.

This is highly relevant to the present OntoBDC direction because it already separates probabilistic intent interpretation from deterministic event-driven execution.

## 6. Concrete UHC events

InfoBIM WIP commit:

- `ed76ac94a1c0d304fdbedff1749002b3c2e08d50`
- message: `feat(uhc): emit suggested event and return suggestions via list_pipes`
- date: 2026-02-14

This commit contains concrete code evidence of capability event metadata and emitted event values.

`UHCSizingCapability` declared success and failure event families:

- `org.ontobdc.aeco.distribution.flow.pipe.sizing.uhc.suggested`
- `org.ontobdc.aeco.distribution.flow.pipe.sizing.uhc.error`

The capability output also carried an `events` collection containing the `...uhc.suggested` event when sizing suggestions were produced.

The same metadata associated the capability output with a semantic state:

- `org.ontobdc.aeco.distribution.flow.pipe.sizing.state.sized`

This gives historical evidence of a distinction between **event** and **state**:

- event: something happened / was emitted (`...suggested`, `...error`);
- state: a semantic condition reached or represented (`...state.sized`).

That distinction should be preserved in Sprint 7 and not collapsed into one concept.

## 7. Historical Event Sourcing in InfoBIM

InfoBIM WIP commit:

- `535ed37fcf429b5d8374df5dd1522bb640d29e79`
- message: `feat(aeco): impl event sourcing, fix wrappers and add ADRs`
- date: 2026-01-25

The commit history explicitly records an **event sourcing** implementation in the AECO work.

However, the diff returned for this commit does not expose the actual event-store/event-sourcing implementation; the visible patch is dominated by dependency/path/wrapper changes. Therefore this commit is evidence that an event-sourcing experiment existed, but not enough evidence to recover its contract from this commit alone.

### Architectural implication

Do not assume that Sprint 7 should use event sourcing simply because it existed historically. Event sourcing is a persistence architecture, not a prerequisite for having events. Before reintroducing it, the historical implementation/ADRs would need separate archaeological recovery and an explicit decision about whether replay/audit/state reconstruction is required.

## 8. InfoBIM consuming OntoBDC View presentation events

InfoBIM WIP commit:

- `0cdb0f032a93728d1b0796df3b104c516124a71e`
- message: `feat(i18n): externalize InfoBIM view-tile UI strings...`
- date: 2026-08-14

The commit states that InfoBIM-specific Tiles listen for the `language-changed` event dispatched by OntoBDC View's language Tile and re-render in the selected locale.

This is important evidence for ownership boundaries: a generic OntoBDC View event can be produced by the generic presentation layer and consumed by InfoBIM domain components without InfoBIM redefining the event.

That pattern is consistent with the desired generic/domain separation.

## 9. Event families recovered from history

The historical evidence currently points to at least the following distinct event families:

### Presentation interaction events

Events exchanged among UI/presentation actors, including the three-scope Presentation Layer model and later concrete browser events.

Historical examples/evidence:

- three-scope event model;
- presentation-event debug log;
- `infobim:project-opened` as a legacy example of the right kind of interaction with the wrong ownership/namespace;
- `language-changed` consumed across OntoBDC View and InfoBIM Tiles.

### Capability / execution events

Events emitted by deterministic capabilities and intended to drive orchestration.

Historical examples:

- `...uhc.suggested`;
- `...uhc.error`;
- generic capability success/failure/granular output-event model in the FSM ADR.

### Pipeline / lifecycle events

Events associated with deterministic data-processing progress, evidenced by A3's `event export` in the parsed-to-dispatched pipeline.

### Persisted events / Event Sourcing

A separate historical experiment exists in InfoBIM AECO. This should be treated as a persistence strategy candidate, not merged automatically with the basic Event model.

## 10. Strong architectural conclusions from the history

1. **Events are not new to OntoBDC/InfoBIM.** Several independent historical implementations and architecture documents existed before the current Presentation Global Events.

2. **Events and states were historically distinct.** The UHC implementation simultaneously declared events and semantic output states.

3. **Presentation events and execution events are different concerns.** They may share common metadata/envelope concepts, but their routing, lifetime and scope are not necessarily identical.

4. **Scope was already considered a first-class concern.** The dDock/PresentationLayer work explicitly described a three-scope event model.

5. **Cross-domain ownership matters.** `infobim:project-opened` was later identified as wrong because a domain-specific namespace/event was being used as a generic Surface contract.

6. **Generic events can have domain-specific consumers.** InfoBIM Tiles listening to OntoBDC View's `language-changed` event is a clean historical example.

7. **Determinism was already tied to events.** The InfoBIM capability ADR explicitly places LLM intent interpretation outside deterministic event-driven workflow orchestration.

8. **Observability was anticipated.** A presentation-event debug log existed in historical mobile work.

9. **Persistence must remain a separate design decision.** Event sourcing existed historically, but ordinary event dispatch does not require event sourcing.

## 11. Sprint 7 recovery work suggested by the historical evidence

Before declaring the Sprint 7 event architecture complete, recover or define explicitly:

- the exact three historical Presentation event scopes and whether they remain correct;
- a generic Event identity/naming policy;
- source/producer identity;
- target or routing scope;
- payload/detail contract;
- timestamp/ordering requirements where relevant;
- event versus state semantics;
- event declaration by capabilities;
- event emission by capabilities;
- event-driven statechart transitions;
- presentation event propagation between Tiles/Surfaces;
- bridge/bus behavior beyond a Surface if dDock still requires it;
- event observability/debugging;
- whether any event categories require persistence;
- whether Event Sourcing has any current requirement at all;
- domain ownership rules so InfoBIM consumes generic events without contaminating OntoBDC contracts.

## 12. Historical commits referenced

OntoBDC WIP:

- `257becfe863d942677718f9c80f7593e8efcdc09` — three-scope Presentation event model.
- `5600a23047fadfdcf03f031cf089149b7ceac8c5` — presentation-event debug log.
- `a7a0b6f1f5ee3ef00f1a7a5dc56fb3172f572577` — audit identifying legacy `infobim:project-opened` event coupling.
- `017666acba088bb4628907e98eb560675863cc82` — A3 event export in deterministic parsed-to-dispatched pipeline.

InfoBIM WIP:

- `535ed37fcf429b5d8374df5dd1522bb640d29e79` — historical AECO event-sourcing implementation marker.
- `ee4c3d178d9111fe7f7d9398367d05e11a6433e8` — ADR for capability events + deterministic FSM orchestration.
- `ed76ac94a1c0d304fdbedff1749002b3c2e08d50` — concrete UHC success/failure events and returned `events` collection.
- `0cdb0f032a93728d1b0796df3b104c516124a71e` — InfoBIM Tiles consuming OntoBDC View `language-changed`.

---

**Sprint 7 event work must reconcile the current implementation with this historical evidence rather than designing events as if the project had no prior event architecture.**
