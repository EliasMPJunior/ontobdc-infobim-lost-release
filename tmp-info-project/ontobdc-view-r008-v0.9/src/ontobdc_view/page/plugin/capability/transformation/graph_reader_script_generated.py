from typing import Any, Dict

from ontobdc.cli.domain.port.context import CliContextPort
from ontobdc.shared.adapter.capability import TransformationCapability
from ontobdc.shared.domain.model.capability import CapabilityMetadata


class GraphReaderScriptGeneratedCapability(TransformationCapability):
    """Stub for generating the active Page builder's graph reader script."""

    METADATA = CapabilityMetadata(
        id=(
            "org.ontobdc.view.plugin.capability.transformation.target."
            "graph_reader_script_generated"
        ),
        version="1.0.0",
        name="Graph Reader Script Generated",
        description=(
            "Generate the Page script that reads its embedded JSON-LD graph."
        ),
        author=["http://kb.elias.eng.br/nid/elias.ttl#Elias"],
        tags=["view", "page", "json-ld", "transformation"],
        supported_languages=["en", "pt-br"],
        log_message={
            "info": {"en": "The Page graph reader script was generated."},
            "debug_entry": {
                "en": "Generating the Page graph reader script."
            },
        },
    )

    def label(self, lang: str = "en") -> str:
        return "Graph Reader Script Generated"

    def description(self, lang: str = "en") -> str:
        return self.METADATA.description

    def check(self, context: CliContextPort) -> bool:
        return False

    def execute(self, context: CliContextPort) -> Dict[str, Any]:
        return {"resulting_state": "__graph_reader_script_generated__"}

    def is_satisfied(self, context: CliContextPort) -> bool:
        return self.check(context)
