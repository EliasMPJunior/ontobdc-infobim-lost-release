from pathlib import Path
from typing import List, Optional, Tuple

from ontobdc.cli.domain.exception.command import CliCommandArgumentException
from ontobdc.cli.domain.model.command import CliCommandMetadata
from ontobdc.shared.facade.port.command import CliCommandPort
from ontobdc.shared.facade.request.command import CliCommandRequest
from ontobdc.shared.facade.response.command import CommandResponse
from ontobdc.storage.adapter.identifier import normalize_container_id
from ontobdc.storage.adapter.rename_machine import ContainerRenameStateTransitionHandler
from ontobdc.storage.domain.port.rename_machine import (
    ContainerRenameStateTransitionHandlerPort,
)
from ontobdc.storage.plugin.check.is_container_id_registered.check import (
    get_registered_container_location,
)


class StorageContainerRenameCommand(CliCommandPort):
    """Rename a registered storage container through its dedicated statechart."""

    METADATA: CliCommandMetadata = CliCommandMetadata(
        id="container_rename",
        logical_component="storage",
        description="Rename a registered storage container.",
        arguments=[
            {
                "accepts": ["--container"],
                "valued": True,
                "description": "Select the registered container identifier.",
                "usage": "ontobdc storage --container <container-id> --rename <name>",
            },
            {
                "accepts": ["--rename"],
                "valued": True,
                "description": "Set the container name.",
                "usage": "ontobdc storage --container <container-id> --rename <name>",
            },
        ],
    )

    @staticmethod
    def accepts(args: List[str]) -> bool:
        return (
            len(args) == 5
            and args[0] == "storage"
            and args[1] == "--container"
            and bool(str(args[2]).strip())
            and args[3] == "--rename"
            and bool(str(args[4]).strip())
        )

    def __init__(self, request: CliCommandRequest) -> None:
        self._request: CliCommandRequest = request

    def check(self) -> bool:
        command_args: List[str] = self._request.command_args
        if not (
            len(command_args) == 4
            and command_args[0] == "--container"
            and command_args[2] == "--rename"
        ):
            return False

        requested_container_id: str = command_args[1].strip()
        requested_name: str = command_args[3].strip()
        if not requested_container_id or not requested_name:
            return False

        normalized_container_id: str = normalize_container_id(
            requested_container_id
        )
        resolved_container: Optional[Tuple[str, Path]] = (
            self._resolve_registered_container(normalized_container_id)
        )
        if resolved_container is None:
            raise CliCommandArgumentException(
                f"Container is not registered: {requested_container_id}"
            )

        canonical_container_id: str
        container_path: Path
        canonical_container_id, container_path = resolved_container

        self._request.context.delete_parameter("container")
        self._request.context.delete_parameter("dataset_path")
        self._request.context.set_parameter_value(
            "container_id",
            canonical_container_id,
        )
        self._request.context.set_parameter_value(
            "container_path",
            str(container_path),
        )
        self._request.context.set_parameter_value(
            "container_rename_to",
            requested_name,
        )
        return True

    def run(self) -> CommandResponse:
        handler: ContainerRenameStateTransitionHandlerPort = (
            ContainerRenameStateTransitionHandler(
                context=self._request.context,
            )
        )
        return handler.execute()

    def _resolve_registered_container(
        self,
        container_id: str,
    ) -> Optional[Tuple[str, Path]]:
        root_path: str = str(self._request.context.root_path)
        container_path: Optional[Path] = get_registered_container_location(
            container_id=container_id,
            root_path=root_path,
        )
        if container_path is None:
            return None
        return container_id, container_path
