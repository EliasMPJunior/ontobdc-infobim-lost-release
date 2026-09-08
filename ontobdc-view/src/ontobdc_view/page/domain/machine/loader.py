import importlib
import inspect
import pkgutil
from types import ModuleType
from typing import List, Tuple, Type

from ontobdc.shared.adapter.util import to_pascal_case
from ontobdc_view.page.domain.port.machine import (
    EntityPageGenerationDataTransitionHandlerPort,
)


class EntityPageGenerationDataTransitionHandlerLoader:
    """Discover the per-entity Page-data handler for an entity type."""

    _HANDLER_PACKAGE_SUFFIX: str = "page.plugin.builder"
    _HANDLER_CLASS_SUFFIX: str = (
        "PageGenerationDataTransitionHandler"
    )

    def __init__(
        self,
        root_packages: Tuple[str, ...] = ("ontobdc_view",),
    ) -> None:
        self._root_packages: Tuple[str, ...] = root_packages

    def get(
        self,
        entity_uri: str,
    ) -> Type[EntityPageGenerationDataTransitionHandlerPort]:
        expected_name: str = self._handler_class_name(entity_uri)
        matches: List[
            Type[EntityPageGenerationDataTransitionHandlerPort]
        ] = [
            handler_type
            for handler_type in self.get_all()
            if handler_type.__name__ == expected_name
        ]

        if not matches:
            raise LookupError(
                "Entity Page generation-data handler not found: "
                f"{expected_name} ({entity_uri})"
            )
        if len(matches) > 1:
            raise ValueError(
                "More than one Entity Page generation-data handler was "
                f"discovered for {entity_uri}: {expected_name}"
            )

        return matches[0]

    def get_all(
        self,
    ) -> List[Type[EntityPageGenerationDataTransitionHandlerPort]]:
        handler_types: List[
            Type[EntityPageGenerationDataTransitionHandlerPort]
        ] = []

        root_package: str
        for root_package in self._root_packages:
            package_name: str = (
                f"{root_package}.{self._HANDLER_PACKAGE_SUFFIX}"
            )
            package: ModuleType = importlib.import_module(package_name)
            handler_types.extend(
                self._handler_types_from_module(package)
            )

            module_info: pkgutil.ModuleInfo
            for module_info in pkgutil.walk_packages(
                package.__path__,
                f"{package.__name__}.",
            ):
                module: ModuleType = importlib.import_module(
                    module_info.name
                )
                handler_types.extend(
                    self._handler_types_from_module(module)
                )

        return sorted(
            handler_types,
            key=lambda handler_type: handler_type.__name__,
        )

    @classmethod
    def _handler_types_from_module(
        cls,
        module: ModuleType,
    ) -> List[Type[EntityPageGenerationDataTransitionHandlerPort]]:
        handler_types: List[
            Type[EntityPageGenerationDataTransitionHandlerPort]
        ] = []
        candidate: Type[object]
        for _, candidate in inspect.getmembers(module, inspect.isclass):
            if candidate.__module__ != module.__name__:
                continue
            if candidate is EntityPageGenerationDataTransitionHandlerPort:
                continue
            if not issubclass(
                candidate,
                EntityPageGenerationDataTransitionHandlerPort,
            ):
                continue
            if inspect.isabstract(candidate):
                continue
            if not candidate.__name__.endswith(
                cls._HANDLER_CLASS_SUFFIX
            ):
                continue
            handler_types.append(candidate)

        return handler_types

    @classmethod
    def _handler_class_name(cls, entity_uri: str) -> str:
        entity_name: str = to_pascal_case(
            cls._local_name(entity_uri)
        )
        if not entity_name or entity_name[0].isdigit():
            raise ValueError(
                "Cannot derive a Page generation-data handler name from "
                f"{entity_uri!r}."
            )
        return f"{entity_name}{cls._HANDLER_CLASS_SUFFIX}"

    @staticmethod
    def _local_name(entity_uri: str) -> str:
        normalized_uri: str = str(entity_uri or "").strip()
        if not normalized_uri:
            raise ValueError("Entity URI cannot be empty.")
        if "#" in normalized_uri:
            return normalized_uri.rsplit("#", 1)[-1]

        trimmed_uri: str = normalized_uri.rstrip("/")
        if "/" in trimmed_uri:
            return trimmed_uri.rsplit("/", 1)[-1]
        if ":" in trimmed_uri:
            return trimmed_uri.rsplit(":", 1)[-1]
        return trimmed_uri
