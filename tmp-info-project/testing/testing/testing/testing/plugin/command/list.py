from pathlib import Path
from typing import Any, Dict, List, Optional

from ontobdc.cli.domain.model.command import CliCommandMetadata
from ontobdc.cli.domain.port.command import CliCommandPort
from ontobdc.cli.domain.request.command import CliCommandRequest
from ontobdc.cli.domain.response.command import ListCommandResponse

from ontobdc_dev.testing.application.catalog import TestCatalog, TestCatalogLoader
from ontobdc_dev.testing.plugin.command.args import flag_value

_RESOURCES: List[str] = ["states", "actions"]


class DevTestListCommand(CliCommandPort):
    """List the states or actions declared in the loaded manifests."""

    METADATA: CliCommandMetadata = CliCommandMetadata(
        id="test-list",
        logical_component="dev",
        description="List states or actions declared in semantic test manifests.",
        arguments=[
            {
                "accepts": ["test"],
                "description": "List states or actions declared in semantic test manifests.",
                "usage": "ontobdc dev test list states|actions --manifest <path>",
            },
            {
                "accepts": ["--manifest"],
                "valued": True,
                "description": "Path to a manifest file or a directory of *.yaml manifests.",
                "usage": "ontobdc dev test list states --manifest tests/semantic",
            },
        ],
    )

    def __init__(self, request: CliCommandRequest) -> None:
        self._request: CliCommandRequest = request
        self._resource: Optional[str] = None
        self._manifest_path: Optional[Path] = None

    @staticmethod
    def accepts(args: List[str]) -> bool:
        return (
            len(args) >= 4
            and args[0] == "dev"
            and args[1] == "test"
            and args[2] == "list"
            and args[3] in _RESOURCES
        )

    def check(self) -> bool:
        command_args: List[str] = self._request.command_args
        if len(command_args) < 3 or command_args[0] != "test" or command_args[1] != "list":
            return False
        if command_args[2] not in _RESOURCES:
            return False

        manifest_value: Optional[str] = flag_value(command_args[3:], "--manifest")
        if not manifest_value:
            return False

        self._resource = command_args[2]
        self._manifest_path = Path(manifest_value).expanduser()
        return True

    def run(self) -> ListCommandResponse:
        catalog: TestCatalog = TestCatalogLoader().load(self._manifest_path)
        items: List[Dict[str, Any]]
        if self._resource == "states":
            items = [
                {"name": state.name, "title": state.metadata.title, "tags": state.metadata.tags}
                for state in sorted(catalog.states.values(), key=lambda state: state.name)
            ]
        else:
            items = [
                {
                    "name": action.name,
                    "role": action.role,
                    "requires": action.requires,
                    "ensures": action.ensures,
                }
                for action in sorted(catalog.actions.values(), key=lambda action: action.name)
            ]

        return ListCommandResponse(
            title="Semantic Test Catalog",
            description=f"Declared {self._resource} in '{self._manifest_path}'.",
            content=items,
        )
