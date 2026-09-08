"""Every ComponentEvent in the shipped ABox promotes to exactly the
targets its ``view:promotesTo`` declares -- the ABox is the source of
truth, the test just re-reads it and drives the Listener with each name.

Regression guard for individual events like ``event:TileExpanded``.
"""

from pathlib import Path
from typing import List, Tuple

import pytest
from rdflib import RDF, Graph, URIRef

from ontobdc_web_dock import WebDock
from ontobdc_web_dock.dock.adapter.policy import VIEW, local_name


def _policy_turtle() -> str:
    try:
        from brasidatacenter.resources import ontology_path
    except ImportError:
        return ""
    abox = ontology_path("tool", "ontobdc", "abox", "presentation_event.ttl")
    path = Path(str(abox))
    return path.read_text(encoding="utf-8") if path.is_file() else ""


def _table() -> List[Tuple[str, List[str]]]:
    turtle = _policy_turtle()
    if not turtle:
        return []
    graph = Graph()
    graph.parse(data=turtle, format="turtle")
    rows: List[Tuple[str, List[str]]] = []
    for event in graph.subjects(RDF.type, URIRef(VIEW.ComponentEvent)):
        targets = sorted(
            local_name(target)
            for target in graph.objects(event, URIRef(VIEW.promotesTo))
        )
        rows.append((local_name(event), targets))
    return sorted(rows)


_TABLE = _table()


@pytest.mark.skipif(not _TABLE, reason="presentation_event.ttl not resolvable")
@pytest.mark.parametrize(
    "component_event, expected_targets",
    _TABLE,
    ids=[row[0] for row in _TABLE],
)
def test_component_event_promotes_to_its_declared_targets(
    policy_turtle, component_event: str, expected_targets: List[str]
) -> None:
    answer = WebDock(policy_turtle).promote(component_event)

    assert answer["status"] == (
        "promoted" if expected_targets else "not_promoted"
    )
    assert sorted(t["event"] for t in answer["targets"]) == expected_targets
