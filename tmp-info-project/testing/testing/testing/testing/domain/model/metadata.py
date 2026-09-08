from dataclasses import dataclass, field
from typing import List


@dataclass(frozen=True)
class ManifestMetadata:
    """`metadata` block shared by every manifest kind (semantic-test-orchestrator.md, 7.1)."""

    name: str
    title: str = ""
    description: str = ""
    tags: List[str] = field(default_factory=list)
