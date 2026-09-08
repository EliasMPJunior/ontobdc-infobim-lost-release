from __future__ import annotations

from enum import Enum
from typing import Any, Callable, Dict, List, Optional

from ontobdc.cli.adapter.logger import NullLogRepository
from ontobdc.cli.domain.port.context import CliContextPort
from ontobdc.shared.adapter.statechart import StatechartLocator
from ontobdc.shared.adapter.worker import StateWorkerAdapter
from ontobdc_view.page.adapter.facade import FacadeLookupAdapter
from ontobdc_view.page.adapter.generation_data import (
    EntityPageGenerationDataTransitionHandler,
)


class WorkStreamPageDataProcessState(str, Enum):
    """States of the WorkStream element Page-data build (see work_stream_page_data.yaml)."""

    UNDEFINED = "__undefined__"
    FACADES_LOCATED = "__facades_located__"
    FACADE_DATA_GATHERED = "__facade_data_gathered__"
    MISSING_DATA_FILLED = "__missing_data_filled__"
    RELATED_ENTITIES_RESOLVED = "__related_entities_resolved__"

    def label(self, lang: str = "en") -> str:
        labels = {
            "en": {
                self.UNDEFINED: "Undefined",
                self.FACADES_LOCATED: "Facades Located",
                self.FACADE_DATA_GATHERED: "Facade Data Gathered",
                self.MISSING_DATA_FILLED: "Missing Data Filled",
                self.RELATED_ENTITIES_RESOLVED: "Related Entities Resolved",
            },
            "pt-br": {
                self.UNDEFINED: "Indefinida",
                self.FACADES_LOCATED: "Facades Localizadas",
                self.FACADE_DATA_GATHERED: "Dados da Facade Reunidos",
                self.MISSING_DATA_FILLED: "Dados Faltantes Preenchidos",
                self.RELATED_ENTITIES_RESOLVED: "Entidades Relacionadas Resolvidas",
            },
        }
        return labels.get(lang, labels["en"]).get(self, self.value)

    def description(self, lang: str = "en") -> str:
        descriptions = {
            "en": {
                self.UNDEFINED: "No Page-data has been built yet for this element.",
                self.FACADES_LOCATED: "Every Facade declared for the WorkStream entity type has been located.",
                self.FACADE_DATA_GATHERED: "Facade field values already present on the DATA_GATHERED element node have been collected.",
                self.MISSING_DATA_FILLED: "Facade fields absent from DATA_GATHERED have been filled from another source.",
                self.RELATED_ENTITIES_RESOLVED: "Entities related to this WorkStream have been resolved.",
            },
            "pt-br": {
                self.UNDEFINED: "Nenhum dado de Page foi construido ainda para este elemento.",
                self.FACADES_LOCATED: "Toda Facade declarada para o tipo de entidade WorkStream foi localizada.",
                self.FACADE_DATA_GATHERED: "Os valores de campo de Facade ja presentes no no do elemento em DATA_GATHERED foram coletados.",
                self.MISSING_DATA_FILLED: "Os campos de Facade ausentes em DATA_GATHERED foram preenchidos a partir de outra fonte.",
                self.RELATED_ENTITIES_RESOLVED: "As entidades relacionadas a este WorkStream foram resolvidas.",
            },
        }
        return descriptions.get(lang, descriptions["en"]).get(self, "")

    @staticmethod
    def get_state(state: str) -> "WorkStreamPageDataProcessState":
        return getattr(WorkStreamPageDataProcessState, state.upper())


