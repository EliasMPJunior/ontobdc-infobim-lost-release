from __future__ import annotations

from rdflib import Namespace

from ontobdc_web_dock.dock.adapter.machine import EventPromotionMachine
from ontobdc_web_dock.dock.adapter.policy import PromotionPolicy
from ontobdc_web_dock.dock.domain.machine.promotion_state import (
    EventPromotionProcessState,
)

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

_FULL_TRACE = [
    EventPromotionProcessState.EVENT_RECEIVED,
    EventPromotionProcessState.SEMANTIC_EVENT_RESOLVED,
    EventPromotionProcessState.PROMOTION_POLICY_EVALUATED,
    EventPromotionProcessState.PROMOTION_TARGETS_RESOLVED,
    EventPromotionProcessState.RESPONSE_PRODUCED,
]
_UNRESOLVED_TRACE = [
    EventPromotionProcessState.EVENT_RECEIVED,
    EventPromotionProcessState.SEMANTIC_EVENT_RESOLVED,
    EventPromotionProcessState.RESPONSE_PRODUCED,
]


def _machine() -> EventPromotionMachine:
    return EventPromotionMachine(PromotionPolicy.from_turtle(_FIXTURE_TURTLE))


def test_unknown_event_name_is_unresolved_with_zero_targets() -> None:
    component_event, targets, trace = _machine().run("DoesNotExist")
    assert component_event is None
    assert targets == ()
    assert trace == _UNRESOLVED_TRACE


def test_declared_component_event_without_promotion_runs_the_full_trace() -> None:
    component_event, targets, trace = _machine().run("Zero")
    assert component_event == EVENT.Zero
    assert targets == ()
    assert trace == _FULL_TRACE


def test_one_target_resolves_source_and_the_single_target() -> None:
    component_event, targets, trace = _machine().run("One")
    assert component_event == EVENT.One
    assert targets == (EVENT.TargetA,)
    assert trace == _FULL_TRACE


def test_multiple_targets_resolves_source_and_every_target() -> None:
    component_event, targets, trace = _machine().run("Many")
    assert component_event == EVENT.Many
    assert targets == (EVENT.TargetA, EVENT.TargetB)
    assert trace == _FULL_TRACE


def test_trace_state_reports_the_final_state_value() -> None:
    _, _, trace = _machine().run("One")
    assert (
        EventPromotionMachine.trace_state(trace)
        == EventPromotionProcessState.RESPONSE_PRODUCED.value
    )


def test_trace_state_reports_undefined_for_an_empty_trace() -> None:
    assert (
        EventPromotionMachine.trace_state([])
        == EventPromotionProcessState.UNDEFINED.value
    )


def test_trace_names_returns_the_plain_state_names() -> None:
    _, _, trace = _machine().run("Many")
    assert EventPromotionMachine.trace_names(trace) == [
        "EVENT_RECEIVED",
        "SEMANTIC_EVENT_RESOLVED",
        "PROMOTION_POLICY_EVALUATED",
        "PROMOTION_TARGETS_RESOLVED",
        "RESPONSE_PRODUCED",
    ]
