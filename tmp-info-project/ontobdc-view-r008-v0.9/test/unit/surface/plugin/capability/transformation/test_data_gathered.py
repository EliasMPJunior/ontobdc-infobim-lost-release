from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List
from unittest.mock import MagicMock, patch

import pytest
from rdflib import Graph, Literal, URIRef
from rdflib.namespace import DCTERMS, RDF

from ontobdc.storage.adapter.manifest import ContainerDataPackageSynchronizer
from ontobdc_view.surface.domain.machine.standard_surface_html.state import SurfaceGenerationProcessState
from ontobdc_view.surface.plugin.capability.transformation.data_gathered import (
    _OBDC,
    DataGatheredCapability,
)

# `StorageBootstrap.get_container_storage_file_path`/`get_dataset_storage_file_path`/
# `get_ontobdc_directory` are pure, side-effect-free Path joins (confirmed by
# reading ontobdc/src/ontobdc/storage/adapter/bootstrap.py) -- so instead of
# mocking them, these tests write real Turtle fixtures at the exact real paths
# those classmethods resolve to. The two collaborators actually mocked are the
# ones that would otherwise require real filesystem enumeration rules
# (ContainerDataPackageSynchronizer) or a real Excel workbook
# (DatasetEntityInstanceRepository) -- everything else (Graph building,
# rdflib parsing/serialization) runs for real.
_DATASET_INSTANCE_REPOSITORY_PATH = (
    "ontobdc.context.adapter.dataset_instance.DatasetEntityInstanceRepository"
)


def _fake_context(container_path: Path) -> MagicMock:
    context = MagicMock()
    context.get_parameter_value.return_value = str(container_path)
    return context


class TestFileTypeClassification:
    @pytest.mark.parametrize(
        ("extension", "expected"),
        [
            ("png", _OBDC.ImageFile),
            ("jpg", _OBDC.ImageFile),
            ("svg", _OBDC.ImageFile),
            ("pdf", _OBDC.PdfFile),
            ("csv", _OBDC.CsvFile),
            ("xlsx", _OBDC.GenericFile),
            ("", _OBDC.GenericFile),
        ],
    )
    def test_file_type_uri_classifies_by_extension(
        self, extension: str, expected: URIRef
    ) -> None:
        assert DataGatheredCapability._file_type_uri(extension) == expected


class TestLocalName:
    def test_local_name_from_hash_fragment(self) -> None:
        predicate = URIRef("http://example.org/ns.ttl#hasFacadeField")
        assert DataGatheredCapability._local_name(predicate) == "hasFacadeField"

    def test_local_name_from_trailing_slash_segment(self) -> None:
        predicate = URIRef("http://example.org/ns/mapsToProperty")
        assert DataGatheredCapability._local_name(predicate) == "mapsToProperty"


class TestContainerSubject:
    def test_container_subject_returns_the_single_data_container(self) -> None:
        capability = DataGatheredCapability()
        graph = Graph()
        subject = URIRef("urn:uuid:container-1")
        graph.add((subject, RDF.type, _OBDC.DataContainer))
        assert capability._container_subject(graph) == subject

    def test_container_subject_raises_when_none_present(self) -> None:
        capability = DataGatheredCapability()
        with pytest.raises(ValueError):
            capability._container_subject(Graph())

    def test_container_subject_raises_when_more_than_one_present(self) -> None:
        capability = DataGatheredCapability()
        graph = Graph()
        graph.add((URIRef("urn:uuid:container-1"), RDF.type, _OBDC.DataContainer))
        graph.add((URIRef("urn:uuid:container-2"), RDF.type, _OBDC.DataContainer))
        with pytest.raises(ValueError):
            capability._container_subject(graph)


class TestSurfaceableDeclarations:
    def test_marks_data_container_and_file_tree_as_surfaceable(self) -> None:
        capability = DataGatheredCapability()
        graph = Graph()
        capability._add_surfaceable_declarations(graph)
        assert (_OBDC.DataContainer, RDF.type, _OBDC.SurfaceableEntity) in graph
        assert (_OBDC.FileTree, RDF.type, _OBDC.SurfaceableEntity) in graph
        assert len(graph) == 2


