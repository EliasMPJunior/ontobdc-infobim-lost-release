"""Top-level convenience API for the Surface generation pipeline.

`ontobdc.view` capabilities (`SurfacePackagedCapability`, ...) treat
`ontobdc_view` as an optional runtime dependency -- every call site wraps
these in `try/except ImportError` -- so the functions exposed here are the
one place that contract is fulfilled. Each one delegates to the adapter
that actually implements it; this module does no work of its own.
"""

from typing import Dict, List, Optional

from ontobdc_view.component.adapter.dock import component_event_promoter_source
from ontobdc_view.component.adapter.source import ComponentSourceAdapter, theme_catalog
from ontobdc_view.page.adapter.asset import PageAssetAdapter
from ontobdc_view.page.adapter.entity_view import EntityViewRenderAdapter

_COMPONENT_SOURCE = ComponentSourceAdapter()
_PAGE_ASSET = PageAssetAdapter()
_ENTITY_VIEW_RENDER = EntityViewRenderAdapter()


def component_source(tag: str, root_path: Optional[str] = None) -> Optional[str]:
    return _COMPONENT_SOURCE.component_source(tag, root_path=root_path)


def file_viewer_source() -> str:
    return _PAGE_ASSET.file_viewer_source()


def render_entity_view(
    entity_type_uris: List[str],
    entity_data: dict,
    *,
    graph_nodes: Optional[List[dict]] = None,
    language: str = "en",
) -> Optional[Dict[str, str]]:
    """Render a standalone detail Page for one entity.

    Returns `None` if no Page descriptor's `required_uris` matches any of
    `entity_type_uris` -- the caller (e.g. `EntityViewsPublishedCapability`)
    should skip that entity in that case. Otherwise returns
    `{"html", "path_segment", "identifier"}`; the caller writes `html` to
    `.__ontobdc__/view/<path_segment>/<identifier>.html`.
    """
    return _ENTITY_VIEW_RENDER.render_entity_view(
        entity_type_uris, entity_data, graph_nodes=graph_nodes, language=language
    )


__all__ = [
    "component_event_promoter_source",
    "component_source",
    "file_viewer_source",
    "render_entity_view",
    "theme_catalog",
]
