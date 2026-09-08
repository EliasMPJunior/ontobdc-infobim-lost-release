from pathlib import Path
from typing import Any, Dict, Optional, Tuple

import ifcopenshell
import pytest

from infobim.ifc.adapter.bounding_volume import BoundingVolumeService
from infobim.ifc.plugin.capability.measurement.linear_distance import (
    IfcBoundingVolumeLinearDistanceCapability,
)


Point3D = Tuple[float, float, float]


class LinearDistanceContext:
    def __init__(self, **parameters: Any) -> None:
        self._parameters: Dict[str, Any] = parameters

    def has_parameter(self, name: str) -> bool:
        return name in self._parameters

    def get_parameter_value(self, name: str) -> Any:
        return self._parameters[name]


class LinearDistanceFixture:
    def __init__(self, path: Path, millimetres: bool = False) -> None:
        self.path: Path = path
        self.model: Any = ifcopenshell.file(schema="IFC4")
        unit: Any = self.model.create_entity(
            "IfcSIUnit",
            UnitType="LENGTHUNIT",
            Prefix="MILLI" if millimetres else None,
            Name="METRE",
        )
        units: Any = self.model.create_entity("IfcUnitAssignment", Units=[unit])
        origin: Any = self._point((0.0, 0.0, 0.0))
        world: Any = self.model.create_entity("IfcAxis2Placement3D", Location=origin)
        self.context: Any = self.model.create_entity(
            "IfcGeometricRepresentationContext",
            ContextIdentifier="Model",
            ContextType="Model",
            CoordinateSpaceDimension=3,
            Precision=1.0e-5,
            WorldCoordinateSystem=world,
        )
        self.model.create_entity(
            "IfcProject",
            GlobalId=ifcopenshell.guid.new(),
            Name="Linear-distance test",
            RepresentationContexts=[self.context],
            UnitsInContext=units,
        )

    def annotation(
        self,
        kind: str,
        placement: Point3D,
        local_center: Point3D,
        axis: Point3D = (0.0, 0.0, 1.0),
    ) -> str:
        if kind == "box":
            item: Any = self.model.create_entity(
                "IfcBoundingBox",
                Corner=self._point(
                    (
                        local_center[0] - 1.0,
                        local_center[1] - 1.0,
                        local_center[2] - 1.0,
                    )
                ),
                XDim=2.0,
                YDim=2.0,
                ZDim=2.0,
            )
            identifier: str = "Box"
            representation_type: str = "BoundingBox"
        elif kind == "cylinder":
            bottom_center: Point3D = (
                local_center[0] - axis[0] * 2.0,
                local_center[1] - axis[1] * 2.0,
                local_center[2] - axis[2] * 2.0,
            )
            item = self.model.create_entity(
                "IfcRightCircularCylinder",
                Position=self._axis_placement(bottom_center, axis),
                Height=4.0,
                Radius=1.0,
            )
            identifier = "Reference"
            representation_type = "CSG"
        else:
            item = self.model.create_entity(
                "IfcSphere",
                Position=self._axis_placement(local_center),
                Radius=1.0,
            )
            identifier = "Reference"
            representation_type = "CSG"

        representation: Any = self.model.create_entity(
            "IfcShapeRepresentation",
            ContextOfItems=self.context,
            RepresentationIdentifier=identifier,
            RepresentationType=representation_type,
            Items=[item],
        )
        product_shape: Any = self.model.create_entity(
            "IfcProductDefinitionShape", Representations=[representation]
        )
        global_id: str = ifcopenshell.guid.new()
        self.model.create_entity(
            "IfcAnnotation",
            GlobalId=global_id,
            Name=f"{kind} bounding volume",
            ObjectType=BoundingVolumeService.OBJECT_TYPE,
            ObjectPlacement=self.model.create_entity(
                "IfcLocalPlacement",
                RelativePlacement=self._axis_placement(placement),
            ),
            Representation=product_shape,
        )
        return global_id

    def save(self) -> None:
        self.model.write(str(self.path))

    def _point(self, coordinates: Point3D) -> Any:
        return self.model.create_entity(
            "IfcCartesianPoint", Coordinates=coordinates
        )

    def _axis_placement(
        self,
        location: Point3D,
        axis: Point3D = (0.0, 0.0, 1.0),
    ) -> Any:
        reference: Point3D = (
            (0.0, 1.0, 0.0) if abs(axis[0]) > 0.9 else (1.0, 0.0, 0.0)
        )
        return self.model.create_entity(
            "IfcAxis2Placement3D",
            Location=self._point(location),
            Axis=self.model.create_entity("IfcDirection", DirectionRatios=axis),
            RefDirection=self.model.create_entity(
                "IfcDirection", DirectionRatios=reference
            ),
        )


