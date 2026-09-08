from typing import Any, Dict, Optional

from ontobdc.cli.domain.port.context import CliContextPort
from ontobdc.shared.adapter.capability import TransformationCapability
from ontobdc.shared.domain.model.capability import CapabilityMetadata
from ontobdc_view.page.adapter.context import (
    PAGE_ENTITY_URI,
    PageDataContextAdapter,
)
from ontobdc_view.page.adapter.entity_page import EntityPageOntologyAdapter


class ToolbarConfigurationGatheredCapability(TransformationCapability):
    """Gather the toolbar declared for the active Entity Page."""

    METADATA = CapabilityMetadata(
        id=(
            "org.ontobdc.view.plugin.capability.transformation.target."
            "toolbar_configuration_gathered"
        ),
        version="1.0.0",
        name="Toolbar Configuration Gathered",
        description=(
            "Locate the toolbar belonging to the active Entity Page and "
            "write its ontology configuration into the Page-data JSON-LD."
        ),
        author=["http://kb.elias.eng.br/nid/elias.ttl#Elias"],
        tags=["view", "page", "toolbar", "json-ld", "transformation"],
        supported_languages=["en", "pt-br"],
        log_message={
            "info": {
                "en": "The Entity Page toolbar configuration was gathered.",
            },
            "debug_entry": {
                "en": "Gathering the Entity Page toolbar configuration.",
            },
        },
    )

    def __init__(
        self,
        ontology: Optional[EntityPageOntologyAdapter] = None,
    ) -> None:
        self._ontology = ontology or EntityPageOntologyAdapter()

    def label(self, lang: str = "en") -> str:
        return "Toolbar Configuration Gathered"

    def description(self, lang: str = "en") -> str:
        return self.METADATA.description

    def check(self, context: CliContextPort) -> bool:
        configuration = PageDataContextAdapter.payload(context).get(
            "toolbar_configuration"
        )
        return (
            isinstance(configuration, dict)
            and isinstance(configuration.get("@graph"), list)
            and bool(configuration["@graph"])
        )

    def execute(self, context: CliContextPort) -> Dict[str, Any]:
        entity_uri = PageDataContextAdapter.require_uri(
            context,
            PAGE_ENTITY_URI,
        )
        payload = PageDataContextAdapter.payload(context)
        payload["toolbar_configuration"] = (
            self._ontology.toolbar_configuration(entity_uri)
        )
        return {"resulting_state": "__toolbar_configuration_gathered__"}

    def is_satisfied(self, context: CliContextPort) -> bool:
        return self.check(context)
