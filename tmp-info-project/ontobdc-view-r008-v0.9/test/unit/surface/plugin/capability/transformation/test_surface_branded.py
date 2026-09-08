from __future__ import annotations

from pathlib import Path
from typing import Callable
from unittest.mock import patch

import pytest

from ontobdc_view.surface.domain.machine.standard_surface_html.state import SurfaceGenerationProcessState
from ontobdc_view.surface.plugin.capability.transformation.surface_branded import (
    SurfaceBrandedCapability,
)

from conftest import FakeCliContext, build_surface_document

_VALID_SVG = b'<svg xmlns="http://www.w3.org/2000/svg"></svg>'
_BRAND_RELATIVE_PATH = Path(".__ontobdc__") / "asset" / "OntoBDCBrand.svg"
_LOGOTYPE_RELATIVE_PATH = Path(".__ontobdc__") / "asset" / "OntoBDCLogotype.svg"


def _matched_context(
    tmp_path: Path, fake_context: Callable[..., FakeCliContext], *, workspace_root: Path
) -> FakeCliContext:
    document = build_surface_document(through_state="surface_set")
    (tmp_path / "index.html").write_text(document, encoding="utf-8")
    return fake_context(container_path=str(tmp_path), root_path=str(workspace_root))


class TestExecute:
    def test_resolves_from_the_container_when_present_there(
        self, tmp_path: Path, fake_context: Callable[..., FakeCliContext]
    ) -> None:
        (tmp_path / _BRAND_RELATIVE_PATH).parent.mkdir(parents=True, exist_ok=True)
        (tmp_path / _BRAND_RELATIVE_PATH).write_bytes(_VALID_SVG)
        (tmp_path / _LOGOTYPE_RELATIVE_PATH).write_bytes(_VALID_SVG)
        context = _matched_context(tmp_path, fake_context, workspace_root=tmp_path)

        result = SurfaceBrandedCapability().execute(context)

        assert result["resulting_state"] is SurfaceGenerationProcessState.SURFACE_BRANDED
        assert result["branding"]["brand"]["source"] == "container"
        assert result["branding"]["logotype"]["source"] == "container"

    def test_resolves_from_the_workspace_when_absent_from_the_container(
        self, tmp_path: Path, fake_context: Callable[..., FakeCliContext]
    ) -> None:
        container_root = tmp_path / "container"
        container_root.mkdir()
        workspace_root = tmp_path / "workspace"
        (workspace_root / _BRAND_RELATIVE_PATH).parent.mkdir(parents=True, exist_ok=True)
        (workspace_root / _BRAND_RELATIVE_PATH).write_bytes(_VALID_SVG)
        (workspace_root / _LOGOTYPE_RELATIVE_PATH).write_bytes(_VALID_SVG)

        document = build_surface_document(through_state="surface_set")
        (container_root / "index.html").write_text(document, encoding="utf-8")
        context = fake_context(container_path=str(container_root), root_path=str(workspace_root))

        result = SurfaceBrandedCapability().execute(context)
        assert result["branding"]["brand"]["source"] == "workspace"
        # A workspace asset is used in place -- never copied into the container.
        assert not (container_root / _BRAND_RELATIVE_PATH).exists()

    def test_falls_back_to_the_empty_svg_when_every_other_tier_fails(
        self, tmp_path: Path, fake_context: Callable[..., FakeCliContext]
    ) -> None:
        context = _matched_context(tmp_path, fake_context, workspace_root=tmp_path)
        with patch.object(
            SurfaceBrandedCapability, "_download", side_effect=OSError("network unavailable")
        ):
            result = SurfaceBrandedCapability().execute(context)

        assert result["branding"]["brand"]["source"] == "empty-fallback"
        written = (tmp_path / _BRAND_RELATIVE_PATH).read_bytes()
        assert written == b'<svg xmlns="http://www.w3.org/2000/svg"></svg>'

    def test_downloads_from_the_official_page_when_local_tiers_are_absent(
        self, tmp_path: Path, fake_context: Callable[..., FakeCliContext]
    ) -> None:
        context = _matched_context(tmp_path, fake_context, workspace_root=tmp_path)
        page_html = (
            b'<html><body><img src="/assets/OntoBDCBrand.svg">'
            b'<img src="/assets/OntoBDCLogotype.svg"></body></html>'
        )

        def fake_download(url: str) -> bytes:
            if url.rstrip("/").endswith("ontobdc.org"):
                return page_html
            return _VALID_SVG

        with patch.object(SurfaceBrandedCapability, "_download", side_effect=fake_download):
            result = SurfaceBrandedCapability().execute(context)

        assert result["branding"]["brand"]["source"] == "https://ontobdc.org/assets/OntoBDCBrand.svg"
        assert (tmp_path / _BRAND_RELATIVE_PATH).read_bytes() == _VALID_SVG

    def test_raises_when_a_local_candidate_is_not_actually_svg(
        self, tmp_path: Path, fake_context: Callable[..., FakeCliContext]
    ) -> None:
        (tmp_path / _BRAND_RELATIVE_PATH).parent.mkdir(parents=True, exist_ok=True)
        (tmp_path / _BRAND_RELATIVE_PATH).write_bytes(b"not an svg file")
        context = _matched_context(tmp_path, fake_context, workspace_root=tmp_path)

        with pytest.raises(ValueError, match="not SVG"):
            SurfaceBrandedCapability().execute(context)

    def test_raises_when_container_path_is_not_set(
        self, fake_context: Callable[..., FakeCliContext]
    ) -> None:
        with pytest.raises(ValueError, match="container_path is required"):
            SurfaceBrandedCapability().execute(fake_context())


class TestCheck:
    def test_is_true_after_a_real_execute(
        self, tmp_path: Path, fake_context: Callable[..., FakeCliContext]
    ) -> None:
        context = _matched_context(tmp_path, fake_context, workspace_root=tmp_path)
        with patch.object(SurfaceBrandedCapability, "_download", side_effect=OSError("offline")):
            SurfaceBrandedCapability().execute(context)
        assert SurfaceBrandedCapability().check(context) is True

    def test_is_false_when_no_surface_exists_yet(
        self, tmp_path: Path, fake_context: Callable[..., FakeCliContext]
    ) -> None:
        context = fake_context(container_path=str(tmp_path))
        assert SurfaceBrandedCapability().check(context) is False

    def test_is_satisfied_matches_check(
        self, tmp_path: Path, fake_context: Callable[..., FakeCliContext]
    ) -> None:
        context = _matched_context(tmp_path, fake_context, workspace_root=tmp_path)
        capability = SurfaceBrandedCapability()
        assert capability.is_satisfied(context) == capability.check(context)


class TestLabelDescriptionAndMetadata:
    @pytest.mark.parametrize(
        ("lang", "expected_label"),
        [("en", "Surface Branded"), ("pt-br", "Surface com Branding")],
    )
    def test_label_delegates_to_process_state(self, lang: str, expected_label: str) -> None:
        assert SurfaceBrandedCapability().label(lang) == expected_label

    @pytest.mark.parametrize("lang", ["en", "pt-br"])
    def test_description_delegates_to_process_state(self, lang: str) -> None:
        capability = SurfaceBrandedCapability()
        assert capability.description(lang) == (
            SurfaceGenerationProcessState.SURFACE_BRANDED.description(lang)
        )

    def test_metadata_id_matches_expected_capability_registry_id(self) -> None:
        assert SurfaceBrandedCapability.METADATA.id == (
            "org.ontobdc.view.plugin.capability.transformation.target.surface_branded"
        )
