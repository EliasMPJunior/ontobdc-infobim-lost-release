# Surface Parameters Ensured

`SurfaceParametersEnsuredCapability` makes URL-controlled presentation state explicit and reproducible by embedding the runtime that owns parameter defaults, selection, and propagation.

| Property | Value |
| --- | --- |
| Capability ID | `org.ontobdc.view.plugin.capability.transformation.target.surface_parameters_ensured` |
| Capability type | `TransformationCapability` |
| Resulting state | `surface_parameters_ensured` |
| Implementation | [`surface_parameters_ensured.py`](https://github.com/EliasMPJunior/ontobdc-view/blob/r008/v0.9/src/ontobdc_view/surface/plugin/capability/transformation/surface_parameters_ensured.py) |
| Runtime block | `<script id="ontobdc-surface-url-state">` |

## Default resolution

The current implementation resolves one default:

| URL parameter | Resolution order |
| --- | --- |
| `lang` | Non-empty context `language`; existing `<html lang>`; `en`. |

Although the shared document adapter declares both `lang` and `theme` as canonical parameter names, `resolve_defaults()` currently returns only `lang`. Consequently, the embedded runtime normalizes and propagates language, but not theme, in this version.

## Runtime behavior

The embedded head script executes before deferred custom-element modules and exposes `window.ontobdcUrlState`. It:

1. Treats `location.search` as the single source of truth; defaults answer only when a parameter is absent.
2. Writes missing defaults into the current URL using `history.replaceState()` without a reload.
3. Falls back to `location.replace()` on opaque-origin `file://` pages where the browser refuses `replaceState()`.
4. Applies the active language to `document.documentElement.lang` and `data-language` before first component paint.
5. Provides `value()`, `current()`, `withParam()`, `select()`, `decorate()`, and `applyLanguage()` helpers.
6. Preserves an explicit parameter already present on an internal target link and propagates only missing live values.
7. Uses `location.assign()` for user selections so browser Back can undo the change.

Components are expected to use this shared runtime instead of parsing or rewriting the query string independently. No cookie or `localStorage` state participates.

## Result

The capability upserts the runtime, advances the marker, and returns `surface_path`, `url_state_defaults`, and `resulting_state`.

## Satisfaction check

The check is marker-based: a document at `surface_parameters_ensured` or any later state passes. It does not inspect the runtime script or compare its embedded defaults with the context.

## Failure behavior

A missing Surface, malformed document without a writable head, write failure, or absent post-write state marker aborts the transition.

## Tests

Unit tests: [`test_surface_parameters_ensured.py`](https://github.com/EliasMPJunior/ontobdc-view/blob/r008/v0.9/test/unit/surface/plugin/capability/transformation/test_surface_parameters_ensured.py).

No mocking: a real `surface_assembled` document is written to `tmp_path`, and `resolve_defaults()`/`execute()` are exercised directly against it.

**`resolve_defaults()`** (`TestResolveDefaults`):

| Test | Condition |
| --- | --- |
| `test_uses_the_requested_language_when_present` | A `language` parameter on the context wins over the document's own `<html lang>` attribute. |
| `test_falls_back_to_the_documents_html_lang_attribute` | With no requested language, the document's `<html lang="pt-BR">` attribute is used. |
| `test_falls_back_to_english_when_neither_is_available` | With neither a requested language nor a `lang` attribute in the document, `"en"` is used. |

**`execute()`**:

| Test | Condition |
| --- | --- |
| `test_embeds_the_bootstrap_script_and_advances_the_marker` | The `ontobdc-surface-url-state` bootstrap script is embedded, `url_state_defaults` reflects the resolved language, and the state marker advances to `surface_parameters_ensured`. |

**`check()`**:

| Test | Condition |
| --- | --- |
| `test_is_true_after_a_real_execute` | `True` immediately after a real `execute()`. |
| `test_is_true_for_any_later_cumulative_state_marker` | `True` for a document already marked past this state (e.g. `surface_packaged`) -- `check()` is marker-based and cumulative, via `SurfaceDocumentAdapter.state_reached()`. |
| `test_is_false_before_the_bootstrap_is_embedded` | `False` for a `surface_assembled` document that has not yet had parameters ensured. |
| `test_is_false_when_no_surface_exists_yet` | `False` when no `index.html` exists at all. |
| `test_is_satisfied_matches_check` | `is_satisfied()` matches `check()`. |

**Labels, descriptions, and registry identity** are covered the same way as every other capability in this package: parametrized `label()`/`description()` delegation to `SurfaceGenerationProcessState.SURFACE_PARAMETERS_ENSURED`, plus a `METADATA.id` regression guard.
