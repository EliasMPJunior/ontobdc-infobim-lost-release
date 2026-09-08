from typing import Any, List

from ontobdc.cli.adapter.logger import NullLogRepository
from ontobdc.cli.adapter.machine import CliHealthStateTransitionHandler
from ontobdc.cli.domain.model.command import CliCommandMetadata
from ontobdc.cli.domain.model.logger import LogStrategyConfig
from ontobdc.cli.domain.port.command import CliCommandPort
from ontobdc.cli.domain.port.logger import LogRepositoryPort
from ontobdc.cli.domain.request.command import CliCommandRequest
from ontobdc.cli.domain.response.command import CommandResponse


class CliHealthCommand(CliCommandPort):
    """
    Command to verify that the ontobdc system is healthy.
    """

    METADATA = CliCommandMetadata(
        id="health",
        logical_component="cli",
        description="Verify that the ontobdc system is healthy.",
        depends_on=None,
        arguments=[
            {
                "accepts": [
                    "health",
                ],
                "description": "Verify that the ontobdc system is healthy.",
                "usage": "ontobdc health",
            },
        ],
    )

    def __init__(self, request: CliCommandRequest):
        self._request: CliCommandRequest = request
        self._logger: LogRepositoryPort = NullLogRepository()
        self._log_strategy: Any = None

    @property
    def log_strategy(self) -> Any:
        return self._log_strategy

    @staticmethod
    def accepts(args: List[str]) -> bool:
        return len(args) == 1 and args[0] == "health"

    def set_log_strategy(self, log_strategy: LogStrategyConfig) -> None:
        self._log_strategy = log_strategy
        self._logger = log_strategy.log_repository

    def check(self) -> bool:
        return (
            len(self._request.command_args) == 1
            and self._request.command_args[0] == "health"
        )

    def run(self) -> CommandResponse:
        handler: CliHealthStateTransitionHandler = (
            CliHealthStateTransitionHandler(
                context=self._request.context,
                logger=self._logger,
            )
        )

        return handler.execute()
