from __future__ import annotations

from enum import Enum
from typing import Dict, List, Optional, Type

from ontobdc.cli.adapter.logger import NullLogRepository
from ontobdc.cli.domain.port.context import CliContextPort
from ontobdc.shared.adapter.capability import CapabilityExecutor
from ontobdc.shared.adapter.loader import CapabilityLoader
from ontobdc.shared.adapter.statechart import StatechartLocator
from ontobdc.shared.adapter.worker import StateWorkerAdapter
from ontobdc.shared.domain.port.capability import CapabilityPort
from ontobdc_view.page.adapter.context import PageScriptGenerationContextAdapter


class IfcWorkScheduleScriptGenerationProcessState(str, Enum):
    """States that publish the restored IfcWorkSchedule Gantt runtime."""

    UNDEFINED = "__undefined__"
    VENDOR_SHEET_JS_ASSET_GENERATED = "__vendor_sheet_js_asset_generated__"
    I18N_SCRIPT_GENERATED = "__i18n_script_generated__"
    GRAPH_READER_SCRIPT_GENERATED = "__graph_reader_script_generated__"
    CONTAINER_CONNECTION_SCRIPT_GENERATED = "__container_connection_script_generated__"
    CONNECTION_STATE_SCRIPT_GENERATED = "__connection_state_script_generated__"
    CHROME_CONTROLS_SCRIPT_GENERATED = "__chrome_controls_script_generated__"
    PYODIDE_RUNTIME_SCRIPT_GENERATED = "__pyodide_runtime_script_generated__"
    TASK_TABLE_TIMELINE_SCRIPT_GENERATED = "__task_table_timeline_script_generated__"
    DEPENDENCY_ARROWS_SCRIPT_GENERATED = "__dependency_arrows_script_generated__"
    GANTT_TAB_MOUNT_SCRIPT_GENERATED = "__gantt_tab_mount_script_generated__"

    def label(self, lang: str = "en") -> str:
        labels = {
            self.UNDEFINED: "Undefined",
            self.VENDOR_SHEET_JS_ASSET_GENERATED: "Vendor Sheet JS Asset Generated",
            self.I18N_SCRIPT_GENERATED: "I18n Script Generated",
            self.GRAPH_READER_SCRIPT_GENERATED: "Graph Reader Script Generated",
            self.CONTAINER_CONNECTION_SCRIPT_GENERATED: "Container Connection Script Generated",
            self.CONNECTION_STATE_SCRIPT_GENERATED: "Connection State Script Generated",
            self.CHROME_CONTROLS_SCRIPT_GENERATED: "Chrome Controls Script Generated",
            self.PYODIDE_RUNTIME_SCRIPT_GENERATED: "Pyodide Runtime Script Generated",
            self.TASK_TABLE_TIMELINE_SCRIPT_GENERATED: "Task Table Timeline Script Generated",
            self.DEPENDENCY_ARROWS_SCRIPT_GENERATED: "Dependency Arrows Script Generated",
            self.GANTT_TAB_MOUNT_SCRIPT_GENERATED: "Gantt Tab Mount Script Generated",
        }
        return labels.get(self, self.value)

    def description(self, lang: str = "en") -> str:
        if self is self.UNDEFINED:
            return "No IfcWorkSchedule Gantt runtime asset has been written yet."
        return f"Publish the {self.label(lang)} asset for the IfcWorkSchedule Entity Page."

    @staticmethod
    def get_state(state: str) -> "IfcWorkScheduleScriptGenerationProcessState":
        return getattr(IfcWorkScheduleScriptGenerationProcessState, state.upper())


_CAPABILITY_ID_BY_STATE: Dict[IfcWorkScheduleScriptGenerationProcessState, str] = {
    state: (
        "org.ontobdc.view.plugin.capability.transformation.target."
        f"ifc_work_schedule_{state.value.strip('_')}"
    )
    for state in IfcWorkScheduleScriptGenerationProcessState
    if state != IfcWorkScheduleScriptGenerationProcessState.UNDEFINED
}


class IfcWorkScheduleScriptGenerationTransitionHandler:
    """Drive the Gantt runtime publication statechart."""

    def __init__(
        self,
        *,
        context: CliContextPort,
        capability_loader: Optional[CapabilityLoader] = None,
    ) -> None:
        self._context = PageScriptGenerationContextAdapter(
            context,
            builder_package=__package__,
            view_directory=__package__.rsplit(".", 1)[-1],
        )
        self._capability_loader = capability_loader or CapabilityLoader(
            root_packages=("ontobdc_view",)
        )
        self._written_paths: List[str] = []
        self._active_state: Optional[IfcWorkScheduleScriptGenerationProcessState] = None
        self._last_transition_state: Optional[IfcWorkScheduleScriptGenerationProcessState] = None

    @property
    def written_paths(self) -> List[str]:
        return list(self._written_paths)

    @property
    def current_state(self) -> IfcWorkScheduleScriptGenerationProcessState:
        return self._active_state or IfcWorkScheduleScriptGenerationProcessState.UNDEFINED

    @property
    def state_sequence(self) -> List[IfcWorkScheduleScriptGenerationProcessState]:
        return list(IfcWorkScheduleScriptGenerationProcessState)

    def bind_active_state(self, state: IfcWorkScheduleScriptGenerationProcessState) -> None:
        self._active_state = state

    def can_transit_to(self, to_state: IfcWorkScheduleScriptGenerationProcessState) -> bool:
        sequence = self.state_sequence
        current = self.current_state
        if current not in sequence or to_state not in sequence:
            return False
        current_index = sequence.index(current)
        return current_index + 1 < len(sequence) and sequence[current_index + 1] == to_state

    def perform_state_transition(self, to_state: IfcWorkScheduleScriptGenerationProcessState) -> None:
        capability_type = self._capability_type_for_state(to_state)
        result = CapabilityExecutor.execute(capability_type(), self._context)
        generated_path = str(result.get("generated_script_path") or "").strip()
        if not generated_path:
            raise ValueError(f"{capability_type.__name__} returned no generated script path.")
        self._written_paths.append(generated_path)
        self._last_transition_state = to_state

    def validate_state_transition(
        self,
        from_state: IfcWorkScheduleScriptGenerationProcessState,
        to_state: IfcWorkScheduleScriptGenerationProcessState,
    ) -> bool:
        return from_state != to_state and self._last_transition_state == to_state

    def _capability_type_for_state(
        self,
        state: IfcWorkScheduleScriptGenerationProcessState,
    ) -> Type[CapabilityPort]:
        capability_id = _CAPABILITY_ID_BY_STATE.get(state)
        if capability_id is None:
            raise ValueError(f"No capability is mapped to IfcWorkSchedule script state: {state}")
        capability_type = self._capability_loader.get(capability_id)
        if capability_type is None:
            raise ValueError(f"IfcWorkSchedule script-generation capability not found: {capability_id}")
        return capability_type


def generate_ifc_work_schedule_scripts(context: CliContextPort) -> List[str]:
    handler = IfcWorkScheduleScriptGenerationTransitionHandler(context=context)
    worker = StateWorkerAdapter(
        state_adapter=IfcWorkScheduleScriptGenerationProcessState,
        state_context_name="IfcWorkScheduleScriptGenerationProcessState",
        handler=handler,
        logger=NullLogRepository(),
        statechart_file_path=StatechartLocator.locate(
            __file__,
            "ifc_work_schedule_script_generation.yaml",
            statechart_package="ontobdc_view.page.plugin.builder.ifc_work_schedule",
        ),
    )
    worker.work()
    return handler.written_paths
