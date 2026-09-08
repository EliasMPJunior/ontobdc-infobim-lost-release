import hashlib
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
from ontobdc.shared.adapter.filesystem import FilesystemAdapter


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
    """Discover entity Page-data handlers and execute one Future per element."""

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
            package_name: str = (
                f"{root_package}.{self._HANDLER_PACKAGE_SUFFIX}"
            )
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

    def execute(
        self,
        *,
        context: CliContextPort,
        grouped_elements: Dict[str, List[Dict[str, Any]]],
        target_directory: Path,
    ) -> Dict[str, List[str]]:
        if not grouped_elements:
            if target_directory.is_dir():
                FilesystemAdapter.remove_directory_tree(target_directory)
            return {}

        handler_types: Dict[
            str,
            Type[EntityPageGenerationDataTransitionHandler],
        ] = {}
        for entity_uri in sorted(grouped_elements):
            handler_type = self.get(entity_uri)
            if handler_type is not None:
                handler_types[entity_uri] = handler_type

        if not handler_types:
            if target_directory.is_dir():
                FilesystemAdapter.remove_directory_tree(target_directory)
            return {}

        jobs: List[
            Tuple[
                str,
                Type[EntityPageGenerationDataTransitionHandler],
                str,
                Dict[str, Any],
                Path,
            ]
        ] = []
        target_paths: Dict[str, str] = {}

        for entity_uri in sorted(handler_types):
            entity_directory: Path = (
                target_directory / self.entity_group_name(entity_uri)
            )
            for record in sorted(
                grouped_elements[entity_uri],
                key=lambda item: str(item.get("element") or ""),
            ):
                element_uri: str = str(record.get("element") or "").strip()
                source_node: Any = record.get("source_node")
                if not element_uri:
                    raise ValueError(
                        f"Element without URI in entity group {entity_uri}."
                    )
                if not isinstance(source_node, dict):
                    raise ValueError(
                        f"Element {element_uri} has no DATA_GATHERED source node."
                    )

                target_path: Path = entity_directory / (
                    f"{self.element_file_name(element_uri)}.jsonld"
                )
                target_key: str = str(target_path)
                previous_element: Optional[str] = target_paths.get(target_key)
                if previous_element is not None:
                    raise ValueError(
                        "Two Page-data jobs resolve to the same target path: "
                        f"{previous_element}, {element_uri} -> {target_path}"
                    )
                target_paths[target_key] = element_uri
                jobs.append(
                    (
                        entity_uri,
                        handler_types[entity_uri],
                        element_uri,
                        source_node,
                        target_path,
                    )
                )

        if target_directory.is_dir():
            FilesystemAdapter.remove_directory_tree(target_directory)
        target_directory.mkdir(parents=True, exist_ok=True)

        generated: Dict[str, List[str]] = {
            entity_uri: [] for entity_uri in sorted(handler_types)
        }
        future_context: Dict[Future, Tuple[str, Path]] = {}

        with ThreadPoolExecutor() as executor:
            for (
                entity_uri,
                handler_type,
                element_uri,
                source_node,
                target_path,
            ) in jobs:
                handler: EntityPageGenerationDataTransitionHandler = (
                    handler_type()
                )
                future: Future = executor.submit(
                    handler.execute,
                    context=context,
                    element_uri=element_uri,
                    entity_uri=entity_uri,
                    source_node=source_node,
                    target_path=target_path,
                )
                future_context[future] = (entity_uri, target_path)

            for future in as_completed(list(future_context)):
                entity_uri, target_path = future_context[future]
                resulting_path: Path = future.result()
                if resulting_path != target_path:
                    raise ValueError(
                        "Entity Page generation-data handler returned an "
                        f"unexpected path: {resulting_path} != {target_path}"
                    )
                generated[entity_uri].append(str(resulting_path))

        return {
            entity_uri: sorted(paths)
            for entity_uri, paths in generated.items()
        }

    @classmethod
    def handler_class_name(cls, entity_uri: str) -> str:
        entity_name: str = cls._pascal_case(cls._local_name(entity_uri))
        return f"{entity_name}{cls._HANDLER_CLASS_SUFFIX}"

    @classmethod
    def entity_group_name(cls, entity_uri: str) -> str:
        return cls._stable_path_key(entity_uri, fallback="entity")

    @classmethod
    def element_file_name(cls, element_uri: str) -> str:
        return cls._stable_path_key(element_uri, fallback="element")

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
            part
            for part in re.split(r"[^A-Za-z0-9]+", value)
            if part
        ]
        result: str = "".join(
            f"{part[:1].upper()}{part[1:]}" for part in parts
        )
        if not result or result[0].isdigit():
            raise ValueError(
                f"Cannot derive a Python handler class name from {value!r}."
            )
        return result

    @classmethod
    def _stable_path_key(cls, uri: str, *, fallback: str) -> str:
        local_name: str = cls._local_name(uri)
        slug: str = re.sub(
            r"[^A-Za-z0-9._-]+",
            "_",
            local_name,
        ).strip("._-").lower()
        if not slug:
            slug = fallback
        digest: str = hashlib.sha256(uri.encode("utf-8")).hexdigest()[:12]
        return f"{slug[:48]}-{digest}"
