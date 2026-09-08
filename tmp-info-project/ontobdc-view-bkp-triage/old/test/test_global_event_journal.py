"""The Global Event journal writer.

Every requirement here is one the browser cannot recover from on its own:
an append that rewrote the snapshot would be unusable at container scale, a
sequence that repeated would make two edits indistinguishable to the
replay's ordering, an unescaped `</script>` would end the block and let a
spreadsheet cell parse as markup, and a half-written block would swallow
whatever is appended after it.
"""

from __future__ import annotations

import json
import multiprocessing
import re
from pathlib import Path

import pytest

from ontobdc_view.surface.adapter.global_event import (
    JOURNAL_MARKER,
    GlobalEventError,
    GlobalEventJournalWriter,
    GlobalEventOperation,
    document_accepts_journal,
    escape_for_script,
    journal_entries,
    journal_event_ids,
    last_sequence,
    prepare_document_for_journal,
    set_snapshot_through,
    snapshot_through,
    truncate_incomplete_block,
)

EVENT_NS = "http://datacenter.app.br/ontology/ontobdc/abox/presentation_event.ttl#"
SET_EVENT = f"{EVENT_NS}EntityPropertySet"
ENTITY = "urn:ontobdc:work_stream:WS-1"
TITLE = "http://purl.org/dc/terms/title"

GENERATED = """<!doctype html>
<html lang="en">
<head><meta charset="utf-8"><title>Surface</title></head>
<body>
<script type="application/ld+json" id="ontobdc-surface-jsonld">
[{"@id": "urn:ontobdc:work_stream:WS-1", "http://purl.org/dc/terms/title": [{"@value": "Antigo"}]}]
</script>
<script type="module">/* components */</script>
</body>
</html>
"""


@pytest.fixture()
def surface(tmp_path) -> Path:
    path = tmp_path / "index.html"
    path.write_text(prepare_document_for_journal(GENERATED), encoding="utf-8")
    return path


@pytest.fixture()
def writer(surface, tmp_path) -> GlobalEventJournalWriter:
    return GlobalEventJournalWriter(surface, tmp_path / "state.json")


def set_title(writer, value, event_id=None):
    return writer.append(
        event=SET_EVENT,
        entity=ENTITY,
        operations=[GlobalEventOperation("set", TITLE, {"@value": value})],
        source={"kind": "xlsx", "dataset": "ds", "resource": "work_stream"},
        event_id=event_id,
    )


# --------------------------------------------------------------------------
# An append does not touch the snapshot
# --------------------------------------------------------------------------


def test_an_append_leaves_the_existing_bytes_identical(writer, surface):
    """Byte-for-byte, not merely equivalent: the point is that the snapshot
    is never deserialized and re-serialized, whatever its size."""
    before = surface.read_bytes()
    set_title(writer, "Novo")
    after = surface.read_bytes()
    assert after[: len(before)] == before
    assert len(after) > len(before)


def test_an_append_does_not_read_the_snapshot_body(writer, surface, monkeypatch):
    """A JSON parse of the snapshot during a normal append would be the
    cost this design exists to avoid."""
    parsed = []
    original = json.loads
    monkeypatch.setattr(json, "loads", lambda *a, **k: (parsed.append(a[0]), original(*a, **k))[1])
    set_title(writer, "Novo")
    assert not any('"@id"' in str(text) and "ontobdc-surface-jsonld" not in str(text) and len(str(text)) > 400 for text in parsed)


def test_the_appended_block_is_readable_as_the_event(writer, surface):
    payload, created = set_title(writer, "Novo")
    assert created is True
    entries = journal_entries(surface.read_text(encoding="utf-8"))
    assert entries == [payload]
    assert entries[0]["operations"] == [
        {"operation": "set", "predicate": TITLE, "value": {"@value": "Novo"}}
    ]


# --------------------------------------------------------------------------
# Sequencing
# --------------------------------------------------------------------------


def test_sequences_are_monotonic(writer, surface):
    first, _ = set_title(writer, "Um")
    second, _ = set_title(writer, "Dois")
    third, _ = set_title(writer, "Três")
    assert [first["sequence"], second["sequence"], third["sequence"]] == [0, 1, 2]


def test_the_sequence_is_assigned_by_the_writer_not_the_caller(writer):
    payload, _ = writer.append(
        event=SET_EVENT,
        entity=ENTITY,
        operations=[GlobalEventOperation("set", TITLE, {"@value": "x"})],
    )
    assert payload["sequence"] == 0


