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
from ontobdc_view.page.adapter.context import (
    PageScriptGenerationContextAdapter,
)


class WorkStreamScriptGenerationProcessState(str, Enum):
    """States of the WorkStream Page script generation."""

    UNDEFINED = "__undefined__"
    VENDOR_SHEET_JS_ASSET_GENERATED = (
        "__vendor_sheet_js_asset_generated__"
    )
    I18N_SCRIPT_GENERATED = "__i18n_script_generated__"
    GRAPH_READER_SCRIPT_GENERATED = "__graph_reader_script_generated__"

    def label(self, lang: str = "en") -> str:
        labels = {
            "en": {
                self.UNDEFINED: "Undefined",
                self.VENDOR_SHEET_JS_ASSET_GENERATED: (
                    "Vendor Sheet JS Asset Generated"
                ),
                self.I18N_SCRIPT_GENERATED: "I18n Script Generated",
                self.GRAPH_READER_SCRIPT_GENERATED: (
                    "Graph Reader Script Generated"
                ),
            },
            "pt-br": {
                self.UNDEFINED: "Indefinida",
                self.VENDOR_SHEET_JS_ASSET_GENERATED: "Asset SheetJS Gerado",
                self.I18N_SCRIPT_GENERATED: "Script de I18n Gerado",
                self.GRAPH_READER_SCRIPT_GENERATED: (
                    "Script de Leitura do Grafo Gerado"
                ),
            },
        }
        return labels.get(lang, labels["en"]).get(self, self.value)

    def description(self, lang: str = "en") -> str:
        descriptions = {
            "en": {
                self.UNDEFINED: "No Page runtime script has been written yet.",
                self.VENDOR_SHEET_JS_ASSET_GENERATED: (
                    "The vendored SheetJS library has been written to the "
                    "WorkStream view."
                ),
                self.I18N_SCRIPT_GENERATED: (
                    "The WorkStream UI translation script has been "
                    "written."
                ),
                self.GRAPH_READER_SCRIPT_GENERATED: (
                    "The script that reads the WorkStream JSON-LD has "
                    "been generated."
                ),
            },
            "pt-br": {
                self.UNDEFINED: (
                    "Nenhum script de runtime da Page foi escrito ainda."
                ),
                self.VENDOR_SHEET_JS_ASSET_GENERATED: (
                    "A biblioteca SheetJS vendorizada foi escrita na view "
                    "WorkStream."
                ),
                self.I18N_SCRIPT_GENERATED: (
                    "O script de traducao da UI do WorkStream foi escrito."
                ),
                self.GRAPH_READER_SCRIPT_GENERATED: (
                    "O script que le o JSON-LD do WorkStream foi gerado."
                ),
            },
        }
        return descriptions.get(lang, descriptions["en"]).get(self, "")

    @staticmethod
    def get_state(state: str) -> "WorkStreamScriptGenerationProcessState":
        return getattr(
            WorkStreamScriptGenerationProcessState,
            state.upper(),
        )


_CAPABILITY_ID_BY_STATE: Dict[
    WorkStreamScriptGenerationProcessState, str
] = {
    WorkStreamScriptGenerationProcessState.VENDOR_SHEET_JS_ASSET_GENERATED: (
        "org.ontobdc.view.plugin.capability.transformation.target."
        "vendor_sheet_js_asset_generated"
    ),
    WorkStreamScriptGenerationProcessState.I18N_SCRIPT_GENERATED: (
        "org.ontobdc.view.plugin.capability.transformation.target."
        "i18n_script_generated"
    ),
    WorkStreamScriptGenerationProcessState.GRAPH_READER_SCRIPT_GENERATED: (
        "org.ontobdc.view.plugin.capability.transformation.target."
        "graph_reader_script_generated"
    ),
}


class WorkStreamScriptGenerationTransitionHandler:
    """Drive the Sismic statechart through script-generation capabilities."""

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
        self._active_state: Optional[
            WorkStreamScriptGenerationProcessState
        ] = None
        self._last_transition_state: Optional[
            WorkStreamScriptGenerationProcessState
        ] = None

    @property
    def written_paths(self) -> List[str]:
        return list(self._written_paths)

    @property
    def current_state(self) -> WorkStreamScriptGenerationProcessState:
        return self._active_state or (
            WorkStreamScriptGenerationProcessState.UNDEFINED
        )

    @property
    def state_sequence(self) -> List[WorkStreamScriptGenerationProcessState]:
        return list(WorkStreamScriptGenerationProcessState)

    def bind_active_state(
        self,
        state: WorkStreamScriptGenerationProcessState,
    ) -> None:
        self._active_state = state

    def can_transit_to(
        self,
        to_state: WorkStreamScriptGenerationProcessState,
    ) -> bool:
        sequence = self.state_sequence
        current = self.current_state
        if current not in sequence or to_state not in sequence:
            return False
        current_index = sequence.index(current)
        return (
            current_index + 1 < len(sequence)
            and sequence[current_index + 1] == to_state
        )

    def perform_state_transition(
        self,
        to_state: WorkStreamScriptGenerationProcessState,
    ) -> None:
        capability_type = self._capability_type_for_state(to_state)
        result = CapabilityExecutor.execute(capability_type(), self._context)
        generated_path = str(result.get("generated_script_path") or "").strip()
        if generated_path:
            self._written_paths.append(generated_path)
        elif (
            to_state
            != WorkStreamScriptGenerationProcessState.GRAPH_READER_SCRIPT_GENERATED
        ):
            raise ValueError(
                f"{capability_type.__name__} returned no generated script path."
            )
        self._last_transition_state = to_state

    def validate_state_transition(
        self,
        from_state: WorkStreamScriptGenerationProcessState,
        to_state: WorkStreamScriptGenerationProcessState,
    ) -> bool:
        if from_state == to_state:
            return False
        return self._last_transition_state == to_state

    def _capability_type_for_state(
        self,
        state: WorkStreamScriptGenerationProcessState,
    ) -> Type[CapabilityPort]:
        capability_id = _CAPABILITY_ID_BY_STATE.get(state)
        if capability_id is None:
            raise ValueError(
                "No capability is mapped to WorkStream script state: "
                f"{state}"
            )
        capability_type = self._capability_loader.get(capability_id)
        if capability_type is None:
            raise ValueError(
                "WorkStream script-generation capability not found: "
                f"{capability_id}"
            )
        return capability_type


def generate_work_stream_scripts(context: CliContextPort) -> List[str]:
    handler = WorkStreamScriptGenerationTransitionHandler(context=context)
    worker = StateWorkerAdapter(
        state_adapter=WorkStreamScriptGenerationProcessState,
        state_context_name="WorkStreamScriptGenerationProcessState",
        handler=handler,
        logger=NullLogRepository(),
        statechart_file_path=StatechartLocator.locate(
            __file__,
            "work_stream_script_generation.yaml",
            statechart_package=(
                "ontobdc_view.page.plugin.builder.work_stream"
            ),
        ),
    )
    worker.work()
    return handler.written_paths
