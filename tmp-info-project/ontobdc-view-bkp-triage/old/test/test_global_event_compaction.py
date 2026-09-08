"""Regenerating a Surface folds the journal into the new snapshot.

A regeneration re-reads the canonical sources, so the snapshot it produces
already contains every change the journal was carrying — up to the instant
those sources were read. Replaying those again after a reload would apply
the same edit twice; dropping the ones that arrived *after* that instant
would lose an edit the user really made. The cutoff is the line between
them, and it is a moment in time, not a property of the document.

That is why the writer takes it in two steps while the old document is
still on disk (`open_regeneration` when the sources are read,
`close_regeneration` just before the document is replaced) and spends it in
one (`apply`, on the freshly built document). By the time the new
`index.html` is written, the old one — and the cutoff only it knew — is
gone.

The last group runs the result in Chromium over `file://`: the compacted
document has to behave, on reload, exactly like the document it replaced.
"""

import json
from pathlib import Path

import pytest

import ontobdc_view
from ontobdc_view.surface.adapter.global_event import (
    GlobalEventJournalWriter,
    GlobalEventOperation,
    JournalCarryOver,
    journal_entries,
    last_sequence,
    prepare_document_for_journal,
    set_snapshot_through,
    snapshot_through,
)

from test_global_event_replay import (
    CHROMIUM,
    ENTITY,
    SET_EVENT,
    WHAT,
    browser,  # noqa: F401 — the module-scoped Chromium fixture
    build_document,
    event,
    op,
    snapshot,
)

browsertest = pytest.mark.skipif(
    not Path(CHROMIUM).exists(), reason="the packaged Chromium build is not present"
)


def surface(nodes=None, events=(), through=None) -> str:
    return prepare_document_for_journal(
        build_document(nodes if nodes is not None else snapshot(), list(events), through)
    )


@pytest.fixture
def container(tmp_path):
    (tmp_path / ".__ontobdc__").mkdir()
    return tmp_path


@pytest.fixture
def writer(container):
    return GlobalEventJournalWriter(
        container / "index.html", container / ".__ontobdc__" / "global_event_sequence.json"
    )


def write_surface(container: Path, document: str) -> None:
    (container / "index.html").write_text(document, encoding="utf-8")


def set_op(value: str) -> GlobalEventOperation:
    return GlobalEventOperation(operation="set", predicate=WHAT, value={"@value": value})


def append(writer: GlobalEventJournalWriter, value: str) -> dict:
    payload, _ = writer.append(
        event=ontobdc_view.global_event_iri_for_operation("set"),
        entity=ENTITY,
        operations=[set_op(value)],
    )
    return payload


# --------------------------------------------------------------------------
# snapshot + journal -> regeneration -> compacted snapshot
# --------------------------------------------------------------------------


def test_a_regeneration_absorbs_the_journal_it_replaces(writer, container):
    """Three events on the old document; the sources were re-read after all
    three, so the new snapshot carries their effects and no block."""
    write_surface(container, surface())
    for value in ("um", "dois", "tres"):
        append(writer, value)
    assert len(journal_entries((container / "index.html").read_text(encoding="utf-8"))) == 3

    carry_over = writer.open_regeneration()
    closed = writer.close_regeneration()
    regenerated = surface([{"@id": ENTITY, WHAT: [{"@value": "tres"}]}])
    compacted = closed.apply(regenerated)

    assert journal_entries(compacted) == []
    assert carry_over.cutoff == closed.cutoff


def test_the_compacted_document_still_accepts_the_next_event(writer, container):
    write_surface(container, surface())
    append(writer, "um")
    writer.open_regeneration()
    closed = writer.close_regeneration()
    compacted = closed.apply(surface([{"@id": ENTITY, WHAT: [{"@value": "um"}]}]))
    write_surface(container, compacted)
    writer.settle_regeneration(compacted)

    payload = append(writer, "dois")
    document = (container / "index.html").read_text(encoding="utf-8")
    assert [entry["sequence"] for entry in journal_entries(document)] == [payload["sequence"]]


# --------------------------------------------------------------------------
# the cutoff is right
# --------------------------------------------------------------------------


def test_the_cutoff_is_the_last_event_the_sources_had_when_they_were_read(writer, container):
    write_surface(container, surface())
    first = append(writer, "um")
    second = append(writer, "dois")

    carry_over = writer.open_regeneration()
    assert carry_over.cutoff == second["sequence"]
    assert carry_over.cutoff > first["sequence"]


