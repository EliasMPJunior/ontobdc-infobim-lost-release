"""Builds the dDock for the browser page.

Three things have to reach a Surface page for the event architecture to
work, and all three are produced here at generation time -- the moment
where ``brasidatacenter`` (the ontology's home) and ``ontobdc_web_dock``
are importable, and the browser is not:

1. **the promotion policy document** -- ``presentation_event.ttl`` itself,
   read from the BrasidataCenter package where the ontology lives;
2. **the dDock Python runtime** -- the ``ontobdc_web_dock`` package,
   turned into a self-installing source bundle that Pyodide materializes
   as the top-level package ``ontobdc_web_dock`` (its modules import
   nothing but the standard library and ``rdflib``, so no ``ontobdc``
   distribution is ever shipped to the browser);
3. **the bridge script** -- assembled here, in Python, with the two above
   embedded. It is never read from a ``.js`` asset file.

Nothing here interprets the policy. The Turtle document travels verbatim
and is parsed, indexed and queried by the Python Listener in the browser.
"""

from __future__ import annotations

import json
from importlib.resources import files
from pathlib import Path
from typing import Dict, List

_DOCK_PACKAGE = "ontobdc_web_dock"
_DOCK_PYODIDE_ROOT = "/lib/ontobdc-web-dock"

# The one canonical DOM envelope in each direction. The bridge needs no
# list of which event names exist because the semantic name rides in
# ``detail.event``.
_COMPONENT_EVENT_TYPE = "ontobdc:component-event"
_SHARED_EVENT_TYPE = "ontobdc:shared-event"

_PYODIDE_CDN_URL = "https://cdn.jsdelivr.net/pyodide/v0.27.2/full/pyodide.js"


def presentation_event_policy() -> str:
    """The ``presentation_event.ttl`` Turtle document, verbatim.

    Source of truth is BrasidataCenter's
    ``ontology/tool/ontobdc/abox/presentation_event.ttl``; this function
    only reads it.
    """
    from brasidatacenter.resources import ontology_path

    path = ontology_path(
        "tool", "ontobdc", "abox", "presentation_event.ttl"
    )
    return Path(str(path)).read_text(encoding="utf-8")


def _dock_module_sources() -> Dict[str, str]:
    """Every ``.py`` under the installed ``ontobdc_web_dock`` package,
    keyed by its path relative to the package root (so the loader's
    ``pkgutil`` walk still finds ``dock/plugin/listener/*.py``)."""
    root = Path(str(files(_DOCK_PACKAGE)))
    sources: Dict[str, str] = {}
    for path in sorted(root.rglob("*.py")):
        if "__pycache__" in path.parts:
            continue
        relative = path.relative_to(root).as_posix()
        sources[relative] = path.read_text(encoding="utf-8")
    return sources


def dock_runtime_module_names() -> List[str]:
    return sorted(_dock_module_sources())


def listener_runtime_source() -> str:
    """A self-contained Python script that installs and imports the dDock.

    Executed once inside Pyodide. It materializes the ``ontobdc_web_dock``
    sources onto the in-browser filesystem, puts them on ``sys.path`` and
    imports the package -- so the Listener plugin loader's normal
    ``pkgutil`` walk discovers the Listener exactly as it does under
    pytest, and the code running in the browser is byte-for-byte the code
    the test suite exercises.
    """
    encoded = json.dumps(_dock_module_sources(), ensure_ascii=False)
    return (
        "# OntoBDC Web Dock runtime installer (generated, do not edit by hand).\n"
        "import json as _json\n"
        "import os as _os\n"
        "import sys as _sys\n"
        f"_ONTOBDC_DOCK_PACKAGE = {_DOCK_PACKAGE!r}\n"
        f"_ONTOBDC_DOCK_ROOT = _os.environ.get('ONTOBDC_DOCK_ROOT') or {_DOCK_PYODIDE_ROOT!r}\n"
        f'_ONTOBDC_DOCK_SOURCES = _json.loads(r"""{encoded}""")\n'
        "_package_dir = _os.path.join(_ONTOBDC_DOCK_ROOT, _ONTOBDC_DOCK_PACKAGE)\n"
        "for _relative, _source in _ONTOBDC_DOCK_SOURCES.items():\n"
        "    _target = _os.path.join(_package_dir, *_relative.split('/'))\n"
        "    _os.makedirs(_os.path.dirname(_target), exist_ok=True)\n"
        "    with open(_target, 'w', encoding='utf-8') as _handle:\n"
        "        _handle.write(_source)\n"
        "if _ONTOBDC_DOCK_ROOT not in _sys.path:\n"
        "    _sys.path.insert(0, _ONTOBDC_DOCK_ROOT)\n"
        "import importlib as _importlib\n"
        "_importlib.invalidate_caches()\n"
        "ontobdc_web_dock = _importlib.import_module(_ONTOBDC_DOCK_PACKAGE)\n"
    )


