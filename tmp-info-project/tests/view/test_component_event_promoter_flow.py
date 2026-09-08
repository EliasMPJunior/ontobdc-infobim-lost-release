"""End-to-end: a Component Event goes in, the Python Listener decides, the
promoted Shared Events come out.

The bridge's JavaScript is executed for real (Node, ES modules) and the
answers it dispatches are computed for real by the shipped dock runtime
reading `view:promotesTo` out of the shipped `presentation_event.ttl`.
Nothing in the chain returns a predetermined answer.

What the harness substitutes is only the *interpreter host*: in a browser
the bridge talks to Pyodide in-process, and here a Python child process
stands in for it, answering the same two calls the bridge makes
(`bootstrap`, `promote`) with the same JSON contract. The JavaScript under
test is the shipped file, unmodified; the policy is the shipped Turtle; the
Listener is the shipped plugin, installed from the very bundle
`listener_runtime_source()` hands to Pyodide.

Skipped when Node is unavailable — the rest of the suite pins the same
invariants statically.
"""

import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

import pytest

import ontobdc_view
from ontobdc_view.component.adapter.dock import listener_runtime_source

NODE = shutil.which("node")

pytestmark = pytest.mark.skipif(NODE is None, reason="node is not available")


# The one-shot the harness runs per `promote()` call. It imports the dock
# package the bridge's own installer materialized, bootstraps it from the
# policy document the bridge embedded, and answers.
PROMOTE_SCRIPT = r'''
import json, sys
sys.path.insert(0, sys.argv[1])
import ontobdc_web_dock as runtime
with open(sys.argv[2], encoding="utf-8") as handle:
    runtime.bootstrap(handle.read())
sys.stdout.write(runtime.promote(sys.stdin.read()))
'''

