from pathlib import Path
from typing import Any, List, Optional, Type

from ontobdc.cli.domain.port.context import CliContextPort
from ontobdc.cli.domain.response.command import (
    CommandResponse,
    ExceptionCommandResponse,
)
from ontobdc.shared.adapter.capability import CapabilityExecutor
from ontobdc.shared.adapter.loader import CapabilityLoader
from ontobdc.shared.adapter.statechart import StatechartLocator
from ontobdc.shared.adapter.worker import StateWorkerAdapter
from ontobdc.shared.domain.port.capability import CapabilityPort
from ontobdc.shared.facade.adapter.logger import NullLogRepository
from ontobdc.shared.facade.port.logger import LogRepositoryPort
from ontobdc.storage.adapter.container_name import ContainerNameAdapter
from ontobdc.storage.domain.machine.rename_state import (
    ContainerRenameProcessState,
)
from ontobdc.storage.domain.port.rename_machine import (
    ContainerRenameProcessStatePort,
    ContainerRenameStateEvaluatorPort,
    ContainerRenameStateTransitionHandlerPort,
)
from ontobdc.storage.plugin.check.is_container_storage_index_ready.check import (
    main as check_container_storage_index_ready,
)


class ContainerRenameStateEvaluatorAdapter(ContainerRenameStateEvaluatorPort):
    @property
    def process_state_class(self) -> Type[ContainerRenameProcessStatePort]:
        return ContainerRenameProcessState

    def evaluate(
        self,
        context: CliContextPort,
    ) -> ContainerRenameProcessStatePort:
        adapter: ContainerNameAdapter = ContainerNameAdapter.from_context(
            context
        )
        if not adapter.is_valid():
            return ContainerRenameProcessState.CONTAINER_INVALID

        requested_name: str = str(
            context.get_parameter_value("container_rename_to")
        ).strip()
        if adapter.metadata_title() != requested_name:
            return ContainerRenameProcessState.UNDEFINED

        if not adapter.storage_index_matches_metadata():
            return ContainerRenameProcessState.CONTAINER_METADATA_RENAMED

        if check_container_storage_index_ready(
            container_path=str(adapter.container_path),
            root_path=str(context.root_path),
        ) != 0:
            return ContainerRenameProcessState.CONTAINER_STORAGE_INDEX_RENAMED

        return ContainerRenameProcessState.CONTAINER_STORAGE_INDEX_READY


