from typing import Any, Dict, List

from ontobdc_view.surface.adapter.rdf import SurfaceRdfParser
from ontobdc_view.surface.adapter.render import SurfaceResolutionService
from rdflib import Graph

from ontobdc.cli.domain.port.context import CliContextPort
from ontobdc.shared.domain.model.capability import CapabilityMetadata
from ontobdc_view.surface.adapter.document import MATCHES_ID, SurfaceDocumentAdapter
from ontobdc_view.surface.domain.machine.standard_surface_html.state import SurfaceGenerationProcessState
from ontobdc_view.surface.plugin.capability.transformation.surface_matched import SurfaceMatchedCapability
from ontobdc_view.surface.plugin.check.is_surface_operational_matched.check import (
    main as check_surface_operational_matched,
)

DEFAULT_LAYOUTS_SCRIPT_ID = "ontobdc-surface-default-layouts"
DEFAULT_LAYOUTS_BOOTSTRAP_ID = "ontobdc-surface-default-layouts-bootstrap"

# `whenDefined` makes this independent of where the script tag lands in the
# document relative to the `onto-presentation-surface` element's own
# defining module script — no insertion-order assumption is needed.
_BOOTSTRAP_JS = f"""\
customElements.whenDefined("onto-presentation-surface").then(() => {{
  const dataEl = document.getElementById("{DEFAULT_LAYOUTS_SCRIPT_ID}");
  const surfaceEl = document.querySelector("onto-presentation-surface");
  if (!dataEl || !surfaceEl) return;
  try {{
    surfaceEl.defaultSurfaceLayouts = JSON.parse(dataEl.textContent);
  }} catch (error) {{
    console.error("Failed to apply OntoBDC defaultSurfaceLayouts", error);
  }}
}});
"""


class SurfaceOperationalMatchedCapability(SurfaceMatchedCapability):
    """Resolve the OperationRegion of the shipped `ontobdc_view` DefaultSurfaceLayout.

    `SurfaceRdfParser.default_surface_layout()` ships one always-matching
    `view:DefaultSurfaceLayout` (Logo/Language/Theme in its OperationRegion)
    — used whenever the caller declared no explicit operation-region Tile of
    its own. Reuses `SurfaceMatchedCapability`'s `_with_resolved_tile` (the
    same Chrome-Tile `tileClass` resolution `SURFACE_MATCHED` already
    implements, in strict mode) to turn each placement into a resolved
    `surface_matches` entry, and additionally embeds the resolved
    `SurfaceDefinition` payload so the browser's own ontology-driven
    `defaultSurfaceLayouts` selection (`onto-presentation-surface.js`,
    `ontobdc-view` >= 0.3) picks it up instead of falling back to the legacy
    fixed topology.

    No fallback: a malformed shipped layout or a shipped placement with no
    registered matching Component raises rather than degrading to a partial
    or empty operation region. Logo/Language/Theme are packaged in this same
    distribution, so either failure is a real defect, never an expected
    runtime condition to tolerate.
    """

    METADATA = CapabilityMetadata(
        id="org.ontobdc.view.plugin.capability.transformation.target.surface_operational_matched",
        version="1.0.0",
        name="Surface Operational Matched",
        description=(
            "Resolve the OperationRegion of the shipped ontobdc_view DefaultSurfaceLayout "
            "(Logo/Language/Theme) when the caller declared no explicit operation-region "
            "Tile, and embed its SurfaceDefinition for client-side ontology-driven selection."
        ),
        author=["http://kb.elias.eng.br/nid/elias.ttl#Elias"],
        tags=["view", "surface", "tile", "operation", "default-layout", "transformation"],
        supported_languages=["en", "pt-br"],
        log_message={
            "info": {
                "en": (
                    "Operation-region defaults were resolved when no explicit tile "
                    "was declared, with Surface definitions embedded for client-side "
                    "selection."
                ),
            },
            "debug_entry": {
                "en": (
                    "Resolving operation-region defaults and embedding Surface "
                    "definitions for client-side selection."
                ),
            },
        },
    )

    def label(self, lang: str = "en") -> str:
        return SurfaceGenerationProcessState.SURFACE_OPERATIONAL_MATCHED.label(lang)

    def description(self, lang: str = "en") -> str:
        return SurfaceGenerationProcessState.SURFACE_OPERATIONAL_MATCHED.description(lang)

    def check(self, context: CliContextPort) -> bool:
        return self._surface.check(context, check_surface_operational_matched)

    def execute(self, context: CliContextPort) -> Dict[str, Any]:
        document = self._surface.read(context)
        matches = SurfaceDocumentAdapter.extract_json_script(document, MATCHES_ID)
        if not isinstance(matches, list):
            raise ValueError("Surface matches are missing or invalid")

        layouts = self._default_layouts()
        operation_already_declared = any(
            str(item.get("region", "")).strip().lower() == "operation" for item in matches
        )

        added: List[Dict[str, Any]] = []
        if layouts and not operation_already_declared:
            empty_graph = Graph()
            for request in self._operation_requests(layouts):
                resolved: Dict[str, Any] = self._with_resolved_tile(empty_graph, request)
                added.append(resolved)

        if added:
            matches = SurfaceDocumentAdapter.normalize_matches(list(matches) + added)
            document = SurfaceDocumentAdapter.upsert_json_script(document, MATCHES_ID, matches)

        if layouts:
            payload = [SurfaceResolutionService.to_render_payload(layout) for layout in layouts]
            document = SurfaceDocumentAdapter.upsert_json_script(document, DEFAULT_LAYOUTS_SCRIPT_ID, payload)
            document = SurfaceDocumentAdapter.upsert_raw_script(
                document, DEFAULT_LAYOUTS_BOOTSTRAP_ID, "module", _BOOTSTRAP_JS
            )

        document = SurfaceDocumentAdapter.set_state_marker(document, "surface_operational_matched")
        path = self._surface.write(context, document)
        self._surface.require_check(
            context, check_surface_operational_matched, "surface_operational_matched"
        )

        return {
            "resulting_state": SurfaceGenerationProcessState.SURFACE_OPERATIONAL_MATCHED,
            "surface_path": str(path),
            "operational_match_count": len(added),
            "default_layout_count": len(layouts),
        }

    @staticmethod
    def _default_layouts() -> List[Any]:
        return SurfaceRdfParser.default_surface_layout()

    @staticmethod
    def _operation_requests(layouts: List[Any]) -> List[Dict[str, Any]]:
        requests: List[Dict[str, Any]] = []
        for layout in layouts:
            for region in layout.regions:
                if region.role != "OperationRegion":
                    continue
                for placement in region.placements:
                    if not placement.component_type_iri:
                        raise ValueError(
                            f"{placement.iri} in the shipped default operation layout "
                            "has no rdf:type on its component -- the shipped ontology "
                            "is malformed."
                        )
                    requests.append(
                        {"tileClass": placement.component_type_iri, "region": "operation"}
                    )
        return requests
