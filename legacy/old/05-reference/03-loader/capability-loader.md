# Capability Loader

`CapabilityLoader` is the runtime discovery mechanism used by OntoBDC to find Capability plugins without maintaining a manual registry.

A Capability becomes available because it follows the plugin convention, is importable, inherits from `Capability`, and publishes valid `CapabilityMetadata`. Consumers resolve it by `METADATA.id`; they do not need to import the concrete Capability class directly.

| Property | Value |
| --- | --- |
| Loader | `CapabilityLoader` |
| Base loader | `PluginLoader` |
| Implementation | [`src/ontobdc/shared/adapter/loader.py`](https://github.com/EliasMPJunior/ontobdc-wip/blob/master/src/ontobdc/shared/adapter/loader.py) |
| Resource name | `capability` |
| Default root package | `ontobdc` |
| Lookup key | `CapabilityMetadata.id` |
| Returned value | Capability class, not an instance |

## Purpose

The loader enforces the architectural rule that capabilities are **published and discovered**, rather than wired together through feature-specific imports.

This matters especially for cross-module reuse. A state machine or another subsystem can request a capability by its global identifier:

```python
capability_type = CapabilityLoader().get(capability_id)
```

The caller depends on the published capability contract and identifier, not on the internal adapter or implementation module that happens to provide it.

The practical consequence is that adding a new Capability normally requires no edit to a central registration table. Placement, inheritance, metadata, and importability are the registration mechanism.

## Discovery convention

For the default `ontobdc` root package, the loader searches domain plugin folders that follow this structure:

```text
ontobdc/
├── <domain>/
│   └── plugin/
│       └── capability/
│           └── ...
└── module/
    └── <domain>/
        └── plugin/
            └── capability/
                └── ...
```

Examples of matching package roots are conceptually:

```text
ontobdc.storage.plugin
ontobdc.context.plugin
ontobdc.view.plugin
ontobdc.module.<module_name>.plugin
```

The loader only adds a domain package when `<domain>/plugin/capability/` physically exists.

Entries whose names start with `.` or `_`, plus `__pycache__`, are ignored while domain folders are scanned.

## Downstream root packages

`CapabilityLoader` can also discover capabilities provided by another installed package:

```python
loader = CapabilityLoader(root_packages=("ontobdc", "infobim"))
```

For downstream packages, the same domain convention is expected:

```text
<root_package>/
└── <domain>/
    └── plugin/
        └── capability/
            └── ...
```

The installed package root is resolved with `importlib.util.find_spec()`.

The special `ontobdc/module/` extension slot applies only to the `ontobdc` root package. Downstream packages are searched from their installed package root and do not receive a parallel `module/` scan.

## Recursive module discovery

Once a `plugin/capability` package is found, `CapabilityLoader` walks its importable modules recursively with `pkgutil.iter_modules()`.

The current recursion depth is capped at 10 levels.

This allows capabilities to be organized below the resource directory instead of requiring every implementation to live directly inside it. For example:

```text
plugin/capability/
├── transformation/
│   ├── target/
│   │   └── container_healthy.py
│   └── source/
└── draw/
    └── logo_as_svg.py
```

Discovery follows Python package structure. A directory that exists on disk but cannot participate as an importable package is not guaranteed to be traversed successfully.

## What qualifies as a Capability

Importing a module is not enough. Every object found in the module is inspected and accepted only when all of the following are true:

1. the object is a class;
2. the class is a subclass of `Capability`;
3. `METADATA` exists;
4. `METADATA` is an instance of `CapabilityMetadata`;
5. `METADATA.id` is non-empty;
6. no previously accepted Capability has the same metadata ID.

Conceptually:

```python
if not inspect.isclass(obj):
    continue

if not issubclass(obj, Capability):
    continue

metadata = getattr(obj, "METADATA", None)
if not isinstance(metadata, CapabilityMetadata):
    continue

if not metadata.id:
    continue
```

Therefore, class naming and file naming are not the registry identity. The published identifier is.

## API

### `CapabilityLoader(root_packages=("ontobdc",))`

Creates a loader configured with one or more package roots.

```python
loader = CapabilityLoader()
```

or:

```python
loader = CapabilityLoader(
    root_packages=("ontobdc", "infobim"),
)
```

Root packages are evaluated in the order supplied.

### `get_all(resource="capability")`

Returns all discovered Capability classes that satisfy the discovery contract.

```python
capability_types = CapabilityLoader().get_all()
```

The loader returns **classes**. It does not instantiate or execute them.

### `get(id)`

Returns the discovered Capability class whose `METADATA.id` exactly equals the requested identifier:

```python
capability_type = CapabilityLoader().get(
    "org.ontobdc.storage.plugin.capability.transformation.target.container_healthy"
)
```

Lookup is an exact string comparison.

If no matching Capability is found, the method returns `None`.

## Duplicate IDs

`CapabilityLoader` keeps a set of capability IDs while discovering classes.

If another valid Capability publishes an ID that has already been accepted, the later class is ignored:

```text
first discovered class with ID X  -> accepted
later discovered class with ID X  -> skipped
```

This behavior makes `METADATA.id` effectively a global registry key across all configured root packages.

Because root packages are processed in configuration order, that order can affect which implementation wins when duplicate IDs exist. Duplicate published IDs should therefore be treated as a configuration or packaging error, not as an intended override mechanism.

## Discovery order

There are several ordering rules worth distinguishing:

| Level | Ordering behavior |
| --- | --- |
| Root packages | Tuple order supplied to `CapabilityLoader`. |
| Domain directories | Sorted filesystem entry names. |
| Recursive package walk | `pkgutil.iter_modules()` traversal order. |
| Members inside a module | `inspect.getmembers()` ordering. |

Consumers should not rely on `get_all()` as a semantic execution order. State machines and other orchestration code must define execution order independently.

## Failure behavior

Discovery is deliberately tolerant of unavailable plugin candidates.

### Package-root and directory failures

If the OntoBDC script directory cannot be resolved, or directory scanning fails, the affected scan returns no plugin packages.

For downstream roots, a package that cannot be resolved by `find_spec()` contributes no capabilities.

### Plugin package import failure

If a discovered domain plugin package cannot be imported, it is skipped.

### Capability resource package import failure

If `<plugin_package>.capability` cannot be imported, it is skipped.

### Individual module failure

If a module below `plugin/capability` raises during import or inspection, the loader writes an error to `stderr` and continues discovering other modules:

```text
[CapabilityLoader] Error loading module <module>: <error>
```

A broken capability module therefore does not automatically prevent unrelated capabilities from being discovered.

This tolerance is useful for partial plugin availability, but it also means that callers must treat `get(id) is None` as a real runtime possibility.

## Relationship with `PluginLoader`

`CapabilityLoader` specializes the generic `PluginLoader` in two ways:

1. it fixes the resource type to `capability`;
2. it adds Capability-specific validation and duplicate-ID handling.

The inherited `PluginLoader.get(resource, id)` performs the final lookup by reading each discovered class's `METADATA.id` and comparing it with the requested ID.

The generic loader also provides the shared filesystem/package discovery helpers used by other loaders such as `ComponentLoader` and `ParameterLoader`.

## Relationship with state machines

OntoBDC state machines use `CapabilityLoader` as a runtime boundary between orchestration and implementation.

Typical flow:

```text
state machine
    ↓
resolve capability ID for a state/transition
    ↓
CapabilityLoader.get(id)
    ↓
Capability class
    ↓
CapabilityExecutor / orchestration layer
    ↓
check / execute / satisfaction behavior
```

The loader itself does not decide whether a capability should run, does not evaluate its state, and does not call `check()` or `execute()`.

Its responsibility ends at discovering and returning the class.

## What the loader does not do

| It does | It does not |
| --- | --- |
| Discover Capability classes dynamically. | Instantiate capabilities. |
| Search configured package roots. | Execute capability behavior. |
| Enforce inheritance from `Capability`. | Validate business semantics. |
| Validate `CapabilityMetadata` type and non-empty ID. | Validate every field inside the capability contract. |
| Resolve a class by exact metadata ID. | Infer IDs from file names or class names. |
| Suppress duplicate IDs after the first discovery. | Provide an intentional override/priority system. |
| Continue after individual broken modules. | Guarantee that every filesystem module loads successfully. |

## Authoring a discoverable Capability

A Capability intended for automatic discovery should satisfy this checklist:

```text
[ ] Located below <domain>/plugin/capability/
[ ] Importable as part of the package tree
[ ] Concrete class inherits from Capability
[ ] Class exposes METADATA
[ ] METADATA is CapabilityMetadata
[ ] METADATA.id is a non-empty globally unique string
[ ] Module imports without raising
```

No central registry edit should be necessary.

## Example

Given:

```text
ontobdc/
└── storage/
    └── plugin/
        └── capability/
            └── transformation/
                └── target/
                    └── container_healthy.py
```

and a class conceptually declared as:

```python
class ContainerHealthyCapability(Capability):
    METADATA = CapabilityMetadata(
        id="org.ontobdc.storage.plugin.capability.transformation.target.container_healthy",
        ...
    )
```

then:

```python
loader = CapabilityLoader()

capability_type = loader.get(
    "org.ontobdc.storage.plugin.capability.transformation.target.container_healthy"
)
```

can resolve the class without importing `container_healthy.py` in the caller.

## Testing guidelines

Tests for the loader should validate the discovery contract rather than merely checking that one known production capability happens to load.

| Test coverage | Expected behavior |
| --- | --- |
| Valid Capability | A subclass with valid `CapabilityMetadata.id` is returned by `get_all()`. |
| ID lookup | `get(id)` returns the class whose metadata ID exactly matches. |
| Missing ID | `get(id)` returns `None`. |
| Non-Capability class | Ignored. |
| Invalid metadata type | Ignored. |
| Empty metadata ID | Ignored. |
| Duplicate IDs | Only the first discovered class is returned. |
| Nested capability package | Discovered within the supported recursive depth. |
| Broken module | Error is reported to `stderr`; other valid modules are still discovered. |
| Multiple roots | Capabilities from each configured root package are discoverable. |
| Downstream package absent | The missing root contributes no capabilities and does not break the remaining scan. |
| `ontobdc/module` extension | Capabilities under the OntoBDC module slot are discovered. |

Tests should isolate discovery fixtures in temporary package trees or controlled import fixtures where possible. They should not depend on the complete set or ordering of production capabilities, because adding an unrelated plugin would otherwise make the loader tests brittle.
