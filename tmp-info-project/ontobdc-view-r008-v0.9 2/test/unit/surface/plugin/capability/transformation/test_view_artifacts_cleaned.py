from __future__ import annotations

from pathlib import Path
from typing import Any, Dict
from unittest.mock import MagicMock

from ontobdc_view.surface.domain.machine.standard_surface_html.state import SurfaceGenerationProcessState
from ontobdc_view.surface.plugin.capability.transformation.view_artifacts_cleaned import (
    ViewArtifactsCleanedCapability,
)


def _fake_context(container_path: Path) -> MagicMock:
    context = MagicMock()
    context.get_parameter_value.return_value = str(container_path)
    return context


class TestCheck:
    def test_returns_true_for_a_container_with_no_generated_artifacts(
        self, tmp_path: Path
    ) -> None:
        capability = ViewArtifactsCleanedCapability()
        assert capability.check(_fake_context(tmp_path)) is True

    def test_returns_false_when_index_html_exists(self, tmp_path: Path) -> None:
        (tmp_path / "index.html").write_text("<html></html>", encoding="utf-8")
        capability = ViewArtifactsCleanedCapability()
        assert capability.check(_fake_context(tmp_path)) is False

    def test_returns_false_when_the_legacy_root_file_viewer_exists(
        self, tmp_path: Path
    ) -> None:
        (tmp_path / "onto-file-viewer.html").write_text("<html></html>", encoding="utf-8")
        capability = ViewArtifactsCleanedCapability()
        assert capability.check(_fake_context(tmp_path)) is False

    def test_returns_false_when_the_legacy_marker_file_viewer_exists(
        self, tmp_path: Path
    ) -> None:
        marker_dir = tmp_path / ".__ontobdc__"
        marker_dir.mkdir()
        (marker_dir / "onto-file-viewer.html").write_text("<html></html>", encoding="utf-8")
        capability = ViewArtifactsCleanedCapability()
        assert capability.check(_fake_context(tmp_path)) is False

    def test_returns_false_when_the_current_file_viewer_exists(
        self, tmp_path: Path
    ) -> None:
        view_dir = tmp_path / ".__ontobdc__" / "view"
        view_dir.mkdir(parents=True)
        (view_dir / "onto-file-viewer.html").write_text("<html></html>", encoding="utf-8")
        capability = ViewArtifactsCleanedCapability()
        assert capability.check(_fake_context(tmp_path)) is False

    def test_returns_false_when_a_published_entity_view_exists(self, tmp_path: Path) -> None:
        view_dir = tmp_path / ".__ontobdc__" / "view" / "work_stream"
        view_dir.mkdir(parents=True)
        (view_dir / "some-entity.html").write_text("<html></html>", encoding="utf-8")
        capability = ViewArtifactsCleanedCapability()
        assert capability.check(_fake_context(tmp_path)) is False

    def test_returns_false_when_generated_js_or_css_exists(
        self, tmp_path: Path
    ) -> None:
        view_dir = tmp_path / ".__ontobdc__" / "view" / "ifc_work_schedule"
        view_dir.mkdir(parents=True)
        (view_dir / "i18n_apply.js").write_text("// generated", encoding="utf-8")
        (view_dir / "page.css").write_text("/* generated */", encoding="utf-8")
        capability = ViewArtifactsCleanedCapability()
        assert capability.check(_fake_context(tmp_path)) is False

    def test_ignores_html_outside_the_view_directory(self, tmp_path: Path) -> None:
        # Other tools (e.g. an IFC work schedule regeneration worker) may
        # leave unrelated .html files elsewhere under .__ontobdc__ -- this
        # state must not treat those as its own artifacts.
        other_dir = tmp_path / ".__ontobdc__" / "asset" / "work_stream_view"
        other_dir.mkdir(parents=True)
        (other_dir / "unrelated.html").write_text("<html></html>", encoding="utf-8")
        capability = ViewArtifactsCleanedCapability()
        assert capability.check(_fake_context(tmp_path)) is True

    def test_returns_false_when_container_path_is_unresolved(self) -> None:
        context = MagicMock()
        context.get_parameter_value.return_value = None
        capability = ViewArtifactsCleanedCapability()
        assert capability.check(context) is False


