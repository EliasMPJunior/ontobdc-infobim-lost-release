[↑ Back to state-machine inventory](index.md)

# Component Event promotion

> **Status:** Current integrated implementation plus a parallel standalone copy.

Resolves one Component Event through the RDF `view:promotesTo` policy into zero, one, or many Shared Events.

## Audited implementation

- Enum: [EventPromotionProcessState](https://github.com/EliasMPJunior/ontobdc-view/blob/9b1daceb0af79258f641409943c9b2a3b4ccbe86/src/ontobdc_view/dock/domain/machine/event_promotion_state.py)
- YAML: none; transitions are expressed directly in Python
- Executor: [integrated listener used by the Surface bundle](https://github.com/EliasMPJunior/ontobdc-view/blob/9b1daceb0af79258f641409943c9b2a3b4ccbe86/src/ontobdc_view/dock/plugin/listener/presentation_event_promotion.py)
- Executor: [browser runtime packager](https://github.com/EliasMPJunior/ontobdc-view/blob/9b1daceb0af79258f641409943c9b2a3b4ccbe86/src/ontobdc_view/component/adapter/dock.py)
- Executor: [parallel standalone machine](https://github.com/EliasMPJunior/ontobdc-web-dock/blob/1164268618c6877d65ddd377d0d49d772d4f8982/src/ontobdc_web_dock/dock/adapter/machine.py)

## States from the enum

| State | Raw value | Enum meaning | Capability or executing operation |
| --- | --- | --- | --- |
| `UNDEFINED` | `__undefined__` | No promotion pass has started. | No running trace |
| `EVENT_RECEIVED` | `__event_received__` | The dDock accepted a Component Event envelope from the browser bridge. | Listener/machine entry |
| `SEMANTIC_EVENT_RESOLVED` | `__semantic_event_resolved__` | The envelope's occurrence name was resolved against the policy graph to a view:ComponentEvent individual, or found not to be one. | `PromotionPolicy.resolve_component_event()` |
| `PROMOTION_POLICY_EVALUATED` | `__promotion_policy_evaluated__` | view:promotesTo was read from the policy graph for the resolved Component Event. | `PromotionPolicy.promotion_targets()` |
| `PROMOTION_TARGETS_RESOLVED` | `__promotion_targets_resolved__` | Every promotesTo object was resolved to a Shared Event target; zero, one and many targets are all normal outcomes. | All `view:promotesTo` objects retained |
| `RESPONSE_PRODUCED` | `__response_produced__` | The dDock response carrying the resolved targets was handed back to the bridge. | Listener response or machine tuple returned |

## Transition table

| From | To | Guard/condition | Action |
| --- | --- | --- | --- |
| `UNDEFINED` | `EVENT_RECEIVED` | unconditional | listener/machine entry |
| `EVENT_RECEIVED` | `SEMANTIC_EVENT_RESOLVED` | unconditional | resolve_component_event |
| `SEMANTIC_EVENT_RESOLVED` | `RESPONSE_PRODUCED` | component event unresolved | return unresolved response |
| `SEMANTIC_EVENT_RESOLVED` | `PROMOTION_POLICY_EVALUATED` | component event resolved | promotion_targets |
| `PROMOTION_POLICY_EVALUATED` | `PROMOTION_TARGETS_RESOLVED` | unconditional | retain every target |
| `PROMOTION_TARGETS_RESOLVED` | `RESPONSE_PRODUCED` | unconditional | return promoted/not_promoted response |

## Runtime findings

- `ontobdc-view` packages its own `ontobdc_view.dock` sources into the Page as `ontobdc_view_dock`; this is the executor reached by current Surface generation.
- `ontobdc-web-dock@master` carries the same enum contract and a direct `EventPromotionMachine`, but the audited `ontobdc-view` packager does not import that distribution. It is a parallel implementation, not the integrated Surface executor.
- Neither implementation uses a Capability or YAML statechart. The RDF policy in `brasidatacenter` remains the source of promotion decisions.
