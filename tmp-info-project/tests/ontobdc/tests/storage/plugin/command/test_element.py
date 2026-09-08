from pathlib import Path
from typing import Any, Dict, List, Optional

import pytest

from ontobdc.cli.adapter.logger import NullLogRepository
from ontobdc.cli.domain.port.context import CliContextPort
from ontobdc.shared.adapter.loader import CommandLoader
from ontobdc.shared.facade.request.command import CliCommandRequest
from ontobdc.shared.facade.response.command import CommandResponse
from ontobdc.storage.plugin.command.element import StorageElementCommand
from ontobdc.storage.plugin.parameter.container import ContainerIdStrategy


class FakeContext(CliContextPort):
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


class StorageElementCommandFactory:
    @staticmethod
    def make(
        context: FakeContext,
        arguments: List[str],
    ) -> StorageElementCommand:
        request: CliCommandRequest = CliCommandRequest(
            logical_component="storage",
            component_action="element",
            command_args=arguments,
            context=context,
        )
        return StorageElementCommand(request)


def test_element_flag_is_not_valued() -> None:
    element_argument: Dict[str, Any] = next(
        argument
        for argument in StorageElementCommand.METADATA.arguments
        if "--element" in argument["accepts"]
    )

    assert element_argument["valued"] is False


def test_container_and_entity_filter_are_valued_selectors() -> None:
    container_argument: Dict[str, Any] = next(
        argument
        for argument in StorageElementCommand.METADATA.arguments
        if "--container" in argument["accepts"]
    )

    assert container_argument["accepts"] == ["--container"]
    assert container_argument["valued"] is True

    entity_argument: Dict[str, Any] = next(
        argument
        for argument in StorageElementCommand.METADATA.arguments
        if "--entity" in argument["accepts"]
    )
    assert entity_argument["valued"] is True


@pytest.mark.parametrize("selector", ["urn:container:example", "/tmp/example"])
def test_accepts_container_selector_followed_by_bare_element(
    selector: str,
) -> None:
    assert StorageElementCommand.accepts(
        ["storage", "--container", selector, "--element"]
    )
    assert StorageElementCommand.accepts(
        [
            "storage",
            "--container",
            selector,
            "--element",
            "--entity",
            "https://example.org/ontology#IfcProject",
        ]
    )


def test_rejects_valued_element() -> None:
    assert not StorageElementCommand.accepts(
        [
            "storage",
            "--container",
            "urn:container:example",
            "--element",
            "element-id",
        ]
    )
    assert not StorageElementCommand.accepts(
        [
            "storage",
            "--container",
            "urn:container:example",
            "--element",
            "--entity",
        ]
    )


def test_rejects_container_id_alias() -> None:
    assert not StorageElementCommand.accepts(
        ["storage", "--container-id", "container-id", "--element"]
    )


def test_storage_loader_discovers_element_command() -> None:
    commands: List[type] = CommandLoader(
        "storage",
        NullLogRepository(),
    ).get_all()

    assert StorageElementCommand in commands


def test_check_resolves_container_filters_and_compacts_elements(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    container_path: Path = tmp_path / "container"
    context: FakeContext = FakeContext(root_path=tmp_path)

    def resolve_container(
        _strategy: ContainerIdStrategy,
        target_context: CliContextPort,
    ) -> CliContextPort:
        assert target_context.get_parameter_value("container") == "container-ref"
        target_context.set_parameter_value("container_id", "container-id")
        target_context.set_parameter_value("container_path", str(container_path))
        return target_context

    monkeypatch.setattr(ContainerIdStrategy, "execute", resolve_container)

    def list_elements(
        _command: StorageElementCommand,
        *,
        container_path: str,
    ) -> List[Dict[str, Any]]:
        assert container_path == str(container_path_value)
        return [
            {
                "id": "global-ifc-project",
                "entity_identifier": "ifc_project",
                "title": "IFC project",
                "facade_name": "IfcProject",
                "source_kind": "dataset_facade_file",
                "iri": "urn:ignored",
            },
            {
                "id": "global-work-schedule",
                "entity_identifier": "ifc_work_schedule",
                "title": "IFC work schedule",
                "facade_name": "IfcWorkSchedule",
                "source_kind": "conforms_to_fallback",
            },
        ]

    container_path_value: Path = container_path
    monkeypatch.setattr(
        StorageElementCommand,
        "_list_data_entity_instances",
        list_elements,
    )
    command: StorageElementCommand = StorageElementCommandFactory.make(
        context,
        [
            "--container",
            "container-ref",
            "--element",
            "--entity",
            "https://example.org/ontology#IfcProject",
        ],
    )

    assert command.check()
    response: CommandResponse = command.run()

    assert response.title == "Storage Element"
    assert response.description == (
        "Listed 1 obdc:DataEntity instance(s) present in the selected "
        "storage container."
    )
    assert response.content == {
        "container_id": "container-id",
        "container_path": str(container_path),
        "elements": [
            {
                "global_id": "global-ifc-project",
                "entity_identifier": "ifc_project",
                "title": "IFC project",
            }
        ],
    }

    unfiltered_command: StorageElementCommand = StorageElementCommandFactory.make(
        context,
        ["--container", "container-ref", "--element"],
    )
    assert unfiltered_command.check()
    unfiltered_response: CommandResponse = unfiltered_command.run()

    assert unfiltered_response.description == (
        "Listed 2 obdc:DataEntity instance(s) present in the selected "
        "storage container."
    )
    assert len(unfiltered_response.content["elements"]) == 2
