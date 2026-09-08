from __future__ import annotations

import re
from typing import Any, Dict, List

from ontobdc.cli.domain.port.context import CliContextPort
from ontobdc.shared.adapter.capability import TransformationCapability
from ontobdc.shared.domain.model.capability import CapabilityMetadata
from ontobdc_view.page.adapter.context import PageDataContextAdapter


class IfcWorkScheduleDimensionTabsGeneratedCapability(TransformationCapability):
    """Build the IfcWorkSchedule dimension-tab model from Facade data.

    ``mapsToDimensionKind`` is semantic classification, not a request to
    render a standalone card. For IfcWorkSchedule, populated fields are
    grouped by their dimension kind and surfaced as tabs inside the single
    schedule card. Dimensions with no collected value are omitted.
    """

    METADATA = CapabilityMetadata(
        id=(
            "org.ontobdc.view.plugin.capability.transformation.target."
            "ifc_work_schedule_dimension_tabs_generated"
        ),
        version="1.0.0",
        name="IfcWorkSchedule Dimension Tabs Generated",
        description=(
            "Group populated IfcWorkSchedule Facade fields by semantic "
            "dimension and build the tab model for the single schedule card."
        ),
        author=["http://kb.elias.eng.br/nid/elias.ttl#Elias"],
        tags=["view", "page", "ifc-work-schedule", "dimension", "tab", "transformation"],
        supported_languages=["en", "pt-br"],
        log_message={
            "info": {
                "en": "The IfcWorkSchedule dimension tabs were assembled.",
            },
            "debug_entry": {
                "en": "Assembling populated IfcWorkSchedule dimensions as tabs.",
            },
        },
    )

    def label(self, lang: str = "en") -> str:
        return "IfcWorkSchedule Dimension Tabs Generated"

    def description(self, lang: str = "en") -> str:
        return self.METADATA.description

    def check(self, context: CliContextPort) -> bool:
        return isinstance(
            PageDataContextAdapter.payload(context).get("dimensions"), list
        )

    def execute(self, context: CliContextPort) -> Dict[str, Any]:
        payload = PageDataContextAdapter.payload(context)
        collected_fields = payload.get("fields")
        if not isinstance(collected_fields, dict):
            collected_fields = {}

        grouped: Dict[str, Dict[str, Any]] = {}
        sequence = 0

        for facade in payload.get("facades", []):
            fields = facade.get("fields", []) if isinstance(facade, dict) else []
            for field in sorted(
                (item for item in fields if isinstance(item, dict)),
                key=lambda item: item.get("field_order", 0),
            ):
                dimension_kind = str(field.get("dimension_kind") or "").strip()
                if not dimension_kind:
                    continue

                name = str(field.get("name") or "").strip()
                if not name or name not in collected_fields:
                    continue

                raw_value = collected_fields.get(name)
                if raw_value is None:
                    continue
                value = str(raw_value).strip()
                if not value:
                    continue

                tab = grouped.get(dimension_kind)
                if tab is None:
                    local_name = self._local_name(dimension_kind)
                    tab = {
                        "kind": local_name,
                        "label": self._humanize(local_name),
                        "fields": [],
                        "_sequence": sequence,
                    }
                    grouped[dimension_kind] = tab
                    sequence += 1

                tab["fields"].append(
                    {
                        "name": name,
                        "value": value,
                    }
                )

        dimensions: List[Dict[str, Any]] = []
        for tab in sorted(grouped.values(), key=lambda item: item["_sequence"]):
            dimensions.append(
                {
                    "kind": tab["kind"],
                    "label": tab["label"],
                    "fields": tab["fields"],
                }
            )

        payload["dimensions"] = dimensions
        return {"resulting_state": "__dimension_tabs_generated__"}

    def is_satisfied(self, context: CliContextPort) -> bool:
        return self.check(context)

    @staticmethod
    def _local_name(uri: str) -> str:
        value = str(uri or "").strip()
        if "#" in value:
            return value.rsplit("#", 1)[-1]
        trimmed = value.rstrip("/")
        if "/" in trimmed:
            return trimmed.rsplit("/", 1)[-1]
        if ":" in trimmed:
            return trimmed.rsplit(":", 1)[-1]
        return trimmed

    @staticmethod
    def _humanize(value: str) -> str:
        spaced = re.sub(r"(?<=[a-z0-9])(?=[A-Z])", " ", value)
        return spaced.replace("_", " ").replace("-", " ").strip()
