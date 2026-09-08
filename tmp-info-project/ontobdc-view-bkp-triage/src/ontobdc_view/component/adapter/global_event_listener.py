"""Ships the Global Event listener into Pyodide.

`submitGlobalEvent()` is a direct call from the Page into Python: the Page
hands over the event it just wrote to its data source, and the call resolves
only once the listener has stored the event in the dataset and appended its
JSON-LD to the Surface journal. There is no queue and no daemon between the
two, so the Python has to be *in* the browser runtime.

What gets shipped is the real modules, at their real import paths — the
journal writer that already exists, the statechart states, the listener that
coordinates them. No copies and no rewritten imports: the code that runs in
Pyodide is the code the test suite exercises, found under the same names.

They can be shipped at all because each one imports only the standard
library. They live in this distribution rather than in `ontobdc`: `ontobdc`
depends on `ontobdc-view`, so reading them out of an installed `ontobdc`
would be an import cycle that only resolves when both repositories happen
to sit side by side on a developer's disk.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, List

# The listener's own modules, in dependency order. Named explicitly rather
# than discovered: shipping the whole `ontobdc` tree into a browser would
# pull in pydantic, sismic, rdflib and the rest, none of which is there.
_LISTENER_MODULES = (
    "ontobdc_view/shared/adapter/atomic_file.py",
    "ontobdc_view/surface/domain/machine/global_event_state.py",
    "ontobdc_view/surface/adapter/global_event.py",
    "ontobdc_view/surface/adapter/global_event_listener.py",
)

_PYODIDE_ROOT = "/lib/ontobdc-global-event"

# Standard library only. A module here that reaches for anything else would
# fail at import inside Pyodide, where the failure is a blank page rather
# than a stack trace anyone sees.
_FORBIDDEN_IMPORTS = ("pydantic", "sismic", "rdflib", "yaml", "jinja2", "requests", "frictionless")


def _ontobdc_source_root() -> Path:
    """The directory holding the `ontobdc_view` package, wherever it is installed.

    The paths in `_LISTENER_MODULES` are relative to this, so the tree that
    gets shipped into Pyodide is laid out exactly as it is here and the
    modules import each other under the names they already use.

    Taken from this file rather than by importing the package: importing
    `ontobdc_view` runs its `__init__`, which pulls in the Tile plugins and
    the whole component loader. None of that is needed to read four files
    off the disk, and the shipped tree must stay importable without it —
    which, in Pyodide, is exactly the situation.
    """
    # Walk up to the directory that *contains* the package rather than
    # counting parents, which silently points at the wrong root if the
    # layout moves.
    path = Path(__file__).resolve()
    for parent in path.parents:
        if parent.name == "ontobdc_view":
            return parent.parent
    raise FileNotFoundError(f"{path} is not inside an `ontobdc_view` package")


def listener_module_sources() -> Dict[str, str]:
    """Each shipped module, keyed by its import path within the tree."""
    root = _ontobdc_source_root()
    sources: Dict[str, str] = {}
    for relative in _LISTENER_MODULES:
        path = root / relative
        if not path.is_file():
            raise FileNotFoundError(
                f"the Global Event listener needs {relative}, which is not present "
                f"under {root}"
            )
        text = path.read_text(encoding="utf-8")
        imports = "\n".join(
            line for line in text.splitlines() if line.strip().startswith(("import ", "from "))
        )
        for forbidden in _FORBIDDEN_IMPORTS:
            if forbidden in imports:
                raise ValueError(
                    f"{relative} imports {forbidden}, which is not part of the browser "
                    "runtime; the Global Event listener must stay standard-library only"
                )
        sources[relative] = text
    return sources


def listener_module_names() -> List[str]:
    return list(_LISTENER_MODULES)


def global_event_listener_source(root: str = _PYODIDE_ROOT) -> str:
    """A self-contained Python script that installs and exposes the listener.

    Run once per page in Pyodide. It materializes the modules onto the
    in-browser filesystem, puts their root on `sys.path` and imports the
    listener, leaving `ontobdc_global_event_listener` in the interpreter's
    globals for the bridge to call.

    `root` is where the tree lands. A Page always takes the default; a test
    host that is not Pyodide passes its own directory. It is a parameter and
    not something a caller edits out of the returned text: a substitution
    that silently misses — a quoting style away — installs the bundle
    somewhere else entirely and leaves the import to be satisfied by
    whatever happens to be on the machine, which is the opposite of what
    running the shipped bundle is supposed to prove.
    """
    encoded = json.dumps(listener_module_sources(), ensure_ascii=False)
    return f'''# OntoBDC Global Event listener installer (generated, do not edit by hand).
import json as _json
import os as _os
import sys as _sys

_ONTOBDC_EVENT_ROOT = {root!r}
_ONTOBDC_EVENT_SOURCES = _json.loads(r"""{encoded}""")

for _relative, _source in _ONTOBDC_EVENT_SOURCES.items():
    _target = _os.path.join(_ONTOBDC_EVENT_ROOT, *_relative.split("/"))
    _os.makedirs(_os.path.dirname(_target), exist_ok=True)
    with open(_target, "w", encoding="utf-8") as _handle:
        _handle.write(_source)

if _ONTOBDC_EVENT_ROOT not in _sys.path:
    _sys.path.insert(0, _ONTOBDC_EVENT_ROOT)

import importlib as _importlib

_importlib.invalidate_caches()
ontobdc_global_event_listener = _importlib.import_module(
    "ontobdc_view.surface.adapter.global_event_listener"
)
'''
