[↑ Back to state-machine inventory](index.md)

# Container attachment

> **Status:** Current and executable.

Reconciles an imported container and its datasets with local identities, storage index, and execution context.

## Audited implementation

- Enum: [ContainerAttachProcessState](https://github.com/EliasMPJunior/ontobdc-wip/blob/fe6d756c44141cdc14234937ce1e659384950b26/src/ontobdc/storage/domain/machine/attach_state.py)
- YAML: [standard_container_attach.yaml](https://github.com/EliasMPJunior/ontobdc-wip/blob/fe6d756c44141cdc14234937ce1e659384950b26/src/ontobdc/storage/domain/machine/standard_container_attach.yaml) (runtime statechart)
- Executor: [evaluator and transition handler](https://github.com/EliasMPJunior/ontobdc-wip/blob/fe6d756c44141cdc14234937ce1e659384950b26/src/ontobdc/storage/adapter/attachment/machine.py)

## States from the enum

| State | Raw value | Enum meaning | Capability or executing operation |
| --- | --- | --- | --- |
| `UNDEFINED` | `__undefined__` | No attachment state can be inferred yet. | Entry/error-classification state; no transition capability |
| `CONTAINER_INSPECTED` | `__container_inspected__` | The imported container and its datasets were inspected without changing their metadata. | `org.ontobdc.storage.plugin.capability.transformation.target.container_inspected`<br>[source](https://github.com/EliasMPJunior/ontobdc-wip/blob/fe6d756c44141cdc14234937ce1e659384950b26/src/ontobdc/storage/plugin/capability/transformation/container_inspected.py) |
| `IDENTITY_RESOLVED` | `__identity_resolved__` | The target local identities and locations were calculated and checked for conflicts. | `org.ontobdc.storage.plugin.capability.transformation.target.identity_resolved`<br>[source](https://github.com/EliasMPJunior/ontobdc-wip/blob/fe6d756c44141cdc14234937ce1e659384950b26/src/ontobdc/storage/plugin/capability/transformation/identity_resolved.py) |
| `CONTAINER_METADATA_ATTACHED` | `__container_metadata_attached__` | The container metadata graph uses the target local identity and location. | `org.ontobdc.storage.plugin.capability.transformation.target.container_metadata_attached`<br>[source](https://github.com/EliasMPJunior/ontobdc-wip/blob/fe6d756c44141cdc14234937ce1e659384950b26/src/ontobdc/storage/plugin/capability/transformation/container_metadata_attached.py) |
| `DATASETS_ATTACHED` | `__datasets_attached__` | Every dataset graph and the dataset index inside the container graph use the target identities and locations. | `org.ontobdc.storage.plugin.capability.transformation.target.datasets_attached`<br>[source](https://github.com/EliasMPJunior/ontobdc-wip/blob/fe6d756c44141cdc14234937ce1e659384950b26/src/ontobdc/storage/plugin/capability/transformation/datasets_attached.py) |
| `STORAGE_INDEX_ATTACHED` | `__storage_index_attached__` | The local storage index contains the canonical entry copied from the attached container metadata. | `org.ontobdc.storage.plugin.capability.transformation.target.storage_index_attached`<br>[source](https://github.com/EliasMPJunior/ontobdc-wip/blob/fe6d756c44141cdc14234937ce1e659384950b26/src/ontobdc/storage/plugin/capability/transformation/storage_index_attached.py) |
| `CONTEXT_ATTACHED` | `__context_attached__` | The execution context points to the attached container and no stale update selector remains. | `org.ontobdc.storage.plugin.capability.transformation.target.context_attached`<br>[source](https://github.com/EliasMPJunior/ontobdc-wip/blob/fe6d756c44141cdc14234937ce1e659384950b26/src/ontobdc/storage/plugin/capability/transformation/context_attached.py) |
| `CONTAINER_ATTACHED` | `__container_attached__` | The container, datasets, storage index, and execution context are mutually consistent. | `org.ontobdc.storage.plugin.capability.transformation.target.container_attached`<br>[source](https://github.com/EliasMPJunior/ontobdc-wip/blob/fe6d756c44141cdc14234937ce1e659384950b26/src/ontobdc/storage/plugin/capability/transformation/container_attached.py) |
| `INVALID_CONTAINER_PATH` | `__invalid_container_path__` | The requested path is not an attachable container directory inside the current project root. | Entry/error-classification state; no transition capability |
| `INVALID_CONTAINER_GRAPH` | `__invalid_container_graph__` | The imported container metadata cannot be parsed or does not identify exactly one data container. | Entry/error-classification state; no transition capability |
| `IDENTITY_CONFLICT` | `__identity_conflict__` | The target container or dataset identity conflicts with another local object. | Entry/error-classification state; no transition capability |
| `DATASET_ATTACH_FAILED` | `__dataset_attach_failed__` | A dataset could not be migrated or validated safely. | Entry/error-classification state; no transition capability |
| `STORAGE_INDEX_ATTACH_FAILED` | `__storage_index_attach_failed__` | The local storage index could not be reconciled with the attached container. | Entry/error-classification state; no transition capability |
| `ATTACH_ROLLBACK_FAILED` | `__attach_rollback_failed__` | The original metadata files could not be restored after a failed attachment. | Entry/error-classification state; no transition capability |

## Transition table

| From | To | Guard/condition | Action |
| --- | --- | --- | --- |
| `UNDEFINED` | `CONTAINER_INSPECTED` | handler.can_transit_to(to_state = ContainerAttachProcessStatePort.CONTAINER_INSPECTED) | handler.perform_state_transition(to_state = ContainerAttachProcessStatePort.CONTAINER_INSPECTED) |
| `CONTAINER_INSPECTED` | `IDENTITY_RESOLVED` | handler.can_transit_to(to_state = ContainerAttachProcessStatePort.IDENTITY_RESOLVED) | handler.perform_state_transition(to_state = ContainerAttachProcessStatePort.IDENTITY_RESOLVED) |
| `IDENTITY_RESOLVED` | `CONTAINER_METADATA_ATTACHED` | handler.can_transit_to(to_state = ContainerAttachProcessStatePort.CONTAINER_METADATA_ATTACHED) | handler.perform_state_transition(to_state = ContainerAttachProcessStatePort.CONTAINER_METADATA_ATTACHED) |
| `CONTAINER_METADATA_ATTACHED` | `DATASETS_ATTACHED` | handler.can_transit_to(to_state = ContainerAttachProcessStatePort.DATASETS_ATTACHED) | handler.perform_state_transition(to_state = ContainerAttachProcessStatePort.DATASETS_ATTACHED) |
| `DATASETS_ATTACHED` | `STORAGE_INDEX_ATTACHED` | handler.can_transit_to(to_state = ContainerAttachProcessStatePort.STORAGE_INDEX_ATTACHED) | handler.perform_state_transition(to_state = ContainerAttachProcessStatePort.STORAGE_INDEX_ATTACHED) |
| `STORAGE_INDEX_ATTACHED` | `CONTEXT_ATTACHED` | handler.can_transit_to(to_state = ContainerAttachProcessStatePort.CONTEXT_ATTACHED) | handler.perform_state_transition(to_state = ContainerAttachProcessStatePort.CONTEXT_ATTACHED) |
| `CONTEXT_ATTACHED` | `CONTAINER_ATTACHED` | handler.can_transit_to(to_state = ContainerAttachProcessStatePort.CONTAINER_ATTACHED) | handler.perform_state_transition(to_state = ContainerAttachProcessStatePort.CONTAINER_ATTACHED) |

## Runtime findings

- The YAML contains the success path and lists the error states as final states, but it has no graph transitions into those errors.
- Runtime exceptions are mapped by `AttachmentErrorClassifier`; the handler rolls back when possible and then binds the classified error state directly.
