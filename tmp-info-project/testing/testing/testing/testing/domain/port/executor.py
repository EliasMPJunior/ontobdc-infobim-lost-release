from typing import Protocol

from ontobdc_dev.testing.domain.model.action import TestAction
from ontobdc_dev.testing.domain.model.context import ExecutionContext
from ontobdc_dev.testing.domain.model.result import ActionResult


class ActionExecutorPort(Protocol):
    """Executes a `TestAction`, typically a `hotfix.py` wrapper (semantic-test-orchestrator.md, 4.5, 19)."""

    def execute(
        self,
        action: TestAction,
        context: ExecutionContext,
    ) -> ActionResult:
        ...
