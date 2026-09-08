from ontobdc.storage.domain.port.rename_machine import (
    ContainerRenameProcessStatePort,
)


class ContainerRenameProcessState(ContainerRenameProcessStatePort):
    """States of the semantic storage container rename process."""

    UNDEFINED = "__undefined__"
    CONTAINER_INVALID = "__container_invalid__"
    CONTAINER_METADATA_RENAMED = "__container_metadata_renamed__"
    CONTAINER_STORAGE_INDEX_RENAMED = "__container_storage_index_renamed__"
    CONTAINER_STORAGE_INDEX_READY = "__container_storage_index_ready__"
    CONTAINER_RENAMED = "__container_renamed__"

    @staticmethod
    def get_state(state: str) -> "ContainerRenameProcessState":
        return getattr(ContainerRenameProcessState, state.upper())
