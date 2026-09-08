from __future__ import annotations

from pathlib import Path
from typing import Any, Callable, List, Optional

import pytest

from ontobdc_view.surface.adapter.document import SurfaceDocumentAdapter
from ontobdc_view.surface.domain.machine.standard_surface_html.state import SurfaceGenerationProcessState
from ontobdc_view.surface.plugin.capability.transformation.surface_validated import (
    SurfaceValidatedCapability,
)

from conftest import FakeCliContext, build_surface_document

# is_packaged_surface() == is_assembled_surface() and has_packaged_runtime():
# the latter requires a component script tagged with the
# data-ontobdc-surface-component attribute whose text contains this exact
# promoter-registration line, and no external (https://) script/style
# reference anywhere in the document.
_PROMOTER_MARKER = "window.OntoBDCComponentEventPromoter = promoter;"


def _packaged_document(matches: Optional[List[Any]] = None) -> str:
    document = build_surface_document(through_state="surface_assembled", matches=matches)
    return SurfaceDocumentAdapter.embed_component_scripts(
        document, [f"const promoter = {{}};\n{_PROMOTER_MARKER}"]
    )


def _context_with(
    tmp_path: Path, fake_context: Callable[..., FakeCliContext], document: str
) -> FakeCliContext:
    context = fake_context(container_path=str(tmp_path))
    (tmp_path / "index.html").write_text(document, encoding="utf-8")
    return context


class TestExecute:
    def test_marks_the_document_validated_when_the_package_is_structurally_valid(
        self, tmp_path: Path, fake_context: Callable[..., FakeCliContext]
    ) -> None:
        context = _context_with(tmp_path, fake_context, _packaged_document())

        result = SurfaceValidatedCapability().execute(context)

        assert result["resulting_state"] is SurfaceGenerationProcessState.SURFACE_VALIDATED
        document = Path(result["surface_path"]).read_text(encoding="utf-8")
        assert SurfaceDocumentAdapter.get_state_marker(document) == "surface_validated"

    def test_raises_when_the_component_promoter_runtime_is_missing(
        self, tmp_path: Path, fake_context: Callable[..., FakeCliContext]
    ) -> None:
        # Assembled, but never packaged with embed_component_scripts().
        context = _context_with(
            tmp_path, fake_context, build_surface_document(through_state="surface_assembled")
        )

        with pytest.raises(ValueError, match="Surface package failed validation"):
            SurfaceValidatedCapability().execute(context)

    def test_raises_when_the_document_references_an_external_runtime(
        self, tmp_path: Path, fake_context: Callable[..., FakeCliContext]
    ) -> None:
        document = _packaged_document().replace(
            "</head>",
            '<link rel="stylesheet" href="https://cdn.example.com/style.css"></head>',
        )
        context = _context_with(tmp_path, fake_context, document)

        with pytest.raises(ValueError, match="Surface package failed validation"):
            SurfaceValidatedCapability().execute(context)


class TestCheck:
    def test_is_true_after_a_real_execute(
        self, tmp_path: Path, fake_context: Callable[..., FakeCliContext]
    ) -> None:
        context = _context_with(tmp_path, fake_context, _packaged_document())
        capability = SurfaceValidatedCapability()
        capability.execute(context)
        assert capability.check(context) is True

    def test_is_false_before_the_document_is_packaged(
        self, tmp_path: Path, fake_context: Callable[..., FakeCliContext]
    ) -> None:
        context = _context_with(
            tmp_path, fake_context, build_surface_document(through_state="surface_assembled")
        )
        assert SurfaceValidatedCapability().check(context) is False

    def test_is_satisfied_matches_check(
        self, tmp_path: Path, fake_context: Callable[..., FakeCliContext]
    ) -> None:
        context = _context_with(tmp_path, fake_context, _packaged_document())
        capability = SurfaceValidatedCapability()
        assert capability.is_satisfied(context) == capability.check(context)


class TestLabelDescriptionAndMetadata:
    @pytest.mark.parametrize(
        ("lang", "expected_label"),
        [("en", "Surface Validated"), ("pt-br", "Surface Validada")],
    )
    def test_label_delegates_to_process_state(self, lang: str, expected_label: str) -> None:
        assert SurfaceValidatedCapability().label(lang) == expected_label

    @pytest.mark.parametrize("lang", ["en", "pt-br"])
    def test_description_delegates_to_process_state(self, lang: str) -> None:
        capability = SurfaceValidatedCapability()
        assert capability.description(lang) == (
            SurfaceGenerationProcessState.SURFACE_VALIDATED.description(lang)
        )

    def test_metadata_id_matches_expected_capability_registry_id(self) -> None:
        assert SurfaceValidatedCapability.METADATA.id == (
            "org.ontobdc.view.plugin.capability.transformation.target.surface_validated"
        )
