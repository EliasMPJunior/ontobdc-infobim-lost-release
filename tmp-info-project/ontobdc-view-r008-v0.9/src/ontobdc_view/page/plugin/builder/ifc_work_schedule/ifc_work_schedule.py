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


class IfcWorkSchedulePageDataProcessState(str, Enum):
    """States of the IfcWorkSchedule element Page-data build (see ifc_work_schedule_page_data.yaml)."""

    UNDEFINED = "__undefined__"
    FACADES_LOCATED = "__facades_located__"
    FACADE_DATA_GATHERED = "__facade_data_gathered__"
    GANTT_PAYLOAD_GATHERED = "__gantt_payload_gathered__"
    MISSING_DATA_FILLED = "__missing_data_filled__"
    DIMENSION_TABS_GENERATED = "__dimension_tabs_generated__"
    RELATED_ENTITIES_RESOLVED = "__related_entities_resolved__"
    TOOLBAR_CONFIGURATION_GATHERED = "__toolbar_configuration_gathered__"

    def label(self, lang: str = "en") -> str:
        labels = {
            "en": {
                self.UNDEFINED: "Undefined",
                self.FACADES_LOCATED: "Facades Located",
                self.FACADE_DATA_GATHERED: "Facade Data Gathered",
                self.GANTT_PAYLOAD_GATHERED: "Gantt Payload Gathered",
                self.MISSING_DATA_FILLED: "Missing Data Filled",
                self.DIMENSION_TABS_GENERATED: "Dimension Tabs Generated",
                self.RELATED_ENTITIES_RESOLVED: "Related Entities Resolved",
                self.TOOLBAR_CONFIGURATION_GATHERED: (
                    "Toolbar Configuration Gathered"
                ),
            },
            "pt-br": {
                self.UNDEFINED: "Indefinida",
                self.FACADES_LOCATED: "Facades Localizadas",
                self.FACADE_DATA_GATHERED: "Dados da Facade Reunidos",
                self.GANTT_PAYLOAD_GATHERED: "Payload do Gantt Reunido",
                self.MISSING_DATA_FILLED: "Dados Faltantes Preenchidos",
                self.DIMENSION_TABS_GENERATED: "Abas de Dimensao Geradas",
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
                self.FACADES_LOCATED: "Every Facade declared for the IfcWorkSchedule entity type has been located.",
                self.FACADE_DATA_GATHERED: "Facade field values already present on the DATA_GATHERED element node have been collected.",
                self.GANTT_PAYLOAD_GATHERED: "The runtime context required by the restored IfcWorkSchedule Gantt has been assembled.",
                self.MISSING_DATA_FILLED: "Facade fields absent from DATA_GATHERED have been filled from another source.",
                self.DIMENSION_TABS_GENERATED: "Populated IfcWorkSchedule fields have been grouped by semantic dimension into tabs for the single schedule card.",
                self.RELATED_ENTITIES_RESOLVED: "Entities related to this IfcWorkSchedule have been resolved.",
                self.TOOLBAR_CONFIGURATION_GATHERED: (
                    "The toolbar declared for this IfcWorkSchedule Entity "
                    "Page has been written to the Page-data JSON-LD."
                ),
            },
            "pt-br": {
                self.UNDEFINED: "Nenhum dado de Page foi construido ainda para este elemento.",
                self.FACADES_LOCATED: "Toda Facade declarada para o tipo de entidade IfcWorkSchedule foi localizada.",
                self.FACADE_DATA_GATHERED: "Os valores de campo de Facade ja presentes no no do elemento em DATA_GATHERED foram coletados.",
                self.GANTT_PAYLOAD_GATHERED: "O contexto de runtime necessario para o Gantt restaurado do IfcWorkSchedule foi montado.",
                self.MISSING_DATA_FILLED: "Os campos de Facade ausentes em DATA_GATHERED foram preenchidos a partir de outra fonte.",
                self.DIMENSION_TABS_GENERATED: "Os campos preenchidos do IfcWorkSchedule foram agrupados por dimensao semantica em abas do unico card do cronograma.",
                self.RELATED_ENTITIES_RESOLVED: "As entidades relacionadas a este IfcWorkSchedule foram resolvidas.",
                self.TOOLBAR_CONFIGURATION_GATHERED: (
                    "A toolbar declarada para esta Entity Page de "
                    "IfcWorkSchedule foi gravada no JSON-LD de dados da Page."
                ),
            },
        }
        return descriptions.get(lang, descriptions["en"]).get(self, "")

    @staticmethod
    def get_state(state: str) -> "IfcWorkSchedulePageDataProcessState":
        return getattr(IfcWorkSchedulePageDataProcessState, state.upper())


