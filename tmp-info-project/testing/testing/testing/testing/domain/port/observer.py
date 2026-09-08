from typing import Protocol

from ontobdc_dev.testing.domain.model.context import ExecutionContext
from ontobdc_dev.testing.domain.model.result import StateSnapshot
from ontobdc_dev.testing.domain.model.state import StateDefinition


class StateObserverPort(Protocol):
    """Observes a `StateDefinition` without modifying the system (semantic-test-orchestrator.md, 4.3, 19)."""

    def observe(
        self,
        definition: StateDefinition,
        context: ExecutionContext,
    ) -> StateSnapshot:
        ...
