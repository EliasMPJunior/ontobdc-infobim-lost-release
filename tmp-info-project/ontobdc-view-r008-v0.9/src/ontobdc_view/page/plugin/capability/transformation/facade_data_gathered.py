from typing import Any, Dict, Optional

from ontobdc.cli.domain.port.context import CliContextPort
from ontobdc.shared.adapter.capability import TransformationCapability
from ontobdc.shared.domain.model.capability import CapabilityMetadata
from ontobdc_view.page.adapter.context import PageDataContextAdapter


class FacadeDataGatheredCapability(TransformationCapability):
    """Collect Facade field values present on the DATA_GATHERED node."""

    METADATA = CapabilityMetadata(
        id="org.ontobdc.view.plugin.capability.transformation.target.facade_data_gathered",
        version="1.0.0",
        name="Facade Data Gathered",
        description=(
            "Collect the Facade field values already present on the "
            "DATA_GATHERED element node."
        ),
        author=["http://kb.elias.eng.br/nid/elias.ttl#Elias"],
        tags=["view", "page", "facade", "transformation"],
        supported_languages=["en", "pt-br"],
        log_message={
            "info": {
                "en": "Facade field values present on the element node were collected.",
            },
            "debug_entry": {
                "en": "Collecting Facade field values from the DATA_GATHERED element node.",
            },
        },
    )

    def label(self, lang: str = "en") -> str:
        return "Facade Data Gathered"

    def description(self, lang: str = "en") -> str:
        return self.METADATA.description

    def check(self, context: CliContextPort) -> bool:
        payload = PageDataContextAdapter.payload(context)
        return isinstance(payload.get("fields"), dict) and isinstance(
            payload.get("missing_fields"), list
        )

    def execute(self, context: CliContextPort) -> Dict[str, Any]:
        payload = PageDataContextAdapter.payload(context)
        source_node = PageDataContextAdapter.source_node(context)
        fields: Dict[str, str] = {}
        missing_fields = []

        for facade in payload.get("facades", []):
            for field in facade.get("fields", []):
                if "mapped_property" not in field:
                    continue
                name = str(field["name"])
                value = self._literal(
                    source_node,
                    str(field["mapped_property"]),
                )
                if value is None:
                    missing_fields.append(name)
                else:
                    fields[name] = value

        payload["fields"] = fields
        payload["missing_fields"] = missing_fields
        return {"resulting_state": "__facade_data_gathered__"}

    def is_satisfied(self, context: CliContextPort) -> bool:
        return self.check(context)

    @staticmethod
    def _literal(
        source_node: Dict[str, Any],
        property_uri: str,
    ) -> Optional[str]:
        values = source_node.get(property_uri)
        if not isinstance(values, list) or not values:
            return None
        picked = values[0]
        if isinstance(picked, dict):
            value = picked.get("@value")
            if value is None:
                value = picked.get("@id")
            return str(value).strip() if value is not None else None
        return str(picked).strip()
