"""The Global Event listener and its statechart.

The listener is called directly by a Page that has already written its data
source. Two things have to hold whatever happens: the dataset record is
written before the Surface document is touched, and a failure leaves behind
exactly enough to re-run.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from ontobdc_view.surface.adapter.global_event import (
    GlobalEventError,
    journal_entries,
    prepare_document_for_journal,
)
from ontobdc_view.surface.adapter.global_event_listener import (
    ENVELOPE_FIELDS,
    GlobalEventEnvelope,
    GlobalEventListener,
    GlobalEventListenerError,
    GlobalEventStore,
    event_file_stem,
    handle_global_event,
    handle_global_event_json,
)
from ontobdc_view.surface.domain.machine.global_event_state import GlobalEventProcessState

EVENT_NS = "http://datacenter.app.br/ontology/ontobdc/abox/presentation_event.ttl#"
SET_EVENT = f"{EVENT_NS}EntityPropertySet"
ENTITY = "urn:ontobdc:work_stream:WS-1"
TITLE = "http://purl.org/dc/terms/title"

GENERATED = """<!doctype html>
<html lang="en">
<head><meta charset="utf-8"><title>Surface</title></head>
<body>
<script type="application/ld+json" id="ontobdc-surface-jsonld">
[{"@id": "urn:ontobdc:work_stream:WS-1"}]
</script>
</body>
</html>
"""


@pytest.fixture()
def container(tmp_path) -> Path:
    (tmp_path / "index.html").write_text(
        prepare_document_for_journal(GENERATED), encoding="utf-8"
    )
    return tmp_path


@pytest.fixture()
def listener(container) -> GlobalEventListener:
    return GlobalEventListener(container)


def envelope(value="Novo", event_id="urn:uuid:e1", predicate=TITLE):
    return {
        "event": SET_EVENT,
        "eventId": event_id,
        "occurredAt": "2026-08-31T00:00:00Z",
        "source": {"kind": "xlsx", "dataset": "ds", "resource": "work_stream"},
        "entity": ENTITY,
        "operations": [
            {"operation": "set", "predicate": predicate, "value": {"@value": value}}
        ],
    }


def journal_values(container: Path):
    return [
        entry["operations"][0]["value"]["@value"]
        for entry in journal_entries((container / "index.html").read_text(encoding="utf-8"))
    ]


# --------------------------------------------------------------------------
# 1. The happy path
# --------------------------------------------------------------------------


def test_a_call_stores_the_event_appends_the_journal_and_returns_a_sequence(
    listener, container
):
    result = listener.handle(envelope())

    assert result["status"] == "completed"
    assert result["eventId"] == "urn:uuid:e1"
    assert result["sequence"] == 0

    stored = listener.store.read("urn:uuid:e1")
    assert stored["entity"] == ENTITY
    assert journal_values(container) == ["Novo"]


def test_the_stored_record_is_the_event_contract_not_a_summary(listener):
    listener.handle(envelope())
    stored = json.loads(listener.store.path_for("urn:uuid:e1").read_text(encoding="utf-8"))
    assert set(stored) == set(ENVELOPE_FIELDS)
    assert stored["operations"][0]["predicate"] == TITLE
    assert stored["source"]["kind"] == "xlsx"


def test_the_store_lives_under_the_datasets_event_directory(listener, container):
    listener.handle(envelope())
    assert listener.store.root == container / ".__ontobdc__" / "event"
    assert listener.store.path_for("urn:uuid:e1").is_file()


def test_each_event_is_its_own_record(listener):
    listener.handle(envelope("um", event_id="urn:uuid:a"))
    listener.handle(envelope("dois", event_id="urn:uuid:b"))
    assert len(list(listener.store.root.glob("*.json"))) == 2


def test_the_event_directory_holds_events_and_nothing_else(listener, container):
    """Listing `.__ontobdc__/event/` is listing the Global Events. The
    sequence counter is bookkeeping and lives beside it, not among them."""
    listener.handle(envelope())
    names = sorted(path.name for path in listener.store.root.iterdir())
    assert names == ["urn-uuid-e1.json"]
    assert (container / ".__ontobdc__" / "global_event_sequence.json").is_file()


def test_the_run_reports_the_states_it_passed_through(listener):
    result = listener.handle(envelope())
    assert result["trace"] == [
        "EVENT_RECEIVED",
        "EVENT_STORED",
        "SURFACE_JOURNAL_UPDATED",
        "COMPLETED",
    ]
    assert result["state"] == GlobalEventProcessState.COMPLETED.value


def test_sequences_stay_monotonic_across_calls(listener):
    first = listener.handle(envelope("um", event_id="urn:uuid:a"))
    second = listener.handle(envelope("dois", event_id="urn:uuid:b"))
    assert [first["sequence"], second["sequence"]] == [0, 1]


# --------------------------------------------------------------------------
# 2. A failure to store leaves index.html alone
# --------------------------------------------------------------------------


def test_a_failed_store_never_touches_the_surface(listener, container, monkeypatch):
    before = (container / "index.html").read_bytes()

    def refuse(envelope_):
        raise OSError("disk full")

    monkeypatch.setattr(listener.store, "store", refuse)

    with pytest.raises(GlobalEventListenerError) as raised:
        listener.handle(envelope())

    assert (container / "index.html").read_bytes() == before
    assert journal_values(container) == []
    assert raised.value.state is GlobalEventProcessState.EVENT_RECEIVED
    assert "SURFACE_JOURNAL_UPDATED" not in raised.value.trace


def test_a_failed_store_stops_the_statechart_before_the_journal(listener, monkeypatch):
    monkeypatch.setattr(
        listener.store, "store", lambda envelope_: (_ for _ in ()).throw(OSError("nope"))
    )
    with pytest.raises(GlobalEventListenerError) as raised:
        listener.handle(envelope())
    assert raised.value.trace == ["EVENT_RECEIVED"]
    assert listener.state is GlobalEventProcessState.EVENT_RECEIVED


# --------------------------------------------------------------------------
# 3. A failure to append keeps the stored event
# --------------------------------------------------------------------------


def test_a_failed_append_keeps_the_event_stored(listener, container, monkeypatch):
    """The event describes a change that really happened to the data source.
    Deleting it to fake atomicity would destroy the only thing that makes the
    failure recoverable."""
    from ontobdc_view.surface.adapter import global_event_listener as module

    def refuse(*args, **kwargs):
        raise OSError("the document is read-only")

    monkeypatch.setattr(module.GlobalEventJournalWriter, "append", refuse)

    with pytest.raises(GlobalEventListenerError) as raised:
        listener.handle(envelope())

    assert listener.store.exists("urn:uuid:e1")
    assert raised.value.state is GlobalEventProcessState.EVENT_STORED
    assert raised.value.trace == ["EVENT_RECEIVED", "EVENT_STORED"]
    assert "COMPLETED" not in raised.value.trace
    assert journal_values(container) == []


def test_a_rerun_after_a_failed_append_converges(listener, container, monkeypatch):
    from ontobdc_view.surface.adapter import global_event_listener as module

    original = module.GlobalEventJournalWriter.append
    monkeypatch.setattr(
        module.GlobalEventJournalWriter,
        "append",
        lambda *a, **k: (_ for _ in ()).throw(OSError("transient")),
    )
    with pytest.raises(GlobalEventListenerError):
        listener.handle(envelope())

    monkeypatch.setattr(module.GlobalEventJournalWriter, "append", original)
    result = listener.handle(envelope())

    assert result["status"] == "completed"
    assert result["sequence"] == 0
    assert journal_values(container) == ["Novo"]
    assert len(list(listener.store.root.glob("*.json"))) == 1


def test_a_missing_surface_document_is_reported_with_the_event_kept(tmp_path):
    listener = GlobalEventListener(tmp_path)
    with pytest.raises(GlobalEventListenerError, match="no Surface document"):
        listener.handle(envelope())
    assert listener.store.exists("urn:uuid:e1")


# --------------------------------------------------------------------------
# 4. Order
# --------------------------------------------------------------------------


def test_the_event_is_always_stored_before_the_journal_is_touched(listener, monkeypatch):
    order = []
    from ontobdc_view.surface.adapter import global_event_listener as module

    real_store = GlobalEventStore.store
    real_append = module.GlobalEventJournalWriter.append

    monkeypatch.setattr(
        GlobalEventStore,
        "store",
        lambda self, env: (order.append("store"), real_store(self, env))[1],
    )
    monkeypatch.setattr(
        module.GlobalEventJournalWriter,
        "append",
        lambda self, **kwargs: (order.append("append"), real_append(self, **kwargs))[1],
    )

    listener.handle(envelope())
    assert order == ["store", "append"]


def test_the_transition_table_is_the_flow():
    """A new state is a row and a method, not a rewrite: nothing in a step
    names what comes after it."""
    sources = [transition.source for transition in GlobalEventListener.TRANSITIONS]
    targets = [transition.target for transition in GlobalEventListener.TRANSITIONS]
    assert sources[0] is GlobalEventProcessState.EVENT_RECEIVED
    assert targets == [
        GlobalEventProcessState.EVENT_STORED,
        GlobalEventProcessState.SURFACE_JOURNAL_UPDATED,
        GlobalEventProcessState.COMPLETED,
    ]
    # Every transition leaves from where the previous one arrived.
    assert sources[1:] == targets[:-1]
    for transition in GlobalEventListener.TRANSITIONS:
        assert callable(getattr(GlobalEventListener, transition.action))


def test_every_state_is_labelled_and_described():
    for state in GlobalEventProcessState:
        for lang in ("en", "pt-br"):
            assert state.label(lang)
            assert state.description(lang)
    assert (
        GlobalEventProcessState.get_state("event_stored")
        is GlobalEventProcessState.EVENT_STORED
    )


# --------------------------------------------------------------------------
# 5. Idempotence
# --------------------------------------------------------------------------


def test_the_same_event_id_twice_changes_the_journal_once(listener, container):
    first = listener.handle(envelope())
    second = listener.handle(envelope())

    assert first["sequence"] == second["sequence"]
    assert first["appended"] is True
    assert second["appended"] is False
    assert journal_values(container) == ["Novo"]
    assert len(journal_entries((container / "index.html").read_text(encoding="utf-8"))) == 1


def test_a_resend_reports_the_record_was_already_there(listener):
    assert listener.handle(envelope())["storedNow"] is True
    assert listener.handle(envelope())["storedNow"] is False


def test_idempotence_comes_from_the_journal_writer_not_a_second_mechanism(listener, container):
    """Re-sending an event with the same id but different content must not
    produce a second semantic change: the writer already refuses an id the
    document carries, and the listener adds no check of its own on top."""
    listener.handle(envelope("primeiro"))
    listener.handle(envelope("segundo"))
    assert journal_values(container) == ["primeiro"]


# --------------------------------------------------------------------------
# The envelope and the entry points
# --------------------------------------------------------------------------


def test_an_envelope_without_an_event_id_is_refused(listener):
    payload = envelope()
    del payload["eventId"]
    with pytest.raises(GlobalEventError, match="eventId"):
        listener.handle(payload)


def test_an_envelope_without_operations_is_refused(listener):
    payload = envelope()
    payload["operations"] = []
    with pytest.raises(GlobalEventError, match="no operations"):
        listener.handle(payload)


def test_a_column_label_is_not_a_predicate(listener, container):
    with pytest.raises(GlobalEventListenerError, match="not an IRI"):
        listener.handle(envelope(predicate="Name"))
    # It got as far as storing — the change to the data source did happen.
    assert listener.store.exists("urn:uuid:e1")
    assert journal_values(container) == []


def test_the_envelope_accepts_json_text_as_well_as_a_dict(listener):
    result = listener.handle(json.dumps(envelope()))
    assert result["sequence"] == 0


def test_the_surface_comes_from_the_container_not_the_envelope(container, tmp_path):
    """A path in the envelope would be a path the browser chose."""
    elsewhere = tmp_path.parent / "elsewhere.html"
    payload = envelope()
    payload["surfacePath"] = str(elsewhere)
    listener = GlobalEventListener(container)
    listener.handle(payload)
    assert not elsewhere.exists()
    assert listener.surface_path == container / "index.html"


def test_the_module_level_entry_point_runs_the_same_flow(container):
    result = handle_global_event(container, envelope())
    assert result["status"] == "completed"
    assert result["sequence"] == 0


def test_the_json_entry_point_reports_a_failure_rather_than_raising(tmp_path):
    result = json.loads(handle_global_event_json(tmp_path, json.dumps(envelope())))
    assert result["status"] == "failed"
    assert result["state"] == GlobalEventProcessState.EVENT_STORED.value
    assert "no Surface document" in result["error"]


def test_the_json_entry_point_reports_a_rejected_envelope(container):
    result = json.loads(handle_global_event_json(container, "{not json"))
    assert result["status"] == "rejected"


def test_the_file_name_is_ascii_only():
    """The browser computes this name too, with `/[^a-zA-Z0-9]/g`, while
    `str.isalnum()` is Unicode-aware — the record has to be findable by the
    same name whoever derives it."""
    assert event_file_stem("urn:uuid:ÁÇÃO-1") == "urn-uuid----O-1"
    assert event_file_stem("urn:uuid:abc-123") == "urn-uuid-abc-123"
    assert all(character.isascii() for character in event_file_stem("urn:uuid:日本語"))


def test_the_envelope_keeps_the_fields_the_contract_defines():
    parsed = GlobalEventEnvelope.read(envelope())
    assert parsed.event_id == "urn:uuid:e1"
    assert parsed.entity == ENTITY
    assert parsed.occurred_at == "2026-08-31T00:00:00Z"
    assert [operation.predicate for operation in parsed.operations] == [TITLE]
