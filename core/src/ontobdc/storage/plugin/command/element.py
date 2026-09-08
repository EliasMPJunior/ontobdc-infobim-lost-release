from typing import Any, ClassVar, Dict, List, Tuple

from ontobdc.cli.domain.exception.command import CliCommandArgumentException
from ontobdc.cli.domain.model.command import CliCommandMetadata
from ontobdc.context.adapter.container_instance import (
    ContainerEntityInstanceRepository,
)
from ontobdc.shared.facade.port.command import CliCommandPort
from ontobdc.shared.facade.request.command import CliCommandRequest
from ontobdc.shared.facade.response.command import CommandResponse
from ontobdc.storage.plugin.parameter.container import ContainerIdStrategy


class StorageElementCommand(CliCommandPort):
    """List obdc:DataEntity instances registered in a selected storage container."""

    ACTIONS: ClassVar[Tuple[str, ...]] = ("--element",)
    METADATA: CliCommandMetadata = CliCommandMetadata(
        id="element",
        logical_component="storage",
        description="Target elements in a selected storage container.",
        arguments=[
            {
                "accepts": ["--container"],
                "valued": True,
                "description": (
                    "Select a registered container by ID or filesystem path."
                ),
                "usage": (
                    "ontobdc storage --container <id-or-path> --element "
                    "[--entity <entity-uri-or-identifier>]"
                ),
            },
            {
                "accepts": ["--element"],
                "valued": False,
                "description": "Target the selected container's elements.",
                "usage": (
                    "ontobdc storage --container <id-or-path> --element "
                    "[--entity <entity-uri-or-identifier>]"
                ),
            },
            {
                "accepts": ["--entity"],
                "valued": True,
                "description": (
                    "Filter elements by an entity URI or entity_identifier."
                ),
                "usage": (
                    "ontobdc storage --container <id-or-path> --element "
                    "--entity <entity-uri-or-identifier>"
                ),
            },
        ],
    )

    def __init__(self, request: CliCommandRequest) -> None:
        self._request: CliCommandRequest = request
        self._entity_filter: str = ""

    @classmethod
    def accepts(cls, args: List[str]) -> bool:
        action_end: int = 3 + len(cls.ACTIONS)
        base_arguments_valid: bool = (
            len(args) >= action_end
            and args[:2] == ["storage", "--container"]
            and bool(str(args[2]).strip())
            and args[3:action_end] == list(cls.ACTIONS)
        )
        if not base_arguments_valid:
            return False
        if len(args) == action_end:
            return True
        return (
            len(args) == action_end + 2
            and args[action_end] == "--entity"
            and bool(str(args[action_end + 1]).strip())
        )

    def check(self) -> bool:
        command_args: List[str] = self._request.command_args
        action_end: int = 2 + len(self.ACTIONS)
        base_arguments_valid: bool = (
            len(command_args) >= action_end
            and command_args[:1] == ["--container"]
            and bool(str(command_args[1]).strip())
            and command_args[2:action_end] == list(self.ACTIONS)
        )
        filter_arguments_valid: bool = len(command_args) == action_end or (
            len(command_args) == action_end + 2
            and command_args[action_end] == "--entity"
            and bool(str(command_args[action_end + 1]).strip())
        )
        if not base_arguments_valid or not filter_arguments_valid:
            return False

        container_selector: str = str(command_args[1]).strip()
        self._request.context.set_parameter_value(
            "container",
            container_selector,
        )
        self._entity_filter = ""
        if len(command_args) == action_end + 2:
            self._entity_filter = str(
                command_args[action_end + 1]
            ).strip()
            self._request.context.delete_parameter("entity")
        ContainerIdStrategy().execute(self._request.context)

        container_id: str = str(
            self._request.context.get_parameter_value("container_id") or ""
        ).strip()
        container_path: str = str(
            self._request.context.get_parameter_value("container_path") or ""
        ).strip()
        if not container_id or not container_path:
            raise CliCommandArgumentException(
                f"Invalid container selector: {container_selector}"
            )

        return True

    def run(self) -> CommandResponse:
        container_id: str = str(
            self._request.context.get_parameter_value("container_id") or ""
        ).strip()
        container_path: str = str(
            self._request.context.get_parameter_value("container_path") or ""
        ).strip()
        element_rows: List[Dict[str, Any]] = self._list_data_entity_instances(
            container_path=container_path
        )
        visible_element_rows: List[Dict[str, str]] = (
            self._compact_element_rows(element_rows)
        )

        return CommandResponse(
            title="Storage Element",
            description=(
                f"Listed {len(visible_element_rows)} obdc:DataEntity instance(s) "
                f"present in the selected storage container."
            ),
            content={
                "container_id": container_id,
                "container_path": container_path,
                "elements": visible_element_rows,
            },
        )

    def _list_element_rows(
        self,
        *,
        container_path: str,
    ) -> List[Dict[str, Any]]:
        return ContainerEntityInstanceRepository(
            container_path=container_path,
            entity=self._entity_filter,
        ).list_elements()

    def _list_data_entity_instances(
        self,
        *,
        container_path: str,
    ) -> List[Dict[str, Any]]:
        """Compatibility entrypoint backed entirely by the repository."""
        return self._list_element_rows(container_path=container_path)

    @staticmethod
    def _compact_element_rows(
        element_rows: List[Dict[str, Any]],
    ) -> List[Dict[str, str]]:
        return [
            {
                "global_id": str(
                    element_row.get("global_id")
                    or element_row.get("id")
                    or ""
                ).strip(),
                "entity_identifier": str(
                    element_row.get("entity_identifier") or ""
                ).strip(),
                "title": str(element_row.get("title") or "").strip(),
            }
            for element_row in element_rows
        ]
