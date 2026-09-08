# Surface Set

`SurfaceSetCapability` declares the Surface regions and runtime presentation rules while leaving actual viewport geometry to the browser runtime.

| Property | Value |
| --- | --- |
| Capability ID | `org.ontobdc.view.plugin.capability.transformation.target.surface_set` |
| Capability type | `TransformationCapability` |
| Resulting state | `surface_set` |
| Implementation | [`surface_set.py`](https://github.com/EliasMPJunior/ontobdc-view/blob/r008/v0.9/src/ontobdc_view/surface/plugin/capability/transformation/surface_set.py) |
| Embedded block | `<script type="application/json" id="ontobdc-surface-config">` |

## Input

The optional `surface_config` context parameter must be a mapping when present. An absent value is treated as an empty object and normalized to the defaults below.

| Field | Default | Rule |
| --- | ---: | --- |
| `operation.enabled` | `true` | Converted to Boolean. |
| `content.mode` | `scroll` | Must be `scroll` or `fixed`, case-insensitively. |
| `pinned.enabled` | `true` | Converted to Boolean. |
| `slotTarget` | `72` | Must be positive; invalid values fall back. |
| `gap` | `12` | Must be non-negative; invalid values fall back. |
| `padding` | `16` | Must be non-negative; invalid values fall back. |
| `tileMargin` | `0` | Must be non-negative; invalid values fall back. |

## Operation

The capability normalizes the configuration, upserts it as JSON in the document head, advances the state marker to `surface_set`, writes the Surface, and verifies the cumulative state.

This configuration describes region availability, the content flow mode, and sizing tokens. It does not choose the Tiles, place them, or calculate a fixed number of viewport columns or rows.

## Result

The result contains `surface_path`, the normalized `surface_config`, and `SURFACE_SET` as `resulting_state`.

## Satisfaction check

The check requires a valid enriched Surface and a configuration object containing `operation`, `content`, `pinned`, `slotTarget`, `gap`, `padding`, and `tileMargin`. It verifies that `content.mode` is `fixed` or `scroll`. It does not repeat every numeric or Boolean normalization rule, so the executable normalization step remains the stronger producer-side contract.

## Failure behavior

A non-mapping `surface_config` or unsupported `content.mode` raises `ValueError`. Non-numeric and out-of-range sizing values are not fatal; they are replaced with their defaults.

## Tests

Unit tests: [`test_surface_set.py`](https://github.com/EliasMPJunior/ontobdc-view/blob/r008/v0.9/test/unit/surface/plugin/capability/transformation/test_surface_set.py).

No mocking: a real `surface_enriched` document is written to `tmp_path`, and every test exercises the real config-normalization logic end to end.

**`execute()`**:

| Test | Condition |
| --- | --- |
| `test_defaults_are_used_when_no_surface_config_is_supplied` | With no `surface_config` parameter, the full default config (`operation`, `content.mode: scroll`, `pinned`, `slotTarget: 72`, `gap: 12`, `padding: 16`, `tileMargin: 0`) is both returned and embedded as the `ontobdc-surface-config` script. |
| `test_normalizes_an_explicit_partial_config_over_the_defaults` | A partial `surface_config` (e.g. `{"content": {"mode": "fixed"}, "gap": 24}`) overrides only the supplied fields; unspecified fields keep their defaults. |
| `test_raises_for_an_unsupported_content_mode` | `ValueError` when `content.mode` is neither `"scroll"` nor `"fixed"`. |
| `test_raises_when_surface_config_is_not_a_mapping` | `ValueError` when `surface_config` is not a mapping (e.g. a list). |
| `test_invalid_numeric_fields_fall_back_to_their_defaults` | A negative or non-numeric value for a numeric field (`slotTarget: -5`, `gap: "not-a-number"`) falls back to that field's default instead of being accepted as-is. |

**`check()`**:

| Test | Condition |
| --- | --- |
| `test_is_true_after_a_real_execute` | `True` immediately after a real `execute()`. |
| `test_is_false_before_the_config_is_embedded` | `False` for a `surface_enriched` document that has not yet been configured. |
| `test_is_satisfied_matches_check` | `is_satisfied()` matches `check()`. |

**Labels, descriptions, and registry identity** are covered the same way as every other capability in this package: parametrized `label()`/`description()` delegation to `SurfaceGenerationProcessState.SURFACE_SET`, plus a `METADATA.id` regression guard.
