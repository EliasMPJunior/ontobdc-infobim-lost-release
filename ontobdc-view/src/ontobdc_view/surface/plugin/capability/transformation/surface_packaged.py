import re
import time
from pathlib import Path
from typing import Any, Dict, List

from ontobdc.cli.domain.port.context import CliContextPort
from ontobdc.shared.adapter.capability import TransformationCapability
from ontobdc.shared.domain.model.capability import CapabilityMetadata
from ontobdc_view.component.adapter.dock import component_event_promoter_source
from ontobdc_view.component.adapter.source import ComponentSourceAdapter
from ontobdc_view.page.plugin.asset import file_viewer_source
from ontobdc_view.surface.adapter.context import SurfaceContextAdapter
from ontobdc_view.surface.adapter.document import JSONLD_ID, MATCHES_ID, SURFACE_TAG, SurfaceDocumentAdapter
from ontobdc_view.surface.adapter.transformation import SurfaceTransformationAdapter
from ontobdc_view.surface.domain.machine.standard_surface_html.state import SurfaceGenerationProcessState
from ontobdc_view.surface.plugin.check.is_surface_packaged.check import main as check_surface_packaged

#region debug-point (infobim-view-slow-crash): H2 instrumentation metrics import
from ontobdc_view.surface.adapter.assembly import SurfaceAssemblyAdapter as _dbg_sc
#endregion

# Journal preparation, copied from the not-yet-migrated
# `ontobdc.view.adapter.surface.global_event` -- only the read/prepare side
# this capability needs (marking where the embedded snapshot's sequence
# cursor is, and leaving the document appendable). The write side
# (`GlobalEventJournalWriter`, `append_event`, compaction) belongs to
# whatever replaces `global_event_listener.py` and is not this capability's
# concern.
_JOURNAL_MARKER = "<!-- ontobdc:global-event-journal -->"
_SNAPSHOT_THROUGH_ATTR = "data-snapshot-through"
_SCRIPT_RE = re.compile(r"<script\b([^>]*)>(.*?)</script>", re.IGNORECASE | re.DOTALL)


class _GlobalEventError(Exception):
    """A Global Event journal document could not be prepared or marked."""


