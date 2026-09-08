from __future__ import annotations

from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional

from ontobdc.cli.adapter.logger import NullLogRepository
from ontobdc.shared.adapter.statechart import StatechartLocator
from ontobdc.shared.adapter.worker import StateWorkerAdapter
from ontobdc_view import component_event_promoter_source
from ontobdc_view.page.adapter.gantt_script import GanttScriptAdapter
from ontobdc_view.shared.adapter.vendor import VENDOR_SHEET_JS_NAME


class IfcWorkScheduleScriptGenerationProcessState(str, Enum):
    """States of the Gantt Page's split runtime JS generation (see ifc_work_schedule_script_generation.yaml)."""

    UNDEFINED = "__undefined__"
    VENDOR_SHEET_JS_ASSET_GENERATED = "__vendor_sheet_js_asset_generated__"
    I18N_SCRIPT_GENERATED = "__i18n_script_generated__"
    GRAPH_READER_SCRIPT_GENERATED = "__graph_reader_script_generated__"
    CONTAINER_CONNECTION_SCRIPT_GENERATED = "__container_connection_script_generated__"
    CONNECTION_STATE_SCRIPT_GENERATED = "__connection_state_script_generated__"
    CHROME_CONTROLS_SCRIPT_GENERATED = "__chrome_controls_script_generated__"
    EVENT_PROMOTERS_GENERATED = "__event_promoters_generated__"
    PYODIDE_RUNTIME_SCRIPT_GENERATED = "__pyodide_runtime_script_generated__"
    TASK_TABLE_TIMELINE_SCRIPT_GENERATED = "__task_table_timeline_script_generated__"
    DEPENDENCY_ARROWS_SCRIPT_GENERATED = "__dependency_arrows_script_generated__"

    def label(self, lang: str = "en") -> str:
        labels = {
            "en": {
                self.UNDEFINED: "Undefined",
                self.VENDOR_SHEET_JS_ASSET_GENERATED: "Vendor Sheet JS Asset Generated",
                self.I18N_SCRIPT_GENERATED: "I18n Script Generated",
                self.GRAPH_READER_SCRIPT_GENERATED: "Graph Reader Script Generated",
                self.CONTAINER_CONNECTION_SCRIPT_GENERATED: "Container Connection Script Generated",
                self.CONNECTION_STATE_SCRIPT_GENERATED: "Connection State Script Generated",
                self.CHROME_CONTROLS_SCRIPT_GENERATED: "Chrome Controls Script Generated",
                self.EVENT_PROMOTERS_GENERATED: "Event Promoters Generated",
                self.PYODIDE_RUNTIME_SCRIPT_GENERATED: "Pyodide Runtime Script Generated",
                self.TASK_TABLE_TIMELINE_SCRIPT_GENERATED: "Task Table Timeline Script Generated",
                self.DEPENDENCY_ARROWS_SCRIPT_GENERATED: "Dependency Arrows Script Generated",
            },
            "pt-br": {
                self.UNDEFINED: "Indefinida",
                self.VENDOR_SHEET_JS_ASSET_GENERATED: "Asset SheetJS Gerado",
                self.I18N_SCRIPT_GENERATED: "Script de I18n Gerado",
                self.GRAPH_READER_SCRIPT_GENERATED: "Script de Leitura do Grafo Gerado",
                self.CONTAINER_CONNECTION_SCRIPT_GENERATED: "Script de Conexao com o Container Gerado",
                self.CONNECTION_STATE_SCRIPT_GENERATED: "Script de Estado da Conexao Gerado",
                self.CHROME_CONTROLS_SCRIPT_GENERATED: "Script dos Controles de Cabecalho Gerado",
                self.EVENT_PROMOTERS_GENERATED: "Promotores de Evento Gerados",
                self.PYODIDE_RUNTIME_SCRIPT_GENERATED: "Script do Runtime Pyodide Gerado",
                self.TASK_TABLE_TIMELINE_SCRIPT_GENERATED: "Script da Tabela e Timeline de Tarefas Gerado",
                self.DEPENDENCY_ARROWS_SCRIPT_GENERATED: "Script das Setas de Dependencia Gerado",
            },
        }
        return labels.get(lang, labels["en"]).get(self, self.value)

    def description(self, lang: str = "en") -> str:
        descriptions = {
            "en": {
                self.UNDEFINED: "No Gantt runtime script has been written yet.",
                self.VENDOR_SHEET_JS_ASSET_GENERATED: "The vendored SheetJS library used to read/write spreadsheets in the browser has been written.",
                self.I18N_SCRIPT_GENERATED: "i18n_apply.js, which applies translations to the UI, has been written.",
                self.GRAPH_READER_SCRIPT_GENERATED: "graph_reader.js, which reads the schedule's JSON-LD (tasks, IFC types, dates, enriched data), has been written.",
                self.CONTAINER_CONNECTION_SCRIPT_GENERATED: "The connection to the container and location of the schedule's dataset have been written.",
                self.CONNECTION_STATE_SCRIPT_GENERATED: "The connection state logic has been written.",
                self.CHROME_CONTROLS_SCRIPT_GENERATED: "The header controls have been written.",
                self.EVENT_PROMOTERS_GENERATED: "The dDock event-promotion scripts have been written.",
                self.PYODIDE_RUNTIME_SCRIPT_GENERATED: "Pyodide + rdflib/openpyxl, which read the schedule's live workbook and rebuild the data the Gantt uses, have been written.",
                self.TASK_TABLE_TIMELINE_SCRIPT_GENERATED: "The main part of the Gantt -- the WBS/Name/Start/End/Duration/% table and the SVG timeline with bars, milestones and progress -- has been written.",
                self.DEPENDENCY_ARROWS_SCRIPT_GENERATED: "The dependency arrows between tasks, derived from IfcRelSequence, have been written -- must run after the bars, since it depends on their geometry.",
            },
            "pt-br": {
                self.UNDEFINED: "Nenhum script de runtime do Gantt foi escrito ainda.",
                self.VENDOR_SHEET_JS_ASSET_GENERATED: "A biblioteca SheetJS vendorizada, usada para ler/escrever planilhas no navegador, foi escrita.",
                self.I18N_SCRIPT_GENERATED: "O i18n_apply.js, que aplica traducoes a interface, foi escrito.",
                self.GRAPH_READER_SCRIPT_GENERATED: "O graph_reader.js, que le o JSON-LD do cronograma (tarefas, tipos IFC, datas, dados enriquecidos), foi escrito.",
                self.CONTAINER_CONNECTION_SCRIPT_GENERATED: "A conexao com o container e a localizacao do dataset do cronograma foram escritas.",
                self.CONNECTION_STATE_SCRIPT_GENERATED: "A logica de estado da conexao foi escrita.",
                self.CHROME_CONTROLS_SCRIPT_GENERATED: "Os controles do cabecalho foram escritos.",
                self.EVENT_PROMOTERS_GENERATED: "Os scripts de promocao de eventos da dDock foram escritos.",
                self.PYODIDE_RUNTIME_SCRIPT_GENERATED: "Pyodide + rdflib/openpyxl, que leem a planilha viva do cronograma e reconstroem os dados usados pelo Gantt, foram escritos.",
                self.TASK_TABLE_TIMELINE_SCRIPT_GENERATED: "A parte principal do Gantt -- a tabela WBS/Nome/Inicio/Fim/Duracao/% e a timeline SVG com barras, marcos e progresso -- foi escrita.",
                self.DEPENDENCY_ARROWS_SCRIPT_GENERATED: "As setas de dependencia entre tarefas, a partir de IfcRelSequence, foram escritas -- precisa rodar depois das barras, pois depende da geometria delas.",
            },
        }
        return descriptions.get(lang, descriptions["en"]).get(self, "")

    @staticmethod
    def get_state(state: str) -> "IfcWorkScheduleScriptGenerationProcessState":
        return getattr(IfcWorkScheduleScriptGenerationProcessState, state.upper())


