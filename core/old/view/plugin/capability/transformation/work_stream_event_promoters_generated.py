from typing import Any, Dict, List

from ontobdc.cli.domain.port.context import CliContextPort
from ontobdc.shared.adapter.capability import TransformationCapability
from ontobdc.shared.domain.model.capability import CapabilityMetadata
from ontobdc.view.adapter.surface.transformation import SurfaceTransformationAdapter
from ontobdc.view.domain.machine.work_stream_script_state import (
    WorkStreamScriptGenerationProcessState,
)
from ontobdc.view.plugin.check.work_stream_script_common import (
    script_is_fresh,
    script_path,
)


# component_event_promoter.js carries the real Component -> Shared bridge
# (assembled by ontobdc_view, embedding the ontobdc_web_dock runtime and
# the presentation_event.ttl policy). shared_event_promoter.js stays an
# empty scaffold until the Shared -> Global policy is defined in the ABox.
_BRIDGE_SCRIPT = "component_event_promoter"
_SCAFFOLD_SCRIPTS = ("shared_event_promoter",)
_SCRIPT_NAMES = (_BRIDGE_SCRIPT, *_SCAFFOLD_SCRIPTS)


class WorkStreamEventPromotersGeneratedCapability(TransformationCapability):
    METADATA = CapabilityMetadata(
        id=(
            "org.ontobdc.view.plugin.capability.transformation.target."
            "work_stream_event_promoters_generated"
        ),
        version="1.0.0",
        name="WorkStream dDock Event Promoters Generated",
        description=(
            "Generates the dDock Component-to-Shared event promoter bridge "
            "(with the ontobdc_web_dock runtime and the presentation_event "
            "policy embedded) and the empty Shared-to-Global scaffold."
        ),
        author=["http://kb.elias.eng.br/nid/elias.ttl#Elias"],
        tags=["view", "workstream", "script", "event", "transformation"],
        supported_languages=["en", "pt-br"],
        log_message={
            "info": {
                "en": (
                    "dDock event promoter JavaScript scaffolds were generated "
                    "under .__ontobdc__/asset/work_stream_view/."
                ),
            },
            "debug_entry": {
                "en": (
                    "Generating dDock event promoter JavaScript scaffolds under "
                    ".__ontobdc__/asset/work_stream_view/."
                ),
            },
        },
    )

    def __init__(self) -> None:
        self._surface = SurfaceTransformationAdapter()

    def label(self, lang: str = "en") -> str:
        return WorkStreamScriptGenerationProcessState.EVENT_PROMOTERS_GENERATED.label(lang)

    def description(self, lang: str = "en") -> str:
        return WorkStreamScriptGenerationProcessState.EVENT_PROMOTERS_GENERATED.description(lang)

    def check(self, context: CliContextPort) -> bool:
        surface_path = str(self._surface.path(context))
        return all(script_is_fresh(surface_path, name) for name in _SCRIPT_NAMES)

    def execute(self, context: CliContextPort) -> Dict[str, Any]:
        import ontobdc_view

        container_path = self._surface.path(context).parent
        contents: Dict[str, str] = {
            _BRIDGE_SCRIPT: ontobdc_view.component_event_promoter_source(),
        }
        for name in _SCAFFOLD_SCRIPTS:
            contents[name] = "\n"

        generated_paths: List[str] = []
        for name in _SCRIPT_NAMES:
            target_path = script_path(container_path, name)
            target_path.parent.mkdir(parents=True, exist_ok=True)
            if target_path.exists():
                target_path.unlink()
            target_path.write_text(contents[name], encoding="utf-8")
            generated_paths.append(str(target_path))

        return {
            "resulting_state": WorkStreamScriptGenerationProcessState.EVENT_PROMOTERS_GENERATED,
            "script_paths": generated_paths,
        }

    def is_satisfied(self, context: CliContextPort) -> bool:
        return self.check(context)
