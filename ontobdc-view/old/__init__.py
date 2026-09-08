from .component.adapter.dock import (
    component_event_promoter_source as _component_event_promoter_source,
)
from .component.adapter.dock import (
    listener_runtime_source as _listener_runtime_source,
)
from .component.adapter.dock import (
    presentation_event_policy as _presentation_event_policy,
)
from .component.adapter.global_event import (
    global_event_iri_for_operation as _global_event_iri_for_operation,
)
from .component.adapter.global_event import (
    global_event_iris as _global_event_iris,
)
from .component.adapter.global_event import (
    global_event_operations as _global_event_operations,
)
from .component.adapter.global_event import (
    global_event_replay_source as _global_event_replay_source,
)
from .component.adapter.source import ComponentSourceAdapter
from .component.adapter.source import theme_catalog as _theme_catalog
from .page.adapter.asset import PageAssetAdapter
from .page.adapter.client_server_entity_view import ClientServerEntityViewRenderAdapter
from .page.adapter.entity_view import EntityViewRenderAdapter
from .page.adapter.gantt_script import GanttScriptAdapter
from .page.adapter.work_stream import WorkStreamScriptAdapter

__all__ = [
    "__version__",
    "component_source",
    "component_event_promoter_source",
    "listener_runtime_source",
    "presentation_event_policy",
    "global_event_replay_source",
    "global_event_iris",
    "global_event_iri_for_operation",
    "global_event_operations",
    "theme_catalog",
    "page_asset_root",
    "page_asset_path",
    "read_page_asset",
    "render_entity_view",
    "render_client_server_entity_view",
    "file_viewer_source",
    "work_stream_script_source",
    "gantt_script_source",
]

__version__ = "0.1.0"

_page_asset = PageAssetAdapter()

component_source = ComponentSourceAdapter().component_source
# The dDock. `component_event_promoter_source()` is the one Component ->
# Shared promotion path a page embeds; the other two are the pieces it is
# built from, exposed so a host can package them itself.
component_event_promoter_source = _component_event_promoter_source
listener_runtime_source = _listener_runtime_source
presentation_event_policy = _presentation_event_policy
# The Global Event replay runtime: applies a page's persisted journal to its
# JSON-LD snapshot before any Tile is upgraded. A generated page embeds it
# ahead of every component module. The other two expose what it was built
# from — the Global Event IRIs and the graph operation each one carries, both
# read from the ontology, so a host never has to restate them.
global_event_replay_source = _global_event_replay_source
global_event_iris = _global_event_iris
global_event_iri_for_operation = _global_event_iri_for_operation
global_event_operations = _global_event_operations
# The catalog `onto-theme-tile` is built with. Public so the generation
# pipeline can declare the same first-entry default in the page URL that
# the tile itself falls back to, instead of hardcoding a second copy.
theme_catalog = _theme_catalog
page_asset_root = _page_asset.page_asset_root
page_asset_path = _page_asset.page_asset_path
read_page_asset = _page_asset.read_page_asset
file_viewer_source = _page_asset.file_viewer_source
render_entity_view = EntityViewRenderAdapter().render_entity_view
render_client_server_entity_view = (
    ClientServerEntityViewRenderAdapter().render_entity_view
)
work_stream_script_source = WorkStreamScriptAdapter().script_source
gantt_script_source = GanttScriptAdapter().script_source
