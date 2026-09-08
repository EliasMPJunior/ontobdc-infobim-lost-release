from __future__ import annotations

import sys
from pathlib import Path
from typing import Any, Dict

import ifcopenshell

from infobim.ifc.plugin.capability.element.delete import IfcElementDeleteCapability


class FakeContext:
    def __init__(self, **parameters: Any) -> None:
        self._parameters: Dict[str, Any] = dict(parameters)

    def has_parameter(self, name: str) -> bool:
        return name in self._parameters

    def get_parameter_value(self, name: str) -> Any:
        return self._parameters.get(name)


def build_ifc(path: Path) -> str:
    model = ifcopenshell.file(schema="IFC4")
    global_id = ifcopenshell.guid.new()
    model.create_entity("IfcBuildingElementProxy", GlobalId=global_id, Name="Keep me")
    model.write(str(path))
    return global_id


def test_confirmed_true_returns_stub_confirmed_status_without_writing_the_file(
    tmp_path: Path,
) -> None:
    path = tmp_path / "confirmed.ifc"
    global_id = build_ifc(path)
    before = path.read_bytes()

    result = IfcElementDeleteCapability().execute(
        FakeContext(ifc_path=str(path), element_global_id=global_id, confirmed=True)
    )

    assert result["confirmed"] is True
    assert result["deleted"] is False
    assert result["stub"] is True
    assert result["status"] == "stub_confirmed"
    assert path.read_bytes() == before


def test_confirmed_false_returns_cancelled_status_without_writing_the_file(
    tmp_path: Path,
) -> None:
    path = tmp_path / "cancelled.ifc"
    global_id = build_ifc(path)
    before = path.read_bytes()

    result = IfcElementDeleteCapability().execute(
        FakeContext(ifc_path=str(path), element_global_id=global_id, confirmed=False)
    )

    assert result["confirmed"] is False
    assert result["deleted"] is False
    assert result["stub"] is True
    assert result["status"] == "cancelled"
    assert path.read_bytes() == before


def test_missing_confirmed_parameter_defaults_to_cancelled(tmp_path: Path) -> None:
    path = tmp_path / "missing.ifc"
    global_id = build_ifc(path)

    result = IfcElementDeleteCapability().execute(
        FakeContext(ifc_path=str(path), element_global_id=global_id)
    )

    assert result["confirmed"] is False
    assert result["status"] == "cancelled"


def test_target_entity_still_exists_in_the_ifc_file_after_execute(
    tmp_path: Path,
) -> None:
    path = tmp_path / "entity.ifc"
    global_id = build_ifc(path)

    IfcElementDeleteCapability().execute(
        FakeContext(ifc_path=str(path), element_global_id=global_id, confirmed=True)
    )

    reopened = ifcopenshell.open(str(path))
    assert reopened.by_guid(global_id) is not None


def test_nonexistent_ifc_file_raises() -> None:
    context = FakeContext(
        ifc_path="/nonexistent/model.ifc",
        element_global_id="G1",
        confirmed=True,
    )

    try:
        IfcElementDeleteCapability().execute(context)
        assert False, "expected ValueError for a missing IFC file"
    except ValueError as error:
        assert "does not exist" in str(error)


def test_nonexistent_global_id_raises(tmp_path: Path) -> None:
    path = tmp_path / "no_entity.ifc"
    build_ifc(path)

    context = FakeContext(
        ifc_path=str(path),
        element_global_id="does-not-exist",
        confirmed=True,
    )

    try:
        IfcElementDeleteCapability().execute(context)
        assert False, "expected ValueError for an unknown GlobalId"
    except ValueError as error:
        assert "No IFC element" in str(error)


def test_capability_source_never_mentions_any_visual_dependency() -> None:
    import infobim.ifc.plugin.capability.element.delete as module

    source = Path(module.__file__).read_text(encoding="utf-8").lower()
    for forbidden in ("textual", "widget", "app", "footer", "header", "button"):
        assert forbidden not in source, f"capability source mentions '{forbidden}'"


def test_importing_the_capability_never_imports_textual() -> None:
    for module_name in list(sys.modules):
        if module_name == "textual" or module_name.startswith("textual."):
            del sys.modules[module_name]
    for module_name in list(sys.modules):
        if module_name.startswith("infobim.ifc.plugin.capability.element"):
            del sys.modules[module_name]

    import infobim.ifc.plugin.capability.element.delete  # noqa: F401

    assert not any(
        name == "textual" or name.startswith("textual.") for name in sys.modules
    )
