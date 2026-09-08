from ontobdc.shared.adapter.config import UnsetProjectRootConfigDataAdapter
from ontobdc.shared.adapter.ontology import OntologyConfigAdapter
from ontobdc.shared.domain.model.component import ComponentMetadata
from ontobdc.shared.domain.port.component import ComponentPort

_VIEW = OntologyConfigAdapter(
    config_adapter=UnsetProjectRootConfigDataAdapter(),
).get_ontology_namespace_by_prefix("obdc_view")


class FileViewerTileComponent(ComponentPort):
    """The single Surface-wide file viewer Tile.

    Not entity-matched (`required_uris=[]`, like `FileSizeTileComponent`) —
    there is exactly one of these per Surface, always, regardless of how
    many files the container owns. It stays closed until the dDock promotes
    another component's `EntityPageOpenRequested` (e.g. a double-click in
    `onto-file-tree-tile`) into the `EntityPageRequested` Shared Event, at
    which point it reveals itself and points its `<iframe>` at the
    standalone `onto-file-viewer.html` page with that file's path passed by
    reference in the query string — the only place, and that Shared Event
    the only moment, any real container file is read. Closing it runs the
    reverse chain: `EntityPageCloseRequested` -> `EntityPageDismissRequested`.
    """

    METADATA = ComponentMetadata(
        id="org.ontobdc.view.plugin.component.file_viewer_tile",
        tag="onto-file-viewer-tile",
        tile_class=str(_VIEW.FileViewerTile),
        version="1.0.0",
        name="File Viewer Tile",
        description="Embeds the standalone file-viewer page for whichever file was last opened.",
        author=["http://kb.elias.eng.br/nid/elias.ttl#Elias"],
        tags=["view", "surface", "tile", "files"],
        supported_languages=["en", "pt-BR", "pt-PT", "es"],
        min_columns=6,
        max_columns=None,
        min_rows=5,
        max_rows=None,
        default_closed=True,
    )
