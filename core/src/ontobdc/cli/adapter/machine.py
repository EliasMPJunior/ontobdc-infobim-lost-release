from pathlib import Path
from typing import Any, Dict, List, Optional, Type

from ontobdc.cli.adapter.logger import NullLogRepository
from ontobdc.cli.domain.port.context import CliContextPort
from ontobdc.shared.adapter.capability import CapabilityExecutor
from ontobdc.shared.adapter.loader import CapabilityLoader
from ontobdc.shared.adapter.statechart import StatechartLocator
from ontobdc.shared.adapter.worker import StateWorkerAdapter
from ontobdc.cli.domain.machine.health_state import CliHealthProcessState
from ontobdc.cli.domain.machine.state import CliInitProcessState
from ontobdc.cli.domain.port.logger import LogRepositoryPort
from ontobdc.cli.domain.port.machine import (
    CliHealthProcessStatePort,
    CliHealthStateEvaluatorPort,
    CliHealthStateTransitionHandlerPort,
    CliInitProcessStatePort,
    CliInitStateEvaluatorPort,
    CliInitStateTransitionHandlerPort,
)
from ontobdc.cli.domain.response.command import CommandResponse
from ontobdc.shared.domain.port.capability import CapabilityPort
from ontobdc.cli.plugin.check.has_valid_engine.check import main as check_engine
from ontobdc.storage.plugin.check.is_root_set.check import main as check_storage_index
from ontobdc.storage.adapter.bootstrap import StorageBootstrap
from ontobdc.cli.plugin.check.has_valid_config_file.check import main as check_config_file
from ontobdc.cli.plugin.check.has_valid_brand.check import main as check_brand
from ontobdc.context.plugin.check.has_valid_context.check import main as check_execution_context


class CliInitStateEvaluatorAdapter(CliInitStateEvaluatorPort):
    @property
    def process_state_class(self) -> Type[CliInitProcessStatePort]:
        return CliInitProcessState

    def evaluate(self, context: CliContextPort) -> CliInitProcessStatePort:
        root_path: Path = StorageBootstrap.get_init_root_path(context=context)
        ontobdc_directory: Path = StorageBootstrap.get_ontobdc_directory(root_path)
        if not ontobdc_directory.is_dir():
            return CliInitProcessState.UNDEFINED

        if check_engine(root_path=str(root_path)) != 0:
            return CliInitProcessState.ONTOBDC_DIRECTORY_READY

        if check_storage_index(root_path=str(root_path)) != 0:
            return CliInitProcessState.ENGINE_READY

        if check_execution_context(root_path=str(root_path)) != 0:
            return CliInitProcessState.STORAGE_INDEX_HEALTHY

        if check_config_file(root_path=str(root_path)) != 0:
            return CliInitProcessState.EXECUTION_CONTEXT_HEALTHY

        if check_brand(root_path=str(root_path)) != 0:
            return CliInitProcessState.CONFIG_ADAPTER_READY

        return CliInitProcessState.BRAND_READY


class CliInitStateTransitionHandler(CliInitStateTransitionHandlerPort):
    def __init__(
        self,
        context: CliContextPort,
        logger: Optional[LogRepositoryPort] = None,
    ) -> None:
        self._context: CliContextPort = context
        self._logger: LogRepositoryPort = logger or NullLogRepository()
        self._state_evaluator: CliInitStateEvaluatorPort = CliInitStateEvaluatorAdapter()
        self._active_state: Optional[CliInitProcessStatePort] = None

    @property
    def current_state(self) -> CliInitProcessStatePort:
        if self._active_state is not None:
            return self._active_state

        return self.observed_state

    @property
    def observed_state(self) -> CliInitProcessStatePort:
        return self._state_evaluator.evaluate(self._context)

    @property
    def state_sequence(self) -> List[CliInitProcessStatePort]:
        return list(CliInitProcessState)

    def can_transit_to(self, to_state: CliInitProcessStatePort) -> bool:
        return self.current_state != to_state

    def perform_state_transition(self, to_state: CliInitProcessStatePort) -> None:
        self._logger.log_info(
            f"CLI init transition: {self.current_state.value} -> {to_state.value}",
        )
        capability_id: str = (
            f"org.ontobdc.cli.plugin.capability.transformation.target.{to_state.value.strip('_')}"
        )
        capability_type: Any = CapabilityLoader().get(capability_id)
        if capability_type is None:
            raise ValueError(f"CLI init capability not found: {capability_id}")

        capability: CapabilityPort = capability_type()
        CapabilityExecutor.execute(capability, self._context)

    def validate_state_transition(
        self,
        from_state: CliInitProcessStatePort,
        to_state: CliInitProcessStatePort,
    ) -> bool:
        if from_state == to_state:
            return False

        observed_state: CliInitProcessStatePort = self.observed_state
        if observed_state == to_state:
            return True

        state_sequence: List[CliInitProcessStatePort] = self.state_sequence
        if to_state not in state_sequence or observed_state not in state_sequence:
            return False

        return state_sequence.index(observed_state) > state_sequence.index(to_state)

    def execute(self) -> CommandResponse:
        worker: StateWorkerAdapter = StateWorkerAdapter(
            state_adapter=CliInitProcessState,
            state_context_name="CliInitProcessStatePort",
            handler=self,
            logger=self._logger,
            statechart_file_path=self._get_statechart_file_path(),
        )
        visited_states: List[str] = worker.work()

        root_path: Path = StorageBootstrap.get_init_root_path(context=self._context)
        self._logger.log_notice("OntoBDC init bootstrap finished successfully.")
        return CommandResponse(
            title="Init",
            description="Bootstrap initialization executed successfully.",
            content={
                "root_path": str(root_path),
                "ontobdc_directory": str(StorageBootstrap.get_ontobdc_directory(root_path)),
                "current_state": self.current_state.value,
                "visited_states": visited_states,
            },
        )

    def _get_statechart_file_path(self) -> Path:
        return StatechartLocator.locate(
            __file__,
            "standard_init.yaml",
        )

    def bind_active_state(self, state: CliInitProcessStatePort) -> None:
        self._active_state = state


