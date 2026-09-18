# Surface Matched

`SurfaceMatchedCapability` resolves presentation requests to registered browser Components, chooses one Component for each request, and attaches the Component's supported size envelope.

| Property | Value |
| --- | --- |
| Capability ID | `org.ontobdc.view.plugin.capability.transformation.target.surface_matched` |
| Capability type | `TransformationCapability` |
| Resulting state | `surface_matched` |
| Implementation | [`surface_matched.py`](https://github.com/EliasMPJunior/ontobdc-view/blob/r008/v0.9/src/ontobdc_view/surface/plugin/capability/transformation/surface_matched.py) |
| Embedded block | `<script type="application/json" id="ontobdc-surface-matches">` |

## Inputs

The capability reads the gathered JSON-LD graph from disk and accepts optional `surface_matches` from the context. Each request must identify either:

- an entity through `data` or `data_id`; or
- a Tile ontology class through `tileClass` or `tile_class`.

An explicit non-empty list is strict: a request without a matching Component raises an error. When no explicit requests are supplied, requests are derived automatically.

## Automatic requests

The capability visits unique URI subjects in the gathered graph. A subject is eligible only when one of its RDF types is itself typed `obdc:SurfaceableEntity` and `ComponentLoader.match()` finds at least one Component. Eligible requests are ordered with `obdc:DataContainer` first, `obdc:FileTree` second, and all other types afterward.

If registered, static `FileSizeTile` and `FileViewerTile` requests are appended after the entity-derived requests.

## Component selection

For entity requests, matching uses the RDF graph and entity URI. For Tile-class requests, matching uses the Tile ontology class. HTML matching removes Components whose custom-element tag ends in `-terminal` when at least one non-terminal alternative exists.

Candidates are sorted by descending number of `required_uris`, then by Component ID; the first candidate wins. The resolved request receives:

- `tile`: the selected custom-element tag;
- `closed`: the Component's `default_closed` value;
- `minColumns`, `preferredColumns`, and `maxColumns`;
- `minRows`, `preferredRows`, and `maxRows`.

When Component metadata declares `size_property` and `chars_per_column`, preferred columns are calculated from the corresponding RDF literal length, bounded by the Component minimum and maximum. Static Tile-class requests use the Component minimum as the preference. Operation and pinned Tiles are forced to exactly one row.

The normalized list is embedded into the HTML and the state marker advances.

## Result

The result contains `surface_path`, `match_count`, and `resulting_state`. It currently also contains `_dbg_*` timing and cache evidence; those diagnostic fields are implementation instrumentation rather than a stable public contract.

## Satisfaction check

The cumulative check requires initialized HTML, valid embedded JSON-LD, valid Surface configuration, and a matches array. Every match must contain a Tile tag, region, and all six size-envelope fields. It checks presence and shape, not whether the registered Component set would make the same choice again.

## Failure behavior

Missing or invalid gathered JSON-LD, malformed requests, absence of a required Component, invalid custom-element tags, invalid regions, or inconsistent size envelopes abort the transition. Matching caches are cleared for every execution because their keys are meaningful only for the current RDF graph.

## Tests

Unit tests: [`test_surface_matched.py`](https://github.com/EliasMPJunior/ontobdc-view/blob/r008/v0.9/test/unit/surface/plugin/capability/transformation/test_surface_matched.py).

No mocking of the matching engine itself: tests match a hand-written gathered graph against the **real, currently-registered** `DataContainerTileComponent` (`min_columns=1, max_columns=6, min_rows=2, max_rows=2`, sized from `dcterms:title` at 4 characters per column) and the real `onto-language-tile` Component. Because `_default_requests()` always appends the two static requests `onto-file-size-tile` and `onto-file-viewer-tile` when their Components are registered -- independent of graph content -- every auto-match assertion accounts for those two tiles in addition to whatever the graph itself produces.

**Auto-matching** (`TestExecuteAutoMatching`):

| Test | Condition |
| --- | --- |
| `test_auto_matches_a_surfaceable_data_container_to_its_real_registered_tile` | A gathered `obdc:DataContainer` marked `obdc:SurfaceableEntity` auto-matches to `onto-data-container-tile` in the `content` region, with column/row envelope and `preferredColumns` computed from the real title-length sizing rule (`ceil(len(title) / 4)`, here 4 for a 14-character title). |
| `test_a_non_surfaceable_entity_type_produces_no_match` | An entity whose type is not registered as surfaceable produces only the two static tiles -- no auto-match. |
| `test_wider_titles_produce_more_preferred_columns_up_to_the_maximum` | A very long title clamps `preferredColumns` at the Component's `max_columns` (6) rather than exceeding it. |

**Explicit requests** (`TestExecuteExplicitRequests`):

| Test | Condition |
| --- | --- |
| `test_an_explicit_tile_class_request_is_resolved_strictly` | An explicit `{"tileClass": ..., "region": "operation"}` request resolves to the real matching Component (`onto-language-tile`), and an `operation`-region request is forced to exactly one row (`minRows == preferredRows == maxRows == 1`). |
| `test_an_explicit_request_with_no_matching_component_raises` | `ValueError` (matching `"No registered component satisfies request"`) for a `tileClass` with no registered Component. |
| `test_a_request_without_data_or_tile_class_raises` | `ValueError` (matching `"must specify either"`) for a request with neither `data` nor `tileClass`. |

**`check()`**:

| Test | Condition |
| --- | --- |
| `test_is_true_after_a_real_execute` | `True` immediately after a real `execute()`. |
| `test_is_false_before_matches_are_embedded` | `False` for a `surface_set` document that has not yet been matched. |
| `test_is_satisfied_matches_check` | `is_satisfied()` matches `check()`. |

**Labels, descriptions, and registry identity** are covered the same way as every other capability in this package: parametrized `label()`/`description()` delegation to `SurfaceGenerationProcessState.SURFACE_MATCHED`, plus a `METADATA.id` regression guard.
