"""The presentation event architecture has exactly one semantics, and it is
not in JavaScript.

These tests read the shipped component sources and pin the architectural
invariants that a well-meaning "simpler" JavaScript refactor would break:
no Tile decides a promotion, no file holds a Component -> Shared table, the
Surface's event bar shows promotions rather than DOM traffic, and the
bridge really does route through the Python Listener with no fallback.
"""

import re
from pathlib import Path

import ontobdc_view

import pytest

ASSETS = Path(__file__).resolve().parents[1] / "src/ontobdc_view/component/asset"

BRIDGE = "component_event_promoter.js"
SURFACE = "onto-presentation-surface.js"

COMPONENT_EVENT_TYPE = "ontobdc:component-event"
SHARED_EVENT_TYPE = "ontobdc:shared-event"

# Every Shared Event name in the Release 8 policy. No component source may
# construct or dispatch one of these itself.
SHARED_EVENT_NAMES = [
    "PageLoaded",
    "TileReady",
    "TileStandby",
    "TileResized",
    "SurfaceAreaFilled",
    "SurfaceAreaEmptied",
    "SurfaceObscured",
    "SurfaceRevealed",
    "EntityPageRequested",
    "EntityPageDismissRequested",
]

# The Component Events each Tile/Surface announces.
EMITTERS = {
    "onto-presentation-surface.js": {"SurfaceLoaded"},
    "onto-file-tree-tile.js": {"EntitySelected", "EntityPageOpenRequested", "TileFullSized", "TileRestored"},
    "onto-file-viewer-tile.js": {
        "TileOpened",
        "TileClosed",
        "TileFullSized",
        "TileRestored",
        "EntityPageCloseRequested",
    },
    "onto-csv-file-tile.js": {"TileOpened", "TileClosed", "TileFullSized", "TileRestored"},
    "onto-generic-file-tile.js": {"TileOpened", "TileClosed", "TileFullSized", "TileRestored"},
    "onto-image-file-tile.js": {"TileOpened", "TileClosed", "TileFullSized", "TileRestored"},
    "onto-pdf-file-tile.js": {"TileOpened", "TileClosed", "TileFullSized", "TileRestored"},
    "onto-workstream-tile.js": {"TileExpanded", "TileCollapsed"},
    "onto-file-size-tile.js": {"TileClosed"},
    "onto-photo-tile.js": {"EntitySelected", "EntityPageOpenRequested"},
}

TILE_SOURCES = sorted(name for name in EMITTERS if name != SURFACE)

ALL_COMPONENT_SOURCES = sorted(
    path.name
    for path in ASSETS.glob("*.js")
    if path.name != BRIDGE and "vendor" not in path.parts
)


def source(name: str) -> str:
    if name == BRIDGE:
        return ontobdc_view.component_event_promoter_source()
    return (ASSETS / name).read_text(encoding="utf-8")


def method_body(code: str, header: str) -> str:
    """One method's body, from its header to the closing brace at method
    indentation — so a windowed assertion never spills into the next
    method and quietly passes (or fails) on the wrong code."""
    start = code.index(header)
    end = code.index("\n  }", start)
    return code[start:end]


def code_only(text: str) -> str:
    """The source with comments stripped, so an explanatory comment about
    the retired mechanism never satisfies (or trips) a code assertion."""
    text = re.sub(r"/\*.*?\*/", "", text, flags=re.DOTALL)
    return "\n".join(re.sub(r"//.*$", "", line) for line in text.splitlines())


# --------------------------------------------------------------------------
# The retired JavaScript semantics is gone
# --------------------------------------------------------------------------


def test_the_surface_no_longer_holds_a_list_of_globally_semantic_event_types():
    assert "PRESENTATION_GLOBAL_EVENT_TYPES" not in code_only(source(SURFACE))


@pytest.mark.parametrize("name", ALL_COMPONENT_SOURCES)
def test_no_component_uses_the_retired_presentation_global_event_names(name):
    """`show-details-requested` and `entity-selected` were the parallel
    semantic bus. Nothing may dispatch or listen for them any more."""
    code = code_only(source(name))
    assert "show-details-requested" not in code
    assert "entity-selected" not in code


@pytest.mark.parametrize("name", ALL_COMPONENT_SOURCES + [BRIDGE])
def test_no_component_holds_a_promotion_map(name):
    """A promotion rule in JavaScript is the thing this architecture
    removes. The give-away is a Component Event name and a Shared Event
    name written into the same expression — a literal map, a switch case, a
    registry entry or a ternary translating one into the other."""
    code = code_only(source(name))
    component_names = sorted({event for events in EMITTERS.values() for event in events})
    for line in code.splitlines():
        if not any(component in line for component in component_names):
            continue
        offenders = [shared for shared in SHARED_EVENT_NAMES if shared in line]
        assert not offenders, f"{name}: {line.strip()!r} pairs a Component Event with {offenders}"


