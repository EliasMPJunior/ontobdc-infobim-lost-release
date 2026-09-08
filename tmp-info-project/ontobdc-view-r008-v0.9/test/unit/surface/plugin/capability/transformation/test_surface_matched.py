from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Callable, Dict, List

import pytest

from ontobdc.storage.adapter.bootstrap import StorageNamespaceBootstrap
from ontobdc_view.surface.adapter.document import MATCHES_ID, SurfaceDocumentAdapter
from ontobdc_view.surface.domain.machine.standard_surface_html.state import SurfaceGenerationProcessState
from ontobdc_view.surface.plugin.capability.transformation.data_gathered import (
    DataGatheredCapability,
)
from ontobdc_view.surface.plugin.capability.transformation.surface_matched import (
    SurfaceMatchedCapability,
)

from conftest import FakeCliContext, build_surface_document

_OBDC = str(StorageNamespaceBootstrap.OBDC)
_VIEW = "http://datacenter.app.br/ontology/ontobdc/domain/view.ttl#"
_DCTERMS_TITLE = "http://purl.org/dc/terms/title"
_CONTAINER_SUBJECT = "urn:test:container:1"
# _default_requests() unconditionally appends these two static-Tile requests
# whenever their Component is registered (independent of the gathered
# graph's content) -- both onto-file-size-tile and onto-file-viewer-tile are
# real, currently-registered Components, so every auto-match test sees them
# in addition to whatever the graph itself produces.
_STATIC_TILE_NAMES = {"onto-file-size-tile", "onto-file-viewer-tile"}


def _gathered_graph(title: str = "Test Container") -> List[Dict[str, Any]]:
    return [
        {
            "@id": _CONTAINER_SUBJECT,
            "@type": [f"{_OBDC}DataContainer"],
            _DCTERMS_TITLE: [{"@value": title}],
        },
        {
            "@id": f"{_OBDC}DataContainer",
            "@type": [f"{_OBDC}SurfaceableEntity"],
        },
    ]


def _matched_ready_context(
    tmp_path: Path,
    fake_context: Callable[..., FakeCliContext],
    *,
    graph: Any = None,
    **context_values: Any,
) -> FakeCliContext:
    context = fake_context(container_path=str(tmp_path), **context_values)
    document = build_surface_document(through_state="surface_set")
    (tmp_path / "index.html").write_text(document, encoding="utf-8")

    state_path = DataGatheredCapability.state_path(context)
    state_path.parent.mkdir(parents=True, exist_ok=True)
    state_path.write_text(
        json.dumps(graph if graph is not None else _gathered_graph()), encoding="utf-8"
    )
    return context


class TestExecuteAutoMatching:
    def test_auto_matches_a_surfaceable_data_container_to_its_real_registered_tile(
        self, tmp_path: Path, fake_context: Callable[..., FakeCliContext]
    ) -> None:
        context = _matched_ready_context(tmp_path, fake_context)

        result = SurfaceMatchedCapability().execute(context)

        assert result["resulting_state"] is SurfaceGenerationProcessState.SURFACE_MATCHED
        document = Path(result["surface_path"]).read_text(encoding="utf-8")
        matches = SurfaceDocumentAdapter.extract_json_script(document, MATCHES_ID)
        assert result["match_count"] == len(matches)
        by_tile = {item["tile"]: item for item in matches}
        assert set(by_tile) == _STATIC_TILE_NAMES | {"onto-data-container-tile"}
        match = by_tile["onto-data-container-tile"]
        assert match["data"] == _CONTAINER_SUBJECT
        assert match["region"] == "content"
        # DataContainerTileComponent: min_columns=1, max_columns=6, sized from
        # dcterms:title length (4 chars_per_column) -- "Test Container" is 14
        # chars, so ceil(14 / 4) = 4 preferred columns.
        assert match["minColumns"] == 1
        assert match["maxColumns"] == 6
        assert match["preferredColumns"] == 4
        assert match["minRows"] == 2
        assert match["maxRows"] == 2

    def test_a_non_surfaceable_entity_type_produces_no_match(
        self, tmp_path: Path, fake_context: Callable[..., FakeCliContext]
    ) -> None:
        graph = [
            {"@id": "urn:test:thing:1", "@type": ["urn:test:UnknownType"]},
        ]
        context = _matched_ready_context(tmp_path, fake_context, graph=graph)

        result = SurfaceMatchedCapability().execute(context)
        document = Path(result["surface_path"]).read_text(encoding="utf-8")
        matches = SurfaceDocumentAdapter.extract_json_script(document, MATCHES_ID)
        assert {item["tile"] for item in matches} == _STATIC_TILE_NAMES

    def test_wider_titles_produce_more_preferred_columns_up_to_the_maximum(
        self, tmp_path: Path, fake_context: Callable[..., FakeCliContext]
    ) -> None:
        long_title = "X" * 100  # ceil(100 / 4) = 25, clamped to max_columns=6
        context = _matched_ready_context(
            tmp_path, fake_context, graph=_gathered_graph(title=long_title)
        )
        result = SurfaceMatchedCapability().execute(context)
        document = Path(result["surface_path"]).read_text(encoding="utf-8")
        matches = SurfaceDocumentAdapter.extract_json_script(document, MATCHES_ID)
        assert matches[0]["preferredColumns"] == 6


