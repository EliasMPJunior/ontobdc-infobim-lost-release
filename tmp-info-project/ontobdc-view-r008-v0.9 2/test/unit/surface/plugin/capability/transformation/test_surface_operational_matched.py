from __future__ import annotations

from pathlib import Path
from typing import Any, Callable, Dict

import pytest

from ontobdc_view.surface.adapter.document import MATCHES_ID, SurfaceDocumentAdapter
from ontobdc_view.surface.domain.machine.standard_surface_html.state import SurfaceGenerationProcessState
from ontobdc_view.surface.plugin.capability.transformation.surface_operational_matched import (
    DEFAULT_LAYOUTS_BOOTSTRAP_ID,
    DEFAULT_LAYOUTS_SCRIPT_ID,
    SurfaceOperationalMatchedCapability,
)

from conftest import FakeCliContext, build_surface_document

_SHIPPED_OPERATION_TILES = {"onto-logo-tile", "onto-language-tile", "onto-theme-tile"}


def _branded_context(
    tmp_path: Path,
    fake_context: Callable[..., FakeCliContext],
    *,
    existing_matches: list | None = None,
) -> FakeCliContext:
    context = fake_context(container_path=str(tmp_path))
    document = build_surface_document(through_state="surface_branded")
    document = SurfaceDocumentAdapter.upsert_json_script(
        document, MATCHES_ID, existing_matches if existing_matches is not None else []
    )
    (tmp_path / "index.html").write_text(document, encoding="utf-8")
    return context


class TestExecute:
    def test_adds_the_shipped_operation_defaults_when_none_declared(
        self, tmp_path: Path, fake_context: Callable[..., FakeCliContext]
    ) -> None:
        context = _branded_context(tmp_path, fake_context)

        result: Dict[str, Any] = SurfaceOperationalMatchedCapability().execute(context)

        assert (
            result["resulting_state"]
            is SurfaceGenerationProcessState.SURFACE_OPERATIONAL_MATCHED
        )
        assert result["operational_match_count"] == 3
        assert result["default_layout_count"] == 1

        document = Path(result["surface_path"]).read_text(encoding="utf-8")
        matches = SurfaceDocumentAdapter.extract_json_script(document, MATCHES_ID)
        operation_tiles = {
            item["tile"] for item in matches if item["region"] == "operation"
        }
        assert operation_tiles == _SHIPPED_OPERATION_TILES
        for item in matches:
            if item["region"] == "operation":
                assert (item["minRows"], item["preferredRows"], item["maxRows"]) == (1, 1, 1)

        assert SurfaceDocumentAdapter.extract_json_script(document, DEFAULT_LAYOUTS_SCRIPT_ID)
        assert f'id="{DEFAULT_LAYOUTS_BOOTSTRAP_ID}"' in document

    def test_skips_the_defaults_when_an_operation_match_already_exists(
        self, tmp_path: Path, fake_context: Callable[..., FakeCliContext]
    ) -> None:
        existing = [
            {
                "tile": "onto-custom-operation-tile",
                "region": "operation",
                "minColumns": 1,
                "preferredColumns": 1,
                "maxColumns": 1,
                "minRows": 1,
                "preferredRows": 1,
                "maxRows": 1,
            }
        ]
        context = _branded_context(tmp_path, fake_context, existing_matches=existing)

        result = SurfaceOperationalMatchedCapability().execute(context)

        # The shipped defaults are suppressed, but the default-layout
        # definitions are still embedded for client-side selection.
        assert result["operational_match_count"] == 0
        assert result["default_layout_count"] == 1
        document = Path(result["surface_path"]).read_text(encoding="utf-8")
        matches = SurfaceDocumentAdapter.extract_json_script(document, MATCHES_ID)
        assert [item["tile"] for item in matches] == ["onto-custom-operation-tile"]
        assert SurfaceDocumentAdapter.extract_json_script(document, DEFAULT_LAYOUTS_SCRIPT_ID)

    def test_raises_when_the_matches_script_is_missing(
        self, tmp_path: Path, fake_context: Callable[..., FakeCliContext]
    ) -> None:
        context = fake_context(container_path=str(tmp_path))
        document = build_surface_document(through_state="surface_branded")
        (tmp_path / "index.html").write_text(document, encoding="utf-8")

        with pytest.raises(ValueError, match="Missing script"):
            SurfaceOperationalMatchedCapability().execute(context)

    def test_raises_when_the_matches_script_is_not_a_list(
        self, tmp_path: Path, fake_context: Callable[..., FakeCliContext]
    ) -> None:
        context = fake_context(container_path=str(tmp_path))
        document = build_surface_document(through_state="surface_branded")
        document = SurfaceDocumentAdapter.upsert_json_script(document, MATCHES_ID, {"not": "a list"})
        (tmp_path / "index.html").write_text(document, encoding="utf-8")

        with pytest.raises(ValueError, match="Surface matches are missing or invalid"):
            SurfaceOperationalMatchedCapability().execute(context)


class TestCheck:
    def test_is_true_after_a_real_execute(
        self, tmp_path: Path, fake_context: Callable[..., FakeCliContext]
    ) -> None:
        context = _branded_context(tmp_path, fake_context)
        capability = SurfaceOperationalMatchedCapability()
        capability.execute(context)
        assert capability.check(context) is True

    def test_is_false_before_operational_matching_runs(
        self, tmp_path: Path, fake_context: Callable[..., FakeCliContext]
    ) -> None:
        context = _branded_context(tmp_path, fake_context)
        assert SurfaceOperationalMatchedCapability().check(context) is False

    def test_is_satisfied_matches_check(
        self, tmp_path: Path, fake_context: Callable[..., FakeCliContext]
    ) -> None:
        context = _branded_context(tmp_path, fake_context)
        capability = SurfaceOperationalMatchedCapability()
        assert capability.is_satisfied(context) == capability.check(context)


class TestLabelDescriptionAndMetadata:
    @pytest.mark.parametrize(
        ("lang", "expected_label"),
        [
            ("en", "Surface Operational Matched"),
            ("pt-br", "Surface Operacional Correlacionada"),
        ],
    )
    def test_label_delegates_to_process_state(self, lang: str, expected_label: str) -> None:
        assert SurfaceOperationalMatchedCapability().label(lang) == expected_label

    @pytest.mark.parametrize("lang", ["en", "pt-br"])
    def test_description_delegates_to_process_state(self, lang: str) -> None:
        capability = SurfaceOperationalMatchedCapability()
        assert capability.description(lang) == (
            SurfaceGenerationProcessState.SURFACE_OPERATIONAL_MATCHED.description(lang)
        )

    def test_metadata_id_matches_expected_capability_registry_id(self) -> None:
        assert SurfaceOperationalMatchedCapability.METADATA.id == (
            "org.ontobdc.view.plugin.capability.transformation.target."
            "surface_operational_matched"
        )
