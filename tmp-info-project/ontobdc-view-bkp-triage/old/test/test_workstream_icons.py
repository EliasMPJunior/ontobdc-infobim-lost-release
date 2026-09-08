from pathlib import Path

from ontobdc_view.page.adapter.work_stream import WorkStreamScriptAdapter


ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "src" / "ontobdc_view" / "page" / "asset"


def test_workstream_refresh_uses_the_shared_icon_button_language() -> None:
    template = (ASSETS / "work_stream_view.html.j2").read_text(encoding="utf-8")
    refresh_source = WorkStreamScriptAdapter().script_source("pyodide_runtime")

    assert 'class="icon-btn refresh-btn"' in template
    assert '<polyline points="23 4 23 10 17 10"/>' in template
    assert 'data-i18n="refreshFromWorkbook"' not in template
    assert "refreshBtn.textContent" not in refresh_source
    assert 'refreshBtn.title = t("refreshingFromWorkbook")' in refresh_source


def test_workstream_resource_tree_uses_themeable_svg_icons() -> None:
    source = WorkStreamScriptAdapter().script_source("dimension_card")
    css = (ASSETS / "work_stream_view.css").read_text(encoding="utf-8")

    assert "RESOURCE_NODE_ICONS" in source
    assert 'stroke="currentColor"' in source
    assert 'icon.setAttribute("aria-hidden", "true")' in source
    assert "\\u{1F4C1}" not in source
    assert "\\u{1F4C2}" not in source
    assert "\\u{1F4C4}" not in source
    assert ".resource-node-icon svg" in css
    assert "var(--onto-theme-accent" in css