class TestCheck:
    _CONTAINER_TTL = "@prefix obdc: <{ns}> .\n<urn:uuid:c> a obdc:DataContainer .\n"

    def test_check_returns_true_for_a_valid_json_object_state_file(
        self, tmp_path: Path
    ) -> None:
        capability = DataGatheredCapability()
        context = _fake_context(tmp_path)
        state_path = capability.state_path(context)
        state_path.parent.mkdir(parents=True, exist_ok=True)
        state_path.write_text(json.dumps({"@graph": []}), encoding="utf-8")
        assert capability.check(context) is True

    def test_check_returns_true_for_a_valid_json_array_state_file(
        self, tmp_path: Path
    ) -> None:
        capability = DataGatheredCapability()
        context = _fake_context(tmp_path)
        state_path = capability.state_path(context)
        state_path.parent.mkdir(parents=True, exist_ok=True)
        state_path.write_text(json.dumps([]), encoding="utf-8")
        assert capability.check(context) is True

    def test_check_returns_false_when_state_file_is_missing(
        self, tmp_path: Path
    ) -> None:
        capability = DataGatheredCapability()
        context = _fake_context(tmp_path)
        assert capability.check(context) is False

    def test_check_returns_false_for_invalid_json(self, tmp_path: Path) -> None:
        capability = DataGatheredCapability()
        context = _fake_context(tmp_path)
        state_path = capability.state_path(context)
        state_path.parent.mkdir(parents=True, exist_ok=True)
        state_path.write_text("{not json", encoding="utf-8")
        assert capability.check(context) is False

    def test_check_returns_false_for_non_container_json_value(
        self, tmp_path: Path
    ) -> None:
        capability = DataGatheredCapability()
        context = _fake_context(tmp_path)
        state_path = capability.state_path(context)
        state_path.parent.mkdir(parents=True, exist_ok=True)
        state_path.write_text(json.dumps("just a string"), encoding="utf-8")
        assert capability.check(context) is False


