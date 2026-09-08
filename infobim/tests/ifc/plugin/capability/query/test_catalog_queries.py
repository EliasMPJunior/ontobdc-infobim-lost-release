from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List, Optional, Set

from infobim.ifc.adapter.class_catalog import IfcClassCatalogRepository
from infobim.ifc.plugin.capability.query.class_elements import (
    IfcClassElementsQueryCapability,
)
from infobim.ifc.plugin.capability.query.classes import IfcClassesQueryCapability
from infobim.ifc.plugin.capability.query.element import IfcElementQueryCapability
from ontobdc.cli.domain.port.context import CliContextPort
from ontobdc.shared.adapter.capability import CapabilityExecutor
from ontobdc.shared.adapter.loader import CapabilityLoader


class QueryContext(CliContextPort):
    def __init__(self, **parameters: Any) -> None:
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


def test_classes_query_delegates_to_the_catalog_repository(
    tmp_path: Path,
    monkeypatch: Any,
) -> None:
    expected: Dict[str, Any] = {
        "project_path": str(tmp_path),
        "class_count": 1,
        "element_count": 2,
        "classes": [{"class_name": "IfcWall", "element_count": 2}],
    }
    monkeypatch.setattr(
        IfcClassCatalogRepository,
        "list_classes",
        lambda self: expected,
    )

    result: Dict[str, Any] = CapabilityExecutor.execute(
        IfcClassesQueryCapability(),
        QueryContext(project_path=str(tmp_path)),
    )

    assert result == expected


def test_class_elements_query_forwards_the_class_parameter(
    tmp_path: Path,
    monkeypatch: Any,
) -> None:
    observed: Dict[str, str] = {}

    def list_elements(
        repository: IfcClassCatalogRepository,
        class_name: str,
    ) -> Dict[str, Any]:
        observed["project_path"] = str(repository._project_path)
        observed["class_name"] = class_name
        return {
            "project_path": str(tmp_path),
            "class_name": class_name,
            "class_uri": "urn:ifc:IfcWall",
            "dataset_count": 1,
            "datasets": [],
            "element_count": 0,
            "elements": [],
        }

    monkeypatch.setattr(IfcClassCatalogRepository, "list_elements", list_elements)

    result: Dict[str, Any] = CapabilityExecutor.execute(
        IfcClassElementsQueryCapability(),
        QueryContext(project_path=str(tmp_path), ifc_class="IfcWall"),
    )

    assert observed == {
        "project_path": str(tmp_path),
        "class_name": "IfcWall",
    }
    assert result["class_name"] == "IfcWall"


def test_element_query_forwards_the_global_id(
    tmp_path: Path,
    monkeypatch: Any,
) -> None:
    observed: Dict[str, str] = {}

    def get_element(
        repository: IfcClassCatalogRepository,
        global_id: str,
    ) -> Dict[str, Any]:
        observed["project_path"] = str(repository._project_path)
        observed["global_id"] = global_id
        return {
            "project_path": str(tmp_path),
            "global_id": global_id,
            "found": True,
            "class_uri": "urn:ifc:IfcWall",
            "class_name": "IfcWall",
            "dataset_count": 1,
            "datasets": [],
            "element": {"GlobalId": global_id},
        }

    monkeypatch.setattr(IfcClassCatalogRepository, "get_element", get_element)

    result: Dict[str, Any] = CapabilityExecutor.execute(
        IfcElementQueryCapability(),
        QueryContext(
            project_path=str(tmp_path),
            element_global_id="wall-global-id",
        ),
    )

    assert observed == {
        "project_path": str(tmp_path),
        "global_id": "wall-global-id",
    }
    assert result["found"] is True


def test_infobim_capability_loader_discovers_the_query_capabilities() -> None:
    capability_ids: Set[str] = {
        capability.METADATA.id
        for capability in CapabilityLoader(root_packages=("infobim",)).get_all()
    }

    assert {
        IfcClassesQueryCapability.METADATA.id,
        IfcClassElementsQueryCapability.METADATA.id,
        IfcElementQueryCapability.METADATA.id,
    }.issubset(capability_ids)
