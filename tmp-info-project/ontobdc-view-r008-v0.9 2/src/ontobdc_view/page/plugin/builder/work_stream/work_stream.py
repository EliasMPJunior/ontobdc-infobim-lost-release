from __future__ import annotations

from enum import Enum
from typing import Any, Dict, List, Optional, Type

from ontobdc.cli.adapter.logger import NullLogRepository
from ontobdc.cli.domain.port.context import CliContextPort
from ontobdc.shared.adapter.capability import CapabilityExecutor
from ontobdc.shared.adapter.loader import CapabilityLoader
from ontobdc.shared.adapter.statechart import StatechartLocator
from ontobdc.shared.adapter.worker import StateWorkerAdapter
from ontobdc.shared.domain.port.capability import CapabilityPort
from ontobdc_view.page.adapter.context import PageDataContextAdapter
from ontobdc_view.surface.plugin.capability.transformation.entity_data_gathered import (
    EntityPageGenerationDataTransitionHandler,
)


class WorkStreamPageDataProcessState(str, Enum):
    """States of the WorkStream element Page-data build (see work_stream_page_data.yaml)."""

    UNDEFINED = "__undefined__"
    FACADES_LOCATED = "__facades_located__"
    FACADE_DATA_GATHERED = "__facade_data_gathered__"
    DIMENSION_CARDS_GENERATED = "__dimension_cards_generated__"
    MISSING_DATA_FILLED = "__missing_data_filled__"
    RELATED_ENTITIES_RESOLVED = "__related_entities_resolved__"
    TOOLBAR_CONFIGURATION_GATHERED = "__toolbar_configuration_gathered__"

    def label(self, lang: str = "en") -> str:
        labels = {
            "en": {
                self.UNDEFINED: "Undefined",
                self.FACADES_LOCATED: "Facades Located",
                self.FACADE_DATA_GATHERED: "Facade Data Gathered",
                self.DIMENSION_CARDS_GENERATED: "Dimension Cards Generated",
                self.MISSING_DATA_FILLED: "Missing Data Filled",
                self.RELATED_ENTITIES_RESOLVED: "Related Entities Resolved",
                self.TOOLBAR_CONFIGURATION_GATHERED: (
                    "Toolbar Configuration Gathered"
                ),
            },
            "pt-br": {
                self.UNDEFINED: "Indefinida",
                self.FACADES_LOCATED: "Facades Localizadas",
                self.FACADE_DATA_GATHERED: "Dados da Facade Reunidos",
                self.DIMENSION_CARDS_GENERATED: "Cards de Dimensao Gerados",
                self.MISSING_DATA_FILLED: "Dados Faltantes Preenchidos",
                self.RELATED_ENTITIES_RESOLVED: "Entidades Relacionadas Resolvidas",
                self.TOOLBAR_CONFIGURATION_GATHERED: (
                    "Configuracao da Toolbar Reunida"
                ),
            },
        }
        return labels.get(lang, labels["en"]).get(self, self.value)

    def description(self, lang: str = "en") -> str:
        descriptions = {
            "en": {
                self.UNDEFINED: "No Page-data has been built yet for this element.",
                self.FACADES_LOCATED: "Every Facade declared for the WorkStream entity type has been located.",
                self.FACADE_DATA_GATHERED: "Facade field values already present on the DATA_GATHERED element node have been collected.",
                self.DIMENSION_CARDS_GENERATED: "The ordered dimension-card model has been assembled from the Facade fields that map to a dimension kind.",
                self.MISSING_DATA_FILLED: "Facade fields absent from DATA_GATHERED have been filled from another source.",
                self.RELATED_ENTITIES_RESOLVED: "Entities related to this WorkStream have been resolved.",
                self.TOOLBAR_CONFIGURATION_GATHERED: (
                    "The toolbar declared for this WorkStream Entity "
                    "Page has been written to the Page-data JSON-LD."
                ),
            },
            "pt-br": {
                self.UNDEFINED: "Nenhum dado de Page foi construido ainda para este elemento.",
                self.FACADES_LOCATED: "Toda Facade declarada para o tipo de entidade WorkStream foi localizada.",
                self.FACADE_DATA_GATHERED: "Os valores de campo de Facade ja presentes no no do elemento em DATA_GATHERED foram coletados.",
                self.DIMENSION_CARDS_GENERATED: "O modelo ordenado de cards de dimensao foi montado a partir dos campos de Facade que mapeiam para um dimension kind.",
                self.MISSING_DATA_FILLED: "Os campos de Facade ausentes em DATA_GATHERED foram preenchidos a partir de outra fonte.",
                self.RELATED_ENTITIES_RESOLVED: "As entidades relacionadas a este WorkStream foram resolvidas.",
                self.TOOLBAR_CONFIGURATION_GATHERED: (
                    "A toolbar declarada para esta Entity Page de "
                    "WorkStream foi gravada no JSON-LD de dados da Page."
                ),
            },
        }
        return descriptions.get(lang, descriptions["en"]).get(self, "")

    @staticmethod
    def get_state(state: str) -> "WorkStreamPageDataProcessState":
        return getattr(WorkStreamPageDataProcessState, state.upper())


