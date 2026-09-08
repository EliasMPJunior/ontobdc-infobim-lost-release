import asyncio

from textual.widgets import Input
from textual_datepicker import DateSelect

from infobim.element.adapter.facade_field import (
    ElementField,
    ElementFieldResolution,
    FacadeFieldSource,
)
from infobim.element.adapter.fill_form import ElementFillFormApp, _widget_id


def _resolution(*fields: ElementField) -> ElementFieldResolution:
    return ElementFieldResolution(
        source=FacadeFieldSource.FACADE,
        entity_uri="urn:test:entity#Widget",
        fields=list(fields),
    )


def test_date_and_date_time_fields_get_a_date_select_widget() -> None:
    resolution = _resolution(
        ElementField(
            identifier="StartTime", label="Start Time", datatype="dateTime",
            required=False,
        ),
        ElementField(
            identifier="DueDate", label="Due Date", datatype="date",
            required=False,
        ),
    )
    app = ElementFillFormApp(entity_uri=resolution.entity_uri, resolution=resolution)
    form = list(app.compose())[1]

    widgets = list(form._pending_children)
    date_widgets = [w for w in widgets if isinstance(w, DateSelect)]
    assert {w.id for w in date_widgets} == {
        _widget_id("StartTime"),
        _widget_id("DueDate"),
    }


def test_other_datatypes_keep_a_plain_input_widget() -> None:
    resolution = _resolution(
        ElementField(
            identifier="Name", label="Name", datatype="string", required=True,
        ),
        ElementField(
            identifier="TotalFloat", label="Total Float", datatype="duration",
            required=False,
        ),
    )
    app = ElementFillFormApp(entity_uri=resolution.entity_uri, resolution=resolution)
    form = list(app.compose())[1]

    widgets = list(form._pending_children)
    input_widgets = [w for w in widgets if isinstance(w, Input)]
    assert {w.id for w in input_widgets} == {
        _widget_id("Name"),
        _widget_id("TotalFloat"),
    }
    assert not any(isinstance(w, DateSelect) for w in widgets)


def test_submit_collects_text_input_and_blank_unset_date() -> None:
    resolution = _resolution(
        ElementField(
            identifier="Name", label="Name", datatype="string", required=True,
        ),
        ElementField(
            identifier="StartTime", label="Start Time", datatype="dateTime",
            required=False,
        ),
    )
    app = ElementFillFormApp(entity_uri=resolution.entity_uri, resolution=resolution)

    # Exercise the value-collection logic directly (the same
    # `_read_value` on_button_pressed uses) rather than relying on
    # App.exit's captured return value, since App.run_test() doesn't
    # surface it the way App.run() does.
    async def _collect() -> dict:
        async with app.run_test():
            app.query_one(f"#{_widget_id('Name')}", Input).value = "Wall A"
            return {
                field.identifier: app._read_value(field)
                for field in resolution.fields
            }

    values = asyncio.run(_collect())
    assert values == {"Name": "Wall A", "StartTime": ""}
