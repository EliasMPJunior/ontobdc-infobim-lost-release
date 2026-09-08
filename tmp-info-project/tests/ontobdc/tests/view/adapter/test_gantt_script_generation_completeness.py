"""The Gantt Page's runtime must actually reach the container.

A state existed in `GanttScriptGenerationProcessState`, had a capability and
had a check, but was missing from `_CAPABILITY_ID_BY_STATE` and from the
statechart. Because the evaluator resolves every state's capability before
evaluating any of them, that one absent entry did not skip one file -- it
raised, the whole runtime went ungenerated, and the error was swallowed into
a return value nobody read. The Page shipped with nine dead `<script src>`
tags and an empty chart.

These tests pin the three independent ways that could happen again: a state
with no mapped capability, a state missing from the statechart, and a
published page whose runtime failed without the build saying so.
"""
from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any, Dict, List, Set

import pytest

from ontobdc.view.adapter import gantt_script_machine
from ontobdc.view.adapter.gantt_script_machine import (
    _CAPABILITY_ID_BY_STATE,
    _capability_type_for_state,
)
from ontobdc.view.adapter.surface.document import (
    JSONLD_ID,
    make_initial_html,
    set_state_marker,
    upsert_json_script,
)
from ontobdc.view.domain.machine.gantt_script_state import (
    GanttScriptGenerationProcessState,
)
from ontobdc.view.plugin.capability.transformation.entity_views_published import (
    EntityViewsPublishedCapability,
)

DCTERMS: str = "http://purl.org/dc/terms/"
INFOBIM: str = "https://infobim.org/ontology/ns#"

STATECHART_PATH: Path = (
    Path(gantt_script_machine.__file__).resolve().parents[1]
    / "domain/machine/standard_gantt_script_generation.yaml"
)

# What the published HTML actually asks the browser to load. Kept here as a
# literal on purpose: if the Page's own list changes, this test should fail
# and make someone confirm the generation side changed with it.
REQUIRED_RUNTIME_FILES: List[str] = [
    "xlsx-0.18.5.full.min.js",
    "i18n_apply.js",
    "graph_reader.js",
    "container_connection.js",
    "connection_state.js",
    "chrome_controls.js",
    "pyodide_runtime.js",
    "task_table_timeline.js",
    "dependency_arrows.js",
]


class StubContext:
    def __init__(self, **parameters: Any) -> None:
        self._parameters: Dict[str, Any] = dict(parameters)

    def get_parameter_value(self, name: str) -> Any:
        return self._parameters.get(name)

    def set_parameter_value(self, name: str, value: Any) -> None:
        self._parameters[name] = value

    def has_parameter(self, name: str) -> bool:
        return name in self._parameters


def build_container(root: Path) -> Path:
    """A clean container holding one IfcWorkSchedule and nothing generated."""
    surface_path: Path = root / "index.html"
    graph = [{
        "@id": "urn:ontobdc:storage/dataset/sched/OBRA",
        "@type": [f"{INFOBIM}IfcWorkSchedule"],
        f"{DCTERMS}identifier": [{"@value": "OBRA"}],
        f"{DCTERMS}title": [{"@value": "Obra"}],
        f"{DCTERMS}conformsTo": [{"@id": f"{INFOBIM}DefaultIfcWorkScheduleFacade"}],
    }]
    document: str = set_state_marker(
        make_initial_html("pt-BR"), "surface_validated"
    )
    surface_path.write_text(
        upsert_json_script(document, JSONLD_ID, graph, "application/ld+json"),
        encoding="utf-8",
    )
    return surface_path


@pytest.fixture
def clean_container(tmp_path: Path) -> Path:
    return build_container(tmp_path)


# ------------------------------------------------- the mapping and the chart

def test_every_state_has_a_mapped_capability() -> None:
    """UNDEFINED aside, a state with no entry here breaks every state."""
    unmapped: List[str] = [
        state.name
        for state in GanttScriptGenerationProcessState
        if state is not GanttScriptGenerationProcessState.UNDEFINED
        and state not in _CAPABILITY_ID_BY_STATE
    ]
    assert not unmapped, unmapped


def test_every_mapped_capability_actually_resolves() -> None:
    """A mapped id that no loader can find fails exactly like a missing one."""
    for state in GanttScriptGenerationProcessState:
        if state is GanttScriptGenerationProcessState.UNDEFINED:
            continue
        assert _capability_type_for_state(state) is not None, state.name


def test_every_state_appears_in_the_statechart() -> None:
    """The chart is the other half: a mapped state the chart skips is never
    reached, which is silent in a different way."""
    chart: str = STATECHART_PATH.read_text(encoding="utf-8")
    declared: Set[str] = set(re.findall(r"^\s+- name: (\S+)", chart, re.MULTILINE))

    missing: List[str] = [
        state.name
        for state in GanttScriptGenerationProcessState
        if state.value.strip("_") not in declared
    ]
    assert not missing, missing


