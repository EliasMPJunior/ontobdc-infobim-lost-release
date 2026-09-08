from __future__ import annotations

from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional

from ontobdc.cli.adapter.logger import NullLogRepository
from ontobdc.shared.adapter.statechart import StatechartLocator
from ontobdc.shared.adapter.worker import StateWorkerAdapter
from ontobdc_view import component_event_promoter_source
from ontobdc_view.page.adapter.work_stream_script import WorkStreamScriptAdapter
from ontobdc_view.shared.adapter.vendor import VENDOR_SHEET_JS_NAME


class WorkStreamScriptGenerationProcessState(str, Enum):
    """States of the WorkStream Page's split runtime JS generation (see work_stream_script_generation.yaml)."""

    UNDEFINED = "__undefined__"
    VENDOR_SHEET_JS_ASSET_GENERATED = "__vendor_sheet_js_asset_generated__"
    I18N_SCRIPT_GENERATED = "__i18n_script_generated__"
    GRAPH_READER_SCRIPT_GENERATED = "__graph_reader_script_generated__"
    CSV_PREVIEW_SCRIPT_GENERATED = "__csv_preview_script_generated__"
    CONTAINER_CONNECTION_SCRIPT_GENERATED = "__container_connection_script_generated__"
    CONNECTION_STATE_SCRIPT_GENERATED = "__connection_state_script_generated__"
    CHROME_CONTROLS_SCRIPT_GENERATED = "__chrome_controls_script_generated__"
    EVENT_PROMOTERS_GENERATED = "__event_promoters_generated__"
    ANNOTATION_BRIDGE_SCRIPT_GENERATED = "__annotation_bridge_script_generated__"
    PYODIDE_RUNTIME_SCRIPT_GENERATED = "__pyodide_runtime_script_generated__"
    LINKSET_OPERATIONS_SCRIPT_GENERATED = "__linkset_operations_script_generated__"
    FILE_CATEGORY_SCRIPT_GENERATED = "__file_category_script_generated__"
    DIMENSION_CARD_SCRIPT_GENERATED = "__dimension_card_script_generated__"

    def label(self, lang: str = "en") -> str:
        labels = {
            "en": {
                self.UNDEFINED: "Undefined",
                self.VENDOR_SHEET_JS_ASSET_GENERATED: "Vendor Sheet JS Asset Generated",
                self.I18N_SCRIPT_GENERATED: "I18n Script Generated",
                self.GRAPH_READER_SCRIPT_GENERATED: "Graph Reader Script Generated",
                self.CSV_PREVIEW_SCRIPT_GENERATED: "CSV Preview Script Generated",
                self.CONTAINER_CONNECTION_SCRIPT_GENERATED: "Container Connection Script Generated",
                self.CONNECTION_STATE_SCRIPT_GENERATED: "Connection State Script Generated",
                self.CHROME_CONTROLS_SCRIPT_GENERATED: "Chrome Controls Script Generated",
                self.EVENT_PROMOTERS_GENERATED: "Event Promoters Generated",
                self.ANNOTATION_BRIDGE_SCRIPT_GENERATED: "Annotation Bridge Script Generated",
                self.PYODIDE_RUNTIME_SCRIPT_GENERATED: "Pyodide Runtime Script Generated",
                self.LINKSET_OPERATIONS_SCRIPT_GENERATED: "Linkset Operations Script Generated",
                self.FILE_CATEGORY_SCRIPT_GENERATED: "File Category Script Generated",
                self.DIMENSION_CARD_SCRIPT_GENERATED: "Dimension Card Script Generated",
            },
            "pt-br": {
                self.UNDEFINED: "Indefinida",
                self.VENDOR_SHEET_JS_ASSET_GENERATED: "Asset SheetJS Gerado",
                self.I18N_SCRIPT_GENERATED: "Script de I18n Gerado",
                self.GRAPH_READER_SCRIPT_GENERATED: "Script de Leitura do Grafo Gerado",
                self.CSV_PREVIEW_SCRIPT_GENERATED: "Script de Preview de CSV Gerado",
                self.CONTAINER_CONNECTION_SCRIPT_GENERATED: "Script de Conexao com o Container Gerado",
                self.CONNECTION_STATE_SCRIPT_GENERATED: "Script de Estado da Conexao Gerado",
                self.CHROME_CONTROLS_SCRIPT_GENERATED: "Script dos Controles de Cabecalho Gerado",
                self.EVENT_PROMOTERS_GENERATED: "Promotores de Evento Gerados",
                self.ANNOTATION_BRIDGE_SCRIPT_GENERATED: "Script da Ponte de Anotacoes Gerado",
                self.PYODIDE_RUNTIME_SCRIPT_GENERATED: "Script do Runtime Pyodide Gerado",
                self.LINKSET_OPERATIONS_SCRIPT_GENERATED: "Script de Operacoes de Linkset Gerado",
                self.FILE_CATEGORY_SCRIPT_GENERATED: "Script de Categoria de Arquivo Gerado",
                self.DIMENSION_CARD_SCRIPT_GENERATED: "Script dos Cards de Dimensao Gerado",
            },
        }
        return labels.get(lang, labels["en"]).get(self, self.value)

    def description(self, lang: str = "en") -> str:
        descriptions = {
            "en": {
                self.UNDEFINED: "No WorkStream runtime script has been written yet.",
                self.VENDOR_SHEET_JS_ASSET_GENERATED: "The vendored SheetJS library used to read/write spreadsheets in the browser has been written.",
                self.I18N_SCRIPT_GENERATED: "i18n_apply.js, which applies translations to the Page's text, titles and aria-labels, has been written.",
                self.GRAPH_READER_SCRIPT_GENERATED: "graph_reader.js, which reads the embedded JSON-LD and exposes helpers for types, literals, resources, labels and MIME kinds, has been written.",
                self.CSV_PREVIEW_SCRIPT_GENERATED: "The CSV preview runtime, implemented directly in JS without depending on Pyodide, has been written.",
                self.CONTAINER_CONNECTION_SCRIPT_GENERATED: "The connection code for the container/dataset folder via the File System Access API + IndexedDB has been written.",
                self.CONNECTION_STATE_SCRIPT_GENERATED: "The visual/functional logic for the connection state (connected, error, silent reconnection) has been written.",
                self.CHROME_CONTROLS_SCRIPT_GENERATED: "The header controls (connect, refresh, workspace, subjects, status, i18n helpers) have been written.",
                self.EVENT_PROMOTERS_GENERATED: "The dDock event-promotion scripts, chiefly the Component Event -> Shared Event path, have been written.",
                self.ANNOTATION_BRIDGE_SCRIPT_GENERATED: "The bridge between the Page and the OntoBDC annotation runtime has been written.",
                self.PYODIDE_RUNTIME_SCRIPT_GENERATED: "The Pyodide bootstrap and the Python used to interpret/manipulate the spreadsheet have been written.",
                self.LINKSET_OPERATIONS_SCRIPT_GENERATED: "The ICDD linkset operations (relate, unrelate, suggest relations) have been written.",
                self.FILE_CATEGORY_SCRIPT_GENERATED: "The classification of resources/files by presentation category has been written.",
                self.DIMENSION_CARD_SCRIPT_GENERATED: "The 5W2H cards and the Page's main render() have been written.",
            },
            "pt-br": {
                self.UNDEFINED: "Nenhum script de runtime do WorkStream foi escrito ainda.",
                self.VENDOR_SHEET_JS_ASSET_GENERATED: "A biblioteca SheetJS vendorizada, usada para ler/escrever planilhas no navegador, foi escrita.",
                self.I18N_SCRIPT_GENERATED: "O i18n_apply.js, que aplica traducoes aos textos, titulos e aria-labels da Page, foi escrito.",
                self.GRAPH_READER_SCRIPT_GENERATED: "O graph_reader.js, que le o JSON-LD embutido e expoe helpers para tipos, literais, recursos, labels e MIME, foi escrito.",
                self.CSV_PREVIEW_SCRIPT_GENERATED: "O runtime de preview de CSV, implementado diretamente em JS sem depender de Pyodide, foi escrito.",
                self.CONTAINER_CONNECTION_SCRIPT_GENERATED: "O codigo de conexao com a pasta/container via File System Access API + IndexedDB foi escrito.",
                self.CONNECTION_STATE_SCRIPT_GENERATED: "A logica visual/funcional do estado da conexao (conectado, erro, reconexao silenciosa) foi escrita.",
                self.CHROME_CONTROLS_SCRIPT_GENERATED: "Os controles do cabecalho (conectar, atualizar, workspace, subjects, status, helpers de i18n) foram escritos.",
                self.EVENT_PROMOTERS_GENERATED: "Os scripts de promocao de eventos da dDock, principalmente o caminho Component Event -> Shared Event, foram escritos.",
                self.ANNOTATION_BRIDGE_SCRIPT_GENERATED: "A ponte entre a Page e o runtime de anotacoes do OntoBDC foi escrita.",
                self.PYODIDE_RUNTIME_SCRIPT_GENERATED: "O bootstrap do Pyodide e o Python usado para interpretar/manipular a planilha foram escritos.",
                self.LINKSET_OPERATIONS_SCRIPT_GENERATED: "As operacoes de linkset ICDD (relacionar, desrelacionar, sugerir relacoes) foram escritas.",
                self.FILE_CATEGORY_SCRIPT_GENERATED: "A classificacao dos recursos/arquivos por categoria de apresentacao foi escrita.",
                self.DIMENSION_CARD_SCRIPT_GENERATED: "Os cards 5W2H e o render() principal da Page foram escritos.",
            },
        }
        return descriptions.get(lang, descriptions["en"]).get(self, "")

    @staticmethod
    def get_state(state: str) -> "WorkStreamScriptGenerationProcessState":
        return getattr(WorkStreamScriptGenerationProcessState, state.upper())


