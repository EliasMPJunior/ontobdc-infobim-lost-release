"""The Global Event replay runtime, exercised as the browser runs it.

Two levels, both against the shipped `global_event_replay.js`:

* the reducer and the ordering rules, driven directly in Node;
* the whole runtime, in Chromium, on a real `file://` document — because
  `file://` is the mode this mechanism exists for, and the thing it
  replaces failed precisely there.

Nothing here stubs the ontology: the accepted event IRIs and the operation
each one carries are resolved from BrasidataCenter's
`presentation_event.ttl` by `global_event_replay_source()`, exactly as a
generated page receives them.
"""

import json
import re
import shutil
import subprocess
import tempfile
from pathlib import Path

import pytest

import ontobdc_view
from ontobdc_view.component.adapter.global_event import (
    global_event_iris,
    global_event_operations,
)

NODE = shutil.which("node")
CHROMIUM = "/opt/pw-browsers/chromium-1194/chrome-linux/chrome"

EVENT_NS = "http://datacenter.app.br/ontology/ontobdc/abox/presentation_event.ttl#"
SET_EVENT = f"{EVENT_NS}EntityPropertySet"
UNSET_EVENT = f"{EVENT_NS}EntityPropertyUnset"
ADD_EVENT = f"{EVENT_NS}EntityRelationAdded"
REMOVE_EVENT = f"{EVENT_NS}EntityRelationRemoved"

TITLE = "http://purl.org/dc/terms/title"
WHAT = "http://datacenter.app.br/ontology/productivity/entity/work_stream/type.ttl#what"
RELATED = "http://purl.org/dc/terms/relation"

ENTITY = "urn:ontobdc:work_stream:WS-1"
OTHER_ENTITY = "urn:ontobdc:work_stream:WS-2"


def snapshot(nodes=None):
    return nodes if nodes is not None else [
        {
            "@id": ENTITY,
            "@type": ["urn:WorkStream"],
            TITLE: [{"@value": "Fundação", "@language": "pt-BR"}],
            WHAT: [{"@value": "antigo"}],
        },
        {
            "@id": OTHER_ENTITY,
            "@type": ["urn:WorkStream"],
            TITLE: [{"@value": "Estrutura", "@language": "pt-BR"}],
        },
    ]


def event(sequence, *operations, event_type=SET_EVENT, entity=ENTITY, event_id=None):
    return {
        "event": event_type,
        "eventId": event_id or f"urn:uuid:evt-{sequence}",
        "sequence": sequence,
        "occurredAt": "2026-08-31T00:00:00Z",
        "source": {"kind": "xlsx", "dataset": "ds", "resource": "work_stream"},
        "entity": entity,
        "operations": list(operations),
    }


def op(operation, predicate, value=None):
    payload = {"operation": operation, "predicate": predicate}
    if value is not None:
        payload["value"] = value
    return payload


def journal_block(payload):
    body = json.dumps(payload, ensure_ascii=False).replace("<", "\\u003c")
    return (
        f'<script type="application/ld+json" data-ontobdc-global-event="true" '
        f'data-event-id="{payload["eventId"]}" data-sequence="{payload["sequence"]}">\n'
        f"{body}\n</script>"
    )


def build_document(snapshot_nodes, events, snapshot_through=None, before_replay=""):
    """A page shaped like a generated Surface: the snapshot, then the replay
    module, then the component modules, then the append-only journal at the
    very end of the body.

    Every module is inlined, exactly as `embed_component_scripts` inlines
    them. A `src=` module would not run at all here: on `file://` its fetch
    is cross-origin from an opaque origin and Chromium blocks it.
    """
    through = "" if snapshot_through is None else f' data-snapshot-through="{snapshot_through}"'
    body = json.dumps(snapshot_nodes, ensure_ascii=False).replace("<", "\\u003c")
    journal = "\n".join(journal_block(payload) for payload in events)
    replay = ontobdc_view.global_event_replay_source().replace("</script>", "<\\/script>")
    reader = READER.replace("</script>", "<\\/script>")
    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>Surface</title>
