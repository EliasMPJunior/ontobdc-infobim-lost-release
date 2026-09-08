"""Stub for the entity-view publication transformation capability."""

import importlib
import inspect
import json
import pkgutil
import re
from concurrent.futures import Future, ThreadPoolExecutor, as_completed
from pathlib import Path
from types import ModuleType
from typing import Any, Dict, List, Optional, Tuple, Type

from ontobdc.cli.domain.port.context import CliContextPort
from ontobdc.shared.adapter.capability import TransformationCapability
from ontobdc.shared.domain.model.capability import CapabilityMetadata
from ontobdc.storage.adapter.bootstrap import StorageNamespaceBootstrap
from ontobdc_view.surface.domain.machine.standard_surface_html.state import (
    SurfaceGenerationProcessState,
)
from ontobdc_view.surface.plugin.capability.transformation.data_gathered import (
    DataGatheredCapability,
)

StorageNamespaceBootstrap.initialize()
_OBDC = StorageNamespaceBootstrap.OBDC


class EntityPageGenerationDataTransitionHandler:
    """Base per-element Page-data generator.

    Entity-specific handlers follow the naming convention
    ``<Entity>PageGenerationDataTransitionHandler`` and override
    ``build_payload`` when they have real Page data to materialize. Until
    then the inherited implementation writes a valid, empty JSON-LD object.
    """

    def build_payload(
        self,
        *,
        context: CliContextPort,
        element_uri: str,
        entity_uri: str,
        source_node: Dict[str, Any],
    ) -> Any:
        del context, element_uri, entity_uri, source_node
        return {}

    def execute(
        self,
        *,
        context: CliContextPort,
        element_uri: str,
        entity_uri: str,
        source_node: Dict[str, Any],
        target_path: Path,
    ) -> Path:
        payload: Any = self.build_payload(
            context=context,
            element_uri=element_uri,
            entity_uri=entity_uri,
            source_node=source_node,
        )
        target_path.parent.mkdir(parents=True, exist_ok=True)
        target_path.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        return target_path


