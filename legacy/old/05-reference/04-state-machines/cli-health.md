[↑ Back to state-machine inventory](index.md)

# CLI health

> **Status:** Current and executable.

Runs every bootstrap repair/validation capability on each invocation and records a complete health report.

## Audited implementation

- Enum: [CliHealthProcessState](https://github.com/EliasMPJunior/ontobdc-wip/blob/fe6d756c44141cdc14234937ce1e659384950b26/src/ontobdc/cli/domain/machine/health_state.py)
- YAML: [standard_health.yaml](https://github.com/EliasMPJunior/ontobdc-wip/blob/fe6d756c44141cdc14234937ce1e659384950b26/src/ontobdc/cli/domain/machine/standard_health.yaml) (runtime statechart)
- Executor: [evaluator and transition handler](https://github.com/EliasMPJunior/ontobdc-wip/blob/fe6d756c44141cdc14234937ce1e659384950b26/src/ontobdc/cli/adapter/machine.py)

## States from the enum

| State | Raw value | Enum meaning | Capability or executing operation |
| --- | --- | --- | --- |
| `UNDEFINED` | `__undefined__` | Initial state before any health check has run. | Synthetic/entry state; no capability |
| `ONTOBDC_DIRECTORY_READY` | `__ontobdc_directory_ready__` | The .__ontobdc__ directory exists in the target path. | `org.ontobdc.cli.plugin.capability.transformation.target.ontobdc_directory_ready`<br>[source](https://github.com/EliasMPJunior/ontobdc-wip/blob/fe6d756c44141cdc14234937ce1e659384950b26/src/ontobdc/cli/plugin/capability/transformation/ontobdc_directory_ready.py) |
| `ENGINE_READY` | `__engine_ready__` | The engine entry is present and valid in the bootstrap configuration. | `org.ontobdc.cli.plugin.capability.transformation.target.engine_ready`<br>[source](https://github.com/EliasMPJunior/ontobdc-wip/blob/fe6d756c44141cdc14234937ce1e659384950b26/src/ontobdc/cli/plugin/capability/transformation/engine_ready.py) |
| `STORAGE_INDEX_HEALTHY` | `__storage_index_healthy__` | storage.ttl exists and conforms to the bootstrap checks. | `org.ontobdc.cli.plugin.capability.transformation.target.storage_index_healthy`<br>[source](https://github.com/EliasMPJunior/ontobdc-wip/blob/fe6d756c44141cdc14234937ce1e659384950b26/src/ontobdc/cli/plugin/capability/transformation/storage_index_healthy.py) |
| `EXECUTION_CONTEXT_HEALTHY` | `__execution_context_healthy__` | context.ttl exists and conforms to the bootstrap checks. | `org.ontobdc.cli.plugin.capability.transformation.target.execution_context_healthy`<br>[source](https://github.com/EliasMPJunior/ontobdc-wip/blob/fe6d756c44141cdc14234937ce1e659384950b26/src/ontobdc/cli/plugin/capability/transformation/execution_context_healthy.py) |
| `CONFIG_ADAPTER_READY` | `__config_adapter_ready__` | config.yaml exists and conforms to the bootstrap config contract. | `org.ontobdc.cli.plugin.capability.transformation.target.config_adapter_ready`<br>[source](https://github.com/EliasMPJunior/ontobdc-wip/blob/fe6d756c44141cdc14234937ce1e659384950b26/src/ontobdc/cli/plugin/capability/transformation/config_adapter_ready.py) |
| `BOOTSTRAP_HEALTHY` | `__bootstrap_healthy__` | Every CLI bootstrap capability has been executed and the system is healthy. | Synthetic/entry state; no capability |

## Transition table

| From | To | Guard/condition | Action |
| --- | --- | --- | --- |
| `UNDEFINED` | `ONTOBDC_DIRECTORY_READY` | handler.can_transit_to(to_state = CliHealthProcessStatePort.ONTOBDC_DIRECTORY_READY) | handler.perform_state_transition(to_state = CliHealthProcessStatePort.ONTOBDC_DIRECTORY_READY) |
| `ONTOBDC_DIRECTORY_READY` | `ENGINE_READY` | handler.can_transit_to(to_state = CliHealthProcessStatePort.ENGINE_READY) | handler.perform_state_transition(to_state = CliHealthProcessStatePort.ENGINE_READY) |
| `ENGINE_READY` | `STORAGE_INDEX_HEALTHY` | handler.can_transit_to(to_state = CliHealthProcessStatePort.STORAGE_INDEX_HEALTHY) | handler.perform_state_transition(to_state = CliHealthProcessStatePort.STORAGE_INDEX_HEALTHY) |
| `STORAGE_INDEX_HEALTHY` | `EXECUTION_CONTEXT_HEALTHY` | handler.can_transit_to(to_state = CliHealthProcessStatePort.EXECUTION_CONTEXT_HEALTHY) | handler.perform_state_transition(to_state = CliHealthProcessStatePort.EXECUTION_CONTEXT_HEALTHY) |
| `EXECUTION_CONTEXT_HEALTHY` | `CONFIG_ADAPTER_READY` | handler.can_transit_to(to_state = CliHealthProcessStatePort.CONFIG_ADAPTER_READY) | handler.perform_state_transition(to_state = CliHealthProcessStatePort.CONFIG_ADAPTER_READY) |
| `CONFIG_ADAPTER_READY` | `BOOTSTRAP_HEALTHY` | handler.can_transit_to(to_state = CliHealthProcessStatePort.BOOTSTRAP_HEALTHY) | handler.perform_state_transition(to_state = CliHealthProcessStatePort.BOOTSTRAP_HEALTHY) |

## Runtime findings

- Unlike CLI initialization, the evaluator intentionally starts every run at `UNDEFINED`; health is a full pass, not a resumable filesystem pipeline.
- `BOOTSTRAP_HEALTHY` is synthetic. It is reached after the five capability-backed checks and does not execute another capability.
