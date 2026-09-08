import importlib
from datetime import datetime, timezone
from typing import Any, Dict

from ontobdc_dev.testing.adapter.substitution import substitute
from ontobdc_dev.testing.domain.enum import ActionOutcomeStatus, ObservationStatus
from ontobdc_dev.testing.domain.exception import TestExecutionError
from ontobdc_dev.testing.domain.model.action import TestAction
from ontobdc_dev.testing.domain.model.context import ExecutionContext
from ontobdc_dev.testing.domain.model.result import ActionResult, StateSnapshot
from ontobdc_dev.testing.domain.model.state import StateDefinition


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _resolve_callable(target: str) -> Any:
    module_path, separator, attribute_name = target.partition(":")
    if not separator or not module_path or not attribute_name:
        raise TestExecutionError(
            f"Invalid python-call target '{target}'. Expected 'module.path:callable'."
        )

    module: Any = importlib.import_module(module_path)
    return getattr(module, attribute_name)


def _call_target(target: str, arguments: Dict[str, Any], context: ExecutionContext) -> int:
    callable_target: Any = _resolve_callable(target)
    resolved_arguments: Dict[str, Any] = substitute(arguments, context)
    exit_code: Any = callable_target(**resolved_arguments)
    if not isinstance(exit_code, int) or isinstance(exit_code, bool):
        raise TestExecutionError(
            f"'{target}' returned {exit_code!r}; a python-call target must return an int exit code."
        )

    return exit_code


class PythonCallObserver:
    """Wraps an existing `check.py:main` as a `StateObserverPort` (semantic-test-orchestrator.md, 7.3).

    No source change is required in the wrapped check: the exit-code
    convention (0 satisfied / 1 unsatisfied / 2 error) already matches what
    every `is_*_ready` check in `ontobdc` returns.
    """

    def observe(self, definition: StateDefinition, context: ExecutionContext) -> StateSnapshot:
        spec: Dict[str, Any] = definition.observer or {}
        target: str = str(spec.get("target", ""))
        try:
            exit_code: int = _call_target(target, spec.get("arguments") or {}, context)
        except Exception as exception:
            return StateSnapshot(
                state=definition.name,
                status=ObservationStatus.ERROR,
                observed_at=_now_iso(),
                detail=str(exception),
                evidence={"target": target},
            )

        status: ObservationStatus = _resolve_observation_status(spec.get("result") or {}, exit_code)
        return StateSnapshot(
            state=definition.name,
            status=status,
            observed_at=_now_iso(),
            detail=f"exit code {exit_code}",
            evidence={"target": target, "exitCode": exit_code},
        )


class PythonCallExecutor:
    """Wraps an existing `hotfix.py:main` as an `ActionExecutorPort` (semantic-test-orchestrator.md, 7.4)."""

    def execute(self, action: TestAction, context: ExecutionContext) -> ActionResult:
        spec: Dict[str, Any] = action.executor
        target: str = str(spec.get("target", ""))
        try:
            exit_code: int = _call_target(target, spec.get("arguments") or {}, context)
        except Exception as exception:
            return ActionResult(
                action=action.name,
                status=ActionOutcomeStatus.ERROR,
                executed_at=_now_iso(),
                detail=str(exception),
            )

        status: ActionOutcomeStatus = _resolve_action_status(spec.get("result") or {}, exit_code)
        return ActionResult(
            action=action.name,
            status=status,
            executed_at=_now_iso(),
            detail=f"exit code {exit_code}",
        )


def _resolve_observation_status(result_spec: Dict[str, Any], exit_code: int) -> ObservationStatus:
    if exit_code in _exit_codes(result_spec, "satisfiedWhen"):
        return ObservationStatus.SATISFIED
    if exit_code in _exit_codes(result_spec, "unsatisfiedWhen"):
        return ObservationStatus.UNSATISFIED
    if exit_code in _exit_codes(result_spec, "errorWhen"):
        return ObservationStatus.ERROR

    otherwise: str = str(result_spec.get("otherwise", "error"))
    return {
        "satisfied": ObservationStatus.SATISFIED,
        "unsatisfied": ObservationStatus.UNSATISFIED,
        "error": ObservationStatus.ERROR,
    }.get(otherwise, ObservationStatus.ERROR)


def _resolve_action_status(result_spec: Dict[str, Any], exit_code: int) -> ActionOutcomeStatus:
    if exit_code in _exit_codes(result_spec, "succeededWhen"):
        return ActionOutcomeStatus.SUCCEEDED
    if exit_code in _exit_codes(result_spec, "failedWhen"):
        return ActionOutcomeStatus.FAILED

    otherwise: str = str(result_spec.get("otherwise", "error"))
    return {
        "succeeded": ActionOutcomeStatus.SUCCEEDED,
        "failed": ActionOutcomeStatus.FAILED,
        "error": ActionOutcomeStatus.ERROR,
    }.get(otherwise, ActionOutcomeStatus.ERROR)


def _exit_codes(result_spec: Dict[str, Any], key: str) -> set:
    branch: Any = result_spec.get(key) or {}
    return set(branch.get("exitCode", []) or [])