_SCRIPT_NAME_BY_STATE: Dict[WorkStreamScriptGenerationProcessState, str] = {
    WorkStreamScriptGenerationProcessState.VENDOR_SHEET_JS_ASSET_GENERATED: VENDOR_SHEET_JS_NAME,
    WorkStreamScriptGenerationProcessState.I18N_SCRIPT_GENERATED: "i18n_apply",
    WorkStreamScriptGenerationProcessState.GRAPH_READER_SCRIPT_GENERATED: "graph_reader",
    WorkStreamScriptGenerationProcessState.CSV_PREVIEW_SCRIPT_GENERATED: "csv_preview",
    WorkStreamScriptGenerationProcessState.CONTAINER_CONNECTION_SCRIPT_GENERATED: "container_connection",
    WorkStreamScriptGenerationProcessState.CONNECTION_STATE_SCRIPT_GENERATED: "connection_state",
    WorkStreamScriptGenerationProcessState.CHROME_CONTROLS_SCRIPT_GENERATED: "chrome_controls",
    WorkStreamScriptGenerationProcessState.ANNOTATION_BRIDGE_SCRIPT_GENERATED: "annotation_bridge",
    WorkStreamScriptGenerationProcessState.PYODIDE_RUNTIME_SCRIPT_GENERATED: "pyodide_runtime",
    WorkStreamScriptGenerationProcessState.LINKSET_OPERATIONS_SCRIPT_GENERATED: "linkset_operations",
    WorkStreamScriptGenerationProcessState.FILE_CATEGORY_SCRIPT_GENERATED: "file_category",
    WorkStreamScriptGenerationProcessState.DIMENSION_CARD_SCRIPT_GENERATED: "dimension_card",
}

