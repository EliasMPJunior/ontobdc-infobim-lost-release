from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List, Optional

import ifcopenshell

from ontobdc.cli.adapter.logger import NullLogRepository
from ontobdc.cli.domain.port.context import CliContextPort
from ontobdc.cli.domain.request.command import CliCommandRequest
from ontobdc.cli.domain.response.command import CommandResponse
from ontobdc.shared.adapter.loader import CommandLoader

from infobim.ifc.plugin.command.element_delete import IfcElementDeleteCommand


class FakeContext(CliContextPort):
    def __init__(
        self,
        *,
        raw_args: Optional[List[str]] = None,
        **parameters: Any,
    ) -> None:
        self._raw_args: List[str] = list(raw_args or [])
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
        return "."

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


class RecordingPromptChoice:
    def __init__(self, answer: str) -> None:
        self.answer: str = answer
        self.calls: List[Any] = []

    def __call__(self, *args: Any, **kwargs: Any) -> str:
        self.calls.append((args, kwargs))
        return self.answer


def build_ifc(path: Path) -> str:
    model = ifcopenshell.file(schema="IFC4")
    global_id = ifcopenshell.guid.new()
    model.create_entity("IfcBuildingElementProxy", GlobalId=global_id, Name="Keep me")
    model.write(str(path))
    return global_id


def _base_args(path: Path, global_id: str, *extra: str) -> List[str]:
    return ["ifc", "--file", str(path), "--global-id", global_id, "--delete", *extra]


def test_accepts_the_delete_shape() -> None:
    assert IfcElementDeleteCommand.accepts(
        ["ifc", "--file", "model.ifc", "--global-id", "G1", "--delete"]
    )


def test_rejects_without_delete_flag() -> None:
    assert not IfcElementDeleteCommand.accepts(
        ["ifc", "--file", "model.ifc", "--global-id", "G1"]
    )


def test_rejects_missing_file_or_global_id() -> None:
    assert not IfcElementDeleteCommand.accepts(
        ["ifc", "--global-id", "G1", "--delete"]
    )
    assert not IfcElementDeleteCommand.accepts(
        ["ifc", "--file", "model.ifc", "--delete"]
    )


def test_short_yes_flag_skips_the_prompt_and_confirms(tmp_path: Path) -> None:
    path = tmp_path / "model.ifc"
    global_id = build_ifc(path)
    before = path.read_bytes()
    args = _base_args(path, global_id, "-y")
    context = FakeContext(raw_args=args)
    command = IfcElementDeleteCommand(
        CliCommandRequest(
            logical_component="ifc",
            component_action="ifc_element_delete",
            command_args=args,
            context=context,
        )
    )
    prompt_choice = RecordingPromptChoice("No")
    command.set_prompt_choice(prompt_choice)

    assert command.check()
    response: CommandResponse = command.run()

    assert response.content["confirmed"] is True
    assert response.content["deleted"] is False
    assert response.content["stub"] is True
    assert prompt_choice.calls == []
    assert path.read_bytes() == before
    assert ifcopenshell.open(str(path)).by_guid(global_id) is not None


def test_long_yes_flag_skips_the_prompt_and_confirms(tmp_path: Path) -> None:
    path = tmp_path / "model.ifc"
    global_id = build_ifc(path)
    args = _base_args(path, global_id, "--yes")
    context = FakeContext(raw_args=args)
    command = IfcElementDeleteCommand(
        CliCommandRequest(
            logical_component="ifc",
            component_action="ifc_element_delete",
            command_args=args,
            context=context,
        )
    )
    prompt_choice = RecordingPromptChoice("No")
    command.set_prompt_choice(prompt_choice)

    assert command.check()
    response: CommandResponse = command.run()

    assert response.content["confirmed"] is True
    assert prompt_choice.calls == []


def test_without_yes_flag_the_injected_prompt_choice_is_called(tmp_path: Path) -> None:
    path = tmp_path / "model.ifc"
    global_id = build_ifc(path)
    args = _base_args(path, global_id)
    context = FakeContext(raw_args=args)
    command = IfcElementDeleteCommand(
        CliCommandRequest(
            logical_component="ifc",
            component_action="ifc_element_delete",
            command_args=args,
            context=context,
        )
    )
    prompt_choice = RecordingPromptChoice("Yes")
    command.set_prompt_choice(prompt_choice)

    assert command.check()
    response: CommandResponse = command.run()

    assert len(prompt_choice.calls) == 1
    assert response.content["confirmed"] is True


def test_declining_the_prompt_cancels_without_writing_the_file(tmp_path: Path) -> None:
    path = tmp_path / "model.ifc"
    global_id = build_ifc(path)
    before = path.read_bytes()
    args = _base_args(path, global_id)
    context = FakeContext(raw_args=args)
    command = IfcElementDeleteCommand(
        CliCommandRequest(
            logical_component="ifc",
            component_action="ifc_element_delete",
            command_args=args,
            context=context,
        )
    )
    command.set_prompt_choice(RecordingPromptChoice("No"))

    assert command.check()
    response: CommandResponse = command.run()

    assert response.content["confirmed"] is False
    assert response.content["deleted"] is False
    assert response.content["status"] == "cancelled"
    assert path.read_bytes() == before
    assert ifcopenshell.open(str(path)).by_guid(global_id) is not None


def test_command_discovery_finds_the_delete_command() -> None:
    discovered = CommandLoader(
        "ifc",
        NullLogRepository(),
        root_package="infobim",
    ).get_all()

    assert "ifc_element_delete" in {
        command.METADATA.id for command in discovered
    }
