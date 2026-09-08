from dataclasses import dataclass
from typing import Any, Dict, Optional

from ontobdc_dev.testing.domain.model.metadata import ManifestMetadata


@dataclass(frozen=True)
class StateDefinition:
    """A verifiable condition of the system (semantic-test-orchestrator.md, 4.2/7.3/8).

    Exactly one of `observer` (a probe: `python-call`, `filesystem`, ...) or
    `expression` (a composite `all`/`any`/`not` over other state names) is
    set; `TestCatalogLoader` enforces this at load time.
    """

    metadata: ManifestMetadata
    observer: Optional[Dict[str, Any]] = None
    expression: Optional[Dict[str, Any]] = None

    @property
    def name(self) -> str:
        return self.metadata.name
