from typing import Any, Dict, List

from ontobdc.cli.adapter.context import CliContextAdapter
from ontobdc.cli.domain.request.command import CliCommandRequest
from ontobdc.cli.domain.response.command import CommandResponse

from infobim.project.plugin.command import element as element_module
from infobim.project.plugin.command.element import ProjectElementCommand
from infobim.project.plugin.parameter.project import ProjectIdStrategy


def test_accepts_project_element_with_optional_entity_filter() -> None:
    assert ProjectElementCommand.accepts(
        ["project", "--project", "project-global-id", "--element"]
    )
    assert ProjectElementCommand.accepts(
        [
            "project",
            "--project",
            "project-global-id",
            "--element",
            "--entity",
            "ifc_project",
        ]
    )


def test_resolves_project_and_delegates_to_storage_element(monkeypatch) -> None:
    context: CliContextAdapter = CliContextAdapter(
        ["--project", "project-global-id", "--element"]
    )

    def resolve_project(
        _strategy: ProjectIdStrategy,
        target_context: CliContextAdapter,
    ) -> CliContextAdapter:
        target_context.set_parameter_value(
            "project_id",
            "project-global-id",
        )
        target_context.set_parameter_value("project_path", "/project")
        target_context.set_parameter_value("container_id", "container-id")
        return target_context

    class FakeStorageElementCommand:
        METADATA = element_module.StorageElementCommand.METADATA

        def __init__(self, request: CliCommandRequest) -> None:
            assert request.command_args == [
                "--container",
                "container-id",
                "--element",
            ]

        def check(self) -> bool:
            return True

        def run(self) -> CommandResponse:
            elements: List[Dict[str, Any]] = [
                {
                    "global_id": "element-id",
                    "entity_identifier": "ifc_project",
                    "title": "IFC Project",
                }
            ]
            return CommandResponse(
                title="Storage Element",
                description="Storage elements.",
                content={"elements": elements},
            )

    monkeypatch.setattr(ProjectIdStrategy, "execute", resolve_project)
    monkeypatch.setattr(
        element_module,
        "StorageElementCommand",
        FakeStorageElementCommand,
    )

    command: ProjectElementCommand = ProjectElementCommand(
        CliCommandRequest(
            logical_component="project",
            component_action="project_element",
            command_args=["--project", "project-global-id", "--element"],
            context=context,
        )
    )

    assert command.check()
    response: CommandResponse = command.run()

    assert response.title == "InfoBIM Project Element"
    assert response.content == {
        "project_id": "project-global-id",
        "project_path": "/project",
        "elements": [
            {
                "global_id": "element-id",
                "entity_identifier": "ifc_project",
                "title": "IFC Project",
            }
        ],
    }