_CAPABILITY_ID_BY_STATE: Dict[IfcWorkSchedulePageDataProcessState, str] = {
    state: (
        "org.ontobdc.view.plugin.capability.transformation.target."
        f"{state.value.strip('_')}"
    )
    for state in IfcWorkSchedulePageDataProcessState
    if state != IfcWorkSchedulePageDataProcessState.UNDEFINED
}
_CAPABILITY_ID_BY_STATE[
    IfcWorkSchedulePageDataProcessState.GANTT_PAYLOAD_GATHERED
] = (
    "org.ontobdc.view.plugin.capability.transformation.target."
    "ifc_work_schedule_gantt_payload_gathered"
)
_CAPABILITY_ID_BY_STATE[
    IfcWorkSchedulePageDataProcessState.DIMENSION_TABS_GENERATED
] = (
    "org.ontobdc.view.plugin.capability.transformation.target."
    "ifc_work_schedule_dimension_tabs_generated"
)


class IfcWorkSchedulePageDataTransitionHandler:
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
        self._payload: Dict[str, Any] = {}
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
        self._active_state: Optional[IfcWorkSchedulePageDataProcessState] = None
        self._last_transition_state: Optional[IfcWorkSchedulePageDataProcessState] = None

    @property
    def payload(self) -> Dict[str, Any]:
        return self._payload

    @property
    def current_state(self) -> IfcWorkSchedulePageDataProcessState:
        return self._active_state or IfcWorkSchedulePageDataProcessState.UNDEFINED

    @property
    def state_sequence(self) -> List[IfcWorkSchedulePageDataProcessState]:
        return list(IfcWorkSchedulePageDataProcessState)

    def bind_active_state(self, state: IfcWorkSchedulePageDataProcessState) -> None:
        self._active_state = state

    def can_transit_to(self, to_state: IfcWorkSchedulePageDataProcessState) -> bool:
        sequence = self.state_sequence
        current = self.current_state
        if current not in sequence or to_state not in sequence:
            return False
        current_index = sequence.index(current)
        return current_index + 1 < len(sequence) and sequence[current_index + 1] == to_state

    def perform_state_transition(self, to_state: IfcWorkSchedulePageDataProcessState) -> None:
        capability_type = self._capability_type_for_state(to_state)
        capability = capability_type()
        CapabilityExecutor.execute(capability, self._context)
        self._last_transition_state = to_state

    def validate_state_transition(
        self,
        from_state: IfcWorkSchedulePageDataProcessState,
        to_state: IfcWorkSchedulePageDataProcessState,
    ) -> bool:
        if from_state == to_state:
            return False
        return self._last_transition_state == to_state

    def _capability_type_for_state(
        self,
        state: IfcWorkSchedulePageDataProcessState,
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


class IfcWorkSchedulePageGenerationDataTransitionHandler(
    EntityPageGenerationDataTransitionHandler
):
    """Builds an IfcWorkSchedule element's Page-data payload by running its statechart."""

    def build_payload(
        self,
        *,
        context: CliContextPort,
        element_uri: str,
        entity_uri: str,
        source_node: Dict[str, Any],
    ) -> Any:
        handler = IfcWorkSchedulePageDataTransitionHandler(
            context=context,
            element_uri=element_uri,
            entity_uri=entity_uri,
            source_node=source_node,
        )
        worker = StateWorkerAdapter(
            state_adapter=IfcWorkSchedulePageDataProcessState,
            state_context_name="IfcWorkSchedulePageDataProcessState",
            handler=handler,
            logger=NullLogRepository(),
            statechart_file_path=StatechartLocator.locate(
                __file__,
                "ifc_work_schedule_page_data.yaml",
                statechart_package=(
                    "ontobdc_view.page.plugin.builder.ifc_work_schedule"
                ),
            ),
        )
        worker.work()
        return handler.payload
