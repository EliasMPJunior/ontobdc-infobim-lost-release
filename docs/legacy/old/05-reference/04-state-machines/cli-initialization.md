[↑ Back to state-machine inventory](index.md)

# CLI initialization

> **Status:** Current and executable.

Creates and validates the local OntoBDC bootstrap artifacts, resuming from the latest observable state.

## Audited implementation

- Enum: [CliInitProcessState](https://github.com/EliasMPJunior/ontobdc-wip/blob/fe6d756c44141cdc14234937ce1e659384950b26/src/ontobdc/cli/domain/machine/state.py)
- YAML: [standard_init.yaml](https://github.com/EliasMPJunior/ontobdc-wip/blob/fe6d756c44141cdc14234937ce1e659384950b26/src/ontobdc/cli/domain/machine/standard_init.yaml) (runtime statechart)
- Executor: [evaluator and transition handler](https://github.com/EliasMPJunior/ontobdc-wip/blob/fe6d756c44141cdc14234937ce1e659384950b26/src/ontobdc/cli/adapter/machine.py)

## States from the enum

| State | Raw value | Enum meaning | Capability or executing operation |
| --- | --- | --- | --- |
| `UNDEFINED` | `__undefined__` | Initial state before any init step is executed. | — |
| `ONTOBDC_DIRECTORY_READY` | `__ontobdc_directory_ready__` | The command target directory contains the .__ontobdc__ directory. | `org.ontobdc.cli.plugin.capability.transformation.target.ontobdc_directory_ready`<br>[source](https://github.com/EliasMPJunior/ontobdc-wip/blob/fe6d756c44141cdc14234937ce1e659384950b26/src/ontobdc/cli/plugin/capability/transformation/ontobdc_directory_ready.py) |
| `ENGINE_READY` | `__engine_ready__` | The configured engine is available in the project configuration. | `org.ontobdc.cli.plugin.capability.transformation.target.engine_ready`<br>[source](https://github.com/EliasMPJunior/ontobdc-wip/blob/fe6d756c44141cdc14234937ce1e659384950b26/src/ontobdc/cli/plugin/capability/transformation/engine_ready.py) |
| `STORAGE_INDEX_HEALTHY` | `__storage_index_healthy__` | The storage.ttl file exists and conforms to the bootstrap checks. | `org.ontobdc.cli.plugin.capability.transformation.target.storage_index_healthy`<br>[source](https://github.com/EliasMPJunior/ontobdc-wip/blob/fe6d756c44141cdc14234937ce1e659384950b26/src/ontobdc/cli/plugin/capability/transformation/storage_index_healthy.py) |
| `EXECUTION_CONTEXT_HEALTHY` | `__execution_context_healthy__` | The context.ttl file exists and conforms to the bootstrap checks. | `org.ontobdc.cli.plugin.capability.transformation.target.execution_context_healthy`<br>[source](https://github.com/EliasMPJunior/ontobdc-wip/blob/fe6d756c44141cdc14234937ce1e659384950b26/src/ontobdc/cli/plugin/capability/transformation/execution_context_healthy.py) |
| `CONFIG_ADAPTER_READY` | `__config_adapter_ready__` | The config.yaml file exists and conforms to the bootstrap config contract. | `org.ontobdc.cli.plugin.capability.transformation.target.config_adapter_ready`<br>[source](https://github.com/EliasMPJunior/ontobdc-wip/blob/fe6d756c44141cdc14234937ce1e659384950b26/src/ontobdc/cli/plugin/capability/transformation/config_adapter_ready.py) |
| `BRAND_READY` | `__brand_ready__` | The brand entry (name, mark_svg, logotype_svg, slogan) is available in the project configuration. | `org.ontobdc.cli.plugin.capability.transformation.target.brand_ready`<br>[source](https://github.com/EliasMPJunior/ontobdc-wip/blob/fe6d756c44141cdc14234937ce1e659384950b26/src/ontobdc/cli/plugin/capability/transformation/brand_ready.py) |

## Transition table

| From | To | Guard/condition | Action |
| --- | --- | --- | --- |
| `UNDEFINED` | `ONTOBDC_DIRECTORY_READY` | handler.can_transit_to(to_state = CliInitProcessStatePort.ONTOBDC_DIRECTORY_READY) | handler.perform_state_transition(to_state = CliInitProcessStatePort.ONTOBDC_DIRECTORY_READY) |
| `ONTOBDC_DIRECTORY_READY` | `ENGINE_READY` | handler.can_transit_to(to_state = CliInitProcessStatePort.ENGINE_READY) | handler.perform_state_transition(to_state = CliInitProcessStatePort.ENGINE_READY) |
| `ENGINE_READY` | `STORAGE_INDEX_HEALTHY` | handler.can_transit_to(to_state = CliInitProcessStatePort.STORAGE_INDEX_HEALTHY) | handler.perform_state_transition(to_state = CliInitProcessStatePort.STORAGE_INDEX_HEALTHY) |
| `STORAGE_INDEX_HEALTHY` | `EXECUTION_CONTEXT_HEALTHY` | handler.can_transit_to(to_state = CliInitProcessStatePort.EXECUTION_CONTEXT_HEALTHY) | handler.perform_state_transition(to_state = CliInitProcessStatePort.EXECUTION_CONTEXT_HEALTHY) |
| `EXECUTION_CONTEXT_HEALTHY` | `CONFIG_ADAPTER_READY` | handler.can_transit_to(to_state = CliInitProcessStatePort.CONFIG_ADAPTER_READY) | handler.perform_state_transition(to_state = CliInitProcessStatePort.CONFIG_ADAPTER_READY) |
| `CONFIG_ADAPTER_READY` | `BRAND_READY` | handler.can_transit_to(to_state = CliInitProcessStatePort.BRAND_READY) | handler.perform_state_transition(to_state = CliInitProcessStatePort.BRAND_READY) |

## Runtime findings

- `CliInitStateEvaluatorAdapter` inspects the filesystem and returns the latest satisfied cumulative state.
- `CliInitStateTransitionHandler` resolves one target capability per missing state through `CapabilityLoader` and executes it with `CapabilityExecutor`.