@pytest.mark.parametrize("name", ALL_COMPONENT_SOURCES)
def test_no_component_source_even_mentions_a_shared_event_name_in_code(name):
    """Consumers filter on a Shared Event name they were promoted *into*
    (`EntityPageRequested`, `EntityPageDismissRequested`) — that is
    subscribing, not deciding. No other Shared Event name belongs in a
    component's code at all, because nothing there produces one."""
    consumable = {"EntityPageRequested", "EntityPageDismissRequested"}
    code = code_only(source(name))
    for shared in SHARED_EVENT_NAMES:
        if shared in consumable:
            continue
        assert shared not in code, f"{name} mentions the Shared Event {shared}"


# --------------------------------------------------------------------------
# Tiles announce, they never promote
# --------------------------------------------------------------------------


@pytest.mark.parametrize("name", TILE_SOURCES)
def test_a_tile_dispatches_only_component_events(name):
    """Every `dispatchEvent` in a Tile carries the Component Event envelope.
    A Tile dispatching a Shared Event directly is the shortcut the
    architecture forbids."""
    code = code_only(source(name))
    dispatched = re.findall(r"new CustomEvent\(\s*([^,]+),", code)
    assert dispatched, f"{name} dispatches nothing at all"
    allowed = {"COMPONENT_EVENT_TYPE"}
    # Presentation-state events (language/theme) are a different, documented
    # event family and keep their own names.
    allowed |= {'"language-changed"', '"theme-changed"', "type"}
    for expression in dispatched:
        assert expression.strip() in allowed, f"{name} dispatches {expression.strip()}"


@pytest.mark.parametrize("name", TILE_SOURCES)
def test_a_tile_never_dispatches_the_shared_event_envelope(name):
    code = code_only(source(name))
    assert "SHARED_EVENT_TYPE" not in code or "dispatchEvent" in code
    assert not re.search(
        r"dispatchEvent\(\s*new CustomEvent\(\s*SHARED_EVENT_TYPE", code
    ), f"{name} dispatches a Shared Event directly"


@pytest.mark.parametrize(("name", "events"), sorted(EMITTERS.items()))
def test_each_component_announces_the_component_events_it_owns(name, events):
    code = code_only(source(name))
    for event in events:
        assert re.search(
            rf'#emitComponentEvent\(\s*"{event}"', code
        ) or re.search(
            rf'\?\s*"{event}"|:\s*"{event}"', code
        ), f"{name} does not announce {event}"


@pytest.mark.parametrize("name", TILE_SOURCES)
def test_component_events_bubble_and_compose_so_they_reach_the_dock(name):
    code = code_only(source(name))
    envelope = code[code.index("new CustomEvent(COMPONENT_EVENT_TYPE") :][:400]
    assert "bubbles: true" in envelope
    assert "composed: true" in envelope


@pytest.mark.parametrize("name", TILE_SOURCES)
def test_the_envelope_carries_the_semantic_name_and_the_origin(name):
    code = code_only(source(name))
    envelope = code[code.index("new CustomEvent(COMPONENT_EVENT_TYPE") :][:600]
    assert "event: name" in envelope
    assert "tile: this.localName" in envelope


# --------------------------------------------------------------------------
# Fullscreen reflects the state reached, not the click
# --------------------------------------------------------------------------


FULLSCREEN_TILES = [
    name for name, events in EMITTERS.items() if "TileFullSized" in events
]


@pytest.mark.parametrize("name", sorted(FULLSCREEN_TILES))
def test_fullscreen_occurrences_come_from_fullscreenchange(name):
    """The user can leave fullscreen with Escape or the browser's own UI, so
    a click handler is not evidence that the state changed."""
    code = code_only(source(name))
    assert 'addEventListener("fullscreenchange"' in code
    assert 'removeEventListener("fullscreenchange"' in code
    handler = code[code.index("#onFullscreenChange = () =>") :][:600]
    assert "document.fullscreenElement === this" in handler
    assert '"TileFullSized"' in handler and '"TileRestored"' in handler


@pytest.mark.parametrize("name", sorted(FULLSCREEN_TILES))
def test_the_fullscreen_button_handler_does_not_announce_the_occurrence(name):
    """`#toggleFullscreen` states an intention; it must not claim the state
    was reached."""
    code = code_only(source(name))
    toggle = method_body(code, "  #toggleFullscreen(force) {")
    assert "TileFullSized" not in toggle
    assert "TileRestored" not in toggle


# --------------------------------------------------------------------------
# The entity page chain
# --------------------------------------------------------------------------


def test_the_requesting_tile_does_not_open_the_page_itself():
    """onto-file-tree-tile asks; the viewer answers. The requester never
    performs the consumer's responsibility."""
    code = code_only(source("onto-file-tree-tile.js"))
    activate = method_body(code, "  #activateFile(path) {")
    assert 'this.#emitComponentEvent("EntityPageOpenRequested"' in activate
    assert "openFile" not in activate
    assert "onto-file-viewer-tile" not in activate