def test_an_empty_journal_puts_the_cutoff_before_every_event(writer, container):
    write_surface(container, surface())
    assert writer.open_regeneration().cutoff == -1


def test_a_previous_compaction_is_not_forgotten(writer, container):
    """After a compaction the blocks are gone but `data-snapshot-through`
    remains. Reading only the blocks would send the cutoff backwards and
    make the next regeneration claim it materialized nothing."""
    write_surface(container, set_snapshot_through(surface(), 42))
    assert writer.open_regeneration().cutoff == 42


def test_the_cutoff_never_advances_past_what_the_snapshot_holds(writer, container):
    """An event journaled after the sources were read is not in the new
    snapshot, and the cutoff must not pretend otherwise."""
    write_surface(container, surface())
    append(writer, "um")
    writer.open_regeneration()
    late = append(writer, "dois")  # arrives while the new Surface is built

    closed = writer.close_regeneration()
    assert closed.cutoff < late["sequence"]
    compacted = closed.apply(surface([{"@id": ENTITY, WHAT: [{"@value": "um"}]}]))
    assert snapshot_through(compacted) == closed.cutoff


def test_the_cutoff_is_read_before_the_generation_overwrites_the_document(writer, container):
    """The number lives in the document the generation is about to replace.
    Taken afterwards, it reads a fresh page and comes back as -1 — which
    would make every past event replay again over a snapshot that has them."""
    write_surface(container, surface())
    append(writer, "um")
    second = append(writer, "dois")

    closed = writer.open_regeneration().closed(
        (container / "index.html").read_text(encoding="utf-8")
    )
    write_surface(container, "<html><body>a freshly initialized Surface")
    assert closed.cutoff == second["sequence"]
    assert JournalCarryOver.opened(
        (container / "index.html").read_text(encoding="utf-8")
    ).cutoff == -1


# --------------------------------------------------------------------------
# nothing is lost while the Surface is being rebuilt
# --------------------------------------------------------------------------


def test_an_event_that_lands_mid_regeneration_is_carried_over(writer, container):
    write_surface(container, surface())
    append(writer, "um")
    writer.open_regeneration()
    late = append(writer, "dois")

    closed = writer.close_regeneration()
    assert [entry["eventId"] for entry in closed.entries] == [late["eventId"]]

    compacted = closed.apply(surface([{"@id": ENTITY, WHAT: [{"@value": "um"}]}]))
    carried = journal_entries(compacted)
    assert [entry["eventId"] for entry in carried] == [late["eventId"]]
    assert carried[0]["sequence"] == late["sequence"]


def test_a_carried_event_keeps_its_identity_rather_than_being_reissued(writer, container):
    """Same id, same sequence. A new id would defeat the de-duplication a
    retried submission relies on; a new sequence would reorder it against
    events that really did come after it."""
    write_surface(container, surface())
    writer.open_regeneration()
    late = append(writer, "tarde")
    closed = writer.close_regeneration()

    entry = journal_entries(closed.apply(surface()))[0]
    assert entry == late


def test_several_late_events_are_carried_in_the_order_they_happened(writer, container):
    write_surface(container, surface())
    writer.open_regeneration()
    first = append(writer, "um")
    second = append(writer, "dois")
    third = append(writer, "tres")

    entries = journal_entries(writer.close_regeneration().apply(surface()))
    assert [entry["sequence"] for entry in entries] == [
        first["sequence"],
        second["sequence"],
        third["sequence"],
    ]


def test_the_numbering_continues_past_a_regeneration(writer, container):
    write_surface(container, surface())
    append(writer, "um")
    last = append(writer, "dois")
    writer.open_regeneration()
    compacted = writer.close_regeneration().apply(surface())
    write_surface(container, compacted)
    writer.settle_regeneration(compacted)

    assert append(writer, "tres")["sequence"] == last["sequence"] + 1


def test_a_spent_carry_over_is_not_applied_twice(writer, container):
    """Left in the state file, the next regeneration would re-attach events
    the document it is compacting already carries."""
    write_surface(container, surface())
    writer.open_regeneration()
    append(writer, "tarde")
    compacted = writer.close_regeneration().apply(surface())
    write_surface(container, compacted)
    writer.settle_regeneration(compacted)
    assert writer.carry_over() is None

    again = writer.open_regeneration()
    assert again.entries == ()
    assert journal_entries(again.closed(compacted).apply(surface())) == []


