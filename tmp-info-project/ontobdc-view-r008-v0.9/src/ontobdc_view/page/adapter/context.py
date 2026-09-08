from __future__ import annotations

from typing import Any, Dict, List, Optional

from ontobdc.cli.domain.port.context import CliContextPort


PAGE_DATA_PAYLOAD = "page_data_payload"
PAGE_ELEMENT_URI = "page_element_uri"
PAGE_ENTITY_URI = "page_entity_uri"
PAGE_SOURCE_NODE = "page_source_node"
PAGE_BUILDER_PACKAGE = "page_builder_package"
PAGE_VIEW_DIRECTORY = "page_view_directory"


class IsolatedCliContextAdapter(CliContextPort):
    """Thread-local parameter overlay over a command context."""

    def __init__(
        self,
        parent: CliContextPort,
        parameters: Optional[Dict[str, Any]] = None,
    ) -> None:
        self._parent = parent
        self._parameters: Dict[str, Any] = dict(parameters or {})

    @property
    def raw_args(self) -> List[str]:
        return list(getattr(self._parent, "raw_args", []))

    @property
    def unprocessed_args(self) -> List[str]:
        return list(getattr(self._parent, "unprocessed_args", []))

    @property
    def is_capability_targeted(self) -> bool:
        return bool(getattr(self._parent, "is_capability_targeted", False))

    @property
    def target_capability_id(self) -> Optional[str]:
        return getattr(self._parent, "target_capability_id", None)

    @property
    def root_path(self) -> str:
        return str(getattr(self._parent, "root_path", ""))

    @property
    def language(self) -> Optional[str]:
        return getattr(self._parent, "language", None)

    def has_parameter(self, param_key: str) -> bool:
        return param_key in self._parameters or self._parent.has_parameter(param_key)

    def get_parameter_value(self, param_key: str) -> Any:
        if param_key in self._parameters:
            return self._parameters[param_key]
        return self._parent.get_parameter_value(param_key)

    def set_parameter_value(self, param_key: str, param_value: Any) -> None:
        self._parameters[param_key] = param_value

    def delete_parameter(self, param_key: str) -> None:
        self._parameters.pop(param_key, None)

    def clear_parameters(self, param_keys: List[str]) -> None:
        for param_key in param_keys:
            self.delete_parameter(param_key)

    def reload(self) -> None:
        reload_parent = getattr(self._parent, "reload", None)
        if callable(reload_parent):
            reload_parent()


class PageDataContextAdapter(IsolatedCliContextAdapter):
    """Thread-local overlay for one element's Page-data transformations.

    Reads fall back to the command context, while every write remains in this
    overlay.  Consequently capabilities retain the standard ``execute(context)``
    contract without putting per-element state in the shared CLI context.
    """

    def __init__(
        self,
        parent: CliContextPort,
        *,
        element_uri: str,
        entity_uri: str,
        source_node: Dict[str, Any],
        payload: Optional[Dict[str, Any]] = None,
    ) -> None:
        super().__init__(
            parent,
            {
                PAGE_ELEMENT_URI: element_uri,
                PAGE_ENTITY_URI: entity_uri,
                PAGE_SOURCE_NODE: source_node,
                PAGE_DATA_PAYLOAD: payload if payload is not None else {},
            },
        )

    @staticmethod
    def payload(context: CliContextPort) -> Dict[str, Any]:
        payload = context.get_parameter_value(PAGE_DATA_PAYLOAD)
        if not isinstance(payload, dict):
            raise TypeError("The Page-data payload must be a dictionary.")
        return payload

    @staticmethod
    def source_node(context: CliContextPort) -> Dict[str, Any]:
        source_node = context.get_parameter_value(PAGE_SOURCE_NODE)
        if not isinstance(source_node, dict):
            raise TypeError("The Page-data source node must be a dictionary.")
        return source_node

    @staticmethod
    def require_uri(context: CliContextPort, parameter: str) -> str:
        value = str(context.get_parameter_value(parameter) or "").strip()
        if not value:
            raise ValueError(f"The Page-data parameter {parameter!r} is required.")
        return value


class PageScriptGenerationContextAdapter(IsolatedCliContextAdapter):
    """Isolated context identifying one entity builder and its output view."""

    def __init__(
        self,
        parent: CliContextPort,
        *,
        builder_package: str,
        view_directory: str,
    ) -> None:
        if not builder_package.strip():
            raise ValueError("The Page builder package is required.")
        if not view_directory.strip():
            raise ValueError("The Page view directory is required.")
        super().__init__(
            parent,
            {
                PAGE_BUILDER_PACKAGE: builder_package.strip(),
                PAGE_VIEW_DIRECTORY: view_directory.strip(),
            },
        )

    @staticmethod
    def builder_package(context: CliContextPort) -> str:
        value = str(
            context.get_parameter_value(PAGE_BUILDER_PACKAGE) or ""
        ).strip()
        if not value:
            raise ValueError("The Page builder package was not resolved.")
        return value

    @staticmethod
    def view_directory(context: CliContextPort) -> str:
        value = str(
            context.get_parameter_value(PAGE_VIEW_DIRECTORY) or ""
        ).strip()
        if not value:
            raise ValueError("The Page view directory was not resolved.")
        return value
