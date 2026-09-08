"""Statechart states for one dDock promotion pass.

Mirrors the cumulative-state convention every OntoBDC process statechart
uses (`WorkStreamScriptGenerationProcessState`, ...): a ``str`` enum whose
members are the states reached, in order, with ``label()`` /
``description()``. It is a plain ``enum.Enum`` over ``str`` -- not an
``ontobdc`` port subclass -- because this module runs inside Pyodide,
where ``ontobdc`` is not installed.

The run is linear and cumulative -- the state a pass ends in tells you
how far it got:

    EVENT_RECEIVED
        -> SEMANTIC_EVENT_RESOLVED
            -> PROMOTION_POLICY_EVALUATED
                -> PROMOTION_TARGETS_RESOLVED
                    -> RESPONSE_PRODUCED

``SEMANTIC_EVENT_RESOLVED`` is the branch point: an occurrence name that
is not a ``view:ComponentEvent`` in the policy graph stops there and goes
straight to ``RESPONSE_PRODUCED`` with no targets. A Component Event that
carries no ``view:promotesTo`` still runs the whole chain and produces an
empty target list -- absence of a promotion is a normal outcome, never an
error.
"""

from enum import Enum
from typing import List


class EventPromotionProcessState(str, Enum):
    UNDEFINED = "__undefined__"
    EVENT_RECEIVED = "__event_received__"
    SEMANTIC_EVENT_RESOLVED = "__semantic_event_resolved__"
    PROMOTION_POLICY_EVALUATED = "__promotion_policy_evaluated__"
    PROMOTION_TARGETS_RESOLVED = "__promotion_targets_resolved__"
    RESPONSE_PRODUCED = "__response_produced__"

    def label(self, lang: str = "en") -> str:
        labels = {
            "en": {
                self.UNDEFINED: "Undefined",
                self.EVENT_RECEIVED: "Event Received",
                self.SEMANTIC_EVENT_RESOLVED: "Semantic Event Resolved",
                self.PROMOTION_POLICY_EVALUATED: "Promotion Policy Evaluated",
                self.PROMOTION_TARGETS_RESOLVED: "Promotion Targets Resolved",
                self.RESPONSE_PRODUCED: "Response Produced",
            },
            "pt-br": {
                self.UNDEFINED: "Indefinido",
                self.EVENT_RECEIVED: "Evento Recebido",
                self.SEMANTIC_EVENT_RESOLVED: "Evento Semantico Resolvido",
                self.PROMOTION_POLICY_EVALUATED: "Politica de Promocao Avaliada",
                self.PROMOTION_TARGETS_RESOLVED: "Destinos de Promocao Resolvidos",
                self.RESPONSE_PRODUCED: "Resposta Produzida",
            },
        }
        return labels.get(lang, labels["en"]).get(self, self.value)

    def description(self, lang: str = "en") -> str:
        descriptions = {
            "en": {
                self.UNDEFINED: "No promotion pass has started.",
                self.EVENT_RECEIVED: (
                    "The dDock accepted a Component Event envelope from the "
                    "browser bridge."
                ),
                self.SEMANTIC_EVENT_RESOLVED: (
                    "The envelope's occurrence name was resolved against the "
                    "policy graph to a view:ComponentEvent individual, or "
                    "found not to be one."
                ),
                self.PROMOTION_POLICY_EVALUATED: (
                    "view:promotesTo was read from the policy graph for the "
                    "resolved Component Event."
                ),
                self.PROMOTION_TARGETS_RESOLVED: (
                    "Every promotesTo object was resolved to a Shared Event "
                    "target; zero, one and many targets are all normal "
                    "outcomes."
                ),
                self.RESPONSE_PRODUCED: (
                    "The dDock response carrying the resolved targets was "
                    "handed back to the bridge."
                ),
            },
            "pt-br": {
                self.UNDEFINED: "Nenhuma passagem de promocao foi iniciada.",
                self.EVENT_RECEIVED: (
                    "A dDock aceitou um envelope de Component Event vindo da "
                    "ponte do navegador."
                ),
                self.SEMANTIC_EVENT_RESOLVED: (
                    "O nome da ocorrencia do envelope foi resolvido no grafo "
                    "da politica para um individuo view:ComponentEvent, ou "
                    "identificado como nao sendo um."
                ),
                self.PROMOTION_POLICY_EVALUATED: (
                    "view:promotesTo foi lido no grafo da politica para o "
                    "Component Event resolvido."
                ),
                self.PROMOTION_TARGETS_RESOLVED: (
                    "Todo objeto de promotesTo foi resolvido para um destino "
                    "Shared Event; zero, um e varios destinos sao todos "
                    "resultados normais."
                ),
                self.RESPONSE_PRODUCED: (
                    "A resposta da dDock com os destinos resolvidos foi "
                    "devolvida a ponte."
                ),
            },
        }
        return descriptions.get(lang, descriptions["en"]).get(self, "")

    @staticmethod
    def get_state(state: str) -> "EventPromotionProcessState":
        return getattr(EventPromotionProcessState, state.upper())

    @staticmethod
    def trace_names(
        trace: List["EventPromotionProcessState"],
    ) -> List[str]:
        """The statechart trace as the plain state names the bridge reports."""
        return [state.name for state in trace]
