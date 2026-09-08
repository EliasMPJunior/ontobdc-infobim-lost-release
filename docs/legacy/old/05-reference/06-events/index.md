# Presentation event reference

This page records the concrete event contract currently declared for OntoBDC View. Event names and promotion targets come from [`Brasidata/brasidatacenter@r008/v0.9/ontology/tool/ontobdc/abox/presentation_event.ttl`](https://github.com/Brasidata/brasidatacenter/blob/r008/v0.9/ontology/tool/ontobdc/abox/presentation_event.ttl). The ontology, not this table or JavaScript, is the executable source of truth.

## Event type contract

| Ontology class | Meaning |
| --- | --- |
| `view:PresentationEvent` | Common superclass of semantic presentation events. |
| `view:ComponentEvent` | Semantic event originating at Component scope. |
| `view:SharedEvent` | Semantic event available across one PresentationLayer. |
| `view:GlobalEvent` | Persisted and replayable event at the dDock/container boundary. |

`ExternalEvent` is not currently an ontology class. It remains an architectural description of a boundary crossing.

## Current Component-to-Shared policy

| Component Event | Promotes to Shared Event(s) | Meaning of the promotion |
| --- | --- | --- |
| `SurfaceLoaded` | `PageLoaded` | Announces that a generated Surface became available as a loaded Page. |
| `EntityPageLoaded` | `PageLoaded` | Normalizes a standalone entity Page load to the shared page-loaded occurrence. |
| `TileOpened` | `TileReady`, `SurfaceAreaFilled` | Announces both Tile availability and occupation of Surface area. |
| `TileClosed` | `TileStandby`, `SurfaceAreaEmptied` | Announces both Tile standby and release of Surface area. |
| `TileExpanded` | `TileResized`, `SurfaceAreaFilled` | Announces the size change and additional area occupation. |
| `TileCollapsed` | `TileResized`, `SurfaceAreaEmptied` | Announces the size change and area release. |
| `TileFullSized` | `SurfaceObscured` | Announces that other Surface content is obscured. |
| `TileRestored` | `SurfaceRevealed` | Announces that previously obscured Surface content is visible again. |
| `EntityPageOpenRequested` | `EntityPageRequested` | Converts the local open request into a presentation-wide Page request. |
| `EntityPageCloseRequested` | `EntityPageDismissRequested` | Converts the local close request into a presentation-wide dismissal request. |
| `ComponentFileDoubleClick` | `EntityPageRequested` | Interprets file activation as a request for an entity/file Page. |
| `ComponentFileSingleClick` | _none_ | Remains a Component Event; absence of promotion is intentional and valid. |

One source can promote to several targets. Each target is dispatched independently. The table must be updated whenever the ABox policy changes, but runtime behavior changes only when the ontology changes.

`ComponentFileSelected` and `EntitySelected` are not declared in the current `r008/v0.9` policy. Historical code or discussion may contain those names; they must not be presented as part of the current contract unless they are restored to the ontology.

## Browser envelopes

### Component Event

DOM type:

```text
ontobdc:component-event
```

Minimum detail:

```json
{
  "event": "ComponentFileDoubleClick"
}
```

The remainder of `detail` is event-specific semantic data. The envelope must bubble and cross Shadow DOM boundaries.

### Shared Event

DOM type:

```text
ontobdc:shared-event
```

Detail added by the promoter:

```json
{
  "event": "EntityPageRequested",
  "eventIri": "http://datacenter.app.br/ontology/ontobdc/abox/presentation_event.ttl#EntityPageRequested",
  "promotedFrom": "ComponentFileDoubleClick",
  "promotedFromIri": "http://datacenter.app.br/ontology/ontobdc/abox/presentation_event.ttl#ComponentFileDoubleClick"
}
```

Original Component Event detail is preserved alongside these fields.

## Global Event envelope

A Global Event has a different contract because it is persisted.

| Field | Required | Meaning |
| --- | --- | --- |
| `eventId` | Yes | Stable idempotency identifier, normally a URI such as a UUID URN. |
| `event` | Yes by semantic contract | Event identifier or name. |
| `entity` | Yes by semantic contract | Entity affected by the occurrence. |
| `occurredAt` | Optional | Timestamp supplied by the producer. |
| `source` | Optional | Provenance identifying the producing Page/runtime. |
| `operations` | Yes, non-empty | Ordered data operations carried by the event. |

Each operation contains:

```json
{
  "operation": "...",
  "predicate": "...",
  "value": "..."
}
```

The listener persists the complete envelope as its own record before appending its JSON-LD representation to the Surface journal.

## Journal representation

A packaged Surface contains:

- an embedded JSON-LD snapshot carrying `data-snapshot-through`;
- the delimiter `<!-- ontobdc:global-event-journal -->`;
- zero or more appended Global Event blocks, each with a monotonically assigned sequence.

On load, the browser starts from the snapshot and replays journal entries whose sequence is greater than `data-snapshot-through`. Regeneration or compaction may fold entries into a newer snapshot and remove the absorbed blocks atomically.

Appending an event is not the same operation as regenerating the Surface. Ordinary Global Event ingestion appends; the Surface generation pipeline may rewrite the generated artifact.

## Implementation status

| Concern | Current home |
| --- | --- |
| Event classes and promotion property | `Brasidata/brasidatacenter@r008/v0.9`, `view.ttl` |
| Concrete Component-to-Shared policy | `Brasidata/brasidatacenter@r008/v0.9`, `presentation_event.ttl` |
| Component-to-Shared Listener | `EliasMPJunior/ontobdc-web-dock@master` |
| Browser bridge and DOM dispatch | `EliasMPJunior/ontobdc-view@r008/v0.9` |
| Journal preparation | `SurfacePackagedCapability` in `ontobdc-view@r008/v0.9` |
| Global Event writer/listener | Existing not-yet-migrated OntoBDC View implementation; not part of the released `ontobdc-view@r008/v0.9` write path |

See [Presentation events](../../02-concepts/presentation-events.md) for the conceptual distinctions and [Event promotion architecture](../../03-architecture/event-promotion.md) for the runtime flow.

