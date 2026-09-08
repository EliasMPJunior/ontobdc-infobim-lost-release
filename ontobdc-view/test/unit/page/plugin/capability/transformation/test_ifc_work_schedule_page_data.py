from __future__ import annotations

from typing import Any, Dict, List

from ontobdc_view.page.adapter.context import PageDataContextAdapter
from ontobdc_view.page.adapter.facade import FacadeLookupAdapter
from ontobdc_view.page.adapter.entity_page import EntityPageOntologyAdapter
from ontobdc_view.page.plugin.builder.ifc_work_schedule.ifc_work_schedule import (
    IfcWorkSchedulePageGenerationDataTransitionHandler,
)
from ontobdc_view.page.plugin.capability.transformation.ifc_work_schedule_gantt_payload_gathered import (
    IfcWorkScheduleGanttPayloadGatheredCapability,
)
from ontobdc.shared.adapter.capability import CapabilityExecutor


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


def test_page_data_context_keeps_element_writes_out_of_parent() -> None:
    parent = FakeCliContext({"container_path": "/container"})
    context = PageDataContextAdapter(
        parent,
        element_uri="urn:element",
        entity_uri="urn:entity",
        source_node={},
    )

    context.set_parameter_value("runtime_value", "local")

    assert context.get_parameter_value("container_path") == "/container"
    assert context.get_parameter_value("runtime_value") == "local"
    assert parent.get_parameter_value("runtime_value") is None


def test_sismic_statechart_executes_page_data_capabilities(monkeypatch: Any) -> None:
    mapped_property = "urn:property:title"
    missing_property = "urn:property:missing"
    source_node = {mapped_property: [{"@value": "Schedule"}]}
    facades = [
        {
            "facade": "urn:facade",
            "fields": [
                {"name": "title", "mapped_property": mapped_property},
                {"name": "missing", "mapped_property": missing_property},
            ],
        }
    ]
    monkeypatch.setattr(
        FacadeLookupAdapter,
        "locate_facades_for_element",
        lambda context, element_uri, entity_uri: facades,
    )
    toolbar_configuration = {"@graph": [{"@id": "urn:toolbar:ifc"}]}
    monkeypatch.setattr(
        EntityPageOntologyAdapter,
        "toolbar_configuration",
        lambda self, entity_uri: toolbar_configuration,
    )
    executed_capabilities: List[str] = []
    execute_capability = CapabilityExecutor.execute

    def record_execution(capability: Any, context: Any) -> Dict[str, Any]:
        executed_capabilities.append(type(capability).__name__)
        return execute_capability(capability, context)

    monkeypatch.setattr(CapabilityExecutor, "execute", record_execution)

    payload = IfcWorkSchedulePageGenerationDataTransitionHandler().build_payload(
        context=FakeCliContext(),
        element_uri="urn:element",
        entity_uri="urn:entity",
        source_node=source_node,
    )

    assert payload == {
        mapped_property: [{"@value": "Schedule"}],
        "facades": facades,
        "fields": {"title": "Schedule"},
        "missing_fields": ["missing"],
        "@graph": [source_node],
        "gantt_payload": None,
        "gantt_script_names": list(
            IfcWorkScheduleGanttPayloadGatheredCapability.SCRIPT_NAMES
        ),
        "related_entities": [],
        "dimensions": [],
        "toolbar_configuration": toolbar_configuration,
    }
    assert executed_capabilities == [
        "FacadesLocatedCapability",
        "FacadeDataGatheredCapability",
        "IfcWorkScheduleGanttPayloadGatheredCapability",
        "MissingDataFilledCapability",
        "IfcWorkScheduleDimensionTabsGeneratedCapability",
        "RelatedEntitiesResolvedCapability",
        "ToolbarConfigurationGatheredCapability",
    ]
