"""The promotion policy is read from real RDF, never from Python."""

from rdflib import RDF, URIRef

from ontobdc_web_dock.dock.adapter.policy import (
    EVENT,
    VIEW,
    PromotionPolicy,
    local_name,
)


def test_surface_loaded_is_a_component_event(policy_turtle) -> None:
    policy = PromotionPolicy.from_turtle(policy_turtle)
    assert "SurfaceLoaded" in policy.component_event_names()
    resolved = policy.resolve_component_event("SurfaceLoaded")
    assert resolved == URIRef(EVENT.SurfaceLoaded)
    assert (resolved, RDF.type, URIRef(VIEW.ComponentEvent)) in policy.graph


def test_surface_loaded_promotes_to_page_loaded(policy_turtle) -> None:
    policy = PromotionPolicy.from_turtle(policy_turtle)
    targets = policy.promotion_targets(
        policy.resolve_component_event("SurfaceLoaded")
    )
    assert [local_name(target) for target in targets] == ["PageLoaded"]


def test_page_loaded_is_a_shared_event(policy_turtle) -> None:
    policy = PromotionPolicy.from_turtle(policy_turtle)
    assert "PageLoaded" in policy.shared_event_names()
    assert policy.is_shared_event(URIRef(EVENT.PageLoaded))


def test_component_event_without_promotes_to_has_no_targets(
    policy_turtle,
) -> None:
    policy = PromotionPolicy.from_turtle(policy_turtle)
    # PageLoaded is a SharedEvent, not a ComponentEvent -> not resolvable
    assert policy.resolve_component_event("PageLoaded") is None


def test_promotes_to_is_multivalued(policy_turtle) -> None:
    # event:TileExpanded  view:promotesTo  event:TileResized, event:SurfaceAreaFilled
    policy = PromotionPolicy.from_turtle(policy_turtle)
    targets = policy.promotion_targets(
        policy.resolve_component_event("TileExpanded")
    )
    assert sorted(local_name(target) for target in targets) == [
        "SurfaceAreaFilled",
        "TileResized",
    ]
