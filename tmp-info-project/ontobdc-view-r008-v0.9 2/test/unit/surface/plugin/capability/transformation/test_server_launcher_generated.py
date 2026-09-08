from __future__ import annotations

from pathlib import Path
from typing import Callable

import pytest

from ontobdc_view.surface.adapter.document import SurfaceDocumentAdapter
from ontobdc_view.surface.domain.machine.standard_surface_html.state import SurfaceGenerationProcessState
from ontobdc_view.surface.plugin.capability.transformation.server_launcher_generated import (
    ServerLauncherGeneratedCapability,
)

from conftest import FakeCliContext, build_surface_document

# ServerLauncherGeneratedCapability.execute() is temporarily nulled out to a
# state-marker-only no-op (see the class docstring): it writes no
# server.cmd and embeds no ontobdc-server-reference script, pending the
# real launcher-generation implementation. Its check (is_server_launcher_
# generated) has been simplified to match -- marker-only, see that
# module's docstring. This is the final state in the pipeline, so there is
# no later marker to exercise the cumulative-check behavior against here
# (that is already covered for SurfaceDocumentAdapter.state_reached() by
# the other capability tests in this package).


def _context_with_surface(
    tmp_path: Path, fake_context: Callable[..., FakeCliContext]
) -> FakeCliContext:
    context = fake_context(container_path=str(tmp_path))
    document = build_surface_document(through_state="surface_initialized")
    (tmp_path / "index.html").write_text(document, encoding="utf-8")
    return context


class TestExecute:
    def test_marks_the_document_reached_without_writing_any_launcher_artifact(
        self, tmp_path: Path, fake_context: Callable[..., FakeCliContext]
    ) -> None:
        context = _context_with_surface(tmp_path, fake_context)

        result = ServerLauncherGeneratedCapability().execute(context)

        assert (
            result["resulting_state"]
            is SurfaceGenerationProcessState.SERVER_LAUNCHER_GENERATED
        )
        assert set(result) == {"resulting_state", "surface_path"}
        document = Path(result["surface_path"]).read_text(encoding="utf-8")
        assert SurfaceDocumentAdapter.get_state_marker(document) == "server_launcher_generated"
        assert not (tmp_path / "server.cmd").exists()


class TestCheck:
    def test_is_true_after_a_real_execute(
        self, tmp_path: Path, fake_context: Callable[..., FakeCliContext]
    ) -> None:
        context = _context_with_surface(tmp_path, fake_context)
        capability = ServerLauncherGeneratedCapability()
        capability.execute(context)
        assert capability.check(context) is True

    def test_is_false_before_the_state_is_reached(
        self, tmp_path: Path, fake_context: Callable[..., FakeCliContext]
    ) -> None:
        context = _context_with_surface(tmp_path, fake_context)
        assert ServerLauncherGeneratedCapability().check(context) is False

    def test_is_satisfied_matches_check(
        self, tmp_path: Path, fake_context: Callable[..., FakeCliContext]
    ) -> None:
        context = _context_with_surface(tmp_path, fake_context)
        capability = ServerLauncherGeneratedCapability()
        assert capability.is_satisfied(context) == capability.check(context)


class TestLabelDescriptionAndMetadata:
    @pytest.mark.parametrize(
        ("lang", "expected_label"),
        [("en", "Server Launcher Generated"), ("pt-br", "Launcher do Servidor Gerado")],
    )
    def test_label_delegates_to_process_state(self, lang: str, expected_label: str) -> None:
        assert ServerLauncherGeneratedCapability().label(lang) == expected_label

    @pytest.mark.parametrize("lang", ["en", "pt-br"])
    def test_description_delegates_to_process_state(self, lang: str) -> None:
        capability = ServerLauncherGeneratedCapability()
        assert capability.description(lang) == (
            SurfaceGenerationProcessState.SERVER_LAUNCHER_GENERATED.description(lang)
        )

    def test_metadata_id_matches_expected_capability_registry_id(self) -> None:
        assert ServerLauncherGeneratedCapability.METADATA.id == (
            "org.ontobdc.view.plugin.capability.transformation.target."
            "server_launcher_generated"
        )