class EntityPageGenerationDataTransitionHandlerLoader:
    """Discover the per-entity Page-data handler for an entity type."""

    _HANDLER_PACKAGE_SUFFIX: str = "page.plugin.builder"
    _HANDLER_CLASS_SUFFIX: str = "PageGenerationDataTransitionHandler"

    def __init__(
        self,
        root_packages: Tuple[str, ...] = ("ontobdc_view",),
    ) -> None:
        self._root_packages: Tuple[str, ...] = root_packages

    def get_all(self) -> List[Type[EntityPageGenerationDataTransitionHandler]]:
        handlers: List[Type[EntityPageGenerationDataTransitionHandler]] = []
        for root_package in self._root_packages:
            package_name: str = f"{root_package}.{self._HANDLER_PACKAGE_SUFFIX}"
            package: Optional[ModuleType] = self._import_optional_package(
                package_name
            )
            if package is None:
                continue

            handlers.extend(self._handler_types_from_module(package))
            package_prefix: str = f"{package.__name__}."
            for _, module_name, _ in pkgutil.walk_packages(
                package.__path__,
                package_prefix,
            ):
                module: ModuleType = importlib.import_module(module_name)
                handlers.extend(self._handler_types_from_module(module))

        return sorted(handlers, key=lambda handler: handler.__name__)

    def get(
        self,
        entity_uri: str,
    ) -> Optional[Type[EntityPageGenerationDataTransitionHandler]]:
        expected_name: str = self.handler_class_name(entity_uri)
        matches: List[Type[EntityPageGenerationDataTransitionHandler]] = [
            handler
            for handler in self.get_all()
            if handler.__name__ == expected_name
        ]
        if not matches:
            return None
        if len(matches) > 1:
            raise ValueError(
                "More than one Entity Page generation-data handler was "
                f"discovered for {entity_uri}: {expected_name}"
            )
        return matches[0]

    @classmethod
    def handler_class_name(cls, entity_uri: str) -> str:
        entity_name: str = cls._pascal_case(cls._local_name(entity_uri))
        return f"{entity_name}{cls._HANDLER_CLASS_SUFFIX}"

    @classmethod
    def _handler_types_from_module(
        cls,
        module: ModuleType,
    ) -> List[Type[EntityPageGenerationDataTransitionHandler]]:
        handlers: List[Type[EntityPageGenerationDataTransitionHandler]] = []
        for _, candidate in inspect.getmembers(module, inspect.isclass):
            if candidate is EntityPageGenerationDataTransitionHandler:
                continue
            if candidate.__module__ != module.__name__:
                continue
            try:
                is_handler: bool = issubclass(
                    candidate,
                    EntityPageGenerationDataTransitionHandler,
                )
            except TypeError:
                continue
            if not is_handler:
                continue
            if not candidate.__name__.endswith(cls._HANDLER_CLASS_SUFFIX):
                continue
            handlers.append(candidate)
        return handlers

    @staticmethod
    def _import_optional_package(package_name: str) -> Optional[ModuleType]:
        try:
            return importlib.import_module(package_name)
        except ModuleNotFoundError as error:
            missing_name: str = str(error.name or "")
            if missing_name and (
                package_name == missing_name
                or package_name.startswith(f"{missing_name}.")
            ):
                return None
            raise

    @staticmethod
    def _local_name(uri: str) -> str:
        value: str = str(uri or "").strip()
        if not value:
            raise ValueError("Entity or element URI cannot be empty.")
        if "#" in value:
            return value.rsplit("#", 1)[-1].strip()
        trimmed: str = value.rstrip("/")
        if "/" in trimmed:
            return trimmed.rsplit("/", 1)[-1].strip()
        if ":" in trimmed:
            return trimmed.rsplit(":", 1)[-1].strip()
        return trimmed

    @staticmethod
    def _pascal_case(value: str) -> str:
        parts: List[str] = [
            part for part in re.split(r"[^A-Za-z0-9]+", value) if part
        ]
        result: str = "".join(
            f"{part[:1].upper()}{part[1:]}" for part in parts
        )
        if not result or result[0].isdigit():
            raise ValueError(
                f"Cannot derive a Python handler class name from {value!r}."
            )
        return result


