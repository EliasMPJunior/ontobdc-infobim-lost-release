# Events — Sprint 7

## Status

This document records the event mechanisms that currently exist across the OntoBDC/OntoBDC View presentation architecture and establishes events as a remaining architectural focus for Sprint 7.

**Sprint 7 is considered complete when the event architecture is understood, normalized and working consistently across the intended runtime/presentation flow.**

This is not a proposal for a generic event bus yet. It is first an inventory of what exists today, followed by the architectural questions that must be resolved during the remainder of the sprint.

---

## Current picture

The event model is currently concentrated in the presentation/browser layer rather than implemented as one generic OntoBDC-wide event infrastructure.

There are several different things that must not be conflated:

1. **Presentation Global Events** — semantic events intended to cross Tile/component boundaries inside a Surface.
2. **Presentation-wide UI events** — events such as language/theme changes that also cross component boundaries, but are not currently registered in the canonical Presentation Global Event list.
3. **Subsystem events** — events local to a feature/runtime such as Annotation.
4. **Native browser events** — `click`, `dblclick`, `touchend`, `keydown`, `change`, `slotchange`, ResizeObserver/MutationObserver reactions, Fullscreen API interactions, etc. These are browser infrastructure, not OntoBDC semantic events.
5. **State transitions** — OntoBDC statecharts contain states, transitions, guards and actions. These must not automatically be treated as domain/presentation events. A transition is not, by itself, an Event Bus event.
6. **Logging** — log severity/records are operational output and must not be confused with semantic events merely because an implementation may call a logged occurrence an "event".

---

# 1. Presentation Global Events

OntoBDC View currently defines a canonical list in `onto-presentation-surface.js`:

```javascript
const PRESENTATION_GLOBAL_EVENT_TYPES = [
  "entity-selected",
  "show-details-requested"
];
```

These are the clearest existing event contract in the current presentation architecture.

The Surface listens to these event types and can observe them as events travelling through the presentation tree.

## 1.1 `entity-selected`

Semantic meaning:

> A presentation component selected an entity/resource and is announcing that selection to the rest of the Surface.

A concrete producer exists today in `onto-file-tree-tile`.

When a file is selected, the Tile emits:

```javascript
entity-selected
```

with detail equivalent to:

```javascript
{
  path,
  kind: "file"
}
```

This is more than a local click callback. The intent is that other presentation components can react to the selected semantic/resource context without the producing Tile knowing which consumers exist.

Conceptually:

```text
FileTreeTile
    |
    +-- entity-selected ----------------> interested Surface components
```

This is already the seed of cross-Tile synchronization.

Potential future examples, without defining their final implementation yet:

- selecting an IFC element causes a properties Tile to update;
- selecting an entity causes related documents to update;
- selecting an entity causes annotations, schedule information or WorkStream context to update;
- selecting an entity in one representation synchronizes another representation.

The important architectural property is that the producer announces the semantic occurrence rather than calling a specific consumer directly.

---

## 1.2 `show-details-requested`

Semantic meaning:

> A presentation component requests that another representation/detail view be opened for a resource/entity.

A concrete producer exists today in `onto-file-tree-tile`.

On file activation (double-click / double-tap), the Tile emits:

```javascript
show-details-requested
```

with detail equivalent to:

```javascript
{
  path,
  kind: "file"
}
```

A concrete consumer also exists today: `onto-file-viewer-tile`.

The file viewer listens for this event and opens the requested file. Therefore the current architecture already demonstrates decoupled producer/consumer interaction:

```text
FileTreeTile
    |
    +-- show-details-requested
                    |
                    v
             FileViewerTile
```

The FileTreeTile does not need to know the implementation details of the viewer Tile. The consumer owns the presentation response.

This is important because it is already very close to the desired general pattern for dDock/Surface interaction: semantic action occurs in one Tile, the Surface transports the occurrence, and another Tile reacts.

---

## Event propagation characteristics