# Node host for the shipped bridge: enough DOM to run it, plus a
# `loadPyodide` whose Python calls really execute Python.
HARNESS = r'''
import { execFileSync } from "node:child_process";
import { writeFileSync, mkdirSync } from "node:fs";
import { join } from "node:path";

const PYTHON = process.env.ONTOBDC_PYTHON;
const DOCK_ROOT = process.env.ONTOBDC_DOCK_ROOT;
const POLICY_PATH = process.env.ONTOBDC_POLICY_PATH;
const PROMOTE_SCRIPT = process.env.ONTOBDC_PROMOTE_SCRIPT;

// ---- the smallest DOM the bridge needs -------------------------------
// Node's own EventTarget retargets `event.target` on every re-dispatch, so
// bubbling is walked explicitly here: the bridge resolves the owning
// Surface from `event.target`, and it has to stay the node that announced.
class DomNode {
  constructor(localName, parent) {
    this.localName = localName;
    this.parentElement = parent ?? null;
    this._listeners = new Map();
  }
  addEventListener(type, handler) {
    if (!this._listeners.has(type)) this._listeners.set(type, []);
    this._listeners.get(type).push(handler);
  }
  removeEventListener(type, handler) {
    const handlers = this._listeners.get(type) ?? [];
    const index = handlers.indexOf(handler);
    if (index >= 0) handlers.splice(index, 1);
  }
  dispatchEvent(event) {
    Object.defineProperty(event, "target", { value: this, configurable: true });
    let node = this;
    while (node) {
      for (const handler of [...(node._listeners.get(event.type) ?? [])]) handler(event);
      if (!event.bubbles) return true;
      node = node.parentElement;
    }
    for (const handler of [...(globalThis.document._listeners.get(event.type) ?? [])]) {
      handler(event);
    }
    return true;
  }
}

class Element extends DomNode {
  closest(selector) {
    let node = this;
    while (node) {
      if (node.localName === selector) return node;
      node = node.parentElement;
    }
    return null;
  }
  getRootNode() { return globalThis.document; }
}
globalThis.Element = Element;

const surface = new Element("onto-presentation-surface", null);
const tile = new Element("onto-file-tree-tile", surface);

const documentNode = new DomNode("#document", null);
documentNode.querySelectorAll = (selector) =>
  selector === "onto-presentation-surface" ? [surface] : [];
documentNode.querySelector = () => null;
documentNode.head = { appendChild() {} };
documentNode.createElement = () => ({});
globalThis.document = documentNode;
globalThis.window = globalThis;
globalThis.requestIdleCallback = undefined;

// ---- the interpreter host stand-in -----------------------------------
let installedSource = null;

globalThis.loadPyodide = async () => ({
  loadPackage: async () => {},
  runPythonAsync: async (source) => {
    if (source.includes("micropip")) return undefined;
    // The dock installer bundle — really executed, into a root the
    // promote() one-shot then imports from.
    mkdirSync(DOCK_ROOT, { recursive: true });
    const installerPath = join(DOCK_ROOT, "_installer.py");
    writeFileSync(
      installerPath,
      source.replace('"/lib/ontobdc-view-dock"', JSON.stringify(DOCK_ROOT)),
      "utf-8",
    );
    execFileSync(PYTHON, [installerPath], { encoding: "utf-8" });
    installedSource = source;
    return undefined;
  },
  globals: {
    get: (name) => {
      if (name !== "ontobdc_web_dock" || installedSource === null) return undefined;
      return {
        bootstrap: (turtle) => {
          writeFileSync(POLICY_PATH, turtle, "utf-8");
          return { ready: true };
        },
        // Synchronous, string in / string out — the shape a Pyodide
        // PyProxy of `runtime.promote` has.
        promote: (envelopeJson) =>
          execFileSync(PYTHON, [PROMOTE_SCRIPT, DOCK_ROOT, POLICY_PATH], {
            input: envelopeJson,
            encoding: "utf-8",
          }),
      };
    },
  },
});

// ---- drive the shipped bridge ----------------------------------------
const { promoter, SHARED_EVENT_TYPE } = await import(process.env.ONTOBDC_BRIDGE);

const dispatched = [];
const announced = [];
surface.addEventListener(SHARED_EVENT_TYPE, (event) => dispatched.push(event.detail));
surface.announcePromotion = (promotion) => { announced.push(promotion); return true; };

async function settle() {
  for (let attempt = 0; attempt < 400; attempt += 1) {
    if (promoter.ready && promoter.pendingCount === 0) return;
    await new Promise((resolve) => setTimeout(resolve, 5));
  }
  throw new Error("the promoter never drained its queue");
}

const script = JSON.parse(process.env.ONTOBDC_SCRIPT);
for (const step of script) {
  tile.dispatchEvent(new CustomEvent("ontobdc:component-event", {
    bubbles: true,
    composed: true,
    detail: { event: step.event, tile: tile.localName, ...(step.detail || {}) },
  }));
}
await settle();

process.stdout.write(JSON.stringify({ dispatched, announced, ready: promoter.ready }));
'''


@pytest.fixture(scope="module")
def flow():
    """Runs a script of Component Events through the real bridge once and
    returns what came out."""
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        (root / "bridge.mjs").write_text(
            ontobdc_view.component_event_promoter_source(), encoding="utf-8"
        )
        (root / "harness.mjs").write_text(HARNESS, encoding="utf-8")
        (root / "promote.py").write_text(PROMOTE_SCRIPT, encoding="utf-8")
        # Sanity: the bundle the harness will install is the shipped one.
        assert "ontobdc_web_dock" in listener_runtime_source()

        script = [
            {"event": "SurfaceLoaded"},
            {"event": "TileOpened", "detail": {"path": "a/b.csv"}},
            {"event": "TileClosed", "detail": {"path": "a/b.csv"}},
            {"event": "TileExpanded"},
            {"event": "TileCollapsed"},
            {"event": "TileFullSized"},
            {"event": "TileRestored"},
            {"event": "EntityPageOpenRequested", "detail": {"path": "a/b.csv", "kind": "file"}},
            {"event": "EntityPageCloseRequested", "detail": {"path": "a/b.csv", "kind": "file"}},
            {"event": "EntitySelected", "detail": {"path": "a/b.csv"}},
        ]

        completed = subprocess.run(
            [NODE, str(root / "harness.mjs")],
            capture_output=True,
            text=True,
            timeout=600,
            env={
                "PATH": "/usr/bin:/bin:/usr/local/bin",
                "HOME": str(root),
                "ONTOBDC_PYTHON": sys.executable,
                "ONTOBDC_BRIDGE": str(root / "bridge.mjs"),
                "ONTOBDC_DOCK_ROOT": str(root / "dockroot"),
                "ONTOBDC_POLICY_PATH": str(root / "policy.ttl"),
                "ONTOBDC_PROMOTE_SCRIPT": str(root / "promote.py"),
                "ONTOBDC_SCRIPT": json.dumps(script),
                "PYTHONPATH": "",
            },
        )
        if completed.returncode != 0:
            pytest.fail(f"harness failed:\n{completed.stderr}\n{completed.stdout}")
        yield json.loads(completed.stdout)