class EntityDataGatheredCapability(TransformationCapability):
    """Placeholder for entity detail-page publication.

    The capability currently restores only the read-side traversal required
    by Page publication: read DATA_GATHERED JSON-LD, identify DataEntity
    elements, group them by their concrete entity type, and dispatch one
    job per (entity type, element) pair on a thread pool, collecting each
    as it completes. Actual Page rendering/publication remains intentionally
    unimplemented -- ``_publish_entity_view`` is the single seam where it
    lands.
    """

    METADATA = CapabilityMetadata(
        id=(
            "org.ontobdc.view.plugin.capability.transformation.target."
            "entity_data_gathered"
        ),
        version="1.0.0",
        name="Entity Data Gathered",
        description=(
            "Enumerate the DATA_GATHERED DataEntity elements and their entity "
            "types for downstream Page publication."
        ),
        author=["http://kb.elias.eng.br/nid/elias.ttl#Elias"],
        tags=["view", "surface", "html", "page", "transformation"],
        supported_languages=["en", "pt-br"],
        log_message={
            "info": {
                "en": "Entity view publication traversal completed.",
            },
            "debug_entry": {
                "en": "Reading entity and element lists from DATA_GATHERED JSON-LD.",
            },
        },
    )

    def __init__(
        self,
        handler_loader: Optional[
            EntityPageGenerationDataTransitionHandlerLoader
        ] = None,
    ) -> None:
        self._handler_loader = (
            handler_loader or EntityPageGenerationDataTransitionHandlerLoader()
        )

    def label(self, lang: str = "en") -> str:
        return SurfaceGenerationProcessState.ENTITY_DATA_GATHERED.label(lang)

    def description(self, lang: str = "en") -> str:
        return SurfaceGenerationProcessState.ENTITY_DATA_GATHERED.description(lang)

    def check(self, context: CliContextPort) -> bool:
        return False

    def execute(self, context: CliContextPort) -> Dict[str, Any]:
        source_path: Path = DataGatheredCapability.state_path(context)
        payload: Any = self._read_data_gathered(context)
        records: List[Dict[str, Any]] = self._list_element_records(payload)
        grouped: Dict[str, List[Dict[str, Any]]] = self._group_elements(records)

        # One job per (concrete entity type, DataEntity element) pair. Each
        # job publishes a single element's detail page and is independent of
        # every other, so they run on a thread pool and are collected as
        # they finish rather than in submission order.
        jobs: List[Tuple[str, str, Dict[str, Any]]] = []
        for entity_uri, elements in grouped.items():
            for record in elements:
                element_uri: str = str(record.get("element") or "").strip()
                if not element_uri:
                    continue
                source_node: Any = record.get("source_node")
                if not isinstance(source_node, dict):
                    raise ValueError(
                        f"Element {element_uri} has no DATA_GATHERED source node."
                    )
                jobs.append((entity_uri, element_uri, source_node))

        published: Dict[str, List[str]] = {
            entity_uri: [] for entity_uri in grouped
        }
        future_element: Dict[Future, Tuple[str, str]] = {}

        with ThreadPoolExecutor() as executor:
            for entity_uri, element_uri, source_node in jobs:
                future: Future = executor.submit(
                    self._publish_entity_view,
                    context=context,
                    entity_uri=entity_uri,
                    element_uri=element_uri,
                    source_node=source_node,
                )
                future_element[future] = (entity_uri, element_uri)

            for future in as_completed(list(future_element)):
                entity_uri, element_uri = future_element[future]
                resulting_uri: str = future.result()
                if resulting_uri != element_uri:
                    raise ValueError(
                        "Entity view publication returned an unexpected "
                        f"element: {resulting_uri} != {element_uri}"
                    )
                published[entity_uri].append(resulting_uri)

        traversed: List[Dict[str, Any]] = [
            {"entity": entity_uri, "elements": sorted(published[entity_uri])}
            for entity_uri in grouped
        ]

        return {
            "source_state_path": str(source_path),
            "entity_count": len(grouped),
            "element_count": len(records),
            "entities": traversed,
            "elements": [
                {
                    "element": str(record["element"]),
                    "entities": list(record["entities"]),
                }
                for record in records
            ],
        }

    def is_satisfied(self, context: CliContextPort) -> bool:
        return False

    def _publish_entity_view(
        self,
        *,
        context: CliContextPort,
        entity_uri: str,
        element_uri: str,
        source_node: Dict[str, Any],
    ) -> str:
        """Publish one entity element's detail page. Runs on a worker thread.

        Page rendering/publication is intentionally unimplemented; for now
        the job only carries the element through the concurrent traversal
        and returns its URI so ``execute`` can reassemble per-entity results.
        """
        handler_type = self._handler_loader.get(entity_uri)
        if handler_type is None:
            return element_uri

        handler_type().execute(
            context=context,
            element_uri=element_uri,
            entity_uri=entity_uri,
            source_node=source_node,
            target_path=self._element_target_path(
                context, entity_uri, element_uri, source_node
            ),
        )

        return element_uri

    @classmethod
    def _element_target_path(
        cls,
        context: CliContextPort,
        entity_uri: str,
        element_uri: str,
        source_node: Dict[str, Any],
    ) -> Path:
        """``<container>/.__ontobdc__/view/<entity>/<identifier>.jsonld``.

        The artifact is named by the element's ``dcterms:identifier`` -- the
        same value the entity tiles build their detail-page links from -- so
        the published ``<identifier>.html`` matches those links. Falls back
        to the element URI's last segment when the node declares none.
        """
        container_path: str = str(
            context.get_parameter_value("container_path") or ""
        ).strip()
        if not container_path:
            raise ValueError("The container path was not resolved.")
        return (
            Path(container_path).expanduser().resolve()
            / ".__ontobdc__"
            / "view"
            / cls._entity_segment(entity_uri)
            / f"{cls._element_identifier(source_node, element_uri)}.jsonld"
        )

    @classmethod
    def _element_identifier(
        cls,
        source_node: Dict[str, Any],
        element_uri: str,
    ) -> str:
        values = source_node.get("http://purl.org/dc/terms/identifier")
        if isinstance(values, list) and values:
            picked = values[0]
            raw = picked.get("@value") if isinstance(picked, dict) else picked
            identifier = re.sub(
                r"[^A-Za-z0-9._-]+", "_", str(raw or "").strip()
            ).strip("._-")
            if identifier:
                return identifier
        return cls._path_segment(element_uri)

    @classmethod
    def _entity_segment(cls, entity_uri: str) -> str:
        local_name: str = (
            EntityPageGenerationDataTransitionHandlerLoader._local_name(entity_uri)
        )
        stepped: str = re.sub(r"(?<=[a-z0-9])(?=[A-Z])", "_", local_name)
        return re.sub(r"[^A-Za-z0-9]+", "_", stepped).strip("_").lower() or "entity"

    @staticmethod
    def _path_segment(uri: str) -> str:
        local_name: str = (
            EntityPageGenerationDataTransitionHandlerLoader._local_name(uri)
        )
        return re.sub(r"[^A-Za-z0-9._-]+", "_", local_name).strip("._-") or "element"

    @staticmethod
    def _read_data_gathered(context: CliContextPort) -> Any:
        path: Path = DataGatheredCapability.state_path(context)
        return json.loads(path.read_text(encoding="utf-8"))

    @classmethod
    def _list_element_records(
        cls,
        payload: Any,
    ) -> List[Dict[str, Any]]:
        nodes: List[Dict[str, Any]] = cls._nodes(payload)
        data_entity_uri: str = str(_OBDC.DataEntity)
        elements: List[Dict[str, Any]] = []

        for node in nodes:
            element_uri: str = str(node.get("@id") or "").strip()
            entity_types: List[str] = cls._types(node)
            if not element_uri or data_entity_uri not in entity_types:
                continue

            entities: List[str] = sorted(
                entity_type
                for entity_type in entity_types
                if entity_type != data_entity_uri
            )
            elements.append(
                {
                    "element": element_uri,
                    "entities": entities,
                    "source_node": node,
                }
            )

        return sorted(elements, key=lambda item: str(item["element"]))

    @staticmethod
    def _group_elements(
        records: List[Dict[str, Any]],
    ) -> Dict[str, List[Dict[str, Any]]]:
        grouped: Dict[str, List[Dict[str, Any]]] = {}
        for record in records:
            for entity_uri in list(record.get("entities") or []):
                normalized_uri: str = str(entity_uri).strip()
                if not normalized_uri:
                    continue
                grouped.setdefault(normalized_uri, []).append(record)

        return {
            entity_uri: sorted(
                elements,
                key=lambda item: str(item.get("element") or ""),
            )
            for entity_uri, elements in sorted(grouped.items())
        }

    @staticmethod
    def _nodes(payload: Any) -> List[Dict[str, Any]]:
        if isinstance(payload, dict):
            graph: Any = payload.get("@graph")
            if isinstance(graph, list):
                return [node for node in graph if isinstance(node, dict)]
            return [payload]
        if isinstance(payload, list):
            return [node for node in payload if isinstance(node, dict)]
        raise ValueError("DATA_GATHERED JSON-LD must be an object or list.")

    @staticmethod
    def _types(node: Dict[str, Any]) -> List[str]:
        raw_types: Any = node.get("@type")
        if isinstance(raw_types, str):
            return [raw_types]
        if isinstance(raw_types, list):
            return [
                str(value).strip()
                for value in raw_types
                if str(value).strip()
            ]
        return []
