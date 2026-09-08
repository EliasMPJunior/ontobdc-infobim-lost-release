# Surface Assembled

`SurfaceAssembledCapability` converts the abstract matches list into the actual custom-element markup hosted by `<onto-presentation-surface>`.

| Property | Value |
| --- | --- |
| Capability ID | `org.ontobdc.view.plugin.capability.transformation.target.surface_assembled` |
| Capability type | `TransformationCapability` |
| Resulting state | `surface_assembled` |
| Implementation | [`surface_assembled.py`](https://github.com/EliasMPJunior/ontobdc-view/blob/r008/v0.9/src/ontobdc_view/surface/plugin/capability/transformation/surface_assembled.py) |

## Inputs and preconditions

The HTML document must contain a matches script whose decoded value is a list. Every item is expected to have already passed match normalization and therefore provide a valid Tile tag, region, and complete size envelope.

## Operation

For each match, `SurfaceDocumentAdapter.assemble_surface_markup()` creates one custom element with these mappings:

| Match field | HTML representation |
| --- | --- |
| `region` | `surface-region` |
| `minColumns` | `min-columns` |
| `preferredColumns` | `columns` |
| `maxColumns` | `max-columns` |
| `minRows` | `min-rows` |
| `preferredRows` | `rows` |
| `maxRows` | `max-rows` |
| `data` | `data-ontobdc-resource`, when present |
| `closed` | `data-tile-closed="true"`, when truthy |

The generated Tiles replace the content of the existing Surface host. The host receives `data-ontobdc-assembled="true"`, the cumulative state marker advances, and the document is written and checked.

The capability does not calculate final pixel positions. It materializes the Components and their constraints; the browser Surface runtime performs responsive placement.

## Result

The stable result fields are `surface_path`, `tile_count`, and `resulting_state`. `_dbg_*` fields expose timing and check metrics used to diagnose large-Surface performance and are not a stable interface.

## Satisfaction check

The check first validates every prior embedded layer. If default layouts are present, they must be a list of objects containing `iri`. It then requires the assembled marker attribute and verifies that every abstract match has a corresponding custom element with the expected tag, region, and, when supplied, resource URI.

The tile verification builds one lookup table from a single scan of the Surface markup. This avoids the former `matches × document-size` regex behavior on large generated pages and correctly supports many Tiles sharing the same tag and region but carrying different resource URIs.

## Failure behavior

A missing or invalid matches list, malformed HTML that cannot accept the assembled host, or any mismatch between the matches data and generated custom elements aborts the transition.

## Tests

Unit tests: [`test_surface_assembled.py`](https://github.com/EliasMPJunior/ontobdc-view/blob/r008/v0.9/test/unit/surface/plugin/capability/transformation/test_surface_assembled.py).

No mocking: the suite asserts on the exact markup `SurfaceDocumentAdapter.assemble_surface_markup` produces for a single content-region match, down to the literal tile-element attribute string.

**`execute()`**:

| Test | Condition |
| --- | --- |
| `test_assembles_matched_tiles_into_the_surface_markup` | A single `content`-region match for `onto-data-container-tile` (columns 1/4/6, rows 2/2/2) is assembled into the exact expected `<onto-data-container-tile surface-region="content" min-columns="1" columns="4" max-columns="6" min-rows="2" rows="2" max-rows="2" data-ontobdc-resource="urn:test:container:1">` markup; the surface is marked `data-ontobdc-assembled="true"` and the state marker advances to `surface_assembled`. |
| `test_produces_zero_tiles_for_an_empty_matches_list` | An empty matches list still marks the surface `data-ontobdc-assembled="true"` and reports `tile_count == 0`. |
| `test_raises_when_the_matches_script_is_not_a_list` | `ValueError` (matching `"Surface matches are missing or invalid"`) when the `ontobdc-surface-matches` script decodes to something other than a list (e.g. a dict). |

**`check()`**:

| Test | Condition |
| --- | --- |
| `test_is_true_after_a_real_execute` | `True` immediately after a real `execute()`. |
| `test_is_false_before_assembly_runs` | `False` for a `surface_matched` document that has not yet been assembled. |
| `test_is_satisfied_matches_check` | `is_satisfied()` matches `check()`. |

**Labels, descriptions, and registry identity** are covered the same way as every other capability in this package: parametrized `label()`/`description()` delegation to `SurfaceGenerationProcessState.SURFACE_ASSEMBLED`, plus a `METADATA.id` regression guard.
