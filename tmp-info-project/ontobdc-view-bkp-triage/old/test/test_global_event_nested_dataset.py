"""A Global Event lands in the resolved dataset, never in the folder picked.

The user connects a parent folder; the runtime descends into the dataset the
Surface was generated for. Everything the listener touches — the event
record and the Surface journal — belongs to *that* folder. Writing into the
picked parent instead puts the event where no Surface replays it, and hands
Python write access to every sibling dataset under the selection.

The chain here is the real one, end to end:

    the shipped `resolveContainerHandle()`   descends parent/ -> dataset-a/
    the shipped `saveWorkStreamField()`      writes the .xlsx with openpyxl
    the shipped `submitGlobalEvent()`        mounts and calls Python
    the shipped `GlobalEventListener`        stores, journals, answers
    the shipped `global_event_replay.js`     replays it in Chromium

What the harness stands in for is the browser itself: a directory handle
over a real directory, and a Pyodide whose `runPythonAsync` really runs
Python. The JavaScript is the generated Page's own source, the Python is the
installed listener, and the files are on a real disk.
"""

import json
import re
import shutil
import subprocess
import sys
from pathlib import Path

import pytest
from openpyxl import Workbook, load_workbook

import ontobdc_view
import ontobdc_view.page.adapter.container as container_module
from ontobdc_view.page.adapter.work_stream import WorkStreamScriptAdapter
from ontobdc_view.surface.adapter.global_event import (
    journal_entries,
    prepare_document_for_journal,
)

NODE = shutil.which("node")
CHROMIUM = "/opt/pw-browsers/chromium-1194/chrome-linux/chrome"

nodeonly = pytest.mark.skipif(NODE is None, reason="node is not available")
browsertest = pytest.mark.skipif(
    not Path(CHROMIUM).exists(), reason="the packaged Chromium build is not present"
)

WORK_STREAM_NS = "http://datacenter.app.br/ontology/productivity/entity/work_stream/type.ttl#"
WHAT = f"{WORK_STREAM_NS}what"
ENTITY = "urn:ontobdc:parent/dataset-a/work_stream/WS-1"
GLOBAL_ID = "WS-1"
DATASET_FOLDER = "dataset-a"
RESOURCE_NAME = "work_stream"


# --------------------------------------------------------------------------
# The container the test connects to
# --------------------------------------------------------------------------


def build_container(root: Path) -> Path:
    """`parent/` holds one dataset, `dataset-a/`, and is not one itself."""
    parent = root / "parent"
    dataset = parent / DATASET_FOLDER
    (dataset / ".__ontobdc__").mkdir(parents=True)
    # `parent/` deliberately carries no datapackage: it is a plain folder the
    # user happens to have picked, exactly the case the bug produced.
    (dataset / ".__ontobdc__" / "datapackage.json").write_text(
        json.dumps({"resources": [{"name": RESOURCE_NAME, "path": "work_stream.xlsx"}]}),
        encoding="utf-8",
    )

    workbook = Workbook()
    sheet = workbook.active
    sheet.title = "WorkStream"
    sheet.append(["GlobalId", "Name", "What"])
    sheet.append([GLOBAL_ID, "Fundação", "antigo"])
    workbook.save(dataset / "work_stream.xlsx")

    (dataset / "index.html").write_text(surface_document(), encoding="utf-8")
    return parent


def surface_document() -> str:
    from test_global_event_replay import build_document

    return prepare_document_for_journal(
        build_document(
            [{"@id": ENTITY, "@type": ["urn:WorkStream"], WHAT: [{"@value": "antigo"}]}],
            [],
        )
    )


# --------------------------------------------------------------------------
# The harness
# --------------------------------------------------------------------------