class ContainerRenameStateTransitionHandler(
    ContainerRenameStateTransitionHandlerPort
):
    def __init__(
        self,
        context: CliContextPort,
        logger: Optional[LogRepositoryPort] = None,
    ) -> None:
        self._context: CliContextPort = context
        self._target_path: Path = Path(
            str(self._context.get_parameter_value("container_path"))
        ).expanduser().resolve()
        self._logger: LogRepositoryPort = logger or NullLogRepository()
        self._state_evaluator: ContainerRenameStateEvaluatorPort = (
            ContainerRenameStateEvaluatorAdapter()
        )
        self._active_state: Optional[ContainerRenameProcessStatePort] = None

    @property
    def context(self) -> CliContextPort:
        return self._context

    @property
    def target_path(self) -> Path:
        return self._target_path

    @property
    def current_state(self) -> ContainerRenameProcessStatePort:
        if self._active_state is not None:
            return self._active_state
        return self.observed_state

    @property
    def observed_state(self) -> ContainerRenameProcessStatePort:
        return self._state_evaluator.evaluate(self._context)

    @property
    def state_sequence(self) -> List[ContainerRenameProcessStatePort]:
        return list(ContainerRenameProcessState)

    def can_transit_to(
        self,
        to_state: ContainerRenameProcessStatePort,
    ) -> bool:
        active_state: ContainerRenameProcessStatePort = self.current_state
        observed_state: ContainerRenameProcessStatePort = self.observed_state

        if active_state == ContainerRenameProcessState.UNDEFINED:
            if observed_state == ContainerRenameProcessState.CONTAINER_INVALID:
                return (
                    to_state
                    == ContainerRenameProcessState.CONTAINER_INVALID
                )
            return (
                to_state
                == ContainerRenameProcessState.CONTAINER_METADATA_RENAMED
            )

        if (
            active_state
            == ContainerRenameProcessState.CONTAINER_METADATA_RENAMED
        ):
            return (
                to_state
                == ContainerRenameProcessState.CONTAINER_STORAGE_INDEX_RENAMED
            )

        if (
            active_state
            == ContainerRenameProcessState.CONTAINER_STORAGE_INDEX_RENAMED
        ):
            return (
                to_state
                == ContainerRenameProcessState.CONTAINER_STORAGE_INDEX_READY
            )

        if (
            active_state
            == ContainerRenameProcessState.CONTAINER_STORAGE_INDEX_READY
        ):
            return to_state == ContainerRenameProcessState.CONTAINER_RENAMED

        return False

    def perform_state_transition(
        self,
        to_state: ContainerRenameProcessStatePort,
    ) -> None:
        observed_state: ContainerRenameProcessStatePort = self.observed_state
        if self._state_reaches(observed_state, to_state):
            return

        capability_id: str = (
            "org.ontobdc.storage.plugin.capability.transformation.target."
            f"{to_state.value.strip('_')}"
        )
        capability_type: Any = CapabilityLoader().get(capability_id)
        if capability_type is None:
            raise ValueError(
                f"Storage container rename capability not found: {capability_id}"
            )

        capability: CapabilityPort = capability_type()
        CapabilityExecutor.execute(capability, self._context)

    def validate_state_transition(
        self,
        from_state: ContainerRenameProcessStatePort,
        to_state: ContainerRenameProcessStatePort,
    ) -> bool:
        if from_state == to_state:
            return False
        return self._state_reaches(self.observed_state, to_state)

    def bind_active_state(
        self,
        state: ContainerRenameProcessStatePort,
    ) -> None:
        self._active_state = state

    def execute(self) -> CommandResponse:
        worker: StateWorkerAdapter = StateWorkerAdapter(
            state_adapter=ContainerRenameProcessState,
            state_context_name="ContainerRenameProcessStatePort",
            handler=self,
            logger=self._logger,
            statechart_file_path=self._get_statechart_file_path(),
        )
        visited_states: List[str] = worker.work()
        return self._build_final_response(visited_states)

    def _build_final_response(
        self,
        visited_states: List[str],
    ) -> CommandResponse:
        if self.current_state == ContainerRenameProcessState.CONTAINER_INVALID:
            return ExceptionCommandResponse(
                title="Invalid Storage Container",
                description=(
                    "The registered container metadata cannot be resolved "
                    "unambiguously for rename."
                ),
                content={
                    "container_id": str(
                        self._context.get_parameter_value("container_id")
                    ),
                    "path": str(self._target_path),
                    "visited_states": visited_states,
                },
            )

        return CommandResponse(
            title="Storage Container Renamed",
            description="The storage container name was updated.",
            content={
                "container_id": str(
                    self._context.get_parameter_value("container_id")
                ),
                "name": str(
                    self._context.get_parameter_value("container_rename_to")
                ),
                "path": str(self._target_path),
                "current_state": self.current_state.value,
                "visited_states": visited_states,
            },
        )

    @staticmethod
    def _state_reaches(
        observed_state: ContainerRenameProcessStatePort,
        target_state: ContainerRenameProcessStatePort,
    ) -> bool:
        if observed_state == target_state:
            return True

        if target_state == ContainerRenameProcessState.CONTAINER_METADATA_RENAMED:
            return observed_state in {
                ContainerRenameProcessState.CONTAINER_STORAGE_INDEX_RENAMED,
                ContainerRenameProcessState.CONTAINER_STORAGE_INDEX_READY,
                ContainerRenameProcessState.CONTAINER_RENAMED,
            }

        if (
            target_state
            == ContainerRenameProcessState.CONTAINER_STORAGE_INDEX_RENAMED
        ):
            return observed_state in {
                ContainerRenameProcessState.CONTAINER_STORAGE_INDEX_READY,
                ContainerRenameProcessState.CONTAINER_RENAMED,
            }

        if (
            target_state
            == ContainerRenameProcessState.CONTAINER_STORAGE_INDEX_READY
        ):
            return observed_state == ContainerRenameProcessState.CONTAINER_RENAMED

        return False

    @staticmethod
    def _get_statechart_file_path() -> Path:
        return StatechartLocator.locate(
            __file__,
            "standard_container_rename.yaml",
            statechart_package="ontobdc.storage.domain.machine",
        )
