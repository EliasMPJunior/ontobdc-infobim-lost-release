"""Reads the promotion policy out of RDF and indexes it once.

The policy is Brasidata/brasidatacenter's
``ontology/tool/ontobdc/abox/presentation_event.ttl``. This adapter parses
that Turtle document with rdflib and builds an in-memory index of
``view:promotesTo``, so a Tile interaction costs a dictionary lookup
rather than a re-parse or a SPARQL evaluation per event.

``view:promotesTo`` is a **multivalued** relation: one Component Event
may promote to zero, one or many Shared Events. Every read here goes
through ``Graph.objects(...)``, which yields all objects. An API that
collapses a predicate to a single object -- ``Graph.value(...)`` and
anything equivalent -- would silently drop the second target of
``TileOpened`` and is never used.
"""

from typing import Dict, List, Optional, Tuple

from rdflib import Graph, Namespace, URIRef
from rdflib.namespace import RDF

VIEW = Namespace("http://datacenter.app.br/ontology/ontobdc/domain/view.ttl#")
EVENT = Namespace(
    "http://datacenter.app.br/ontology/ontobdc/abox/presentation_event.ttl#"
)

PROMOTES_TO = VIEW.promotesTo
COMPONENT_EVENT = VIEW.ComponentEvent
SHARED_EVENT = VIEW.SharedEvent


class PromotionPolicyError(Exception):
    """The policy document could not be read as RDF."""


def local_name(iri: URIRef) -> str:
    """The event name a browser Component/Shared Event carries.

    The event individuals are minted in the ``presentation_event.ttl#``
    namespace, so the name is whatever follows it. Falls back to the last
    ``#`` / ``/`` segment for an individual minted elsewhere.
    """
    text = str(iri)
    if text.startswith(str(EVENT)):
        return text[len(str(EVENT)):]
    for separator in ("#", "/"):
        if separator in text:
            return text.rsplit(separator, 1)[-1]
    return text


class PromotionPolicy:
    """An indexed, read-only view of the presentation promotion policy.

    Build it once per runtime (the dDock keeps a single instance for the
    life of the page) and answer every interaction from the index.
    """

    def __init__(self, graph: Graph) -> None:
        self._graph = graph
        self._component_events: Dict[str, URIRef] = {}
        self._shared_events: Dict[str, URIRef] = {}
        self._promotions: Dict[URIRef, Tuple[URIRef, ...]] = {}
        self._index()

    # ---- construction --------------------------------------------------

    @classmethod
    def from_turtle(cls, turtle: str) -> "PromotionPolicy":
        """Parse a Turtle policy document -- the form the browser bridge
        hands to the runtime, since Pyodide has no access to the
        brasidatacenter package the document is published in."""
        graph = Graph()
        try:
            graph.parse(data=turtle, format="turtle")
        except Exception as error:  # rdflib raises a family of parse errors
            raise PromotionPolicyError(
                f"presentation event policy is not readable as Turtle: {error}"
            ) from error
        return cls(graph)

    def _index(self) -> None:
        for subject in self._graph.subjects(RDF.type, COMPONENT_EVENT):
            if not isinstance(subject, URIRef):
                continue
            self._component_events[local_name(subject)] = subject
            targets = sorted(
                (
                    target
                    for target in self._graph.objects(subject, PROMOTES_TO)
                    if isinstance(target, URIRef)
                ),
                key=str,
            )
            self._promotions[subject] = tuple(targets)

        for subject in self._graph.subjects(RDF.type, SHARED_EVENT):
            if isinstance(subject, URIRef):
                self._shared_events[local_name(subject)] = subject

    # ---- queries -----------------------------------------------------

    @property
    def graph(self) -> Graph:
        return self._graph

    def component_event_names(self) -> List[str]:
        return sorted(self._component_events)

    def shared_event_names(self) -> List[str]:
        return sorted(self._shared_events)

    def resolve_component_event(self, name: str) -> Optional[URIRef]:
        """The ``view:ComponentEvent`` individual an occurrence name
        denotes, or ``None`` when the name is not a Component Event in this
        policy."""
        return self._component_events.get(str(name or "").strip())

    def promotion_targets(
        self, component_event: URIRef
    ) -> Tuple[URIRef, ...]:
        """Every ``view:promotesTo`` object of ``component_event``.

        Returns an empty tuple when the Component Event declares no
        promotion -- a normal, non-error outcome.
        """
        return self._promotions.get(component_event, ())

    def is_shared_event(self, iri: URIRef) -> bool:
        return iri in set(self._shared_events.values())
