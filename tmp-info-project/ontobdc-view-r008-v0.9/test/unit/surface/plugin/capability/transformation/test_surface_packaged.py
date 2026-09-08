from __future__ import annotations

import re
from pathlib import Path
from typing import Any, Dict, List, Optional

import pytest

from ontobdc_view.surface.adapter.document import (
    CONFIG_ID,
    JSONLD_ID,
    MATCHES_ID,
    SurfaceDocumentAdapter,
)
from ontobdc_view.surface.domain.machine.standard_surface_html.state import SurfaceGenerationProcessState
from ontobdc_view.surface.plugin.capability.transformation.surface_packaged import (
    SurfacePackagedCapability,
    _GlobalEventError,
)

_VALID_CONFIG: Dict[str, Any] = {
    "operation": {"enabled": True},
    "content": {"mode": "scroll"},
    "pinned": {"enabled": True},
    "slotTarget": 72,
    "gap": 12,
    "padding": 16,
    "tileMargin": 0,
}
_MATCHES: List[Dict[str, Any]] = [
    {
        "tile": "onto-logo-tile",
        "region": "operation",
        "minColumns": 1,
        "preferredColumns": 1,
        "maxColumns": 1,
        "minRows": 1,
        "preferredRows": 1,
        "maxRows": 1,
        "data": "urn:x:1",
    }
]


class _FakeContext:
    """Minimal real CliContextPort double: a plain dict-backed store.

    Not a mock -- SurfaceTransformationAdapter.write() calls
    set_parameter_value("surface_path", ...) and a later read must see that
    value, which a bare MagicMock would not wire up without extra plumbing.
    """

    def __init__(self, values: Dict[str, Any]) -> None:
        self._values: Dict[str, Any] = dict(values)

    def get_parameter_value(self, key: str) -> Any:
        return self._values.get(key)

    def set_parameter_value(self, key: str, value: Any) -> None:
        self._values[key] = value

    @property
    def root_path(self) -> str:
        return str(self._values.get("container_path") or "")


def _build_assembled_surface_document() -> str:
    """A document already at the surface_assembled stage -- everything
    SurfacePackagedCapability.execute() and the packaged-Surface check
    require to have happened before packaging."""
    document = SurfaceDocumentAdapter.make_initial_html("en")
    document = SurfaceDocumentAdapter.upsert_json_script(
        document, JSONLD_ID, [{"@id": "urn:x:1"}], "application/ld+json"
    )
    document = SurfaceDocumentAdapter.upsert_json_script(document, CONFIG_ID, _VALID_CONFIG)
    document = SurfaceDocumentAdapter.upsert_json_script(document, MATCHES_ID, _MATCHES)
    document = SurfaceDocumentAdapter.assemble_surface_markup(document, _MATCHES)
    document = re.sub(
        r"<onto-presentation-surface\b(?![^>]*\bdata-ontobdc-assembled=)",
        '<onto-presentation-surface data-ontobdc-assembled="true"',
        document,
        flags=re.IGNORECASE,
    )
    return SurfaceDocumentAdapter.set_state_marker(document, "surface_assembled")


def _write_surface(container_root: Path, document: str) -> Path:
    surface_path = container_root / "index.html"
    surface_path.write_text(document, encoding="utf-8")
    return surface_path


def _context_with_explicit_scripts(container_root: Path) -> _FakeContext:
    # Supplying surface_component_scripts bypasses _read_component_sources()
    # (and therefore ontobdc_view.component_source()) entirely -- the
    # promoter and file-viewer sourcing below stay real, since they are not
    # gated behind this parameter.
    return _FakeContext(
        {
            "container_path": str(container_root),
            "surface_component_scripts": [
                "customElements.define('onto-logo-tile', class extends HTMLElement {});"
            ],
        }
    )