# Runs the listener the Page installed, and — before it does — records what
# the .xlsx says at that instant. That recording is the ordering proof: if
# the datasource already carries the new value when the listener is entered,
# the write cannot have happened after the event.
LISTENER_ONE_SHOT = r'''
import json, sys

# Only the tree the installer just materialized — see the note in
# test_work_stream_global_event_producer.py.
_SHIPPED_ROOT = sys.argv[1]
from openpyxl import load_workbook

workbook = load_workbook(sys.argv[3])
sheet = workbook["WorkStream"]
witness = [
    sheet.cell(row=row, column=3).value
    for row in range(2, sheet.max_row + 1)
    if str(sheet.cell(row=row, column=1).value or "") == sys.argv[4]
]
workbook.close()
with open(sys.argv[5], "w", encoding="utf-8") as handle:
    json.dump({"datasourceAtListenerEntry": witness}, handle)

sys.path = [_SHIPPED_ROOT] + [entry for entry in sys.path if "ontobdc" not in entry]
import ontobdc_view.surface.adapter.global_event_listener as shipped

assert shipped.__file__.startswith(_SHIPPED_ROOT), shipped.__file__
sys.stdout.write(shipped.handle_global_event_json(sys.argv[2], sys.stdin.read()))
'''

# The workbook write the Page's Pyodide path performs, run with the real
# openpyxl against the real file.
WORKBOOK_ONE_SHOT = r'''
import json, sys
globals().update(json.load(open(sys.argv[1], encoding="utf-8")))
exec(compile(open(sys.argv[2], encoding="utf-8").read(), "workbook_write", "exec"))
'''