The current semantic presentation events are emitted as DOM `CustomEvent`s using propagation that allows them to cross component boundaries:

```javascript
bubbles: true,
composed: true
```

`bubbles: true` allows the event to travel upward through the DOM hierarchy.

`composed: true` allows the event to cross Shadow DOM boundaries.

This is essential because OntoBDC View components are Web Components and commonly use Shadow DOM. Without composed propagation, an event could remain trapped inside the producing component.

So the current transport mechanism for Presentation Global Events is effectively the browser's event propagation model.

No separate generic JavaScript Event Bus is required for these existing cases today.

---

# 2. Presentation-wide UI events

There are other events that behave globally across the presentation but are currently distinct from the canonical `PRESENTATION_GLOBAL_EVENT_TYPES` list.

## 2.1 `language-changed`

Produced by `onto-language-tile`.

The emitted event includes presentation state similar to:

```javascript
{
  language,
  label
}
```

It is emitted as a `CustomEvent` with:

```javascript
bubbles: true,
composed: true
```

Other components listen to `language-changed` and update their labels/rendering accordingly.

This makes it a real cross-component event even though it is not currently listed beside `entity-selected` and `show-details-requested` in the Surface's canonical Presentation Global Event type list.

The current architecture therefore contains an important distinction that Sprint 7 must examine:

```text
Canonical Presentation Global Events
    entity-selected
    show-details-requested

Other presentation-global behaviour
    language-changed
    theme-changed
```

We need to decide whether this distinction is intentional and semantically useful, or merely historical/implementation drift.

---

## 2.2 `theme-changed`

Produced by `onto-theme-tile`.

The emitted event contains data similar to:

```javascript
{
  theme,
  label,
  options
}
```

It is also emitted as a propagating/composed `CustomEvent`.

Its purpose is presentation synchronization rather than selection/navigation.

As with `language-changed`, it behaves as a presentation-wide event but is not currently part of the canonical `PRESENTATION_GLOBAL_EVENT_TYPES` list.

---

# 3. Subsystem events

Subsystems can also define local events that should not automatically be promoted into the global OntoBDC event vocabulary.

## 3.1 Annotation — `ontobdc:categorychange`

The Annotation editor currently emits:

```text
ontobdc:categorychange
```

when its annotation category changes.

It is implemented as a `CustomEvent` and is consumed inside the Annotation runtime/editor flow.

This is currently best understood as an Annotation subsystem event rather than a generic Presentation Global Event.

The existence of this event demonstrates that the codebase already has multiple event scopes:

```text
Presentation-global semantic events
Presentation-wide state events
Subsystem-local events
Native DOM events
```

One Sprint 7 objective is to make those scopes intentional instead of leaving their distinction implicit.

---

# 4. Native browser events are not OntoBDC semantic events

OntoBDC View naturally relies on browser events and browser observation APIs.

Examples currently used include:

```text
click
dblclick
touchend
keydown
change
slotchange
fullscreen interactions
ResizeObserver
MutationObserver
```

These are mechanisms used to detect interaction or browser/layout state.

They should not be entered into the semantic OntoBDC event vocabulary merely because they trigger an application behaviour.

For example:

```text
DOM dblclick
    -> FileTreeTile interprets activation
    -> emits show-details-requested
```

The first is a browser interaction.

The second is the semantic presentation event.

That separation is valuable and should be preserved.

---

# 5. Statecharts and events are related but not identical

OntoBDC uses statecharts extensively.

A statechart includes concepts such as:

```text
state
transition
guard
action
contract / validation
```

A state transition may eventually produce or react to an event, but the transition itself must not be assumed to be the event architecture.

For the Sprint 7 event work, this distinction matters:

```text
Event
    describes that something happened / was requested / changed

State transition
    describes movement of a state machine between states
```

The architecture may later establish explicit relationships between the two, but they should remain separate concepts unless a concrete contract says otherwise.

---

# 6. Logging is not the semantic event system

OntoBDC logging has severity levels and operational records.

