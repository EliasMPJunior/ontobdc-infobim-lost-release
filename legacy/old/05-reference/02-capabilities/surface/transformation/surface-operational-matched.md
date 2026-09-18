# Surface Operational Matched

`SurfaceOperationalMatchedCapability` supplies the shipped default operation-region Tiles when the caller has not already declared an operation Tile, and embeds the default Surface definitions used by the browser runtime.

| Property | Value |
| --- | --- |
| Capability ID | `org.ontobdc.view.plugin.capability.transformation.target.surface_operational_matched` |
| Capability type | `TransformationCapability` |
| Resulting state | `surface_operational_matched` |
| Implementation | [`surface_operational_matched.py`](https://github.com/EliasMPJunior/ontobdc-view/blob/r008/v0.9/src/ontobdc_view/surface/plugin/capability/transformation/surface_operational_matched.py) |
| Data block | `ontobdc-surface-default-layouts` |
| Bootstrap block | `ontobdc-surface-default-layouts-bootstrap` |

## Inputs and preconditions

The Surface must contain a valid `ontobdc-surface-matches` array. Default layouts are obtained from `SurfaceRdfParser.default_surface_layout()`.

The shipped default layout currently describes the operation-region controls, such as Logo, Language, and Theme. The capability does not read `surface_layouts_path` even though `SurfaceContextAdapter` contains a resolver for that parameter; the active implementation uses the packaged default-layout factory.

## Operation

1. Read and validate the existing matches list.
2. Load the packaged default layouts. Parsing failures and a missing/malformed shipped ontology resource are not caught; they propagate.
3. Detect whether any existing match already targets the `operation` region.
4. If no operation match exists, collect every placement in each `OperationRegion`. A placement whose component has no `rdf:type` raises `ValueError` -- the shipped default layout is expected to always be well-formed, so a hole here is treated as a packaging bug, not a normal case.
5. Resolve each placement with the same Tile-class matching and size-envelope logic used by `SurfaceMatchedCapability`, using an empty RDF graph and strict mode: a placement whose `tileClass` has no registered matching Component raises `ValueError` rather than being silently skipped.
6. Append and normalize the resolved matches.
7. When layouts exist, serialize them with `to_render_payload()`, embed the payload, and embed a module bootstrap that waits for `<onto-presentation-surface>` to be defined before assigning `defaultSurfaceLayouts`.
8. Advance the state marker, write, and check the document.

An explicit operation-region Tile suppresses the addition of all shipped operation defaults, but the default layout definitions are still embedded when available.

## Result

The result contains `surface_path`, `operational_match_count`, `default_layout_count`, and `resulting_state`.

## Satisfaction check

The check requires the `surface_operational_matched` marker, or a later marker, plus all structural requirements of `surface_matched`. It does not verify that the default-layout JSON or bootstrap script was embedded. This means a legal no-layout execution and a missing-layout artifact are indistinguishable to this specific check.

## Failure behavior

Missing or non-list matches, a missing or malformed shipped default-layout resource, a placement with no `rdf:type` on its component, invalid packaged layout payload generation, or a post-write check failure all abort the transition. A default placement with no registered matching Component also aborts the transition -- there is deliberately no fallback here: the shipped Logo/Language/Theme Tiles are packaged together with their layout definition, so a mismatch between them is a real defect, not a case to degrade past silently.

## Tests

Unit tests: [`test_surface_operational_matched.py`](https://github.com/EliasMPJunior/ontobdc-view/blob/r008/v0.9/test/unit/surface/plugin/capability/transformation/test_surface_operational_matched.py).

No mocking: the suite resolves the **real, shipped** default layout (one `DefaultSurfaceLayout`/`PresentationSurface` definition, three operation Tiles -- `onto-logo-tile`, `onto-language-tile`, `onto-theme-tile`) and matches it with the now-strict (`strict=True`) resolution this capability uses after the "no silent fallback" fix described above. It directly imports `DEFAULT_LAYOUTS_BOOTSTRAP_ID`/`DEFAULT_LAYOUTS_SCRIPT_ID` from the capability module to assert on the embedded script tags by name.

**`execute()`**:

| Test | Condition |
| --- | --- |
| `test_adds_the_shipped_operation_defaults_when_none_declared` | With no pre-existing `operation`-region match, the shipped default operation tiles (`onto-logo-tile`, `onto-language-tile`, `onto-theme-tile`) are added, each forced to exactly one row; the default-layout definitions are embedded as both a data script and a bootstrap `<script>`. |
| `test_skips_the_defaults_when_an_operation_match_already_exists` | When an `operation`-region match already exists (e.g. from an earlier, explicit request), the shipped defaults are suppressed -- `operational_match_count == 0` -- while the default-layout definitions are still embedded for client-side layout selection. |
| `test_raises_when_the_matches_script_is_missing` | `ValueError` (matching `"Missing script"`) when the `ontobdc-surface-matches` script tag is entirely absent -- raised by `SurfaceDocumentAdapter.extract_json_script` itself. |
| `test_raises_when_the_matches_script_is_not_a_list` | `ValueError` (matching `"Surface matches are missing or invalid"`) when the script tag exists but does not decode to a list -- raised by the capability's own shape check. This is a distinct failure from the previous test: one is a missing tag, the other is a malformed one. |

**`check()`**:

| Test | Condition |
| --- | --- |
| `test_is_true_after_a_real_execute` | `True` immediately after a real `execute()`. |
| `test_is_false_before_operational_matching_runs` | `False` for a `surface_branded` document that has not yet been operationally matched. |
| `test_is_satisfied_matches_check` | `is_satisfied()` matches `check()`. |

**Labels, descriptions, and registry identity** are covered the same way as every other capability in this package: parametrized `label()`/`description()` delegation to `SurfaceGenerationProcessState.SURFACE_OPERATIONAL_MATCHED`, plus a `METADATA.id` regression guard.

This suite is also the regression guard for the "no silent fallback" fix: before the fix, an unresolved shipped placement was silently skipped (`continue`) and default-layout resolution tolerated a partial match (`strict=False`); both paths now raise instead of degrading quietly, and `test_adds_the_shipped_operation_defaults_when_none_declared` exercises the now-strict resolution against the real shipped layout end to end.
