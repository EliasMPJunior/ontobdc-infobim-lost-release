[↑ Back to state-machine inventory](index.md)

# Container creation

> **Status:** Current and executable.

Creates a container directory, metadata graph, storage-index entry, and synchronized manifest.

## Audited implementation

- Enum: [ContainerCreateProcessState](https://github.com/EliasMPJunior/ontobdc-wip/blob/fe6d756c44141cdc14234937ce1e659384950b26/src/ontobdc/storage/domain/machine/state.py)
- YAML: [standard_container_create.yaml](https://github.com/EliasMPJunior/ontobdc-wip/blob/fe6d756c44141cdc14234937ce1e659384950b26/src/ontobdc/storage/domain/machine/standard_container_create.yaml) (runtime statechart)
- Executor: [evaluator and transition handler](https://github.com/EliasMPJunior/ontobdc-wip/blob/fe6d756c44141cdc14234937ce1e659384950b26/src/ontobdc/storage/adapter/machine.py)

## States from the enum

| State | Raw value | Enum meaning | Capability or executing operation |
| --- | --- | --- | --- |
| `UNDEFINED` | `__undefined__` | Initial state before the target container directory exists. | — |
| `INVALID_PATH` | `__invalid_path__` | The target path points to an existing file and cannot be used as a container directory. | — |
| `DIRECTORY_READY` | `__directory_ready__` | The target container directory exists and is ready for the next creation steps. | `org.ontobdc.storage.plugin.capability.transformation.target.directory_ready`<br>[source](https://github.com/EliasMPJunior/ontobdc-wip/blob/fe6d756c44141cdc14234937ce1e659384950b26/src/ontobdc/storage/plugin/capability/transformation/directory_ready.py) |
| `CONTAINER_METADATA_READY` | `__container_metadata_ready__` | The container metadata file exists and contains a valid data container description without requiring datasets. | `org.ontobdc.storage.plugin.capability.transformation.target.container_metadata_ready`<br>[source](https://github.com/EliasMPJunior/ontobdc-wip/blob/fe6d756c44141cdc14234937ce1e659384950b26/src/ontobdc/storage/plugin/capability/transformation/container_metadata_ready.py) |
| `CONTAINER_STORAGE_INDEX_READY` | `__container_storage_index_ready__` | The storage index entry for the container matches the container metadata file and is synchronized. | `org.ontobdc.storage.plugin.capability.transformation.target.container_storage_index_ready`<br>[source](https://github.com/EliasMPJunior/ontobdc-wip/blob/fe6d756c44141cdc14234937ce1e659384950b26/src/ontobdc/storage/plugin/capability/transformation/container_storage_index_ready.py) |
| `CONTAINER_MANIFEST_SYNCED` | `__container_manifest_synced__` | The container manifest file exists and lists all container files excluding marker and dataset directories. | `org.ontobdc.storage.plugin.capability.transformation.target.container_manifest_synced`<br>[source](https://github.com/EliasMPJunior/ontobdc-wip/blob/fe6d756c44141cdc14234937ce1e659384950b26/src/ontobdc/storage/plugin/capability/transformation/container_manifest_synced.py) |

## Transition table

| From | To | Guard/condition | Action |
| --- | --- | --- | --- |
| `UNDEFINED` | `INVALID_PATH` | handler.can_transit_to(to_state = ContainerCreateProcessStatePort.INVALID_PATH) | no transition action |
| `UNDEFINED` | `DIRECTORY_READY` | handler.can_transit_to(to_state = ContainerCreateProcessStatePort.DIRECTORY_READY) | handler.perform_state_transition(to_state = ContainerCreateProcessStatePort.DIRECTORY_READY) |
| `DIRECTORY_READY` | `CONTAINER_METADATA_READY` | handler.can_transit_to(to_state = ContainerCreateProcessStatePort.CONTAINER_METADATA_READY) | handler.perform_state_transition(to_state = ContainerCreateProcessStatePort.CONTAINER_METADATA_READY) |
| `CONTAINER_METADATA_READY` | `CONTAINER_STORAGE_INDEX_READY` | handler.can_transit_to(to_state = ContainerCreateProcessStatePort.CONTAINER_STORAGE_INDEX_READY) | handler.perform_state_transition(to_state = ContainerCreateProcessStatePort.CONTAINER_STORAGE_INDEX_READY) |
| `CONTAINER_STORAGE_INDEX_READY` | `CONTAINER_MANIFEST_SYNCED` | handler.can_transit_to(to_state = ContainerCreateProcessStatePort.CONTAINER_MANIFEST_SYNCED) | handler.perform_state_transition(to_state = ContainerCreateProcessStatePort.CONTAINER_MANIFEST_SYNCED) |

## Runtime findings

- `INVALID_PATH` is selected by a guarded, actionless YAML transition; it is not produced by a capability.
- Every successful target state is observable from the filesystem, allowing the handler to resume an incomplete creation.