class TestExecute:
    _NS = str(_OBDC)

    @staticmethod
    def _write_container_ttl(container_root: Path, subject: str) -> None:
        container_ttl = container_root / ".__ontobdc__" / "container.ttl"
        container_ttl.parent.mkdir(parents=True, exist_ok=True)
        container_ttl.write_text(
            f'@prefix obdc: <{TestExecute._NS}> .\n'
            f"<{subject}> a obdc:DataContainer .\n",
            encoding="utf-8",
        )

    def test_execute_with_zero_datasets_writes_state_and_returns_summary(
        self, tmp_path: Path
    ) -> None:
        container_root = tmp_path.resolve()
        self._write_container_ttl(container_root, "urn:uuid:container-1")
        for name in ("photo.png", "notes.pdf"):
            (container_root / name).write_bytes(b"x")

        capability = DataGatheredCapability()
        context = _fake_context(container_root)

        with patch.object(
            ContainerDataPackageSynchronizer,
            "list_container_file_paths",
            return_value=["photo.png", "notes.pdf"],
        ) as mocked_file_paths:
            result: Dict[str, Any] = capability.execute(context)

        mocked_file_paths.assert_called_once_with(container_root)
        assert result["resulting_state"] is SurfaceGenerationProcessState.DATA_GATHERED
        assert result["file_count"] == 2
        assert result["dataset_count"] == 0
        state_path = Path(result["state_path"])
        assert state_path == capability.state_path(context)
        assert state_path.is_file()

        written_graph = Graph()
        written_graph.parse(str(state_path), format="json-ld")

        file_types: List[URIRef] = sorted(
            written_graph.objects(None, RDF.type), key=str
        )
        assert _OBDC.FileTree in file_types
        assert _OBDC.ImageFile in file_types
        assert _OBDC.PdfFile in file_types

        file_sizes: List[Any] = list(written_graph.objects(None, _OBDC.fileSize))
        assert len(file_sizes) == 2

    def test_execute_merges_dataset_triples_and_facade_field_values(
        self, tmp_path: Path
    ) -> None:
        container_root = tmp_path.resolve()
        self._write_container_ttl(container_root, "urn:uuid:container-1")

        dataset_root = container_root / "dataset_a"
        dataset_ttl = dataset_root / ".__ontobdc__" / "dataset.ttl"
        dataset_ttl.parent.mkdir(parents=True, exist_ok=True)
        dataset_ttl.write_text(
            f"@prefix obdc: <{self._NS}> .\n"
            "@prefix dcterms: <http://purl.org/dc/terms/> .\n"
            "@prefix type: <urn:test:type#> .\n\n"
            "<urn:test:dataset/dataset_a> a obdc:EntityDataset ;\n"
            "    obdc:hasDataEntity <urn:test:entity/e1> ;\n"
            '    dcterms:identifier "urn:test:dataset/dataset_a" .\n\n'
            "<urn:test:entity/e1> a type:Thing, obdc:DataEntity ;\n"
            '    dcterms:identifier "GLOBAL-1" .\n',
            encoding="utf-8",
        )

        facade_ttl = dataset_root / ".__ontobdc__" / "linkset" / "facade.ttl"
        facade_ttl.parent.mkdir(parents=True, exist_ok=True)
        facade_ttl.write_text(
            "@prefix : <urn:test:facade#> .\n"
            "@prefix type: <urn:test:type#> .\n"
            "@prefix schema: <http://schema.org/> .\n\n"
            "type:Thing :hasDataEntityFacade :ThingFacade .\n"
            ":ThingFacade :hasFacadeField :WhatField .\n"
            ':WhatField schema:identifier "What" ;\n'
            "    :mapsToProperty <urn:test:type#what> .\n",
            encoding="utf-8",
        )

        capability = DataGatheredCapability()
        context = _fake_context(container_root)

        instances_payload: Dict[str, Any] = {
            "instances": [
                {
                    "GlobalId": "GLOBAL-1",
                    "Name": "Test Entity",
                    "Description": "A test description",
                    "What": "Some Value",
                }
            ]
        }
        with patch.object(
            ContainerDataPackageSynchronizer,
            "list_container_file_paths",
            return_value=[],
        ), patch(_DATASET_INSTANCE_REPOSITORY_PATH) as mocked_repository_class:
            mocked_repository_class.return_value.list_instances.return_value = (
                instances_payload
            )
            result: Dict[str, Any] = capability.execute(context)

        mocked_repository_class.assert_called_once_with(
            dataset_path=str(dataset_root), entity="urn:test:type#Thing"
        )
        assert result["dataset_count"] == 1

        written_graph = Graph()
        written_graph.parse(Path(result["state_path"]), format="json-ld")
        entity = URIRef("urn:test:entity/e1")
        assert (entity, DCTERMS.title, Literal("Test Entity")) in written_graph
        assert (
            entity,
            DCTERMS.description,
            Literal("A test description"),
        ) in written_graph
        assert (
            entity,
            URIRef("urn:test:type#what"),
            Literal("Some Value"),
        ) in written_graph

    def test_execute_tolerates_dataset_instance_repository_failure(
        self, tmp_path: Path
    ) -> None:
        # _find_entity_row swallows any exception from the workbook repository
        # (a missing/corrupt datapackage must not break the whole DATA_GATHERED
        # step over one dataset's field-value enrichment) -- confirm execute()
        # still completes and simply omits the enriched field values.
        container_root = tmp_path.resolve()
        self._write_container_ttl(container_root, "urn:uuid:container-1")

        dataset_root = container_root / "dataset_a"
        dataset_ttl = dataset_root / ".__ontobdc__" / "dataset.ttl"
        dataset_ttl.parent.mkdir(parents=True, exist_ok=True)
        dataset_ttl.write_text(
            f"@prefix obdc: <{self._NS}> .\n"
            "@prefix dcterms: <http://purl.org/dc/terms/> .\n"
            "@prefix type: <urn:test:type#> .\n\n"
            "<urn:test:dataset/dataset_a> a obdc:EntityDataset ;\n"
            "    obdc:hasDataEntity <urn:test:entity/e1> ;\n"
            '    dcterms:identifier "urn:test:dataset/dataset_a" .\n\n'
            "<urn:test:entity/e1> a type:Thing, obdc:DataEntity ;\n"
            '    dcterms:identifier "GLOBAL-1" .\n',
            encoding="utf-8",
        )
        facade_ttl = dataset_root / ".__ontobdc__" / "linkset" / "facade.ttl"
        facade_ttl.parent.mkdir(parents=True, exist_ok=True)
        facade_ttl.write_text(
            "@prefix : <urn:test:facade#> .\n"
            "@prefix type: <urn:test:type#> .\n"
            "@prefix schema: <http://schema.org/> .\n\n"
            "type:Thing :hasDataEntityFacade :ThingFacade .\n"
            ":ThingFacade :hasFacadeField :WhatField .\n"
            ':WhatField schema:identifier "What" ;\n'
            "    :mapsToProperty <urn:test:type#what> .\n",
            encoding="utf-8",
        )

        capability = DataGatheredCapability()
        context = _fake_context(container_root)

        with patch.object(
            ContainerDataPackageSynchronizer,
            "list_container_file_paths",
            return_value=[],
        ), patch(_DATASET_INSTANCE_REPOSITORY_PATH) as mocked_repository_class:
            mocked_repository_class.return_value.list_instances.side_effect = (
                FileNotFoundError("datapackage.json not found")
            )
            result: Dict[str, Any] = capability.execute(context)

        assert result["dataset_count"] == 1
        written_graph = Graph()
        written_graph.parse(Path(result["state_path"]), format="json-ld")
        entity = URIRef("urn:test:entity/e1")
        assert (entity, DCTERMS.title, None) not in written_graph
        assert (entity, URIRef("urn:test:type#what"), None) not in written_graph
