"""Listener plugin discovery.

Same convention as ``ontobdc.shared.adapter.loader``: walk the
``<domain>/plugin/<resource>/`` package, import every module found, and
collect the classes that declare a ``METADATA`` of the resource's
metadata type. Nothing is registered by hand -- dropping a new Listener
module into ``ontobdc_web_dock/dock/plugin/listener/`` is enough to have
it found.

``ontobdc.shared.adapter.loader.PluginLoader`` itself is *not* reused
here: it resolves plugin roots through ``ConfigDataAdapter`` and drags in
the ``ontobdc`` distribution, which is not installed in Pyodide. The walk
is therefore reimplemented against ``pkgutil`` / ``importlib`` only --
the convention is shared, the machinery is the runtime-appropriate one.
"""

import importlib
import pkgutil
from typing import Any, List, Optional, Type

from ontobdc_web_dock.dock.domain.port.listener import (
    ListenerMetadata,
    ListenerPort,
)

_RESOURCE = "listener"
_PLUGIN_PACKAGE = "ontobdc_web_dock.dock.plugin"


class ListenerLoader:
    def __init__(self, plugin_package: str = _PLUGIN_PACKAGE) -> None:
        self._plugin_package = plugin_package

    def get_all(
        self, resource: str = _RESOURCE
    ) -> List[Type[ListenerPort]]:
        listeners: List[Type[ListenerPort]] = []
        seen = set()

        try:
            resource_package = importlib.import_module(
                f"{self._plugin_package}.{resource}"
            )
        except ImportError:
            return listeners

        if not hasattr(resource_package, "__path__"):
            return listeners

        prefix = resource_package.__name__ + "."
        for _, module_name, _ in pkgutil.iter_modules(
            resource_package.__path__, prefix
        ):
            try:
                module = importlib.import_module(module_name)
            except ImportError:
                continue
            for attribute in vars(module).values():
                if not isinstance(attribute, type):
                    continue
                if (
                    not issubclass(attribute, ListenerPort)
                    or attribute is ListenerPort
                ):
                    continue
                metadata: Any = getattr(attribute, "METADATA", None)
                if not isinstance(metadata, ListenerMetadata) or not metadata.id:
                    continue
                if metadata.id in seen:
                    continue
                seen.add(metadata.id)
                listeners.append(attribute)

        return listeners

    def get(
        self, id: str, resource: str = _RESOURCE
    ) -> Optional[Type[ListenerPort]]:
        for listener in self.get_all(resource):
            if listener.METADATA.id == id:
                return listener
        return None