HARNESS = r"""
import { execFileSync } from "node:child_process";
import { writeFileSync, mkdirSync, readdirSync, readFileSync, statSync } from "node:fs";
import { join, basename } from "node:path";

const PYTHON = process.env.ONTOBDC_PYTHON;
const PARENT = process.env.PARENT;
const INSTALL_ROOT = process.env.INSTALL_ROOT;
const DEFAULT_INSTALL_ROOT = process.env.DEFAULT_INSTALL_ROOT;
const LISTENER_ONE_SHOT = process.env.LISTENER_ONE_SHOT;
const WORKBOOK_ONE_SHOT = process.env.WORKBOOK_ONE_SHOT;
const WITNESS = process.env.WITNESS;
const SCRATCH = process.env.SCRATCH;

globalThis.window = globalThis;
globalThis.location = { href: "file://" + PARENT + "/dataset-a/index.html" };

// -- a FileSystemDirectoryHandle over a real directory ---------------------
//
// Only what the shipped resolution and mount actually call. `realPath` is
// not part of the browser API; the harness reads it to know which directory
// a mount was made of, which is the whole question under test.
function directoryHandle(realPath) {
  const handle = {
    kind: "directory",
    name: basename(realPath),
    realPath,
    async getDirectoryHandle(name) {
      const target = join(realPath, name);
      if (!statSync(target, { throwIfNoEntry: false })?.isDirectory()) {
        const error = new Error(name + " not found");
        error.name = "NotFoundError";
        throw error;
      }
      return directoryHandle(target);
    },
    async getFileHandle(name) {
      const target = join(realPath, name);
      if (!statSync(target, { throwIfNoEntry: false })?.isFile()) {
        const error = new Error(name + " not found");
        error.name = "NotFoundError";
        throw error;
      }
      return {
        kind: "file",
        name,
        async getFile() {
          const text = readFileSync(target, "utf-8");
          return { text: async () => text };
        },
      };
    },
    async *values() {
      for (const entry of readdirSync(realPath, { withFileTypes: true })) {
        yield entry.isDirectory()
          ? await handle.getDirectoryHandle(entry.name)
          : await handle.getFileHandle(entry.name);
      }
    },
  };
  return handle;
}

const mounts = [];
const runtime = { state: {} };
runtime.WORK_STREAM_RESOURCE_NAME = process.env.RESOURCE_NAME;

let pythonGlobals = {};
runtime.ensurePyodide = async () => ({
  FS: {
    mkdirTree() {},
    unmount() {},
    syncfs(_populate, callback) { callback(null); },
  },
  async mountNativeFS(mountPath, handle) {
    // A Pyodide mount makes the handle's directory readable at mountPath.
    // Here the directory already has a path, so the harness records the
    // pairing and translates when Python is called.
    mounts.push({ mountPath, realPath: handle.realPath });
  },
  async runPythonAsync(source) {
    if (source.includes("_ONTOBDC_EVENT_SOURCES")) {
      // The listener installer the generated page carries — really run,
      // into a root the one-shot below imports from.
      mkdirSync(INSTALL_ROOT, { recursive: true });
      const installer = join(INSTALL_ROOT, "_installer.py");
      // Redirect the install root at the one literal the generator emits.
      // Asserted, not hoped for: a substitution that misses installs the
      // bundle at its real path and leaves the import to be satisfied by
      // whatever else is on the machine.
      const redirected = source.replace(DEFAULT_INSTALL_ROOT, JSON.stringify(INSTALL_ROOT));
      if (redirected === source) {
        throw new Error("the install root literal " + DEFAULT_INSTALL_ROOT + " was not found");
      }
      writeFileSync(installer, redirected, "utf-8");
      execFileSync(PYTHON, [installer], { encoding: "utf-8" });
      return null;
    }
    // The workbook write: the shipped Python, the real openpyxl, the real
    // .xlsx. `workbook_path` arrives as a path under the mount, so it is
    // translated back the same way the listener's container path is.
    const globalsPath = join(SCRATCH, "globals.json");
    const scriptPath = join(SCRATCH, "workbook_write.py");
    writeFileSync(globalsPath, JSON.stringify({
      ...pythonGlobals,
      workbook_path: realPathFor(pythonGlobals.workbook_path),
    }), "utf-8");
    writeFileSync(scriptPath, source, "utf-8");
    return execFileSync(PYTHON, [WORKBOOK_ONE_SHOT, globalsPath, scriptPath], {
      encoding: "utf-8",
    });
  },
  globals: {
    set(name, value) { pythonGlobals[name] = value; },
    get(name) {
      if (name !== "ontobdc_global_event_listener") return undefined;
      return {
        handle_global_event_json: (mountPath, envelopeJson) =>
          execFileSync(
            PYTHON,
            [
              LISTENER_ONE_SHOT,
              INSTALL_ROOT,
              realPathFor(mountPath),
              join(realPathFor(mountPath), "work_stream.xlsx"),
              process.env.GLOBAL_ID,
              WITNESS,
            ],
            { input: envelopeJson, encoding: "utf-8" },
          ),
      };
    },
  },
});

function realPathFor(mountedPath) {
  for (const mount of mounts) {
    if (mountedPath === mount.mountPath) return mount.realPath;
    if (String(mountedPath).startsWith(mount.mountPath + "/")) {
      return join(mount.realPath, String(mountedPath).slice(mount.mountPath.length + 1));
    }
  }
  throw new Error("nothing is mounted at " + mountedPath);
}

// The Page-level names the extracted blocks close over.
const ensurePyodide = runtime.ensurePyodide;
const withPyodideLock = async (task) => task();
runtime.withPyodideLock = withPyodideLock;

const t = (key, vars) => key;
const WORKSTREAM_PAYLOAD = JSON.parse(process.env.PAYLOAD);
runtime.WORKSTREAM_PAYLOAD = WORKSTREAM_PAYLOAD;
const WORKBOOK_COLUMN_TO_PROPERTY = JSON.parse(process.env.COLUMNS);
runtime.ENTITY_PROPERTY_SET_EVENT = process.env.EVENT_IRI;
const WORK_STREAM_RESOURCE_NAME = process.env.RESOURCE_NAME;

__RESOLUTION__

__CONTAINER_CLIENT__

runtime.submitGlobalEvent = submitGlobalEvent;

__PRODUCER__

// -- the run --------------------------------------------------------------
//
// Exactly the sequence a connect-then-save performs: descend to the dataset,
// then save one field.
const rootHandle = directoryHandle(PARENT);
const resolved = await resolveContainerHandle(rootHandle);
runtime.state.rawContainerHandle = rootHandle;
runtime.state.datasetHandle = resolved;

// The Pyodide write path, which is the one whose Python really runs here.
const pyodide = await runtime.ensurePyodide();
const workbookMount = "/container_for_workbook";
await pyodide.mountNativeFS(workbookMount, resolved);
runtime.state.activeMountPath = workbookMount;
runtime.state.activeMountHandle = resolved;
runtime.state.liveWorkbookPath = workbookMount + "/work_stream.xlsx";
runtime.state.liveWorksheetName = "WorkStream";
runtime.state.liveWorkbookRecord = { What: "antigo" };

const result = await saveWorkStreamField("What", process.env.VALUE).catch((error) => ({
  error: String(error.message || error),
  state: error.globalEventState || null,
  trace: error.globalEventTrace || [],
}));

process.stdout.write(JSON.stringify({
  result,
  resolvedDataset: resolved.name,
  resolvedRealPath: resolved.realPath,
  datasetRelPath: runtime.state.datasetRelPath,
  mounts,
}));
"""


