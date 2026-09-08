from pathlib import Path
from typing import Any, Dict, Tuple

import ifcopenshell
import ifcopenshell.geom
import ifcopenshell.validate
import pytest

from infobim.ifc.plugin.capability.geometry.bounding_volume import (
    IfcBoundingVolumeCapability,
)


class BoundingVolumeContext:
    def __init__(self, **parameters: Any) -> None:
        self._parameters: Dict[str, Any] = parameters

    def has_parameter(self, name: str) -> bool:
        return name in self._parameters

    def get_parameter_value(self, name: str) -> Any:
        return self._parameters[name]


class BoundingVolumeFixture:
    @staticmethod
    def create(
        path: Path,
        shape_kind: str,
        dimensions: Tuple[float, ...],
        millimetres: bool = False,
    ) -> str:
        model: Any = ifcopenshell.file(schema="IFC4")
        unit: Any = model.create_entity(
            "IfcSIUnit",
            UnitType="LENGTHUNIT",
            Prefix="MILLI" if millimetres else None,
            Name="METRE",
        )
        units: Any = model.create_entity("IfcUnitAssignment", Units=[unit])
        origin: Any = model.create_entity(
            "IfcCartesianPoint", Coordinates=(0.0, 0.0, 0.0)
        )
        world: Any = model.create_entity("IfcAxis2Placement3D", Location=origin)
        context: Any = model.create_entity(
            "IfcGeometricRepresentationContext",
            ContextIdentifier="Model",
            ContextType="Model",
            CoordinateSpaceDimension=3,
            Precision=1.0e-5,
            WorldCoordinateSystem=world,
        )
        body_context: Any = model.create_entity(
            "IfcGeometricRepresentationSubContext",
            ContextIdentifier="Body",
            ContextType="Model",
            ParentContext=context,
            TargetView="MODEL_VIEW",
        )
        model.create_entity(
            "IfcProject",
            GlobalId=ifcopenshell.guid.new(),
            Name="Bounding-volume test",
            RepresentationContexts=[context],
            UnitsInContext=units,
        )

        solid_position: Any = model.create_entity(
            "IfcAxis2Placement3D",
            Location=model.create_entity(
                "IfcCartesianPoint", Coordinates=(0.0, 0.0, 0.0)
            ),
            Axis=model.create_entity(
                "IfcDirection", DirectionRatios=(0.0, 0.0, 1.0)
            ),
            RefDirection=model.create_entity(
                "IfcDirection", DirectionRatios=(1.0, 0.0, 0.0)
            ),
        )
        if shape_kind == "block":
            item: Any = model.create_entity(
                "IfcBlock",
                Position=solid_position,
                XLength=dimensions[0],
                YLength=dimensions[1],
                ZLength=dimensions[2],
            )
        elif shape_kind == "cylinder":
            profile: Any = model.create_entity(
                "IfcCircleProfileDef",
                ProfileType="AREA",
                Radius=dimensions[0],
            )
            item = model.create_entity(
                "IfcExtrudedAreaSolid",
                SweptArea=profile,
                Position=solid_position,
                ExtrudedDirection=model.create_entity(
                    "IfcDirection", DirectionRatios=(0.0, 0.0, 1.0)
                ),
                Depth=dimensions[1],
            )
        else:
            item = model.create_entity(
                "IfcSphere", Position=solid_position, Radius=dimensions[0]
            )
        shape: Any = model.create_entity(
            "IfcShapeRepresentation",
            ContextOfItems=body_context,
            RepresentationIdentifier="Body",
            RepresentationType=("SweptSolid" if shape_kind == "cylinder" else "CSG"),
            Items=[item],
        )
        product_shape: Any = model.create_entity(
            "IfcProductDefinitionShape", Representations=[shape]
        )
        placement: Any = model.create_entity(
            "IfcLocalPlacement",
            RelativePlacement=model.create_entity(
                "IfcAxis2Placement3D",
                Location=model.create_entity(
                    "IfcCartesianPoint", Coordinates=(100.0, 200.0, 300.0)
                ),
            ),
        )
        global_id: str = ifcopenshell.guid.new()
        model.create_entity(
            "IfcBuildingElementProxy",
            GlobalId=global_id,
            Name=f"Source {shape_kind}",
            ObjectPlacement=placement,
            Representation=product_shape,
            PredefinedType="NOTDEFINED",
        )
        model.write(str(path))
        return global_id