Logging can record an event, but logging itself must not become the event transport or semantic event model.

A useful separation is:

```text
Semantic Event
    -> may cause behaviour
    -> may optionally be logged

Log Record
    -> describes/records an occurrence
    -> does not itself imply semantic dispatch
```

This avoids coupling runtime behaviour to observability output.

---

# 7. Evidence that the event concept already crosses OntoBDC and OntoBDC View

The concept is not isolated only inside one JavaScript file.

`ComponentMetadata` in OntoBDC already documents that a default-closed File Viewer Tile can be opened through the `show-details-requested` **Presentation Global Event**.

That means the event concept has already become part of the component/presentation contract understood by OntoBDC itself, even though the concrete browser transport currently lives in OntoBDC View.

The relevant conceptual flow is already:

```text
OntoBDC component metadata / presentation contract
                    |
                    v
           OntoBDC View Surface
                    |
                    v
        Presentation Global Event
                    |
                    v
              consumer Tile
```

This is important for the next work: we are not starting from zero.

---

# 8. What exists today, summarized

## Canonical Presentation Global Events

| Event | Current role | Known producer | Known consumer / observer |
| --- | --- | --- | --- |
| `entity-selected` | Announces semantic/resource selection | File Tree Tile | Surface/other interested components |
| `show-details-requested` | Requests detailed/open representation | File Tree Tile | File Viewer Tile; Surface observes |

## Other presentation-wide events

| Event | Current role |
| --- | --- |
| `language-changed` | Synchronizes active language across presentation components |
| `theme-changed` | Synchronizes active theme/presentation state |

## Known subsystem event

| Event | Scope | Current role |
| --- | --- | --- |
| `ontobdc:categorychange` | Annotation | Annotation editor category change |

## Not semantic OntoBDC events

```text
click
dblclick
touchend
keydown
change
slotchange
ResizeObserver callbacks
MutationObserver callbacks
Fullscreen API callbacks
```

These remain browser/runtime mechanisms.

---

# 9. Current architecture in one diagram

```text
                         OntoBDC
                            |
                            | component/presentation metadata
                            | already references Presentation Global Events
                            v
                    OntoBDC View Surface
                            |
            +---------------+----------------+
            |                                |
            | Presentation Global Events     | presentation state events
            |                                |
            | entity-selected                | language-changed
            | show-details-requested         | theme-changed
            |                                |
            +---------------+----------------+
                            |
                            v
                       Components / Tiles
                            |
                  subsystem-local events
                            |
                  ontobdc:categorychange

Browser interaction below that layer:
click / dblclick / touch / keydown / change / slotchange / observers / etc.
```

---

# 10. Architectural observations for Sprint 7

The current implementation already proves several useful things.

## 10.1 Cross-Tile communication already works

`show-details-requested` demonstrates a real producer/consumer path where the producer does not need a hard dependency on the consumer.

This is exactly the kind of behaviour needed for a reactive Surface composed of independent Tiles.

## 10.2 Semantic events can be separated from browser interactions

The browser generates `dblclick`; the Tile translates that into `show-details-requested`.

This is the correct direction of abstraction: components should expose semantic intent rather than forcing other components to understand raw UI gestures.

## 10.3 Shadow DOM is already accounted for

`bubbles: true` + `composed: true` makes semantic events capable of travelling through Web Component boundaries.

## 10.4 There is already scope drift

Some events are formally called Presentation Global Events while others (`language-changed`, `theme-changed`) behave globally without belonging to the same registry.

Sprint 7 should determine whether event scope needs explicit contracts/categories.

## 10.5 There is no need to invent an Event Bus before establishing the contract

The DOM already provides transport for the current browser presentation scenario.

The architectural problem to solve first is semantic:

- what is an event?
- who owns its vocabulary?
- what scopes exist?
- what payload identifies an entity/resource?
- which events are requests versus statements of fact?
- which events may cross Surface/component boundaries?
- which events may cross runtime/process boundaries in the future?
- how do capabilities/actions relate to events?
- how does deterministic processing react to events without becoming UI-coupled?

