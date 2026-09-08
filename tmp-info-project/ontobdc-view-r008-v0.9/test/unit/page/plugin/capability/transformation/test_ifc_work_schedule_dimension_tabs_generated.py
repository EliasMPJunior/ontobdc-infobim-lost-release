from __future__ import annotations

from typing import Any, Dict, List

from ontobdc_view.page.adapter.context import PageDataContextAdapter
from ontobdc_view.page.plugin.capability.transformation.ifc_work_schedule_dimension_tabs_generated import (
    IfcWorkScheduleDimensionTabsGeneratedCapability,
)


class FakeCliContext:
    raw_args: List[str] = []
    unprocessed_args: List[str] = []
    is_capability_targeted = False
    target_capability_id = None
    root_path = ""
    language = "en"

    def __init__(self, values: Dict[str, Any] | None = None) -> None:
        self.values = dict(values or {})

    def has_parameter(self, key: str) -> bool:
        return key in self.values

    def get_parameter_value(self, key: str) -> Any:
        return self.values.get(key)

    def set_parameter_value(self, key: str, value: Any) -> None:
        self.values[key] = value

    def delete_parameter(self, key: str) -> None:
        self.values.pop(key, None)

    def clear_parameters(self, keys: List[str]) -> None:
        for key in keys:
            self.delete_parameter(key)

    def reload(self) -> None:
        pass


def test_only_populated_dimensions_become_tabs() -> None:
    payload = {
        "facades": [
            {
                "facade": "urn:facade:schedule",
                "fields": [
                    {
                        "name": "ScopeName",
                        "mapped_property": "urn:property:scope-name",
                        "dimension_kind": "urn:dimension:Scope",
                        "field_order": 1,
                    },
                    {
                        "name": "Start",
                        "mapped_property": "urn:property:start",
                        "dimension_kind": "urn:dimension:Time",
                        "field_order": 2,
                    },
                    {
                        "name": "Finish",
                        "mapped_property": "urn:property:finish",
                        "dimension_kind": "urn:dimension:Time",
                        "field_order": 3,
                    },
                    {
                        "name": "ActualCost",
                        "mapped_property": "urn:property:actual-cost",
                        "dimension_kind": "urn:dimension:Cost",
                        "field_order": 4,
                    },
                    {
                        "name": "ProgressMarker",
                        "dimension_kind": "urn:dimension:Progress",
                        "field_order": 5,
                    },
                ],
            }
        ],
        "fields": {
            "ScopeName": "Mobilization",
            "Start": "2026-09-01",
            "Finish": "2026-09-03",
        },
    }
    context = PageDataContextAdapter(
        FakeCliContext(),
        element_uri="urn:element",
        entity_uri="urn:entity:IfcWorkSchedule",
        source_node={},
        payload=payload,
    )

    result = IfcWorkScheduleDimensionTabsGeneratedCapability().execute(context)

    assert result == {"resulting_state": "__dimension_tabs_generated__"}
    assert payload["dimensions"] == [
        {
            "kind": "Scope",
            "label": "Scope",
            "fields": [
                {"name": "ScopeName", "value": "Mobilization"},
            ],
        },
        {
            "kind": "Time",
            "label": "Time",
            "fields": [
                {"name": "Start", "value": "2026-09-01"},
                {"name": "Finish", "value": "2026-09-03"},
            ],
        },
    ]


def test_dimension_tab_label_is_humanized() -> None:
    payload = {
        "facades": [
            {
                "facade": "urn:facade:schedule",
                "fields": [
                    {
                        "name": "PlannedCrew",
                        "mapped_property": "urn:property:planned-crew",
                        "dimension_kind": "urn:dimension:LaborPlanned",
                    }
                ],
            }
        ],
        "fields": {"PlannedCrew": "12"},
    }
    context = PageDataContextAdapter(
        FakeCliContext(),
        element_uri="urn:element",
        entity_uri="urn:entity:IfcWorkSchedule",
        source_node={},
        payload=payload,
    )

    IfcWorkScheduleDimensionTabsGeneratedCapability().execute(context)

    assert payload["dimensions"][0]["label"] == "Labor Planned"
