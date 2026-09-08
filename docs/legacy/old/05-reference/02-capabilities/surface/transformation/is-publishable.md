# Is Publishable

`IsPublishableCapability` synchronizes the container's publication inventory. Its concrete purpose is to make `.__ontobdc__/datapackage.json` describe the same publishable resources that currently exist in the container.

It does **not** publish the container to a server, generate the Presentation Surface, or decide whether the information is suitable for public release. In this state, *publishable* has a narrower technical meaning:

> The container metadata is ready, and the publication descriptor's resource list matches the current Frictionless-compatible source files.

| Property | Value |
| --- | --- |
| Capability ID | `org.ontobdc.view.plugin.capability.transformation.target.is_publishable` |
| Capability type | `TransformationCapability` |
| Resulting state | `is_publishable` |
| Implementation | [`is_publishable.py`](https://github.com/EliasMPJunior/ontobdc-view/blob/r008/v0.9/src/ontobdc_view/surface/plugin/capability/transformation/is_publishable.py) |
| Main collaborator | [`SurfacePublicationAdapter`](https://github.com/EliasMPJunior/ontobdc-view/blob/r008/v0.9/src/ontobdc_view/surface/adapter/publication.py) |
| Main artifact affected | `<container>/.__ontobdc__/datapackage.json` and related RO-Crate metadata |

## Why this capability exists

The files in the container directory and the resources declared in `datapackage.json` can diverge over time. For example, a file may be added, renamed, modified, or deleted while the descriptor still represents the previous state.

The Surface pipeline must not proceed with an obsolete publication inventory. Downstream transformations need a descriptor that can be treated as the current inventory of publishable source resources.

This capability reconciles those two views of the container:

| View | Meaning |
| --- | --- |
| Filesystem inventory | Publishable source files that currently exist inside the container. |
| Descriptor inventory | Local resources currently declared in `.__ontobdc__/datapackage.json`. |

The desired invariant is:

```text
publishable filesystem resources == descriptor resources
```

## Example

Suppose the container contains these publishable source files:

```text
schedule.csv
costs.csv
resources.csv
```

but `datapackage.json` still declares:

```text
schedule.csv
deleted-table.csv
```

The descriptor is stale: `costs.csv` and `resources.csv` are missing, while `deleted-table.csv` no longer exists. Execution synchronizes the descriptor so its resource inventory reflects the current compatible files. Records may be added, updated, or removed.

Files that are not Frictionless-compatible may still belong to the container and its complete RO-Crate inventory. They are excluded only from this Frictionless data-package comparison; this capability does not delete those files from the container.

## `check()` and `execute()` have different roles

The capability name sounds like a Boolean question, but the capability is a transformation. Its two main methods perform different jobs:

| Method | Responsibility |
| --- | --- |
| `check(context)` | Ask whether the publication descriptor is already synchronized with the current publishable files. It does not repair anything. |
| `execute(context)` | Synchronize and normalize the publication descriptor so the container can reach the `is_publishable` state. |
| `is_satisfied(context)` | Return the same result as `check(context)`. |

`execute()` does not call `check()` itself. The state machine uses the capability's check to observe whether the cumulative state is satisfied and uses execution to perform the transition when it is not.

## Satisfaction check

`check()` delegates specifically to `SurfacePublicationAdapter.is_container_publishable(context)` and performs the following evaluation:

1. Resolve `container_path` and confirm that it is an accessible directory.
2. Run the container-metadata readiness check.
3. Build `expected_paths` from the container resources currently found by `ContainerDataPackageSynchronizer.list_resource_paths()`.
4. Keep only resources whose file extension is supported by `FrictionlessFormatRegistry`.
5. Load `.__ontobdc__/datapackage.json` and resolve its local resource paths as `described_paths`.
6. Remove the generated Presentation Surface path from both sets.
7. Return `True` only when `expected_paths` and `described_paths` are equal.

Set equality means that all of the following conditions hold:

- every compatible source file is described;
- every described local resource still exists in the expected inventory;
- no stale descriptor entry remains;
- the generated Surface is not mistaken for one of its own source resources.

The check returns `False` rather than raising when it encounters inaccessible paths, invalid metadata, malformed descriptor JSON, invalid values, or a resource-set mismatch.

## Execution

`execute()` delegates to `SurfacePublicationAdapter.ensure_publishable(context)`:

1. Resolve and validate the container path.
2. Parse the container metadata and require exactly one `obdc:DataContainer`.
3. Resolve the container identifier used in the result.
4. Run `ContainerDataPackageSynchronizer.sync(container_path)` to reconcile local resources with the data-package descriptor.
5. Reapply `ContainerDataPackageFrictionlessValidCapability`'s hotfix, removing descriptor resources whose formats are not Frictionless-compatible.
6. Reapply the RO-Crate synchronization hotfix so the descriptor remains aligned with the same compatible-resource definition used by `container_healthy`.
7. Add `SurfaceGenerationProcessState.IS_PUBLISHABLE` to the returned result as `resulting_state`.

The two hotfixes are necessary because the generic synchronizer is deliberately format-blind. Without the Frictionless pruning step, synchronization could restore incompatible resources that the preceding `container_healthy` stage intentionally removed.

## Result

Execution returns the synchronization report plus the resulting state:

| Field | Meaning |
| --- | --- |
| `container_path` | Resolved absolute container path. |
| `container_id` | Identifier read from the container metadata. |
| `datapackage_path` | Path of the synchronized data-package descriptor. |
| `resource_count` | Resource count reported by the synchronizer. |
| `local_resource_count` | Local resource count reported by the synchronizer. |
| `added_resource_count` | Descriptor resources added during synchronization. |
| `updated_resource_count` | Descriptor resources updated during synchronization. |
| `removed_resource_count` | Descriptor resources removed during synchronization. |
| `resulting_state` | `SurfaceGenerationProcessState.IS_PUBLISHABLE`. |

## Treatment of `index.html`

This capability does not delete, create, or overwrite `index.html`.

The generated Surface is deliberately excluded from both sides of the resource comparison because it is an output of publication, not a source resource. When `surface_path` is absent from the context, the check assumes the generated path is `<container>/index.html` for this exclusion.

The broader `ontobdc view` command does remove an existing Surface before starting the state machine, and `SurfaceInitializedCapability` later creates a fresh HTML document. Those operations happen outside `IsPublishableCapability`.

## What this capability does not do

| It does | It does not |
| --- | --- |
| Synchronize the publication resource inventory. | Upload or expose the container anywhere. |
| Update data-package and related RO-Crate metadata. | Generate `index.html` or any other Surface markup. |
| Filter the expected inventory to Frictionless-compatible formats. | Gather the JSON-LD consumed by the Surface. |
| Detect missing, extra, or stale descriptor resources. | Match data to Tiles or package browser Components. |
| Establish the `is_publishable` pipeline state. | Judge confidentiality, licensing, approval, or business readiness for public release. |

## Preconditions and failure behavior

The context must provide `container_path`, and `context.root_path` must be available to the metadata-validation hotfixes. The state machine reaches this capability only after `container_healthy`.

Execution propagates invalid paths, malformed container metadata, synchronization failures, and storage-validation errors. It does not report partial success as a completed state.

## Tests

Unit tests: [`test_is_publishable.py`](https://github.com/EliasMPJunior/ontobdc-view/blob/r008/v0.9/test/unit/surface/plugin/capability/transformation/test_is_publishable.py).

The unit suite isolates the capability from `SurfacePublicationAdapter` and verifies the capability-level delegation contract:

| Test coverage | Verified behavior |
| --- | --- |
| Positive and negative checks | `check()` returns the adapter's Boolean result. |
| Context identity | The exact context object is forwarded without wrapping or copying. |
| Successful execution | The adapter result is preserved and `resulting_state` is added. |
| Adapter failure | Exceptions from `ensure_publishable()` propagate to the caller. |
| Satisfaction alias | `is_satisfied()` matches `check()`. |
| Labels and descriptions | Values delegate to `SurfaceGenerationProcessState.IS_PUBLISHABLE`. |
| Registry identity | `METADATA.id` matches the identifier used by `CapabilityLoader`. |

These tests mock the adapter. They validate delegation but do not exercise real filesystem synchronization, RDF parsing, Frictionless filtering, or RO-Crate mutation.
