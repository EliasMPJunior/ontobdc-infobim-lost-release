"""Statechart states for processing one Global Event.

Same cumulative-state convention as the other OntoBDC process statecharts
(`SurfaceGenerationProcessState`, `WorkStreamScriptGenerationProcessState`):
a `str` enum whose members are the states reached, in order, each with a
`label()`/`description()`.

A plain `enum.Enum` rather than a sismic statechart, because this one runs
inside Pyodide when a Page calls the listener, and sismic is not part of the
browser runtime.

The order is the guarantee, not decoration:

    EVENT_RECEIVED
        -> (persist the event under `.__ontobdc__/event/`)
    EVENT_STORED
        -> (append its JSON-LD to the Surface journal)
    SURFACE_JOURNAL_UPDATED
        -> COMPLETED

A state is entered only once its transition's action has completed
successfully, so the state a run ends in says exactly how far it got — and,
on a failure, exactly what is already on disk. `EVENT_STORED` before
`SURFACE_JOURNAL_UPDATED` in particular is what makes a failed journal
append recoverable: the event that provoked it is already persisted, and
re-running the listener with the same `eventId` converges.

New states go in the table in `global_event_listener.py` without the rest of
the flow changing: `VALIDATED` before `EVENT_STORED`, `COMPACTED` after
`SURFACE_JOURNAL_UPDATED`.
"""

from enum import Enum
from typing import List


class GlobalEventProcessState(str, Enum):
    UNDEFINED = "__undefined__"
    EVENT_RECEIVED = "__event_received__"
    EVENT_STORED = "__event_stored__"
    SURFACE_JOURNAL_UPDATED = "__surface_journal_updated__"
    COMPLETED = "__completed__"

    def label(self, lang: str = "en") -> str:
        labels = {
            "en": {
                self.UNDEFINED: "Undefined",
                self.EVENT_RECEIVED: "Global Event Received",
                self.EVENT_STORED: "Global Event Stored",
                self.SURFACE_JOURNAL_UPDATED: "Surface Journal Updated",
                self.COMPLETED: "Completed",
            },
            "pt-br": {
                self.UNDEFINED: "Indefinido",
                self.EVENT_RECEIVED: "Global Event Recebido",
                self.EVENT_STORED: "Global Event Persistido",
                self.SURFACE_JOURNAL_UPDATED: "Journal da Superficie Atualizado",
                self.COMPLETED: "Concluido",
            },
        }
        return labels.get(lang, labels["en"]).get(self, self.value)

    def description(self, lang: str = "en") -> str:
        descriptions = {
            "en": {
                self.UNDEFINED: "No Global Event is being processed.",
                self.EVENT_RECEIVED: (
                    "A Page handed the listener a Global Event envelope, after its own "
                    "write to the data source completed."
                ),
                self.EVENT_STORED: (
                    "The event is persisted under the dataset's .__ontobdc__/event/ as a "
                    "record of its own. Nothing touches index.html before this."
                ),
                self.SURFACE_JOURNAL_UPDATED: (
                    "The event's JSON-LD was appended to the Surface document's journal "
                    "and a sequence was assigned to it."
                ),
                self.COMPLETED: (
                    "Both the dataset record and the Surface journal carry the event; the "
                    "sequence is what the Page is told."
                ),
            },
            "pt-br": {
                self.UNDEFINED: "Nenhum Global Event esta sendo processado.",
                self.EVENT_RECEIVED: (
                    "Uma Page entregou ao listener um envelope de Global Event, depois de "
                    "concluir sua propria gravacao na fonte de dados."
                ),
                self.EVENT_STORED: (
                    "O evento esta persistido em .__ontobdc__/event/ do dataset como "
                    "registro proprio. Nada toca o index.html antes disso."
                ),
                self.SURFACE_JOURNAL_UPDATED: (
                    "O JSON-LD do evento foi acrescentado ao journal do documento da "
                    "Superficie e recebeu uma sequence."
                ),
                self.COMPLETED: (
                    "O registro no dataset e o journal da Superficie carregam o evento; a "
                    "sequence e o que a Page recebe."
                ),
            },
        }
        return descriptions.get(lang, descriptions["en"]).get(self, "")

    @staticmethod
    def get_state(state: str) -> "GlobalEventProcessState":
        return getattr(GlobalEventProcessState, state.upper())

    @staticmethod
    def trace_names(trace: List["GlobalEventProcessState"]) -> List[str]:
        return [state.name for state in trace]
