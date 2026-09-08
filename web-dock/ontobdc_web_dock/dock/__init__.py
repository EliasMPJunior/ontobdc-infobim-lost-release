"""dDock presentation-event runtime -- the Python authority over promotion.

Two hard constraints shape every module here:

1. **Pyodide-only dependencies.** Nothing but the standard library and
   ``rdflib``. No ``ontobdc``, no ``sismic``, no ``pydantic`` -- the
   bridge ships these modules as source text and executes them in
   Pyodide.
2. **No promotion policy in code.** The policy lives in
   brasidatacenter's ``ontology/tool/ontobdc/abox/presentation_event.ttl``
   and is read as RDF through ``view:promotesTo``. Nothing here
   enumerates, mirrors or special-cases a Component -> Shared mapping.
"""

from ontobdc_web_dock.dock.adapter.listener import PresentationEventDock
from ontobdc_web_dock.dock.adapter.policy import PromotionPolicy
from ontobdc_web_dock.dock.domain.machine.promotion_state import (
    EventPromotionProcessState,
)
from ontobdc_web_dock.dock.domain.port.listener import (
    ListenerMetadata,
    ListenerPort,
)

__all__ = [
    "EventPromotionProcessState",
    "ListenerMetadata",
    "ListenerPort",
    "PresentationEventDock",
    "PromotionPolicy",
]
