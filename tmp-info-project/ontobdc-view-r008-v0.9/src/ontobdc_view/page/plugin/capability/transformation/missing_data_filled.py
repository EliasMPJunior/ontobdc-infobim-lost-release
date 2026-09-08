from typing import Any, Dict

from ontobdc.cli.domain.port.context import CliContextPort
from ontobdc.shared.adapter.capability import TransformationCapability
from ontobdc.shared.domain.model.capability import CapabilityMetadata
from ontobdc_view.page.adapter.context import PageDataContextAdapter


class MissingDataFilledCapability(TransformationCapability):
    """Stub -- fill Facade fields absent from DATA_GATHERED from another source."""

    METADATA = CapabilityMetadata(
        id="org.ontobdc.view.plugin.capability.transformation.target.missing_data_filled",
        version="1.0.0",
        name="Missing Data Filled",
        description=(
            "Fill the Facade fields absent from DATA_GATHERED from another "
            "source."
        ),
        author=["http://kb.elias.eng.br/nid/elias.ttl#Elias"],
        tags=["view", "page", "facade", "transformation"],
        supported_languages=["en", "pt-br"],
        log_message={
            "info": {
                "en": "Facade fields absent from DATA_GATHERED were filled.",
            },
            "debug_entry": {
                "en": "Filling the Facade fields absent from DATA_GATHERED.",
            },
        },
    )

    def label(self, lang: str = "en") -> str:
        return "Missing Data Filled"

    def description(self, lang: str = "en") -> str:
        return self.METADATA.description

    def check(self, context: CliContextPort) -> bool:
        return False

    def execute(self, context: CliContextPort) -> Dict[str, Any]:
        # No secondary data source has been defined yet. Keep the unresolved
        # fields explicit in the payload until one is available.
        PageDataContextAdapter.payload(context)
        return {"resulting_state": "__missing_data_filled__"}

    def is_satisfied(self, context: CliContextPort) -> bool:
        return self.check(context)
