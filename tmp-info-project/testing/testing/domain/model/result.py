from dataclasses import dataclass, field
from typing import Any, Dict, Optional

from ontobdc_dev.testing.domain.enum import ActionOutcomeStatus, ObservationStatus, TestVerdict


@dataclass(frozen=True)
class StateSnapshot:
    """Immutable record of a state observed at one instant (semantic-test-orchestrator.md, 4.4)."""

    state: str
    status: ObservationStatus
    observed_at: str
    detail: str = ""
    evidence: Dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class ActionResult:
    """Raw result of executing a `TestAction` (semantic-test-orchestrator.md, 4.14, `ActualResult`)."""

    action: str
    status: ActionOutcomeStatus
    executed_at: str
    detail: str = ""


@dataclass(frozen=True)
class TestRunResult:
    """Result of one `check` or `check -> hotfix -> recheck` cycle.

    `mode` is `"state"` for a bare check, or `"action"` when a `TestAction`
    was executed. The verdict is always derived from `after` (the recheck),
    never from `action_result` alone (semantic-test-orchestrator.md, 6.1:
    "o retorno do hotfix não comprova estado").
    """

    mode: str
    target: str
    before: Dict[str, StateSnapshot]
    action_result: Optional[ActionResult]
    after: Dict[str, StateSnapshot]
    verdict: TestVerdict
    detail: str = ""