</head>
<body>
<script type="application/ld+json" id="ontobdc-surface-jsonld"{through}>
{body}
</script>
{before_replay}
<script type="module">
{replay}
</script>
<script type="module">
{reader}
</script>
{journal}
</body>
</html>
"""


# The "component module": emitted after the replay module, it stands in for a
# Tile reading the graph in `connectedCallback`. Whatever it records is what a
# real Tile would have rendered.
READER = """
const script = document.getElementById("ontobdc-surface-jsonld");
const graph = JSON.parse(script.textContent);
window.__READ_BY_COMPONENT__ = Array.isArray(graph) ? graph : [graph];
window.__READ_AFTER_REPLAY__ = Boolean(window.OntoBDCGlobalEventRuntime);
"""


# --------------------------------------------------------------------------
# The reducer, driven directly (Node)
# --------------------------------------------------------------------------

nodeonly = pytest.mark.skipif(NODE is None, reason="node is not available")


def run_in_node(snapshot_nodes, events, snapshot_through=None):
    """Applies a journal through the shipped module's own exported reducer."""
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        # The module runs its own `run()` at import against whatever document
        # exists, so give it the smallest one that satisfies it, then drive the
        # exported reducer directly with the case under test.
        (root / "replay.mjs").write_text(
            ontobdc_view.global_event_replay_source(), encoding="utf-8"
        )
        (root / "harness.mjs").write_text(
            """
const listeners = new Map();
globalThis.document = {
  getElementById: () => null,
  querySelectorAll: () => [],
  dispatchEvent: () => true,
  addEventListener: () => {},
};
globalThis.window = globalThis;
globalThis.addEventListener = () => {};
const { replay, validate } = await import("./replay.mjs");
const input = JSON.parse(process.env.ONTOBDC_INPUT);
const errors = [];
const events = input.events.map((e) => validate(e, errors)).filter((e) => e !== null);
const result = replay(input.nodes, events, input.through, errors);
process.stdout.write(JSON.stringify({ nodes: input.nodes, errors, ...result }));
""",
            encoding="utf-8",
        )
        completed = subprocess.run(
            [NODE, str(root / "harness.mjs")],
            capture_output=True,
            text=True,
            timeout=120,
            env={
                "PATH": "/usr/bin:/bin:/usr/local/bin",
                "ONTOBDC_INPUT": json.dumps(
                    {
                        "nodes": snapshot_nodes,
                        "events": events,
                        "through": -1 if snapshot_through is None else snapshot_through,
                    }
                ),
            },
        )
        if completed.returncode != 0:
            pytest.fail(f"reducer harness failed:\n{completed.stderr}")
        return json.loads(completed.stdout)


def node_of(result, entity=ENTITY):
    return next(node for node in result["nodes"] if node["@id"] == entity)


@nodeonly
def test_set_creates_a_property_that_was_absent():
    result = run_in_node(snapshot(), [event(1, op("set", RELATED, {"@value": "novo"}))])
    assert node_of(result)[RELATED] == [{"@value": "novo"}]


@nodeonly
def test_set_replaces_an_existing_value():
    result = run_in_node(snapshot(), [event(1, op("set", WHAT, {"@value": "novo"}))])
    assert node_of(result)[WHAT] == [{"@value": "novo"}]


@nodeonly
def test_set_preserves_the_language_the_event_did_not_replace():
    """A label edited through a spreadsheet column carries no language tag.
    Dropping the one the snapshot had would silently change the triple."""
    result = run_in_node(snapshot(), [event(1, op("set", TITLE, {"@value": "Sapata"}))])
    assert node_of(result)[TITLE] == [{"@value": "Sapata", "@language": "pt-BR"}]


@nodeonly
def test_an_event_may_replace_the_language_explicitly():
    result = run_in_node(
        snapshot(), [event(1, op("set", TITLE, {"@value": "Footing", "@language": "en"}))]
    )
    assert node_of(result)[TITLE] == [{"@value": "Footing", "@language": "en"}]


