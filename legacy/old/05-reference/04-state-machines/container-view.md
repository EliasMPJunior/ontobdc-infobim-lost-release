[↑ Back to state-machine inventory](index.md)

# Legacy container view

> **Status:** Legacy and not end-to-end executable from the current tree.

Preserves the pre-Surface container-view state model and adapter shell.

## Audited implementation

- Enum: [ContainerViewProcessState](https://github.com/EliasMPJunior/ontobdc-wip/blob/fe6d756c44141cdc14234937ce1e659384950b26/src/ontobdc/view/domain/machine/state.py)
- YAML: [standard_container_view.yaml](https://github.com/EliasMPJunior/ontobdc-wip/blob/fe6d756c44141cdc14234937ce1e659384950b26/src/ontobdc/view/domain/machine/standard_container_view.yaml) (runtime statechart)
- Executor: [legacy evaluator and transition handler](https://github.com/EliasMPJunior/ontobdc-wip/blob/fe6d756c44141cdc14234937ce1e659384950b26/src/ontobdc/view/adapter/machine.py)

## States from the enum

| State | Raw value | Enum meaning | Capability or executing operation |
| --- | --- | --- | --- |
| `UNDEFINED` | `__undefined__` | No later legacy container view state can be inferred from the current artefacts. | — |
| `DATA_GATHERED` | `__data_gathered__` | The publishing capabilities completed and the data used by the legacy view was materialized. | `org.ontobdc.view.plugin.capability.transformation.target.data_gathered`<br>[source](https://github.com/EliasMPJunior/ontobdc-wip/blob/fe6d756c44141cdc14234937ce1e659384950b26/src/ontobdc/view/plugin/capability/transformation/data_gathered.py)<br>current implementation now returns a Surface state |
| `HARDCODED` | `__hardcoded__` | View-generation operations that have not yet been formalized were executed. | `org.ontobdc.view.plugin.capability.transformation.target.hardcoded`<br>source absent from the audited tree |
| `FACADES_SERIALIZED` | `__facades_serialized__` | Every dataset was materialized through its facade; the contracts and resulting instances were serialized as JSON-LD and embedded in the container view. | `org.ontobdc.view.plugin.capability.transformation.target.facades_serialized`<br>source absent from the audited tree |
| `DATASET_VIEWS_GENERATED` | `__dataset_views_generated__` | The WorkStream and IfcWorkSchedule pages declared by datasets were rendered from Jinja templates. | `org.ontobdc.view.plugin.capability.transformation.target.dataset_views_generated`<br>source absent from the audited tree |
| `GENERATED` | `__generated__` | The requested legacy container view representation was generated. | `org.ontobdc.view.plugin.capability.transformation.target.generated`<br>source absent from the audited tree |

## Transition table

| From | To | Guard/condition | Action |
| --- | --- | --- | --- |
| `UNDEFINED` | `DATA_GATHERED` | handler.can_transit_to(to_state = ContainerViewProcessStatePort.DATA_GATHERED) | handler.perform_state_transition(to_state = ContainerViewProcessStatePort.DATA_GATHERED) |
| `DATA_GATHERED` | `HARDCODED` | handler.can_transit_to(to_state = ContainerViewProcessStatePort.HARDCODED) | handler.perform_state_transition(to_state = ContainerViewProcessStatePort.HARDCODED) |
| `HARDCODED` | `FACADES_SERIALIZED` | handler.can_transit_to(to_state = ContainerViewProcessStatePort.FACADES_SERIALIZED) | handler.perform_state_transition(to_state = ContainerViewProcessStatePort.FACADES_SERIALIZED) |
| `FACADES_SERIALIZED` | `DATASET_VIEWS_GENERATED` | handler.can_transit_to(to_state = ContainerViewProcessStatePort.DATASET_VIEWS_GENERATED) | handler.perform_state_transition(to_state = ContainerViewProcessStatePort.DATASET_VIEWS_GENERATED) |
| `DATASET_VIEWS_GENERATED` | `GENERATED` | handler.can_transit_to(to_state = ContainerViewProcessStatePort.GENERATED) | handler.perform_state_transition(to_state = ContainerViewProcessStatePort.GENERATED) |

## Runtime findings

- The source itself calls this the legacy view. Current publication uses `SurfaceGenerationProcessState` instead.
- The adapter still maps five capability IDs. Four source modules (`hardcoded`, `facades_serialized`, `dataset_views_generated`, `generated`) are absent from the audited tree. The remaining `data_gathered` ID now belongs to the Surface pipeline and returns `SurfaceGenerationProcessState.DATA_GATHERED`.
- Therefore the preserved enum/YAML/adapter is historical code, not a viable alternate current pipeline.
