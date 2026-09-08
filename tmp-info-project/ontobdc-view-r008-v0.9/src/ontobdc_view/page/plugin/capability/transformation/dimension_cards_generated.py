from typing import Any, Dict, List, Optional

from ontobdc.cli.domain.port.context import CliContextPort
from ontobdc.shared.adapter.capability import TransformationCapability
from ontobdc.shared.domain.model.capability import CapabilityMetadata
from ontobdc_view.page.adapter.context import PageDataContextAdapter


class DimensionCardsGeneratedCapability(TransformationCapability):
    """Assemble the entity's dimension cards from the Facade dimension fields.

    Every Facade field that maps to a dimension kind
    (``:mapsToDimensionKind``, surfaced by ``FacadeLookupAdapter`` as the
    field's ``dimension_kind`` URI) becomes one ordered card. The value is
    read from the element node using the property that shares the kind's
    namespace with a lower-cased first character (``…#What`` -> ``…#what``).
    The entity-specific Jinja template renders ``payload["dimensions"]`` --
    no runtime script.
    """

    METADATA = CapabilityMetadata(
        id=(
            "org.ontobdc.view.plugin.capability.transformation.target."
            "dimension_cards_generated"
        ),
        version="1.0.0",
        name="Dimension Cards Generated",
        description=(
            "Build the ordered dimension-card model (kind, label, value) from "
            "the Facade fields that map to a dimension kind."
        ),
        author=["http://kb.elias.eng.br/nid/elias.ttl#Elias"],
        tags=["view", "page", "dimension", "transformation"],
        supported_languages=["en", "pt-br"],
        log_message={
            "info": {"en": "The Entity Page dimension cards were assembled."},
            "debug_entry": {"en": "Assembling the Entity Page dimension cards."},
        },
    )

    def label(self, lang: str = "en") -> str:
        return "Dimension Cards Generated"

    def description(self, lang: str = "en") -> str:
        return self.METADATA.description

    def check(self, context: CliContextPort) -> bool:
        return isinstance(
            PageDataContextAdapter.payload(context).get("dimensions"), list
        )

    def execute(self, context: CliContextPort) -> Dict[str, Any]:
        payload = PageDataContextAdapter.payload(context)
        source_node = PageDataContextAdapter.source_node(context)

        dimension_fields = [
            field
            for facade in payload.get("facades", [])
            for field in facade.get("fields", [])
            if field.get("dimension_kind")
        ]
        dimension_fields.sort(key=lambda field: field.get("field_order", 0))

        payload["dimensions"] = [
            {
                "kind": self._local_name(str(field["dimension_kind"])),
                "label": str(field["name"]),
                "value": self._literal(
                    source_node, self._value_property(str(field["dimension_kind"]))
                )
                or "",
            }
            for field in dimension_fields
        ]
        return {"resulting_state": "__dimension_cards_generated__"}

    def is_satisfied(self, context: CliContextPort) -> bool:
        return self.check(context)

    @staticmethod
    def _local_name(uri: str) -> str:
        if "#" in uri:
            return uri.rsplit("#", 1)[-1]
        return uri.rstrip("/").rsplit("/", 1)[-1]

    @staticmethod
    def _value_property(dimension_kind_uri: str) -> str:
        base, sep, fragment = dimension_kind_uri.rpartition("#")
        if not sep or not fragment:
            return dimension_kind_uri
        return f"{base}#{fragment[:1].lower()}{fragment[1:]}"

    @staticmethod
    def _literal(source_node: Dict[str, Any], property_uri: str) -> Optional[str]:
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