def default_install_root() -> str:
    """The install-root literal exactly as the generated installer spells it.

    Taken from the generator rather than written out here, so a harness can
    never quietly miss it and end up testing whatever else is installed.
    """
    from ontobdc_view.component.adapter import global_event_listener as shipper

    return repr(shipper._PYODIDE_ROOT)


def extract_block(source: str, start: str, end: str) -> str:
    begin = source.index(start)
    return source[begin : source.index(end, begin)]


def page_source() -> str:
    return "\n".join(
        ontobdc_view.work_stream_script_source(name)
        for name in WorkStreamScriptAdapter._BUILDERS
    )


def build_harness(scratch: Path) -> Path:
    # The descent and the Global Event bridge are generated into two
    # different Page scripts; both are taken as they ship.
    resolution = extract_block(
        container_module.container_connection_source(container_module.WORK_STREAM_RUNTIME),
        "  async function readDatapackageOrNull(handle, metadataDirName) {",
        "  function openHandleDb() {",
    )
    container_js = container_module.connection_state_source(
        container_module.WORK_STREAM_RUNTIME
    )
    client = extract_block(
        container_js,
        "  const GLOBAL_EVENT_SEQUENCE_PARAM = ",
        "  function scheduleSurfaceRegeneration(reason) {",
    )
    producer = extract_block(
        page_source(),
        "  const WORKBOOK_WRITE_SCRIPT = `",
        "  async function openContainerFromHandle(handle) {",
    )
    script = (
        HARNESS.replace("__RESOLUTION__", resolution)
        .replace("__CONTAINER_CLIENT__", client)
        .replace("__PRODUCER__", producer)
    )
    path = scratch / "nested.mjs"
    path.write_text(script, encoding="utf-8")
    (scratch / "listener_one_shot.py").write_text(LISTENER_ONE_SHOT, encoding="utf-8")
    (scratch / "workbook_one_shot.py").write_text(WORKBOOK_ONE_SHOT, encoding="utf-8")
    return path


