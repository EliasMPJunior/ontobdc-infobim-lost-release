from __future__ import annotations

from pathlib import Path
from typing import Any, Callable, Dict, List

import pytest

from ontobdc_view.surface.adapter.document import MATCHES_ID, SurfaceDocumentAdapter
from ontobdc_view.surface.domain.machine.standard_surface_html.state import SurfaceGenerationProcessState
from ontobdc_view.surface.plugin.capability.transformation.surface_assembled import (
    SurfaceAssembledCapability,
)

from conftest import FakeCliContext, build_surface_document

_MATCH: List[Dict[str, Any]] = [
    {
        "tile": "onto-data-container-tile",
        "region": "content",
        "data": "urn:test:container:1",
        "minColumns": 1,
        "preferredColumns": 4,
        "maxColumns": 6,
        "minRows": 2,
        "preferredRows": 2,
        "maxRows": 2,
    }
]


def _matched_context(
    tmp_path: Path,
    fake_context: Callable[..., FakeCliContext],
    *,
    matches: Any = None,
) -> FakeCliContext:
    context = fake_context(container_path=str(tmp_path))
    document = build_surface_document(
        through_state="surface_matched",
        matches=matches if matches is not None else _MATCH,
    )
    (tmp_path / "index.html").write_text(document, encoding="utf-8")
    return context


class TestExecute:
    def test_assembles_matched_tiles_into_the_surface_markup(
        self, tmp_path: Path, fake_context: Callable[..., FakeCliContext]
    ) -> None:
        context = _matched_context(tmp_path, fake_context)

        result = SurfaceAssembledCapability().execute(context)

        assert result["resulting_state"] is SurfaceGenerationProcessState.SURFACE_ASSEMBLED
        assert result["tile_count"] == 1
        document = Path(result["surface_path"]).read_text(encoding="utf-8")
        assert 'data-ontobdc-assembled="true"' in document
        assert (
            '<onto-data-container-tile surface-region="content" min-columns="1" '
            'columns="4" max-columns="6" min-rows="2" rows="2" max-rows="2" '
            'data-ontobdc-resource="urn:test:container:1">'
            in document
        )
        assert SurfaceDocumentAdapter.get_state_marker(document) == "surface_assembled"

    def test_produces_zero_tiles_for_an_empty_matches_list(
        self, tmp_path: Path, fake_context: Callable[..., FakeCliContext]
    ) -> None:
        context = _matched_context(tmp_path, fake_context, matches=[])
        result = SurfaceAssembledCapability().execute(context)
        assert result["tile_count"] == 0
        document = Path(result["surface_path"]).read_text(encoding="utf-8")
        assert 'data-ontobdc-assembled="true"' in document

    def test_raises_when_the_matches_script_is_not_a_list(
        self, tmp_path: Path, fake_context: Callable[..., FakeCliContext]
    ) -> None:
        context = fake_context(container_path=str(tmp_path))
        document = build_surface_document(through_state="surface_matched")
        document = SurfaceDocumentAdapter.upsert_json_script(document, MATCHES_ID, {"not": "a list"})
        (tmp_path / "index.html").write_text(document, encoding="utf-8")

        with pytest.raises(ValueError, match="Surface matches are missing or invalid"):
            SurfaceAssembledCapability().execute(context)


class TestCheck:
    def test_is_true_after_a_real_execute(
        self, tmp_path: Path, fake_context: Callable[..., FakeCliContext]
    ) -> None:
        context = _matched_context(tmp_path, fake_context)
        capability = SurfaceAssembledCapability()
        capability.execute(context)
        assert capability.check(context) is True

    def test_is_false_before_assembly_runs(
        self, tmp_path: Path, fake_context: Callable[..., FakeCliContext]
    ) -> None:
        context = _matched_context(tmp_path, fake_context)
        assert SurfaceAssembledCapability().check(context) is False

    def test_is_satisfied_matches_check(
        self, tmp_path: Path, fake_context: Callable[..., FakeCliContext]
    ) -> None:
        context = _matched_context(tmp_path, fake_context)
        capability = SurfaceAssembledCapability()
        assert capability.is_satisfied(context) == capability.check(context)


class TestLabelDescriptionAndMetadata:
    @pytest.mark.parametrize(
        ("lang", "expected_label"),
        [("en", "Surface Assembled"), ("pt-br", "Surface Montada")],
    )
    def test_label_delegates_to_process_state(self, lang: str, expected_label: str) -> None:
        assert SurfaceAssembledCapability().label(lang) == expected_label

    @pytest.mark.parametrize("lang", ["en", "pt-br"])
    def test_description_delegates_to_process_state(self, lang: str) -> None:
        capability = SurfaceAssembledCapability()
        assert capability.description(lang) == (
            SurfaceGenerationProcessState.SURFACE_ASSEMBLED.description(lang)
        )

    def test_metadata_id_matches_expected_capability_registry_id(self) -> None:
        assert SurfaceAssembledCapability.METADATA.id == (
            "org.ontobdc.view.plugin.capability.transformation.target.surface_assembled"
        )
