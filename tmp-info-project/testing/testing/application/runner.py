from datetime import datetime, timezone
from typing import Any, Dict, List

from ontobdc_dev.testing.adapter.filesystem import FilesystemObserver
from ontobdc_dev.testing.adapter.python_call import PythonCallExecutor, PythonCallObserver
from ontobdc_dev.testing.application.catalog import TestCatalog
from ontobdc_dev.testing.domain.enum import ActionOutcomeStatus, ObservationStatus, TestVerdict
from ontobdc_dev.testing.domain.model.action import TestAction
from ontobdc_dev.testing.domain.model.context import ExecutionContext
from ontobdc_dev.testing.domain.model.result import ActionResult, StateSnapshot, TestRunResult
from ontobdc_dev.testing.domain.model.state import StateDefinition
from ontobdc_dev.testing.domain.port.executor import ActionExecutorPort
from ontobdc_dev.testing.domain.port.observer import StateObserverPort


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


class SemanticTestRunner:
    """Runs the `check -> hotfix -> recheck` cycle against a `TestCatalog`.

    This is the executable core of semantic-test-orchestrator.md section 6
    ("Semântica de check e hotfix") and section 10 ("Ciclo de execução"),
    reduced to what is needed to run a single state or a single action: no
    fixtures, sandbox, planner, or evidence persistence (phases 4/5/6 of the
    document) are implemented here.
    """

    def __init__(self, catalog: TestCatalog) -> None:
        self._catalog: TestCatalog = catalog
        self._observers: Dict[str, StateObserverPort] = {
            "python-call": PythonCallObserver(),
            "filesystem": FilesystemObserver(),
        }
        self._executors: Dict[str, ActionExecutorPort] = {
            "python-call": PythonCallExecutor(),
        }

    def observe(self, state_name: str, context: ExecutionContext) -> StateSnapshot:
        definition: StateDefinition = self._catalog.get_state(state_name)
        if definition.expression is not None:
            return self._observe_expression(definition, context)

        observer_spec: Dict[str, Any] = definition.observer or {}
        observer_type: str = str(observer_spec.get("type", ""))
        observer: Any = self._observers.get(observer_type)
        if observer is None:
            return StateSnapshot(
                state=state_name,
                status=ObservationStatus.ERROR,
                observed_at=_now_iso(),
                detail=f"Unsupported observer type '{observer_type}'.",
            )

        return observer.observe(definition, context)

    def execute(self, action_name: str, context: ExecutionContext) -> ActionResult:
        action: TestAction = self._catalog.get_action(action_name)
        executor_type: str = str(action.executor.get("type", ""))
        executor: Any = self._executors.get(executor_type)
        if executor is None:
            return ActionResult(
                action=action_name,
                status=ActionOutcomeStatus.ERROR,
                executed_at=_now_iso(),
                detail=f"Unsupported executor type '{executor_type}'.",
            )

        return executor.execute(action, context)

    def run_state(self, state_name: str, context: ExecutionContext) -> TestRunResult:
        """Observe one state and derive a verdict directly from it (a check without a hotfix)."""

        snapshot: StateSnapshot = self.observe(state_name, context)
        return TestRunResult(
            mode="state",
            target=state_name,
            before={state_name: snapshot},
            action_result=None,
            after={},
            verdict=self._verdict_from_snapshots([snapshot]),
            detail=snapshot.detail,
        )

    def run_action(self, action_name: str, context: ExecutionContext) -> TestRunResult:
        """Run check -> hotfix -> recheck for one action.

        The pre-execution observation is informational only. The verdict is
        always computed from the post-execution reobservation of
        `verification_states`, never from the action outcome alone
        (semantic-test-orchestrator.md, 6.1).
        """

        action: TestAction = self._catalog.get_action(action_name)
        before: Dict[str, StateSnapshot] = {
            state_name: self.observe(state_name, context)
            for state_name in action.verification_states
        }

        action_result: ActionResult = self.execute(action_name, context)
        if action_result.status is ActionOutcomeStatus.ERROR:
            return TestRunResult(
                mode="action",
                target=action_name,
                before=before,
                action_result=action_result,
                after={},
                verdict=TestVerdict.ERROR,
                detail=action_result.detail,
            )

        if action_result.status in (ActionOutcomeStatus.FAILED, ActionOutcomeStatus.TIMED_OUT):
            return TestRunResult(
                mode="action",
                target=action_name,
                before=before,
                action_result=action_result,
                after={},
                verdict=TestVerdict.FAILED,
                detail=action_result.detail,
            )

        after: Dict[str, StateSnapshot] = {
            state_name: self.observe(state_name, context)
            for state_name in action.verification_states
        }
        return TestRunResult(
            mode="action",
            target=action_name,
            before=before,
            action_result=action_result,
            after=after,
            verdict=self._verdict_from_snapshots(list(after.values())),
            detail="; ".join(f"{name}={snapshot.status.value}" for name, snapshot in after.items()),
        )

    def _observe_expression(
        self,
        definition: StateDefinition,
        context: ExecutionContext,
    ) -> StateSnapshot:
        expression: Dict[str, Any] = definition.expression or {}

        if "not" in expression:
            referenced_name: str = str(expression["not"])
            referenced_snapshot: StateSnapshot = self.observe(referenced_name, context)
            status: ObservationStatus = self._negate(referenced_snapshot.status)
            sub_snapshots: List[StateSnapshot] = [referenced_snapshot]
        elif "all" in expression:
            sub_snapshots = [self.observe(str(name), context) for name in expression["all"]]
            status = self._combine_all(sub_snapshots)
        elif "any" in expression:
            sub_snapshots = [self.observe(str(name), context) for name in expression["any"]]
            status = self._combine_any(sub_snapshots)
        else:
            return StateSnapshot(
                state=definition.name,
                status=ObservationStatus.ERROR,
                observed_at=_now_iso(),
                detail="Composite state expression must declare 'all', 'any', or 'not'.",
            )

        detail: str = ", ".join(f"{snapshot.state}={snapshot.status.value}" for snapshot in sub_snapshots)
        return StateSnapshot(state=definition.name, status=status, observed_at=_now_iso(), detail=detail)

    def _negate(self, status: ObservationStatus) -> ObservationStatus:
        if status is ObservationStatus.ERROR:
            return ObservationStatus.ERROR
        if status is ObservationStatus.SATISFIED:
            return ObservationStatus.UNSATISFIED

        return ObservationStatus.SATISFIED

    def _combine_all(self, snapshots: List[StateSnapshot]) -> ObservationStatus:
        if any(snapshot.status is ObservationStatus.ERROR for snapshot in snapshots):
            return ObservationStatus.ERROR
        if all(snapshot.status is ObservationStatus.SATISFIED for snapshot in snapshots):
            return ObservationStatus.SATISFIED

        return ObservationStatus.UNSATISFIED

    def _combine_any(self, snapshots: List[StateSnapshot]) -> ObservationStatus:
        if any(snapshot.status is ObservationStatus.SATISFIED for snapshot in snapshots):
            return ObservationStatus.SATISFIED
        if any(snapshot.status is ObservationStatus.ERROR for snapshot in snapshots):
            return ObservationStatus.ERROR

        return ObservationStatus.UNSATISFIED

    def _verdict_from_snapshots(self, snapshots: List[StateSnapshot]) -> TestVerdict:
        if any(snapshot.status is ObservationStatus.ERROR for snapshot in snapshots):
            return TestVerdict.ERROR
        if snapshots and all(snapshot.status is ObservationStatus.SATISFIED for snapshot in snapshots):
            return TestVerdict.PASSED

        return TestVerdict.FAILED
