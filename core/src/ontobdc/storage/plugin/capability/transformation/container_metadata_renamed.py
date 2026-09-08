from typing import Any, Dict

from ontobdc.cli.domain.port.context import CliContextPort
from ontobdc.shared.adapter.capability import TransactionCapability
from ontobdc.shared.domain.model.capability import CapabilityMetadata
from ontobdc.storage.adapter.container_name import ContainerNameAdapter
from ontobdc.storage.domain.machine.rename_state import (
    ContainerRenameProcessState,
)


class ContainerMetadataRenamedCapability(TransactionCapability):
    METADATA: CapabilityMetadata = CapabilityMetadata(
        id=(
            "org.ontobdc.storage.plugin.capability.transformation.target."
            "container_metadata_renamed"
        ),
        version="1.0.0",
        name="Container Metadata Renamed",
        description="Set the canonical container title in container.ttl.",
        author=["Elias Magalhães"],
        tags=["storage", "container", "rename", "metadata"],
        supported_languages=["en", "pt-br"],
        log_message={
            "info": {
                "en": "Container metadata name updated.",
            },
            "debug_entry": {
                "en": "Updating the canonical container name in container.ttl.",
            },
        },
    )

    def label(self, lang: str = "en") -> str:
        return "Container Metadata Renamed"

    def description(self, lang: str = "en") -> str:
        return "Sets the canonical container title in container.ttl."

    def execute(self, context: CliContextPort) -> Dict[str, Any]:
        requested_name: str = str(
            context.get_parameter_value("container_rename_to")
        ).strip()
        adapter: ContainerNameAdapter = ContainerNameAdapter.from_context(
            context
        )
        adapter.rename_metadata(requested_name)

        if adapter.metadata_title() != requested_name:
            raise ValueError("Container metadata name was not persisted.")

        return {
            "resulting_state": (
                ContainerRenameProcessState.CONTAINER_METADATA_RENAMED
            ),
            "container_id": adapter.container_id,
            "name": requested_name,
        }
