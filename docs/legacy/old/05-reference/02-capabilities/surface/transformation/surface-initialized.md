# Surface Initialized

`SurfaceInitializedCapability` creates the minimal, standalone HTML document that every later Surface transformation modifies.

| Property | Value |
| --- | --- |
| Capability ID | `org.ontobdc.view.plugin.capability.transformation.target.surface_initialized` |
| Capability type | `TransformationCapability` |
| Resulting state | `surface_initialized` |
| Implementation | [`surface_initialized.py`](https://github.com/EliasMPJunior/ontobdc-view/blob/r008/v0.9/src/ontobdc_view/surface/plugin/capability/transformation/surface_initialized.py) |
| Primary artifact | `surface_path`, or `<container_path>/index.html` |

## Inputs and preconditions

The context must resolve a Surface path from either `surface_path` or `container_path`. The optional `language` parameter becomes the initial `<html lang>` value; an absent or false value defaults to `en`.

## Operation

`SurfaceDocumentAdapter.make_initial_html()` creates a complete document containing:

- the HTML doctype, `<html>`, `<head>`, and `<body>`;
- UTF-8 and responsive viewport metadata;
- the `ontobdc:surface-state` meta element;
- baseline page and host sizing styles;
- one empty `<onto-presentation-surface>` custom-element host.

The capability sets the state marker to `surface_initialized`, writes the document, stores the resolved path as `surface_path` in the context, and performs the post-write check.

This stage creates a fresh document rather than incrementally editing a pre-existing page. The preceding [View Artifacts Cleaned](view-artifacts-cleaned.md) state removes a previous `index.html` (and every other HTML artefact `ontobdc view` generated) before this state runs, so a failed earlier run cannot be mistaken for a resumable current build.

## Result

The result contains the resolved `surface_path` and `SURFACE_INITIALIZED` as `resulting_state`.

## Satisfaction check

The check is structural. It requires a doctype plus `<html>`, `<head>`, `<body>`, and an `<onto-presentation-surface>` element. It does not require the state meta marker itself. Consequently, any document with that minimal structure satisfies the check, even if its marker is missing or stale.

## Failure behavior

Path resolution, directory creation, write, or structural-check failures abort the transition. The language is HTML-escaped before it is placed in the attribute.

## Tests

Unit tests: [`test_surface_initialized.py`](https://github.com/EliasMPJunior/ontobdc-view/blob/r008/v0.9/test/unit/surface/plugin/capability/transformation/test_surface_initialized.py).

Because this is the very first HTML-producing state, the suite needs no earlier-stage fixture: every test starts from a plain `tmp_path` container and drives the capability directly against the real `SurfaceDocumentAdapter` (no mocking).

**`execute()`**:

| Test | Condition |
| --- | --- |
| `test_creates_a_minimal_valid_document_at_the_container_index_html` | Writes `<container>/index.html`, and the written document contains a doctype, the `<onto-presentation-surface>` host element, and the `surface_initialized` state marker. |
| `test_uses_the_requested_language_as_the_html_lang_attribute` | A `language` parameter on the context (e.g. `pt-BR`) becomes the document's `<html lang="...">` attribute. |
| `test_defaults_to_english_when_no_language_is_requested` | With no `language` parameter, `<html lang="en">` is used. |
| `test_records_the_resolved_surface_path_back_on_the_context` | After execution, `context.get_parameter_value("surface_path")` returns the resolved `index.html` path. |

**`check()`**:

| Test | Condition |
| --- | --- |
| `test_is_true_after_a_real_execute` | `True` immediately after a real `execute()`. |
| `test_is_true_for_a_minimal_document_even_without_the_state_marker` | `True` for any structurally valid document (doctype, `html`/`head`/`body`, the Surface host element) even when the state marker itself is absent -- the check is purely structural, not marker-based. |
| `test_is_false_when_no_surface_exists_yet` | `False` when `index.html` does not exist. |
| `test_is_false_for_html_missing_the_surface_host_element` | `False` for an otherwise well-formed HTML document that lacks `<onto-presentation-surface>`. |
| `test_is_satisfied_matches_check` | `is_satisfied()` matches `check()`. |

**Labels, descriptions, and registry identity** are covered the same way as every other capability in this package: parametrized `label()`/`description()` delegation to `SurfaceGenerationProcessState.SURFACE_INITIALIZED`, plus a `METADATA.id` regression guard.
