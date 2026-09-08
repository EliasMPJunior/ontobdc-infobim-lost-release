# Server Launcher Generated

`ServerLauncherGeneratedCapability` currently advances the final Surface state without generating a server launcher.

| Property | Value |
| --- | --- |
| Capability ID | `org.ontobdc.view.plugin.capability.transformation.target.server_launcher_generated` |
| Capability type | `TransformationCapability` |
| Resulting state | `server_launcher_generated` |
| Implementation | [`server_launcher_generated.py`](https://github.com/EliasMPJunior/ontobdc-view/blob/r008/v0.9/src/ontobdc_view/surface/plugin/capability/transformation/server_launcher_generated.py) |
| Current status | Marker-only placeholder |

## Declared purpose

The metadata declares that the capability generates `server.cmd` beside `index.html`, chooses a shared host/port reference, and embeds that reference into every generated HTML page so a Windows user can start `ontobdc server` by double-clicking the launcher.

## Current operation

The active implementation does none of those artifact operations. It:

1. reads the Surface document;
2. sets the state marker to `server_launcher_generated`;
3. writes the Surface and verifies the marker;
4. returns the Surface path and resulting state.

No `server.cmd` is created and no `ontobdc-server-reference` script is embedded.

## Satisfaction check

The check is intentionally marker-only to remain consistent with the placeholder execution. A marker at `server_launcher_generated` passes. It does not inspect the filesystem or generated pages.

## Restoration boundary

The capability docstring points to `ontobdc/old/view/plugin/capability/transformation/server_launcher_generated.py` as the implementation to restore. Its former artifact-level check must be restored in the same change; restoring only the stronger check would make the current marker-only execution permanently fail.

Until that migration occurs, this final state means only that the state machine reached its terminal marker, not that a local server launcher exists.

## Tests

Unit tests: [`test_server_launcher_generated.py`](https://github.com/EliasMPJunior/ontobdc-view/blob/r008/v0.9/test/unit/surface/plugin/capability/transformation/test_server_launcher_generated.py).

Matches the currently nulled-out `execute()` (see the class docstring): no `server.cmd` or per-page `ontobdc-server-reference` script exists yet to test, so the suite verifies only the marker-advance contract, against a real, minimal `surface_initialized` fixture -- no mocking. This is the final state in the pipeline, so there is no later marker to exercise the cumulative-check behavior against here (that is already covered elsewhere in this package, e.g. by `test_entity_views_published.py`).

**`execute()`**:

| Test | Condition |
| --- | --- |
| `test_marks_the_document_reached_without_writing_any_launcher_artifact` | The result contains exactly `resulting_state` and `surface_path` (no launcher-specific fields yet), the state marker advances to `server_launcher_generated`, and no `server.cmd` is written to the container. |

**`check()`**:

| Test | Condition |
| --- | --- |
| `test_is_true_after_a_real_execute` | `True` immediately after a real `execute()`. |
| `test_is_false_before_the_state_is_reached` | `False` for a document that has not yet reached `server_launcher_generated`. |
| `test_is_satisfied_matches_check` | `is_satisfied()` matches `check()`. |

**Labels, descriptions, and registry identity** are covered the same way as every other capability in this package: parametrized `label()`/`description()` delegation to `SurfaceGenerationProcessState.SERVER_LAUNCHER_GENERATED`, plus a `METADATA.id` regression guard.

This suite will need a real `server.cmd`-writing fixture and per-page reference-script assertions once the real implementation is restored from `ontobdc/old/view/plugin/capability/transformation/server_launcher_generated.py`.
