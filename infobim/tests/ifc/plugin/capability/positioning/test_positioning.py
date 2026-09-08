from pathlib import Path
from typing import Any

import ifcopenshell
import pytest

from infobim.ifc.plugin.capability.positioning.linear_element_end_point import (
    LinearElementEndPointCapability,
)
from infobim.ifc.plugin.capability.positioning.linear_element_length import (
    LinearElementLengthCapability,
)
from infobim.ifc.plugin.capability.positioning.linear_element_start_point import (
    LinearElementStartPointCapability,
)
from infobim.ifc.plugin.capability.positioning.move import MoveCapability
from infobim.ifc.plugin.capability.positioning.support import PositioningSupport


class Context:
    def __init__(self, **parameters: Any) -> None:
        self.parameters = parameters

    def has_parameter(self, name: str) -> bool:
        return name in self.parameters

    def get_parameter_value(self, name: str) -> Any:
        return self.parameters[name]


def build_linear_ifc(path: Path) -> str:
    model = ifcopenshell.file(schema="IFC4")
    millimetre = model.create_entity(
        "IfcSIUnit", UnitType="LENGTHUNIT", Prefix="MILLI", Name="METRE"
    )
    units = model.create_entity("IfcUnitAssignment", Units=[millimetre])
    origin = model.create_entity("IfcCartesianPoint", Coordinates=(0.0, 0.0, 0.0))
    world = model.create_entity("IfcAxis2Placement3D", Location=origin)
    context = model.create_entity(
        "IfcGeometricRepresentationContext",
        ContextIdentifier="Model",
        ContextType="Model",
        CoordinateSpaceDimension=3,
        Precision=1.0e-5,
        WorldCoordinateSystem=world,
    )
    model.create_entity(
        "IfcProject",
        GlobalId=ifcopenshell.guid.new(),
        Name="Positioning test",
        RepresentationContexts=[context],
        UnitsInContext=units,
    )

    profile = model.create_entity("IfcCircleProfileDef", ProfileType="AREA", Radius=25.0)
    solid_origin = model.create_entity(
        "IfcCartesianPoint", Coordinates=(0.0, 0.0, 0.0)
    )
    solid_position = model.create_entity("IfcAxis2Placement3D", Location=solid_origin)
    extrusion = model.create_entity("IfcDirection", DirectionRatios=(0.0, 0.0, 1.0))
    solid = model.create_entity(
        "IfcExtrudedAreaSolid",
        SweptArea=profile,
        Position=solid_position,
        ExtrudedDirection=extrusion,
        Depth=1000.0,
    )
    shape = model.create_entity(
        "IfcShapeRepresentation",
        ContextOfItems=context,
        RepresentationIdentifier="Body",
        RepresentationType="SweptSolid",
        Items=[solid],
    )
    product_shape = model.create_entity(
        "IfcProductDefinitionShape", Representations=[shape]
    )
    placement_point = model.create_entity(
        "IfcCartesianPoint", Coordinates=(100.0, 200.0, 300.0)
    )
    placement_axis = model.create_entity(
        "IfcAxis2Placement3D", Location=placement_point
    )
    placement = model.create_entity("IfcLocalPlacement", RelativePlacement=placement_axis)
    global_id = ifcopenshell.guid.new()
    model.create_entity(
        "IfcMember",
        GlobalId=global_id,
        Name="Linear member",
        ObjectPlacement=placement,
        Representation=product_shape,
        PredefinedType="BRACE",
    )
    model.write(str(path))
    return global_id


def endpoints(path: Path, global_id: str):
    model = ifcopenshell.open(str(path))
    target = model.by_guid(global_id)
    return PositioningSupport.endpoints(target)


def test_move_uses_project_units_and_requires_only_one_axis(tmp_path: Path):
    path = tmp_path / "move.ifc"
    global_id = build_linear_ifc(path)

    result = MoveCapability().execute(
        Context(ifc_path=str(path), element_global_id=global_id, z=50.0)
    )

    start, end, _ = endpoints(path, global_id)
    assert start == pytest.approx((100.0, 200.0, 350.0))
    assert end == pytest.approx((100.0, 200.0, 1350.0))
    assert result["offset"] == [0.0, 0.0, 50.0]
    assert result["project_unit_scale_to_si"] == pytest.approx(0.001)