# The bootstrap capabilities ``ontobdc health`` runs, in pipeline order.
# Each entry maps a health state to the transformation capability whose
# id ends with that state's name.
_HEALTH_CAPABILITY_IDS: Dict[CliHealthProcessState, str] = {
    CliHealthProcessState.ONTOBDC_DIRECTORY_READY: (
        "org.ontobdc.cli.plugin.capability.transformation.target."
        "ontobdc_directory_ready"
    ),
    CliHealthProcessState.ENGINE_READY: (
        "org.ontobdc.cli.plugin.capability.transformation.target.engine_ready"
    ),
    CliHealthProcessState.STORAGE_INDEX_HEALTHY: (
        "org.ontobdc.cli.plugin.capability.transformation.target."
        "storage_index_healthy"
    ),
    CliHealthProcessState.EXECUTION_CONTEXT_HEALTHY: (
        "org.ontobdc.cli.plugin.capability.transformation.target."
        "execution_context_healthy"
    ),
    CliHealthProcessState.CONFIG_ADAPTER_READY: (
        "org.ontobdc.cli.plugin.capability.transformation.target."
        "config_adapter_ready"
    ),
}


class CliHealthStateEvaluatorAdapter(CliHealthStateEvaluatorPort):
    """The health pipeline always runs start-to-finish.

    Unlike CLI init, ``ontobdc health`` does not resume from wherever the
    filesystem already is -- it re-runs every bootstrap capability on each
    invocation so the check list is always complete. The observed state is
    therefore always ``UNDEFINED`` until the worker starts binding the
    active state.
    """

    @property
    def process_state_class(self) -> Type[CliHealthProcessStatePort]:
        return CliHealthProcessState

    def evaluate(self, context: CliContextPort) -> CliHealthProcessStatePort:
        _ = context
        return CliHealthProcessState.UNDEFINED


