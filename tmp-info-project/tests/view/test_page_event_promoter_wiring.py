"""Standalone Pages load the generated Component Event promoter.

The event-generator capabilities write component_event_promoter.js beside
the other Page runtime assets. These tests pin the final HTML wiring and its
load order, rather than testing the bridge only after manually importing it.
"""

from pathlib import Path

from jinja2 import Template

from ontobdc_view.page.adapter.entity_view import (
    _GANTT_SCRIPT_NAMES,
    _WORKSTREAM_SCRIPT_NAMES,
)
from ontobdc_view.page.adapter.gantt_script import GanttScriptAdapter
from ontobdc_view.page.adapter.work_stream import WorkStreamScriptAdapter


ASSETS = Path(__file__).resolve().parents[1] / "src/ontobdc_view/page/asset"
PAGE_EVENT_DISPLAY = (ASSETS / "page_event_display.js").read_text(encoding="utf-8")


def test_workstream_page_loads_the_promoter_after_its_pyodide_runtime() -> None:
    html = Template(
        (ASSETS / "work_stream_view.html.j2").read_text(encoding="utf-8")
    ).render(
        has_workstream_payload=True,
        workstream_script_names=_WORKSTREAM_SCRIPT_NAMES,
        page_event_display_js=PAGE_EVENT_DISPLAY,
    )

    pyodide = "../../asset/work_stream_view/pyodide_runtime.js"
    promoter = "../../asset/work_stream_view/component_event_promoter.js"
    next_runtime = "../../asset/work_stream_view/linkset_operations.js"

    assert f'<script defer src="{promoter}"></script>' in html
    assert "data-ontobdc-page-event-bar" in html
    assert 'event: "EntityPageLoaded"' in html
    assert html.index(pyodide) < html.index(promoter) < html.index(next_runtime)


def test_gantt_page_loads_the_promoter_after_its_pyodide_runtime() -> None:
    html = Template(
        (ASSETS / "ifc_work_schedule_view.html.j2").read_text(encoding="utf-8")
    ).render(
        has_gantt_payload=True,
        gantt_script_names=_GANTT_SCRIPT_NAMES,
        page_event_display_js=PAGE_EVENT_DISPLAY,
    )

    pyodide = html.index('"pyodide_runtime"')
    promoter = html.index('"component_event_promoter"')
    next_runtime = html.index('"task_table_timeline"')

    assert pyodide < promoter < next_runtime
    assert "data-ontobdc-page-event-bar" in html
    assert 'event: "EntityPageLoaded"' in html


def test_page_loaded_waits_for_the_promoter_listener() -> None:
    assert '"ontobdc:component-event-promoter-ready"' in PAGE_EVENT_DISPLAY
    assert "window.OntoBDCComponentEventPromoter" in PAGE_EVENT_DISPLAY


def test_workstream_pyodide_attempts_the_cdn_from_file_protocol() -> None:
    runtime = WorkStreamScriptAdapter().script_source("pyodide_runtime")

    assert "await loadScriptTag(PYODIDE_CDN_URL)" in runtime
    assert "Pyodide unavailable on file:// protocol" not in runtime
    assert "if (isFileProtocol)" not in runtime


def test_gantt_pyodide_uses_the_cdn_from_file_protocol() -> None:
    runtime = GanttScriptAdapter().script_source("pyodide_runtime")

    assert 'location.protocol === "file:"' in runtime
    assert "return { scriptUrl: fallbackCdn, indexUrl: fallbackIndex };" in runtime
    assert "await loadScriptTag(PYODIDE_CDN_URL)" in runtime
    assert "Pyodide unavailable on file:// protocol" not in runtime
    assert "if (isFileProtocol)" not in runtime