class TestExecute:
    def test_removes_every_generated_artifact_and_reports_the_paths(
        self, tmp_path: Path
    ) -> None:
        (tmp_path / "index.html").write_text("<html></html>", encoding="utf-8")
        (tmp_path / "onto-file-viewer.html").write_text("<html></html>", encoding="utf-8")
        marker_dir = tmp_path / ".__ontobdc__"
        marker_dir.mkdir()
        (marker_dir / "onto-file-viewer.html").write_text("<html></html>", encoding="utf-8")
        view_dir = marker_dir / "view" / "work_stream"
        view_dir.mkdir(parents=True)
        entity_page = view_dir / "some-entity.html"
        entity_page.write_text("<html></html>", encoding="utf-8")
        file_viewer_page = marker_dir / "view" / "onto-file-viewer.html"
        file_viewer_page.write_text("<html></html>", encoding="utf-8")
        generated_js = view_dir / "i18n_apply.js"
        generated_js.write_text("// generated", encoding="utf-8")
        generated_css = view_dir / "page.css"
        generated_css.write_text("/* generated */", encoding="utf-8")
        legacy_asset_dir = marker_dir / "asset" / "work_stream_view"
        legacy_asset_dir.mkdir(parents=True)
        legacy_js = legacy_asset_dir / "runtime.js"
        legacy_js.write_text("// generated", encoding="utf-8")
        legacy_css = legacy_asset_dir / "runtime.css"
        legacy_css.write_text("/* generated */", encoding="utf-8")

        capability = ViewArtifactsCleanedCapability()
        result: Dict[str, Any] = capability.execute(_fake_context(tmp_path))

        assert result["resulting_state"] is SurfaceGenerationProcessState.VIEW_ARTIFACTS_CLEANED
        assert result["container_path"] == str(tmp_path.resolve())
        assert set(result["removed_paths"]) == {
            str(tmp_path / "index.html"),
            str(tmp_path / "onto-file-viewer.html"),
            str(marker_dir / "onto-file-viewer.html"),
            str(entity_page),
            str(file_viewer_page),
            str(generated_js),
            str(generated_css),
            str(legacy_js),
            str(legacy_css),
        }
        assert not (tmp_path / "index.html").exists()
        assert not (tmp_path / "onto-file-viewer.html").exists()
        assert not (marker_dir / "onto-file-viewer.html").exists()
        assert not entity_page.exists()
        assert not file_viewer_page.exists()
        assert not generated_js.exists()
        assert not generated_css.exists()
        assert not legacy_js.exists()
        assert not legacy_css.exists()

    def test_does_not_touch_html_outside_the_view_directory(self, tmp_path: Path) -> None:
        other_dir = tmp_path / ".__ontobdc__" / "asset" / "work_stream_view"
        other_dir.mkdir(parents=True)
        untouched = other_dir / "unrelated.html"
        untouched.write_text("<html></html>", encoding="utf-8")

        capability = ViewArtifactsCleanedCapability()
        result = capability.execute(_fake_context(tmp_path))

        assert result["removed_paths"] == []
        assert untouched.is_file()

    def test_does_not_touch_js_outside_a_legacy_view_asset_directory(
        self, tmp_path: Path
    ) -> None:
        other_dir = tmp_path / ".__ontobdc__" / "asset" / "other_tool"
        other_dir.mkdir(parents=True)
        untouched = other_dir / "runtime.js"
        untouched.write_text("// unrelated", encoding="utf-8")

        capability = ViewArtifactsCleanedCapability()
        result = capability.execute(_fake_context(tmp_path))

        assert result["removed_paths"] == []
        assert untouched.is_file()

    def test_is_a_no_op_when_nothing_needs_cleaning(self, tmp_path: Path) -> None:
        capability = ViewArtifactsCleanedCapability()
        result = capability.execute(_fake_context(tmp_path))
        assert result["removed_paths"] == []

    def test_check_is_true_after_execute(self, tmp_path: Path) -> None:
        (tmp_path / "index.html").write_text("<html></html>", encoding="utf-8")
        capability = ViewArtifactsCleanedCapability()
        context = _fake_context(tmp_path)
        capability.execute(context)
        assert capability.check(context) is True

    def test_is_satisfied_matches_check(self, tmp_path: Path) -> None:
        capability = ViewArtifactsCleanedCapability()
        context = _fake_context(tmp_path)
        assert capability.is_satisfied(context) == capability.check(context)
