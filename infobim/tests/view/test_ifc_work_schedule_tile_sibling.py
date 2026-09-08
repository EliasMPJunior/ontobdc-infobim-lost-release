"""The IFC Work Schedule Tile is WorkStream's sibling.

Both summarize one named entity, so on a Surface carrying both they have to
read as a matched pair: same size envelope, same information architecture,
same shell. Before this, the schedule declared a different envelope (3-8
columns, 2-5 rows against WorkStream's fixed 6x3) and rendered every
property as a raw key/value list on its face — including the facade IRI —
with no identifier line, no description, no footer and no chip.
"""
from pathlib import Path

import pytest
from ontobdc_view.component.plugin.workstream_tile import WorkStreamTileComponent

from infobim.view.plugin.component.ifc_work_schedule import IfcWorkScheduleTileComponent

SOURCE = (
    Path(__file__).resolve().parents[2]
    / "src/infobim/view/plugin/asset/js/onto-infobim-ifc-work-schedule-tile.js"
).read_text(encoding="utf-8")

REFERENCE = IfcWorkScheduleTileComponent.METADATA
SIBLING = WorkStreamTileComponent.METADATA


@pytest.mark.parametrize(
    "attribute",
    ["min_columns", "max_columns", "min_rows", "max_rows", "size_property", "chars_per_column"],
)
def test_size_envelope_matches_the_sibling(attribute):
    assert getattr(REFERENCE, attribute) == getattr(SIBLING, attribute)


@pytest.mark.parametrize(
    "selector",
    [".tile", ".label", ".body", ".name", ".identifier", ".description", ".fields", ".footer", ".dims", ".badge"],
)
def test_shell_carries_the_same_parts(selector):
    assert f'class="{selector.lstrip(".")}"' in SOURCE or f"{selector} {{" in SOURCE


def test_the_face_promotes_title_identifier_and_description():
    for element in (".name", ".identifier", ".description"):
        assert f'querySelector("{element}")' in SOURCE


def test_remaining_properties_stay_behind_the_expand_toggle():
    # The bug this replaces: every property dumped into a <dl> on the face.
    assert "<dl>" not in SOURCE
    assert "expand-btn" in SOURCE
    assert "#populatedFields" in SOURCE


def test_an_iri_value_is_humanized_rather_than_printed_raw():
    """A bare facade URL on a summary Tile is noise; the IRI survives as the
    value's tooltip so the pointer is not lost."""
    assert "#humanize(reference)" in SOURCE
    assert "valueEl.title = title" in SOURCE


def test_the_chip_and_labels_come_from_the_catalog():
    for key in ("badge", "eyebrow", "expand", "collapse", "noDetailsToShow"):
        assert f't("{key}")' in SOURCE


def test_it_links_to_the_standalone_page_published_for_the_schedule():
    """IfcWorkScheduleViewPage declares path_segment "ifc_work_schedule" and
    EntityViewsPublishedCapability writes it to
    `.__ontobdc__/view/<segment>/<identifier>.html`, so the Tile has the same
    open action its sibling has. Asserted against the page plugin's own
    declaration rather than a copied string."""
    from ontobdc_view.page.plugin.ifc_work_schedule_view import IfcWorkScheduleViewPage

    segment = IfcWorkScheduleViewPage.METADATA.path_segment
    assert f'const VIEW_PATH_SEGMENT = "{segment}"' in SOURCE
    assert ".__ontobdc__/view/${VIEW_PATH_SEGMENT}/" in SOURCE
    assert 'class="icon-btn open-link"' in SOURCE


def test_the_page_renderer_matches_the_type_this_tile_matches():
    from ontobdc_view.page.plugin.ifc_work_schedule_view import IfcWorkScheduleViewPage

    assert set(IfcWorkScheduleViewPage.METADATA.required_uris) == set(REFERENCE.required_uris)


def test_the_open_link_carries_presentation_state_on_its_own():
    """Same self-sufficiency rule every Tile is held to: prefer the page's
    url-state runtime, never depend on it."""
    import re

    assert "decorateInternalUrl" in SOURCE
    assert not re.search(r"ontobdcUrlState\?\.\s*decorate", SOURCE)
    assert "searchParams.set(name, carried)" in SOURCE
