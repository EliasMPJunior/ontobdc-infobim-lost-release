from __future__ import annotations

from ontobdc_web_dock.dock.adapter.policy import PromotionPolicy
from ontobdc_web_dock.dock.plugin.listener.presentation_event import (
    PresentationEventPromotionListener,
)

_FIXTURE_TURTLE = """
@prefix view: <http://datacenter.app.br/ontology/ontobdc/domain/view.ttl#> .
@prefix event: <http://example.org/presentation_event.ttl#> .
@prefix owl: <http://www.w3.org/2002/07/owl#> .

event:NotPromoted a owl:NamedIndividual, view:ComponentEvent .
event:Promoted a owl:NamedIndividual, view:ComponentEvent ;
    view:promotesTo event:TargetA, event:TargetB .
event:TargetA a owl:NamedIndividual, view:SharedEvent .
event:TargetB a owl:NamedIndividual, view:SharedEvent .
"""


def _listener() -> PresentationEventPromotionListener:
    return PresentationEventPromotionListener(PromotionPolicy.from_turtle(_FIXTURE_TURTLE))


def test_listens_to_reports_component_event() -> None:
    assert _listener().listens_to() == "ComponentEvent"


def test_policy_property_returns_the_bootstrapped_policy() -> None:
    policy = PromotionPolicy.from_turtle(_FIXTURE_TURTLE)
    assert PresentationEventPromotionListener(policy).policy is policy


def test_handle_reports_unresolved_for_an_undeclared_event_name() -> None:
    answer = _listener().handle({"event": "DoesNotExist"})
    assert answer["status"] == "unresolved"
    assert answer["componentEvent"] == "DoesNotExist"
    assert answer["componentEventIri"] == ""
    assert answer["targets"] == []
    assert answer["trace"] == [
        "EVENT_RECEIVED",
        "SEMANTIC_EVENT_RESOLVED",
        "RESPONSE_PRODUCED",
    ]


def test_handle_reports_not_promoted_for_a_declared_event_without_targets() -> None:
    answer = _listener().handle({"event": "NotPromoted"})
    assert answer["status"] == "not_promoted"
    assert answer["componentEventIri"] == "http://example.org/presentation_event.ttl#NotPromoted"
    assert answer["targets"] == []


def test_handle_reports_promoted_with_local_names_and_full_iris_for_every_target() -> None:
    answer = _listener().handle({"event": "Promoted"})
    assert answer["status"] == "promoted"
    assert answer["targets"] == [
        {"event": "TargetA", "iri": "http://example.org/presentation_event.ttl#TargetA"},
        {"event": "TargetB", "iri": "http://example.org/presentation_event.ttl#TargetB"},
    ]
    assert answer["trace"][-1] == "RESPONSE_PRODUCED"
    assert answer["state"] == "__response_produced__"


def test_handle_treats_a_missing_envelope_event_key_as_an_empty_occurrence_name() -> None:
    answer = _listener().handle({})
    assert answer["status"] == "unresolved"
    assert answer["componentEvent"] == ""
