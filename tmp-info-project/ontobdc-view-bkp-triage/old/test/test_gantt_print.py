"""The Gantt printer is visible, translated and wired to printable output."""

from pathlib import Path

from ontobdc_view.page.adapter.container import (
    IFC_WORK_SCHEDULE_RUNTIME,
    chrome_controls_source,
    connection_state_source,
)

ROOT = Path(__file__).resolve().parents[1]
TEMPLATE = (
    ROOT / "src/ontobdc_view/page/asset/ifc_work_schedule_view.html.j2"
).read_text(encoding="utf-8")
STYLESHEET = (
    ROOT / "src/ontobdc_view/page/asset/ifc_work_schedule_view.css"
).read_text(encoding="utf-8")
LOCALE_ROOT = ROOT / "src/ontobdc_view/component/adapter/i18n/locale"


def test_gantt_header_exposes_a_printer_action() -> None:
    assert 'class="icon-btn gantt-print-btn"' in TEMPLATE
    assert 'data-i18n-title="printGanttTitle"' in TEMPLATE
    assert 'data-i18n-aria-label="printGantt"' in TEMPLATE


def test_only_the_project_loader_is_enabled_before_connection() -> None:
    for class_name in (
        "refresh-btn",
        "workspace-btn",
        "gantt-filter-btn",
        "gantt-add-task-btn",
        "gantt-print-btn",
        "gantt-open-workbook-btn",
        "gantt-fullscreen-btn",
    ):
        button = TEMPLATE.split(f'class="icon-btn {class_name}"', 1)[1]
        assert "disabled" in button.split(">", 1)[0], class_name

    connect = TEMPLATE.split('class="connect-btn"', 1)[1].split(">", 1)[0]
    assert "disabled" not in connect


def test_validated_project_connection_enables_gantt_actions() -> None:
    source = connection_state_source(IFC_WORK_SCHEDULE_RUNTIME)
    assert 'querySelectorAll("button:not(.connect-btn)")' in source
    assert "setProjectActionsDisabled(false);" in source
    assert "setProjectActionsDisabled(true);" in source
    assert "new MutationObserver" in source
    assert "runtime.state.projectActionsDisabled" in source


def test_printer_action_uses_the_browser_pdf_pipeline() -> None:
    source = chrome_controls_source(IFC_WORK_SCHEDULE_RUNTIME)
    assert 'document.querySelector(".gantt-print-btn")' in source
    assert "window.print();" in source


def test_excel_action_prepends_the_dataset_folder_to_the_workbook_path() -> None:
    # The runtime resolves the workbook path relative to the dataset folder,
    # but the Page is served from the container root, so the dataset folder
    # (a direct child of the root, carried in the payload) must be prepended.
    source = chrome_controls_source(IFC_WORK_SCHEDULE_RUNTIME)
    assert "payload.datasetFolder" in source
    assert 'var relPath = [datasetFolder, workbookRelPath].filter(Boolean).join("/");' in source


def test_print_layout_is_a4_landscape_without_interactive_chrome() -> None:
    assert "@media print" in STYLESHEET
    assert "size: A4 landscape" in STYLESHEET
    print_rules = STYLESHEET.split("@media print", 1)[1]
    assert ".header-actions" in print_rules
    assert ".gantt-container" in print_rules
    assert "overflow: visible !important" in print_rules


def test_printer_strings_exist_in_every_supported_page_locale() -> None:
    for locale in ("en", "pt-BR", "pt-PT", "es"):
        content = (LOCALE_ROOT / f"{locale}.yaml").read_text(encoding="utf-8")
        assert "printGantt:" in content, locale
        assert "printGanttTitle:" in content, locale
