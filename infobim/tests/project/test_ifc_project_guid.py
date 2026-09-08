import uuid

from infobim.project.plugin.capability.transformation.ifc_project_ready import (
    IfcProjectReadyCapability,
)


def test_ifc_guid_compression_matches_buildingsmart_example() -> None:
    source = uuid.UUID("f70dd363-bfe3-495d-84a0-2c02dcb7d4d2")
    assert IfcProjectReadyCapability._compress_ifc_guid(source) == (
        "3t3TDZl_D9NOIWB0BSjzJI"
    )


def test_new_ifc_project_global_id_is_valid_fixed_length() -> None:
    result = IfcProjectReadyCapability._new_ifc_global_id()
    assert len(result) == 22
    assert result[0] in "0123"