class TestExecuteExplicitRequests:
    def test_an_explicit_tile_class_request_is_resolved_strictly(
        self, tmp_path: Path, fake_context: Callable[..., FakeCliContext]
    ) -> None:
        context = _matched_ready_context(
            tmp_path,
            fake_context,
            surface_matches=[{"tileClass": f"{_VIEW}LanguageTile", "region": "operation"}],
        )
        result = SurfaceMatchedCapability().execute(context)
        assert result["match_count"] == 1
        document = Path(result["surface_path"]).read_text(encoding="utf-8")
        matches = SurfaceDocumentAdapter.extract_json_script(document, MATCHES_ID)
        assert matches[0]["tile"] == "onto-language-tile"
        # Operation-region requests are forced to exactly one row.
        assert matches[0]["minRows"] == 1
        assert matches[0]["preferredRows"] == 1
        assert matches[0]["maxRows"] == 1

    def test_an_explicit_request_with_no_matching_component_raises(
        self, tmp_path: Path, fake_context: Callable[..., FakeCliContext]
    ) -> None:
        context = _matched_ready_context(
            tmp_path,
            fake_context,
            surface_matches=[{"tileClass": "urn:test:NoSuchTileClass", "region": "content"}],
        )
        with pytest.raises(ValueError, match="No registered component satisfies request"):
            SurfaceMatchedCapability().execute(context)

    def test_a_request_without_data_or_tile_class_raises(
        self, tmp_path: Path, fake_context: Callable[..., FakeCliContext]
    ) -> None:
        context = _matched_ready_context(
            tmp_path, fake_context, surface_matches=[{"region": "content"}]
        )
        with pytest.raises(ValueError, match="must specify either"):
            SurfaceMatchedCapability().execute(context)


class TestCheck:
    def test_is_true_after_a_real_execute(
        self, tmp_path: Path, fake_context: Callable[..., FakeCliContext]
    ) -> None:
        context = _matched_ready_context(tmp_path, fake_context)
        capability = SurfaceMatchedCapability()
        capability.execute(context)
        assert capability.check(context) is True

    def test_is_false_before_matches_are_embedded(
        self, tmp_path: Path, fake_context: Callable[..., FakeCliContext]
    ) -> None:
        context = _matched_ready_context(tmp_path, fake_context)
        assert SurfaceMatchedCapability().check(context) is False

    def test_is_satisfied_matches_check(
        self, tmp_path: Path, fake_context: Callable[..., FakeCliContext]
    ) -> None:
        context = _matched_ready_context(tmp_path, fake_context)
        capability = SurfaceMatchedCapability()
        assert capability.is_satisfied(context) == capability.check(context)


class TestLabelDescriptionAndMetadata:
    @pytest.mark.parametrize(
        ("lang", "expected_label"),
        [("en", "Surface Matched"), ("pt-br", "Surface Correlacionada")],
    )
    def test_label_delegates_to_process_state(self, lang: str, expected_label: str) -> None:
        assert SurfaceMatchedCapability().label(lang) == expected_label

    @pytest.mark.parametrize("lang", ["en", "pt-br"])
    def test_description_delegates_to_process_state(self, lang: str) -> None:
        capability = SurfaceMatchedCapability()
        assert capability.description(lang) == (
            SurfaceGenerationProcessState.SURFACE_MATCHED.description(lang)
        )

    def test_metadata_id_matches_expected_capability_registry_id(self) -> None:
        assert SurfaceMatchedCapability.METADATA.id == (
            "org.ontobdc.view.plugin.capability.transformation.target.surface_matched"
        )
