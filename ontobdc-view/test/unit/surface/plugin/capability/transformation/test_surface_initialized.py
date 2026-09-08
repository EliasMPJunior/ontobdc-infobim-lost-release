from __future__ import annotations

from pathlib import Path
from typing import Any, Callable, Dict

import pytest

from ontobdc_view.surface.adapter.document import SurfaceDocumentAdapter
from ontobdc_view.surface.domain.machine.standard_surface_html.state import SurfaceGenerationProcessState
from ontobdc_view.surface.plugin.capability.transformation.surface_initialized import (
    SurfaceInitializedCapability,
)

from conftest import FakeCliContext


class TestExecute:
    def test_creates_a_minimal_valid_document_at_the_container_index_html(
        self, tmp_path: Path, fake_context: Callable[..., FakeCliContext]
    ) -> None:
        context = fake_context(container_path=str(tmp_path))
        capability = SurfaceInitializedCapability()

        result: Dict[str, Any] = capability.execute(context)

        assert result["resulting_state"] is SurfaceGenerationProcessState.SURFACE_INITIALIZED
        surface_path = Path(result["surface_path"])
        assert surface_path == tmp_path / "index.html"
        assert surface_path.is_file()

        document = surface_path.read_text(encoding="utf-8")
        assert "<!doctype html" in document.lower()
        assert "<onto-presentation-surface" in document
        assert SurfaceDocumentAdapter.get_state_marker(document) == "surface_initialized"

    def test_uses_the_requested_language_as_the_html_lang_attribute(
        self, tmp_path: Path, fake_context: Callable[..., FakeCliContext]
    ) -> None:
        context = fake_context(container_path=str(tmp_path), language="pt-BR")
        SurfaceInitializedCapability().execute(context)
        document = (tmp_path / "index.html").read_text(encoding="utf-8")
        assert '<html lang="pt-BR">' in document

    def test_defaults_to_english_when_no_language_is_requested(
        self, tmp_path: Path, fake_context: Callable[..., FakeCliContext]
    ) -> None:
        context = fake_context(container_path=str(tmp_path))
        SurfaceInitializedCapability().execute(context)
        document = (tmp_path / "index.html").read_text(encoding="utf-8")
        assert '<html lang="en">' in document

    def test_records_the_resolved_surface_path_back_on_the_context(
        self, tmp_path: Path, fake_context: Callable[..., FakeCliContext]
    ) -> None:
        context = fake_context(container_path=str(tmp_path))
        SurfaceInitializedCapability().execute(context)
        assert context.get_parameter_value("surface_path") == str(tmp_path / "index.html")


class TestCheck:
    def test_is_true_after_a_real_execute(
        self, tmp_path: Path, fake_context: Callable[..., FakeCliContext]
    ) -> None:
        context = fake_context(container_path=str(tmp_path))
        capability = SurfaceInitializedCapability()
        capability.execute(context)
        assert capability.check(context) is True

    def test_is_true_for_a_minimal_document_even_without_the_state_marker(
        self, tmp_path: Path, fake_context: Callable[..., FakeCliContext]
    ) -> None:
        # The check is purely structural (doctype + html/head/body + the
        # Surface host element) -- it does not require the marker itself.
        document = SurfaceDocumentAdapter.make_initial_html("en")
        (tmp_path / "index.html").write_text(document, encoding="utf-8")
        context = fake_context(container_path=str(tmp_path))
        assert SurfaceInitializedCapability().check(context) is True

    def test_is_false_when_no_surface_exists_yet(
        self, tmp_path: Path, fake_context: Callable[..., FakeCliContext]
    ) -> None:
        context = fake_context(container_path=str(tmp_path))
        assert SurfaceInitializedCapability().check(context) is False

    def test_is_false_for_html_missing_the_surface_host_element(
        self, tmp_path: Path, fake_context: Callable[..., FakeCliContext]
    ) -> None:
        (tmp_path / "index.html").write_text(
            "<!doctype html><html lang=\"en\"><head></head><body></body></html>",
            encoding="utf-8",
        )
        context = fake_context(container_path=str(tmp_path))
        assert SurfaceInitializedCapability().check(context) is False

    def test_is_satisfied_matches_check(
        self, tmp_path: Path, fake_context: Callable[..., FakeCliContext]
    ) -> None:
        context = fake_context(container_path=str(tmp_path))
        capability = SurfaceInitializedCapability()
        assert capability.is_satisfied(context) == capability.check(context)


class TestLabelDescriptionAndMetadata:
    @pytest.mark.parametrize(
        ("lang", "expected_label"),
        [("en", "Surface Initialized"), ("pt-br", "Surface Inicializada")],
    )
    def test_label_delegates_to_process_state(self, lang: str, expected_label: str) -> None:
        assert SurfaceInitializedCapability().label(lang) == expected_label

    @pytest.mark.parametrize("lang", ["en", "pt-br"])
    def test_description_delegates_to_process_state(self, lang: str) -> None:
        capability = SurfaceInitializedCapability()
        assert capability.description(lang) == (
            SurfaceGenerationProcessState.SURFACE_INITIALIZED.description(lang)
        )

    def test_metadata_id_matches_expected_capability_registry_id(self) -> None:
        assert SurfaceInitializedCapability.METADATA.id == (
            "org.ontobdc.view.plugin.capability.transformation.target.surface_initialized"
        )
