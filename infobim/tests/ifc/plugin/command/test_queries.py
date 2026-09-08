from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace
from typing import Any, Dict, List, Optional, Set, Type

from infobim.ifc.plugin.capability.query.class_elements import (
    IfcClassElementsQueryCapability,
)
from infobim.ifc.plugin.capability.query.classes import IfcClassesQueryCapability
from infobim.ifc.plugin.capability.query.element import IfcElementQueryCapability
from infobim.ifc.plugin.command.class_all import IfcClassAllCommand
from infobim.ifc.plugin.command.class_elements_all import (
    IfcClassElementsAllCommand,
)
from infobim.ifc.plugin.command.element import IfcElementCommand
from infobim.ifc.plugin.command import support as command_support
from infobim.project.plugin.parameter.project import ProjectIdStrategy
from ontobdc.cli import CliParameterValidationOrchestrator
from ontobdc.cli.adapter.logger import NullLogRepository
from ontobdc.cli.domain.port.context import CliContextPort
from ontobdc.cli.domain.request.command import CliCommandRequest
from ontobdc.cli.domain.response.command import CommandResponse
from ontobdc.shared.adapter.loader import ParameterLoader


class QueryCommandContext(CliContextPort):
    def __init__(
        self,
        *,
        raw_args: Optional[List[str]] = None,
        root_path: str = ".",
        **parameters: Any,
    ) -> None:
        self._raw_args: List[str] = list(raw_args or [])
        self._root_path: str = root_path
        self._parameters: Dict[str, Any] = dict(parameters)

    @property
    def raw_args(self) -> List[str]:
        return self._raw_args

    @property
    def unprocessed_args(self) -> List[str]:
        return []

    @property
    def is_capability_targeted(self) -> bool:
        return False

    @property
    def target_capability_id(self) -> Optional[str]:
        return None

    @property
    def root_path(self) -> str:
        return self._root_path

    @property
    def language(self) -> Optional[str]:
        return None

    def has_parameter(self, name: str) -> bool:
        return name in self._parameters

    def get_parameter_value(self, name: str) -> Any:
        return self._parameters.get(name)

    def set_parameter_value(self, name: str, value: Any) -> None:
        self._parameters[name] = value

    def delete_parameter(self, name: str) -> None:
        self._parameters.pop(name, None)

    def clear_parameters(self, names: List[str]) -> None:
        for name in names:
            self.delete_parameter(name)

    def reload(self) -> None:
        return None


class RecordingProjectStrategy:
    METADATA: SimpleNamespace = SimpleNamespace(name="project_id")

    def execute(self, context: CliContextPort) -> CliContextPort:
        context.set_parameter_value("project_id", "resolved-project")
        context.set_parameter_value("project_path", context.root_path)
        return context


class RecordingParameterLoader:
    def get_all(self) -> List[RecordingProjectStrategy]:
        return [RecordingProjectStrategy()]


def make_request(
    command_id: str,
    args: List[str],
    context: QueryCommandContext,
) -> CliCommandRequest:
    return CliCommandRequest(
        logical_component="ifc",
        component_action=command_id,
        command_args=args,
        context=context,
    )


def test_query_command_argument_shapes_are_unambiguous() -> None:
    assert IfcClassAllCommand.accepts(["ifc", "--class", "--all"])
    assert not IfcClassAllCommand.accepts(
        ["ifc", "--class", "IfcWall", "--all"]
    )
    assert IfcClassElementsAllCommand.accepts(
        ["ifc", "--class", "IfcWall", "--all"]
    )
    assert IfcElementCommand.accepts(
        ["ifc", "--project", ".", "--element", "wall-id"]
    )
    assert not IfcElementCommand.accepts(
        [
            "ifc",
            "--project",
            ".",
            "--project-id",
            "project-id",
            "--element",
            "wall-id",
        ]
    )


def test_parameter_pipeline_binds_capability_parameter_names(
    tmp_path: Path,
) -> None:
    args: List[str] = ["ifc", "--project", ".", "--element", "wall-id"]
    context: QueryCommandContext = QueryCommandContext(
        raw_args=args[1:],
        root_path=str(tmp_path),
    )
    command: IfcElementCommand = IfcElementCommand(
        make_request(IfcElementCommand.METADATA.id, args[1:], context)
    )

    validator: CliParameterValidationOrchestrator = (
        CliParameterValidationOrchestrator()
    )
    assert validator.check(
        command,
        args,
        NullLogRepository(),
        RecordingParameterLoader(),
    )
    assert context.get_parameter_value("element_global_id") == "wall-id"
    assert context.get_parameter_value("project_id") == "resolved-project"


def test_parameter_loader_discovers_infobim_project_strategy() -> None:
    strategy_ids: Set[str] = {
        strategy.METADATA.id
        for strategy in ParameterLoader(
            logger=NullLogRepository(),
            root_packages=("infobim",),
        ).get_all()
    }

    assert ProjectIdStrategy.METADATA.id in strategy_ids


def test_commands_delegate_queries_to_capability_executor(
    tmp_path: Path,
    monkeypatch: Any,
) -> None:
    calls: List[Type[Any]] = []

    def execute(capability: Any, context: CliContextPort) -> Dict[str, Any]:
        calls.append(type(capability))
        if isinstance(capability, IfcClassesQueryCapability):
            return {
                "project_path": str(tmp_path),
                "class_count": 1,
                "element_count": 1,
                "classes": [],
            }
        if isinstance(capability, IfcClassElementsQueryCapability):
            return {
                "project_path": str(tmp_path),
                "class_name": "IfcWall",
                "class_uri": "urn:ifc:IfcWall",
                "dataset_count": 1,
                "datasets": [],
                "element_count": 1,
                "elements": [],
            }
        return {
            "project_path": str(tmp_path),
            "global_id": "wall-id",
            "found": True,
            "class_uri": "urn:ifc:IfcWall",
            "class_name": "IfcWall",
            "dataset_count": 1,
            "datasets": [],
            "element": {"GlobalId": "wall-id"},
        }

    monkeypatch.setattr(command_support.CapabilityExecutor, "execute", execute)
    common: Dict[str, Any] = {
        "project_id": "project-id",
        "project_path": str(tmp_path),
    }

    classes_command: IfcClassAllCommand = IfcClassAllCommand(
        make_request(
            IfcClassAllCommand.METADATA.id,
            ["--class", "--all"],
            QueryCommandContext(**common),
        )
    )
    assert classes_command.check()
    classes_response: CommandResponse = classes_command.run()
    assert classes_response.content["class_count"] == 1

    elements_command: IfcClassElementsAllCommand = IfcClassElementsAllCommand(
        make_request(
            IfcClassElementsAllCommand.METADATA.id,
            ["--class", "IfcWall", "--all"],
            QueryCommandContext(ifc_class="IfcWall", **common),
        )
    )
    assert elements_command.check()
    elements_response: CommandResponse = elements_command.run()
    assert elements_response.content["class_name"] == "IfcWall"

    element_command: IfcElementCommand = IfcElementCommand(
        make_request(
            IfcElementCommand.METADATA.id,
            ["--element", "wall-id"],
            QueryCommandContext(element_global_id="wall-id", **common),
        )
    )
    assert element_command.check()
    element_response: CommandResponse = element_command.run()
    assert element_response.content["global_id"] == "wall-id"

    assert calls == [
        IfcClassesQueryCapability,
        IfcClassElementsQueryCapability,
        IfcElementQueryCapability,
    ]
