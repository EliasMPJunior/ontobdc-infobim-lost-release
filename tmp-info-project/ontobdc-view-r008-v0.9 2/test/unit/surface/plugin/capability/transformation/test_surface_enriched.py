from __future__ import annotations

import json
from pathlib import Path
from typing import Callable

import pytest

from ontobdc_view.surface.adapter.document import JSONLD_ID, SurfaceDocumentAdapter
from ontobdc_view.surface.domain.machine.standard_surface_html.state import SurfaceGenerationProcessState
from ontobdc_view.surface.plugin.capability.transformation.data_gathered import (
    DataGatheredCapability,
)
from ontobdc_view.surface.plugin.capability.transformation.surface_enriched import (
    SurfaceEnrichedCapability,
)

from conftest import FakeCliContext

_GATHERED_GRAPH = [{"@id": "urn:x:1", "@type": ["urn:test:Thing"]}]


def _initialized_context(tmp_path: Path, fake_context: Callable[..., FakeCliContext]) -> FakeCliContext:
    context = fake_context(container_path=str(tmp_path))
    document = SurfaceDocumentAdapter.set_state_marker(
        SurfaceDocumentAdapter.make_initial_html("en"), "surface_initialized"
    )
    (tmp_path / "index.html").write_text(document, encoding="utf-8")
    return context


def _write_gathered_artifact(
    tmp_path: Path, context: FakeCliContext, payload: object = _GATHERED_GRAPH
) -> Path:
    state_path = DataGatheredCapability.state_path(context)
    state_path.parent.mkdir(parents=True, exist_ok=True)
    state_path.write_text(json.dumps(payload), encoding="utf-8")
    return state_path


class TestExecute:
    def test_embeds_the_gathered_jsonld_and_advances_the_state_marker(
        self, tmp_path: Path, fake_context: Callable[..., FakeCliContext]
    ) -> None:
        context = _initialized_context(tmp_path, fake_context)
        _write_gathered_artifact(tmp_path, context)

        result = SurfaceEnrichedCapability().execute(context)

        assert result["resulting_state"] is SurfaceGenerationProcessState.SURFACE_ENRICHED
        document = Path(result["surface_path"]).read_text(encoding="utf-8")
        assert SurfaceDocumentAdapter.get_state_marker(document) == "surface_enriched"
        embedded = SurfaceDocumentAdapter.extract_json_script(document, JSONLD_ID)
        assert embedded == _GATHERED_GRAPH

    def test_raises_when_the_gathered_artifact_is_missing(
        self, tmp_path: Path, fake_context: Callable[..., FakeCliContext]
    ) -> None:
        context = _initialized_context(tmp_path, fake_context)
        with pytest.raises(FileNotFoundError):
            SurfaceEnrichedCapability().execute(context)

    def test_raises_when_the_gathered_artifact_is_invalid_json(
        self, tmp_path: Path, fake_context: Callable[..., FakeCliContext]
    ) -> None:
        context = _initialized_context(tmp_path, fake_context)
        state_path = DataGatheredCapability.state_path(context)
        state_path.parent.mkdir(parents=True, exist_ok=True)
        state_path.write_text("{not json", encoding="utf-8")
        with pytest.raises(json.JSONDecodeError):
            SurfaceEnrichedCapability().execute(context)


class TestCheck:
    def test_is_true_after_a_real_execute(
        self, tmp_path: Path, fake_context: Callable[..., FakeCliContext]
    ) -> None:
        context = _initialized_context(tmp_path, fake_context)
        _write_gathered_artifact(tmp_path, context)
        capability = SurfaceEnrichedCapability()
        capability.execute(context)
        assert capability.check(context) is True

    def test_is_false_before_the_jsonld_script_is_embedded(
        self, tmp_path: Path, fake_context: Callable[..., FakeCliContext]
    ) -> None:
        context = _initialized_context(tmp_path, fake_context)
        assert SurfaceEnrichedCapability().check(context) is False

    def test_is_false_when_no_surface_exists_yet(
        self, tmp_path: Path, fake_context: Callable[..., FakeCliContext]
    ) -> None:
        context = fake_context(container_path=str(tmp_path))
        assert SurfaceEnrichedCapability().check(context) is False

    def test_is_satisfied_matches_check(
        self, tmp_path: Path, fake_context: Callable[..., FakeCliContext]
    ) -> None:
        context = _initialized_context(tmp_path, fake_context)
        capability = SurfaceEnrichedCapability()
        assert capability.is_satisfied(context) == capability.check(context)


class TestLabelDescriptionAndMetadata:
    @pytest.mark.parametrize(
        ("lang", "expected_label"),
        [("en", "Surface Enriched"), ("pt-br", "Surface Enriquecida")],
    )
    def test_label_delegates_to_process_state(self, lang: str, expected_label: str) -> None:
        assert SurfaceEnrichedCapability().label(lang) == expected_label

    @pytest.mark.parametrize("lang", ["en", "pt-br"])
    def test_description_delegates_to_process_state(self, lang: str) -> None:
        capability = SurfaceEnrichedCapability()
        assert capability.description(lang) == (
            SurfaceGenerationProcessState.SURFACE_ENRICHED.description(lang)
        )

    def test_metadata_id_matches_expected_capability_registry_id(self) -> None:
        assert SurfaceEnrichedCapability.METADATA.id == (
            "org.ontobdc.view.plugin.capability.transformation.target.surface_enriched"
        )