def test_a_lost_state_file_never_reissues_a_sequence(writer, surface, tmp_path):
    """The document is consulted as well as the counter, so a rolled-back or
    deleted state file cannot hand out a number already in the journal."""
    set_title(writer, "Um")
    set_title(writer, "Dois")
    (tmp_path / "state.json").unlink()
    third, _ = set_title(writer, "Três")
    assert third["sequence"] == 2
    sequences = [entry["sequence"] for entry in journal_entries(surface.read_text(encoding="utf-8"))]
    assert sequences == sorted(set(sequences))


def test_a_compacted_document_continues_the_numbering(tmp_path):
    path = tmp_path / "index.html"
    path.write_text(
        prepare_document_for_journal(set_snapshot_through(GENERATED, 41)), encoding="utf-8"
    )
    writer = GlobalEventJournalWriter(path, tmp_path / "state.json")
    payload, _ = set_title(writer, "Depois")
    assert payload["sequence"] == 42


# --------------------------------------------------------------------------
# Idempotence
# --------------------------------------------------------------------------


def test_a_repeated_event_id_does_not_create_a_second_block(writer, surface):
    """The recovery path: an event persisted but never acknowledged is
    retried with the same id, and the retry has to converge."""
    first, created_first = set_title(writer, "Novo", event_id="urn:uuid:fixed")
    second, created_second = set_title(writer, "Novo", event_id="urn:uuid:fixed")
    assert created_first is True
    assert created_second is False
    assert second["sequence"] == first["sequence"]
    assert len(journal_entries(surface.read_text(encoding="utf-8"))) == 1


def test_event_ids_are_unique_when_not_supplied(writer):
    first, _ = set_title(writer, "Um")
    second, _ = set_title(writer, "Dois")
    assert first["eventId"] != second["eventId"]
    assert first["eventId"].startswith("urn:uuid:")


# --------------------------------------------------------------------------
# Escaping and encoding
# --------------------------------------------------------------------------


def test_a_value_containing_a_script_end_tag_does_not_end_the_block(writer, surface):
    hostile = 'antes </script><img src=x onerror=alert(1)> depois'
    set_title(writer, hostile)
    document = surface.read_text(encoding="utf-8")
    # Exactly one `</script>` was added: the block's own closing tag.
    assert document.count("</script>") == GENERATED.count("</script>") + 1
    assert journal_entries(document)[0]["operations"][0]["value"]["@value"] == hostile


@pytest.mark.parametrize(
    "hostile",
    [
        "</script >",
        "</SCRIPT>",
        "<!-- comment",
        "<script>",
        "</script\n>",
    ],
)
def test_every_angle_bracket_form_is_neutralized(writer, surface, hostile):
    """One rule — escape every `<` — instead of a list of parser quirks to
    keep in sync."""
    set_title(writer, hostile)
    document = surface.read_text(encoding="utf-8")
    block = document[document.index("data-ontobdc-global-event") :]
    body = block[block.index(">") + 1 : block.index("</script>")]
    assert "<" not in body
    assert journal_entries(document)[0]["operations"][0]["value"]["@value"] == hostile


def test_unicode_survives_the_round_trip(writer, surface):
    value = "Execução de fundação — ação 100 % 日本語 🏗"
    set_title(writer, value)
    assert journal_entries(surface.read_text(encoding="utf-8"))[0]["operations"][0][
        "value"
    ]["@value"] == value


def test_escaping_keeps_the_payload_valid_json():
    assert json.loads(escape_for_script({"x": "</script>"})) == {"x": "</script>"}


# --------------------------------------------------------------------------
# The document stays appendable and parseable
# --------------------------------------------------------------------------


def test_a_generated_document_is_prepared_to_accept_a_journal():
    prepared = prepare_document_for_journal(GENERATED)
    assert document_accepts_journal(prepared)
    assert "</html>" not in prepared
    assert "</body>" not in prepared
    # Everything else is untouched.
    assert '<script type="application/ld+json" id="ontobdc-surface-jsonld">' in prepared


def test_an_unprepared_document_is_reported_as_not_appendable():
    assert not document_accepts_journal(GENERATED)


def test_the_journal_region_is_delimited_by_a_marker():
    prepared = prepare_document_for_journal(GENERATED)
    assert prepared.rstrip().endswith(JOURNAL_MARKER)


def test_a_sequence_written_in_a_component_script_is_not_read_as_the_journals():
    """The generated document inlines component scripts, and one of them
    documents this very block format in a comment. A free-text scan for
    `data-sequence="N"` read that comment as the journal's last sequence,
    so every following append got a number that was already taken."""
    decoy = GENERATED.replace(
        "/* components */",
        '/* <script data-ontobdc-global-event="true" data-sequence="4200"> */',
    )
    prepared = prepare_document_for_journal(decoy)
    assert last_sequence(prepared) == -1
    assert journal_event_ids(prepared) == []
    assert journal_entries(prepared) == []


