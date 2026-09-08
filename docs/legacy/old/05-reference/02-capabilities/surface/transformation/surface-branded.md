# Surface Branded

`SurfaceBrandedCapability` resolves the SVG assets used as the OntoBDC brand and logotype, using a deterministic local-to-remote precedence.

| Property | Value |
| --- | --- |
| Capability ID | `org.ontobdc.view.plugin.capability.transformation.target.surface_branded` |
| Capability type | `TransformationCapability` |
| Resulting state | `surface_branded` |
| Implementation | [`surface_branded.py`](https://github.com/EliasMPJunior/ontobdc-view/blob/r008/v0.9/src/ontobdc_view/surface/plugin/capability/transformation/surface_branded.py) |
| Asset names | `OntoBDCBrand.svg`, `OntoBDCLogotype.svg` |

## Inputs and preconditions

`container_path` is mandatory. `context.root_path` supplies the workspace root. The preceding Surface HTML must exist.

For each asset, the capability checks these sources in order:

1. `<container>/.__ontobdc__/asset/<filename>`;
2. `<workspace>/.__ontobdc__/asset/<filename>`;
3. an SVG linked from `https://ontobdc.org/`, preferring an exact filename;
4. a built-in empty but valid SVG as the final fallback.

## Operation

An existing local candidate is read and validated. A downloaded candidate is accepted only when its first non-whitespace bytes contain an `<svg` element; network access uses the `OntoBDC/SurfaceBranded` user agent and a 15-second timeout. A remotely obtained or empty-fallback asset is written into the container asset directory. A workspace asset is used in place and is not copied to the container.

After both roles resolve, the capability updates only the HTML state marker and writes the document. It returns, for each role, the resolved filesystem path and a source value such as `container`, `workspace`, the source URL, or `empty-fallback`.

## Important current behavior

The current implementation does not embed the resolved SVG content or paths into `index.html`; it only resolves the files and marks the state. This is narrower than the state description saying that branding resources are declared in the HTML artifact.

## Satisfaction check

The check reads the HTML and uses the cumulative state marker. A marker at `surface_branded` or any later state satisfies it. It does not verify that either SVG still exists, is valid, or is referenced by the Surface.

## Failure behavior

An existing container or workspace candidate that is not SVG raises `ValueError` immediately. Network lookup errors are tolerated and lead to the empty fallback. Filesystem failures while creating the container asset directory or writing a downloaded fallback abort the transition.

## Tests

Unit tests: [`test_surface_branded.py`](https://github.com/EliasMPJunior/ontobdc-view/blob/r008/v0.9/test/unit/surface/plugin/capability/transformation/test_surface_branded.py).

Only `SurfaceBrandedCapability._download` is mocked (with `unittest.mock.patch.object`) -- it is the one genuine external-network boundary this capability has. Container/workspace file resolution, the empty-SVG fallback, and validation all run against the real filesystem.

**`execute()`**:

| Test | Condition |
| --- | --- |
| `test_resolves_from_the_container_when_present_there` | Brand and logotype SVGs already present under `<container>/.__ontobdc__/asset/` are used as-is; `branding.brand.source == "container"`. |
| `test_resolves_from_the_workspace_when_absent_from_the_container` | When absent from the container but present under the workspace root, the workspace copy is used in place (`source == "workspace"`) and is never copied into the container. |
| `test_falls_back_to_the_empty_svg_when_every_other_tier_fails` | When no local tier has the asset and the mocked `_download` raises `OSError`, an empty placeholder SVG is written and `source == "empty-fallback"`. |
| `test_downloads_from_the_official_page_when_local_tiers_are_absent` | With `_download` mocked to return the official OntoBDC page HTML, then the referenced asset bytes, the capability parses the page's `<img src>` references, downloads the real assets, and reports `source` as the resolved absolute URL. |
| `test_raises_when_a_local_candidate_is_not_actually_svg` | `ValueError` (matching `"not SVG"`) when a local candidate file exists but its content is not SVG. |
| `test_raises_when_container_path_is_not_set` | `ValueError` (matching `"container_path is required"`) when the context has no `container_path`. |

**`check()`**:

| Test | Condition |
| --- | --- |
| `test_is_true_after_a_real_execute` | `True` immediately after a real `execute()` (offline, via the mocked `_download` raising `OSError` and falling back to the empty SVG). |
| `test_is_false_when_no_surface_exists_yet` | `False` when no `index.html` exists at all. |
| `test_is_satisfied_matches_check` | `is_satisfied()` matches `check()`. |

**Labels, descriptions, and registry identity** are covered the same way as every other capability in this package: parametrized `label()`/`description()` delegation to `SurfaceGenerationProcessState.SURFACE_BRANDED`, plus a `METADATA.id` regression guard.
