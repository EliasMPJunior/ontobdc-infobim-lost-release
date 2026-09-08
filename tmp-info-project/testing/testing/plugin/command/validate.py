from pathlib import Path
from typing import List, Optional

from ontobdc.cli.domain.model.command import CliCommandMetadata
from ontobdc.cli.domain.port.command import CliCommandPort
from ontobdc.cli.domain.request.command import CliCommandRequest
from ontobdc.cli.domain.response.command import CommandResponse

from ontobdc_dev.testing.application.catalog import TestCatalogLoader
from ontobdc_dev.testing.plugin.command.args import flag_value


class DevTestValidateCommand(CliCommandPort):
    """Validate semantic test manifests without executing anything.

    A manifest that fails to load raises `TestManifestError`, which is left
    to propagate to `DevCliApplication`'s exception handling so the process
    reports a failure instead of a silent pass.
    """

    METADATA: CliCommandMetadata = CliCommandMetadata(
        id="test-validate",
        logical_component="dev",
        description="Validate StateDefinition/TestAction manifests structurally and semantically.",
        arguments=[
            {
                "accepts": ["test"],
                "description": "Validate semantic test manifests.",
                "usage": "ontobdc dev test validate --manifest <path>",
            },
            {
                "accepts": ["--manifest"],
                "valued": True,
                "description": "Path to a manifest file or a directory of *.yaml manifests.",
                "usage": "ontobdc dev test validate --manifest tests/semantic",
            },
        ],
    )

    def __init__(self, request: CliCommandRequest) -> None:
        self._request: CliCommandRequest = request
        self._manifest_path: Optional[Path] = None

    @staticmethod
    def accepts(args: List[str]) -> bool:
        return (
            len(args) >= 3
            and args[0] == "dev"
            and args[1] == "test"
            and args[2] == "validate"
        )

    def check(self) -> bool:
        command_args: List[str] = self._request.command_args
        if len(command_args) < 2 or command_args[0] != "test" or command_args[1] != "validate":
            return False

        manifest_value: Optional[str] = flag_value(command_args[2:], "--manifest")
        if not manifest_value:
            return False

        self._manifest_path = Path(manifest_value).expanduser()
        return True

    def run(self) -> CommandResponse:
        catalog = TestCatalogLoader().load(self._manifest_path)
        return CommandResponse(
            title="Semantic Test Validation",
            description="All discovered manifests are structurally and semantically valid.",
            content={
                "manifest": str(self._manifest_path),
                "states": sorted(catalog.states.keys()),
                "actions": sorted(catalog.actions.keys()),
            },
        )