def test_the_statechart_reaches_every_state_from_undefined() -> None:
    """Declared but untargeted is the same as absent."""
    chart: str = STATECHART_PATH.read_text(encoding="utf-8")
    targeted: Set[str] = set(re.findall(r"- target: (\S+)", chart))

    unreachable: List[str] = [
        state.name
        for state in GanttScriptGenerationProcessState
        if state is not GanttScriptGenerationProcessState.UNDEFINED
        and state.value.strip("_") not in targeted
    ]
    assert not unreachable, unreachable


# --------------------------------------------------- generation end to end

def test_a_clean_container_gets_every_file_the_page_loads(
    clean_container: Path,
) -> None:
    result: Dict[str, Any] = EntityViewsPublishedCapability().execute(
        StubContext(surface_path=str(clean_container), language="pt-BR")
    )

    assert result["published_view_count"] == 1
    assert result["gantt_scripts_error"] == ""

    asset_dir: Path = (
        clean_container.parent
        / ".__ontobdc__" / "asset" / "ifc_work_schedule_view"
    )
    assert asset_dir.is_dir(), "the runtime directory was never created"

    written: Set[str] = {path.name for path in asset_dir.glob("*.js")}
    missing: List[str] = [
        name for name in REQUIRED_RUNTIME_FILES if name not in written
    ]
    assert not missing, missing

    empty: List[str] = [
        path.name for path in asset_dir.glob("*.js") if path.stat().st_size == 0
    ]
    assert not empty, empty


def test_the_vendored_library_is_the_real_build(clean_container: Path) -> None:
    """Materialized, not stubbed: an empty placeholder passes a file-exists
    check and fails in the browser."""
    EntityViewsPublishedCapability().execute(
        StubContext(surface_path=str(clean_container), language="pt-BR")
    )

    vendored: Path = (
        clean_container.parent
        / ".__ontobdc__" / "asset" / "ifc_work_schedule_view"
        / "xlsx-0.18.5.full.min.js"
    )
    assert vendored.stat().st_size > 100_000
    source: str = vendored.read_text(encoding="utf-8")
    assert "SheetJS" in source[:200]
    assert "XLSX" in source


def test_the_page_and_the_generated_files_agree(clean_container: Path) -> None:
    """The regression was a Page naming files nothing produced. Compare the
    published HTML's own script tags against what landed on disk."""
    EntityViewsPublishedCapability().execute(
        StubContext(surface_path=str(clean_container), language="pt-BR")
    )

    page: Path = next(
        (clean_container.parent / ".__ontobdc__" / "view").rglob("*.html")
    )
    # The Page no longer carries literal `<script src>` tags: its loader
    # resolves the asset folder at runtime and builds the URLs from a
    # `SCRIPT_NAMES` array. That array is what the browser actually fetches,
    # so it is what the generated files have to match.
    declared = re.search(
        r"var SCRIPT_NAMES = (\[[^\]]*\])", page.read_text(encoding="utf-8")
    )
    assert declared, "the Page declares no runtime script list at all"
    requested: List[str] = [
        f"{name}.js" for name in json.loads(declared.group(1))
    ]

    asset_dir: Path = (
        clean_container.parent
        / ".__ontobdc__" / "asset" / "ifc_work_schedule_view"
    )
    dead: List[str] = [
        name for name in requested if not (asset_dir / name).is_file()
    ]
    assert not dead, dead


# ------------------------------------------------------- loud, not silent

def test_a_missing_runtime_fails_the_build(
    clean_container: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Publishing a Page whose runtime never generated is not a partial
    success -- it is an HTML file that opens to dead script tags."""
    broken: Dict[Any, str] = dict(_CAPABILITY_ID_BY_STATE)
    broken.pop(GanttScriptGenerationProcessState.CHROME_CONTROLS_SCRIPT_GENERATED)
    monkeypatch.setattr(
        gantt_script_machine, "_CAPABILITY_ID_BY_STATE", broken
    )

    with pytest.raises(RuntimeError, match="mandatory runtime scripts"):
        EntityViewsPublishedCapability().execute(
            StubContext(surface_path=str(clean_container), language="pt-BR")
        )


def test_a_failed_build_does_not_mark_the_surface_done(
    clean_container: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Otherwise a re-run treats the step as finished and never retries it."""
    broken: Dict[Any, str] = dict(_CAPABILITY_ID_BY_STATE)
    broken.pop(GanttScriptGenerationProcessState.CHROME_CONTROLS_SCRIPT_GENERATED)
    monkeypatch.setattr(
        gantt_script_machine, "_CAPABILITY_ID_BY_STATE", broken
    )

    with pytest.raises(RuntimeError):
        EntityViewsPublishedCapability().execute(
            StubContext(surface_path=str(clean_container), language="pt-BR")
        )

    assert "entity_views_published" not in clean_container.read_text(
        encoding="utf-8"
    )
