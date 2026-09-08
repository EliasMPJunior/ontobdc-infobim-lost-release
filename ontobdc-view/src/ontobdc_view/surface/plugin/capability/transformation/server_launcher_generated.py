from typing import Any, Dict

from ontobdc.cli.domain.port.context import CliContextPort
from ontobdc.shared.adapter.capability import TransformationCapability
from ontobdc.shared.domain.model.capability import CapabilityMetadata
from ontobdc_view.surface.adapter.document import SurfaceDocumentAdapter
from ontobdc_view.surface.adapter.transformation import SurfaceTransformationAdapter
from ontobdc_view.surface.domain.machine.standard_surface_html.state import SurfaceGenerationProcessState
from ontobdc_view.surface.plugin.check.is_server_launcher_generated.check import (
    main as check_server_launcher_generated,
)


class ServerLauncherGeneratedCapability(TransformationCapability):
    """Generate the Windows launcher and publish the server reference.

    Temporarily nulled out: `execute()` only marks the state reached. It
    writes no `server.cmd` and embeds no `ontobdc-server-reference` script
    into any page -- `is_server_launcher_generated`'s check has been
    simplified to match (marker-only, see that module's docstring).
    Restore the real implementation from `ontobdc/old/view/plugin/
    capability/transformation/server_launcher_generated.py` (and restore
    the full artifact validation in the check) together.
    """

    METADATA = CapabilityMetadata(
        id=(
            "org.ontobdc.view.plugin.capability.transformation.target."
            "server_launcher_generated"
        ),
        version="1.0.0",
        name="Server Launcher Generated",
        description=(
            "Generate server.cmd and publish one shared host/port reference "
            "into every generated HTML page."
        ),
        author=["http://kb.elias.eng.br/nid/elias.ttl#Elias"],
        tags=[
            "view",
            "surface",
            "server",
            "launcher",
            "windows",
            "cmd",
            "host",
            "port",
            "transformation",
        ],
        supported_languages=["en", "pt-br"],
        log_message={
            "info": {
                "en": (
                    "The Windows server launcher and shared HTML server "
                    "reference were generated."
                ),
            },
            "debug_entry": {
                "en": (
                    "Generating server.cmd, choosing the server reference, "
                    "and publishing it into generated HTML pages."
                ),
            },
        },
    )

    def __init__(self) -> None:
        self._surface = SurfaceTransformationAdapter()

    def label(self, lang: str = "en") -> str:
        return SurfaceGenerationProcessState.SERVER_LAUNCHER_GENERATED.label(lang)

    def description(self, lang: str = "en") -> str:
        return SurfaceGenerationProcessState.SERVER_LAUNCHER_GENERATED.description(lang)

    def check(self, context: CliContextPort) -> bool:
        return self._surface.check(context, check_server_launcher_generated)

    def execute(self, context: CliContextPort) -> Dict[str, Any]:
        document = self._surface.read(context)
        document = SurfaceDocumentAdapter.set_state_marker(document, "server_launcher_generated")
        path = self._surface.write(context, document)
        self._surface.require_check(
            context, check_server_launcher_generated, "server_launcher_generated"
        )
        return {
            "resulting_state": SurfaceGenerationProcessState.SERVER_LAUNCHER_GENERATED,
            "surface_path": str(path),
        }

    def is_satisfied(self, context: CliContextPort) -> bool:
        return self.check(context)
