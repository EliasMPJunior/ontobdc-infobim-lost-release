from ontobdc.cli.adapter.context import CliContextAdapter
from ontobdc.cli.adapter.tree import CommandTreeAdapter
from ontobdc.cli.domain.request.command import CliCommandRequest
from ontobdc.cli.domain.response.command import HelpCommandResponse

from infobim.cli.plugin.command.welcome import InfoBIMWelcomeCommand


def test_bare_infobim_returns_autodiscovered_command_tree() -> None:
    command = InfoBIMWelcomeCommand(
        CliCommandRequest(
            logical_component="cli",
            component_action="welcome",
            command_args=[],
            context=CliContextAdapter([]),
        )
    )

    response: HelpCommandResponse = command.run()
    command_tree: str = response.content["Commands"]

    assert response.title == "InfoBIM Commands"
    assert response.description == "Available commands and options."
    assert response.content["Usage"] == "infobim <command> [flags/parameters]"
    assert command_tree.startswith("infobim\n")
    assert "project" in command_tree
    assert "--version" in command_tree
    assert "ontobdc\n" not in command_tree


def test_infobim_command_tree_is_deterministic() -> None:
    adapter = CommandTreeAdapter(
        root_package="infobim",
        executable="infobim",
        excluded_command_ids=("welcome",),
    )

    assert adapter.render() == adapter.render()
