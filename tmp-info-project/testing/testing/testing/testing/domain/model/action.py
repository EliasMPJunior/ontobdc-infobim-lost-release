from dataclasses import dataclass, field
from typing import Any, Dict, List

from ontobdc_dev.testing.domain.model.metadata import ManifestMetadata


@dataclass(frozen=True)
class TestAction:
    """An executable operation, typically wrapping a `hotfix.py` (semantic-test-orchestrator.md, 4.5/4.6/7.4).

    `requires` and `ensures` are recorded and reference-checked against the
    catalog, but are not resolved by a planner in this slice (semantic
    planning is out of scope, see semantic-test-orchestrator.md section 9).
    `verification_states` is what the runner actually reobserves after
    execution; it defaults to `ensures` when `verification.states` is absent.
    """

    metadata: ManifestMetadata
    role: str
    executor: Dict[str, Any]
    requires: List[str] = field(default_factory=list)
    ensures: List[str] = field(default_factory=list)
    verification_states: List[str] = field(default_factory=list)

    @property
    def name(self) -> str:
        return self.metadata.name