def component_event_promoter_source() -> str:
    """The Component -> Shared promotion bridge script, assembled in Python.

    There is one and only one such bridge in the browser; it carries no
    promotion table and never renames an event -- the names it dispatches
    are exactly the names the Python Listener answered with. The source is
    classic-script compatible so it can run both in generated Page assets
    and inside the Surface's module script tag.
    """
    policy_json = json.dumps(presentation_event_policy(), ensure_ascii=False)
    runtime_json = json.dumps(listener_runtime_source(), ensure_ascii=False)

    return f"""// dDock bridge -- Component Event -> Shared Event promotion.
// GENERATED by ontobdc_view.component.adapter.dock; do not edit by hand.
//
//   interaction -> Tile/Surface JS -> COMPONENT EVENT (bubbles, composed)
//     -> this bridge -> Pyodide -> ontobdc_web_dock Listener (Python)
//     -> view:promotesTo (presentation_event.ttl)
//     -> zero / one / many Shared Events -> this bridge
//     -> Surface announcement + SHARED EVENT dispatch
//
// The bridge holds no promotion rules and never translates one event name
// into another. An empty target list means nothing is dispatched -- an
// occurrence that promotes to nothing is a normal outcome. There is no
// JavaScript fallback: occurrences queue until the runtime is ready, and
// a runtime failure is reported explicitly with the queue kept.

const COMPONENT_EVENT_TYPE = {_COMPONENT_EVENT_TYPE!r};
const SHARED_EVENT_TYPE = {_SHARED_EVENT_TYPE!r};

// --- debug -----------------------------------------------------------
// Verbose while the event architecture is being brought up. Flip to
// false (or set window.__ontobdcDockDebug = false before this loads) to
// silence.
const DEBUG =
  typeof window !== "undefined" && window.__ontobdcDockDebug === false
    ? false
    : true;
function log(...args) {{
  if (DEBUG) console.log("%c[dDock]", "color:#0284c7;font-weight:bold", ...args);
}}
function pyToJs(value) {{
  try {{
    return value && typeof value.toJs === "function"
      ? value.toJs({{ dict_converter: Object.fromEntries }})
      : value;
  }} catch (error) {{
    return value;
  }}
}}
log("bridge script loaded; listening for", COMPONENT_EVENT_TYPE);

// The promotion policy document (presentation_event.ttl), embedded verbatim
// so a file:// page needs no fetch. Never read here -- handed to Python.
const PRESENTATION_EVENT_POLICY = {policy_json};

// The dDock Python package, as a self-installing source bundle.
const DOCK_RUNTIME_SOURCE = {runtime_json};

const PYODIDE_CDN_URL = "{_PYODIDE_CDN_URL}";

const HOST_RUNTIME_KEYS = [
  "OntoBDCWorkStreamViewRuntime",
  "OntoBDCGanttViewRuntime",
  "OntoBDCEntityViewRuntime",
];

function hostRuntime() {{
  for (const key of HOST_RUNTIME_KEYS) {{
    const candidate = window[key];
    if (candidate && typeof candidate.ensurePyodide === "function") return candidate;
  }}
  return null;
}}

function loadScriptTag(src) {{
  return new Promise((resolve, reject) => {{
    const script = document.createElement("script");
    script.src = src;
    script.onload = resolve;
    script.onerror = () => reject(new Error(`Failed to load ${{src}}`));
    document.head.appendChild(script);
  }});
}}

async function ownPyodide() {{
  if (typeof loadPyodide !== "function") {{
    await loadScriptTag(PYODIDE_CDN_URL);
  }}
  const instance = await loadPyodide();
  await instance.loadPackage("micropip");
  await instance.runPythonAsync("import micropip\\nawait micropip.install('rdflib')");
  return instance;
}}

class ComponentEventPromoter {{
  #promote = null;
  #bootstrapPromise = null;
  #pending = [];
  #failure = null;
  #draining = false;

  get ready() {{ return this.#promote !== null; }}
  get pendingCount() {{ return this.#pending.length; }}
  get failure() {{ return this.#failure; }}

  bootstrap() {{
    if (this.#bootstrapPromise) return this.#bootstrapPromise;
    log("bootstrap: starting");
    this.#bootstrapPromise = (async () => {{
      const host = hostRuntime();
      log("bootstrap: pyodide via", host ? "host runtime" : "own loadPyodide");
      const pyodide = host ? await host.ensurePyodide() : await ownPyodide();
      const withLock =
        host && typeof host.withPyodideLock === "function"
          ? host.withPyodideLock
          : (task) => task();
      const promote = await withLock(async () => {{
        log("bootstrap: installing ontobdc_web_dock into Pyodide");
        await pyodide.runPythonAsync(DOCK_RUNTIME_SOURCE);
        const runtimeModule = pyodide.globals.get("ontobdc_web_dock");
        if (!runtimeModule) {{
          throw new Error("ontobdc_web_dock runtime did not install in Pyodide");
        }}
        log("bootstrap: runtime installed; parsing policy");
        const info = pyToJs(runtimeModule.bootstrap(PRESENTATION_EVENT_POLICY));
        // <-- Python -> JS: what the Listener knows after bootstrap.
        log("bootstrap: Python returned", info);
        return runtimeModule.promote;
      }});
      this.#promote = promote;
      this.#failure = null;
      log("bootstrap: ready");
      return promote;
    }})();
    this.#bootstrapPromise.catch((error) => {{
      this.#failure = error;
      this.#bootstrapPromise = null;
      console.error("[dDock] promotion runtime unavailable", error);
      announceFailure(error);
    }});
    return this.#bootstrapPromise;
  }}

  accept(occurrence) {{
    log("accept: component event", occurrence.envelope.event, occurrence.envelope);
    this.#pending.push(occurrence);
    return this.#drain();
  }}

  async #drain() {{
    if (this.#draining) return;
    this.#draining = true;
    try {{
      while (this.#pending.length) {{
        if (!this.ready) {{
          try {{ await this.bootstrap(); }}
          catch (error) {{ log("drain: bootstrap failed, keeping queue", error); return; }}
        }}
        const occurrence = this.#pending.shift();
        try {{ await this.#resolveAndDispatch(occurrence); }}
        catch (error) {{
          console.error("[dDock] the Listener could not answer", occurrence.envelope, error);
        }}
      }}
    }} finally {{
      this.#draining = false;
    }}
  }}

  async #resolveAndDispatch(occurrence) {{
    log("promote: ->", occurrence.envelope);
    const raw = this.#promote(JSON.stringify(occurrence.envelope));
    // <-- Python -> JS: the Listener's answer, as a JSON string.
    log("promote: <- (raw)", raw);
    const answer = JSON.parse(raw);
    log(
      "promote: <- (parsed)",
      "status=" + answer.status,
      "targets=" + JSON.stringify(answer.targets),
      "trace=" + JSON.stringify(answer.trace),
    );
    const targets = Array.isArray(answer.targets) ? answer.targets : [];
    if (targets.length === 0) {{
      log("promote: no targets ->", occurrence.envelope.event, "is not promoted");
    }}
    for (const target of targets) {{
      log("dispatch: shared event", target.event, "(promoted from", answer.componentEvent + ")");
      announcePromotion(occurrence, answer, target);
      dispatchSharedEvent(occurrence, answer, target);
    }}
    return answer;
  }}
}}

const promoter = new ComponentEventPromoter();

function promotionDisplay(occurrence) {{
  const surface = occurrence.surface;
  if (surface && typeof surface.announcePromotion === "function") return surface;
  const pageDisplay = window.OntoBDCPageEventDisplay;
  if (pageDisplay && typeof pageDisplay.announcePromotion === "function") return pageDisplay;
  return null;
}}

function announcePromotion(occurrence, answer, target) {{
  const display = promotionDisplay(occurrence);
  if (!display) return;
  display.announcePromotion({{
    sharedEvent: target.event,
    sharedEventIri: target.iri,
    componentEvent: answer.componentEvent,
    componentEventIri: answer.componentEventIri,
    detail: occurrence.envelope.detail,
  }});
}}

function announceFailure(error) {{
  for (const surface of document.querySelectorAll("onto-presentation-surface")) {{
    if (typeof surface.announcePromotionFailure === "function") {{
      surface.announcePromotionFailure(error);
    }}
  }}
  const pageDisplay = window.OntoBDCPageEventDisplay;
  if (pageDisplay && typeof pageDisplay.announcePromotionFailure === "function") {{
    pageDisplay.announcePromotionFailure(error);
  }}
}}

function dispatchSharedEvent(occurrence, answer, target) {{
  const detail = {{
    ...(occurrence.envelope.detail || {{}}),
    event: target.event,
    eventIri: target.iri,
    promotedFrom: answer.componentEvent,
    promotedFromIri: answer.componentEventIri,
  }};
  const node = occurrence.surface || document;
  log("dispatchSharedEvent:", SHARED_EVENT_TYPE, "on", node === document ? "document" : node, detail);
  node.dispatchEvent(
    new CustomEvent(SHARED_EVENT_TYPE, {{ bubbles: true, composed: true, detail }}),
  );
}}

function owningSurface(target) {{
  if (!(target instanceof Element)) return null;
  const direct = target.closest("onto-presentation-surface");
  if (direct) return direct;
  const root = target.getRootNode?.();
  if (root && root.host instanceof Element) {{
    return root.host.closest("onto-presentation-surface") ?? null;
  }}
  return null;
}}

const ONCE_KEY = Symbol.for("ontobdc.component-event-promoter.attached");
if (!document[ONCE_KEY]) {{
  document[ONCE_KEY] = true;
  document.addEventListener(COMPONENT_EVENT_TYPE, (event) => {{
    const detail = event.detail || {{}};
    const name = String(detail.event || "").trim();
    log("received", COMPONENT_EVENT_TYPE, "name=" + (name || "<empty>"), "target=", event.target, detail);
    if (!name) {{
      log("ignored: envelope carried no detail.event");
      return;
    }}
    const surface = owningSurface(event.target);
    log("resolved owning surface:", surface || "<none>");
    promoter.accept({{
      surface,
      origin: event.target,
      envelope: {{ event: name, detail }},
    }});
  }});
  const warm = () => promoter.bootstrap().catch(() => {{}});
  if (typeof requestIdleCallback === "function") requestIdleCallback(warm);
  else setTimeout(warm, 0);
}}

window.OntoBDCComponentEventPromoter = promoter;
document.dispatchEvent(new CustomEvent("ontobdc:component-event-promoter-ready"));

"""