@nodeonly
def test_a_typed_literal_keeps_its_datatype():
    nodes = [{"@id": ENTITY, WHAT: [{"@value": "1", "@type": "http://www.w3.org/2001/XMLSchema#integer"}]}]
    result = run_in_node(nodes, [event(1, op("set", WHAT, {"@value": "2"}))])
    assert node_of(result)[WHAT] == [
        {"@value": "2", "@type": "http://www.w3.org/2001/XMLSchema#integer"}
    ]


@nodeonly
def test_unset_removes_the_property():
    result = run_in_node(
        snapshot(), [event(1, op("unset", WHAT), event_type=UNSET_EVENT)]
    )
    assert WHAT not in node_of(result)


@nodeonly
def test_set_and_unset_are_idempotent():
    once = run_in_node(snapshot(), [event(1, op("set", WHAT, {"@value": "novo"}))])
    twice = run_in_node(
        snapshot(),
        [
            event(1, op("set", WHAT, {"@value": "novo"})),
            event(2, op("set", WHAT, {"@value": "novo"})),
        ],
    )
    assert node_of(once)[WHAT] == node_of(twice)[WHAT]

    gone = run_in_node(
        snapshot(),
        [
            event(1, op("unset", WHAT), event_type=UNSET_EVENT),
            event(2, op("unset", WHAT), event_type=UNSET_EVENT, event_id="urn:uuid:evt-2b"),
        ],
    )
    assert WHAT not in node_of(gone)


@nodeonly
def test_add_and_remove_operate_on_relations():
    added = run_in_node(
        snapshot(),
        [event(1, op("add", RELATED, {"@id": "urn:doc:1"}), event_type=ADD_EVENT)],
    )
    assert node_of(added)[RELATED] == [{"@id": "urn:doc:1"}]

    removed = run_in_node(
        snapshot(),
        [
            event(1, op("add", RELATED, {"@id": "urn:doc:1"}), event_type=ADD_EVENT),
            event(
                2,
                op("remove", RELATED, {"@id": "urn:doc:1"}),
                event_type=REMOVE_EVENT,
            ),
        ],
    )
    assert RELATED not in node_of(removed)


@nodeonly
def test_add_does_not_duplicate_an_existing_relation():
    result = run_in_node(
        snapshot(),
        [
            event(1, op("add", RELATED, {"@id": "urn:doc:1"}), event_type=ADD_EVENT),
            event(
                2,
                op("add", RELATED, {"@id": "urn:doc:1"}),
                event_type=ADD_EVENT,
                event_id="urn:uuid:evt-2b",
            ),
        ],
    )
    assert node_of(result)[RELATED] == [{"@id": "urn:doc:1"}]


# --- ordering, cutoff, duplicates, diagnostics ----------------------------


@nodeonly
def test_events_are_applied_in_sequence_order_not_document_order():
    """The later edit to the same field must win no matter how the blocks
    happen to sit in the file."""
    result = run_in_node(
        snapshot(),
        [
            event(7, op("set", WHAT, {"@value": "sétimo"})),
            event(3, op("set", WHAT, {"@value": "terceiro"})),
        ],
    )
    assert node_of(result)[WHAT] == [{"@value": "sétimo"}]
    assert result["lastSequence"] == 7


@nodeonly
def test_events_already_in_the_snapshot_are_ignored():
    result = run_in_node(
        snapshot(),
        [
            event(41, op("set", WHAT, {"@value": "compactado"})),
            event(42, op("set", TITLE, {"@value": "novo"})),
        ],
        snapshot_through=41,
    )
    assert node_of(result)[WHAT] == [{"@value": "antigo"}]  # untouched
    assert result["replayedEventIds"] == ["urn:uuid:evt-42"]


