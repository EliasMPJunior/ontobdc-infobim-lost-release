from pathlib import Path
from typing import Any, Dict, List, Optional, Set

from ontobdc.shared.adapter.util import is_valid_uri
from rdflib import Graph, Literal, URIRef
from rdflib.namespace import RDF

from ontobdc.cli.domain.port.context import CliContextPort, CliContextStrategyPort
from ontobdc.context.adapter.vector import EntityVectorRepositoryAdapter
from ontobdc.shared.adapter.config import ConfigDataAdapter
from ontobdc.shared.adapter.ontology import OntologyConfigAdapter
from ontobdc.shared.domain.model.parameter import ParameterMetadata
from ontobdc.shared.domain.port.parameter import ParameterPort


class EntityUriStrategy(ParameterPort, CliContextStrategyPort):
    METADATA = ParameterMetadata(
        id="org.ontobdc.domain.context.capability.incoming.entity",
        version="0.1.0",
        name="entity",
        description="Resolve the target entity identifier to a URI reference.",
        author=["http://kb.elias.eng.br/nid/elias.ttl#Elias"],
        python_type=URIRef,
    )

    def execute(self, context: CliContextPort) -> CliContextPort:
        raw_entity_value: str = str(context.get_parameter_value("entity") or "").strip()
        if not raw_entity_value:
            return context

        if self._is_valid_entity_uri(raw_entity_value):
            context.set_parameter_value("entity_uri", URIRef(raw_entity_value))
            return context

        raw_entity_value: str = self._lemmatize(
            raw_entity_value,
            language=str(context.language or "en"),
        )
        if not raw_entity_value:
            return context

        resolved_entity_value: Optional[str] = self._resolve_entity_from_aliases(context, raw_entity_value)
        if not resolved_entity_value:
            return context

        if self._is_valid_entity_uri(resolved_entity_value):
            context.set_parameter_value("entity_uri", URIRef(resolved_entity_value))
            return context

        context.set_parameter_value("entity_uri", resolved_entity_value)

        return context

    @staticmethod
    def _lemmatize(value: str, language: str) -> str:
        """Lemmatize an alias to improve alias matching.

        Lemmatization needs the spaCy stack, which only ships with the
        optional ``ontobdc-a3`` package. When it is not installed the raw
        alias is returned unchanged so entity resolution still works,
        just without morphological normalization.
        """
        if not ConfigDataAdapter.is_a3_installed():
            return value

        from ontobdc_a3.prompt.adapter.lemmatization import to_lemma

        return to_lemma(value, language=language)

    def _is_valid_entity_uri(self, value: str) -> bool:
        normalized_value: str = str(value or "").strip()
        if not normalized_value:
            return False

        if "://" not in normalized_value and not normalized_value.startswith("urn:"):
            return False

        return bool(is_valid_uri(normalized_value))

    def _resolve_entity_from_aliases(
        self,
        context: CliContextPort,
        raw_entity_value: str,
    ) -> Optional[str]:
        entity_candidates: List[Dict[str, Any]] = self._collect_entity_candidates(context)
        if not entity_candidates:
            return None

        if len(entity_candidates) == 1:
            return entity_candidates[0]["entity_uri"]

        raise ValueError(f"Multiple entity candidates found for alias: {raw_entity_value}")

    def _collect_entity_candidates(self, context: CliContextPort) -> List[Dict[str, Any]]:
        # seen_keys: Set[str] = set()
        candidates: List[Dict[str, Any]] = []

        for candidate in self._collect_context_candidates(context) + self._collect_registered_candidates(context):
            candidates.append(candidate)

        return candidates

    def _collect_context_candidates(self, context: CliContextPort) -> List[Dict[str, Any]]:
        config_adapter: ConfigDataAdapter = ConfigDataAdapter()
        ontology_adapter: OntologyConfigAdapter = OntologyConfigAdapter(config_adapter)
        obdc_namespace: Optional[Any] = ontology_adapter.get_ontology_namespace_by_prefix("obdc")
        if obdc_namespace is None:
            return []

        entity_alias: URIRef = obdc_namespace["entityAlias"]

        context_graph: Graph = Graph()
        context_file_path: Path = Path(context.root_path)  / ".__ontobdc__" / "context.ttl"
        context_graph.parse(context_file_path, format="turtle")

        candidates: List[Dict[str, Any]] = []

        for subject in set(context_graph.subjects(entity_alias, None)):
            if is_valid_uri(str(subject)):
                candidates.append(
                    {
                        "entity_uri": str(subject),
                        "entity_ref": subject,
                    }
                )

        return candidates

    def _collect_registered_candidates(self, context: CliContextPort) -> List[Dict[str, Any]]:
        candidates: List[Dict[str, Any]] = []

        return candidates
