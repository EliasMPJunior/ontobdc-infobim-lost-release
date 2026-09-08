
from typing import Any, Dict
from ontobdc.cli.domain.port.context import CliContextPort
from ontobdc.shared.adapter.capability import TransformationCapability
from ontobdc.shared.domain.model.capability import CapabilityMetadata
from ontobdc_view.surface.adapter.document import SurfaceDocumentAdapter
from ontobdc_view.surface.adapter.transformation import SurfaceTransformationAdapter
from ontobdc_view.surface.domain.machine.standard_surface_html.state import SurfaceGenerationProcessState
from ontobdc_view.surface.plugin.check.is_surface_initialized.check import main as check_surface_initialized


class SurfaceInitializedCapability(TransformationCapability):
    METADATA = CapabilityMetadata(
        id="org.ontobdc.view.plugin.capability.transformation.target.surface_initialized",
        version="1.0.0",
        name="Surface Initialized",
        description="Create the minimal offline HTML Presentation Surface document.",
        author=["http://kb.elias.eng.br/nid/elias.ttl#Elias"],
        tags=["view", "surface", "html", "transformation"],
        supported_languages=["en", "pt-br"],
        log_message={
            "info": {
                "en": (
                    "Minimal offline HTML Presentation Surface document was created."
                ),
            },
            "debug_entry": {
                "en": (
                    "Creating the minimal offline HTML Presentation Surface document."
                ),
            },
        },
    )

    def __init__(self) -> None:
        self._surface = SurfaceTransformationAdapter()

    def label(self, lang: str = "en") -> str:
        return SurfaceGenerationProcessState.SURFACE_INITIALIZED.label(lang)

    def description(self, lang: str = "en") -> str:
        return SurfaceGenerationProcessState.SURFACE_INITIALIZED.description(lang)

    def check(self, context: CliContextPort) -> bool:
        return self._surface.check(context, check_surface_initialized)

    def execute(self, context: CliContextPort) -> Dict[str, Any]:
        path = self._surface.path(context)
        lang = str(context.get_parameter_value("language") or "en")
        document = SurfaceDocumentAdapter.set_state_marker(SurfaceDocumentAdapter.make_initial_html(lang), "surface_initialized")
        self._surface.write(context, document)
        self._surface.require_check(context, check_surface_initialized, "surface_initialized")
        return {
            "resulting_state": SurfaceGenerationProcessState.SURFACE_INITIALIZED,
            "surface_path": str(path),
        }

    def is_satisfied(self, context: CliContextPort) -> bool:
        return self.check(context)
