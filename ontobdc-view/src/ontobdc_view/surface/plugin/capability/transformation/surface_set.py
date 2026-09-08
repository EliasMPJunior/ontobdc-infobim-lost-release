from typing import Any, Dict

from ontobdc.cli.domain.port.context import CliContextPort
from ontobdc.shared.adapter.capability import TransformationCapability
from ontobdc.shared.domain.model.capability import CapabilityMetadata
from ontobdc_view.surface.adapter.context import SurfaceContextAdapter
from ontobdc_view.surface.adapter.document import CONFIG_ID, SurfaceDocumentAdapter
from ontobdc_view.surface.adapter.transformation import SurfaceTransformationAdapter
from ontobdc_view.surface.domain.machine.standard_surface_html.state import SurfaceGenerationProcessState
from ontobdc_view.surface.plugin.check.is_surface_set.check import main as check_surface_set


class SurfaceSetCapability(TransformationCapability):
    METADATA = CapabilityMetadata(
        id="org.ontobdc.view.plugin.capability.transformation.target.surface_set",
        version="1.0.0",
        name="Surface Set",
        description="Declare Surface regions and runtime presentation rules without fixing viewport geometry.",
        author=["http://kb.elias.eng.br/nid/elias.ttl#Elias"],
        tags=["view", "surface", "configuration", "transformation"],
        supported_languages=["en", "pt-br"],
        log_message={
            "info": {
                "en": (
                    "Surface regions and runtime presentation rules were declared "
                    "without fixing viewport geometry."
                ),
            },
            "debug_entry": {
                "en": (
                    "Declaring Surface regions and runtime presentation rules "
                    "(no fixed viewport geometry)."
                ),
            },
        },
    )

    def __init__(self) -> None:
        self._surface = SurfaceTransformationAdapter()
        self._context_adapter = SurfaceContextAdapter()

    def label(self, lang: str = "en") -> str:
        return SurfaceGenerationProcessState.SURFACE_SET.label(lang)

    def description(self, lang: str = "en") -> str:
        return SurfaceGenerationProcessState.SURFACE_SET.description(lang)

    def check(self, context: CliContextPort) -> bool:
        return self._surface.check(context, check_surface_set)

    def execute(self, context: CliContextPort) -> Dict[str, Any]:
        config = SurfaceDocumentAdapter.normalize_surface_config(self._context_adapter.surface_config(context))
        document = SurfaceDocumentAdapter.upsert_json_script(self._surface.read(context), CONFIG_ID, config)
        document = SurfaceDocumentAdapter.set_state_marker(document, "surface_set")
        path = self._surface.write(context, document)
        self._surface.require_check(context, check_surface_set, "surface_set")
        return {
            "resulting_state": SurfaceGenerationProcessState.SURFACE_SET,
            "surface_path": str(path),
            "surface_config": config,
        }

    def is_satisfied(self, context: CliContextPort) -> bool:
        return self.check(context)
