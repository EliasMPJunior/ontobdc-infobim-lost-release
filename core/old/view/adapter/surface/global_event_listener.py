"""The Global Event listener: a Page calls it, a statechart coordinates it.

A Page that has just written and verified its data source calls this
directly — in the browser, through Pyodide — and gets the result of the
processing back. There is no queue and no daemon: the call itself is the
processing, and it resolves only once the event really is on disk in both
places it belongs.

    Page saves the .xlsx / .ttl
        -> builds the Global Event
        -> submitGlobalEvent(event)          [JavaScript]
        -> GlobalEventListener.handle(...)   [Python, here]
             EVENT_RECEIVED
               -> store the event under `.__ontobdc__/event/`
             EVENT_STORED
               -> append its JSON-LD to the Surface journal
             SURFACE_JOURNAL_UPDATED
               -> COMPLETED
        -> {eventId, sequence, status} back to the Page

The order is the contract, not an implementation detail. The dataset record
is written first, so a failure to append leaves behind the evidence of a
change that really did happen to the data source — recoverable by re-running
the listener with the same `eventId`, which converges because the journal
writer already refuses to append an id it carries. The reverse order would
put the Surface ahead of the dataset, with nothing to reconcile it from.

Nothing here re-implements the journal. `GlobalEventJournalWriter` does the
appending, the sequencing and the idempotence exactly as it already did for
every other caller.

This module runs in Pyodide, so it imports the standard library and the
journal writer beside it, and nothing else.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple

from ontobdc.shared.adapter.atomic_file import AtomicFileWriter
from ontobdc.view.adapter.surface.global_event import (
    GlobalEventError,
    GlobalEventJournalWriter,
    GlobalEventOperation,
)
from ontobdc.view.domain.machine.global_event_state import GlobalEventProcessState

MARKER_DIR = ".__ontobdc__"
EVENT_DIR = "event"
# Beside the event directory, not inside it: `.__ontobdc__/event/` holds
# Global Event records and nothing else, so listing it is listing the events.
SEQUENCE_FILE = "global_event_sequence.json"
SURFACE_FILE = "index.html"

_STATE = GlobalEventProcessState

# Everything a Global Event is, as the contract already defines it. The store
# writes these and nothing else — the record in the dataset is the event, not
# a summary of it.
ENVELOPE_FIELDS = ("eventId", "event", "entity", "occurredAt", "source", "operations")

_ASCII_ALNUM = frozenset(
    "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"
)


def event_file_stem(event_id: str) -> str:
    """A file name for an event id.

    `urn:uuid:…` is not a legal file name on Windows, so everything that is
    not an ASCII letter or digit becomes a dash. ASCII deliberately, not
    `str.isalnum()`: the record has to be findable by the same name whoever
    computes it, and `isalnum()` is Unicode-aware while a browser's
    `/[^a-zA-Z0-9]/g` is not.
    """
    return "".join(character if character in _ASCII_ALNUM else "-" for character in event_id)


class GlobalEventListenerError(Exception):
    """The listener could not carry the event through, and says where it stopped."""

    def __init__(self, message: str, state: GlobalEventProcessState, trace: List[str]) -> None:
        super().__init__(message)
        self.state = state
        self.trace = trace


# --------------------------------------------------------------------------
# The envelope
# --------------------------------------------------------------------------


@dataclass(frozen=True)
class GlobalEventEnvelope:
    """One Global Event, as the Page hands it over."""

    event_id: str
    event: str
    entity: str
    operations: List[GlobalEventOperation]
    source: Dict[str, Any]
    occurred_at: Optional[str]
    raw: Dict[str, Any]

    @classmethod
    def read(cls, payload: Any) -> "GlobalEventEnvelope":
        if isinstance(payload, str):
            try:
                payload = json.loads(payload)
            except ValueError as error:
                raise GlobalEventError(f"the envelope is not readable JSON: {error}") from error
        if not isinstance(payload, dict):
            raise GlobalEventError("a Global Event envelope must be an object")

        event_id = str(payload.get("eventId", "")).strip()
        if not event_id:
            raise GlobalEventError("a Global Event needs an eventId")

        operations = payload.get("operations")
        if not isinstance(operations, list) or not operations:
            raise GlobalEventError(f"{event_id} carries no operations")

        parsed: List[GlobalEventOperation] = []
        for entry in operations:
            if not isinstance(entry, dict):
                raise GlobalEventError(f"{event_id} has a malformed operation")
            parsed.append(
                GlobalEventOperation(
                    operation=str(entry.get("operation", "")),
                    predicate=str(entry.get("predicate", "")),
                    value=entry.get("value"),
                )
            )

        return cls(
            event_id=event_id,
            event=str(payload.get("event", "")).strip(),
            entity=str(payload.get("entity", "")).strip(),
            operations=parsed,
            source=payload.get("source") or {},
            occurred_at=payload.get("occurredAt"),
            raw=payload,
        )

    def as_record(self) -> Dict[str, Any]:
        """The event as it is stored in the dataset — the contract's own
        fields, carried through unchanged."""
        return {field: self.raw.get(field) for field in ENVELOPE_FIELDS if field in self.raw}


# --------------------------------------------------------------------------
# The dataset's event store
# --------------------------------------------------------------------------


class GlobalEventStore:
    """`<container>/.__ontobdc__/event/<event-id>.json`.

    One file per event, because each Global Event is a fact of its own: two
    Pages saving at the same moment both leave a record, and a record is
    never overwritten by a later event.
    """

    def __init__(self, container_path: Path) -> None:
        self._root = Path(container_path) / MARKER_DIR / EVENT_DIR

    @property
    def root(self) -> Path:
        return self._root

    def path_for(self, event_id: str) -> Path:
        return self._root / f"{event_file_stem(event_id)}.json"

    def exists(self, event_id: str) -> bool:
        return self.path_for(event_id).is_file()

    def read(self, event_id: str) -> Optional[Dict[str, Any]]:
        try:
            return json.loads(self.path_for(event_id).read_text(encoding="utf-8"))
        except (OSError, ValueError):
            return None

    def store(self, envelope: GlobalEventEnvelope) -> Tuple[Path, bool]:
        """Persist the event. Returns its path and whether it was new.

        Re-storing an id already on disk rewrites the same record rather than
        raising: a re-run after a failed journal append has to get past this
        state to reach the one that failed.
        """
        target = self.path_for(envelope.event_id)
        existed = target.is_file()
        self._root.mkdir(parents=True, exist_ok=True)
        body = json.dumps(envelope.as_record(), ensure_ascii=False, indent=2) + "\n"
        AtomicFileWriter.write(target, lambda temp: temp.write_text(body, encoding="utf-8"))
        return target, not existed


# --------------------------------------------------------------------------
# The statechart
# --------------------------------------------------------------------------


@dataclass(frozen=True)
class Transition:
    """One step: from a state, through an action, into the next state.

    The action is a method name on the listener. The runner calls it and
    advances only if it returns; a raise leaves the run in the state it was
    already in, which is what the caller is told.
    """

    source: GlobalEventProcessState
    action: str
    target: GlobalEventProcessState


class GlobalEventListener:
    """Runs one Global Event through the statechart.

    The table is the flow. Inserting `VALIDATED` before `EVENT_STORED`, or
    `COMPACTED` after `SURFACE_JOURNAL_UPDATED`, is one more row and one more
    method — no other step changes, because no step knows what follows it.
    """

    TRANSITIONS: Tuple[Transition, ...] = (
        Transition(_STATE.EVENT_RECEIVED, "store_event", _STATE.EVENT_STORED),
        Transition(_STATE.EVENT_STORED, "update_surface_journal", _STATE.SURFACE_JOURNAL_UPDATED),
        Transition(_STATE.SURFACE_JOURNAL_UPDATED, "complete", _STATE.COMPLETED),
    )

    def __init__(
        self,
        container_path: Path,
        *,
        surface_path: Optional[Path] = None,
    ) -> None:
        self._container = Path(container_path)
        # Resolved from the container the listener was opened on, never from
        # the envelope: a path in the envelope would be a path the browser
        # chose, and honouring it would make this an arbitrary-write call.
        self._surface_path = Path(surface_path) if surface_path else self._container / SURFACE_FILE
        self._store = GlobalEventStore(self._container)
        self._state = _STATE.UNDEFINED
        self._trace: List[GlobalEventProcessState] = []
        self._result: Dict[str, Any] = {}

    @property
    def store(self) -> GlobalEventStore:
        return self._store

    @property
    def surface_path(self) -> Path:
        return self._surface_path

    @property
    def state(self) -> GlobalEventProcessState:
        return self._state

    def _writer(self) -> GlobalEventJournalWriter:
        return GlobalEventJournalWriter(
            self._surface_path, self._container / MARKER_DIR / SEQUENCE_FILE
        )

    # -- the run -----------------------------------------------------------

    def handle(self, payload: Any) -> Dict[str, Any]:
        envelope = GlobalEventEnvelope.read(payload)

        self._state = _STATE.EVENT_RECEIVED
        self._trace = [self._state]
        self._result = {
            "eventId": envelope.event_id,
            "event": envelope.event,
            "entity": envelope.entity,
        }

        for transition in self.TRANSITIONS:
            if self._state is not transition.source:
                raise GlobalEventListenerError(
                    f"the statechart is in {self._state.name} and cannot take the "
                    f"transition out of {transition.source.name}",
                    self._state,
                    _STATE.trace_names(self._trace),
                )
            action: Callable[[GlobalEventEnvelope], None] = getattr(self, transition.action)
            try:
                action(envelope)
            except GlobalEventListenerError:
                raise
            except Exception as error:  # noqa: BLE001 — reported with where it stopped
                raise GlobalEventListenerError(
                    f"{transition.action} failed in {self._state.name}: {error}",
                    self._state,
                    _STATE.trace_names(self._trace),
                ) from error
            # Entered only now: the action completed.
            self._state = transition.target
            self._trace.append(self._state)

        self._result["status"] = "completed"
        self._result["state"] = self._state.value
        self._result["trace"] = _STATE.trace_names(self._trace)
        return dict(self._result)

    # -- the actions -------------------------------------------------------

    def store_event(self, envelope: GlobalEventEnvelope) -> None:
        """Persist the event in the dataset. Nothing touches the Surface
        document before this has succeeded."""
        path, created = self._store.store(envelope)
        self._result["storedAt"] = str(path)
        self._result["stored"] = True
        self._result["storedNow"] = created

    def update_surface_journal(self, envelope: GlobalEventEnvelope) -> None:
        """Append the event's JSON-LD to the Surface journal.

        Through the existing writer, so the sequence, the idempotence, the
        append-without-deserializing-the-snapshot and the recovery from a
        partial block are the ones already implemented and tested.
        """
        if not self._surface_path.is_file():
            raise GlobalEventError(
                f"no Surface document at {self._surface_path}; the event stays stored "
                "in the dataset and can be replayed once one exists"
            )
        payload, created = self._writer().append(
            event=envelope.event,
            entity=envelope.entity,
            operations=envelope.operations,
            source=envelope.source,
            event_id=envelope.event_id,
            occurred_at=envelope.occurred_at,
        )
        self._result["sequence"] = payload["sequence"]
        self._result["appended"] = created

    def complete(self, envelope: GlobalEventEnvelope) -> None:
        """Nothing left to do but say so. A separate state so the run has a
        terminal the table can grow before."""
        if "sequence" not in self._result:
            raise GlobalEventError("the journal did not assign a sequence")


def handle_global_event(container_path: Any, payload: Any) -> Dict[str, Any]:
    """The listener as the browser bridge calls it: envelope in, result out.

    Returns a plain dict so a Pyodide caller reads it directly. A failure
    raises `GlobalEventListenerError`, carrying the state it stopped in.
    """
    return GlobalEventListener(Path(str(container_path))).handle(payload)


def handle_global_event_json(container_path: Any, payload_json: str) -> str:
    """JSON in, JSON out — for a caller that would rather not marshal a dict
    across the language boundary."""
    try:
        result = handle_global_event(container_path, payload_json)
    except GlobalEventListenerError as error:
        return json.dumps(
            {"status": "failed", "error": str(error), "state": error.state.value, "trace": error.trace},
            ensure_ascii=False,
        )
    except GlobalEventError as error:
        return json.dumps(
            {"status": "rejected", "error": str(error), "state": _STATE.UNDEFINED.value, "trace": []},
            ensure_ascii=False,
        )
    return json.dumps(result, ensure_ascii=False)
