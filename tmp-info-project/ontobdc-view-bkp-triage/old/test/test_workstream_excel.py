"""The WorkStream page exposes its connected workbook through Excel."""

from pathlib import Path

from ontobdc_view.page.adapter.container import (
    WORK_STREAM_RUNTIME,
    chrome_controls_source,
    container_connection_source,
)
from ontobdc_view.page.adapter.work_stream import WorkStreamScriptAdapter


ROOT = Path(__file__).resolve().parents[1]
TEMPLATE = (
    ROOT / "src/ontobdc_view/page/asset/work_stream_view.html.j2"
).read_text(encoding="utf-8")
LOCALE_ROOT = ROOT / "src/ontobdc_view/component/adapter/i18n/locale"


def test_workstream_header_exposes_disabled_excel_action() -> None:
    assert 'class="icon-btn workstream-open-workbook-btn"' in TEMPLATE
    button = TEMPLATE.split(
        'class="icon-btn workstream-open-workbook-btn"', 1
    )[1].split(">", 1)[0]
    assert "disabled" in button
    assert 'data-i18n-title="openWorkbookTitle"' in button
    assert 'data-i18n-aria-label="openWorkbook"' in button
    assert 'fill="#1D6F42"' in TEMPLATE


def test_workstream_enables_excel_only_after_resolving_relative_workbook() -> None:
    source = WorkStreamScriptAdapter().script_source("pyodide_runtime")
    assert '"workbookRelativePath": workbook_relative_path' in source
    assert (
        'runtime.state.workbookRelPath = result.workbookRelativePath || "";'
        in source
    )
    assert 'openWorkbookBtn.disabled = !runtime.state.workbookRelPath;' in source


def test_shared_excel_action_includes_nested_dataset_path() -> None:
    controls = chrome_controls_source(WORK_STREAM_RUNTIME)
    # One shared handler for both Pages, prepending the dataset folder (from
    # the payload) to the dataset-relative workbook path.
    assert '".gantt-open-workbook-btn, .workstream-open-workbook-btn"' in controls
    assert "payload.datasetFolder" in controls
    assert 'var relPath = [datasetFolder, workbookRelPath].filter(Boolean).join("/");' in controls
    assert 'opener.href = "ms-excel:ofe|u|" + fileUrl;' in controls


def test_workstream_excel_strings_exist_in_every_supported_locale() -> None:
    for locale in ("en", "pt-BR", "pt-PT", "es"):
        content = (LOCALE_ROOT / f"{locale}.yaml").read_text(encoding="utf-8")
        workstream = content.split("work_stream_view:", 1)[1].split(
            "ifc_work_schedule_view:", 1
        )[0]
        assert "openWorkbook:" in workstream, locale
        assert "openWorkbookTitle:" in workstream, locale
