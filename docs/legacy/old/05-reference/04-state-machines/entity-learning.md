[↑ Back to state-machine inventory](index.md)

# Entity learning

> **Status:** Current contract and handler; capability implementations absent.

Builds a deterministic entity-learning profile and publishes the result into `context.ttl`.

## Audited implementation

- Enum: [EntityLearningProcessState](https://github.com/EliasMPJunior/ontobdc-wip/blob/fe6d756c44141cdc14234937ce1e659384950b26/src/ontobdc/context/domain/machine/learning_state.py)
- YAML: [standard_entity_learning.yaml](https://github.com/EliasMPJunior/ontobdc-wip/blob/fe6d756c44141cdc14234937ce1e659384950b26/src/ontobdc/context/domain/machine/standard_entity_learning.yaml) (runtime statechart)
- Executor: [transition handler](https://github.com/EliasMPJunior/ontobdc-wip/blob/fe6d756c44141cdc14234937ce1e659384950b26/src/ontobdc/context/adapter/machine.py)

## States from the enum

| State | Raw value | Enum meaning | Capability or executing operation |
| --- | --- | --- | --- |
| `UNDEFINED` | `__undefined__` | Initial state before the learning source is identified. | — |
| `IDENTIFIED` | `__identified__` | The source file was identified and stored in the learning pipeline. | `org.ontobdc.context.plugin.capability.transformation.target.identified`<br>source absent from the audited tree |
| `EXTRACTED` | `__extracted__` | The source file produced extractable text content. | `org.ontobdc.context.plugin.capability.transformation.target.extracted`<br>source absent from the audited tree |
| `SPATIALIZED` | `__spatialized__` | The extracted content was enriched with bounding boxes. | `org.ontobdc.context.plugin.capability.transformation.target.spatialized`<br>source absent from the audited tree |
| `ALIGNED` | `__aligned__` | The spatialized content produced a deterministic aligned vector. | `org.ontobdc.context.plugin.capability.transformation.target.aligned`<br>source absent from the audited tree |
| `PUBLISHED` | `__published__` | The learning result was published into context.ttl. | `org.ontobdc.context.plugin.capability.transformation.target.published`<br>source absent from the audited tree |

## Transition table

| From | To | Guard/condition | Action |
| --- | --- | --- | --- |
| `UNDEFINED` | `IDENTIFIED` | handler.can_transit_to(to_state = EntityLearningProcessState.IDENTIFIED) | handler.perform_state_transition(to_state = EntityLearningProcessState.IDENTIFIED) |
| `IDENTIFIED` | `EXTRACTED` | handler.can_transit_to(to_state = EntityLearningProcessState.EXTRACTED) | handler.perform_state_transition(to_state = EntityLearningProcessState.EXTRACTED) |
| `EXTRACTED` | `SPATIALIZED` | handler.can_transit_to(to_state = EntityLearningProcessState.SPATIALIZED) | handler.perform_state_transition(to_state = EntityLearningProcessState.SPATIALIZED) |
| `SPATIALIZED` | `ALIGNED` | handler.can_transit_to(to_state = EntityLearningProcessState.ALIGNED) | handler.perform_state_transition(to_state = EntityLearningProcessState.ALIGNED) |
| `ALIGNED` | `PUBLISHED` | handler.can_transit_to(to_state = EntityLearningProcessState.PUBLISHED) | handler.perform_state_transition(to_state = EntityLearningProcessState.PUBLISHED) |

## Runtime findings

- The YAML is executed through `StateWorkerAdapter` by `EntityLearningStateTransitionHandler`.
- The handler derives the target capability ID from each state, but `src/ontobdc/context/plugin/capability/transformation/` does not exist in the audited tree. The machine is therefore not end-to-end executable from this source snapshot alone.