class TestSnapshotThroughHelpers:
    def test_snapshot_through_is_minus_one_when_the_snapshot_carries_no_attribute(
        self,
    ) -> None:
        document = SurfaceDocumentAdapter.upsert_json_script(
            SurfaceDocumentAdapter.make_initial_html("en"), JSONLD_ID, [], "application/ld+json"
        )
        assert SurfacePackagedCapability._snapshot_through(document) == -1

    def test_snapshot_through_is_minus_one_when_the_snapshot_script_is_absent(self) -> None:
        document = SurfaceDocumentAdapter.make_initial_html("en")
        assert SurfacePackagedCapability._snapshot_through(document) == -1

    def test_set_snapshot_through_marks_and_snapshot_through_reads_it_back(self) -> None:
        document = SurfaceDocumentAdapter.upsert_json_script(
            SurfaceDocumentAdapter.make_initial_html("en"), JSONLD_ID, [], "application/ld+json"
        )
        marked = SurfacePackagedCapability._set_snapshot_through(document, 7)
        assert SurfacePackagedCapability._snapshot_through(marked) == 7

    def test_set_snapshot_through_replaces_a_previous_value_rather_than_duplicating_it(
        self,
    ) -> None:
        document = SurfaceDocumentAdapter.upsert_json_script(
            SurfaceDocumentAdapter.make_initial_html("en"), JSONLD_ID, [], "application/ld+json"
        )
        once = SurfacePackagedCapability._set_snapshot_through(document, 3)
        twice = SurfacePackagedCapability._set_snapshot_through(once, 9)
        assert SurfacePackagedCapability._snapshot_through(twice) == 9
        assert twice.count("data-snapshot-through") == 1

    def test_set_snapshot_through_raises_global_event_error_without_a_snapshot_script(
        self,
    ) -> None:
        document = SurfaceDocumentAdapter.make_initial_html("en")
        with pytest.raises(_GlobalEventError):
            SurfacePackagedCapability._set_snapshot_through(document, 0)

    def test_prepare_document_for_journal_drops_optional_end_tags_and_appends_marker(
        self,
    ) -> None:
        document = SurfaceDocumentAdapter.make_initial_html("en")
        prepared = SurfacePackagedCapability._prepare_document_for_journal(document)
        assert "</body>" not in prepared
        assert "</html>" not in prepared
        assert prepared.rstrip().endswith("<!-- ontobdc:global-event-journal -->")

    def test_prepare_document_for_journal_is_idempotent(self) -> None:
        document = SurfaceDocumentAdapter.make_initial_html("en")
        once = SurfacePackagedCapability._prepare_document_for_journal(document)
        twice = SurfacePackagedCapability._prepare_document_for_journal(once)
        assert twice == once.rstrip() + "\n"


class TestRequiredComponentTags:
    def test_lists_the_surface_tag_first_then_every_distinct_matched_tile(self) -> None:
        document = SurfaceDocumentAdapter.upsert_json_script(
            SurfaceDocumentAdapter.make_initial_html("en"),
            MATCHES_ID,
            [
                {"tile": "onto-logo-tile"},
                {"tile": "onto-language-tile"},
                {"tile": "onto-logo-tile"},
            ],
        )
        capability = SurfacePackagedCapability()
        tags = capability._required_component_tags(document)
        assert tags == ["onto-presentation-surface", "onto-logo-tile", "onto-language-tile"]

    def test_raises_when_no_matches_script_is_present(self) -> None:
        # _required_component_tags has no fallback for a missing matches
        # script -- it is only ever called after surface_matched, which
        # guarantees the script exists.
        document = SurfaceDocumentAdapter.make_initial_html("en")
        capability = SurfacePackagedCapability()
        with pytest.raises(ValueError, match="Missing script"):
            capability._required_component_tags(document)


