from enum import Enum


class ObservationStatus(str, Enum):
    """Outcome of observing a `StateDefinition` (semantic-test-orchestrator.md, 6.2)."""

    SATISFIED = "satisfied"
    UNSATISFIED = "unsatisfied"
    ERROR = "error"


class ActionOutcomeStatus(str, Enum):
    """Outcome of executing a `TestAction` (semantic-test-orchestrator.md, 5.3)."""

    SUCCEEDED = "succeeded"
    FAILED = "failed"
    ERROR = "error"
    NOOP = "noop"
    TIMED_OUT = "timed_out"


class TestVerdict(str, Enum):
    """Final classification of a test run (semantic-test-orchestrator.md, 4.16/5.4)."""

    PASSED = "passed"
    FAILED = "failed"
    ERROR = "error"
    BLOCKED = "blocked"
    SKIPPED = "skipped"
    INCONCLUSIVE = "inconclusive"