class TestIfcBoundingVolumeCapability:
    @pytest.mark.parametrize(
        ("shape_kind", "dimensions", "expected_kind", "expected_item"),
        [
            (
                "block",
                (4.0, 2.0, 1.0),
                "RECTANGULAR_CUBOID",
                "IfcBoundingBox",
            ),
            (
                "cylinder",
                (1.0, 4.0),
                "CYLINDER",
                "IfcRightCircularCylinder",
            ),
            ("sphere", (1.0,), "SPHERE", "IfcSphere"),
        ],
    )
    def test_selects_and_attaches_smallest_supported_volume(
        self,
        tmp_path: Path,
        shape_kind: str,
        dimensions: Tuple[float, ...],
        expected_kind: str,
        expected_item: str,
    ) -> None:
        path: Path = tmp_path / f"{shape_kind}.ifc"
        global_id: str = BoundingVolumeFixture.create(path, shape_kind, dimensions)

        result: Dict[str, Any] = IfcBoundingVolumeCapability().execute(
            BoundingVolumeContext(
                ifc_path=str(path), element_global_id=global_id
            )
        )

        assert result["selected_shape"] == expected_kind
        assert result["bounding_volume"] >= result["element_volume"]
        assert result["extra_volume"] == pytest.approx(
            result["bounding_volume"] - result["element_volume"]
        )
        model: Any = ifcopenshell.open(str(path))
        target: Any = model.by_guid(global_id)
        assignments: Any = [
            assignment
            for assignment in model.by_type("IfcRelAssignsToProduct")
            if assignment.RelatingProduct == target
        ]
        assert len(assignments) == 1
        annotation: Any = assignments[0].RelatedObjects[0]
        assert annotation.is_a("IfcAnnotation")
        assert annotation.ObjectType == "INFOBIM_BOUNDING_VOLUME"
        assert annotation.GlobalId == result["annotation_global_id"]
        representation: Any = annotation.Representation.Representations[0]
        assert representation.Items[0].is_a(expected_item)
        assert len(target.Representation.Representations) == 1
        if expected_item != "IfcBoundingBox":
            settings: Any = ifcopenshell.geom.settings()
            assert ifcopenshell.geom.create_shape(settings, representation) is not None
        logger: Any = ifcopenshell.validate.json_logger()
        ifcopenshell.validate.validate(model, logger, express_rules=True)
        assert logger.statements == []

    def test_preserves_project_units_in_millimetres(self, tmp_path: Path) -> None:
        path: Path = tmp_path / "millimetres.ifc"
        global_id: str = BoundingVolumeFixture.create(
            path, "block", (4000.0, 2000.0, 1000.0), millimetres=True
        )

        result: Dict[str, Any] = IfcBoundingVolumeCapability().execute(
            BoundingVolumeContext(
                ifc_path=str(path), element_global_id=global_id
            )
        )

        assert result["selected_shape"] == "RECTANGULAR_CUBOID"
        assert result["bounding_volume"] == pytest.approx(8_000_000_000.0)
        assert result["project_unit_scale_to_si"] == pytest.approx(0.001)
        model: Any = ifcopenshell.open(str(path))
        bounding_box: Any = model.by_type("IfcBoundingBox")[0]
        assert (bounding_box.XDim, bounding_box.YDim, bounding_box.ZDim) == pytest.approx(
            (4000.0, 2000.0, 1000.0)
        )

    def test_rejects_a_second_bounding_volume(self, tmp_path: Path) -> None:
        path: Path = tmp_path / "duplicate.ifc"
        global_id: str = BoundingVolumeFixture.create(
            path, "block", (4.0, 2.0, 1.0)
        )
        capability: IfcBoundingVolumeCapability = IfcBoundingVolumeCapability()
        context: BoundingVolumeContext = BoundingVolumeContext(
            ifc_path=str(path), element_global_id=global_id
        )
        capability.execute(context)

        with pytest.raises(ValueError, match="already has an IFC bounding-volume"):
            capability.execute(context)

    def test_metadata_declares_transaction_contract(self) -> None:
        properties: Dict[str, Any] = IfcBoundingVolumeCapability.METADATA.input_schema[
            "properties"
        ]
        assert properties["ifc_path"]["required"] is True
        assert properties["element_global_id"]["required"] is True