class CliHealthStateTransitionHandler(CliHealthStateTransitionHandlerPort):
    """Drive the ``StandardCliHealth`` statechart.

    Each transition runs one bootstrap capability (the same ones
    ``ontobdc init`` uses: repair + validate) and records the outcome --
    the capability's uri, name and description plus a pass/fail status --
    in :attr:`checks`. The pipeline never stops on a failing capability;
    every check is attempted and reported. The final response is healthy
    only when every recorded check passed.
    """

    def __init__(
        self,
        context: CliContextPort,
        logger: Optional[LogRepositoryPort] = None,
    ) -> None:
        self._context: CliContextPort = context
        self._logger: LogRepositoryPort = logger or NullLogRepository()
        self._state_evaluator: CliHealthStateEvaluatorPort = (
            CliHealthStateEvaluatorAdapter()
        )
        self._active_state: Optional[CliHealthProcessStatePort] = None
        self._checks: List[Dict[str, Any]] = []

    @property
    def checks(self) -> List[Dict[str, Any]]:
        return list(self._checks)

    @property
    def current_state(self) -> CliHealthProcessStatePort:
        if self._active_state is not None:
            return self._active_state

        return CliHealthProcessState.UNDEFINED

    @property
    def observed_state(self) -> CliHealthProcessStatePort:
        return self.current_state

    @property
    def state_sequence(self) -> List[CliHealthProcessStatePort]:
        return list(CliHealthProcessState)

    def can_transit_to(self, to_state: CliHealthProcessStatePort) -> bool:
        return self.current_state != to_state

    def perform_state_transition(
        self,
        to_state: CliHealthProcessStatePort,
    ) -> None:
        self._logger.log_info(
            f"CLI health transition: {self.current_state.value} -> "
            f"{to_state.value}",
        )

        capability_id: Optional[str] = _HEALTH_CAPABILITY_IDS.get(to_state)
        if capability_id is None:
            # ``bootstrap_healthy`` is the synthetic terminal state -- every
            # real capability has already run by the time it is reached.
            return

        capability_type: Any = CapabilityLoader().get(capability_id)
        if capability_type is None:
            self._record_check(
                uri=capability_id,
                name=to_state.label(),
                description="",
                status="fail",
                detail=f"Capability not found: {capability_id}",
            )
            return

        capability: CapabilityPort = capability_type()
        metadata: Any = capability.METADATA
        try:
            CapabilityExecutor.execute(capability, self._context)
        except Exception as error:  # noqa: BLE001 - reported, not raised
            self._record_check(
                uri=str(metadata.id),
                name=str(metadata.name),
                description=str(metadata.description),
                status="fail",
                detail=f"{type(error).__name__}: {error}",
            )
            return

        self._record_check(
            uri=str(metadata.id),
            name=str(metadata.name),
            description=str(metadata.description),
            status="pass",
            detail="",
        )

    def _record_check(
        self,
        *,
        uri: str,
        name: str,
        description: str,
        status: str,
        detail: str,
    ) -> None:
        marker: str = "OK" if status == "pass" else "FAILED"
        if status == "pass":
            self._logger.log_info(f"[{marker}] {name}")
        else:
            self._logger.log_error(f"[{marker}] {name}: {detail}")
        self._checks.append(
            {
                "name": name,
                "status": status,
                "detail": detail,
                "uri": uri,
                "description": description,
            }
        )

    def validate_state_transition(
        self,
        from_state: CliHealthProcessStatePort,
        to_state: CliHealthProcessStatePort,
    ) -> bool:
        state_sequence: List[CliHealthProcessStatePort] = self.state_sequence
        if (
            from_state not in state_sequence
            or to_state not in state_sequence
        ):
            return False

        # A legal step is forward by exactly one position in the linear
        # pipeline. Whether the capability actually succeeded is recorded
        # in ``checks`` -- it does not gate the pipeline.
        return (
            state_sequence.index(to_state)
            == state_sequence.index(from_state) + 1
        )

    def execute(self) -> CommandResponse:
        # ``ontobdc health`` verifies an existing project -- it never
        # bootstraps one. The bootstrap capabilities would happily create
        # .__ontobdc__ under the current directory (that is how
        # ``ontobdc init`` works); guard against that here so health stays
        # a diagnostic, not an implicit init.
        root_path: Path = StorageBootstrap.get_init_root_path(
            context=self._context
        )
        if not StorageBootstrap.get_ontobdc_directory(root_path).is_dir():
            raise RuntimeError(
                "System health verification failed: no OntoBDC project "
                f"found at {root_path}. Run 'ontobdc init' first."
            )

        self._checks = []
        StateWorkerAdapter(
            state_adapter=CliHealthProcessState,
            state_context_name="CliHealthProcessStatePort",
            handler=self,
            logger=self._logger,
            statechart_file_path=self._get_statechart_file_path(),
        ).work()

        failed: List[Dict[str, Any]] = [
            check for check in self._checks if check["status"] != "pass"
        ]
        healthy: bool = bool(self._checks) and not failed

        if healthy:
            self._logger.log_notice(
                "OntoBDC system health verification passed."
            )
            description: str = (
                f"All {len(self._checks)} health checks passed."
            )
        else:
            self._logger.log_warning(
                f"OntoBDC system health verification found "
                f"{len(failed)} failing check(s)."
            )
            description = (
                f"{len(self._checks) - len(failed)} of "
                f"{len(self._checks)} health checks passed."
            )

        # The ``detail`` column only carries text on a failure; drop it
        # entirely when every check passed so the table stays a clean
        # name/status pair instead of a wide empty column.
        checks: List[Dict[str, Any]] = self._checks
        if not any(check["detail"] for check in checks):
            checks = [
                {key: value for key, value in check.items() if key != "detail"}
                for check in checks
            ]

        return CommandResponse(
            title="Health",
            description=description,
            content={
                "healthy": healthy,
                "checks": checks,
            },
            severity="SUCCESS" if healthy else "ERROR",
        )

    def _get_statechart_file_path(self) -> Path:
        return StatechartLocator.locate(
            __file__,
            "standard_health.yaml",
        )

    def bind_active_state(self, state: CliHealthProcessStatePort) -> None:
        self._active_state = state