def test_the_viewer_opens_only_on_the_promoted_shared_event():
    """`default_closed` means the element may not exist when the Shared
    Event arrives, so opening is owned by the module-level dispatcher that
    can create it; the instance handles only the dismissal. Handling the
    open in both places would open the same file twice."""
    code = code_only(source("onto-file-viewer-tile.js"))
    assert "addEventListener(SHARED_EVENT_TYPE" in code
    handler = method_body(code, "  handleSharedEvent(event) {")
    assert 'detail.event !== "EntityPageDismissRequested"' in handler
    assert "EntityPageRequested\"" not in handler
    # rindex: the first occurrence is the instance listener in connectedCallback.
    dispatcher = code[code.rindex("document.addEventListener(SHARED_EVENT_TYPE") :][:700]
    assert 'detail.event !== "EntityPageRequested"' in dispatcher
    assert "viewer.openFile?.(path)" in dispatcher


def test_the_viewer_close_control_requests_rather_than_closes():
    code = code_only(source("onto-file-viewer-tile.js"))
    close = method_body(code, "  #close() {")
    assert 'this.#emitComponentEvent("EntityPageCloseRequested"' in close
    # The actual dismissal lives behind the promoted Shared Event.
    assert ".close(this)" not in close


def test_the_viewer_dismissal_runs_only_from_the_promoted_shared_event():
    code = code_only(source("onto-file-viewer-tile.js"))
    dismiss = method_body(code, "  dismissPage() {")
    assert ".close(this)" in dismiss
    assert 'this.#emitComponentEvent("TileClosed"' in dismiss


def test_the_iframe_close_message_goes_through_the_same_chain():
    """The standalone viewer page's postMessage used to hide the Tile
    directly, bypassing the event architecture entirely."""
    code = code_only(source("onto-file-viewer-tile.js"))
    handler = code[code.index('payload.type !== "ontobdc:viewer:close-requested"') :][:400]
    assert "requestPageDismissal()" in handler
    assert "dataset.tileClosed" not in handler


@pytest.mark.parametrize(
    "name",
    ["onto-csv-file-tile.js", "onto-generic-file-tile.js", "onto-image-file-tile.js", "onto-pdf-file-tile.js"],
)
def test_preview_tiles_reveal_themselves_on_the_promoted_shared_event(name):
    code = code_only(source(name))
    handler = method_body(code, "  #handleSharedEvent(event) {")
    assert 'event.detail?.event !== "EntityPageRequested"' in handler
    assert 'this.#emitComponentEvent("TileOpened"' in handler


# --------------------------------------------------------------------------
# The Surface event bar
# --------------------------------------------------------------------------


def test_the_event_bar_is_written_only_by_a_dock_decided_promotion():
    code = code_only(source(SURFACE))
    writes = re.findall(r"this\.#writeEventBar\(", code)
    assert len(writes) == 2  # announcePromotion + announcePromotionFailure
    announce = method_body(code, "  announcePromotion({")
    assert "this.#writeEventBar(" in announce
    failure = method_body(code, "  announcePromotionFailure(error) {")
    assert "this.#writeEventBar(" in failure


def test_the_surface_does_not_log_component_events_it_happens_to_see():
    """The bar is not a trace of DOM traffic: the Surface registers no
    listener that writes an event onto it."""
    code = code_only(source(SURFACE))
    for match in re.finditer(r"addEventListener\(([^)]*)\)", code):
        assert "writeEventBar" not in match.group(0)
    assert "addEventListener(COMPONENT_EVENT_TYPE" not in code
    assert "addEventListener(SHARED_EVENT_TYPE" not in code


def test_layout_mechanics_notifications_stay_off_the_event_bar():
    """`surface-tile-pinned` and friends are the element's imperative API
    reporting that a DOM operation completed — they are not promotions."""
    code = code_only(source(SURFACE))
    dispatch = method_body(code, "  #dispatch(type, detail) {")
    assert "writeEventBar" not in dispatch
    assert "announcePromotion" not in dispatch


def test_the_surface_announces_surface_loaded_as_a_component_event():
    code = code_only(source(SURFACE))
    assert 'this.#emitComponentEvent("SurfaceLoaded"' in code
    envelope = code[code.index("new CustomEvent(COMPONENT_EVENT_TYPE") :][:400]
    assert "bubbles: true" in envelope and "composed: true" in envelope


def test_the_surface_never_decides_a_promotion_of_its_own():
    code = code_only(source(SURFACE))
    announce = code[code.index("announcePromotion({") : code.index("announcePromotionFailure")]
    # It reports the names it was handed; it does not derive them.
    for shared in SHARED_EVENT_NAMES:
        assert shared not in announce