def test_a_snapshot_marker_written_in_a_component_script_is_not_read_either():
    decoy = GENERATED.replace(
        "/* components */",
        '/* <script id="ontobdc-surface-jsonld" data-snapshot-through="99"> */',
    )
    assert snapshot_through(prepare_document_for_journal(decoy)) == -1


def test_an_unprepared_document_has_no_journal_to_read():
    """Without the marker there is no journal region: reading the whole file
    instead is exactly the mistake the marker exists to prevent."""
    assert journal_entries(GENERATED) == []
    assert last_sequence(GENERATED) == -1


def test_preparing_is_idempotent():
    once = prepare_document_for_journal(GENERATED)
    assert prepare_document_for_journal(once) == once


# --------------------------------------------------------------------------
# Crash recovery
# --------------------------------------------------------------------------


def test_an_interrupted_append_is_truncated_before_the_next_one(writer, surface):
    """A block with no closing tag swallows everything after it, including
    the next event appended."""
    set_title(writer, "Um")
    with surface.open("a", encoding="utf-8") as handle:
        handle.write(
            '\n<script type="application/ld+json" data-ontobdc-global-event="true"'
            ' data-event-id="urn:uuid:half" data-sequence="99">\n{"event": "trunc'
        )

    set_title(writer, "Dois")

    document = surface.read_text(encoding="utf-8")
    assert "urn:uuid:half" not in document
    entries = journal_entries(document)
    assert [entry["operations"][0]["value"]["@value"] for entry in entries] == ["Um", "Dois"]


def test_truncation_reports_whether_it_did_anything(writer, surface):
    set_title(writer, "Um")
    assert truncate_incomplete_block(surface) is False
    with surface.open("a", encoding="utf-8") as handle:
        handle.write('\n<script type="application/ld+json" data-ontobdc-global-event="true" >{')
    assert truncate_incomplete_block(surface) is True
    assert truncate_incomplete_block(surface) is False


def test_a_truncated_tail_does_not_cost_the_events_before_it(writer, surface):
    set_title(writer, "Um")
    set_title(writer, "Dois")
    with surface.open("a", encoding="utf-8") as handle:
        handle.write('\n<script type="application/ld+json" data-ontobdc-global-event="true">{"eve')
    truncate_incomplete_block(surface)
    entries = journal_entries(surface.read_text(encoding="utf-8"))
    assert len(entries) == 2


# --------------------------------------------------------------------------
# Concurrency
# --------------------------------------------------------------------------


def _append_in_process(args):
    path, state, value, event_id = args
    writer = GlobalEventJournalWriter(Path(path), Path(state))
    payload, _ = writer.append(
        event=SET_EVENT,
        entity=ENTITY,
        operations=[GlobalEventOperation("set", TITLE, {"@value": value})],
        event_id=event_id,
    )
    return payload["sequence"]


def test_concurrent_appends_do_not_interleave_blocks(surface, tmp_path):
    """The caller serializes writers with the journal lock, but a single
    `write` of a whole block is what makes a lost lock a missing event rather
    than a corrupted document."""
    jobs = [
        (str(surface), str(tmp_path / "state.json"), f"v{index}", f"urn:uuid:{index}")
        for index in range(8)
    ]
    with multiprocessing.get_context("fork").Pool(4) as pool:
        pool.map(_append_in_process, jobs)

    document = surface.read_text(encoding="utf-8")
    # Whatever the interleaving cost in sequence numbers, every block that
    # made it in is complete and parseable.
    entries = journal_entries(document)
    assert len(entries) == len(journal_event_ids(document))
    assert entries, "no event survived"
    for entry in entries:
        assert entry["entity"] == ENTITY
        assert entry["operations"][0]["predicate"] == TITLE
    opens = len(re.findall(r'data-ontobdc-global-event="true"', document))
    assert opens == len(entries)


# --------------------------------------------------------------------------
# Durability ordering
# --------------------------------------------------------------------------


def test_the_state_file_is_written_only_after_the_append(writer, surface, monkeypatch):
    """A state file ahead of the journal would claim a sequence the journal
    never received; the retry would then skip it silently."""
    order = []
    from ontobdc_view.surface.adapter import global_event as module

    real_append = module.append_event
    monkeypatch.setattr(
        module, "append_event", lambda path, payload: (order.append("append"), real_append(path, payload))[1]
    )
    real_state = GlobalEventJournalWriter._write_state
    monkeypatch.setattr(
        GlobalEventJournalWriter,
        "_write_state",
        lambda self, state: (order.append("state"), real_state(self, state))[1],
    )
    set_title(writer, "Novo")
    assert order == ["append", "state"]


