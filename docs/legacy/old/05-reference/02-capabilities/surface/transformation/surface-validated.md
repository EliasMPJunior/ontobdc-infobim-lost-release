# Surface Validated

`SurfaceValidatedCapability` applies the packaged-Surface predicate and, if it passes, advances the artifact marker to `surface_validated`.

| Property | Value |
| --- | --- |
| Capability ID | `org.ontobdc.view.plugin.capability.transformation.target.surface_validated` |
| Capability type | `TransformationCapability` |
| Resulting state | `surface_validated` |
| Implementation | [`surface_validated.py`](https://github.com/EliasMPJunior/ontobdc-view/blob/r008/v0.9/src/ontobdc_view/surface/plugin/capability/transformation/surface_validated.py) |

## Validation predicate

In the current implementation, `is_valid_surface(document)` is exactly `is_packaged_surface(document)`. A valid Surface must therefore satisfy the cumulative conditions below:

- minimal initialized HTML and `<onto-presentation-surface>` host;
- valid embedded JSON-LD;
- valid Surface configuration;
- a structurally complete matches array;
- valid default-layout data when that optional block exists;
- assembled custom elements corresponding to every match;
- no external HTTP(S) runtime reference detected in script sources, stylesheet links, or CSS imports;
- at least one embedded Surface Component module;
- the Component Event promoter marker.

This stage does not introduce an additional schema, browser execution test, HTML conformance parser, or network-offline simulation beyond that packaged predicate.

## Operation

The capability reads the document and evaluates `is_valid_surface()` before mutating it. On success it changes the state marker to `surface_validated`, writes the document, and runs the same predicate through the post-write check.

## Result

The result contains `surface_path` and `SURFACE_VALIDATED` as `resulting_state`.

## Satisfaction check nuance

`check_surface_validated.main()` returns the packaged-Surface predicate and does not require the `surface_validated` marker. The state evaluator can therefore consider this state satisfied as soon as a document is fully packaged, even before `execute()` has written the validation marker. The marker still records that the explicit validation transition ran, but it is not part of this check's current truth condition.

## Failure behavior

If the initial packaged predicate is false, execution raises `ValueError("Surface package failed validation")`. Read, write, or post-write validation failures also abort the transition.

## Tests

Unit tests: [`test_surface_validated.py`](https://github.com/EliasMPJunior/ontobdc-view/blob/r008/v0.9/test/unit/surface/plugin/capability/transformation/test_surface_validated.py).

No mocking: `is_valid_surface()` is a purely structural check (`is_packaged_surface` -- assembled tiles plus a packaged runtime), so the suite builds a real "packaged" document by taking a `surface_assembled` fixture and embedding a real component script via `SurfaceDocumentAdapter.embed_component_scripts()` that contains the exact promoter-registration line the check requires (`window.OntoBDCComponentEventPromoter = promoter;`).

**`execute()`**:

| Test | Condition |
| --- | --- |
| `test_marks_the_document_validated_when_the_package_is_structurally_valid` | A structurally valid packaged document is marked `surface_validated`. |
| `test_raises_when_the_component_promoter_runtime_is_missing` | `ValueError` (matching `"Surface package failed validation"`) for an assembled document that was never packaged with the component-event promoter script. |
| `test_raises_when_the_document_references_an_external_runtime` | `ValueError` for an otherwise-packaged document that references an external (`https://`) stylesheet or script -- packaging must be fully offline. |

**`check()`**:

| Test | Condition |
| --- | --- |
| `test_is_true_after_a_real_execute` | `True` immediately after a real `execute()`. |
| `test_is_false_before_the_document_is_packaged` | `False` for an assembled-but-not-yet-packaged document. |
| `test_is_satisfied_matches_check` | `is_satisfied()` matches `check()`. |

**Labels, descriptions, and registry identity** are covered the same way as every other capability in this package: parametrized `label()`/`description()` delegation to `SurfaceGenerationProcessState.SURFACE_VALIDATED`, plus a `METADATA.id` regression guard.
