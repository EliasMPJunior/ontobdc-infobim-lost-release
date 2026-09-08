from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List

from rdflib import Graph, URIRef

from ontobdc.cli.domain.port.context import CliContextPort
from ontobdc.storage.adapter.bootstrap import StorageBootstrap


class FacadeLookupAdapter:
    """Locate every Facade a dataset declares for an entity type.

    A dataset materializes its own `facade.ttl` (`hasDataEntityFacade` /
    `hasFacadeField` / `mapsToProperty` triples) at entity-creation time —
    see `ContextEntityCommand`. `DataGatheredCapability._resolve_facade_fields`
    already walks this same file, but only reads `facade_subjects[0]`: it
    assumes one Facade per entity type. This adapter makes no such
    assumption and returns every declared Facade, since resolving them all
    is now its own dedicated step in the Page-data builder statechart.
    """

    @classmethod
    def locate_facades_for_element(
        cls,
        context: CliContextPort,
        element_uri: str,
        entity_type_uri: str,
    ) -> List[Dict[str, Any]]:
        dataset_path = cls._resolve_dataset_path(context, element_uri)
        if dataset_path is None:
            return []

        facade_file = StorageBootstrap.get_ontobdc_directory(dataset_path) / "linkset" / "facade.ttl"
        if not facade_file.is_file():
            return []

        graph = Graph()
        try:
            graph.parse(str(facade_file), format="turtle")
        except Exception:
            return []

        entity_type = URIRef(entity_type_uri)
        facade_subjects: List[URIRef] = [
            obj
            for _, predicate, obj in graph.triples((entity_type, None, None))
            if isinstance(obj, URIRef) and cls._local_name(predicate) == "hasDataEntityFacade"
        ]

        return [
            {
                "facade": str(facade_subject),
                "fields": cls._facade_fields(graph, facade_subject),
            }
            for facade_subject in facade_subjects
        ]

    @classmethod
    def _facade_fields(cls, graph: Graph, facade_subject: URIRef) -> List[Dict[str, Any]]:
        fields: List[Dict[str, Any]] = []
        for _, predicate, field_subject in graph.triples((facade_subject, None, None)):
            if cls._local_name(predicate) != "hasFacadeField" or not isinstance(field_subject, URIRef):
                continue

            identifier: Any = None
            mapped_property: Any = None
            for _, field_predicate, obj in graph.triples((field_subject, None, None)):
                local_name = cls._local_name(field_predicate)
                if local_name == "identifier":
                    identifier = obj
                elif local_name == "mapsToProperty" and isinstance(obj, URIRef):
                    mapped_property = obj

            if identifier is None or mapped_property is None:
                continue
            fields.append(
                {"name": str(identifier).strip(), "mapped_property": str(mapped_property)}
            )
        return fields

    @staticmethod
    def _resolve_dataset_path(context: CliContextPort, element_uri: str) -> Path | None:
        container_path = str(context.get_parameter_value("container_path") or "").strip()
        if not container_path:
            return None

        # Same convention as WorkstreamPayloadAdapter/GanttPayloadAdapter:
        # the dataset folder is the element URI's second-to-last segment
        # (the element sits directly under its dataset's own root).
        segments = [segment for segment in str(element_uri or "").split("/") if segment]
        if len(segments) < 2:
            return None

        return Path(container_path).expanduser().resolve() / segments[-2]

    @staticmethod
    def _local_name(predicate: Any) -> str:
        value = str(predicate).strip()
        if "#" in value:
            return value.rsplit("#", 1)[-1].strip()
        return value.rstrip("/").rsplit("/", 1)[-1].strip()