@nodeonly
def test_a_redelivered_event_id_is_applied_once():
    result = run_in_node(
        snapshot(),
        [
            event(1, op("add", RELATED, {"@id": "urn:doc:1"}), event_type=ADD_EVENT),
            event(
                2,
                op("add", RELATED, {"@id": "urn:doc:2"}),
                event_type=ADD_EVENT,
                event_id="urn:uuid:evt-1",
            ),
        ],
    )
    assert node_of(result)[RELATED] == [{"@id": "urn:doc:1"}]
    assert result["replayedEventIds"] == ["urn:uuid:evt-1"]


@nodeonly
def test_an_unknown_entity_is_reported_without_stopping_the_replay():
    result = run_in_node(
        snapshot(),
        [
            event(1, op("set", WHAT, {"@value": "perdido"}), entity="urn:ontobdc:missing"),
            event(2, op("set", WHAT, {"@value": "aplicado"})),
        ],
    )
    assert node_of(result)[WHAT] == [{"@value": "aplicado"}]
    assert any(error["reason"] == "unknown-entity" for error in result["errors"])


@nodeonly
def test_an_invalid_event_does_not_block_the_valid_ones_after_it():
    broken = event(1, op("set", WHAT, {"@value": "x"}))
    del broken["eventId"]
    unknown_type = event(2, op("set", WHAT, {"@value": "y"}))
    unknown_type["event"] = "urn:not:an:event"
    result = run_in_node(
        snapshot(), [broken, unknown_type, event(3, op("set", WHAT, {"@value": "válido"}))]
    )
    assert node_of(result)[WHAT] == [{"@value": "válido"}]
    reasons = {error["reason"] for error in result["errors"]}
    assert {"missing-event-id", "unknown-event-type"} <= reasons


@nodeonly
def test_an_operation_the_event_does_not_declare_is_refused():
    """`EntityPropertySet` carries `set`. A block claiming it deletes
    something is rejected rather than obeyed."""
    result = run_in_node(
        snapshot(), [event(1, op("unset", WHAT), event_type=SET_EVENT)]
    )
    assert node_of(result)[WHAT] == [{"@value": "antigo"}]
    assert any(error["reason"] == "operation-not-allowed" for error in result["errors"])


@nodeonly
def test_two_entities_do_not_receive_each_others_values():
    result = run_in_node(
        snapshot(),
        [
            event(1, op("set", TITLE, {"@value": "Um"})),
            event(2, op("set", TITLE, {"@value": "Dois"}), entity=OTHER_ENTITY),
        ],
    )
    assert node_of(result)[TITLE][0]["@value"] == "Um"
    assert node_of(result, OTHER_ENTITY)[TITLE][0]["@value"] == "Dois"


# --------------------------------------------------------------------------
# The vocabulary comes from the ontology
# --------------------------------------------------------------------------


def test_the_accepted_event_iris_come_from_the_graph():
    source = ontobdc_view.global_event_replay_source()
    for iri in global_event_iris():
        assert json.dumps(iri) in source
    assert "__ONTOBDC_BUILD_" not in source


def test_the_runtime_holds_no_vocabulary_of_its_own():
    """The event names must not be spelled out in the JavaScript: adding an
    event to the ontology is what makes it replayable."""
    raw = (
        Path(ontobdc_view.__file__).parent / "component/asset/global_event_replay.js"
    ).read_text(encoding="utf-8")
    code = "\n".join(re.sub(r"//.*$", "", line) for line in raw.splitlines())
    for name in ("EntityPropertySet", "EntityPropertyUnset", "EntityRelationAdded", "EntityRelationRemoved"):
        assert name not in code, name
    assert "__ONTOBDC_BUILD_GLOBAL_EVENT_IRIS__" in code
    assert "__ONTOBDC_BUILD_GLOBAL_EVENT_OPERATIONS__" in code


def test_an_operation_the_reducer_cannot_apply_fails_the_build(monkeypatch):
    from ontobdc_view.component.adapter import global_event as module

    graph = module._policy_graph()
    graph.add(
        (
            module.VIEW["http://example.org/x"] if False else
            __import__("rdflib").URIRef(f"{EVENT_NS}EntityPropertySet"),
            module.VIEW.appliesOperation,
            __import__("rdflib").Literal("teleport"),
        )
    )
    monkeypatch.setattr(module, "_policy_graph", lambda: graph)
    with pytest.raises(ValueError, match="teleport"):
        module.global_event_operations()


