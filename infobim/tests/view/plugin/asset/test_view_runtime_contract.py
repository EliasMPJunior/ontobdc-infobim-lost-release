from pathlib import Path


ROOT = Path(__file__).resolve().parents[4]


def test_view_reuses_generic_runtime_without_subject_ui() -> None:
    view_root = ROOT / "src" / "infobim" / "view"
    sources = "\n".join(
        path.read_text(encoding="utf-8")
        for path in view_root.rglob("*")
        if path.suffix in {".py", ".js"}
    )

    assert "from ontobdc.view" in sources
    assert "ComponentLoader" in sources
    assert "Subject" not in sources
    assert '"subjects"' not in sources
    assert "subjectWorkspace" not in sources
    assert "annotation_workspace.js" not in sources


def test_command_contains_no_html_renderer() -> None:
    source = (
        ROOT / "src/infobim/view/plugin/command/project.py"
    ).read_text(encoding="utf-8")

    assert "<html" not in source.lower()
    assert "InfoBIMSurfaceGenerationStateTransitionHandler" in source


def test_ifc_project_tile_exposes_project_information_fields() -> None:
    source = (
        ROOT
        / "src/infobim/view/plugin/asset/js/onto-infobim-project-tile.js"
    ).read_text(encoding="utf-8")

    assert "GlobalId" in source
    assert "Geolocalização" in source
    assert "Path" in source
    assert "Arquivos indexados" in source
    assert "description_IfcRoot" in source
    assert "navigator.geolocation" in source