_ASSET_DIRECTORY_NAME = "work_stream_view"
_EVENT_PROMOTER_SCRIPT_NAME = "component_event_promoter"


class WorkStreamScriptGenerationTransitionHandler:
    """Drives the WorkStream Page's runtime-script generation through its statechart.

    Not `CapabilityLoader`/`CliContextPort`-based like `SurfaceGeneration
    StateTransitionHandler`: each state just writes one already-built script
    (`WorkStreamScriptAdapter.script_source(name)`, or
    `component_event_promoter_source()` for the one state that isn't one of
    `WorkStreamScriptAdapter`'s own scripts) to
    `.__ontobdc__/asset/work_stream_view/<name>.js`.
    """

    def __init__(self, *, container_path: Path) -> None:
        self._container_path = container_path
        self._adapter = WorkStreamScriptAdapter()
        self._written_paths: List[str] = []
        self._active_state: Optional[WorkStreamScriptGenerationProcessState] = None
        self._last_transition_state: Optional[WorkStreamScriptGenerationProcessState] = None

    @property
    def written_paths(self) -> List[str]:
        return self._written_paths

    @property
    def current_state(self) -> WorkStreamScriptGenerationProcessState:
        return self._active_state or WorkStreamScriptGenerationProcessState.UNDEFINED

    @property
    def state_sequence(self) -> List[WorkStreamScriptGenerationProcessState]:
        return list(WorkStreamScriptGenerationProcessState)

    def bind_active_state(self, state: WorkStreamScriptGenerationProcessState) -> None:
        self._active_state = state

    def can_transit_to(self, to_state: WorkStreamScriptGenerationProcessState) -> bool:
        sequence = self.state_sequence
        current = self.current_state
        if current not in sequence or to_state not in sequence:
            return False
        current_index = sequence.index(current)
        return current_index + 1 < len(sequence) and sequence[current_index + 1] == to_state

    def perform_state_transition(self, to_state: WorkStreamScriptGenerationProcessState) -> None:
        if to_state is WorkStreamScriptGenerationProcessState.EVENT_PROMOTERS_GENERATED:
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
        from_state: WorkStreamScriptGenerationProcessState,
        to_state: WorkStreamScriptGenerationProcessState,
    ) -> bool:
        if from_state == to_state:
            return False
        return self._last_transition_state == to_state


def generate_work_stream_scripts(container_path: Path) -> List[str]:
    """Run the WorkStream script-generation statechart to completion, returning every written path."""
    handler = WorkStreamScriptGenerationTransitionHandler(container_path=container_path)
    worker = StateWorkerAdapter(
        state_adapter=WorkStreamScriptGenerationProcessState,
        state_context_name="WorkStreamScriptGenerationProcessState",
        handler=handler,
        logger=NullLogRepository(),
        statechart_file_path=StatechartLocator.locate(
            __file__, "work_stream_script_generation.yaml"
        ),
    )
    worker.work()
    return handler.written_paths