Only after those contracts are clear should we decide whether another transport mechanism is needed.

---

# 11. Sprint 7 event work

Events are now a first-class remaining concern of Sprint 7.

The sprint should not be considered architecturally closed merely because the current event names work in isolated browser interactions.

The remaining work is to make the event model explicit and consistent enough that future interactions can be implemented without ad-hoc direct dependencies between Tiles/components/runtimes.

Questions to settle during the sprint include at least:

1. **Event taxonomy**
   - Presentation Global Event
   - presentation state event
   - subsystem event
   - domain/runtime event, if required
   - external event, if required

2. **Naming convention**
   - when to use names such as `entity-selected`;
   - whether namespaced forms such as `ontobdc:*` are appropriate and at what scope;
   - whether request events and occurrence events need distinct naming rules.

3. **Payload contract**
   - entity URI / identifier;
   - resource identity;
   - source component/source context when relevant;
   - typed detail/payload instead of component-specific anonymous shapes where interoperability requires it.

4. **Event scope**
   - Tile-local;
   - Surface-global;
   - presentation/document-global;
   - runtime/global beyond one browser Surface, only where actually required.

5. **Event ownership**
   - which event vocabulary belongs to generic OntoBDC;
   - which belongs to OntoBDC View;
   - which belongs to a domain such as InfoBIM;
   - which belongs only to a local subsystem such as Annotation.

6. **Events vs commands/requests**
   - `entity-selected` describes an occurrence/state change;
   - `show-details-requested` describes intent/request;
   - the architecture should decide whether those are deliberately in the same event channel or require an explicit semantic distinction.

7. **Events vs capabilities/actions**
   - an event may announce that something happened;
   - a capability/action performs deterministic work;
   - event handling must not bypass the capability contracts when deterministic execution is required.

8. **Events vs statecharts**
   - determine when an event triggers a transition;
   - determine when a transition emits an event;
   - do not collapse the two models into one concept.

9. **Observability**
   - semantic events may be logged;
   - logging remains observability and not the event transport.

10. **Cross-component synchronization**
    - selecting an entity in one Tile should be able to update multiple independent Tiles;
    - opening details should be resolvable by the presentation layer rather than hard-coded producer-to-consumer calls;
    - components must remain independently replaceable where practical.

---

# 12. Expected direction

The existing event mechanism should be treated as an **embryo of the event architecture**, not discarded merely to introduce a fashionable abstraction.

The current strongest primitive is:

```text
semantic CustomEvent
    + bubbles
    + composed
    + Surface-level scope
    + independent producers/consumers
```

The next implementation decisions should preserve what already works while making semantics and ownership explicit.

A likely conceptual target, still to be validated during Sprint 7, is:

```text
Interaction / runtime occurrence
            |
            v
      semantic event
            |
            v
   Surface/runtime routing
      /      |       \
     v       v        v
  Tile A   Tile B   capability/action
```

The event layer should enable coordination without forcing every participant to know every other participant.

At the same time, OntoBDC's deterministic capability execution must remain deterministic. Events must not become an excuse to hide execution logic inside uncontrolled browser callbacks.

---

# Sprint 7 completion criterion

For this workstream, Sprint 7 ends when the event architecture is sufficiently settled that:

- the event scopes are explicit;
- event naming and payload contracts are explicit;
- Presentation Global Events are consistently defined and routed;
- global presentation-state events have an intentional place in the model;
- subsystem events remain properly scoped;
- semantic events are clearly separated from native browser events, state transitions and logging;
- independent Tiles/components can synchronize through events without hard-coded mutual knowledge;
- deterministic OntoBDC capabilities remain the execution path for deterministic operations;
- the resulting model is usable by the remaining Sprint 7 presentation/runtime work without ad-hoc event conventions.

**Sprint 7 closes when events are right.**
