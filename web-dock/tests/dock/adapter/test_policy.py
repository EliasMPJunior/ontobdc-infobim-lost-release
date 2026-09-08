from __future__ import annotations

import pytest
from rdflib import Namespace, URIRef

from ontobdc_web_dock.dock.adapter.policy import (
    PromotionPolicy,
    PromotionPolicyError,
    local_name,
)

# A small, self-contained fixture -- not the real BrasidataCenter policy.
# This layer tests PromotionPolicy's parsing/indexing behavior in general
# (zero/one/many targets, local-name resolution); the real presentation_event.ttl
# content is verified separately, against the packaged file, by
# brasidatacenter's tests/tool/test_presentation_event_ontology.py.
_TEST_NS = "http://example.org/presentation_event.ttl#"
EVENT = Namespace(_TEST_NS)
_FIXTURE_TURTLE = f"""
@prefix view: <http://datacenter.app.br/ontology/ontobdc/domain/view.ttl#> .
@prefix event: <{_TEST_NS}> .
@prefix owl: <http://www.w3.org/2002/07/owl#> .

event:Zero a owl:NamedIndividual, view:ComponentEvent .
event:One a owl:NamedIndividual, view:ComponentEvent ;
    view:promotesTo event:TargetA .
event:Many a owl:NamedIndividual, view:ComponentEvent ;
    view:promotesTo event:TargetA, event:TargetB .
event:TargetA a owl:NamedIndividual, view:SharedEvent .
event:TargetB a owl:NamedIndividual, view:SharedEvent .
"""


def test_from_turtle_parses_and_indexes_component_and_shared_events() -> None:
    policy = PromotionPolicy.from_turtle(_FIXTURE_TURTLE)
    assert policy.component_event_names() == ["Many", "One", "Zero"]
    assert policy.shared_event_names() == ["TargetA", "TargetB"]


def test_from_turtle_raises_promotion_policy_error_for_invalid_turtle() -> None:
    with pytest.raises(PromotionPolicyError, match="not readable as Turtle"):
        PromotionPolicy.from_turtle("not { valid turtle @@@")


def test_local_name_uses_the_canonical_event_namespace_first() -> None:
    assert local_name(URIRef(f"{_TEST_NS}TileOpened")) == "TileOpened"


def test_local_name_falls_back_to_hash_or_slash_segment() -> None:
    assert local_name(URIRef("http://example.org/ns.ttl#Foo")) == "Foo"
    assert local_name(URIRef("http://example.org/path/Bar")) == "Bar"
    assert local_name(URIRef("NoSeparatorHere")) == "NoSeparatorHere"


def test_promotion_targets_returns_zero_one_and_every_multivalued_target() -> None:
    policy = PromotionPolicy.from_turtle(_FIXTURE_TURTLE)

    zero = policy.resolve_component_event("Zero")
    one = policy.resolve_component_event("One")
    many = policy.resolve_component_event("Many")
    assert zero is not None
    assert one is not None
    assert many is not None

    assert policy.promotion_targets(zero) == ()
    assert policy.promotion_targets(one) == (EVENT.TargetA,)
    assert policy.promotion_targets(many) == (EVENT.TargetA, EVENT.TargetB)


def test_resolve_component_event_returns_none_for_unknown_name() -> None:
    policy = PromotionPolicy.from_turtle(_FIXTURE_TURTLE)
    assert policy.resolve_component_event("DoesNotExist") is None


def test_is_shared_event_distinguishes_shared_from_component_events() -> None:
    policy = PromotionPolicy.from_turtle(_FIXTURE_TURTLE)
    assert policy.is_shared_event(EVENT.TargetA) is True
    assert policy.is_shared_event(EVENT.One) is False