def run_save(tmp_path: Path, value: str = "novo") -> dict:
    parent = build_container(tmp_path)
    scratch = tmp_path / "scratch"
    scratch.mkdir()
    harness = build_harness(scratch)
    completed = subprocess.run(
        [NODE, str(harness)],
        capture_output=True,
        text=True,
        timeout=300,
        env={
            "PATH": "/usr/bin:/bin:/usr/local/bin",
            "ONTOBDC_PYTHON": sys.executable,
            "PARENT": str(parent),
            "INSTALL_ROOT": str(scratch / "pylib"),
            "DEFAULT_INSTALL_ROOT": default_install_root(),
            "SCRATCH": str(scratch),
            "LISTENER_ONE_SHOT": str(scratch / "listener_one_shot.py"),
            "WORKBOOK_ONE_SHOT": str(scratch / "workbook_one_shot.py"),
            "WITNESS": str(scratch / "witness.json"),
            "GLOBAL_ID": GLOBAL_ID,
            "VALUE": value,
            "RESOURCE_NAME": RESOURCE_NAME,
            "EVENT_IRI": ontobdc_view.global_event_iri_for_operation("set"),
            "PAYLOAD": json.dumps(
                {
                    "workstreamUri": ENTITY,
                    "elementId": GLOBAL_ID,
                    "datasetFolder": DATASET_FOLDER,
                }
            ),
            "COLUMNS": json.dumps({"What": WHAT, "Name": "http://purl.org/dc/terms/title"}),
        },
    )
    if completed.returncode != 0:
        pytest.fail(f"nested-dataset harness failed:\n{completed.stderr}")
    answer = json.loads(completed.stdout)
    answer["parent"] = parent
    answer["scratch"] = scratch
    return answer


@pytest.fixture(scope="module")
def run(tmp_path_factory):
    if NODE is None:
        pytest.skip("node is not available")
    return run_save(tmp_path_factory.mktemp("nested"))


# --------------------------------------------------------------------------
# 1. the datasource was changed
# --------------------------------------------------------------------------


@nodeonly
def test_the_workbook_in_the_resolved_dataset_carries_the_new_value(run):
    workbook = load_workbook(run["parent"] / DATASET_FOLDER / "work_stream.xlsx")
    sheet = workbook["WorkStream"]
    assert [sheet.cell(row=2, column=index).value for index in (1, 3)] == [
        GLOBAL_ID,
        "novo",
    ]
    workbook.close()


# --------------------------------------------------------------------------
# 2. the event was emitted only after that change
# --------------------------------------------------------------------------


@nodeonly
def test_the_listener_already_saw_the_new_value_in_the_datasource(run):
    """Read straight out of the .xlsx at the instant the listener was
    entered. The write cannot have come after the event it already sees."""
    witness = json.loads((run["scratch"] / "witness.json").read_text(encoding="utf-8"))
    assert witness["datasourceAtListenerEntry"] == ["novo"]


# --------------------------------------------------------------------------
# 3. the listener received the resolved dataset
# --------------------------------------------------------------------------


@nodeonly
def test_the_runtime_descended_into_the_dataset(run):
    assert run["resolvedDataset"] == DATASET_FOLDER
    assert run["datasetRelPath"] == DATASET_FOLDER
    assert run["resolvedRealPath"] == str(run["parent"] / DATASET_FOLDER)


@nodeonly
def test_every_mount_the_page_made_is_of_the_dataset_not_the_picked_folder(run):
    """The mount is what Python can reach. A mount of `parent/` would give
    the listener the run of every dataset under the selection."""
    assert run["mounts"], "nothing was mounted"
    for mount in run["mounts"]:
        assert mount["realPath"] == str(run["parent"] / DATASET_FOLDER), mount
        assert mount["realPath"] != str(run["parent"])


# --------------------------------------------------------------------------
# 4./5. the event and the journal are inside the dataset
# --------------------------------------------------------------------------


@nodeonly
def test_the_event_is_stored_under_the_datasets_marker_directory(run):
    records = sorted((run["parent"] / DATASET_FOLDER / ".__ontobdc__" / "event").glob("*.json"))
    assert len(records) == 1
    stored = json.loads(records[0].read_text(encoding="utf-8"))
    assert stored["eventId"] == run["result"]["eventId"]
    assert stored["entity"] == ENTITY
    assert stored["operations"][0]["value"] == {"@value": "novo"}


@nodeonly
def test_the_journal_of_the_datasets_own_surface_was_updated(run):
    entries = journal_entries(
        (run["parent"] / DATASET_FOLDER / "index.html").read_text(encoding="utf-8")
    )
    assert [entry["eventId"] for entry in entries] == [run["result"]["eventId"]]
    assert entries[0]["sequence"] == run["result"]["sequence"]


