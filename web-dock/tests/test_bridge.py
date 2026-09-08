from __future__ import annotations

import json

import pytest

from ontobdc_web_dock import bridge
from ontobdc_web_dock.dock.adapter.listener import DockNotReadyError

_FIXTURE_TURTLE = """
@prefix view: <http://datacenter.app.br/ontology/ontobdc/domain/view.ttl#> .
@prefix event: <http://example.org/presentation_event.ttl#> .
@prefix owl: <http://www.w3.org/2002/07/owl#> .

event:One a owl:NamedIndividual, view:ComponentEvent ;
    view:promotesTo event:TargetA .
event:TargetA a owl:NamedIndividual, view:SharedEvent .
"""


@pytest.fixture(autouse=True)
def _reset_module_level_dock():
    # bootstrap()/promote()/is_ready() share one module-global _DOCK, matching
    # the single Pyodide-page-lifetime the bridge runs under in production.
    # Each test must start from an unbootstrapped state regardless of
    # execution order.
    bridge._DOCK = None
    yield
    bridge._DOCK = None


def test_is_ready_is_false_before_bootstrap() -> None:
    assert bridge.is_ready() is False


def test_bootstrap_reports_the_discovered_listener_and_policy_catalog() -> None:
    info = bridge.bootstrap(_FIXTURE_TURTLE)
    assert info["ready"] is True
    assert info["listeners"] == [
        "org.ontobdc.web_dock.dock.plugin.listener.presentation_event_promotion"
    ]
    assert info["componentEvents"] == ["One"]
    assert info["sharedEvents"] == ["TargetA"]
    assert bridge.is_ready() is True


def test_promote_before_bootstrap_fails_explicitly() -> None:
    with pytest.raises(DockNotReadyError):
        bridge.promote(json.dumps({"event": "One"}))


def test_promote_accepts_a_json_string_envelope() -> None:
    bridge.bootstrap(_FIXTURE_TURTLE)
    answer = json.loads(bridge.promote(json.dumps({"event": "One"})))
    assert answer["status"] == "promoted"
    assert answer["targets"] == [
        {"event": "TargetA", "iri": "http://example.org/presentation_event.ttl#TargetA"}
    ]


def test_promote_accepts_a_dict_envelope() -> None:
    bridge.bootstrap(_FIXTURE_TURTLE)
    answer = json.loads(bridge.promote({"event": "One"}))
    assert answer["status"] == "promoted"


def test_promote_raises_for_unreadable_json_string() -> None:
    bridge.bootstrap(_FIXTURE_TURTLE)
    with pytest.raises(DockNotReadyError, match="unreadable Component Event envelope"):
        bridge.promote("{not json")


def test_web_dock_facade_produces_the_same_answer_as_the_module_level_functions() -> None:
    bridge.bootstrap(_FIXTURE_TURTLE)
    module_level_answer = json.loads(bridge.promote(json.dumps({"event": "One"})))

    web_dock = bridge.WebDock(_FIXTURE_TURTLE)
    facade_answer = web_dock.promote("One")

    assert facade_answer["status"] == module_level_answer["status"]
    assert facade_answer["targets"] == module_level_answer["targets"]


def test_web_dock_promote_before_bootstrap_fails_explicitly() -> None:
    with pytest.raises(DockNotReadyError, match="WebDock was not bootstrapped"):
        bridge.WebDock().promote("One")
