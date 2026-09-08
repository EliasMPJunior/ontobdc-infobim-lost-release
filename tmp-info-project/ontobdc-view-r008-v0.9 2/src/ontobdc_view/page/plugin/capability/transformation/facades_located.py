from typing import Any, Dict

from ontobdc.cli.domain.port.context import CliContextPort
from ontobdc.shared.adapter.capability import TransformationCapability
from ontobdc.shared.domain.model.capability import CapabilityMetadata
from ontobdc_view.page.adapter.context import (
    PAGE_ELEMENT_URI,
    PAGE_ENTITY_URI,
    PageDataContextAdapter,
)
from ontobdc_view.page.adapter.facade import FacadeLookupAdapter


class FacadesLocatedCapability(TransformationCapability):
    """Locate every Facade declared for the element's entity type."""

    METADATA = CapabilityMetadata(
        id="org.ontobdc.view.plugin.capability.transformation.target.facades_located",
        version="1.0.0",
        name="Facades Located",
        description=(
            "Locate every Facade the dataset declares for the element's entity "
            "type."
        ),
        author=["http://kb.elias.eng.br/nid/elias.ttl#Elias"],
        tags=["view", "page", "facade", "transformation"],
        supported_languages=["en", "pt-br"],
        log_message={
            "info": {
                "en": "Facades declared for the entity type were located.",
            },
            "debug_entry": {
                "en": "Locating the Facades declared for the entity type.",
            },
        },
    )

    def label(self, lang: str = "en") -> str:
        return "Facades Located"

    def description(self, lang: str = "en") -> str:
        return self.METADATA.description

    def check(self, context: CliContextPort) -> bool:
        return isinstance(PageDataContextAdapter.payload(context).get("facades"), list)

    def execute(self, context: CliContextPort) -> Dict[str, Any]:
        element_uri = PageDataContextAdapter.require_uri(context, PAGE_ELEMENT_URI)
        entity_uri = PageDataContextAdapter.require_uri(context, PAGE_ENTITY_URI)
        payload = PageDataContextAdapter.payload(context)
        payload["facades"] = FacadeLookupAdapter.locate_facades_for_element(
            context,
            element_uri,
            entity_uri,
        )
        return {"resulting_state": "__facades_located__"}

    def is_satisfied(self, context: CliContextPort) -> bool:
        return self.check(context)