# --------------------------------------------------------------------------
# 6. nothing was written into the folder the user picked
# --------------------------------------------------------------------------


@nodeonly
def test_the_picked_parent_folder_was_not_touched(run):
    parent = run["parent"]
    assert not (parent / ".__ontobdc__").exists(), "the listener wrote into parent/"
    assert not (parent / "index.html").exists()
    assert sorted(item.name for item in parent.iterdir()) == [DATASET_FOLDER]


# --------------------------------------------------------------------------
# 7./8. what the JavaScript got back
# --------------------------------------------------------------------------


@nodeonly
def test_the_page_was_told_the_run_completed(run):
    assert run["result"].get("error") is None, run["result"]
    assert run["result"]["status"] == "completed"
    assert run["result"]["trace"] == [
        "EVENT_RECEIVED",
        "EVENT_STORED",
        "SURFACE_JOURNAL_UPDATED",
        "COMPLETED",
    ]


@nodeonly
def test_the_page_was_given_a_usable_sequence(run):
    sequence = run["result"]["sequence"]
    assert isinstance(sequence, int)
    assert sequence >= 0
    state = json.loads(
        (run["parent"] / DATASET_FOLDER / ".__ontobdc__" / "global_event_sequence.json")
        .read_text(encoding="utf-8")
    )
    assert state["lastSequence"] == sequence


# --------------------------------------------------------------------------
# The four generic pieces stay generic
# --------------------------------------------------------------------------


def listener_tree_source() -> str:
    from ontobdc_view.component.adapter.global_event_listener import listener_module_sources

    return "\n".join(listener_module_sources().values())


def bridge_source() -> str:
    container_js = container_module.connection_state_source(
        container_module.WORK_STREAM_RUNTIME
    )
    return extract_block(
        container_js,
        "  const GLOBAL_EVENT_SEQUENCE_PARAM = ",
        "  function scheduleSurfaceRegeneration(reason) {",
    )


def strip_prose(text: str) -> str:
    """Comments and docstrings out; what executes stays.

    Prose is allowed to say "WorkStream" — a module explaining that its
    statechart follows the same convention as
    `WorkStreamScriptGenerationProcessState` is naming a neighbour, not
    handling a workbook. Code that says it is a different matter.
    """
    text = re.sub(r'"""(?:.|\n)*?"""', "", text)
    text = re.sub(r"/\*(?:.|\n)*?\*/", "", text)
    lines = []
    for line in text.splitlines():
        line = re.sub(r"//.*$", "", line)
        line = re.sub(r"(?<!:)#.*$", "", line)
        lines.append(line)
    return "\n".join(lines).lower()


@pytest.mark.parametrize(
    "name,source",
    [
        ("submitGlobalEvent", bridge_source),
        ("the listener, the statechart and the journal", listener_tree_source),
    ],
)
def test_nothing_workstream_specific_leaks_into_the_generic_machinery(name, source):
    """A Global Event is a Global Event. What makes one a WorkStream field
    save belongs to the producer that builds it — these four carry an
    envelope they do not interpret, and teaching any of them about a column,
    a worksheet or an .xlsx would make the next producer a special case too.
    """
    code = strip_prose(source())
    for specific in (
        "workstream",
        "work_stream",
        "worksheet",
        "openpyxl",
        "sheetjs",
        "xlsx",
        "5w2h",
        "workbook",
        "globalid",
    ):
        assert specific not in code, f"{name} handles {specific!r}"


def test_the_envelope_the_listener_reads_names_no_producer_of_its_own():
    """The fields are the event contract. A `column` or a `datasetFolder`
    among them would be one producer's vocabulary promoted to everyone's."""
    from ontobdc_view.surface.adapter.global_event_listener import ENVELOPE_FIELDS

    assert set(ENVELOPE_FIELDS) == {
        "eventId",
        "event",
        "entity",
        "occurredAt",
        "source",
        "operations",
    }
