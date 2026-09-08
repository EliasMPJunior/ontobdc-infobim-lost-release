[↑ Back to state-machine inventory](index.md)

# Dataset creation

> **Status:** Current and executable.

Creates dataset metadata and synchronizes its entry into the owning container graph.

## Audited implementation

- Enum: [DatasetCreateProcessState](https://github.com/EliasMPJunior/ontobdc-wip/blob/fe6d756c44141cdc14234937ce1e659384950b26/src/ontobdc/storage/domain/machine/state.py)
- YAML: [standard_dataset_create.yaml](https://github.com/EliasMPJunior/ontobdc-wip/blob/fe6d756c44141cdc14234937ce1e659384950b26/src/ontobdc/storage/domain/machine/standard_dataset_create.yaml) (runtime statechart)
- Executor: [evaluator and transition handler](https://github.com/EliasMPJunior/ontobdc-wip/blob/fe6d756c44141cdc14234937ce1e659384950b26/src/ontobdc/storage/adapter/machine.py)

## States from the enum

| State | Raw value | Enum meaning | Capability or executing operation |
| --- | --- | --- | --- |
| `UNDEFINED` | `__undefined__` | Initial state before the target dataset directory exists. | — |
| `INVALID_PATH` | `__invalid_path__` | The target path points to an existing file and cannot be used as a dataset directory. | — |
| `DIRECTORY_READY` | `__directory_ready__` | The target dataset directory exists and is ready for the next creation steps. | `org.ontobdc.storage.plugin.capability.transformation.target.directory_ready`<br>[source](https://github.com/EliasMPJunior/ontobdc-wip/blob/fe6d756c44141cdc14234937ce1e659384950b26/src/ontobdc/storage/plugin/capability/transformation/directory_ready.py) |
| `DATASET_METADATA_READY` | `__dataset_metadata_ready__` | The dataset metadata file exists and contains a valid dataset description. | `org.ontobdc.storage.plugin.capability.transformation.target.dataset_metadata_ready`<br>[source](https://github.com/EliasMPJunior/ontobdc-wip/blob/fe6d756c44141cdc14234937ce1e659384950b26/src/ontobdc/storage/plugin/capability/transformation/dataset_metadata_ready.py) |
| `DATASET_CONTAINER_INDEX_READY` | `__dataset_container_index_ready__` | The container metadata file contains the dataset entry and remains synchronized with the dataset metadata file. | `org.ontobdc.storage.plugin.capability.transformation.target.dataset_container_index_ready`<br>[source](https://github.com/EliasMPJunior/ontobdc-wip/blob/fe6d756c44141cdc14234937ce1e659384950b26/src/ontobdc/storage/plugin/capability/transformation/dataset_container_index_ready.py) |

## Transition table

| From | To | Guard/condition | Action |
| --- | --- | --- | --- |
| `UNDEFINED` | `INVALID_PATH` | handler.can_transit_to(to_state = DatasetCreateProcessStatePort.INVALID_PATH) | no transition action |
| `UNDEFINED` | `DIRECTORY_READY` | handler.can_transit_to(to_state = DatasetCreateProcessStatePort.DIRECTORY_READY) | handler.perform_state_transition(to_state = DatasetCreateProcessStatePort.DIRECTORY_READY) |
| `DIRECTORY_READY` | `DATASET_METADATA_READY` | handler.can_transit_to(to_state = DatasetCreateProcessStatePort.DATASET_METADATA_READY) | handler.perform_state_transition(to_state = DatasetCreateProcessStatePort.DATASET_METADATA_READY) |
| `DATASET_METADATA_READY` | `DATASET_CONTAINER_INDEX_READY` | handler.can_transit_to(to_state = DatasetCreateProcessStatePort.DATASET_CONTAINER_INDEX_READY) | handler.perform_state_transition(to_state = DatasetCreateProcessStatePort.DATASET_CONTAINER_INDEX_READY) |

## Runtime findings

- `INVALID_PATH` is an actionless terminal branch.
- The successful path is resumable from the directory and metadata checks performed by `DatasetCreateStateEvaluatorAdapter`.
