[↑ Back to state-machine inventory](index.md)

# A3 intent resolution

> **Status:** Current OntoBDC extension and executable.

Receives, normalizes, parses, matches, and validates a prompt intent for capability selection.

## Audited implementation

- Enum: [IntentResolutionState](https://github.com/EliasMPJunior/ontobdc-a3/blob/acb815bf7b39a5f2c429481fb6bd9cb6206645a4/src/ontobdc_a3/prompt/domain/machine/state.py)
- YAML: [standard_intent_resolution.yaml](https://github.com/EliasMPJunior/ontobdc-a3/blob/acb815bf7b39a5f2c429481fb6bd9cb6206645a4/src/ontobdc_a3/prompt/domain/machine/standard_intent_resolution.yaml) (runtime statechart)
- Executor: [evaluator and transition handler](https://github.com/EliasMPJunior/ontobdc-a3/blob/acb815bf7b39a5f2c429481fb6bd9cb6206645a4/src/ontobdc_a3/prompt/adapter/machine.py)

## States from the enum

| State | Raw value | Enum meaning | Capability or executing operation |
| --- | --- | --- | --- |
| `UNDEFINED` | `__undefined__` | Initial state before intent resolution begins. | — |
| `RECEIVED` | `__received__` | The prompt has been received. | `org.ontobdc.a3.prompt.plugin.capability.transformation.target.received`<br>[source](https://github.com/EliasMPJunior/ontobdc-a3/blob/acb815bf7b39a5f2c429481fb6bd9cb6206645a4/src/ontobdc_a3/prompt/plugin/capability/transformation/received.py) |
| `LANGUAGE_DEFINED` | `__language_defined__` | The prompt's language is confirmed to be one a3 recognizes. | `org.ontobdc.a3.prompt.plugin.capability.transformation.target.language_defined`<br>[source](https://github.com/EliasMPJunior/ontobdc-a3/blob/acb815bf7b39a5f2c429481fb6bd9cb6206645a4/src/ontobdc_a3/prompt/plugin/capability/transformation/language_defined.py) |
| `CANONICAL` | `__canonical__` | The prompt has been normalized to a stable canonical form. | `org.ontobdc.a3.prompt.plugin.capability.transformation.target.canonical`<br>[source](https://github.com/EliasMPJunior/ontobdc-a3/blob/acb815bf7b39a5f2c429481fb6bd9cb6206645a4/src/ontobdc_a3/prompt/plugin/capability/transformation/canonical.py) |
| `PARSED` | `__parsed__` | The canonical intent has been parsed (POS tags, entities, dependencies, root) and scored. | `org.ontobdc.a3.prompt.plugin.capability.transformation.target.parsed`<br>[source](https://github.com/EliasMPJunior/ontobdc-a3/blob/acb815bf7b39a5f2c429481fb6bd9cb6206645a4/src/ontobdc_a3/prompt/plugin/capability/transformation/parsed.py) |
| `LOW_CONFIDENCE` | `__low_confidence__` | The parsed score was insufficient; capability tag matching was attempted from the parsed intent's noun root. | `org.ontobdc.a3.prompt.plugin.capability.transformation.target.low_confidence`<br>[source](https://github.com/EliasMPJunior/ontobdc-a3/blob/acb815bf7b39a5f2c429481fb6bd9cb6206645a4/src/ontobdc_a3/prompt/plugin/capability/transformation/low_confidence.py) |
| `MATCHED` | `__matched__` | The parsed score was sufficient; candidate capabilities were matched by tag directly from the parsed intent's noun root. | `org.ontobdc.a3.prompt.plugin.capability.transformation.target.matched`<br>[source](https://github.com/EliasMPJunior/ontobdc-a3/blob/acb815bf7b39a5f2c429481fb6bd9cb6206645a4/src/ontobdc_a3/prompt/plugin/capability/transformation/matched.py) |
| `VALIDATED` | `__validated__` | The user confirmed which matched capability they meant; intent resolution stops here for now. | `org.ontobdc.a3.prompt.plugin.capability.transformation.target.validated`<br>[source](https://github.com/EliasMPJunior/ontobdc-a3/blob/acb815bf7b39a5f2c429481fb6bd9cb6206645a4/src/ontobdc_a3/prompt/plugin/capability/transformation/validated.py) |

## Transition table

| From | To | Guard/condition | Action |
| --- | --- | --- | --- |
| `UNDEFINED` | `RECEIVED` | handler.can_transit_to(to_state = IntentResolutionStatePort.RECEIVED) | handler.perform_state_transition(to_state = IntentResolutionStatePort.RECEIVED) |
| `RECEIVED` | `LANGUAGE_DEFINED` | handler.can_transit_to(to_state = IntentResolutionStatePort.LANGUAGE_DEFINED) | handler.perform_state_transition(to_state = IntentResolutionStatePort.LANGUAGE_DEFINED) |
| `LANGUAGE_DEFINED` | `CANONICAL` | handler.can_transit_to(to_state = IntentResolutionStatePort.CANONICAL) | handler.perform_state_transition(to_state = IntentResolutionStatePort.CANONICAL) |
| `CANONICAL` | `PARSED` | handler.can_transit_to(to_state = IntentResolutionStatePort.PARSED) | handler.perform_state_transition(to_state = IntentResolutionStatePort.PARSED) |
| `PARSED` | `MATCHED` | handler.intent_score_is_sufficient() and handler.can_transit_to(to_state = IntentResolutionStatePort.MATCHED) | handler.perform_state_transition(to_state = IntentResolutionStatePort.MATCHED) |
| `PARSED` | `LOW_CONFIDENCE` | handler.intent_score_is_insufficient() and handler.can_transit_to(to_state = IntentResolutionStatePort.LOW_CONFIDENCE) | handler.perform_state_transition(to_state = IntentResolutionStatePort.LOW_CONFIDENCE) |
| `LOW_CONFIDENCE` | `VALIDATED` | handler.intent_score_is_sufficient() and handler.can_transit_to(to_state = IntentResolutionStatePort.VALIDATED) | handler.perform_state_transition(to_state = IntentResolutionStatePort.VALIDATED) |
| `MATCHED` | `VALIDATED` | handler.intent_score_is_sufficient() and handler.can_transit_to(to_state = IntentResolutionStatePort.VALIDATED) | handler.perform_state_transition(to_state = IntentResolutionStatePort.VALIDATED) |

## Runtime findings

- This is an explicit current state machine even though its enum is named `IntentResolutionState` rather than ending in `ProcessState`; it is listed separately from the strict `*ProcessState` inventory.
- After `PARSED`, mutually exclusive score guards route to `MATCHED` or `LOW_CONFIDENCE`; both paths converge on `VALIDATED`.
- The older `RunIntentResolutionState` and `capability_intent_resolution.yaml` live under `prompt/old/` and are classified as legacy, not as a second active machine.
