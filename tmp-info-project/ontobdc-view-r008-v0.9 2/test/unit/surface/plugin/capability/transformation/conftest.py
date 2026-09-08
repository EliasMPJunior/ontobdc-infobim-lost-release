from __future__ import annotations

from typing import Any, Callable, Dict, List, Optional

import pytest

from ontobdc_view.surface.adapter.document import (
    CONFIG_ID,
    JSONLD_ID,
    MATCHES_ID,
    SurfaceDocumentAdapter,
)

# Reused by every capability test past SURFACE_INITIALIZED that needs a
# real, valid document already at an earlier pipeline stage to build on --
# one function that stacks the same transformations the real capabilities
# themselves apply, through SurfaceDocumentAdapter, so a fixture document is
# never more than the concatenation of steps this session already migrated
# and unit-tested individually.
DEFAULT_JSONLD: List[Dict[str, Any]] = [
    {"@id": "urn:test:entity:1", "@type": ["urn:test:Thing"]}
]
DEFAULT_CONFIG: Dict[str, Any] = {
    "operation": {"enabled": True},
    "content": {"mode": "scroll"},
    "pinned": {"enabled": True},
    "slotTarget": 72,
    "gap": 12,
    "padding": 16,
    "tileMargin": 0,
}

_STAGE_ORDER = (
    "surface_initialized",
    "surface_enriched",
    "surface_set",
    "surface_branded",
    "surface_matched",
    "surface_assembled",
)


def build_surface_document(
    *,
    lang: str = "en",
    jsonld: Optional[Any] = None,
    config: Optional[Dict[str, Any]] = None,
    matches: Optional[List[Dict[str, Any]]] = None,
    through_state: str = "surface_initialized",
) -> str:
    if through_state not in _STAGE_ORDER:
        raise ValueError(f"unknown or unsupported stage: {through_state!r}")
    stop_index = _STAGE_ORDER.index(through_state)

    document = SurfaceDocumentAdapter.make_initial_html(lang)
    document = SurfaceDocumentAdapter.set_state_marker(document, "surface_initialized")
    if stop_index == 0:
        return document

    document = SurfaceDocumentAdapter.upsert_json_script(
        document,
        JSONLD_ID,
        jsonld if jsonld is not None else DEFAULT_JSONLD,
        "application/ld+json",
    )
    document = SurfaceDocumentAdapter.set_state_marker(document, "surface_enriched")
    if stop_index == 1:
        return document

    document = SurfaceDocumentAdapter.upsert_json_script(
        document, CONFIG_ID, config if config is not None else dict(DEFAULT_CONFIG)
    )
    document = SurfaceDocumentAdapter.set_state_marker(document, "surface_set")
    if stop_index == 2:
        return document

    # surface_branded resolves SVG branding assets on disk; it does not add
    # anything a later state's check() or a capability under test reads back
    # from the document, so this stage is just the marker advancing.
    document = SurfaceDocumentAdapter.set_state_marker(document, "surface_branded")
    if stop_index == 3:
        return document

    document = SurfaceDocumentAdapter.upsert_json_script(
        document, MATCHES_ID, matches if matches is not None else []
    )
    document = SurfaceDocumentAdapter.set_state_marker(document, "surface_matched")
    if stop_index == 4:
        return document

    document = SurfaceDocumentAdapter.assemble_surface_markup(
        document, matches if matches is not None else []
    )
    document = document.replace(
        "<onto-presentation-surface>",
        '<onto-presentation-surface data-ontobdc-assembled="true">',
    )
    document = SurfaceDocumentAdapter.set_state_marker(document, "surface_assembled")
    return document


class FakeCliContext:
    """A minimal real CliContextPort double: a plain dict-backed store.

    Not a mock -- several capabilities call get_parameter_value(key) for a
    key that a *previous* call in the same test set via
    set_parameter_value(key, value) (e.g. SurfaceTransformationAdapter.write()
    writes back "surface_path"). A bare MagicMock would not wire that up
    without extra manual plumbing; this class makes it work the same way the
    real CLI context does.
    """

    def __init__(self, values: Optional[Dict[str, Any]] = None) -> None:
        self._values: Dict[str, Any] = dict(values or {})

    def get_parameter_value(self, key: str) -> Any:
        return self._values.get(key)

    def set_parameter_value(self, key: str, value: Any) -> None:
        self._values[key] = value

    def has_parameter(self, key: str) -> bool:
        return key in self._values

    @property
    def root_path(self) -> str:
        # Falls back to container_path: most tests don't care about the
        # container/workspace distinction and only ever set one path.
        # Pass an explicit root_path= for a test that does (e.g. resolving
        # a workspace-level, not container-level, branding asset).
        return str(self._values.get("root_path") or self._values.get("container_path") or "")


@pytest.fixture
def fake_context() -> Callable[..., FakeCliContext]:
    def _make(**values: Any) -> FakeCliContext:
        return FakeCliContext(values)

    return _make