def test_every_declared_event_maps_to_exactly_one_operation():
    operations = global_event_operations()
    assert len(operations) == 4
    assert sorted(sum(operations.values(), [])) == ["add", "remove", "set", "unset"]


# --------------------------------------------------------------------------
# The whole runtime, in Chromium, on file://
# --------------------------------------------------------------------------

browsertest = pytest.mark.skipif(
    not Path(CHROMIUM).exists(), reason="the packaged Chromium build is not present"
)


@pytest.fixture(scope="module")
def browser():
    playwright = pytest.importorskip("playwright.sync_api")
    with playwright.sync_playwright() as p:
        instance = p.chromium.launch(executable_path=CHROMIUM)
        yield instance
        instance.close()


def write_page(root: Path, snapshot_nodes, events, snapshot_through=None):
    page = root / "index.html"
    page.write_text(
        build_document(snapshot_nodes, events, snapshot_through), encoding="utf-8"
    )
    return page


def read_values(page, entity=ENTITY):
    graph = page.evaluate("window.__READ_BY_COMPONENT__")
    return next(node for node in graph if node["@id"] == entity)


@browsertest
def test_a_file_url_surface_shows_the_snapshot_until_an_event_arrives(browser, tmp_path):
    page_path = write_page(tmp_path, snapshot(), [])
    page = browser.new_page()
    page.goto(page_path.as_uri())
    assert read_values(page)[WHAT] == [{"@value": "antigo"}]
    page.close()


@browsertest
def test_appending_an_event_and_reloading_shows_the_new_value(browser, tmp_path):
    """The whole point: the file on disk grew by one block, and reopening it
    is all it takes. No IndexedDB, no directory picker, no workbook."""
    page_path = write_page(tmp_path, snapshot(), [])
    page = browser.new_page()
    page.goto(page_path.as_uri())
    assert read_values(page)[WHAT] == [{"@value": "antigo"}]

    with page_path.open("a", encoding="utf-8") as handle:
        handle.write("\n" + journal_block(event(1, op("set", WHAT, {"@value": "novo"}))))

    page.reload()
    assert read_values(page)[WHAT] == [{"@value": "novo"}]
    page.close()


@browsertest
def test_the_later_event_wins_for_the_same_field(browser, tmp_path):
    page_path = write_page(
        tmp_path,
        snapshot(),
        [
            event(1, op("set", WHAT, {"@value": "primeiro"})),
            event(2, op("set", WHAT, {"@value": "segundo"})),
        ],
    )
    page = browser.new_page()
    page.goto(page_path.as_uri())
    assert read_values(page)[WHAT] == [{"@value": "segundo"}]
    page.close()


@browsertest
def test_the_value_survives_a_new_browser_context(browser, tmp_path):
    """Nothing about the new state lives in the browser: it is in the file."""
    page_path = write_page(
        tmp_path, snapshot(), [event(1, op("set", WHAT, {"@value": "persistido"}))]
    )
    first = browser.new_context()
    page = first.new_page()
    page.goto(page_path.as_uri())
    assert read_values(page)[WHAT] == [{"@value": "persistido"}]
    first.close()

    second = browser.new_context()
    page = second.new_page()
    page.goto(page_path.as_uri())
    assert read_values(page)[WHAT] == [{"@value": "persistido"}]
    second.close()


@browsertest
def test_the_replay_finishes_before_a_component_reads_the_graph(browser, tmp_path):
    """Ordering is the whole reason no Tile needs a refresh path: the module
    emitted after the replay already reads materialized values."""
    page_path = write_page(
        tmp_path, snapshot(), [event(1, op("set", WHAT, {"@value": "materializado"}))]
    )
    page = browser.new_page()
    page.goto(page_path.as_uri())
    assert page.evaluate("window.__READ_AFTER_REPLAY__") is True
    assert read_values(page)[WHAT] == [{"@value": "materializado"}]
    page.close()