class TestExecute:
    def test_packages_a_real_assembled_surface_with_explicit_component_scripts(
        self, tmp_path: Path
    ) -> None:
        container_root = tmp_path.resolve()
        _write_surface(container_root, _build_assembled_surface_document())
        context = _context_with_explicit_scripts(container_root)

        capability = SurfacePackagedCapability()
        result = capability.execute(context)

        assert result["resulting_state"] is SurfaceGenerationProcessState.SURFACE_PACKAGED
        assert result["component_script_count"] == 1

        packaged = Path(result["surface_path"]).read_text(encoding="utf-8")
        assert "window.OntoBDCComponentEventPromoter = promoter;" in packaged
        assert "onto-logo-tile" in packaged
        assert "</body>" not in packaged
        assert "</html>" not in packaged
        assert packaged.rstrip().endswith("<!-- ontobdc:global-event-journal -->")

        # The packaged-Surface check ran for real inside execute() (require_check);
        # calling check() again independently must agree.
        assert capability.check(context) is True

    def test_promoter_script_is_embedded_before_component_implementations(
        self, tmp_path: Path
    ) -> None:
        container_root = tmp_path.resolve()
        _write_surface(container_root, _build_assembled_surface_document())
        context = _context_with_explicit_scripts(container_root)

        result = SurfacePackagedCapability().execute(context)
        packaged = Path(result["surface_path"]).read_text(encoding="utf-8")

        # Compare the embedded <script data-ontobdc-surface-component="N">
        # blocks specifically -- "onto-logo-tile" alone would also match the
        # tag name already present in the assembled markup, which sits
        # earlier in <body> than either embedded script.
        promoter_index = packaged.index('data-ontobdc-surface-component="0"')
        component_index = packaged.index('data-ontobdc-surface-component="1"')
        assert promoter_index < component_index
        assert packaged.index(
            "window.OntoBDCComponentEventPromoter", promoter_index
        ) < component_index

    def test_repackaging_replaces_a_stale_bridge_instead_of_duplicating_it(
        self, tmp_path: Path
    ) -> None:
        # Simulates recovering from an earlier partial packaging attempt: the
        # assembled document already carries a stale promoter/component set
        # (</body> still present -- the journal-prep step that removes it
        # only ever runs at the end of a successful execute()) and execute()
        # must replace it, not accumulate a second copy.
        container_root = tmp_path.resolve()
        document = _build_assembled_surface_document()
        stale = SurfaceDocumentAdapter.embed_component_scripts(
            document, ["/* stale promoter */", "/* stale component */"]
        )
        _write_surface(container_root, stale)
        context = _context_with_explicit_scripts(container_root)

        result = SurfacePackagedCapability().execute(context)
        packaged = Path(result["surface_path"]).read_text(encoding="utf-8")

        assert packaged.count('data-ontobdc-surface-component="0"') == 1
        assert packaged.count("window.OntoBDCComponentEventPromoter = promoter;") == 1
        assert "/* stale promoter */" not in packaged
        assert "/* stale component */" not in packaged

    def test_raises_when_no_component_scripts_are_available(self, tmp_path: Path) -> None:
        container_root = tmp_path.resolve()
        _write_surface(container_root, _build_assembled_surface_document())
        # No surface_component_scripts and no real Tile asset resolvable for
        # a made-up tag under this temporary root -- _read_component_sources()
        # returns [] for real (ontobdc_view.component_source() finds nothing).
        document = SurfaceDocumentAdapter.upsert_json_script(
            SurfaceDocumentAdapter.make_initial_html("en"),
            MATCHES_ID,
            [{"tile": "onto-does-not-exist-tile"}],
        )
        document = SurfaceDocumentAdapter.upsert_json_script(
            document, JSONLD_ID, [], "application/ld+json"
        )
        _write_surface(container_root, document)
        context = _FakeContext({"container_path": str(container_root)})

        with pytest.raises(ValueError, match="No complete build-ready Surface component set"):
            SurfacePackagedCapability().execute(context)

    def test_check_is_false_before_packaging(self, tmp_path: Path) -> None:
        container_root = tmp_path.resolve()
        _write_surface(container_root, _build_assembled_surface_document())
        context = _FakeContext({"container_path": str(container_root)})
        assert SurfacePackagedCapability().check(context) is False

    def test_packages_from_the_shipped_component_set_without_explicit_scripts(
        self, tmp_path: Path
    ) -> None:
        # No surface_component_scripts: _read_component_sources() has to
        # resolve every required tag from the installed package for real.
        # The first required tag is always onto-presentation-surface (the
        # Surface container element, not a Tile) -- if its JS asset goes
        # missing from the package this is the only test that fails, and
        # ``ontobdc view`` would otherwise break end-to-end with a green
        # suite.
        container_root = tmp_path.resolve()
        _write_surface(container_root, _build_assembled_surface_document())
        context = _FakeContext({"container_path": str(container_root)})

        result = SurfacePackagedCapability().execute(context)

        assert result["resulting_state"] is SurfaceGenerationProcessState.SURFACE_PACKAGED
        assert result["component_script_count"] >= 2  # surface element + onto-logo-tile
        packaged = Path(result["surface_path"]).read_text(encoding="utf-8")
        assert "onto-presentation-surface" in packaged
        assert "onto-logo-tile" in packaged
        assert "__ONTOBDC_BUILD_" not in packaged
