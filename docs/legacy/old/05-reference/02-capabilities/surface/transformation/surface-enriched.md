# Surface Enriched

`SurfaceEnrichedCapability` embeds the gathered semantic snapshot into the HTML artifact as JSON-LD.

| Property | Value |
| --- | --- |
| Capability ID | `org.ontobdc.view.plugin.capability.transformation.target.surface_enriched` |
| Capability type | `TransformationCapability` |
| Resulting state | `surface_enriched` |
| Implementation | [`surface_enriched.py`](https://github.com/EliasMPJunior/ontobdc-view/blob/r008/v0.9/src/ontobdc_view/surface/plugin/capability/transformation/surface_enriched.py) |
| Embedded block | `<script type="application/ld+json" id="ontobdc-surface-jsonld">` |

## Inputs and preconditions

The initialized Surface document must exist. The `DATA_GATHERED` artifact must exist at its standard ETL path and contain valid JSON.

The capability deliberately reads the JSON-LD artifact from disk instead of expecting a value passed through the CLI context. This makes a state produced by an earlier process invocation usable in a later run.

## Operation

1. Resolve the standard `DATA_GATHERED` artifact path from `container_path`.
2. Read and parse the JSON-LD payload.
3. Read the current Surface HTML.
4. Insert the payload into `<head>` under `ontobdc-surface-jsonld`, or replace the existing block with that ID.
5. Set the state marker to `surface_enriched`, write the document, and run the cumulative check.

JSON serialization preserves non-ASCII characters, uses indentation, and escapes `</` inside the script body to prevent data from prematurely closing the HTML script element.

## Result and side effects

The capability updates the same HTML file and returns its `surface_path` plus `SURFACE_ENRICHED` as `resulting_state`. It does not delete the standalone ETL artifact.

## Satisfaction check

The check requires the initialized HTML structure and a JSON script with the expected ID whose body parses to a JSON object or array. It validates the embedded representation, not equality with the current ETL artifact, and does not require the state marker.

## Failure behavior

A missing or invalid ETL artifact, a missing Surface file, malformed HTML without a closing `</head>`, or a failed post-write check aborts the transition.

## Tests

Unit tests: [`test_surface_enriched.py`](https://github.com/EliasMPJunior/ontobdc-view/blob/r008/v0.9/test/unit/surface/plugin/capability/transformation/test_surface_enriched.py).

No mocking: a real `surface_initialized` document is written to `tmp_path`, and the gathered JSON-LD artifact is written to the exact path `DataGatheredCapability.state_path(context)` resolves, so the capability reads real files throughout.

**`execute()`**:

| Test | Condition |
| --- | --- |
| `test_embeds_the_gathered_jsonld_and_advances_the_state_marker` | The gathered graph is embedded verbatim as the `ontobdc-surface-jsonld` script, and the state marker advances to `surface_enriched`. |
| `test_raises_when_the_gathered_artifact_is_missing` | `FileNotFoundError` propagates when the `data_gathered` ETL artifact was never written. |
| `test_raises_when_the_gathered_artifact_is_invalid_json` | `json.JSONDecodeError` propagates when the artifact exists but is not valid JSON. |

**`check()`**:

| Test | Condition |
| --- | --- |
| `test_is_true_after_a_real_execute` | `True` immediately after a real `execute()`. |
| `test_is_false_before_the_jsonld_script_is_embedded` | `False` for a `surface_initialized` document that has not yet been enriched. |
| `test_is_false_when_no_surface_exists_yet` | `False` when no `index.html` exists at all. |
| `test_is_satisfied_matches_check` | `is_satisfied()` matches `check()`. |

**Labels, descriptions, and registry identity** are covered the same way as every other capability in this package: parametrized `label()`/`description()` delegation to `SurfaceGenerationProcessState.SURFACE_ENRICHED`, plus a `METADATA.id` regression guard.
