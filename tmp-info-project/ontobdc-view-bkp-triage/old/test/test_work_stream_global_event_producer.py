"""The WorkStream Page calls the Global Event listener directly.

The Page writes its data source, builds the event, and awaits Python. The
call resolves only once the listener has stored the event under the
dataset's `.__ontobdc__/event/` and appended its JSON-LD to the Surface
journal — so there is no state in which the Page believes the Surface knows
and it does not.

The last tests run that for real: the envelope is built by the shipped Page
JavaScript in Node, handed to the real Python listener, and the resulting
document opened in Chromium over `file://`.
"""

import json
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

import pytest

import ontobdc_view
import ontobdc_view.page.adapter.container
from ontobdc_view.page.adapter.work_stream import WorkStreamScriptAdapter

NODE = shutil.which("node")
CHROMIUM = "/opt/pw-browsers/chromium-1194/chrome-linux/chrome"

PAGE = Path(ontobdc_view.__file__).parent / "page/adapter/work_stream.py"
CONTAINER = Path(ontobdc_view.__file__).parent / "page/adapter/container.py"

WORK_STREAM_NS = "http://datacenter.app.br/ontology/productivity/entity/work_stream/type.ttl#"
TITLE = "http://purl.org/dc/terms/title"
ENTITY = "urn:ontobdc:container/dataset-a/work_stream/WS-1"


def page_source(name: str) -> str:
    return ontobdc_view.work_stream_script_source(name)


def all_page_source() -> str:
    return "\n".join(page_source(name) for name in WorkStreamScriptAdapter._BUILDERS)


def code_only(text: str) -> str:
    text = re.sub(r"/\*.*?\*/", "", text, flags=re.DOTALL)
    return "\n".join(re.sub(r"//.*$", "", line) for line in text.splitlines())


# --------------------------------------------------------------------------
# The event type comes from the ontology
# --------------------------------------------------------------------------


def test_the_event_iri_is_resolved_from_the_graph_not_written_by_hand():
    source = all_page_source()
    assert ontobdc_view.global_event_iri_for_operation("set") in source
    assert "__ONTOBDC_BUILD_" not in source


def test_the_page_template_carries_a_placeholder_rather_than_an_iri():
    """The IRI must not be a literal in the Python that generates the page
    either — the ontology is what says which event carries a `set`."""
    template = PAGE.read_text(encoding="utf-8")
    assert "__ONTOBDC_BUILD_ENTITY_PROPERTY_SET_EVENT__" in template
    assert "presentation_event.ttl#EntityPropertySet" not in template


def test_an_unresolved_placeholder_fails_the_build(monkeypatch):
    adapter = WorkStreamScriptAdapter()
    with pytest.raises(ValueError, match="unresolved build placeholder"):
        adapter._resolve_build_placeholders("var x = __ONTOBDC_BUILD_SOMETHING_ELSE__;")


def test_the_ontology_must_name_exactly_one_event_for_an_operation():
    from ontobdc_view.component.adapter import global_event as module

    monkey = {"a": ["set"], "b": ["set"]}
    original = module.global_event_operations
    try:
        module.global_event_operations = lambda: monkey
        with pytest.raises(ValueError, match="more than one"):
            module.global_event_iri_for_operation("set")
        module.global_event_operations = lambda: {}
        with pytest.raises(ValueError, match="no view:GlobalEvent"):
            module.global_event_iri_for_operation("set")
    finally:
        module.global_event_operations = original


# --------------------------------------------------------------------------
# The predicate is an IRI, never a column label
# --------------------------------------------------------------------------


def test_the_predicate_resolver_prefers_the_containers_own_linkset():
    code = code_only(all_page_source())
    resolver = code[code.index("function workStreamPredicateFor(column)") :]
    resolver = resolver[: resolver.index("\n  }\n")]
    assert "runtime.state.liveColumnMappings" in resolver
    assert "WORKBOOK_COLUMN_TO_PROPERTY[column]" in resolver
    # The linkset is consulted first; the convention is the fallback.
    assert resolver.index("liveColumnMappings") < resolver.index("WORKBOOK_COLUMN_TO_PROPERTY")