@browsertest
def test_a_value_containing_a_script_end_tag_does_not_break_the_document(browser, tmp_path):
    """A spreadsheet cell is user data. `</script>` inside a JSON-LD block
    still closes it as far as the HTML parser is concerned, so the writer
    escapes `<`; this proves the escaped form survives the round trip."""
    hostile = 'antes </script><img src=x onerror="window.__PWNED__=true"> depois'
    page_path = write_page(
        tmp_path, snapshot(), [event(1, op("set", WHAT, {"@value": hostile}))]
    )
    page = browser.new_page()
    page.goto(page_path.as_uri())
    assert page.evaluate("window.__PWNED__ === true") is False
    assert read_values(page)[WHAT] == [{"@value": hostile}]
    page.close()


@browsertest
def test_compaction_reproduces_exactly_what_replay_produced(browser, tmp_path):
    """After a regeneration folds the journal into the snapshot, the page must
    look identical — and must not re-apply the events it already absorbed."""
    events = [
        event(1, op("set", WHAT, {"@value": "um"})),
        event(2, op("set", TITLE, {"@value": "Dois"})),
    ]
    before = tmp_path / "before"
    before.mkdir()
    page_path = write_page(before, snapshot(), events)
    page = browser.new_page()
    page.goto(page_path.as_uri())
    replayed = read_values(page)
    page.close()

    # What a regeneration writes: the materialized graph, marked as already
    # containing everything up to sequence 2, with the journal dropped.
    after = tmp_path / "after"
    after.mkdir()
    compacted_path = write_page(after, [replayed, snapshot()[1]], [], snapshot_through=2)
    page = browser.new_page()
    page.goto(compacted_path.as_uri())
    assert read_values(page) == replayed
    assert page.evaluate("window.OntoBDCGlobalEventRuntime.replayedEventIds") == []
    page.close()


@browsertest
def test_a_stale_journal_left_after_compaction_is_not_reapplied(browser, tmp_path):
    """Belt and braces: even if a compacted event's block is still in the
    file, `data-snapshot-through` keeps it out of the replay."""
    page_path = write_page(
        tmp_path,
        [{"@id": ENTITY, WHAT: [{"@value": "compactado"}]}],
        [event(1, op("set", WHAT, {"@value": "obsoleto"}))],
        snapshot_through=1,
    )
    page = browser.new_page()
    page.goto(page_path.as_uri())
    assert read_values(page)[WHAT] == [{"@value": "compactado"}]
    page.close()


@browsertest
def test_the_surface_needs_no_indexeddb_and_opens_no_workbook(browser, tmp_path):
    """The failure this replaces: the Surface asked IndexedDB for a directory
    handle it could never see across `file://` origins, and said nothing when
    it was missing."""
    page_path = write_page(
        tmp_path, snapshot(), [event(1, op("set", WHAT, {"@value": "novo"}))]
    )
    page = browser.new_page()
    page.add_init_script(
        """
        window.__INDEXEDDB_USED__ = false;
        const open = indexedDB.open.bind(indexedDB);
        indexedDB.open = (...args) => { window.__INDEXEDDB_USED__ = true; return open(...args); };
        window.__PICKER_USED__ = false;
        window.showDirectoryPicker = () => { window.__PICKER_USED__ = true; };
        """
    )
    requests = []
    page.on("request", lambda request: requests.append(request.url))
    page.goto(page_path.as_uri())
    assert read_values(page)[WHAT] == [{"@value": "novo"}]
    assert page.evaluate("window.__INDEXEDDB_USED__") is False
    assert page.evaluate("window.__PICKER_USED__") is False
    assert not [url for url in requests if url.endswith(".xlsx")]
    page.close()


