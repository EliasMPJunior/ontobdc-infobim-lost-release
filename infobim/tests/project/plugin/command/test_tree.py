from typing import Any, Dict

from ontobdc.cli.adapter.context import CliContextAdapter
from ontobdc.cli.domain.request.command import CliCommandRequest
from ontobdc.cli.domain.response.command import TreeCommandResponse

from infobim.project.plugin.command import tree as tree_module
from infobim.project.plugin.command.tree import ProjectTreeCommand
from infobim.project.plugin.parameter.project import ProjectIdStrategy


def test_accepts_project_selector() -> None:
    assert ProjectTreeCommand.accepts(
        ["project", "--project", "project-global-id"]
    )


def test_resolves_project_and_delegates_to_container_tree(monkeypatch) -> None:
    context: CliContextAdapter = CliContextAdapter(
        ["--project", "project-global-id"]
    )

    def resolve_project(
        _strategy: ProjectIdStrategy,
        target_context: CliContextAdapter,
    ) -> CliContextAdapter:
        target_context.set_parameter_value(
            "project_id",
            "project-global-id",
        )
        target_context.set_parameter_value("container_id", "container-id")
        return target_context

    class FakeContainerTreeCommand:
        METADATA = tree_module.StorageContainerTreeCommand.METADATA

        def __init__(self, request: CliCommandRequest) -> None:
            assert request.command_args == ["--container-id", "container-id"]

        def check(self) -> bool:
            return True

        def run(self) -> TreeCommandResponse:
            tree: Dict[str, Any] = {
                "name": "Container title",
                "kind": "root",
                "children": [],
            }
            return TreeCommandResponse(
                title="Storage Container",
                description="Container tree.",
                content={"tree": tree},
            )

    monkeypatch.setattr(ProjectIdStrategy, "execute", resolve_project)
    monkeypatch.setattr(
        tree_module,
        "StorageContainerTreeCommand",
        FakeContainerTreeCommand,
    )

    command: ProjectTreeCommand = ProjectTreeCommand(
        CliCommandRequest(
            logical_component="project",
            component_action="project_tree",
            command_args=["--project", "project-global-id"],
            context=context,
        )
    )

    assert command.check()
    response: TreeCommandResponse = command.run()

    assert response.title == "InfoBIM Project"
    assert response.description == "Tree view of Project project-global-id."
    assert response.content["tree"]["name"] == "project-global-id"