def dispatched_for(flow, component_event):
    return [
        detail["event"]
        for detail in flow["dispatched"]
        if detail["promotedFrom"] == component_event
    ]


@pytest.mark.parametrize(
    ("component_event", "shared_events"),
    [
        ("SurfaceLoaded", {"PageLoaded"}),
        ("TileOpened", {"TileReady", "SurfaceAreaFilled"}),
        ("TileClosed", {"TileStandby", "SurfaceAreaEmptied"}),
        ("TileExpanded", {"TileResized", "SurfaceAreaFilled"}),
        ("TileCollapsed", {"TileResized", "SurfaceAreaEmptied"}),
        ("TileFullSized", {"SurfaceObscured"}),
        ("TileRestored", {"SurfaceRevealed"}),
        ("EntityPageOpenRequested", {"EntityPageRequested"}),
        ("EntityPageCloseRequested", {"EntityPageDismissRequested"}),
    ],
)
def test_the_bridge_dispatches_what_the_listener_promoted(flow, component_event, shared_events):
    assert set(dispatched_for(flow, component_event)) == shared_events


def test_an_occurrence_the_policy_does_not_declare_dispatches_nothing(flow):
    assert dispatched_for(flow, "EntitySelected") == []


def test_the_event_bar_is_announced_once_per_promoted_shared_event(flow):
    """The bar shows promotions, not Component Events: ten occurrences went
    in, and the bar carries exactly the promoted targets."""
    assert len(flow["announced"]) == len(flow["dispatched"])
    assert len(flow["announced"]) == 13  # the nine mappings, TileOpened/Closed/... expanded
    for promotion in flow["announced"]:
        assert promotion["sharedEvent"]
        assert promotion["componentEvent"]
    announced_pairs = {
        (promotion["componentEvent"], promotion["sharedEvent"]) for promotion in flow["announced"]
    }
    assert ("EntitySelected", "PageLoaded") not in announced_pairs
    assert not any(pair[0] == "EntitySelected" for pair in announced_pairs)


def test_the_payload_survives_the_round_trip(flow):
    opened = [
        detail for detail in flow["dispatched"] if detail["promotedFrom"] == "EntityPageOpenRequested"
    ]
    assert opened, "EntityPageOpenRequested was not promoted"
    for detail in opened:
        assert detail["path"] == "a/b.csv"
        assert detail["kind"] == "file"
        assert detail["tile"] == "onto-file-tree-tile"
        assert detail["event"] == "EntityPageRequested"


def test_occurrences_that_arrived_before_the_runtime_was_ready_were_not_lost(flow):
    """Every occurrence in the script was dispatched at page start, before
    the interpreter finished booting — the queue is what makes them all
    still arrive, in place of a JavaScript answer."""
    assert flow["ready"] is True
    promoted_sources = {detail["promotedFrom"] for detail in flow["dispatched"]}
    assert promoted_sources == {
        "SurfaceLoaded",
        "TileOpened",
        "TileClosed",
        "TileExpanded",
        "TileCollapsed",
        "TileFullSized",
        "TileRestored",
        "EntityPageOpenRequested",
        "EntityPageCloseRequested",
    }
