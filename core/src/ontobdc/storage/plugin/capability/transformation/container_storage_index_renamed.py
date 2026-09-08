from typing import Any, Dict

from ontobdc.cli.domain.port.context import CliContextPort
from ontobdc.shared.adapter.capability import TransactionCapability
from ontobdc.shared.domain.model.capability import CapabilityMetadata
from ontobdc.storage.adapter.container_name import ContainerNameAdapter
from ontobdc.storage.domain.machine.rename_state import (
    ContainerRenameProcessState,
)


class ContainerStorageIndexRenamedCapability(TransactionCapability):
    METADATA: CapabilityMetadata = CapabilityMetadata(
        id=(
            "org.ontobdc.storage.plugin.capability.transformation.target."
            "container_storage_index_renamed"
        ),
        version="1.0.0",
        name="Container Storage Index Renamed",
        description="Synchronize the renamed container title into storage.ttl.",
        author=["Elias Magalhães"],
        tags=["storage", "container", "rename", "index"],
        supported_languages=["en", "pt-br"],
        log_message={
            "info": {
                "en": "Storage index container name synchronized.",
            },
            "debug_entry": {
                "en": "Synchronizing the renamed container name into storage.ttl.",
            },
        },
    )

    def label(self, lang: str = "en") -> str:
        return "Container Storage Index Renamed"

    def description(self, lang: str = "en") -> str:
        return "Synchronizes the renamed container title into storage.ttl."

    def execute(self, context: CliContextPort) -> Dict[str, Any]:
        adapter: ContainerNameAdapter = ContainerNameAdapter.from_context(
            context
        )
        adapter.rename_storage_index()

        if not adapter.storage_index_matches_metadata():
            raise ValueError("Storage index container name was not synchronized.")

        return {
            "resulting_state": (
                ContainerRenameProcessState.CONTAINER_STORAGE_INDEX_RENAMED
            ),
            "container_id": adapter.container_id,
        }