def test_an_unmapped_column_declines_to_emit_rather_than_guessing():
    code = code_only(all_page_source())
    emitter = code[code.index("async function emitWorkStreamFieldEvent") :]
    emitter = emitter[: emitter.index("\n  }\n")]
    assert "if (!predicate)" in emitter
    assert "globalEventNoPredicate" in emitter
    # It must not fall back to the column label.
    assert "predicate: column" not in emitter


def test_a_parse_without_mappings_does_not_erase_a_known_one():
    """Only the Pyodide parse can read the container's Turtle linkset; a
    SheetJS refresh returns no mappings and must not wipe them."""
    code = code_only(all_page_source())
    assert "if (result.mappings) runtime.state.liveColumnMappings = result.mappings;" in code


# --------------------------------------------------------------------------
# One save, one event, after the write
# --------------------------------------------------------------------------


def test_both_write_paths_emit_through_the_same_producer():
    """SheetJS and Pyodide+openpyxl are two ways to write the same cell; a
    second emission path would be a second contract."""
    code = code_only(all_page_source())
    save = code[code.index("async function saveWorkStreamField(column, value)") :]
    save = save[: save.index("\n  async function openContainerFromHandle")]
    assert save.count("emitWorkStreamFieldEvent(column, value,") == 2


def test_the_event_carries_one_operation_but_the_field_stays_plural():
    code = code_only(all_page_source())
    emitter = code[code.index("async function emitWorkStreamFieldEvent") :]
    emitter = emitter[: emitter.index("\n  }\n")]
    assert 'operations: [' in emitter
    assert '{ operation: "set", predicate: predicate, value: { "@value": next } },' in emitter


def test_an_unchanged_value_emits_nothing():
    code = code_only(all_page_source())
    emitter = code[code.index("async function emitWorkStreamFieldEvent") :]
    emitter = emitter[: emitter.index("\n  }\n")]
    assert "if (next === String(previousValue ?? \"\"))" in emitter
    assert "return null;" in emitter


def test_the_entity_is_the_surface_id_not_the_global_id():
    code = code_only(all_page_source())
    emitter = code[code.index("async function emitWorkStreamFieldEvent") :]
    emitter = emitter[: emitter.index("\n  }\n")]
    assert "WORKSTREAM_PAYLOAD?.workstreamUri" in emitter
    # elementId is the workbook's GlobalId — provenance, not identity.
    assert 'entityIdentifier: String(WORKSTREAM_PAYLOAD?.elementId' in emitter


# --------------------------------------------------------------------------
# The old full-regeneration-per-field path is gone
# --------------------------------------------------------------------------


def test_saving_a_field_no_longer_asks_for_a_full_surface_regeneration():
    code = code_only(all_page_source())
    assert "scheduleSurfaceRegeneration(\"workstream_field:" not in code


def test_the_structural_regeneration_signal_is_untouched():
    """It is a different thing and stays as it is: a single overwritable
    file, where only the latest request matters."""
    code = code_only(CONTAINER.read_text(encoding="utf-8"))
    assert "surface-regeneration.request.json" in code
    assert "function scheduleSurfaceRegeneration(reason)" in code


def test_the_listener_call_is_not_the_regeneration_signal():
    code = code_only(CONTAINER.read_text(encoding="utf-8"))
    submit = code[code.index("async function submitGlobalEvent(event)") :]
    submit = submit[: submit.index("\n  }\n")]
    assert "SURFACE_REGENERATION_REQUEST_FILE" not in submit
    assert "handle_global_event_json" in submit


def test_there_is_no_queue_left_in_the_page_runtime():
    """`pending/`, `processed/`, receipts and polling are gone: the call into
    Python is the processing, so there is nothing for a daemon to consume."""
    code = code_only(CONTAINER.read_text(encoding="utf-8"))
    for gone in (
        "awaitGlobalEventReceipt",
        "readGlobalEventReceipt",
        "globalEventFileStem",
        "GLOBAL_EVENT_PENDING",
        "GLOBAL_EVENT_PROCESSED",
        "GLOBAL_EVENT_RECEIPT_TIMEOUT_MS",
    ):
        assert gone not in code, gone


