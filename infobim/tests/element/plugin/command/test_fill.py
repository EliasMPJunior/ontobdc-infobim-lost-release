from pathlib import Path
from typing import Any, Dict, List, Optional

import pytest

from ontobdc.cli.domain.port.context import CliContextPort
from ontobdc.cli.domain.response.command import InteractiveCommandResponse
from ontobdc.shared.facade.request.command import CliCommandRequest

from infobim.element.adapter.facade_field import (
    ElementFacadeFieldResolver,
    ElementField,
    ElementFieldResolution,
    FacadeFieldSource,
)
from infobim.element.adapter.fill_form import ElementFillFormAdapter
from infobim.element.plugin.command.fill import ElementFillCommand
from infobim.project.plugin.parameter.project import ProjectIdStrategy

_BASE = [
    "element",
    "--project",
    "PROJECT-ID",
    "--dataset",
    "DATASET-ID",
    "--entity",
    "https://example.test/Entity",
    "--fill",
]


def test_accepts_the_bare_fill_shape() -> None:
    assert ElementFillCommand.accepts(_BASE)


def test_accepts_the_fill_shape_with_schema() -> None:
    assert ElementFillCommand.accepts([*_BASE, "--schema", "IFC2X3"])


def test_rejects_when_not_the_element_component() -> None:
    assert not ElementFillCommand.accepts(["storage", *_BASE[1:]])


def test_rejects_missing_required_flag_values() -> None:
    assert not ElementFillCommand.accepts(
        ["element", "--project", "", "--dataset", "D", "--entity", "E", "--fill"]
    )
    assert not ElementFillCommand.accepts(
        ["element", "--project", "P", "--dataset", "D", "--entity", "", "--fill"]
    )


def test_rejects_dangling_schema_flag_without_a_value() -> None:
    assert not ElementFillCommand.accepts([*_BASE, "--schema"])


def test_rejects_wrong_token_count() -> None:
    assert not ElementFillCommand.accepts(_BASE[:-1])
    assert not ElementFillCommand.accepts([*_BASE, "extra"])


class FillContext(CliContextPort):
    def __init__(self, root_path: Path, **parameters: Any) -> None:
        self._root_path: Path = root_path
        self._parameters: Dict[str, Any] = dict(parameters)

    @property
    def raw_args(self) -> List[str]:
        return []

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
        return str(self._root_path)

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


class StaticFieldResolver(ElementFacadeFieldResolver):
    def resolve(self, **_kwargs: Any) -> ElementFieldResolution:
        return ElementFieldResolution(
            source=FacadeFieldSource.FACADE,
            entity_uri="https://example.test/Entity",
            fields=[
                ElementField(
                    identifier="Name", label="Name", datatype="string",
                    required=True,
                ),
                ElementField(
                    identifier="StartTime", label="Start Time",
                    datatype="dateTime", required=False,
                ),
            ],
        )


class RecordingFormAdapter(ElementFillFormAdapter):
    def __init__(self, values: Dict[str, str]) -> None:
        self._values: Dict[str, str] = values
        self.opened_with: Optional[ElementFieldResolution] = None

    def open(
        self,
        *,
        entity_uri: str,
        resolution: ElementFieldResolution,
    ) -> Dict[str, str]:
        self.opened_with = resolution
        return self._values


def test_run_returns_the_values_filled_in_the_form(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    dataset_path = tmp_path / "DATASET-ID"
    dataset_path.mkdir()
    context = FillContext(root_path=tmp_path)

    def resolve_container(
        _strategy: ProjectIdStrategy,
        target_context: CliContextPort,
    ) -> CliContextPort:
        target_context.set_parameter_value("project_id", "PROJECT-ID")
        target_context.set_parameter_value("project_path", str(tmp_path))
        return target_context

    monkeypatch.setattr(ProjectIdStrategy, "execute", resolve_container)

    form_adapter = RecordingFormAdapter(
        {"Name": "Wall A", "StartTime": "2026-01-15T00:00:00Z"}
    )
    request = CliCommandRequest(
        logical_component="element",
        component_action="element_fill",
        command_args=[
            "--project",
            "PROJECT-ID",
            "--dataset",
            "DATASET-ID",
            "--entity",
            "https://example.test/Entity",
            "--fill",
        ],
        context=context,
    )
    command = ElementFillCommand(
        request,
        field_resolver=StaticFieldResolver(),
        form_adapter=form_adapter,
    )

    assert command.check()
    response: InteractiveCommandResponse = command.run()

    assert response.description == (
        "Filled 2/2 field(s) (facade) on https://example.test/Entity."
    )
    assert response.content["values"] == {
        "Name": "Wall A",
        "StartTime": "2026-01-15T00:00:00Z",
    }
    assert form_adapter.opened_with is not None
    assert form_adapter.opened_with.field_count == 2