_SCRIPT_NAME_BY_STATE: Dict[IfcWorkScheduleScriptGenerationProcessState, str] = {
    IfcWorkScheduleScriptGenerationProcessState.VENDOR_SHEET_JS_ASSET_GENERATED: VENDOR_SHEET_JS_NAME,
    IfcWorkScheduleScriptGenerationProcessState.I18N_SCRIPT_GENERATED: "i18n_apply",
    IfcWorkScheduleScriptGenerationProcessState.GRAPH_READER_SCRIPT_GENERATED: "graph_reader",
    IfcWorkScheduleScriptGenerationProcessState.CONTAINER_CONNECTION_SCRIPT_GENERATED: "container_connection",
    IfcWorkScheduleScriptGenerationProcessState.CONNECTION_STATE_SCRIPT_GENERATED: "connection_state",
    IfcWorkScheduleScriptGenerationProcessState.CHROME_CONTROLS_SCRIPT_GENERATED: "chrome_controls",
    IfcWorkScheduleScriptGenerationProcessState.PYODIDE_RUNTIME_SCRIPT_GENERATED: "pyodide_runtime",
    IfcWorkScheduleScriptGenerationProcessState.TASK_TABLE_TIMELINE_SCRIPT_GENERATED: "task_table_timeline",
    IfcWorkScheduleScriptGenerationProcessState.DEPENDENCY_ARROWS_SCRIPT_GENERATED: "dependency_arrows",
}