def test_closing_without_opening_still_loses_nothing(writer, container):
    """A lifecycle that skipped the first step treats the whole document as
    materialized — the same answer opening now would give — rather than
    carrying an undefined cutoff into the new snapshot."""
    write_surface(container, surface())
    last = append(writer, "um")
    assert writer.close_regeneration().cutoff == last["sequence"]


# --------------------------------------------------------------------------
# what a reload actually shows
# --------------------------------------------------------------------------


def read_values(page, entity=ENTITY):
    graph = page.evaluate("window.__READ_BY_COMPONENT__")
    return next(node for node in graph if node["@id"] == entity)


def open_page(browser, path):
    page = browser.new_page()
    page.goto(Path(path).as_uri())
    return page


@browsertest
def test_a_reload_does_not_reapply_what_the_snapshot_absorbed(browser, tmp_path):
    """The compacted document has no blocks left to reapply, and says so
    with its cutoff. Both halves are checked: what it shows, and that the
    replay reports having applied nothing."""
    writer = GlobalEventJournalWriter(
        tmp_path / "index.html", tmp_path / "global_event_sequence.json"
    )
    write_surface(tmp_path, surface())
    append(writer, "materializado")
    writer.open_regeneration()
    closed = writer.close_regeneration()
    compacted = closed.apply(surface([{"@id": ENTITY, WHAT: [{"@value": "materializado"}]}]))
    write_surface(tmp_path, compacted)
    writer.settle_regeneration(compacted)

    page = open_page(browser, tmp_path / "index.html")
    assert read_values(page)[WHAT] == [{"@value": "materializado"}]
    assert page.evaluate("window.OntoBDCGlobalEventRuntime.replayedEventIds") == []
    page.close()


@browsertest
def test_an_event_after_the_cutoff_is_still_replayed_after_a_regeneration(browser, tmp_path):
    """The cutoff hides what the snapshot has; it must not hide what came
    next. A document that suppressed both would silently drop the edit."""
    document = build_document(
        [{"@id": ENTITY, "@type": ["urn:WorkStream"], WHAT: [{"@value": "materializado"}]}],
        [event(7, op("set", WHAT, {"@value": "depois"}))],
        snapshot_through=5,
    )
    (tmp_path / "index.html").write_text(document, encoding="utf-8")

    page = open_page(browser, tmp_path / "index.html")
    assert read_values(page)[WHAT] == [{"@value": "depois"}]
    assert page.evaluate("window.OntoBDCGlobalEventRuntime.replayedEventIds") == [
        "urn:uuid:evt-7"
    ]
    page.close()


@browsertest
def test_a_regeneration_that_lost_the_cutoff_would_be_visible_here(browser, tmp_path):
    """The negative control for the bug this closes: a compacted snapshot
    stamped `-1` instead of its real cutoff. The value shown is the same
    either way — the difference is that every past event is replayed again,
    and that is what a lost mutation looks like the moment the operations
    stop being idempotent."""
    document = build_document(
        [{"@id": ENTITY, "@type": ["urn:WorkStream"], WHAT: [{"@value": "materializado"}]}],
        [event(5, op("set", WHAT, {"@value": "materializado"}))],
        snapshot_through=-1,
    )
    (tmp_path / "index.html").write_text(document, encoding="utf-8")
    page = open_page(browser, tmp_path / "index.html")
    assert page.evaluate("window.OntoBDCGlobalEventRuntime.replayedEventIds") == [
        "urn:uuid:evt-5"
    ]
    page.close()


@browsertest
def test_a_mutation_made_during_a_regeneration_survives_the_reload(browser, tmp_path):
    """End to end for the window the two-step cutoff exists to cover: the
    sources were read, the event landed while the Surface was being rebuilt,
    and reopening the rebuilt page shows it."""
    writer = GlobalEventJournalWriter(
        tmp_path / "index.html", tmp_path / "global_event_sequence.json"
    )
    write_surface(tmp_path, surface())
    append(writer, "materializado")
    writer.open_regeneration()
    append(writer, "durante a regeneracao")
    closed = writer.close_regeneration()

    compacted = closed.apply(surface([{"@id": ENTITY, WHAT: [{"@value": "materializado"}]}]))
    write_surface(tmp_path, compacted)
    writer.settle_regeneration(compacted)

    page = open_page(browser, tmp_path / "index.html")
    assert read_values(page)[WHAT] == [{"@value": "durante a regeneracao"}]
    page.close()
