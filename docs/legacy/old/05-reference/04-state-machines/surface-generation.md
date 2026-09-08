[↑ Back to state-machine inventory](index.md)

# Surface generation

> **Status:** Current and executable.

Builds the complete offline HTML Presentation Surface and standalone entity views, then emits the local server launcher.

## Audited implementation

- Enum: [SurfaceGenerationProcessState](https://github.com/EliasMPJunior/ontobdc-wip/blob/fe6d756c44141cdc14234937ce1e659384950b26/src/ontobdc/view/domain/machine/surface_state.py)
- YAML: [standard_surface_html.yaml](https://github.com/EliasMPJunior/ontobdc-wip/blob/fe6d756c44141cdc14234937ce1e659384950b26/src/ontobdc/view/domain/machine/standard_surface_html.yaml) (runtime statechart)
- Executor: [evaluator and transition handler](https://github.com/EliasMPJunior/ontobdc-wip/blob/fe6d756c44141cdc14234937ce1e659384950b26/src/ontobdc/view/adapter/surface/machine.py)

## States from the enum

| State | Raw value | Enum meaning | Capability or executing operation |
| --- | --- | --- | --- |
| `UNDEFINED` | `__undefined__` | No HTML Presentation Surface artefact exists yet. | — |
| `CONTAINER_HEALTHY` | `__container_healthy__` | The source container satisfies its structural and semantic health requirements. | `org.ontobdc.storage.plugin.capability.transformation.target.container_healthy`<br>[source](https://github.com/EliasMPJunior/ontobdc-wip/blob/fe6d756c44141cdc14234937ce1e659384950b26/src/ontobdc/storage/plugin/capability/transformation/container_healthy.py) |
| `IS_PUBLISHABLE` | `__is_publishable__` | The healthy source container has a valid publication descriptor and the resources required for presentation generation. | `org.ontobdc.view.plugin.capability.transformation.target.is_publishable`<br>[source](https://github.com/EliasMPJunior/ontobdc-wip/blob/fe6d756c44141cdc14234937ce1e659384950b26/src/ontobdc/view/plugin/capability/transformation/is_publishable.py) |
| `DATA_GATHERED` | `__data_gathered__` | Presentation source data has been materialized as the JSON-LD state artefact consumed by subsequent Surface transformations. | `org.ontobdc.view.plugin.capability.transformation.target.data_gathered`<br>[source](https://github.com/EliasMPJunior/ontobdc-wip/blob/fe6d756c44141cdc14234937ce1e659384950b26/src/ontobdc/view/plugin/capability/transformation/data_gathered.py) |
| `SURFACE_INITIALIZED` | `__surface_initialized__` | The minimal offline HTML document and Presentation Surface host exist. | `org.ontobdc.view.plugin.capability.transformation.target.surface_initialized`<br>[source](https://github.com/EliasMPJunior/ontobdc-wip/blob/fe6d756c44141cdc14234937ce1e659384950b26/src/ontobdc/view/plugin/capability/transformation/surface_initialized.py) |
| `SURFACE_ENRICHED` | `__surface_enriched__` | Semantic data and metadata are embedded in the HTML document as JSON-LD. | `org.ontobdc.view.plugin.capability.transformation.target.surface_enriched`<br>[source](https://github.com/EliasMPJunior/ontobdc-wip/blob/fe6d756c44141cdc14234937ce1e659384950b26/src/ontobdc/view/plugin/capability/transformation/surface_enriched.py) |
| `SURFACE_SET` | `__surface_set__` | Surface regions and presentation rules are declared without fixing runtime viewport geometry. | `org.ontobdc.view.plugin.capability.transformation.target.surface_set`<br>[source](https://github.com/EliasMPJunior/ontobdc-wip/blob/fe6d756c44141cdc14234937ce1e659384950b26/src/ontobdc/view/plugin/capability/transformation/surface_set.py) |
| `SURFACE_BRANDED` | `__surface_branded__` | Branding resources required by the Surface are declared in the HTML artefact. | `org.ontobdc.view.plugin.capability.transformation.target.surface_branded`<br>[source](https://github.com/EliasMPJunior/ontobdc-wip/blob/fe6d756c44141cdc14234937ce1e659384950b26/src/ontobdc/view/plugin/capability/transformation/surface_branded.py) |
| `SURFACE_MATCHED` | `__surface_matched__` | Presentation data are matched to compatible Tile definitions and their support envelopes. | `org.ontobdc.view.plugin.capability.transformation.target.surface_matched`<br>[source](https://github.com/EliasMPJunior/ontobdc-wip/blob/fe6d756c44141cdc14234937ce1e659384950b26/src/ontobdc/view/plugin/capability/transformation/surface_matched.py) |
| `SURFACE_OPERATIONAL_MATCHED` | `__surface_operational_matched__` | The OperationRegion of the shipped default Surface layout (Logo/Language/Theme) is resolved when no explicit operation-region Tile was declared, and its SurfaceDefinition is embedded for client-side selection. | `org.ontobdc.view.plugin.capability.transformation.target.surface_operational_matched`<br>[source](https://github.com/EliasMPJunior/ontobdc-wip/blob/fe6d756c44141cdc14234937ce1e659384950b26/src/ontobdc/view/plugin/capability/transformation/surface_operational_matched.py) |
| `SURFACE_ASSEMBLED` | `__surface_assembled__` | Operation, content and pinned regions are composed with matched Tiles and runtime layout constraints. | `org.ontobdc.view.plugin.capability.transformation.target.surface_assembled`<br>[source](https://github.com/EliasMPJunior/ontobdc-wip/blob/fe6d756c44141cdc14234937ce1e659384950b26/src/ontobdc/view/plugin/capability/transformation/surface_assembled.py) |
| `SURFACE_PARAMETERS_ENSURED` | `__surface_parameters_ensured__` | The canonical URL-controlled presentation parameters (language, theme) have a declared default embedded in the artefact, so a generated page normalizes its own address bar on first open and every internal link inherits the live state. | `org.ontobdc.view.plugin.capability.transformation.target.surface_parameters_ensured`<br>[source](https://github.com/EliasMPJunior/ontobdc-wip/blob/fe6d756c44141cdc14234937ce1e659384950b26/src/ontobdc/view/plugin/capability/transformation/surface_parameters_ensured.py) |
| `SURFACE_PACKAGED` | `__surface_packaged__` | Required browser component implementations are embedded for offline execution. | `org.ontobdc.view.plugin.capability.transformation.target.surface_packaged`<br>[source](https://github.com/EliasMPJunior/ontobdc-wip/blob/fe6d756c44141cdc14234937ce1e659384950b26/src/ontobdc/view/plugin/capability/transformation/surface_packaged.py) |
| `SURFACE_VALIDATED` | `__surface_validated__` | The packaged HTML Surface satisfies the offline Surface generation checks. | `org.ontobdc.view.plugin.capability.transformation.target.surface_validated`<br>[source](https://github.com/EliasMPJunior/ontobdc-wip/blob/fe6d756c44141cdc14234937ce1e659384950b26/src/ontobdc/view/plugin/capability/transformation/surface_validated.py) |
| `ENTITY_VIEWS_PUBLISHED` | `__entity_views_published__` | A standalone detail page was published for every entity ontobdc_view has a Page renderer for. | `org.ontobdc.view.plugin.capability.transformation.target.entity_views_published`<br>[source](https://github.com/EliasMPJunior/ontobdc-wip/blob/fe6d756c44141cdc14234937ce1e659384950b26/src/ontobdc/view/plugin/capability/transformation/entity_views_published.py) |
| `SERVER_LAUNCHER_GENERATED` | `__server_launcher_generated__` | A Windows server.cmd launcher was generated beside index.html so the container can start ontobdc server by double-click. | `org.ontobdc.view.plugin.capability.transformation.target.server_launcher_generated`<br>[source](https://github.com/EliasMPJunior/ontobdc-wip/blob/fe6d756c44141cdc14234937ce1e659384950b26/src/ontobdc/view/plugin/capability/transformation/server_launcher_generated.py) |

## Transition table

| From | To | Guard/condition | Action |
| --- | --- | --- | --- |
| `UNDEFINED` | `CONTAINER_HEALTHY` | handler.can_transit_to(to_state = SurfaceGenerationProcessStatePort.CONTAINER_HEALTHY) | handler.perform_state_transition(to_state = SurfaceGenerationProcessStatePort.CONTAINER_HEALTHY) |
| `CONTAINER_HEALTHY` | `IS_PUBLISHABLE` | handler.can_transit_to(to_state = SurfaceGenerationProcessStatePort.IS_PUBLISHABLE) | handler.perform_state_transition(to_state = SurfaceGenerationProcessStatePort.IS_PUBLISHABLE) |
| `IS_PUBLISHABLE` | `DATA_GATHERED` | handler.can_transit_to(to_state = SurfaceGenerationProcessStatePort.DATA_GATHERED) | handler.perform_state_transition(to_state = SurfaceGenerationProcessStatePort.DATA_GATHERED) |
| `DATA_GATHERED` | `SURFACE_INITIALIZED` | handler.can_transit_to(to_state = SurfaceGenerationProcessStatePort.SURFACE_INITIALIZED) | handler.perform_state_transition(to_state = SurfaceGenerationProcessStatePort.SURFACE_INITIALIZED) |
| `SURFACE_INITIALIZED` | `SURFACE_ENRICHED` | handler.can_transit_to(to_state = SurfaceGenerationProcessStatePort.SURFACE_ENRICHED) | handler.perform_state_transition(to_state = SurfaceGenerationProcessStatePort.SURFACE_ENRICHED) |
| `SURFACE_ENRICHED` | `SURFACE_SET` | handler.can_transit_to(to_state = SurfaceGenerationProcessStatePort.SURFACE_SET) | handler.perform_state_transition(to_state = SurfaceGenerationProcessStatePort.SURFACE_SET) |
| `SURFACE_SET` | `SURFACE_BRANDED` | handler.can_transit_to(to_state = SurfaceGenerationProcessStatePort.SURFACE_BRANDED) | handler.perform_state_transition(to_state = SurfaceGenerationProcessStatePort.SURFACE_BRANDED) |
| `SURFACE_BRANDED` | `SURFACE_MATCHED` | handler.can_transit_to(to_state = SurfaceGenerationProcessStatePort.SURFACE_MATCHED) | handler.perform_state_transition(to_state = SurfaceGenerationProcessStatePort.SURFACE_MATCHED) |
| `SURFACE_MATCHED` | `SURFACE_OPERATIONAL_MATCHED` | handler.can_transit_to(to_state = SurfaceGenerationProcessStatePort.SURFACE_OPERATIONAL_MATCHED) | handler.perform_state_transition(to_state = SurfaceGenerationProcessStatePort.SURFACE_OPERATIONAL_MATCHED) |
| `SURFACE_OPERATIONAL_MATCHED` | `SURFACE_ASSEMBLED` | handler.can_transit_to(to_state = SurfaceGenerationProcessStatePort.SURFACE_ASSEMBLED) | handler.perform_state_transition(to_state = SurfaceGenerationProcessStatePort.SURFACE_ASSEMBLED) |
| `SURFACE_ASSEMBLED` | `SURFACE_PARAMETERS_ENSURED` | handler.can_transit_to(to_state = SurfaceGenerationProcessStatePort.SURFACE_PARAMETERS_ENSURED) | handler.perform_state_transition(to_state = SurfaceGenerationProcessStatePort.SURFACE_PARAMETERS_ENSURED) |
| `SURFACE_PARAMETERS_ENSURED` | `SURFACE_PACKAGED` | handler.can_transit_to(to_state = SurfaceGenerationProcessStatePort.SURFACE_PACKAGED) | handler.perform_state_transition(to_state = SurfaceGenerationProcessStatePort.SURFACE_PACKAGED) |
| `SURFACE_PACKAGED` | `SURFACE_VALIDATED` | handler.can_transit_to(to_state = SurfaceGenerationProcessStatePort.SURFACE_VALIDATED) | handler.perform_state_transition(to_state = SurfaceGenerationProcessStatePort.SURFACE_VALIDATED) |
| `SURFACE_VALIDATED` | `ENTITY_VIEWS_PUBLISHED` | handler.can_transit_to(to_state = SurfaceGenerationProcessStatePort.ENTITY_VIEWS_PUBLISHED) | handler.perform_state_transition(to_state = SurfaceGenerationProcessStatePort.ENTITY_VIEWS_PUBLISHED) |
| `ENTITY_VIEWS_PUBLISHED` | `SERVER_LAUNCHER_GENERATED` | handler.can_transit_to(to_state = SurfaceGenerationProcessStatePort.SERVER_LAUNCHER_GENERATED) | handler.perform_state_transition(to_state = SurfaceGenerationProcessStatePort.SERVER_LAUNCHER_GENERATED) |

## Runtime findings

- The current machine has 16 enum states. `VIEW_ARTIFACTS_CLEANED` and `ENTITY_DATA_GATHERED` from `ontobdc-view@r008/v0.9` are not members of the current enum.
- `SurfaceGenerationStateEvaluatorAdapter` evaluates capabilities in enum order and stops at the first failed `check(context)`.
- `SERVER_LAUNCHER_GENERATED` now generates `server.cmd` and embeds one host/port reference into generated HTML; it is no longer a marker-only state.
