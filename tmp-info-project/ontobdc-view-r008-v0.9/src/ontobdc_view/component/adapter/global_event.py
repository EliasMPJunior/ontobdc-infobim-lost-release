"""Packages the Global Event replay runtime for the browser page.

The runtime applies a persisted journal of Global Events to the Surface's
build-time JSON-LD snapshot before any Tile reads it. Which occurrences it
will accept, and which graph operation each one carries, are not its own
decisions: both come from BrasidataCenter's
`ontology/tool/ontobdc/abox/presentation_event.ttl`, read here at
generation time from the package the ontology lives in — the same source
`dock.presentation_event_policy()` reads the promotion policy from.

That is the point of resolving them here rather than writing them into the
JavaScript: adding a Global Event to the graph is what makes it replayable.
"""

from __future__ import annotations

import json
from importlib.resources import files
from pathlib import Path
from typing import Dict, List

from rdflib import Graph, Namespace
from rdflib.namespace import RDF

VIEW = Namespace("http://datacenter.app.br/ontology/ontobdc/domain/view.ttl#")

_IRIS_PLACEHOLDER = "__ONTOBDC_BUILD_GLOBAL_EVENT_IRIS__"
_OPERATIONS_PLACEHOLDER = "__ONTOBDC_BUILD_GLOBAL_EVENT_OPERATIONS__"

_REPLAY_ASSET = "global_event_replay.js"

# The reducer implements exactly these. An operation named in the graph that
# the runtime cannot apply is a contract break worth failing the build over,
# not something to ship and discover in a browser.
_SUPPORTED_OPERATIONS = frozenset({"set", "unset", "add", "remove"})


def _policy_graph() -> Graph:
    from brasidatacenter.resources import ontology_path

    path = ontology_path("tool", "ontobdc", "abox", "presentation_event.ttl")
    graph = Graph()
    graph.parse(Path(str(path)), format="turtle")
    return graph


def global_event_operations() -> Dict[str, List[str]]:
    """Every `view:GlobalEvent` individual, mapped to the graph operations it
    declares through `view:appliesOperation`.

    Keys are full IRIs — the same string a persisted event carries in its
    `event` field — so nothing downstream has to reconstruct one from a local
    name.
    """
    graph = _policy_graph()
    operations: Dict[str, List[str]] = {}
    for subject in graph.subjects(RDF.type, VIEW.GlobalEvent):
        declared = sorted(str(value) for value in graph.objects(subject, VIEW.appliesOperation))
        unsupported = sorted(set(declared) - _SUPPORTED_OPERATIONS)
        if unsupported:
            raise ValueError(
                f"{subject} declares view:appliesOperation {unsupported}, which the "
                f"Global Event replay reducer does not implement "
                f"(supported: {sorted(_SUPPORTED_OPERATIONS)})"
            )
        operations[str(subject)] = declared
    return operations


def global_event_iri_for_operation(operation: str) -> str:
    """The Global Event IRI that declares `operation`.

    A producer needs to name the event it is emitting, and naming it means
    the IRI, not a local name it built by hand. Resolving it from
    `view:appliesOperation` keeps the ontology the only place that says which
    event carries a `set`.

    Raises when the policy declares no event, or more than one, for the
    operation: either is a contract the producer cannot resolve on its own.
    """
    matches = sorted(
        iri
        for iri, operations in global_event_operations().items()
        if operation in operations
    )
    if not matches:
        raise ValueError(
            f"no view:GlobalEvent declares view:appliesOperation {operation!r}"
        )
    if len(matches) > 1:
        raise ValueError(
            f"view:appliesOperation {operation!r} is declared by more than one "
            f"Global Event ({matches}); a producer cannot choose between them"
        )
    return matches[0]


def global_event_iris() -> List[str]:
    """The IRIs of every declared Global Event, sorted for a stable build."""
    return sorted(global_event_operations())


def global_event_replay_source() -> str:
    """`global_event_replay.js` with its build placeholders resolved.

    This is the module a generated page embeds *before* its component
    modules, so the graph is materialized before `customElements.define`
    upgrades any Tile.
    """
    source = (
        files("ontobdc_view")
        .joinpath("component", "asset", _REPLAY_ASSET)
        .read_text(encoding="utf-8")
    )
    operations = global_event_operations()
    source = source.replace(
        _IRIS_PLACEHOLDER, json.dumps(sorted(operations), ensure_ascii=False)
    )
    source = source.replace(
        _OPERATIONS_PLACEHOLDER, json.dumps(operations, ensure_ascii=False, sort_keys=True)
    )
    if "__ONTOBDC_BUILD_" in source:
        raise ValueError(
            "global_event_replay.js still carries an unresolved build placeholder"
        )
    return source