def test_submitting_awaits_the_listener_rather_than_polling():
    code = code_only(CONTAINER.read_text(encoding="utf-8"))
    submit = code[code.index("async function submitGlobalEvent(event)") :]
    submit = submit[: submit.index("\n  }\n")]
    assert "await runtime.ensurePyodide()" in submit
    assert "ensureGlobalEventListener(pyodide)" in submit
    assert "setTimeout" not in submit
    assert "deadline" not in submit


def test_only_a_completed_run_resolves_as_success():
    code = code_only(CONTAINER.read_text(encoding="utf-8"))
    submit = code[code.index("async function submitGlobalEvent(event)") :]
    submit = submit[: submit.index("\n  }\n")]
    assert 'answer.status !== "completed"' in submit
    assert "throw error;" in submit
    assert "globalEventState" in submit


def test_the_listener_writes_through_pyodide_and_the_result_is_synced():
    """Nothing is on the real disk until `syncfs` returns, so the sync has to
    happen before the call resolves."""
    code = code_only(CONTAINER.read_text(encoding="utf-8"))
    submit = code[code.index("async function submitGlobalEvent(event)") :]
    submit = submit[: submit.index("\n  }\n")]
    assert "await syncEventFilesystem(pyodide)" in submit
    assert submit.index("handle_global_event_json") < submit.index("syncEventFilesystem")


def mount_function() -> str:
    code = code_only(CONTAINER.read_text(encoding="utf-8"))
    assert "async function ensureEventContainerMount(pyodide)" in code
    mount = code[code.index("async function ensureEventContainerMount(pyodide)") :]
    return mount[: mount.index("\n  }\n")]


def test_the_container_is_mounted_for_python_even_on_a_sheetjs_connect():
    """A Page connected through SheetJS never mounted the container, and the
    listener cannot write into a filesystem Python cannot see."""
    assert "await pyodide.mountNativeFS(mountPath, datasetHandle)" in mount_function()


def test_the_listener_is_given_the_resolved_dataset_never_the_picked_folder():
    """`rawContainerHandle` is whatever folder the user pointed at, which for
    a container holding several datasets is the parent of this Page's own.
    Both files the listener touches live in the dataset."""
    mount = mount_function()
    assert "const datasetHandle = runtime.state.datasetHandle;" in mount
    assert "rawContainerHandle" not in mount


def test_a_mount_is_reused_only_when_it_is_a_mount_of_this_dataset():
    """`activeMountPath` is a shared slot — the workbook parse and the Gantt
    ingestion write it too — so the path alone does not say which directory
    Python is looking at."""
    mount = mount_function()
    assert "runtime.state.activeMountHandle === datasetHandle" in mount
    assert "runtime.state.activeMountHandle = datasetHandle;" in mount


def test_every_mount_site_records_which_handle_it_mounted():
    """The invariant the reuse check depends on: wherever a container is
    mounted, the handle behind the path is recorded with it."""
    for module in (CONTAINER, PAGE, Path(ontobdc_view.__file__).parent / "page/adapter/gantt_script.py"):
        code = code_only(module.read_text(encoding="utf-8"))
        mounts = code.count("await pyodide.mountNativeFS(")
        records = code.count("runtime.state.activeMountHandle = ")
        assert records >= mounts, f"{module.name}: {mounts} mounts, {records} recorded"


# --------------------------------------------------------------------------
# Failure is reported, never faked
# --------------------------------------------------------------------------


def test_the_producer_returns_what_python_answered(page_code=None):
    """No receipt to wait for and nothing to reconcile: the listener's own
    result is the producer's result."""
    code = code_only(all_page_source())
    emitter = code[code.index("async function emitWorkStreamFieldEvent") :]
    emitter = emitter[: emitter.index("\n  }\n")]
    assert "return await runtime.submitGlobalEvent({" in emitter
    assert "receipt" not in emitter
    assert "setTimeout" not in emitter


def test_the_return_url_carries_the_sequence_as_a_revision():
    code = code_only(CONTAINER.read_text(encoding="utf-8"))
    assert 'GLOBAL_EVENT_SEQUENCE_PARAM = "_ontobdc_global_event"' in code
    builder = code[code.index("function surfaceUrlForSequence(sequence)") :]
    builder = builder[: builder.index("\n  }\n")]
    assert 'new URL("index.html", location.href)' in builder
    assert "url.searchParams.set(GLOBAL_EVENT_SEQUENCE_PARAM" in builder


