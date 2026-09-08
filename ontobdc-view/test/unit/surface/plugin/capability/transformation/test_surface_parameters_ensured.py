from __future__ import annotations

from pathlib import Path
from typing import Callable

import pytest

from ontobdc_view.surface.adapter.document import SurfaceDocumentAdapter
from ontobdc_view.surface.domain.machine.standard_surface_html.state import SurfaceGenerationProcessState
from ontobdc_view.surface.plugin.capability.transformation.surface_parameters_ensured import (
    SurfaceParametersEnsuredCapability,
)

from conftest import FakeCliContext, build_surface_document


def _assembled_context(
    tmp_path: Path, fake_context: Callable[..., FakeCliContext], *, lang: str = "en"
) -> FakeCliContext:
    context = fake_context(container_path=str(tmp_path))
    document = build_surface_document(lang=lang, through_state="surface_assembled")
    (tmp_path / "index.html").write_text(document, encoding="utf-8")
    return context


class TestResolveDefaults:
    def test_uses_the_requested_language_when_present(
        self, tmp_path: Path, fake_context: Callable[..., FakeCliContext]
    ) -> None:
        context = _assembled_context(tmp_path, fake_context, lang="en")
        context.set_parameter_value("language", "es")
        document = build_surface_document(lang="en", through_state="surface_assembled")
        defaults = SurfaceParametersEnsuredCapability.resolve_defaults(context, document)
        assert defaults == {"lang": "es"}

    def test_falls_back_to_the_documents_html_lang_attribute(
        self, tmp_path: Path, fake_context: Callable[..., FakeCliContext]
    ) -> None:
        context = _assembled_context(tmp_path, fake_context)
        document = build_surface_document(lang="pt-BR", through_state="surface_assembled")
        defaults = SurfaceParametersEnsuredCapability.resolve_defaults(context, document)
        assert defaults == {"lang": "pt-BR"}

    def test_falls_back_to_english_when_neither_is_available(
        self, tmp_path: Path, fake_context: Callable[..., FakeCliContext]
    ) -> None:
        context = _assembled_context(tmp_path, fake_context)
        document = "<html><head></head><body></body></html>"
        defaults = SurfaceParametersEnsuredCapability.resolve_defaults(context, document)
        assert defaults == {"lang": "en"}


class TestExecute:
    def test_embeds_the_bootstrap_script_and_advances_the_marker(
        self, tmp_path: Path, fake_context: Callable[..., FakeCliContext]
    ) -> None:
        context = _assembled_context(tmp_path, fake_context, lang="pt-BR")

        result = SurfaceParametersEnsuredCapability().execute(context)

        assert (
            result["resulting_state"]
            is SurfaceGenerationProcessState.SURFACE_PARAMETERS_ENSURED
        )
        assert result["url_state_defaults"] == {"lang": "pt-BR"}
        document = Path(result["surface_path"]).read_text(encoding="utf-8")
        assert 'id="ontobdc-surface-url-state"' in document
        assert 'const NAMES = ["lang","theme"];' in document
        assert "Object.entries(DEFAULTS)" in document
        assert "params.get(name) ?? applied(name)" in document
        assert SurfaceDocumentAdapter.get_state_marker(document) == "surface_parameters_ensured"


class TestCheck:
    def test_is_true_after_a_real_execute(
        self, tmp_path: Path, fake_context: Callable[..., FakeCliContext]
    ) -> None:
        context = _assembled_context(tmp_path, fake_context)
        capability = SurfaceParametersEnsuredCapability()
        capability.execute(context)
        assert capability.check(context) is True

    def test_is_true_for_any_later_cumulative_state_marker(
        self, tmp_path: Path, fake_context: Callable[..., FakeCliContext]
    ) -> None:
        # check() is marker-only and cumulative: a document already past
        # SURFACE_PARAMETERS_ENSURED (e.g. surface_packaged) still satisfies it.
        context = fake_context(container_path=str(tmp_path))
        document = build_surface_document(through_state="surface_assembled")
        document = SurfaceDocumentAdapter.set_state_marker(document, "surface_packaged")
        (tmp_path / "index.html").write_text(document, encoding="utf-8")
        assert SurfaceParametersEnsuredCapability().check(context) is True

    def test_is_false_before_the_bootstrap_is_embedded(
        self, tmp_path: Path, fake_context: Callable[..., FakeCliContext]
    ) -> None:
        context = _assembled_context(tmp_path, fake_context)
        assert SurfaceParametersEnsuredCapability().check(context) is False

    def test_is_false_when_no_surface_exists_yet(
        self, tmp_path: Path, fake_context: Callable[..., FakeCliContext]
    ) -> None:
        context = fake_context(container_path=str(tmp_path))
        assert SurfaceParametersEnsuredCapability().check(context) is False

    def test_is_satisfied_matches_check(
        self, tmp_path: Path, fake_context: Callable[..., FakeCliContext]
    ) -> None:
        context = _assembled_context(tmp_path, fake_context)
        capability = SurfaceParametersEnsuredCapability()
        assert capability.is_satisfied(context) == capability.check(context)


class TestLabelDescriptionAndMetadata:
    @pytest.mark.parametrize(
        ("lang", "expected_label"),
        [
            ("en", "Surface Parameters Ensured"),
            ("pt-br", "Parametros da Surface Garantidos"),
        ],
    )
    def test_label_delegates_to_process_state(self, lang: str, expected_label: str) -> None:
        assert SurfaceParametersEnsuredCapability().label(lang) == expected_label

    @pytest.mark.parametrize("lang", ["en", "pt-br"])
    def test_description_delegates_to_process_state(self, lang: str) -> None:
        capability = SurfaceParametersEnsuredCapability()
        assert capability.description(lang) == (
            SurfaceGenerationProcessState.SURFACE_PARAMETERS_ENSURED.description(lang)
        )

    def test_metadata_id_matches_expected_capability_registry_id(self) -> None:
        assert SurfaceParametersEnsuredCapability.METADATA.id == (
            "org.ontobdc.view.plugin.capability.transformation.target."
            "surface_parameters_ensured"
        )
