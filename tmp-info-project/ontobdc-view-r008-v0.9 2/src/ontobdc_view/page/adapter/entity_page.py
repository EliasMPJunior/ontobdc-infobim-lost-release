from __future__ import annotations

import json
from functools import lru_cache
from typing import Any, Dict, Optional

from rdflib import BNode, Graph, Literal, Namespace, URIRef
from rdflib.namespace import DCTERMS, RDF, RDFS, SDO


VIEW = Namespace("http://datacenter.app.br/ontology/ontobdc/domain/view.ttl#")

_TOOLBAR_CONFIGURATION_RELATIONS = {
    VIEW.hasToolbarAlignment,
    VIEW.hasToolbarItemPlacement,
    VIEW.placesComponent,
    VIEW.hasAlignment,
    VIEW.hasRequest,
    VIEW.hasSupportProfile,
}


@lru_cache(maxsize=1)
def _packaged_ontology_graph() -> Graph:
    """Load the packaged ontology catalog once for Entity Page resolution."""
    from brasidatacenter.resources import iter_ontology_files

    graph = Graph()
    for resource in iter_ontology_files((".ttl",)):
        with resource.open("rb") as stream:
            graph.parse(file=stream, format="turtle")
    return graph


class EntityPageOntologyAdapter:
    """Resolve Entity Page definitions and localized entity-class labels."""

    def __init__(self, graph: Optional[Graph] = None) -> None:
        self._graph = graph

    @property
    def graph(self) -> Graph:
        return self._graph if self._graph is not None else _packaged_ontology_graph()

    def entity_title(self, view_directory: str, language: str) -> str:
        page = self._page_for_directory(view_directory)
        entity_types = list(self.graph.objects(page, VIEW.presentsEntityType))
        if len(entity_types) != 1:
            raise ValueError(
                f"Entity Page {page} must declare exactly one "
                "view:presentsEntityType."
            )

        labels = [
            value
            for value in self.graph.objects(entity_types[0], RDFS.label)
            if isinstance(value, Literal)
        ]
        picked = self._localized_literal(labels, language)
        if picked is None:
            raise ValueError(
                f"Entity type {entity_types[0]} has no rdfs:label."
            )
        return str(picked)

    def localized_entity_titles(self, view_directory: str) -> Dict[str, str]:
        return {
            language: self.entity_title(view_directory, language)
            for language in ("en", "pt-BR", "pt-PT", "es")
        }

    def toolbar_configuration(self, entity_uri: str) -> Dict[str, Any]:
        """Return the Entity Page toolbar as a deterministic JSON-LD graph."""
        page = self._page_for_entity_type(entity_uri)
        toolbars = {
            subject
            for subject in self.graph.subjects(DCTERMS.isPartOf, page)
            if (subject, RDF.type, VIEW.EntityPageToolbar) in self.graph
        }
        if len(toolbars) != 1:
            raise ValueError(
                f"Entity Page {page} must declare exactly one "
                f"view:EntityPageToolbar; found {len(toolbars)}."
            )

        configuration = Graph()
        pending = [next(iter(toolbars))]
        visited = set()
        while pending:
            subject = pending.pop()
            if subject in visited:
                continue
            visited.add(subject)
            for triple in self.graph.triples((subject, None, None)):
                configuration.add(triple)
                _, predicate, value = triple
                if (
                    predicate in _TOOLBAR_CONFIGURATION_RELATIONS
                    and isinstance(value, (URIRef, BNode))
                ):
                    pending.append(value)

        serialized = json.loads(
            configuration.serialize(format="json-ld", ensure_ascii=False)
        )
        nodes = (
            serialized.get("@graph", [])
            if isinstance(serialized, dict)
            else serialized
        )
        return {"@graph": self._canonicalize(nodes)}

    def _page_for_directory(self, view_directory: str):
        matches = {
            subject
            for subject, identifier in self.graph.subject_objects(SDO.identifier)
            if str(identifier).strip() == str(view_directory).strip()
            and (subject, None, None) in self.graph
            and (subject, VIEW.presentsEntityType, None) in self.graph
        }
        if len(matches) != 1:
            raise ValueError(
                f"Expected exactly one Entity Page definition for "
                f"{view_directory!r}; found {len(matches)}."
            )
        return next(iter(matches))

    def _page_for_entity_type(self, entity_uri: str):
        entity_type = URIRef(str(entity_uri).strip())
        if not str(entity_type):
            raise ValueError("The entity type URI is required.")
        matches = set(self.graph.subjects(VIEW.presentsEntityType, entity_type))
        if len(matches) != 1:
            raise ValueError(
                f"Expected exactly one Entity Page for entity type "
                f"{entity_uri!r}; found {len(matches)}."
            )
        return next(iter(matches))

    @classmethod
    def _canonicalize(cls, value: Any) -> Any:
        if isinstance(value, dict):
            return {
                key: cls._canonicalize(item)
                for key, item in sorted(value.items())
            }
        if isinstance(value, list):
            items = [cls._canonicalize(item) for item in value]
            return sorted(
                items,
                key=lambda item: json.dumps(
                    item,
                    ensure_ascii=False,
                    sort_keys=True,
                ),
            )
        return value

    @staticmethod
    def _localized_literal(
        labels: list[Literal],
        language: str,
    ) -> Optional[Literal]:
        if not labels:
            return None

        requested = str(language or "en").replace("_", "-").lower()
        base = requested.split("-", 1)[0]
        preferences = (
            lambda tag: tag == requested,
            lambda tag: tag.split("-", 1)[0] == base,
            lambda tag: tag == "en",
            lambda tag: not tag,
        )
        for matches in preferences:
            for label in labels:
                if matches(str(label.language or "").lower()):
                    return label
        return sorted(labels, key=str)[0]
