"""The bridge integrates; it does not decide.

`component_event_promoter.js` is the single Component -> Shared promotion
path in the browser. These tests pin what that means in practice: it calls
the Python Listener, it dispatches exactly what the Listener answered, it
queues rather than guessing when the runtime is not up, and there is no
JavaScript fallback anywhere in it.

The last group runs the Python side the bridge actually ships — the
generated installer bundle, executed as a module — so the code proven here
is byte-for-byte the code Pyodide runs.
"""

import json
import os
import re
import tempfile
from pathlib import Path

import pytest

import ontobdc_view
from ontobdc_view.component.adapter.dock import (
    dock_runtime_module_names,
    listener_runtime_source,
)

ASSETS = Path(__file__).resolve().parents[1] / "src/ontobdc_view/component/asset"


@pytest.fixture(scope="module")
def bridge() -> str:
    # The bridge is assembled in Python, not shipped as a .js asset.
    return ontobdc_view.component_event_promoter_source()


@pytest.fixture(scope="module")
def built_bridge() -> str:
    return ontobdc_view.component_event_promoter_source()


def without_embedded_blobs(text: str) -> str:
    # The bridge embeds two opaque blobs verbatim -- the presentation
    # event policy (Turtle) and the dock Python runtime (a JSON source
    # bundle). Neither is bridge logic; strip them before scanning so an
    # event name or URL that legitimately lives inside the policy or the
    # runtime source is not mistaken for one the JavaScript itself holds.
    return re.sub(
        r"^const (PRESENTATION_EVENT_POLICY|DOCK_RUNTIME_SOURCE) = .*;$",
        r"const \1 = <embedded>;",
        text,
        flags=re.MULTILINE,
    )


def code_only(text: str) -> str:
    text = without_embedded_blobs(text)
    text = re.sub(r"/\*.*?\*/", "", text, flags=re.DOTALL)
    return "\n".join(re.sub(r"//.*$", "", line) for line in text.splitlines())


# --------------------------------------------------------------------------
# One promoter, no second path
# --------------------------------------------------------------------------


def test_the_bridge_is_assembled_in_python_not_shipped_as_an_asset():
    assert not (ASSETS / "component_event_promoter.js").exists()
    assert "COMPONENT EVENT" in ontobdc_view.component_event_promoter_source()


def test_there_is_no_second_promoter_asset():
    promoters = sorted(p.name for p in ASSETS.glob("*promoter*.js"))
    assert promoters == []


def test_the_bridge_is_classic_script_compatible(bridge):
    bridge_source = code_only(bridge)

    assert "window.OntoBDCComponentEventPromoter = promoter;" in bridge_source
    assert "export {" not in bridge_source


def test_the_bridge_announces_to_a_standalone_page_display(bridge):
    code = code_only(bridge)

    assert "window.OntoBDCPageEventDisplay" in code
    assert "pageDisplay.announcePromotion" in code
    assert "pageDisplay.announcePromotionFailure" in code


def test_the_bridge_signals_when_its_listener_is_ready(bridge):
    assert '"ontobdc:component-event-promoter-ready"' in bridge


def test_the_bridge_listens_for_the_component_event_envelope_once(bridge):
    code = code_only(bridge)
    assert code.count("addEventListener(COMPONENT_EVENT_TYPE") == 1
    assert "Symbol.for(" in code  # the once-guard, as the viewer Tile already uses


# --------------------------------------------------------------------------
# The decision belongs to Python
# --------------------------------------------------------------------------


def test_the_bridge_holds_no_promotion_rule(bridge):
    """No mapping, no branch on an event name, no name translation."""
    code = code_only(bridge)
    for shared in (
        "PageLoaded",
        "TileReady",
        "TileStandby",
        "TileResized",
        "SurfaceAreaFilled",
        "SurfaceAreaEmptied",
        "SurfaceObscured",
        "SurfaceRevealed",
        "EntityPageRequested",
        "EntityPageDismissRequested",
    ):
        assert shared not in code
    for component in ("SurfaceLoaded", "TileOpened", "TileFullSized", "EntityPageOpenRequested"):
        assert component not in code
    assert "switch" not in code