class SurfacePackagedCapability(TransformationCapability):
    METADATA = CapabilityMetadata(
        id="org.ontobdc.view.plugin.capability.transformation.target.surface_packaged",
        version="1.0.0",
        name="Surface Packaged",
        description=(
            "Embed every browser component implementation required by the "
            "Surface for offline execution."
        ),
        author=["http://kb.elias.eng.br/nid/elias.ttl#Elias"],
        tags=[
            "view",
            "surface",
            "html",
            "offline",
            "packaging",
            "transformation",
        ],
        supported_languages=["en", "pt-br"],
        log_message={
            "info": {
                "en": (
                    "Browser component implementations required by the Surface were "
                    "embedded for offline execution."
                ),
            },
            "debug_entry": {
                "en": (
                    "Embedding required Surface Browser component implementations "
                    "for offline execution."
                ),
            },
        },
    )

    def __init__(self) -> None:
        self._surface = SurfaceTransformationAdapter()
        self._context_adapter = SurfaceContextAdapter()

    def label(self, lang: str = "en") -> str:
        return SurfaceGenerationProcessState.SURFACE_PACKAGED.label(lang)

    def description(self, lang: str = "en") -> str:
        return SurfaceGenerationProcessState.SURFACE_PACKAGED.description(lang)

    def check(self, context: CliContextPort) -> bool:
        return self._surface.check(context, check_surface_packaged)

    def execute(self, context: CliContextPort) -> Dict[str, Any]:
        #region debug-point (infobim-view-slow-crash): H2 instrumentation (131s step)
        _dbg_t0: float = time.perf_counter()
        #endregion
        document = self._surface.read(context)
        #region debug-point (infobim-view-slow-crash): read timer
        _dbg_t_read: float = time.perf_counter()
        _dbg_ctx_t0: float = time.perf_counter()
        #endregion
        scripts = self._context_adapter.component_scripts(context)
        #region debug-point (infobim-view-slow-crash): context adapter timer
        _dbg_t_ctx: float = time.perf_counter()
        _dbg_src_t0: float = time.perf_counter()
        #endregion
        if not scripts:
            scripts = self._read_component_sources(document, context)
        #region debug-point (infobim-view-slow-crash): read sources timer
        _dbg_t_src: float = time.perf_counter()
        #endregion
        if not scripts:
            raise ValueError(
                "No complete build-ready Surface component set was available. "
                "Install ontobdc-view with build-ready components or provide "
                "surface_component_scripts."
            )

        #region debug-point (infobim-view-slow-crash): embed timer
        _dbg_emb_t0: float = time.perf_counter()
        #endregion
        promoter_source = self._read_component_event_promoter_source()
        document = SurfaceDocumentAdapter.embed_component_scripts(document, [promoter_source, *scripts])
        #region debug-point (infobim-view-slow-crash): embed done, state marker
        _dbg_t_embed: float = time.perf_counter()
        _dbg_state_t0: float = time.perf_counter()
        #endregion
        document = SurfaceDocumentAdapter.set_state_marker(document, "surface_packaged")
        # Leave the document able to receive Global Events. `</body>` and
        # `</html>` are optional in the HTML syntax, and dropping them is what
        # lets the worker append a block at the end of the file that still
        # parses as a child of `<body>` — rather than relying on a browser's
        # error recovery for content that follows `</html>`. The marker after
        # them delimits the journal, so reading it never has to reason about
        # the component scripts embedded above.
        document = self._set_snapshot_through(document, self._snapshot_through(document))
        document = self._prepare_document_for_journal(document)
        #region debug-point (infobim-view-slow-crash): state done, write
        _dbg_t_state: float = time.perf_counter()
        _dbg_write_t0: float = time.perf_counter()
        #endregion
        path = self._surface.write(context, document)
        self._write_file_viewer(path.parent)
        #region debug-point (infobim-view-slow-crash): write done, check
        _dbg_t_write: float = time.perf_counter()
        _dbg_check_t0: float = time.perf_counter()
        #endregion
        self._surface.require_check(context, check_surface_packaged, "surface_packaged")
        #region debug-point (infobim-view-slow-crash): check done, snapshot metrics
        _dbg_t_check: float = time.perf_counter()
        _dbg_common = dict(getattr(_dbg_sc, "_DBG_METRICS", {}) or {})
        #endregion
        return {
            "resulting_state": SurfaceGenerationProcessState.SURFACE_PACKAGED,
            "surface_path": str(path),
            "component_script_count": len(scripts),
            #region debug-point (infobim-view-slow-crash): inject H2 evidence
            "_dbg_seconds_total": round(_dbg_t_check - _dbg_t0, 4),
            "_dbg_document_chars": len(document),
            "_dbg_seconds_read": round(_dbg_t_read - _dbg_t0, 4),
            "_dbg_seconds_context_scripts": round(_dbg_t_ctx - _dbg_ctx_t0, 4),
            "_dbg_seconds_read_component_sources": round(_dbg_t_src - _dbg_src_t0, 4),
            "_dbg_seconds_embed_scripts": round(_dbg_t_embed - _dbg_emb_t0, 4),
            "_dbg_seconds_set_state": round(_dbg_t_state - _dbg_state_t0, 4),
            "_dbg_seconds_write": round(_dbg_t_write - _dbg_write_t0, 4),
            "_dbg_seconds_require_check": round(_dbg_t_check - _dbg_check_t0, 4),
            "_dbg_check_common_metrics": _dbg_common,
            #endregion
        }

    def is_satisfied(self, context: CliContextPort) -> bool:
        return self.check(context)

    def _read_component_event_promoter_source(self) -> str:
        try:
            source = component_event_promoter_source()
        except Exception as error:
            raise ValueError(
                "The Component Event promoter could not be built for the Surface."
            ) from error
        if not isinstance(source, str) or not source.strip():
            raise ValueError(
                "The Component Event promoter built for the Surface was empty."
            )
        return source

    def _required_component_tags(self, document: str) -> List[str]:
        tags = [SURFACE_TAG]
        matches = SurfaceDocumentAdapter.extract_json_script(document, MATCHES_ID)
        if isinstance(matches, list):
            for item in matches:
                if not isinstance(item, dict):
                    continue
                tile = str(item.get("tile", "")).strip()
                if tile and tile not in tags:
                    tags.append(tile)
        return tags

    @staticmethod
    def _snapshot_through(document: str) -> int:
        """The highest Global Event sequence the embedded snapshot already
        incorporates, or -1.

        Copied from the not-yet-migrated `global_event.py` (read-only slice
        this capability needs -- see the module-level note above).
        """
        for script in _SCRIPT_RE.finditer(document):
            attributes = script.group(1)
            if f'id="{JSONLD_ID}"' not in attributes:
                continue
            found = re.search(
                rf'\b{re.escape(_SNAPSHOT_THROUGH_ATTR)}\s*=\s*"(-?\d+)"', attributes
            )
            return int(found.group(1)) if found else -1
        return -1

    @staticmethod
    def _set_snapshot_through(document: str, sequence: int) -> str:
        """Record on the snapshot block which sequences it already contains."""
        pattern = re.compile(
            rf'(<script\b[^>]*\bid="{re.escape(JSONLD_ID)}")([^>]*)>'
        )
        match = pattern.search(document)
        if not match:
            raise _GlobalEventError(
                f"the document has no <script id=\"{JSONLD_ID}\"> to mark"
            )
        attributes = re.sub(
            rf'\s*{re.escape(_SNAPSHOT_THROUGH_ATTR)}\s*=\s*"[^"]*"', "", match.group(2)
        )
        return (
            document[: match.start()]
            + f'{match.group(1)}{attributes} {_SNAPSHOT_THROUGH_ATTR}="{sequence}">'
            + document[match.end() :]
        )

    @staticmethod
    def _prepare_document_for_journal(document: str) -> str:
        """Drop the optional `</body>`/`</html>` end tags from a generated
        document so events can be appended to the end of the file.

        Both tags are optional in the HTML syntax; a parser closes the
        elements at end of file. Anything appended after this point is
        therefore parsed as ordinary trailing content of `<body>` -- which is
        what the replay runtime walks -- instead of relying on a browser's
        tolerance for content that follows `</html>`.
        """
        trimmed = document.rstrip()
        if trimmed.endswith(_JOURNAL_MARKER):
            return trimmed + "\n"
        for closing in ("</html>", "</body>"):
            while trimmed.lower().endswith(closing):
                trimmed = trimmed[: -len(closing)].rstrip()
        return f"{trimmed}\n{_JOURNAL_MARKER}\n"

    def _write_file_viewer(self, container_path: Path) -> None:
        """Write the standalone file-viewer page beside the published views.

        `onto-file-tree-tile` opens this page
        (`.__ontobdc__/view/onto-file-viewer.html`, relative to the
        container root) with the clicked file's path passed by reference in
        the query string — the only place, and only moment, a real
        container file is ever read. It lives under the already-ignored
        `.__ontobdc__/view` directory, alongside every other generated
        view, so it never appears as an ordinary user-visible container
        file in the RO-Crate inventory or the file tree tile. The asset's
        own `<base href="../../">` resolves both the requested file path
        and `ro-crate-metadata.json` against the container root from there.
        """
        source = file_viewer_source()

        view_dir: Path = container_path / ".__ontobdc__" / "view"
        view_dir.mkdir(parents=True, exist_ok=True)
        (view_dir / "onto-file-viewer.html").write_text(
            source, encoding="utf-8"
        )

    def _read_component_sources(self, document: str, context: CliContextPort) -> List[str]:
        try:
            root_path = context.root_path
        except Exception:
            root_path = None

        component_source = ComponentSourceAdapter()
        scripts: List[str] = []
        for tag in self._required_component_tags(document):
            try:
                source = component_source.component_source(tag, root_path=root_path)
            except Exception:
                return []
            if not isinstance(source, str) or not source.strip():
                return []
            scripts.append(source)
        return scripts
