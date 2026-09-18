[↑ Back to state-machine inventory](index.md)

# Container update

> **Status:** Current and executable.

Repairs, cleans, and resynchronizes a container and regenerates its existing HTML Surface when present.

## Audited implementation

- Enum: [ContainerUpdateProcessState](https://github.com/EliasMPJunior/ontobdc-wip/blob/fe6d756c44141cdc14234937ce1e659384950b26/src/ontobdc/storage/domain/machine/state.py)
- YAML: [standard_container_update.yaml](https://github.com/EliasMPJunior/ontobdc-wip/blob/fe6d756c44141cdc14234937ce1e659384950b26/src/ontobdc/storage/domain/machine/standard_container_update.yaml) (runtime statechart)
- Executor: [evaluator and transition handler](https://github.com/EliasMPJunior/ontobdc-wip/blob/fe6d756c44141cdc14234937ce1e659384950b26/src/ontobdc/storage/adapter/machine.py)

## States from the enum

| State | Raw value | Enum meaning | Capability or executing operation |
| --- | --- | --- | --- |
| `UNDEFINED` | `__undefined__` | **No English description in the enum.** YAML: Initial state before the target container validity is evaluated. | Entry or structural terminal state; no capability |
| `CONTAINER_INVALID` | `__container_invalid__` | **No English description in the enum.** YAML: The target container is structurally invalid and cannot be updated automatically. | Entry or structural terminal state; no capability |
| `CONTAINER_HEALTHY` | `__container_healthy__` | **No English description in the enum.** YAML: The target container is structurally valid, registered, accessible, and ready for cleanup. | `org.ontobdc.storage.plugin.capability.transformation.target.container_healthy`<br>[source](https://github.com/EliasMPJunior/ontobdc-wip/blob/fe6d756c44141cdc14234937ce1e659384950b26/src/ontobdc/storage/plugin/capability/transformation/container_healthy.py) |
| `CONTAINER_DATASETS_HEALTHY` | `__container_datasets_healthy__` | **No English description in the enum.** YAML: Every dataset registered in the container was checked and repaired where possible. | `org.ontobdc.storage.plugin.capability.transformation.target.container_datasets_healthy`<br>[source](https://github.com/EliasMPJunior/ontobdc-wip/blob/fe6d756c44141cdc14234937ce1e659384950b26/src/ontobdc/storage/plugin/capability/transformation/container_datasets_healthy.py) |
| `CONTAINER_CLEANED` | `__container_cleaned__` | **No English description in the enum.** YAML: Files configured for cleanup are absent from the container. | `org.ontobdc.storage.plugin.capability.transformation.target.container_cleaned`<br>[source](https://github.com/EliasMPJunior/ontobdc-wip/blob/fe6d756c44141cdc14234937ce1e659384950b26/src/ontobdc/storage/plugin/capability/transformation/container_cleaned.py) |
| `CONTAINER_DATAPACKAGE_UPDATED` | `__container_datapackage_updated__` | **No English description in the enum.** YAML: The container Data Package descriptor is synchronized with the current container resources and is valid. | `org.ontobdc.storage.plugin.capability.transformation.target.container_datapackage_updated`<br>[source](https://github.com/EliasMPJunior/ontobdc-wip/blob/fe6d756c44141cdc14234937ce1e659384950b26/src/ontobdc/storage/plugin/capability/transformation/container_datapackage_updated.py) |
| `CONTAINER_RO_CRATE_UPDATED` | `__container_ro_crate_updated__` | **No English description in the enum.** YAML: The container RO-Crate metadata is synchronized with the current container resources and is valid. | `org.ontobdc.storage.plugin.capability.transformation.target.container_ro_crate_updated`<br>[source](https://github.com/EliasMPJunior/ontobdc-wip/blob/fe6d756c44141cdc14234937ce1e659384950b26/src/ontobdc/storage/plugin/capability/transformation/container_ro_crate_updated.py) |
| `CONTAINER_HTML_VIEW_UPDATED` | `__container_html_view_updated__` | **No English description in the enum.** YAML: The existing container index.html was regenerated from the current container data. | `org.ontobdc.storage.plugin.capability.transformation.target.container_html_view_updated`<br>[source](https://github.com/EliasMPJunior/ontobdc-wip/blob/fe6d756c44141cdc14234937ce1e659384950b26/src/ontobdc/storage/plugin/capability/transformation/container_html_view_updated.py) |
| `CONTAINER_UPDATED` | `__container_updated__` | **No English description in the enum.** YAML: The container is healthy and clean, its Data Package and RO-Crate metadata are updated, and an existing HTML view was updated when present. | Entry or structural terminal state; no capability |

## Transition table

| From | To | Guard/condition | Action |
| --- | --- | --- | --- |
| `UNDEFINED` | `CONTAINER_INVALID` | handler.can_transit_to(to_state = ContainerUpdateProcessStatePort.CONTAINER_INVALID) | no transition action |
| `UNDEFINED` | `CONTAINER_HEALTHY` | handler.can_transit_to(to_state = ContainerUpdateProcessStatePort.CONTAINER_HEALTHY) | handler.perform_state_transition(to_state = ContainerUpdateProcessStatePort.CONTAINER_HEALTHY) |
| `CONTAINER_HEALTHY` | `CONTAINER_DATASETS_HEALTHY` | handler.can_transit_to(to_state = ContainerUpdateProcessStatePort.CONTAINER_DATASETS_HEALTHY) | handler.perform_state_transition(to_state = ContainerUpdateProcessStatePort.CONTAINER_DATASETS_HEALTHY) |
| `CONTAINER_DATASETS_HEALTHY` | `CONTAINER_CLEANED` | handler.can_transit_to(to_state = ContainerUpdateProcessStatePort.CONTAINER_CLEANED) | handler.perform_state_transition(to_state = ContainerUpdateProcessStatePort.CONTAINER_CLEANED) |
| `CONTAINER_CLEANED` | `CONTAINER_DATAPACKAGE_UPDATED` | handler.can_transit_to(to_state = ContainerUpdateProcessStatePort.CONTAINER_DATAPACKAGE_UPDATED) | handler.perform_state_transition(to_state = ContainerUpdateProcessStatePort.CONTAINER_DATAPACKAGE_UPDATED) |
| `CONTAINER_DATAPACKAGE_UPDATED` | `CONTAINER_RO_CRATE_UPDATED` | handler.can_transit_to(to_state = ContainerUpdateProcessStatePort.CONTAINER_RO_CRATE_UPDATED) | handler.perform_state_transition(to_state = ContainerUpdateProcessStatePort.CONTAINER_RO_CRATE_UPDATED) |
| `CONTAINER_RO_CRATE_UPDATED` | `CONTAINER_HTML_VIEW_UPDATED` | handler.can_transit_to(to_state = ContainerUpdateProcessStatePort.CONTAINER_HTML_VIEW_UPDATED) | handler.perform_state_transition(to_state = ContainerUpdateProcessStatePort.CONTAINER_HTML_VIEW_UPDATED) |
| `CONTAINER_RO_CRATE_UPDATED` | `CONTAINER_UPDATED` | handler.can_transit_to(to_state = ContainerUpdateProcessStatePort.CONTAINER_UPDATED) | no transition action |
| `CONTAINER_HTML_VIEW_UPDATED` | `CONTAINER_UPDATED` | handler.can_transit_to(to_state = ContainerUpdateProcessStatePort.CONTAINER_UPDATED) | no transition action |

## Runtime findings

- This enum stores only raw values. `StateWorkerAdapter` binds localized labels and descriptions from the YAML at runtime.
- After `CONTAINER_RO_CRATE_UPDATED`, the YAML branches to `CONTAINER_HTML_VIEW_UPDATED` only when `index.html` exists; otherwise it enters `CONTAINER_UPDATED` without executing another capability.
- The HTML update capability invokes the current Surface generation handler, so update and Surface generation are nested rather than duplicated.
