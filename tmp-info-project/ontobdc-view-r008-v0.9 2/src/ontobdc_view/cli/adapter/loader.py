from typing import Dict, List, Tuple, Type

from ontobdc.cli.domain.port.command import CliCommandPort
from ontobdc.cli.domain.port.logger import LogRepositoryPort
from ontobdc.shared.domain.port.loader import CommandLoaderPort

from ontobdc_view.surface.plugin.command.view import ContainerViewCommand


class ViewCommandLoader(CommandLoaderPort):
    """Load the command classes owned by the ontobdc-view package.

    Commands are organized on disk by subject (``surface/``, ``page/``, ...)
    rather than by CLI routing token -- every one of them is invoked under
    the single ``ontobdc view`` noun, so they all declare
    ``METADATA.logical_component="view"`` regardless of which subfolder they
    live in. This explicit registry is the bridge between that folder
    layout and the CLI token, mirroring ``ontobdc_dev.cli.adapter.loader.
    DevCommandLoader``.
    """

    _COMMANDS_BY_COMPONENT: Dict[
        str,
        Tuple[Type[CliCommandPort], ...],
    ] = {
        "view": (
            ContainerViewCommand,
        ),
    }

    @classmethod
    def command_classes(cls) -> List[Type[CliCommandPort]]:
        """Every registered command, across all logical components."""
        registered: List[Type[CliCommandPort]] = []
        command_group: Tuple[Type[CliCommandPort], ...]
        for command_group in cls._COMMANDS_BY_COMPONENT.values():
            command_class: Type[CliCommandPort]
            for command_class in command_group:
                if command_class not in registered:
                    registered.append(command_class)
        return registered

    def __init__(
        self,
        logical_component: str,
        logger: LogRepositoryPort,
    ) -> None:
        self._logical_component: str = logical_component
        self._logger: LogRepositoryPort = logger

    def get(self, id: str) -> Type[CliCommandPort]:
        command_class: Type[CliCommandPort]
        for command_class in self.get_all():
            if command_class.METADATA.id == id:
                return command_class

        raise LookupError(
            f"Command '{id}' was not found for component "
            f"'{self._logical_component}'."
        )

    def get_all(
        self,
        resource: str = "command",
    ) -> List[Type[CliCommandPort]]:
        if resource != "command":
            return []

        command_classes: Tuple[Type[CliCommandPort], ...] = (
            self._COMMANDS_BY_COMPONENT.get(
                self._logical_component,
                (),
            )
        )
        return list(command_classes)