# --------------------------------------------------------------------------
# The file name the Page writes is the one the worker expects
# --------------------------------------------------------------------------

listener_module = pytest.importorskip(
    "ontobdc.view.adapter.surface.global_event_listener",
    reason="the OntoBDC Global Event listener is not installed",
)
journal_module = pytest.importorskip(
    "ontobdc.view.adapter.surface.global_event",
    reason="the OntoBDC journal writer is not installed",
)

nodeonly = pytest.mark.skipif(NODE is None, reason="node is not available")


def test_the_stored_record_is_named_for_the_event(tmp_path):
    """The listener names the dataset record after the event id; the Page
    never derives that name, so there is only one implementation of it."""
    assert (
        listener_module.event_file_stem("urn:uuid:ÁÇÃO-1") == "urn-uuid----O-1"
    )
    assert listener_module.event_file_stem("urn:uuid:abc-1") == "urn-uuid-abc-1"


# --------------------------------------------------------------------------
# The whole chain: Page JS -> queue -> worker -> journal -> browser
# --------------------------------------------------------------------------

browsertest = pytest.mark.skipif(
    not Path(CHROMIUM).exists(), reason="the packaged Chromium build is not present"
)

# Runs the shipped producer against a Pyodide stand-in whose Python calls are
# real Python. Only the interpreter *host* is emulated — `runPythonAsync`
# executes the listener installer the generated page carries, and
# `handle_global_event_json` is the listener itself, working on the real
# container directory. The envelope, the statechart and the journal are the
# shipped ones.
LISTENER_ONE_SHOT = r'''
import json, sys

# Only the tree the installer just materialized. A regular package of the
# same name anywhere else on the path would win over this namespace one, and
# the harness would end up exercising the development checkout instead of
# what a generated Page actually ships.
sys.path = [sys.argv[1]] + [entry for entry in sys.path if "ontobdc" not in entry]
from ontobdc_view.surface.adapter.global_event_listener import handle_global_event_json
import ontobdc_view.surface.adapter.global_event_listener as shipped

assert shipped.__file__.startswith(sys.argv[1]), shipped.__file__
sys.stdout.write(handle_global_event_json(sys.argv[2], sys.stdin.read()))
'''

PRODUCER_HARNESS = r"""
import { execFileSync } from "node:child_process";
import { writeFileSync, mkdirSync } from "node:fs";
import { join } from "node:path";

const PYTHON = process.env.ONTOBDC_PYTHON;
const CONTAINER = process.env.CONTAINER;
const INSTALL_ROOT = process.env.INSTALL_ROOT;
const DEFAULT_INSTALL_ROOT = process.env.DEFAULT_INSTALL_ROOT;
const ONE_SHOT = process.env.ONE_SHOT;

globalThis.window = globalThis;
globalThis.location = { href: "file://" + CONTAINER + "/dataset/page.html" };

const runtime = { state: {} };
// What a connect leaves behind: the folder the user picked, and the dataset
// the descent resolved. They are the same object here — this container holds
// exactly one dataset and is itself the dataset — so this file stays about
// the producer. The nested case, where they differ, is
// test_global_event_nested_dataset.py.
const containerHandle = { name: "container" };
runtime.state.rawContainerHandle = containerHandle;
runtime.state.datasetHandle = containerHandle;
// The container is already visible to Python here: the real directory is
// what stands in for the browser's mount.
runtime.state.activeMountPath = CONTAINER;
runtime.state.activeMountHandle = containerHandle;

runtime.ensurePyodide = async () => ({
  FS: {
    mkdirTree() {},
    syncfs(_populate, callback) { callback(null); },
  },
  async mountNativeFS() {},
  async runPythonAsync(source) {
    // The listener installer the page carries — really executed, into a
    // root the one-shot below then imports from.
    mkdirSync(INSTALL_ROOT, { recursive: true });
    const installer = join(INSTALL_ROOT, "_installer.py");
    // Redirect the install root at the one literal the generator emits.
    // Asserted, not hoped for: a substitution that misses installs the
    // bundle at its real path and leaves the import to be satisfied by
    // whatever else is on the machine — which would make this harness prove
    // nothing about the shipped tree.
    const redirected = source.replace(DEFAULT_INSTALL_ROOT, JSON.stringify(INSTALL_ROOT));
    if (redirected === source) {
      throw new Error("the install root literal " + DEFAULT_INSTALL_ROOT + " was not found");
    }
    writeFileSync(installer, redirected, "utf-8");
    execFileSync(PYTHON, [installer], { encoding: "utf-8" });
  },
  globals: {
    get(name) {
      if (name !== "ontobdc_global_event_listener") return undefined;
      return {
        // Synchronous, string in / string out — the shape a Pyodide PyProxy
        // of this function has.
        handle_global_event_json: (mountPath, envelopeJson) =>
          execFileSync(PYTHON, [ONE_SHOT, INSTALL_ROOT, mountPath], {
            input: envelopeJson,
            encoding: "utf-8",
          }),
      };
    },
  },
});

const t = (key, vars) => key;
const WORKSTREAM_PAYLOAD = JSON.parse(process.env.PAYLOAD);
const WORKBOOK_COLUMN_TO_PROPERTY = JSON.parse(process.env.COLUMNS);
runtime.ENTITY_PROPERTY_SET_EVENT = process.env.EVENT_IRI;

__CONTAINER_CLIENT__

runtime.submitGlobalEvent = submitGlobalEvent;

__PRODUCER__

const result = await emitWorkStreamFieldEvent(
  process.env.COLUMN,
  process.env.VALUE,
  process.env.PREVIOUS || "",
).catch((error) => ({
  error: String(error.message || error),
  state: error.globalEventState || null,
  trace: error.globalEventTrace || [],
}));

process.stdout.write(JSON.stringify(result === null ? { skipped: true } : result));
"""