def test_the_dispatched_names_come_straight_from_the_listener_answer(bridge):
    code = code_only(bridge)
    dispatch = code[code.index("function dispatchSharedEvent") :]
    dispatch = dispatch[: dispatch.index("\n}\n")]
    assert "event: target.event" in dispatch
    assert "promotedFrom: answer.componentEvent" in dispatch
    # The type is the canonical envelope, never a name the bridge invented.
    assert "new CustomEvent(SHARED_EVENT_TYPE" in dispatch


def test_zero_targets_dispatch_and_announce_nothing(bridge):
    code = code_only(bridge)
    resolve = code[code.index("async #resolveAndDispatch(occurrence)") :]
    resolve = resolve[: resolve.index("\n  }\n")]
    # Everything happens inside the loop over the answered targets, so an
    # empty answer is a no-op by construction.
    assert "for (const target of targets)" in resolve
    assert "announcePromotion(occurrence, answer, target)" in resolve
    assert "dispatchSharedEvent(occurrence, answer, target)" in resolve


def test_the_bridge_calls_the_python_listener(bridge):
    code = code_only(bridge)
    assert "runPythonAsync(DOCK_RUNTIME_SOURCE)" in code
    assert 'pyodide.globals.get("ontobdc_web_dock")' in code
    assert "runtimeModule.bootstrap(PRESENTATION_EVENT_POLICY)" in code
    assert "return runtimeModule.promote;" in code
    assert "this.#promote(JSON.stringify(occurrence.envelope))" in code


def test_the_python_names_the_bridge_calls_exist_in_the_runtime():
    """Cross-language contract: the attribute names the JavaScript reaches
    for are really module-level callables of the shipped dock runtime."""
    import ontobdc_web_dock as runtime

    code = code_only(ontobdc_view.component_event_promoter_source())
    for attribute in re.findall(r"runtimeModule\.(\w+)", code):
        assert callable(getattr(runtime, attribute)), attribute


# --------------------------------------------------------------------------
# No fallback, explicit failure, queueing
# --------------------------------------------------------------------------


def test_occurrences_queue_until_the_runtime_is_ready(bridge):
    code = code_only(bridge)
    accept = code[code.index("  accept(occurrence) {") :]
    accept = accept[: accept.index("\n  }\n")]
    assert "this.#pending.push(occurrence)" in accept
    drain = code[code.index("  async #drain() {") :]
    drain = drain[: drain.index("\n  }\n")]
    assert "await this.bootstrap()" in drain
    # A failed bootstrap returns without draining — the queue is kept.
    assert "return; " in drain or "return;" in drain


def test_a_failed_runtime_is_reported_rather_than_worked_around(bridge):
    code = code_only(bridge)
    assert "announceFailure(error)" in code
    assert "console.error" in code
    for word in ("fallback", "FALLBACK"):
        assert word not in code


def test_the_bridge_never_decides_when_python_is_unavailable(bridge):
    """There must be no branch that produces targets without the Listener."""
    code = code_only(bridge)
    assert "targets" in code
    for match in re.finditer(r"targets\s*=\s*(.+)", code):
        assert "answer.targets" in match.group(1), match.group(0)


def test_the_transport_is_in_process_pyodide_only(bridge):
    """JS -> Pyodide -> Python, in one process. No server anywhere in the
    chain, so a file:// page keeps working."""
    code = code_only(bridge)
    for forbidden in (
        "WebSocket",
        "EventSource",
        "XMLHttpRequest",
        "navigator.sendBeacon",
        "fetch(",
    ):
        assert forbidden not in code
    # The only network reference is the pinned Pyodide distribution, and
    # only when the page has no host runtime that already loaded it. Read
    # from the raw source: comment stripping would eat "https://" itself.
    urls = re.findall(r'"(https?://[^"]+)"', without_embedded_blobs(bridge))
    assert urls == ["https://cdn.jsdelivr.net/pyodide/v0.27.2/full/pyodide.js"]


def test_the_policy_document_travels_with_the_page(built_bridge):
    """No download of the ontology per event — or at all: the Turtle is
    embedded at build time, so file:// pages work."""
    policy = ontobdc_view.presentation_event_policy()
    assert "view:promotesTo" in policy
    # The whole document is present in the built bridge, as a string literal.
    assert json.dumps(policy, ensure_ascii=False) in built_bridge
    assert "__ONTOBDC_BUILD_" not in built_bridge


