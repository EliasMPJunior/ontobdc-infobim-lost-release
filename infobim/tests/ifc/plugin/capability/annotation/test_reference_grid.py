import pytest

from infobim.ifc.plugin.capability.annotation.reference_grid import ReferenceGridCapability


def test_x_axis_labels_repeat_each_symbol_after_alphabet():
    tags = ReferenceGridCapability._repeated_symbol_tags(tuple("ABC"), 8)
    assert tags == ["A", "B", "C", "AA", "BB", "CC", "AAA", "BBB"]


def test_z_axis_labels_use_greek_symbols_and_then_repeat():
    tags = ReferenceGridCapability._repeated_symbol_tags(tuple("αβγ"), 7)
    assert tags == ["α", "β", "γ", "αα", "ββ", "γγ", "ααα"]


def test_axis_positions_reject_non_positive_spacing():
    with pytest.raises(ValueError, match="greater than zero"):
        ReferenceGridCapability._axis_positions(0.0, 10.0, 0.0)
    with pytest.raises(ValueError, match="greater than zero"):
        ReferenceGridCapability._axis_positions(0.0, 10.0, -1.0)


def test_axis_positions_cover_requested_range():
    assert ReferenceGridCapability._axis_positions(0.0, 5.0, 2.0) == [0.0, 2.0, 4.0, 6.0]


def test_metadata_identifies_annotation_not_transformation_state():
    capability = ReferenceGridCapability
    assert capability.METADATA.name == "Reference Grid"
    assert capability.METADATA.id == "org.infobim.ifc.plugin.capability.annotation.reference_grid"
    assert "transformation" not in capability.METADATA.id
    assert "created" not in capability.METADATA.id