@browsertest
def test_the_runtime_reports_what_it_did(browser, tmp_path):
    page_path = write_page(
        tmp_path,
        snapshot(),
        [event(1, op("set", WHAT, {"@value": "novo"}))],
        snapshot_through=0,
    )
    page = browser.new_page()
    page.goto(page_path.as_uri())
    state = page.evaluate("window.OntoBDCGlobalEventRuntime")
    assert state["snapshotThrough"] == 0
    assert state["replayedEventIds"] == ["urn:uuid:evt-1"]
    assert state["lastSequence"] == 1
    assert state["errors"] == []
    page.close()


@browsertest
def test_the_replay_announces_itself_without_promoting_anything(browser, tmp_path):
    """`GlobalEventsReplayed` is a Component Event with no `view:promotesTo`,
    so replaying persisted history never re-enters the promotion chain."""
    page_path = write_page(
        tmp_path, snapshot(), [event(1, op("set", WHAT, {"@value": "novo"}))]
    )
    listener = """<script type="module">
window.__COMPONENT_EVENTS__ = [];
document.addEventListener("ontobdc:component-event", (e) => {
  window.__COMPONENT_EVENTS__.push(e.detail);
});
</script>"""
    document = build_document(
        snapshot(),
        [event(1, op("set", WHAT, {"@value": "novo"}))],
        before_replay=listener,
    )
    (tmp_path / "index.html").write_text(document, encoding="utf-8")
    page = browser.new_page()
    page.goto((tmp_path / "index.html").as_uri())
    announced = page.evaluate("window.__COMPONENT_EVENTS__")
    assert [detail["event"] for detail in announced] == ["GlobalEventsReplayed"]
    assert announced[0]["replayed"] == 1
    page.close()


# --------------------------------------------------------------------------
# The two halves meet: OntoBDC writes the journal, the browser replays it
# --------------------------------------------------------------------------

writer_module = pytest.importorskip(
    "ontobdc.view.adapter.surface.global_event",
    reason="the OntoBDC journal writer is not installed",
)


def generated_surface(nodes) -> str:
    """A document shaped like a generated Surface, with the replay runtime
    and a component module inlined in the order the generator emits them."""
    return build_document(nodes, [])


@browsertest
def test_a_journal_written_by_ontobdc_is_replayed_by_the_browser(browser, tmp_path):
    """The end-to-end contract between the two repositories: the writer's
    escaping, sequencing and block shape are what the runtime's parsing,
    ordering and cutoff rules read. Neither side is stubbed."""
    page_path = tmp_path / "index.html"
    page_path.write_text(
        writer_module.prepare_document_for_journal(generated_surface(snapshot())),
        encoding="utf-8",
    )
    writer = writer_module.GlobalEventJournalWriter(page_path, tmp_path / "state.json")

    page = browser.new_page()
    page.goto(page_path.as_uri())
    assert read_values(page)[WHAT] == [{"@value": "antigo"}]

    writer.append(
        event=SET_EVENT,
        entity=ENTITY,
        operations=[writer_module.GlobalEventOperation("set", WHAT, {"@value": "escrito"})],
        source={"kind": "xlsx", "dataset": "ds", "resource": "work_stream"},
    )

    page.reload()
    assert read_values(page)[WHAT] == [{"@value": "escrito"}]
    assert page.evaluate("window.OntoBDCGlobalEventRuntime.errors") == []
    page.close()


@browsertest
def test_a_hostile_cell_written_by_ontobdc_stays_inert_in_the_browser(browser, tmp_path):
    """The writer escapes every `<`; this proves the escaped block really
    does survive Chromium's HTML parser with the value intact."""
    page_path = tmp_path / "index.html"
    page_path.write_text(
        writer_module.prepare_document_for_journal(generated_surface(snapshot())),
        encoding="utf-8",
    )
    writer = writer_module.GlobalEventJournalWriter(page_path, tmp_path / "state.json")
    hostile = '</script><img src=x onerror="window.__PWNED__=true">'
    writer.append(
        event=SET_EVENT,
        entity=ENTITY,
        operations=[writer_module.GlobalEventOperation("set", WHAT, {"@value": hostile})],
    )

    page = browser.new_page()
    page.goto(page_path.as_uri())
    assert page.evaluate("window.__PWNED__ === true") is False
    assert read_values(page)[WHAT] == [{"@value": hostile}]
    page.close()