_ASSET_DIRECTORY_NAME = "ifc_work_schedule_view"
_EVENT_PROMOTER_SCRIPT_NAME = "component_event_promoter"


class IfcWorkScheduleScriptGenerationTransitionHandler:
    """Drives the Gantt Page's runtime-script generation through its statechart.

    Not `CapabilityLoader`/`CliContextPort`-based like `SurfaceGeneration
    StateTransitionHandler`: each state just writes one already-built script
    (`GanttScriptAdapter.script_source(name)`, or
    `component_event_promoter_source()` for the one state that isn't one of
    `GanttScriptAdapter`'s own scripts) to
    `.__ontobdc__/asset/ifc_work_schedule_view/<name>.js`.
    """

    def __init__(self, *, container_path: Path) -> None:
        self._container_path = container_path
        self._adapter = GanttScriptAdapter()
        self._written_paths: List[str] = []
        self._active_state: Optional[IfcWorkScheduleScriptGenerationProcessState] = None
        self._last_transition_state: Optional[IfcWorkScheduleScriptGenerationProcessState] = None

    @property
    def written_paths(self) -> List[str]:
        return self._written_paths

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
        if to_state is IfcWorkScheduleScriptGenerationProcessState.EVENT_PROMOTERS_GENERATED:
            script_name = _EVENT_PROMOTER_SCRIPT_NAME
            content = component_event_promoter_source()
        else:
            script_name = _SCRIPT_NAME_BY_STATE[to_state]
            content = self._adapter.script_source(script_name)

        target_path = (
            self._container_path
            / ".__ontobdc__"
            / "asset"
            / _ASSET_DIRECTORY_NAME
            / f"{script_name}.js"
        )
        target_path.parent.mkdir(parents=True, exist_ok=True)
        target_path.write_text(content, encoding="utf-8")
        self._written_paths.append(str(target_path))
        self._last_transition_state = to_state

    def validate_state_transition(
        self,
        from_state: IfcWorkScheduleScriptGenerationProcessState,
        to_state: IfcWorkScheduleScriptGenerationProcessState,
    ) -> bool:
        if from_state == to_state:
            return False
        return self._last_transition_state == to_state


def generate_ifc_work_schedule_scripts(container_path: Path) -> List[str]:
    """Run the Gantt script-generation statechart to completion, returning every written path."""
    handler = IfcWorkScheduleScriptGenerationTransitionHandler(container_path=container_path)
    worker = StateWorkerAdapter(
        state_adapter=IfcWorkScheduleScriptGenerationProcessState,
        state_context_name="IfcWorkScheduleScriptGenerationProcessState",
        handler=handler,
        logger=NullLogRepository(),
        statechart_file_path=StatechartLocator.locate(
            __file__, "ifc_work_schedule_script_generation.yaml"
        ),
    )
    worker.work()
    return handler.written_paths
