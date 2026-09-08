from typing import List

from ontobdc.cli.adapter.context import CliContextAdapter
from ontobdc.cli.adapter.logger import NullLogRepository
from ontobdc.context.plugin.command.help import ContextHelpCommand
from ontobdc.shared.adapter.loader import CommandLoader
from ontobdc.shared.facade.request.command import CliCommandRequest
from ontobdc.shared.facade.response.command import HelpCommandResponse


class ContextHelpCommandFixture:
    @staticmethod
    def make(command_args: List[str]) -> ContextHelpCommand:
        request: CliCommandRequest = CliCommandRequest(
            logical_component="context",
            component_action="help",
            command_args=command_args,
            context=CliContextAdapter(command_args),
        )
        return ContextHelpCommand(request)


def test_accepts_context_help_arguments() -> None:
    assert ContextHelpCommand.accepts(["context", "--help"])
    assert ContextHelpCommand.accepts(["context", "-h"])
    assert not ContextHelpCommand.accepts(["context"])
    assert not ContextHelpCommand.accepts(["storage", "--help"])


def test_check_validates_scoped_command_arguments() -> None:
    assert ContextHelpCommandFixture.make(["--help"]).check()
    assert ContextHelpCommandFixture.make(["-h"]).check()
    assert not ContextHelpCommandFixture.make([]).check()
    assert not ContextHelpCommandFixture.make(["--analyse"]).check()


def test_run_returns_populated_help_response() -> None:
    command: ContextHelpCommand = ContextHelpCommandFixture.make(["--help"])

    response: HelpCommandResponse = command.run()

    assert isinstance(response, HelpCommandResponse)
    assert isinstance(response.content["Usage"], dict)
    assert isinstance(response.content["Options"], dict)
    assert response.content["Usage"]
    assert response.content["Options"]


def test_command_loader_discovers_context_help_command() -> None:
    discovered_ids: List[str] = [
        command.METADATA.id
        for command in CommandLoader(
            "context",
            NullLogRepository(),
        ).get_all()
    ]

    assert "help" in discovered_ids