def default_install_root() -> str:
    """The install-root literal exactly as the generated installer spells it.

    Taken from the generator rather than written out here, so a harness can
    never quietly miss it and end up testing whatever else is installed.
    """
    from ontobdc_view.component.adapter import global_event_listener as shipper

    return repr(shipper._PYODIDE_ROOT)


def extract_block(source: str, start_marker: str, end_marker: str) -> str:
    begin = source.index(start_marker)
    end = source.index(end_marker, begin)
    return source[begin:end]


def build_harness(tmp: Path) -> Path:
    container_js = ontobdc_view.page.adapter.container.connection_state_source(
        ontobdc_view.page.adapter.container.WORK_STREAM_RUNTIME
    )
    client = extract_block(
        container_js,
        "  const GLOBAL_EVENT_SEQUENCE_PARAM = ",
        "  function scheduleSurfaceRegeneration(reason) {",
    )
    producer = extract_block(
        all_page_source(),
        "  function workStreamPredicateFor(column) {",
        "  async function saveWorkStreamField(column, value) {",
    )
    script = PRODUCER_HARNESS.replace("__CONTAINER_CLIENT__", client).replace(
        "__PRODUCER__", producer
    )
    path = tmp / "producer.mjs"
    path.write_text(script, encoding="utf-8")
    (tmp / "one_shot.py").write_text(LISTENER_ONE_SHOT, encoding="utf-8")
    return path


def run_producer(tmp: Path, container: Path, column="What", value="novo", previous=""):
    harness = build_harness(tmp)
    completed = subprocess.run(
        [NODE, str(harness)],
        capture_output=True,
        text=True,
        timeout=300,
        env={
            "PATH": "/usr/bin:/bin:/usr/local/bin",
            "ONTOBDC_PYTHON": sys.executable,
            "CONTAINER": str(container),
            "INSTALL_ROOT": str(tmp / "pylib"),
            "DEFAULT_INSTALL_ROOT": default_install_root(),
            "ONE_SHOT": str(tmp / "one_shot.py"),
            "COLUMN": column,
            "VALUE": value,
            "PREVIOUS": previous,
            "EVENT_IRI": ontobdc_view.global_event_iri_for_operation("set"),
            "PAYLOAD": json.dumps(
                {
                    "workstreamUri": ENTITY,
                    "elementId": "WS-1",
                    "datasetFolder": "dataset",
                }
            ),
            "COLUMNS": json.dumps({"What": f"{WORK_STREAM_NS}what", "Name": TITLE}),
        },
    )
    if completed.returncode != 0:
        pytest.fail(f"producer harness failed:\n{completed.stderr}")
    return json.loads(completed.stdout)


