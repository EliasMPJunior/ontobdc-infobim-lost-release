"""The event-promotion statechart, run as one linear pass.

``ontobdc``'s ``StateWorkerAdapter`` drives its statecharts through
``sismic`` off a YAML file. That whole stack (sismic + the ontobdc
distribution) is not available in Pyodide, so this pass is the same
statechart expressed directly: the enum in
``domain.machine.promotion_state`` is the state set, and this adapter is
the ``adapter/machine`` that walks it, appending each state reached to a
trace exactly as the cumulative-state convention prescribes.

Every transition is unconditional except the one out of
``SEMANTIC_EVENT_RESOLVED``: a name that is not a ``view:ComponentEvent``
in the policy graph ends the pass there.
"""

from typing import Dict, List, Optional, Tuple

from rdflib import URIRef

from ontobdc_web_dock.dock.adapter.policy import PromotionPolicy
from ontobdc_web_dock.dock.domain.machine.promotion_state import (
    EventPromotionProcessState as _STATE,
)


class EventPromotionMachine:
    """Runs one promotion pass against an indexed policy."""

    def __init__(self, policy: PromotionPolicy) -> None:
        self._policy = policy

    def run(
        self, occurrence_name: str
    ) -> Tuple[
        Optional[URIRef],
        Tuple[URIRef, ...],
        List[_STATE],
    ]:
        """Return ``(component_event_iri, targets, trace)``.

        ``component_event_iri`` is ``None`` when the occurrence name is not
        a Component Event in the policy; ``targets`` is then empty.
        """
        trace: List[_STATE] = [_STATE.EVENT_RECEIVED]

        name = str(occurrence_name or "").strip()
        component_event = self._policy.resolve_component_event(name)
        trace.append(_STATE.SEMANTIC_EVENT_RESOLVED)

        if component_event is None:
            trace.append(_STATE.RESPONSE_PRODUCED)
            return None, (), trace

        targets = self._policy.promotion_targets(component_event)
        trace.append(_STATE.PROMOTION_POLICY_EVALUATED)
        trace.append(_STATE.PROMOTION_TARGETS_RESOLVED)
        trace.append(_STATE.RESPONSE_PRODUCED)
        return component_event, targets, trace

    @staticmethod
    def trace_state(trace: List[_STATE]) -> str:
        return trace[-1].value if trace else _STATE.UNDEFINED.value

    @staticmethod
    def trace_names(trace: List[_STATE]) -> List[str]:
        return _STATE.trace_names(trace)
