[↑ Back to state-machine inventory](index.md)

# Entity analysis

> **Status:** Current contract and handler; capability implementations absent.

Compares an analyzed source against registered entity vectors and materializes the scored result.

## Audited implementation

- Enum: [EntityAnalysisProcessState](https://github.com/EliasMPJunior/ontobdc-wip/blob/fe6d756c44141cdc14234937ce1e659384950b26/src/ontobdc/context/domain/machine/learning_state.py)
- YAML: [standard_entity_analysis.yaml](https://github.com/EliasMPJunior/ontobdc-wip/blob/fe6d756c44141cdc14234937ce1e659384950b26/src/ontobdc/context/domain/machine/standard_entity_analysis.yaml) (runtime statechart)
- Executor: [transition handler](https://github.com/EliasMPJunior/ontobdc-wip/blob/fe6d756c44141cdc14234937ce1e659384950b26/src/ontobdc/context/adapter/machine.py)

## States from the enum

| State | Raw value | Enum meaning | Capability or executing operation |
| --- | --- | --- | --- |
| `UNDEFINED` | `__undefined__` | Initial state before the analysis source is identified. | — |
| `IDENTIFIED` | `__identified__` | The source file was identified and stored in the analysis pipeline. | `org.ontobdc.context.plugin.capability.transformation.target.identified`<br>source absent from the audited tree |
| `EXTRACTED` | `__extracted__` | The source file produced extractable text content. | `org.ontobdc.context.plugin.capability.transformation.target.extracted`<br>source absent from the audited tree |
| `SPATIALIZED` | `__spatialized__` | The extracted content was enriched with bounding boxes. | `org.ontobdc.context.plugin.capability.transformation.target.spatialized`<br>source absent from the audited tree |
| `ALIGNED` | `__aligned__` | The spatialized content produced a deterministic aligned vector. | `org.ontobdc.context.plugin.capability.transformation.target.aligned`<br>source absent from the audited tree |
| `ORIGIN_RESOLVED` | `__origin_resolved__` | The registered vector sources were resolved. | `org.ontobdc.context.plugin.capability.transformation.target.origin_resolved`<br>source absent from the audited tree |
| `VECTORS_LOADED` | `__vectors_loaded__` | The registered vector candidates were loaded. | `org.ontobdc.context.plugin.capability.transformation.target.vectors_loaded`<br>source absent from the audited tree |
| `SCORED` | `__scored__` | The loaded vector candidates were scored against the aligned file vector. | `org.ontobdc.context.plugin.capability.transformation.target.scored`<br>source absent from the audited tree |
| `ANALYSED` | `__analysed__` | The aligned content was analysed against available vector candidates. | `org.ontobdc.context.plugin.capability.transformation.target.analysed`<br>source absent from the audited tree |

## Transition table

| From | To | Guard/condition | Action |
| --- | --- | --- | --- |
| `UNDEFINED` | `IDENTIFIED` | handler.can_transit_to(to_state = EntityAnalysisProcessState.IDENTIFIED) | handler.perform_state_transition(to_state = EntityAnalysisProcessState.IDENTIFIED) |
| `IDENTIFIED` | `EXTRACTED` | handler.can_transit_to(to_state = EntityAnalysisProcessState.EXTRACTED) | handler.perform_state_transition(to_state = EntityAnalysisProcessState.EXTRACTED) |
| `EXTRACTED` | `SPATIALIZED` | handler.can_transit_to(to_state = EntityAnalysisProcessState.SPATIALIZED) | handler.perform_state_transition(to_state = EntityAnalysisProcessState.SPATIALIZED) |
| `SPATIALIZED` | `ALIGNED` | handler.can_transit_to(to_state = EntityAnalysisProcessState.ALIGNED) | handler.perform_state_transition(to_state = EntityAnalysisProcessState.ALIGNED) |
| `ALIGNED` | `ORIGIN_RESOLVED` | handler.can_transit_to(to_state = EntityAnalysisProcessState.ORIGIN_RESOLVED) | handler.perform_state_transition(to_state = EntityAnalysisProcessState.ORIGIN_RESOLVED) |
| `ORIGIN_RESOLVED` | `VECTORS_LOADED` | handler.can_transit_to(to_state = EntityAnalysisProcessState.VECTORS_LOADED) | handler.perform_state_transition(to_state = EntityAnalysisProcessState.VECTORS_LOADED) |
| `VECTORS_LOADED` | `SCORED` | handler.can_transit_to(to_state = EntityAnalysisProcessState.SCORED) | handler.perform_state_transition(to_state = EntityAnalysisProcessState.SCORED) |
| `SCORED` | `ANALYSED` | handler.can_transit_to(to_state = EntityAnalysisProcessState.ANALYSED) | handler.perform_state_transition(to_state = EntityAnalysisProcessState.ANALYSED) |

## Runtime findings

- The YAML is executed through `StateWorkerAdapter` by `EntityAnalysisStateTransitionHandler`.
- As with Entity Learning, the dynamically named target capabilities are absent from the audited source tree, so the current repository does not provide an end-to-end run.