class TestIfcBoundingVolumeLinearDistanceCapability:
    def test_measures_straight_line_between_world_centers(self, tmp_path: Path) -> None:
        path: Path = tmp_path / "straight.ifc"
        fixture: LinearDistanceFixture = LinearDistanceFixture(path)
        first: str = fixture.annotation("box", (10.0, 20.0, 30.0), (1.0, 2.0, 3.0))
        second: str = fixture.annotation("sphere", (14.0, 26.0, 45.0), (0.0, 0.0, 0.0))
        fixture.save()

        result: Dict[str, Any] = self._execute(path, first, second, "STRAIGHT_LINE")

        assert result["first_center"] == pytest.approx((11.0, 22.0, 33.0))
        assert result["second_center"] == pytest.approx((14.0, 26.0, 45.0))
        assert result["measurement_vector"] == pytest.approx((3.0, 4.0, 12.0))
        assert result["distance"] == pytest.approx(13.0)
        assert result["signed_distance"] is None
        assert result["plane_normal"] is None

    @pytest.mark.parametrize(
        ("axis", "distance", "signed", "normal"),
        [
            ("x", 3.0, 3.0, (1.0, 0.0, 0.0)),
            ("y", 4.0, 4.0, (0.0, 1.0, 0.0)),
            ("z", 12.0, 12.0, (0.0, 0.0, 1.0)),
        ],
    )
    def test_measures_parallel_planes_normal_to_global_axis(
        self,
        tmp_path: Path,
        axis: str,
        distance: float,
        signed: float,
        normal: Point3D,
    ) -> None:
        path: Path = tmp_path / f"planes-{axis}.ifc"
        fixture: LinearDistanceFixture = LinearDistanceFixture(path)
        first: str = fixture.annotation("box", (10.0, 20.0, 30.0), (1.0, 2.0, 3.0))
        second: str = fixture.annotation("sphere", (14.0, 26.0, 45.0), (0.0, 0.0, 0.0))
        fixture.save()

        result: Dict[str, Any] = self._execute(
            path, first, second, "PARALLEL_PLANES", axis
        )

        assert result["distance"] == pytest.approx(distance)
        assert result["signed_distance"] == pytest.approx(signed)
        assert result["plane_normal"] == pytest.approx(normal)

    def test_resolves_a_rotated_cylinder_center(self, tmp_path: Path) -> None:
        path: Path = tmp_path / "cylinder.ifc"
        fixture: LinearDistanceFixture = LinearDistanceFixture(path)
        first: str = fixture.annotation(
            "cylinder", (10.0, 20.0, 30.0), (5.0, 2.0, 3.0), axis=(1.0, 0.0, 0.0)
        )
        second: str = fixture.annotation("sphere", (20.0, 22.0, 33.0), (0.0, 0.0, 0.0))
        fixture.save()

        result: Dict[str, Any] = self._execute(path, first, second, "STRAIGHT_LINE")

        assert result["first_center"] == pytest.approx((15.0, 22.0, 33.0))
        assert result["second_center"] == pytest.approx((20.0, 22.0, 33.0))
        assert result["distance"] == pytest.approx(5.0)

    def test_rejects_invalid_mode_axis_combinations(self, tmp_path: Path) -> None:
        path: Path = tmp_path / "invalid.ifc"
        fixture: LinearDistanceFixture = LinearDistanceFixture(path)
        first: str = fixture.annotation("box", (0.0, 0.0, 0.0), (0.0, 0.0, 0.0))
        second: str = fixture.annotation("sphere", (1.0, 0.0, 0.0), (0.0, 0.0, 0.0))
        fixture.save()

        with pytest.raises(ValueError, match="not accepted"):
            self._execute(path, first, second, "STRAIGHT_LINE", "x")
        with pytest.raises(ValueError, match="must be one of"):
            self._execute(path, first, second, "PARALLEL_PLANES")

    def test_reports_project_unit_scale_without_converting_distance(
        self, tmp_path: Path
    ) -> None:
        path: Path = tmp_path / "millimetres.ifc"
        fixture: LinearDistanceFixture = LinearDistanceFixture(path, millimetres=True)
        first: str = fixture.annotation("box", (0.0, 0.0, 0.0), (0.0, 0.0, 0.0))
        second: str = fixture.annotation("sphere", (3000.0, 4000.0, 0.0), (0.0, 0.0, 0.0))
        fixture.save()

        result: Dict[str, Any] = self._execute(path, first, second, "STRAIGHT_LINE")

        assert result["distance"] == pytest.approx(5000.0)
        assert result["project_unit_scale_to_si"] == pytest.approx(0.001)

    @staticmethod
    def _execute(
        path: Path,
        first: str,
        second: str,
        mode: str,
        axis: Optional[str] = None,
    ) -> Dict[str, Any]:
        parameters: Dict[str, Any] = {
            "ifc_path": str(path),
            "first_bounding_volume_global_id": first,
            "second_bounding_volume_global_id": second,
            "measurement_mode": mode,
        }
        if axis is not None:
            parameters["axis"] = axis
        return IfcBoundingVolumeLinearDistanceCapability().execute(
            LinearDistanceContext(**parameters)
        )
