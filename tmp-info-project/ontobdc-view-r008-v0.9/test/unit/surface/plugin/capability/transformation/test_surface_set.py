from __future__ import annotations

from pathlib import Path
from typing import Any, Callable, Dict

import pytest

from ontobdc_view.surface.adapter.document import CONFIG_ID, SurfaceDocumentAdapter
from ontobdc_view.surface.domain.machine.standard_surface_html.state import SurfaceGenerationProcessState
from ontobdc_view.surface.plugin.capability.transformation.surface_set import (
    SurfaceSetCapability,
)

from conftest import DEFAULT_CONFIG, FakeCliContext, build_surface_document


def _enriched_context(
    tmp_path: Path, fake_context: Callable[..., FakeCliContext], **context_values: Any
) -> FakeCliContext:
    context = fake_context(container_path=str(tmp_path), **context_values)
    document = build_surface_document(through_state="surface_enriched")
    (tmp_path / "index.html").write_text(document, encoding="utf-8")
    return context


class TestExecute:
    def test_defaults_are_used_when_no_surface_config_is_supplied(
        self, tmp_path: Path, fake_context: Callable[..., FakeCliContext]
    ) -> None:
        context = _enriched_context(tmp_path, fake_context)
        result: Dict[str, Any] = SurfaceSetCapability().execute(context)

        assert result["resulting_state"] is SurfaceGenerationProcessState.SURFACE_SET
        assert result["surface_config"] == DEFAULT_CONFIG
        document = Path(result["surface_path"]).read_text(encoding="utf-8")
        assert SurfaceDocumentAdapter.get_state_marker(document) == "surface_set"
        assert SurfaceDocumentAdapter.extract_json_script(document, CONFIG_ID) == DEFAULT_CONFIG

    def test_normalizes_an_explicit_partial_config_over_the_defaults(
        self, tmp_path: Path, fake_context: Callable[..., FakeCliContext]
    ) -> None:
        context = _enriched_context(
            tmp_path,
            fake_context,
            surface_config={"content": {"mode": "fixed"}, "gap": 24},
        )
        result = SurfaceSetCapability().execute(context)
        assert result["surface_config"]["content"]["mode"] == "fixed"
        assert result["surface_config"]["gap"] == 24
        assert result["surface_config"]["slotTarget"] == 72

    def test_raises_for_an_unsupported_content_mode(
        self, tmp_path: Path, fake_context: Callable[..., FakeCliContext]
    ) -> None:
        context = _enriched_context(
            tmp_path, fake_context, surface_config={"content": {"mode": "carousel"}}
        )
        with pytest.raises(ValueError, match="scroll.*fixed|fixed.*scroll"):
            SurfaceSetCapability().execute(context)

    def test_raises_when_surface_config_is_not_a_mapping(
        self, tmp_path: Path, fake_context: Callable[..., FakeCliContext]
    ) -> None:
        context = _enriched_context(tmp_path, fake_context, surface_config=["not", "a", "mapping"])
        with pytest.raises(ValueError):
            SurfaceSetCapability().execute(context)

    def test_invalid_numeric_fields_fall_back_to_their_defaults(
        self, tmp_path: Path, fake_context: Callable[..., FakeCliContext]
    ) -> None:
        context = _enriched_context(
            tmp_path, fake_context, surface_config={"slotTarget": -5, "gap": "not-a-number"}
        )
        result = SurfaceSetCapability().execute(context)
        assert result["surface_config"]["slotTarget"] == 72
        assert result["surface_config"]["gap"] == 12


class TestCheck:
    def test_is_true_after_a_real_execute(
        self, tmp_path: Path, fake_context: Callable[..., FakeCliContext]
    ) -> None:
        context = _enriched_context(tmp_path, fake_context)
        capability = SurfaceSetCapability()
        capability.execute(context)
        assert capability.check(context) is True

    def test_is_false_before_the_config_is_embedded(
        self, tmp_path: Path, fake_context: Callable[..., FakeCliContext]
    ) -> None:
        context = _enriched_context(tmp_path, fake_context)
        assert SurfaceSetCapability().check(context) is False

    def test_is_satisfied_matches_check(
        self, tmp_path: Path, fake_context: Callable[..., FakeCliContext]
    ) -> None:
        context = _enriched_context(tmp_path, fake_context)
        capability = SurfaceSetCapability()
        assert capability.is_satisfied(context) == capability.check(context)


class TestLabelDescriptionAndMetadata:
    @pytest.mark.parametrize(
        ("lang", "expected_label"),
        [("en", "Surface Set"), ("pt-br", "Surface Configurada")],
    )
    def test_label_delegates_to_process_state(self, lang: str, expected_label: str) -> None:
        assert SurfaceSetCapability().label(lang) == expected_label

    @pytest.mark.parametrize("lang", ["en", "pt-br"])
    def test_description_delegates_to_process_state(self, lang: str) -> None:
        capability = SurfaceSetCapability()
        assert capability.description(lang) == (
            SurfaceGenerationProcessState.SURFACE_SET.description(lang)
        )

    def test_metadata_id_matches_expected_capability_registry_id(self) -> None:
        assert SurfaceSetCapability.METADATA.id == (
            "org.ontobdc.view.plugin.capability.transformation.target.surface_set"
        )
