[↑ Back to state-machine inventory](index.md)

# Global Event processing

> **Status:** Current direct state machine; no YAML/Sismic.

Persists one Global Event and appends it to the Surface journal with a recoverable, idempotent order.

## Audited implementation

- Enum: [GlobalEventProcessState](https://github.com/EliasMPJunior/ontobdc-wip/blob/fe6d756c44141cdc14234937ce1e659384950b26/src/ontobdc/view/domain/machine/global_event_state.py)
- YAML: none; transitions are expressed directly in Python
- Executor: [listener, transition table, and store](https://github.com/EliasMPJunior/ontobdc-wip/blob/fe6d756c44141cdc14234937ce1e659384950b26/src/ontobdc/view/adapter/surface/global_event_listener.py)

## States from the enum

| State | Raw value | Enum meaning | Capability or executing operation |
| --- | --- | --- | --- |
| `UNDEFINED` | `__undefined__` | No Global Event is being processed. | No running trace |
| `EVENT_RECEIVED` | `__event_received__` | A Page handed the listener a Global Event envelope, after its own write to the data source completed. | Entry assigned by `GlobalEventListener.handle()` |
| `EVENT_STORED` | `__event_stored__` | The event is persisted under the dataset's .__ontobdc__/event/ as a record of its own. Nothing touches index.html before this. | `store_event` action |
| `SURFACE_JOURNAL_UPDATED` | `__surface_journal_updated__` | The event's JSON-LD was appended to the Surface document's journal and a sequence was assigned to it. | `update_surface_journal` action |
| `COMPLETED` | `__completed__` | Both the dataset record and the Surface journal carry the event; the sequence is what the Page is told. | `complete` action |

## Transition table

| From | To | Guard/condition | Action |
| --- | --- | --- | --- |
| `UNDEFINED` | `EVENT_RECEIVED` | unconditional | GlobalEventListener.handle entry |
| `EVENT_RECEIVED` | `EVENT_STORED` | unconditional | store_event |
| `EVENT_STORED` | `SURFACE_JOURNAL_UPDATED` | unconditional | update_surface_journal |
| `SURFACE_JOURNAL_UPDATED` | `COMPLETED` | unconditional | complete |

## Runtime findings

- This machine is a Python enum plus the `GlobalEventListener.TRANSITIONS` table because Sismic is not shipped into the Pyodide browser runtime.
- The event record is persisted before `index.html` is modified. Replaying the same `eventId` converges rather than duplicating the event.
