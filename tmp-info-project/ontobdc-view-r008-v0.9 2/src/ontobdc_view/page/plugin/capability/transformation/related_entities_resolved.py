from typing import Any, Dict

from ontobdc.cli.domain.port.context import CliContextPort
from ontobdc.shared.adapter.capability import TransformationCapability
from ontobdc.shared.domain.model.capability import CapabilityMetadata
from ontobdc_view.page.adapter.context import PageDataContextAdapter


class RelatedEntitiesResolvedCapability(TransformationCapability):
    """Stub -- resolve the entities related to this element."""

    METADATA = CapabilityMetadata(
        id="org.ontobdc.view.plugin.capability.transformation.target.related_entities_resolved",
        version="1.0.0",
        name="Related Entities Resolved",
        description="Resolve the entities related to this element.",
        author=["http://kb.elias.eng.br/nid/elias.ttl#Elias"],
        tags=["view", "page", "entity", "transformation"],
        supported_languages=["en", "pt-br"],
        log_message={
            "info": {
                "en": "Entities related to the element were resolved.",
            },
            "debug_entry": {
                "en": "Resolving the entities related to the element.",
            },
        },
    )

    def label(self, lang: str = "en") -> str:
        return "Related Entities Resolved"

    def description(self, lang: str = "en") -> str:
        return self.METADATA.description

    def check(self, context: CliContextPort) -> bool:
        return isinstance(
            PageDataContextAdapter.payload(context).get("related_entities"),
            list,
        )

    def execute(self, context: CliContextPort) -> Dict[str, Any]:
        PageDataContextAdapter.payload(context).setdefault("related_entities", [])
        return {"resulting_state": "__related_entities_resolved__"}

    def is_satisfied(self, context: CliContextPort) -> bool:
        return self.check(context)