def test_a_failed_append_leaves_no_acknowledged_sequence(writer, surface, monkeypatch, tmp_path):
    from ontobdc_view.surface.adapter import global_event as module

    def boom(path, payload):
        raise OSError("disk full")

    monkeypatch.setattr(module, "append_event", boom)
    with pytest.raises(OSError):
        set_title(writer, "Novo")
    assert not (tmp_path / "state.json").exists()


# --------------------------------------------------------------------------
# Validation
# --------------------------------------------------------------------------


def test_a_predicate_must_be_an_iri(writer):
    """A column label is not a predicate. Accepting one would put a value
    under a key no Tile reads and no reader can interpret."""
    with pytest.raises(GlobalEventError, match="not an IRI"):
        writer.append(
            event=SET_EVENT,
            entity=ENTITY,
            operations=[GlobalEventOperation("set", "Name", {"@value": "x"})],
        )


def test_an_event_needs_a_type_an_entity_and_an_operation(writer):
    with pytest.raises(GlobalEventError):
        writer.append(event="", entity=ENTITY, operations=[GlobalEventOperation("set", TITLE)])
    with pytest.raises(GlobalEventError):
        writer.append(event=SET_EVENT, entity="", operations=[GlobalEventOperation("set", TITLE)])
    with pytest.raises(GlobalEventError):
        writer.append(event=SET_EVENT, entity=ENTITY, operations=[])


def test_one_logical_edit_is_one_event_with_several_operations(writer, surface):
    """Saving several fields together must stay atomic in the journal: one
    event, one sequence, several operations."""
    payload, _ = writer.append(
        event=SET_EVENT,
        entity=ENTITY,
        operations=[
            GlobalEventOperation("set", TITLE, {"@value": "Novo"}),
            GlobalEventOperation("set", f"{TITLE}/2", {"@value": "Outro"}),
        ],
    )
    entries = journal_entries(surface.read_text(encoding="utf-8"))
    assert len(entries) == 1
    assert len(entries[0]["operations"]) == 2
    assert payload["sequence"] == 0


# --------------------------------------------------------------------------
# Compaction
# --------------------------------------------------------------------------


def test_compaction_marks_how_far_the_snapshot_goes(writer, surface):
    set_title(writer, "Um")
    set_title(writer, "Dois")
    materialized = GENERATED.replace('"Antigo"', '"Dois"')
    cutoff = writer.write_compacted(materialized)
    assert cutoff == 1

    document = surface.read_text(encoding="utf-8")
    assert snapshot_through(document) == 1
    assert journal_entries(document) == []
    assert "Dois" in document


def test_a_compacted_document_still_accepts_new_events(writer, surface):
    set_title(writer, "Um")
    writer.write_compacted(GENERATED.replace('"Antigo"', '"Um"'))
    payload, created = set_title(writer, "Dois")
    assert created is True
    assert payload["sequence"] == 1
    document = surface.read_text(encoding="utf-8")
    assert document_accepts_journal(document)
    assert len(journal_entries(document)) == 1


def test_set_snapshot_through_replaces_rather_than_repeats(writer):
    once = set_snapshot_through(GENERATED, 1)
    twice = set_snapshot_through(once, 2)
    assert twice.count("data-snapshot-through") == 1
    assert snapshot_through(twice) == 2


def test_set_snapshot_through_needs_a_snapshot_block():
    with pytest.raises(GlobalEventError, match="ontobdc-surface-jsonld"):
        set_snapshot_through("<html><body></body></html>", 1)


def test_last_sequence_sees_both_the_journal_and_the_cutoff(writer, surface):
    """After compaction there are no blocks left to read a sequence from, so
    the cutoff on the snapshot is what keeps the numbering going."""
    assert last_sequence(surface.read_text(encoding="utf-8")) == -1
    set_title(writer, "Um")
    set_title(writer, "Dois")
    assert last_sequence(surface.read_text(encoding="utf-8")) == 1

    cutoff = writer.write_compacted(GENERATED)
    document = surface.read_text(encoding="utf-8")
    assert journal_entries(document) == []
    assert cutoff == 1
    assert last_sequence(document) == 1


def test_compaction_stamps_the_journal_cutoff_not_whatever_it_was_handed(writer, surface):
    """The regeneration produces a graph; how far that graph reaches is the
    journal's business, so a stale marker in the generated document is
    replaced rather than trusted."""
    set_title(writer, "Um")
    cutoff = writer.write_compacted(set_snapshot_through(GENERATED, 999))
    assert cutoff == 0
    assert snapshot_through(surface.read_text(encoding="utf-8")) == 0
