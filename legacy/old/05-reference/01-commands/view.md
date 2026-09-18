[↑ Back to command reference](../README.md)

# `view` commands

The `view` component publishes a single command: the one that generates a container's standalone presentation Surface and opens it.

| Property | Value |
| --- | --- |
| Logical component | `view` |
| Plugin directory | [`src/ontobdc/view/plugin/command/`](https://github.com/EliasMPJunior/ontobdc-wip/tree/master/src/ontobdc/view/plugin/command) |
| Routing token | `view` |
| Commands | 1 |

## `view_generate` — generate and open a container view

| Property | Value |
| --- | --- |
| `METADATA.id` | `view_generate` |
| Class | `ContainerViewCommand` |
| Module | [`view/plugin/command/view.py`](https://github.com/EliasMPJunior/ontobdc-wip/blob/master/src/ontobdc/view/plugin/command/view.py) |
| Response | The Surface-generation response, enriched with view fields |
| State machine | [Surface generation](../04-state-machines/surface-generation.md) |

| Argument | Valued | Default | Accepted values |
| --- | --- | --- | --- |
| `--container-id`, `--container` | yes | resolved from the working directory | An ID, or a filesystem path with `--container`. |
| `--type` | yes | `standard` | `standard` only. |
| `--representation` | yes | `html` | `html` only. |
| `--language` | yes | `en` | Any language tag; declared by the generated view. |

**Routing.** `accepts()` requires `view` as the first token and then walks the remainder in flag/value pairs, rejecting an unknown flag, a repeated flag, a missing value, a value starting with `--`, and an invocation passing **both** container flags. Every flag is optional: bare `ontobdc view` is a valid invocation.

**Validation.** Unlike `ontobdc server` (see [`cli` commands](cli.md)), this command may infer its container. `check()` first deletes any inherited `container_id` and `container_path` from the per-project `context.ttl` — `ContainerIdStrategy` is authoritative only for the current working directory, and a stale value would otherwise silently open a sibling container's view — then runs the strategy and requires the resolved path to be an existing directory, returning `False` when it is not.

`--representation` and `--type` are then validated against their single supported values, raising `ValueError` for anything else, and `container_path`, `view_type`, `representation` and `language` are written to the context.

**Execution.** `run()` clears the artifacts that would otherwise let a failed or previous run leak into this one:

| Removed | Why |
| --- | --- |
| The Surface `index.html` | A prior failure can leave it frozen mid-state. |
| `onto-file-viewer.html` and its `.__ontobdc__/` copy | Left in place, it is inventoried as an ordinary container file and pollutes the RO-Crate file tree with the tool's own artifact. |
| The `DataGatheredCapability` state directory | `DataGatheredCapability.check()` passes whenever the ETL artifact exists, so a leftover makes the machine resume from a stale `DATA_GATHERED` instead of re-running it. |

`SurfaceGenerationStateTransitionHandler` then runs the full Surface generation process. The command requires `index.html` to exist afterwards and raises `FileNotFoundError` when the process finished without producing it.

Finally the generated file is opened as a `file://` URI in the default browser. A browser that does not open is recorded in `runtime_error` rather than raised, and the returned response carries `container_id`, `view_type`, `representation`, `language`, `index_path`, `index_uri`, `browser_opened` and `runtime_error` merged into its content. A non-dict response content is wrapped under a `result` key before merging.

The capabilities executed inside the generation process are documented in the [capability reference](../02-capabilities/index.md), and the structure of the generated pages in the [layout reference](../05-layout/index.md).