def test_the_built_bridge_still_reaches_no_host_but_pyodide(built_bridge):
    """Embedding the policy and the runtime must not have introduced a
    second origin — the resolved bundle is checked, not just the template."""
    origins = {
        match.split("/")[2] for match in re.findall(r"https?://[^\s\"']+", built_bridge)
    }
    # cdn.jsdelivr.net is the only one ever fetched. The rest are IRIs
    # inside the embedded RDF policy and the Listener's plugin metadata —
    # identifiers, never requests.
    assert origins <= {
        "cdn.jsdelivr.net",
        "datacenter.app.br",
        "www.w3.org",
        "kb.elias.eng.br",
    }


def test_the_policy_is_parsed_once_not_per_event(bridge):
    code = code_only(bridge)
    assert code.count("bootstrap(PRESENTATION_EVENT_POLICY)") == 1
    bootstrap = code[code.index("  bootstrap() {") :]
    bootstrap = bootstrap[: bootstrap.index("\n  }\n")]
    assert "if (this.#bootstrapPromise) return this.#bootstrapPromise;" in bootstrap


def test_a_host_page_runtime_pyodide_is_reused_rather_than_duplicated(bridge):
    code = code_only(bridge)
    assert "OntoBDCWorkStreamViewRuntime" in code
    assert "host.ensurePyodide()" in code
    assert "host.withPyodideLock" in code


# --------------------------------------------------------------------------
# The shipped Python bundle
# --------------------------------------------------------------------------


def test_the_runtime_bundle_carries_the_whole_dock_package():
    names = dock_runtime_module_names()
    assert "bridge.py" in names
    assert "dock/adapter/policy.py" in names
    assert "dock/adapter/loader.py" in names
    assert "dock/plugin/listener/presentation_event.py" in names
    assert "dock/domain/machine/promotion_state.py" in names


def test_the_dock_package_imports_nothing_pyodide_lacks():
    """It runs in the browser: standard library and rdflib only."""
    import ontobdc_web_dock
    root = Path(ontobdc_web_dock.__file__).parent
    forbidden = ("ontobdc.", "pydantic", "sismic", "yaml", "jinja2", "requests")
    for path in sorted(root.rglob("*.py")):
        text = path.read_text(encoding="utf-8")
        code = "\n".join(
            line for line in text.splitlines() if line.strip().startswith(("import ", "from "))
        )
        for module in forbidden:
            assert module not in code, f"{path.name} imports {module}"


def test_the_shipped_bundle_installs_and_answers_exactly_like_the_package():
    """Executes the generated installer — the same text handed to
    `pyodide.runPythonAsync` — in a throwaway root, then drives it through
    the same JSON contract the bridge uses."""
    installer = listener_runtime_source()
    policy = ontobdc_view.presentation_event_policy()

    with tempfile.TemporaryDirectory() as tmp:
        # Pyodide writes into its own in-memory FS at /lib; a test process
        # needs a writable root of its own. The installer honours
        # ONTOBDC_DOCK_ROOT for exactly this.
        previous = os.environ.get("ONTOBDC_DOCK_ROOT")
        os.environ["ONTOBDC_DOCK_ROOT"] = os.path.join(tmp, "lib")
        try:
            namespace: dict = {}
            exec(compile(installer, "<dock-installer>", "exec"), namespace)
        finally:
            if previous is None:
                os.environ.pop("ONTOBDC_DOCK_ROOT", None)
            else:
                os.environ["ONTOBDC_DOCK_ROOT"] = previous
        runtime = namespace["ontobdc_web_dock"]

        ready = runtime.bootstrap(policy)
        assert ready["ready"] is True
        assert ready["listeners"] == [
            "org.ontobdc.web_dock.dock.plugin.listener."
            "presentation_event_promotion"
        ]

        answer = json.loads(
            runtime.promote(json.dumps({"event": "TileOpened", "detail": {"tile": "t"}}))
        )
        assert {target["event"] for target in answer["targets"]} == {
            "TileReady",
            "SurfaceAreaFilled",
        }

        # zero, one and many, all through the shipped bundle
        assert json.loads(runtime.promote(json.dumps({"event": "Unknown"})))["targets"] == []
        single = json.loads(runtime.promote(json.dumps({"event": "SurfaceLoaded"})))
        assert [t["event"] for t in single["targets"]] == ["PageLoaded"]
