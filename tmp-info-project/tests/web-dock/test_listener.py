"""The Listener returns the promoted event(s), read from RDF, via the
statechart -- and it is discovered as a plugin, not from a list."""

import pytest

from ontobdc_web_dock import WebDock, bootstrap, promote
from ontobdc_web_dock.dock.adapter.loader import ListenerLoader
from ontobdc_web_dock.dock.adapter.policy import PromotionPolicy
from ontobdc_web_dock.dock.domain.machine.promotion_state import (
    EventPromotionProcessState as S,
)
from ontobdc_web_dock.dock.domain.port.listener import ListenerPort
from ontobdc_web_dock.dock.plugin.listener.presentation_event import (
    PresentationEventPromotionListener,
)

_PROMOTION_TRACE = [
    "EVENT_RECEIVED",
    "SEMANTIC_EVENT_RESOLVED",
    "PROMOTION_POLICY_EVALUATED",
    "PROMOTION_TARGETS_RESOLVED",
    "RESPONSE_PRODUCED",
]
_UNRESOLVED_TRACE = [
    "EVENT_RECEIVED",
    "SEMANTIC_EVENT_RESOLVED",
    "RESPONSE_PRODUCED",
]


def _listener(policy_turtle) -> PresentationEventPromotionListener:
    return PresentationEventPromotionListener(
        PromotionPolicy.from_turtle(policy_turtle)
    )


def test_listener_is_discovered_through_plugin_listener() -> None:
    ids = {cls.METADATA.id for cls in ListenerLoader().get_all()}
    assert (
        "org.ontobdc.web_dock.dock.plugin.listener.presentation_event_promotion"
        in ids
    )
    for cls in ListenerLoader().get_all():
        assert issubclass(cls, ListenerPort)


def test_listener_returns_page_loaded_for_surface_loaded(
    policy_turtle,
) -> None:
    answer = _listener(policy_turtle).handle({"event": "SurfaceLoaded"})

    assert answer["status"] == "promoted"
    assert [t["event"] for t in answer["targets"]] == ["PageLoaded"]
    assert answer["trace"] == _PROMOTION_TRACE


def test_listener_returns_every_target_for_a_fan_out_event(
    policy_turtle,
) -> None:
    answer = _listener(policy_turtle).handle({"event": "TileExpanded"})

    assert answer["status"] == "promoted"
    assert sorted(t["event"] for t in answer["targets"]) == [
        "SurfaceAreaFilled",
        "TileResized",
    ]
    assert answer["trace"] == _PROMOTION_TRACE


def test_statechart_takes_the_no_promotion_path_for_unknown_events(
    policy_turtle,
) -> None:
    answer = _listener(policy_turtle).handle({"event": "NotAnEvent"})

    assert answer["status"] == "unresolved"
    assert answer["targets"] == []
    assert answer["trace"] == _UNRESOLVED_TRACE
    assert answer["state"] == S.RESPONSE_PRODUCED.value


def test_bridge_bootstrap_then_promote_json_roundtrip(policy_turtle) -> None:
    import json

    info = bootstrap(policy_turtle)
    assert info["ready"] is True
    assert "SurfaceLoaded" in info["componentEvents"]

    answer = json.loads(promote(json.dumps({"event": "SurfaceLoaded"})))
    assert answer["status"] == "promoted"
    assert answer["targets"][0]["event"] == "PageLoaded"
    assert answer["targets"][0]["iri"].endswith("#PageLoaded")


def test_webdock_object_facade(policy_turtle) -> None:
    answer = WebDock(policy_turtle).promote("TileOpened")
    assert answer["status"] == "promoted"
    assert sorted(t["event"] for t in answer["targets"]) == [
        "SurfaceAreaFilled",
        "TileReady",
    ]


def test_promote_before_bootstrap_is_an_explicit_error() -> None:
    from ontobdc_web_dock.dock.adapter.listener import DockNotReadyError

    with pytest.raises(DockNotReadyError):
        WebDock().promote("SurfaceLoaded")
