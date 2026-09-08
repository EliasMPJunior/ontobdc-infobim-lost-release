from dataclasses import dataclass, field
from typing import Dict, Optional


@dataclass(frozen=True)
class ExecutionContext:
    """Named values available to `${context.<name>}` placeholders.

    Fixture materialization (semantic-test-orchestrator.md, 13) is not
    implemented in this slice, so values are supplied directly by the
    caller (the `--param key=value` flags of `ontobdc-dev test run`).
    """

    values: Dict[str, str] = field(default_factory=dict)

    def get(self, key: str) -> Optional[str]:
        return self.values.get(key)
