
from typing import Dict, Iterable, List, NoReturn, Optional

from ontobdc.cli.domain.model.command import CliCommandMetadata
from ontobdc.cli.domain.port.command import CliCommandPort
from ontobdc.cli.domain.request.command import CliCommandRequest
from ontobdc.cli.domain.response.command import CommandResponse
from ontobdc.shared.adapter.module import OntoBDCExtraModuleResolver


class ViewProxyCommand(CliCommandPort):
    """Locate and execute the external ontobdc-view package."""

    METADATA: CliCommandMetadata = CliCommandMetadata(
        id="view",
        logical_component="view",
        description="Delegate view commands to the ontobdc-view workspace CLI.",
        arguments=[
            {
                "accepts": ["view"],
                "description": "Delegate view commands to the ontobdc-view CLI.",
                "usage": "ontobdc view <command> [flags/parameters]",
            },
        ],
    )

    @staticmethod
    def accepts(args: List[str]) -> bool:
        return len(args) > 0 and args[0] == "view"

    def __init__(self, request: CliCommandRequest) -> None:
        self._request: CliCommandRequest = request

    def check(self) -> bool:
        return True

    def run(self) -> CommandResponse:
        module_resolver: OntoBDCExtraModuleResolver = OntoBDCExtraModuleResolver(self.METADATA.id)

        forwarded_args: List[str] = list(self._request.command_args)

        module_resolver.exec_module_cli(forwarded_args)