def surface_with(nodes) -> str:
    from test_global_event_replay import build_document  # noqa: E402

    return journal_module.prepare_document_for_journal(build_document(nodes, []))


@nodeonly
def test_the_producer_call_reaches_the_listener_and_returns_a_sequence(tmp_path):
    """The whole point of the change: one awaited call, and by the time it
    resolves the event is in the dataset and in the journal."""
    container = tmp_path / "container"
    container.mkdir()
    (container / "index.html").write_text(
        surface_with([{"@id": ENTITY, f"{WORK_STREAM_NS}what": [{"@value": "antigo"}]}]),
        encoding="utf-8",
    )

    result = run_producer(tmp_path, container)

    assert result["status"] == "completed"
    assert result["sequence"] == 0
    assert result["trace"] == [
        "EVENT_RECEIVED",
        "EVENT_STORED",
        "SURFACE_JOURNAL_UPDATED",
        "COMPLETED",
    ]

    records = sorted((container / ".__ontobdc__" / "event").glob("*.json"))
    assert len(records) == 1
    stored = json.loads(records[0].read_text(encoding="utf-8"))
    assert stored["entity"] == ENTITY
    assert stored["operations"][0]["predicate"] == f"{WORK_STREAM_NS}what"

    entries = journal_module.journal_entries(
        (container / "index.html").read_text(encoding="utf-8")
    )
    assert [entry["operations"][0]["value"]["@value"] for entry in entries] == ["novo"]


@nodeonly
def test_an_unchanged_value_never_reaches_python(tmp_path):
    container = tmp_path / "container"
    container.mkdir()
    result = run_producer(tmp_path, container, value="igual", previous="igual")
    assert result == {"skipped": True}
    assert not (container / ".__ontobdc__" / "event").exists()


@nodeonly
def test_an_unmapped_column_never_reaches_python(tmp_path):
    container = tmp_path / "container"
    container.mkdir()
    result = run_producer(tmp_path, container, column="Unmapped")
    assert "globalEventNoPredicate" in result["error"]
    assert not (container / ".__ontobdc__" / "event").exists()


@nodeonly
def test_a_listener_failure_reaches_the_page_with_the_state_it_stopped_in(tmp_path):
    """No Surface document: the event is stored (the workbook really did
    change) but the journal step cannot run, and the Page is told so rather
    than being handed a success."""
    container = tmp_path / "container"
    container.mkdir()

    result = run_producer(tmp_path, container)

    assert "no Surface document" in result["error"]
    assert result["state"] == "__event_stored__"
    assert result["trace"] == ["EVENT_RECEIVED", "EVENT_STORED"]
    # The evidence of the change survives for a later re-run.
    assert len(list((container / ".__ontobdc__" / "event").glob("*.json"))) == 1


@nodeonly
@browsertest
def test_the_whole_chain_updates_what_the_surface_shows(tmp_path):
    """Page JavaScript -> Python listener -> dataset record + journal ->
    Chromium on `file://`. Nothing between the edit and the screen is
    stubbed but the interpreter host."""
    playwright = pytest.importorskip("playwright.sync_api")

    container = tmp_path / "container"
    container.mkdir()
    surface = container / "index.html"
    surface.write_text(
        surface_with([{"@id": ENTITY, f"{WORK_STREAM_NS}what": [{"@value": "antigo"}]}]),
        encoding="utf-8",
    )

    with playwright.sync_playwright() as p:
        browser = p.chromium.launch(executable_path=CHROMIUM)
        page = browser.new_page()
        page.goto(surface.as_uri())
        before = page.evaluate("window.__READ_BY_COMPONENT__")
        assert before[0][f"{WORK_STREAM_NS}what"] == [{"@value": "antigo"}]

        result = run_producer(tmp_path, container, column="What", value="editado")
        assert result["status"] == "completed"

        page.goto(surface.as_uri() + f"?_ontobdc_global_event={result['sequence']}")
        after = page.evaluate("window.__READ_BY_COMPONENT__")
        assert after[0][f"{WORK_STREAM_NS}what"] == [{"@value": "editado"}]
        assert page.evaluate("window.OntoBDCGlobalEventRuntime.errors") == []
        browser.close()
