import json
from pathlib import Path
from typing import Any, Dict, Iterable, List, Mapping, Set, Tuple
from urllib.parse import quote

from rdflib import Graph, Namespace, RDF

from ontobdc.cli.domain.port.context import CliContextPort
from ontobdc.shared.adapter.capability import TransformationCapability
from ontobdc.shared.domain.model.capability import CapabilityMetadata
from ontobdc_view.page.adapter.context import PageDataContextAdapter


class WorkStreamRelatedEntitiesResolvedCapability(TransformationCapability):
    """Materialize the WorkStream read model consumed by its Entity Page.

    The browser never opens a container folder.  This build-time capability
    therefore folds the DATA_GATHERED JSON-LD graph, the dimension/resource
    linksets and persisted enrichment annotations into the Page JSON-LD.
    """

    _OBDC_NS = "http://ontobdc.org/ontology/domain/ontobdc/ns.ttl#"
    _FILE_TYPES = {
        f"{_OBDC_NS}GenericFile",
        f"{_OBDC_NS}ImageFile",
        f"{_OBDC_NS}PdfFile",
        f"{_OBDC_NS}CsvFile",
    }
    _LS = Namespace("https://standards.iso.org/iso/21597/-1/ed-1/en/Linkset#")

    METADATA = CapabilityMetadata(
        id=(
            "org.ontobdc.view.plugin.capability.transformation.target."
            "work_stream_related_entities_resolved"
        ),
        version="1.0.0",
        name="Related Entities Resolved",
        description="Resolve the entities related to this element.",
        author=["http://kb.elias.eng.br/nid/elias.ttl#Elias"],
        tags=["view", "page", "entity", "transformation"],
        supported_languages=["en", "pt-br"],
        log_message={
            "info": {
                "en": "Entities related to the element were resolved.",
            },
            "debug_entry": {
                "en": "Resolving the entities related to the element.",
            },
        },
    )

    def label(self, lang: str = "en") -> str:
        return "Related Entities Resolved"

    def description(self, lang: str = "en") -> str:
        return self.METADATA.description

    def check(self, context: CliContextPort) -> bool:
        return isinstance(
            PageDataContextAdapter.payload(context).get("related_entities"),
            list,
        )

    def execute(self, context: CliContextPort) -> Dict[str, Any]:
        payload = PageDataContextAdapter.payload(context)
        source_node = PageDataContextAdapter.source_node(context)
        element_uri = PageDataContextAdapter.require_uri(
            context, "page_element_uri"
        )
        container_path = self._container_path(context)
        graph_nodes = (
            self._data_gathered_nodes(context)
            if container_path is not None
            else []
        )
        resources = [
            node
            for node in graph_nodes
            if self._is_resource(node)
        ]
        relations = (
            self._relations(container_path, element_uri)
            if container_path is not None
            else {}
        )
        annotations = (
            self._annotations(container_path, element_uri)
            if container_path is not None
            else []
        )

        # The entity is first by contract so generic JSON-LD consumers can
        # select it deterministically; every resource needed by the read-only
        # trees/previews follows it.
        payload["@graph"] = [dict(source_node), *resources]
        payload["related_entities"] = [
            {
                "dimension": dimension,
                "related": sorted(values.get("related", set())),
                "suggested": sorted(values.get("suggested", set())),
            }
            for dimension, values in sorted(relations.items())
        ]
        payload["annotations"] = annotations
        self._attach_dimension_resources(
            payload,
            resources=resources,
            relations=relations,
            annotations=annotations,
        )
        return {"resulting_state": "__related_entities_resolved__"}

    def is_satisfied(self, context: CliContextPort) -> bool:
        return self.check(context)

    @staticmethod
    def _container_path(context: CliContextPort) -> Path | None:
        value = str(context.get_parameter_value("container_path") or "").strip()
        if not value:
            return None
        return Path(value).expanduser().resolve()

    @staticmethod
    def _data_gathered_nodes(context: CliContextPort) -> List[Dict[str, Any]]:
        from ontobdc_view.surface.plugin.capability.transformation.data_gathered import (
            DataGatheredCapability,
        )

        document = json.loads(
            DataGatheredCapability.state_path(context).read_text(encoding="utf-8")
        )
        if isinstance(document, list):
            return [node for node in document if isinstance(node, dict)]
        if isinstance(document, dict):
            nodes = document.get("@graph")
            if isinstance(nodes, list):
                return [node for node in nodes if isinstance(node, dict)]
            return [document]
        return []

    @classmethod
    def _is_resource(cls, node: Mapping[str, Any]) -> bool:
        raw_types = node.get("@type")
        types = raw_types if isinstance(raw_types, list) else [raw_types]
        return any(str(value) in cls._FILE_TYPES for value in types)

    @classmethod
    def _relations(
        cls, container_path: Path, element_uri: str
    ) -> Dict[str, Dict[str, Set[str]]]:
        result: Dict[str, Dict[str, Set[str]]] = {}
        patterns = {
            "related": "WorkStreamResource.ttl",
            "suggested": "WorkStreamSuggested.ttl",
        }
        for relation_kind, filename in patterns.items():
            for path in cls._unique_paths(container_path.rglob(filename)):
                graph = Graph()
                try:
                    graph.parse(path, format="turtle")
                except Exception:
                    continue
                for link in graph.subjects(RDF.type, cls._LS.DirectedBinaryLink):
                    endpoints = cls._link_endpoints(graph, link)
                    if endpoints is None:
                        continue
                    dimension_uri, resource_uri = endpoints
                    prefix = f"{element_uri}/dimension/"
                    if not dimension_uri.startswith(prefix):
                        continue
                    dimension = dimension_uri[len(prefix):].replace("-", "_")
                    bucket = result.setdefault(
                        dimension,
                        {"related": set(), "suggested": set()},
                    )
                    bucket[relation_kind].add(resource_uri)
        return result

    @classmethod
    def _link_endpoints(
        cls, graph: Graph, link: Any
    ) -> Tuple[str, str] | None:
        values: List[str] = []
        for predicate in (cls._LS.hasFromLinkElement, cls._LS.hasToLinkElement):
            element = graph.value(link, predicate)
            identifier = graph.value(element, cls._LS.hasIdentifier)
            value = graph.value(identifier, cls._LS.uri) or graph.value(
                identifier, cls._LS.identifier
            )
            if value is None:
                return None
            values.append(str(value))
        return values[0], values[1]

    @classmethod
    def _annotations(
        cls, container_path: Path, element_uri: str
    ) -> List[Dict[str, Any]]:
        collected: Dict[str, Dict[str, Any]] = {}
        for path in cls._unique_paths(container_path.rglob("EnrichmentAnnotation.ttl")):
            graph = Graph()
            try:
                graph.parse(path, format="turtle")
            except Exception:
                continue
            for subject, predicate, value in graph:
                if cls._local_name(str(predicate)) != "payload":
                    continue
                try:
                    annotation = json.loads(str(value))
                except (TypeError, ValueError):
                    continue
                if not isinstance(annotation, dict):
                    continue
                if not str(annotation.get("relatedDimension") or "").startswith(
                    f"{element_uri}/dimension/"
                ):
                    continue
                identifier = str(annotation.get("id") or subject)
                collected[identifier] = annotation
        return [collected[key] for key in sorted(collected)]

    @classmethod
    def _attach_dimension_resources(
        cls,
        payload: Dict[str, Any],
        *,
        resources: List[Dict[str, Any]],
        relations: Dict[str, Dict[str, Set[str]]],
        annotations: List[Dict[str, Any]],
    ) -> None:
        resource_models = {
            str(node.get("@id") or ""): cls._resource_model(node, annotations)
            for node in resources
            if str(node.get("@id") or "").strip()
        }
        relation_by_key = {
            cls._key(dimension): values
            for dimension, values in relations.items()
        }
        found = sorted(resource_models.values(), key=lambda item: item["path"])
        for dimension in payload.get("dimensions", []):
            if not isinstance(dimension, dict):
                continue
            values = relation_by_key.get(
                cls._key(str(dimension.get("kind") or "")),
                {"related": set(), "suggested": set()},
            )
            related_ids = values.get("related", set())
            suggested_ids = values.get("suggested", set()) - related_ids
            dimension["related_resources"] = [
                resource_models[identifier]
                for identifier in sorted(related_ids)
                if identifier in resource_models
            ]
            dimension["suggested_resources"] = [
                resource_models[identifier]
                for identifier in sorted(suggested_ids)
                if identifier in resource_models
            ]
            dimension["found_resources"] = found

    @classmethod
    def _resource_model(
        cls,
        node: Mapping[str, Any],
        annotations: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        identifier = str(node.get("@id") or "")
        path = cls._literal(node, f"{cls._OBDC_NS}filePath")
        title = (
            cls._literal(node, "http://purl.org/dc/terms/title")
            or Path(path).name
            or identifier
        )
        raw_types = node.get("@type")
        types = raw_types if isinstance(raw_types, list) else [raw_types]
        if f"{cls._OBDC_NS}ImageFile" in types:
            kind = "image"
            category = "photos"
        elif f"{cls._OBDC_NS}PdfFile" in types:
            kind = "pdf"
            category = "documents"
        elif f"{cls._OBDC_NS}CsvFile" in types:
            kind = "csv"
            category = "documents"
        else:
            kind = "generic"
            category = "drawings" if Path(path).suffix.lower() in {
                ".dwg", ".dxf", ".ifc"
            } else "documents"
        return {
            "id": identifier,
            "title": title,
            "path": path,
            "href": f"../../../{quote(path, safe='/')}" if path else "",
            "kind": kind,
            "category": category,
            "annotations": [
                annotation
                for annotation in annotations
                if str(annotation.get("logicalSource") or "") == identifier
                or str(annotation.get("representationSource") or "") == identifier
            ],
        }

    @staticmethod
    def _literal(node: Mapping[str, Any], predicate: str) -> str:
        values = node.get(predicate)
        picked = values[0] if isinstance(values, list) and values else values
        if isinstance(picked, dict):
            return str(picked.get("@value") or picked.get("@id") or "").strip()
        return str(picked or "").strip()

    @staticmethod
    def _key(value: str) -> str:
        return "".join(character for character in value.lower() if character.isalnum())

    @staticmethod
    def _unique_paths(paths: Iterable[Path]) -> List[Path]:
        return sorted({path.resolve() for path in paths if path.is_file()})

    @staticmethod
    def _local_name(uri: str) -> str:
        return uri.rsplit("#", 1)[-1].rstrip("/").rsplit("/", 1)[-1]