@browsertest
def test_ordering_survives_the_round_trip(browser, tmp_path):
    """Sequences assigned by the writer are what the runtime orders by, so
    the last edit to a field is the one on screen."""
    page_path = tmp_path / "index.html"
    page_path.write_text(
        writer_module.prepare_document_for_journal(generated_surface(snapshot())),
        encoding="utf-8",
    )
    writer = writer_module.GlobalEventJournalWriter(page_path, tmp_path / "state.json")
    for value in ("primeiro", "segundo", "terceiro"):
        writer.append(
            event=SET_EVENT,
            entity=ENTITY,
            operations=[writer_module.GlobalEventOperation("set", WHAT, {"@value": value})],
        )

    page = browser.new_page()
    page.goto(page_path.as_uri())
    assert read_values(page)[WHAT] == [{"@value": "terceiro"}]
    assert page.evaluate("window.OntoBDCGlobalEventRuntime.lastSequence") == 2
    page.close()


@browsertest
def test_compaction_by_ontobdc_produces_the_same_screen(browser, tmp_path):
    """The acceptance criterion for compaction: after a regeneration folds
    the journal in, the page shows exactly what replay was showing, and the
    absorbed events are not applied again."""
    page_path = tmp_path / "index.html"
    page_path.write_text(
        writer_module.prepare_document_for_journal(generated_surface(snapshot())),
        encoding="utf-8",
    )
    writer = writer_module.GlobalEventJournalWriter(page_path, tmp_path / "state.json")
    writer.append(
        event=SET_EVENT,
        entity=ENTITY,
        operations=[writer_module.GlobalEventOperation("set", WHAT, {"@value": "editado"})],
    )

    page = browser.new_page()
    page.goto(page_path.as_uri())
    replayed = read_values(page)
    page.close()

    # What a regeneration produces: the sources re-read, so the snapshot
    # already carries the edit.
    materialized = generated_surface([replayed, snapshot()[1]])
    cutoff = writer.write_compacted(materialized)
    assert cutoff == 0

    page = browser.new_page()
    page.goto(page_path.as_uri())
    assert read_values(page) == replayed
    assert page.evaluate("window.OntoBDCGlobalEventRuntime.replayedEventIds") == []
    assert page.evaluate("window.OntoBDCGlobalEventRuntime.snapshotThrough") == 0
    page.close()


@browsertest
def test_an_interrupted_append_does_not_hide_the_events_before_it(browser, tmp_path):
    """A half-written block swallows everything after it in the HTML parser.
    The writer truncates it before the next append; this checks the browser
    agrees about what survived."""
    page_path = tmp_path / "index.html"
    page_path.write_text(
        writer_module.prepare_document_for_journal(generated_surface(snapshot())),
        encoding="utf-8",
    )
    writer = writer_module.GlobalEventJournalWriter(page_path, tmp_path / "state.json")
    writer.append(
        event=SET_EVENT,
        entity=ENTITY,
        operations=[writer_module.GlobalEventOperation("set", WHAT, {"@value": "primeiro"})],
    )
    with page_path.open("a", encoding="utf-8") as handle:
        handle.write(
            '\n<script type="application/ld+json" data-ontobdc-global-event="true"'
            ' data-event-id="urn:uuid:half" data-sequence="9">\n{"event": "trunc'
        )
    writer.append(
        event=SET_EVENT,
        entity=ENTITY,
        operations=[writer_module.GlobalEventOperation("set", TITLE, {"@value": "Segundo"})],
    )

    page = browser.new_page()
    page.goto(page_path.as_uri())
    values = read_values(page)
    assert values[WHAT] == [{"@value": "primeiro"}]
    assert values[TITLE] == [{"@value": "Segundo", "@language": "pt-BR"}]
    page.close()