class WorkStreamPageDataTransitionHandler:
    """Drives one WorkStream element's Page-data build through its statechart.

    Not `CapabilityLoader`/`CliContextPort`-based like `SurfaceGeneration
    StateTransitionHandler`: the unit of work here is a single element
    (one of possibly many built concurrently in a thread pool), not the
    whole container, so each state dispatches directly to a bound step
    method that mutates `self.payload` instead of resolving a registered
    Capability.
    """

    def __init__(
        self,
        *,
        context: CliContextPort,
        element_uri: str,
        entity_uri: str,
        source_node: Dict[str, Any],
    ) -> None:
        self._context = context
        self._element_uri = element_uri
        self._entity_uri = entity_uri
        self._source_node = source_node
        self._payload: Dict[str, Any] = {}
        self._active_state: Optional[WorkStreamPageDataProcessState] = None
        self._last_transition_state: Optional[WorkStreamPageDataProcessState] = None
        self._steps: Dict[WorkStreamPageDataProcessState, Callable[[], None]] = {
            WorkStreamPageDataProcessState.FACADES_LOCATED: self._locate_facades,
            WorkStreamPageDataProcessState.FACADE_DATA_GATHERED: self._gather_facade_data,
            WorkStreamPageDataProcessState.MISSING_DATA_FILLED: self._fill_missing_data,
            WorkStreamPageDataProcessState.RELATED_ENTITIES_RESOLVED: self._resolve_related_entities,
        }

    @property
    def payload(self) -> Dict[str, Any]:
        return self._payload

    @property
    def current_state(self) -> WorkStreamPageDataProcessState:
        return self._active_state or WorkStreamPageDataProcessState.UNDEFINED

    @property
    def state_sequence(self) -> List[WorkStreamPageDataProcessState]:
        return list(WorkStreamPageDataProcessState)

    def bind_active_state(self, state: WorkStreamPageDataProcessState) -> None:
        self._active_state = state

    def can_transit_to(self, to_state: WorkStreamPageDataProcessState) -> bool:
        sequence = self.state_sequence
        current = self.current_state
        if current not in sequence or to_state not in sequence:
            return False
        current_index = sequence.index(current)
        return current_index + 1 < len(sequence) and sequence[current_index + 1] == to_state

    def perform_state_transition(self, to_state: WorkStreamPageDataProcessState) -> None:
        self._steps[to_state]()
        self._last_transition_state = to_state

    def validate_state_transition(
        self,
        from_state: WorkStreamPageDataProcessState,
        to_state: WorkStreamPageDataProcessState,
    ) -> bool:
        if from_state == to_state:
            return False
        return self._last_transition_state == to_state

    def _locate_facades(self) -> None:
        self._payload["facades"] = FacadeLookupAdapter.locate_facades_for_element(
            self._context, self._element_uri, self._entity_uri
        )

    def _gather_facade_data(self) -> None:
        fields: Dict[str, str] = {}
        missing_fields: List[str] = []
        for facade in self._payload.get("facades", []):
            for field in facade.get("fields", []):
                name = str(field["name"])
                value = self._literal(str(field["mapped_property"]))
                if value is not None:
                    fields[name] = value
                else:
                    missing_fields.append(name)
        self._payload["fields"] = fields
        self._payload["missing_fields"] = missing_fields

    def _fill_missing_data(self) -> None:
        """Not yet implemented -- a no-op until a data source is decided."""

    def _resolve_related_entities(self) -> None:
        """Not yet implemented -- a no-op until the relation rules are decided."""
        self._payload.setdefault("related_entities", [])

    def _literal(self, property_uri: str) -> Optional[str]:
        values = self._source_node.get(property_uri)
        if not isinstance(values, list) or not values:
            return None
        picked = values[0]
        if isinstance(picked, dict):
            value = picked.get("@value")
            if value is None:
                value = picked.get("@id")
            return str(value).strip() if value is not None else None
        return str(picked).strip()


class WorkStreamPageGenerationDataTransitionHandler(
    EntityPageGenerationDataTransitionHandler
):
    """Builds a WorkStream element's Page-data payload by running its statechart."""

    def build_payload(
        self,
        *,
        context: CliContextPort,
        element_uri: str,
        entity_uri: str,
        source_node: Dict[str, Any],
    ) -> Any:
        handler = WorkStreamPageDataTransitionHandler(
            context=context,
            element_uri=element_uri,
            entity_uri=entity_uri,
            source_node=source_node,
        )
        worker = StateWorkerAdapter(
            state_adapter=WorkStreamPageDataProcessState,
            state_context_name="WorkStreamPageDataProcessState",
            handler=handler,
            logger=NullLogRepository(),
            statechart_file_path=StatechartLocator.locate(
                __file__, "work_stream_page_data.yaml"
            ),
        )
        worker.work()
        return handler.payload