def test_start_point_preserves_end_and_omitted_coordinates(tmp_path: Path):
    path = tmp_path / "start.ifc"
    global_id = build_linear_ifc(path)

    result = LinearElementStartPointCapability().execute(
        Context(ifc_path=str(path), element_global_id=global_id, z=400.0)
    )

    start, end, _ = endpoints(path, global_id)
    assert start == pytest.approx((100.0, 200.0, 400.0))
    assert end == pytest.approx((100.0, 200.0, 1300.0))
    assert result["length"] == pytest.approx(900.0)

    with pytest.raises(ValueError, match="after its start point"):
        LinearElementStartPointCapability().execute(
            Context(ifc_path=str(path), element_global_id=global_id, z=1400.0)
        )


def test_end_point_preserves_start_and_rejects_a_point_before_it(tmp_path: Path):
    path = tmp_path / "end.ifc"
    global_id = build_linear_ifc(path)

    result = LinearElementEndPointCapability().execute(
        Context(ifc_path=str(path), element_global_id=global_id, z=1600.0)
    )
    start, end, _ = endpoints(path, global_id)
    assert start == pytest.approx((100.0, 200.0, 300.0))
    assert end == pytest.approx((100.0, 200.0, 1600.0))
    assert result["length"] == pytest.approx(1300.0)

    with pytest.raises(ValueError, match="after its start point"):
        LinearElementEndPointCapability().execute(
            Context(ifc_path=str(path), element_global_id=global_id, z=200.0)
        )


def test_length_preserves_start_and_direction(tmp_path: Path):
    path = tmp_path / "length.ifc"
    global_id = build_linear_ifc(path)

    result = LinearElementLengthCapability().execute(
        Context(ifc_path=str(path), element_global_id=global_id, l=500.0)
    )

    start, end, direction = endpoints(path, global_id)
    assert start == pytest.approx((100.0, 200.0, 300.0))
    assert end == pytest.approx((100.0, 200.0, 800.0))
    assert direction == pytest.approx((0.0, 0.0, 1.0))
    assert result["new_length"] == pytest.approx(500.0)


def test_length_is_required_and_must_be_positive(tmp_path: Path):
    path = tmp_path / "invalid-length.ifc"
    global_id = build_linear_ifc(path)
    capability = LinearElementLengthCapability()

    with pytest.raises(ValueError, match="required"):
        capability.execute(Context(ifc_path=str(path), element_global_id=global_id))
    with pytest.raises(ValueError, match="greater than zero"):
        capability.execute(
            Context(ifc_path=str(path), element_global_id=global_id, l=0.0)
        )


@pytest.mark.parametrize(
    "capability",
    [MoveCapability(), LinearElementStartPointCapability(), LinearElementEndPointCapability()],
)
def test_coordinate_capabilities_require_at_least_one_axis(
    tmp_path: Path, capability: Any
):
    path = tmp_path / f"{capability.__class__.__name__}.ifc"
    global_id = build_linear_ifc(path)

    with pytest.raises(ValueError, match="At least one"):
        capability.execute(Context(ifc_path=str(path), element_global_id=global_id))


def test_metadata_exposes_four_positioning_contracts():
    capabilities = (
        MoveCapability,
        LinearElementStartPointCapability,
        LinearElementEndPointCapability,
        LinearElementLengthCapability,
    )
    assert [capability.METADATA.name for capability in capabilities] == [
        "Move",
        "Linear Element Start Point",
        "Linear Element End Point",
        "Linear Element Length",
    ]
    for capability in capabilities[:3]:
        properties = capability.METADATA.input_schema["properties"]
        assert all(properties[axis]["required"] is False for axis in ("x", "y", "z"))
    assert capabilities[3].METADATA.input_schema["properties"]["l"]["required"] is True
