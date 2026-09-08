from pathlib import Path
from typing import Any, Dict, List, Optional
from urllib.parse import unquote, urlparse
from urllib.request import url2pathname

from rdflib import Graph, Literal, Namespace, URIRef
from rdflib.namespace import DCTERMS, PROV, RDF

from ontobdc.context.adapter.dataset_instance import (
    DatasetEntityInstanceRepository,
)
from ontobdc.context.adapter.instance_support import (
    EntityInstanceRepositorySupport,
)
from ontobdc.storage.adapter.bootstrap import (
    get_container_storage_file_path,
    get_dataset_storage_file_path,
    get_ontobdc_directory,
)


OBDC: Namespace = Namespace(
    "http://ontobdc.org/ontology/domain/ontobdc/ns.ttl#"
)
FACADE_FILE_NAME: str = "facade.ttl"
LINKSET_DIRECTORY_NAME: str = "linkset"


class ContainerEntityInstanceRepository(EntityInstanceRepositorySupport):
    """Read Entity instances and Element identities inside one Container."""

    def __init__(self, *, container_path: str, entity: str = "") -> None:
        self._container_path: Path = Path(
            container_path
        ).expanduser().resolve()
        self._entity: str = str(entity or "").strip()

    @property
    def container_path(self) -> Path:
        return self._container_path

    @property
    def container_metadata_path(self) -> Path:
        return get_container_storage_file_path(self._container_path)

    @property
    def entity(self) -> str:
        return self._entity

    def list_instances(self) -> Dict[str, Any]:
        """List facade-projected instances of the selected Entity."""
        if not self._entity:
            raise ValueError("Entity reference is required.")

        container_graph: Graph = self._load_container_graph()
        container_subject: URIRef = self._resolve_container_subject(
            container_graph
        )
        dataset_subjects: List[URIRef] = self._resolve_dataset_subjects(
            container_graph=container_graph,
            container_subject=container_subject,
        )

        datasets: List[Dict[str, Any]] = []
        instances: List[Dict[str, Any]] = []
        resolved_entity_uri: str = ""
        resolved_entity_name: str = self._entity

        for dataset_subject in dataset_subjects:
            dataset_path: Path = self._resolve_dataset_path(
                container_graph=container_graph,
                dataset_subject=dataset_subject,
            )
            facade: Optional[Dict[str, Any]] = self._resolve_dataset_facade(
                dataset_path=dataset_path,
            )
            if facade is None:
                continue

            dataset_repository: DatasetEntityInstanceRepository = (
                self._build_dataset_repository(
                    dataset_path=dataset_path,
                    entity_uri=str(facade["entity_uri"]),
                )
            )
            dataset_payload: Dict[str, Any] = (
                dataset_repository.list_instances()
            )
            projected_instances: List[Dict[str, Any]] = (
                self._project_instances(
                    instances=list(dataset_payload["instances"]),
                    fields=list(facade["fields"]),
                )
            )
            instances.extend(projected_instances)
            datasets.append(
                self._build_dataset_summary(
                    dataset_subject=dataset_subject,
                    dataset_path=dataset_path,
                    facade=facade,
                    instance_count=len(projected_instances),
                )
            )

            if not resolved_entity_uri:
                resolved_entity_uri = str(facade["entity_uri"])
                resolved_entity_name = str(facade["entity_name"])

        return {
            "container_uri": str(container_subject),
            "container_path": str(self._container_path),
            "entity": resolved_entity_name,
            "entity_uri": resolved_entity_uri,
            "resolution": "container_dataset_facade",
            "dataset_count": len(datasets),
            "datasets": datasets,
            "instance_count": len(instances),
            "instances": instances,
        }

    def get_instance(self, global_id: str) -> Dict[str, Any]:
        """Resolve exactly one projected Entity instance by GlobalId."""
        requested_global_id: str = str(global_id or "").strip()
        if not requested_global_id:
            raise ValueError("GlobalId is required.")
        if not self._entity:
            raise ValueError("Entity reference is required.")

        payload: Dict[str, Any] = self.list_instances()
        matches: List[Dict[str, Any]] = []
        for instance in list(payload.get("instances") or []):
            if not isinstance(instance, dict):
                continue
            value: str = self._mapping_value(
                instance,
                "GlobalId",
                "global_id",
            )
            if value == requested_global_id:
                matches.append(dict(instance))

        if not matches:
            raise ValueError(
                f"Could not resolve entity '{self._entity}' with GlobalId "
                f"'{requested_global_id}'."
            )
        if len(matches) != 1:
            raise ValueError(
                f"GlobalId '{requested_global_id}' resolves to multiple "
                f"'{self._entity}' instances."
            )
        return matches[0]

    def list_elements(self) -> List[Dict[str, Any]]:
        """List canonical Element identities in the selected Container.

        Identity is read from dataset RDF metadata, not from Facade projection.
        `dcterms:identifier` is the persisted GlobalId of an `obdc:DataEntity`.
        No URI-local-name, title, or nearest-match fallback is permitted.
        """
        container_graph: Graph = self._load_container_graph()
        container_subject: URIRef = self._resolve_container_subject(
            container_graph
        )
        dataset_subjects: List[URIRef] = self._resolve_dataset_subjects(
            container_graph=container_graph,
            container_subject=container_subject,
        )

        elements: List[Dict[str, Any]] = []
        for dataset_subject in dataset_subjects:
            dataset_path: Path = self._resolve_dataset_path(
                container_graph=container_graph,
                dataset_subject=dataset_subject,
            )
            dataset_graph: Graph = self._load_turtle_graph(
                file_path=get_dataset_storage_file_path(dataset_path),
                label="dataset metadata",
            )
            facade: Optional[Dict[str, Any]] = self._resolve_dataset_facade(
                dataset_path=dataset_path,
            )
            dataset_id: str = self._single_literal_value(
                graph=container_graph,
                subject=dataset_subject,
                predicate=DCTERMS.identifier,
                required=False,
            )
            dataset_title, _ = self._title_with_language(
                container_graph,
                dataset_subject,
            )

            for subject in dataset_graph.subjects(RDF.type, OBDC.DataEntity):
                if not isinstance(subject, URIRef):
                    continue

                global_id: str = self._single_literal_value(
                    graph=dataset_graph,
                    subject=subject,
                    predicate=DCTERMS.identifier,
                    required=True,
                    label="Element GlobalId",
                )
                entity_types: List[URIRef] = [
                    entity_type
                    for entity_type in dataset_graph.objects(subject, RDF.type)
                    if isinstance(entity_type, URIRef)
                    and entity_type != OBDC.DataEntity
                ]
                if self._entity and not self._element_matches_entity(
                    entity_types=entity_types,
                    facade=facade,
                ):
                    continue

                entity_uri: str = self._element_entity_uri(
                    entity_types=entity_types,
                    facade=facade,
                )
                title, language = self._title_with_language(
                    dataset_graph,
                    subject,
                )
                facade_uri: str = (
                    str(facade.get("facade_uri") or "").strip()
                    if facade is not None
                    else self._first_uri_value(
                        graph=dataset_graph,
                        subject=subject,
                        predicate=DCTERMS.conformsTo,
                    )
                )

                elements.append(
                    {
                        "id": global_id,
                        "global_id": global_id,
                        "iri": str(subject),
                        "title": title,
                        "language": language,
                        "entity_uri": entity_uri,
                        "entity_identifier": (
                            self._snake_case(self._local_name(entity_uri))
                            if entity_uri
                            else ""
                        ),
                        "entity_types": [
                            str(entity_type)
                            for entity_type in entity_types
                        ],
                        "facade_uri": facade_uri,
                        "facade_identifier": (
                            self._local_name(facade_uri)
                            if facade_uri
                            else ""
                        ),
                        "facade_name": (
                            self._local_name(facade_uri)
                            if facade_uri
                            else ""
                        ),
                        "dataset_path": str(dataset_path),
                        "source_dataset_id": (
                            dataset_id or self._local_name(dataset_subject)
                        ),
                        "source_dataset_title": dataset_title,
                        "source_kind": "dataset_metadata",
                    }
                )

        elements.sort(
            key=lambda element: (
                str(element.get("source_dataset_id") or ""),
                str(element.get("entity_identifier") or ""),
                str(element.get("global_id") or ""),
                str(element.get("iri") or ""),
            )
        )
        return elements

    def get_element(self, global_id: str) -> Dict[str, Any]:
        """Resolve exactly one Element by GlobalId in this Container."""
        requested_global_id: str = str(global_id or "").strip()
        if not requested_global_id:
            raise ValueError("GlobalId is required.")

        matches: List[Dict[str, Any]] = [
            element
            for element in self.list_elements()
            if str(element.get("global_id") or "").strip()
            == requested_global_id
        ]
        if not matches:
            raise ValueError(
                f"Could not resolve Element with GlobalId "
                f"'{requested_global_id}' in container "
                f"'{self._container_path}'."
            )
        if len(matches) != 1:
            raise ValueError(
                f"GlobalId '{requested_global_id}' resolves to multiple "
                f"Elements in container '{self._container_path}'."
            )
        return dict(matches[0])

    def _load_container_graph(self) -> Graph:
        return self._load_turtle_graph(
            file_path=self.container_metadata_path,
            label="container metadata",
        )

    def _resolve_container_subject(
        self,
        container_graph: Graph,
    ) -> URIRef:
        subjects: List[URIRef] = [
            subject
            for subject in container_graph.subjects(
                RDF.type,
                OBDC.DataContainer,
            )
            if isinstance(subject, URIRef)
        ]
        if len(subjects) != 1:
            raise ValueError(
                "Container metadata must declare exactly one DataContainer: "
                f"{self.container_metadata_path}"
            )
        return subjects[0]

    def _resolve_dataset_subjects(
        self,
        *,
        container_graph: Graph,
        container_subject: URIRef,
    ) -> List[URIRef]:
        return [
            dataset_subject
            for dataset_subject in container_graph.objects(
                container_subject,
                OBDC.hasEntityDataset,
            )
            if isinstance(dataset_subject, URIRef)
            and (
                dataset_subject,
                RDF.type,
                OBDC.EntityDataset,
            ) in container_graph
        ]

    def _resolve_dataset_path(
        self,
        *,
        container_graph: Graph,
        dataset_subject: URIRef,
    ) -> Path:
        locations: List[Any] = list(
            container_graph.objects(dataset_subject, PROV.atLocation)
        )
        if len(locations) != 1:
            raise ValueError(
                f"Dataset '{dataset_subject}' must expose exactly one "
                "prov:atLocation in the container metadata."
            )
        return self._location_to_path(locations[0])

    def _location_to_path(self, location: Any) -> Path:
        raw_location: str = str(location or "").strip()
        if not raw_location:
            raise ValueError("Dataset location cannot be empty.")

        parsed = urlparse(raw_location)
        if parsed.scheme == "file":
            return Path(
                url2pathname(unquote(parsed.path))
            ).expanduser().resolve()

        location_path: Path = Path(raw_location).expanduser()
        if not location_path.is_absolute():
            location_path = self._container_path / location_path
        return location_path.resolve()

    def _build_dataset_repository(
        self,
        *,
        dataset_path: Path,
        entity_uri: str,
    ) -> DatasetEntityInstanceRepository:
        return DatasetEntityInstanceRepository(
            dataset_path=str(dataset_path),
            entity=entity_uri,
        )

    def _resolve_dataset_facade(
        self,
        *,
        dataset_path: Path,
    ) -> Optional[Dict[str, Any]]:
        facade_path: Path = self._resolve_facade_path(dataset_path)
        if not facade_path.is_file():
            return None
        facade_graph: Graph = self._load_turtle_graph(
            file_path=facade_path,
            label="dataset facade",
        )
        return self._find_entity_facade(
            facade_graph=facade_graph,
            facade_path=facade_path,
        )

    def _resolve_facade_path(self, dataset_path: Path) -> Path:
        return (
            get_ontobdc_directory(dataset_path)
            / LINKSET_DIRECTORY_NAME
            / FACADE_FILE_NAME
        )

    def _find_entity_facade(
        self,
        *,
        facade_graph: Graph,
        facade_path: Path,
    ) -> Optional[Dict[str, Any]]:
        for entity_subject, predicate, facade_subject in facade_graph:
            if self._local_name(predicate) != "hasDataEntityFacade":
                continue
            if self._entity and not self._references_match(
                self._entity,
                entity_subject,
            ):
                continue
            if not isinstance(facade_subject, URIRef):
                continue

            fields: List[Dict[str, Any]] = self._resolve_facade_fields(
                facade_graph=facade_graph,
                facade_subject=facade_subject,
            )
            if not fields:
                continue
            return {
                "entity_uri": str(entity_subject),
                "entity_name": self._local_name(entity_subject),
                "entity_identifier": self._snake_case(
                    self._local_name(entity_subject)
                ),
                "facade_uri": str(facade_subject),
                "facade_path": str(facade_path),
                "fields": fields,
            }
        return None

    def _resolve_facade_fields(
        self,
        *,
        facade_graph: Graph,
        facade_subject: URIRef,
    ) -> List[Dict[str, Any]]:
        fields: List[Dict[str, Any]] = []
        for _, predicate, field_subject in facade_graph.triples(
            (facade_subject, None, None)
        ):
            if self._local_name(predicate) != "hasFacadeField":
                continue
            if not isinstance(field_subject, URIRef):
                continue

            field: Optional[Dict[str, Any]] = self._resolve_facade_field(
                facade_graph=facade_graph,
                field_subject=field_subject,
            )
            if field is not None:
                fields.append(field)
        fields.sort(key=self._facade_field_sort_key)
        return fields

    def _resolve_facade_field(
        self,
        *,
        facade_graph: Graph,
        field_subject: URIRef,
    ) -> Optional[Dict[str, Any]]:
        identifier: Optional[Literal] = self._first_literal_by_local_name(
            graph=facade_graph,
            subject=field_subject,
            local_name="identifier",
        )
        if identifier is None:
            return None

        mapped_property: Optional[URIRef] = self._first_uri_by_local_name(
            graph=facade_graph,
            subject=field_subject,
            local_name="mapsToProperty",
        )
        identifier_value: str = str(identifier).strip()
        return {
            "identifier": identifier_value,
            "name": self._column_name(identifier_value),
            "mapped_property": (
                str(mapped_property)
                if mapped_property is not None
                else ""
            ),
        }

    def _first_literal_by_local_name(
        self,
        *,
        graph: Graph,
        subject: URIRef,
        local_name: str,
    ) -> Optional[Literal]:
        for _, predicate, value in graph.triples((subject, None, None)):
            if (
                self._local_name(predicate) == local_name
                and isinstance(value, Literal)
            ):
                return value
        return None

    def _first_uri_by_local_name(
        self,
        *,
        graph: Graph,
        subject: URIRef,
        local_name: str,
    ) -> Optional[URIRef]:
        for _, predicate, value in graph.triples((subject, None, None)):
            if (
                self._local_name(predicate) == local_name
                and isinstance(value, URIRef)
            ):
                return value
        return None

    def _facade_field_sort_key(
        self,
        field: Dict[str, Any],
    ) -> tuple[int, str]:
        identifier: str = str(field.get("identifier") or "")
        normalized_identifier: str = self._normalized_reference(identifier)
        if normalized_identifier == "globalid":
            return 0, identifier
        if normalized_identifier == "name":
            return 1, identifier
        return 2, identifier

    def _project_instances(
        self,
        *,
        instances: List[Dict[str, Any]],
        fields: List[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        return [
            self._project_instance(instance=instance, fields=fields)
            for instance in instances
        ]

    def _project_instance(
        self,
        *,
        instance: Dict[str, Any],
        fields: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        projected: Dict[str, Any] = {}
        for field in fields:
            source_key: Optional[str] = self._resolve_instance_field_key(
                instance=instance,
                field=field,
            )
            if source_key is not None:
                projected[str(field["name"])] = instance[source_key]
        return projected

    def _resolve_instance_field_key(
        self,
        *,
        instance: Dict[str, Any],
        field: Dict[str, Any],
    ) -> Optional[str]:
        candidates: List[str] = self._field_key_candidates(field)
        for candidate in candidates:
            if candidate in instance:
                return candidate

        normalized_keys: Dict[str, str] = {
            self._normalized_reference(key): str(key)
            for key in instance
        }
        for candidate in candidates:
            normalized_candidate: str = self._normalized_reference(candidate)
            if normalized_candidate in normalized_keys:
                return normalized_keys[normalized_candidate]
        return None

    def _field_key_candidates(
        self,
        field: Dict[str, Any],
    ) -> List[str]:
        candidates: List[str] = []
        for value in (
            field.get("name"),
            field.get("identifier"),
            self._local_name(field.get("mapped_property")),
        ):
            candidate: str = str(value or "").strip()
            if candidate and candidate not in candidates:
                candidates.append(candidate)
        return candidates

    def _mapping_value(
        self,
        mapping: Dict[str, Any],
        *candidates: str,
    ) -> str:
        for candidate in candidates:
            if candidate in mapping:
                return str(mapping[candidate] or "").strip()
        normalized_keys: Dict[str, str] = {
            self._normalized_reference(key): str(key)
            for key in mapping
        }
        for candidate in candidates:
            source_key: Optional[str] = normalized_keys.get(
                self._normalized_reference(candidate)
            )
            if source_key is not None:
                return str(mapping[source_key] or "").strip()
        return ""

    def _element_matches_entity(
        self,
        *,
        entity_types: List[URIRef],
        facade: Optional[Dict[str, Any]],
    ) -> bool:
        if not self._entity:
            return True
        if any(
            self._references_match(self._entity, entity_type)
            for entity_type in entity_types
        ):
            return True
        if facade is None:
            return False
        return self._references_match(
            self._entity,
            facade.get("entity_uri"),
        )

    def _element_entity_uri(
        self,
        *,
        entity_types: List[URIRef],
        facade: Optional[Dict[str, Any]],
    ) -> str:
        if facade is not None:
            facade_entity_uri: str = str(
                facade.get("entity_uri") or ""
            ).strip()
            if facade_entity_uri:
                return facade_entity_uri

        if self._entity:
            matches: List[URIRef] = [
                entity_type
                for entity_type in entity_types
                if self._references_match(self._entity, entity_type)
            ]
            if len(matches) == 1:
                return str(matches[0])
        if len(entity_types) == 1:
            return str(entity_types[0])
        return ""

    def _single_literal_value(
        self,
        *,
        graph: Graph,
        subject: URIRef,
        predicate: URIRef,
        required: bool,
        label: str = "identifier",
    ) -> str:
        values: List[str] = [
            str(value).strip()
            for value in graph.objects(subject, predicate)
            if isinstance(value, Literal) and str(value).strip()
        ]
        if len(values) > 1:
            raise ValueError(
                f"{label} must have exactly one value for '{subject}'."
            )
        if not values:
            if required:
                raise ValueError(
                    f"{label} is required for '{subject}'."
                )
            return ""
        return values[0]

    def _first_uri_value(
        self,
        *,
        graph: Graph,
        subject: URIRef,
        predicate: URIRef,
    ) -> str:
        values: List[str] = sorted(
            {
                str(value).strip()
                for value in graph.objects(subject, predicate)
                if isinstance(value, URIRef) and str(value).strip()
            }
        )
        return values[0] if values else ""

    def _title_with_language(
        self,
        graph: Graph,
        subject: URIRef,
    ) -> tuple[str, str]:
        preferred_pt: str = ""
        preferred_en: str = ""
        default_value: str = ""
        default_language: str = ""
        for value in graph.objects(subject, DCTERMS.title):
            if not isinstance(value, Literal):
                continue
            text: str = str(value).strip()
            if not text:
                continue
            language: str = str(value.language or "").strip()
            normalized_language: str = language.lower()
            if normalized_language in {"pt", "pt-br"} and not preferred_pt:
                preferred_pt = text
            elif normalized_language.startswith("en") and not preferred_en:
                preferred_en = text
            if not default_value:
                default_value = text
                default_language = language

        if preferred_pt:
            return preferred_pt, "pt-BR"
        if preferred_en:
            return preferred_en, "en"
        if default_value:
            return default_value, default_language or "und"
        return "", "und"

    def _build_dataset_summary(
        self,
        *,
        dataset_subject: URIRef,
        dataset_path: Path,
        facade: Dict[str, Any],
        instance_count: int,
    ) -> Dict[str, Any]:
        return {
            "dataset_uri": str(dataset_subject),
            "dataset_path": str(dataset_path),
            "facade_uri": str(facade["facade_uri"]),
            "facade_path": str(facade["facade_path"]),
            "instance_count": instance_count,
        }