_CAPABILITY_ID_BY_STATE: Dict[WorkStreamPageDataProcessState, str] = {
    state: (
        "org.ontobdc.view.plugin.capability.transformation.target."
        f"{state.value.strip('_')}"
    )
    for state in WorkStreamPageDataProcessState
    if state != WorkStreamPageDataProcessState.UNDEFINED
}
_CAPABILITY_ID_BY_STATE[
    WorkStreamPageDataProcessState.RELATED_ENTITIES_RESOLVED
] = (
    "org.ontobdc.view.plugin.capability.transformation.target."
    "work_stream_related_entities_resolved"
)


class WorkStreamPageDataTransitionHandler:
    """Drive one element's Page-data statechart through capabilities."""

    def __init__(
        self,
        *,
        context: CliContextPort,
        element_uri: str,
        entity_uri: str,
        source_node: Dict[str, Any],
        capability_loader: Optional[CapabilityLoader] = None,
    ) -> None:
        # Page-data is an enriched JSON-LD projection of the entity, not a
        # detached view-model.  Keeping the source node here preserves the
        # entity identity, types and properties consumed by the browser-side
        # graph reader; subsequent capabilities add their derived sections.
        self._payload: Dict[str, Any] = dict(source_node)
        self._context = PageDataContextAdapter(
            context,
            element_uri=element_uri,
            entity_uri=entity_uri,
            source_node=source_node,
            payload=self._payload,
        )
        self._capability_loader = capability_loader or CapabilityLoader(
            root_packages=("ontobdc_view",)
        )
        self._active_state: Optional[WorkStreamPageDataProcessState] = None
        self._last_transition_state: Optional[WorkStreamPageDataProcessState] = None

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
        capability_type = self._capability_type_for_state(to_state)
        capability = capability_type()
        CapabilityExecutor.execute(capability, self._context)
        self._last_transition_state = to_state

    def validate_state_transition(
        self,
        from_state: WorkStreamPageDataProcessState,
        to_state: WorkStreamPageDataProcessState,
    ) -> bool:
        if from_state == to_state:
            return False
        return self._last_transition_state == to_state

    def _capability_type_for_state(
        self,
        state: WorkStreamPageDataProcessState,
    ) -> Type[CapabilityPort]:
        capability_id = _CAPABILITY_ID_BY_STATE.get(state)
        if capability_id is None:
            raise ValueError(
                f"No transformation capability is mapped to Page-data state: {state}"
            )
        capability_type = self._capability_loader.get(capability_id)
        if capability_type is None:
            raise ValueError(
                f"Page-data transformation capability not found: {capability_id}"
            )
        return capability_type


class WorkStreamPageGenerationDataTransitionHandler(
    EntityPageGenerationDataTransitionHandler
):
    """Builds an WorkStream element's Page-data payload by running its statechart."""

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
                __file__,
                "work_stream_page_data.yaml",
                statechart_package=(
                    "ontobdc_view.page.plugin.builder.work_stream"
                ),
            ),
        )
        worker.work()
        return handler.payload
