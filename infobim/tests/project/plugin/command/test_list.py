from ontobdc.cli.adapter.context import CliContextAdapter
from ontobdc.cli.domain.request.command import CliCommandRequest

from infobim.project.plugin.command.list import ProjectListCommand


def test_accepts_bare_project_command() -> None:
    assert ProjectListCommand.accepts(["project"])


def test_checks_bare_project_request() -> None:
    command: ProjectListCommand = ProjectListCommand(
        CliCommandRequest(
            logical_component="project",
            component_action="project_list",
            command_args=[],
            context=CliContextAdapter(["project"]),
        )
    )

    assert command.check()
