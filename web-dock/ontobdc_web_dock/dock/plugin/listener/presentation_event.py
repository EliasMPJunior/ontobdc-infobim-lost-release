"""The Listener that answers presentation Component Events.

The single authority over Component -> Shared promotion in the whole
presentation stack. Nothing in JavaScript decides, mirrors or
short-circuits what this class returns.

It runs the promotion statechart (see
``ontobdc_web_dock.dock.adapter.machine``) end to end:

    EVENT_RECEIVED
        -> SEMANTIC_EVENT_RESOLVED
            -> PROMOTION_POLICY_EVALUATED
                -> PROMOTION_TARGETS_RESOLVED
                    -> RESPONSE_PRODUCED

and its answer is always a list, because ``view:promotesTo`` is
multivalued: ``[]``, ``[target]`` and ``[target1, target2, ...]`` are all
ordinary results.
"""

from typing import Any, Dict

from ontobdc_web_dock.dock.adapter.machine import EventPromotionMachine
from ontobdc_web_dock.dock.adapter.policy import PromotionPolicy, local_name
from ontobdc_web_dock.dock.domain.port.listener import (
    ListenerMetadata,
    ListenerPort,
)


class PresentationEventPromotionListener(ListenerPort):
    METADATA = ListenerMetadata(
        id=(
            "org.ontobdc.web_dock.dock.plugin.listener."
            "presentation_event_promotion"
        ),
        version="1.0.0",
        name="Presentation Event Promotion Listener",
        description=(
            "Resolves a presentation Component Event against the "
            "view:promotesTo policy published in "
            "ontology/tool/ontobdc/abox/presentation_event.ttl and answers "
            "with every Shared Event it promotes to."
        ),
        author=["http://kb.elias.eng.br/nid/elias.ttl#Elias"],
        tags=["view", "dock", "event", "promotion", "listener"],
        supported_languages=["en", "pt-br"],
        input_schema={
            "type": "object",
            "required": ["event"],
            "properties": {
                "event": {
                    "type": "string",
                    "description": (
                        "Local name of the Component Event that occurred."
                    ),
                },
                "detail": {
                    "type": "object",
                    "description": (
                        "Occurrence payload carried through unchanged."
                    ),
                },
            },
        },
        output_schema={
            "type": "object",
            "properties": {
                "status": {
                    "enum": ["promoted", "not_promoted", "unresolved"]
                },
                "componentEvent": {"type": "string"},
                "componentEventIri": {"type": "string"},
                "targets": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "event": {"type": "string"},
                            "iri": {"type": "string"},
                        },
                    },
                },
                "trace": {"type": "array", "items": {"type": "string"}},
            },
        },
        log_message={
            "info": {
                "en": (
                    "Component Event {event} promoted to {count} Shared "
                    "Event(s)."
                ),
                "pt-br": (
                    "Component Event {event} promovido para {count} Shared "
                    "Event(s)."
                ),
            },
            "debug_entry": {
                "en": (
                    "Evaluating view:promotesTo for Component Event {event}."
                ),
                "pt-br": (
                    "Avaliando view:promotesTo para o Component Event "
                    "{event}."
                ),
            },
        },
    )

    def __init__(self, policy: PromotionPolicy) -> None:
        self._policy = policy
        self._machine = EventPromotionMachine(policy)

    def listens_to(self) -> str:
        return "ComponentEvent"

    @property
    def policy(self) -> PromotionPolicy:
        return self._policy

    def handle(self, envelope: Dict[str, Any]) -> Dict[str, Any]:
        name = str((envelope or {}).get("event") or "").strip()
        component_event, targets, trace = self._machine.run(name)

        if component_event is None:
            status = "unresolved"
        elif targets:
            status = "promoted"
        else:
            status = "not_promoted"

        return {
            "status": status,
            "componentEvent": name,
            "componentEventIri": (
                str(component_event) if component_event else ""
            ),
            "targets": [
                {"event": local_name(target), "iri": str(target)}
                for target in targets
            ],
            "trace": EventPromotionMachine.trace_names(trace),
            "state": EventPromotionMachine.trace_state(trace),
        }
