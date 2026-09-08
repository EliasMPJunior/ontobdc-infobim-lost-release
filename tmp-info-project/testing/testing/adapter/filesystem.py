from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict

from ontobdc_dev.testing.adapter.substitution import substitute
from ontobdc_dev.testing.domain.enum import ObservationStatus
from ontobdc_dev.testing.domain.model.context import ExecutionContext
from ontobdc_dev.testing.domain.model.result import StateSnapshot
from ontobdc_dev.testing.domain.model.state import StateDefinition


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


class FilesystemObserver:
    """Observes file/directory existence without modifying the system (semantic-test-orchestrator.md, 4.3, 8.1)."""

    def observe(self, definition: StateDefinition, context: ExecutionContext) -> StateSnapshot:
        spec: Dict[str, Any] = definition.observer or {}
        try:
            raw_path: str = str(substitute(spec.get("exists", ""), context))
        except Exception as exception:
            return StateSnapshot(
                state=definition.name,
                status=ObservationStatus.ERROR,
                observed_at=_now_iso(),
                detail=str(exception),
            )

        resolved_path: Path = Path(raw_path).expanduser()
        kind: str = str(spec.get("kind", ""))
        satisfied: bool = self._matches(resolved_path, kind)

        return StateSnapshot(
            state=definition.name,
            status=ObservationStatus.SATISFIED if satisfied else ObservationStatus.UNSATISFIED,
            observed_at=_now_iso(),
            detail=str(resolved_path),
            evidence={"path": str(resolved_path), "kind": kind},
        )

    def _matches(self, resolved_path: Path, kind: str) -> bool:
        if kind == "directory":
            return resolved_path.is_dir()
        if kind == "file":
            return resolved_path.is_file()

        return resolved_path.exists()
