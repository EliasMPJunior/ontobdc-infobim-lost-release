from __future__ import annotations

from typing import List, Type

import pytest

from ontobdc_web_dock.dock.adapter.listener import DockNotReadyError, PresentationEventDock
from ontobdc_web_dock.dock.adapter.policy import PromotionPolicy
from ontobdc_web_dock.dock.domain.port.listener import ListenerPort
from ontobdc_web_dock.dock.plugin.listener.presentation_event import (
    PresentationEventPromotionListener,
)

_FIXTURE_TURTLE = """
@prefix view: <http://datacenter.app.br/ontology/ontobdc/domain/view.ttl#> .
@prefix event: <http://example.org/presentation_event.ttl#> .
@prefix owl: <http://www.w3.org/2002/07/owl#> .

event:One a owl:NamedIndividual, view:ComponentEvent ;
    view:promotesTo event:TargetA .
event:TargetA a owl:NamedIndividual, view:SharedEvent .
"""


class _EmptyLoader:
    """A narrowly-scoped fake used only to exercise the missing-registration
    error path -- the normal dispatch tests below use the real ListenerLoader
    and the real PresentationEventPromotionListener, per the architecture
    doc's testing guidelines."""

    def get_all(self, resource: str = "listener") -> List[Type[ListenerPort]]:
        return []


def _dock() -> PresentationEventDock:
    return PresentationEventDock(PromotionPolicy.from_turtle(_FIXTURE_TURTLE))


def test_listener_ids_reports_the_discovered_presentation_event_promotion_listener() -> None:
    assert _dock().listener_ids() == [PresentationEventPromotionListener.METADATA.id]


def test_policy_property_returns_the_bootstrapped_policy() -> None:
    policy = PromotionPolicy.from_turtle(_FIXTURE_TURTLE)
    dock = PresentationEventDock(policy)
    assert dock.policy is policy


def test_listener_returns_the_default_listener_registered_under_its_metadata_id() -> None:
    listener = _dock().listener()
    assert isinstance(listener, PresentationEventPromotionListener)


def test_listener_raises_dock_not_ready_error_and_reports_discovered_ids_when_missing() -> None:
    dock = PresentationEventDock(
        PromotionPolicy.from_turtle(_FIXTURE_TURTLE), loader=_EmptyLoader()
    )
    with pytest.raises(DockNotReadyError, match=r"discovered: \[\]"):
        dock.listener()


def test_promote_dispatches_through_the_registered_listener() -> None:
    answer = _dock().promote({"event": "One"})
    assert answer["status"] == "promoted"
    assert answer["targets"] == [{"event": "TargetA", "iri": "http://example.org/presentation_event.ttl#TargetA"}]
