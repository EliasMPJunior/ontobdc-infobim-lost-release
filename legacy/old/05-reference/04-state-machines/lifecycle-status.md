[↑ Back to state-machine inventory](index.md)

# Lifecycle and repository status

This page records what the code scan found, including negative results. “Present” means a concrete enum/state type exists on the audited `master`; it does not automatically mean the machine is reachable or end-to-end executable.

## Repository scan

| Repository snapshot | Finding | Documentation decision |
| --- | --- | --- |
| [`ontobdc-wip@fe6d756`](https://github.com/EliasMPJunior/ontobdc-wip/tree/fe6d756c44141cdc14234937ce1e659384950b26) | 14 unique `*ProcessState` enums; 13 YAML statecharts; Global Event uses a Python transition table. | Primary source for CLI, Context, Storage, Surface, script-generation, legacy Container View, and Global Event machines. |
| [`ontobdc-view@9b1dace`](https://github.com/EliasMPJunior/ontobdc-view/tree/9b1daceb0af79258f641409943c9b2a3b4ccbe86) | `EventPromotionProcessState` plus the integrated `PresentationEventPromotionListener`; no Surface/Page state enums on `master`. | Primary integrated Event Promotion executor. The old `r008/v0.9` Surface/Page inventory is not treated as current. |
| [`ontobdc-web-dock@1164268`](https://github.com/EliasMPJunior/ontobdc-web-dock/tree/1164268618c6877d65ddd377d0d49d772d4f8982) | A second, identical `EventPromotionProcessState` contract and direct `EventPromotionMachine`. | Recorded as a parallel standalone implementation; current `ontobdc-view` packaging embeds its internal dDock instead. |
| [`ontobdc-a3@acb815b`](https://github.com/EliasMPJunior/ontobdc-a3/tree/acb815bf7b39a5f2c429481fb6bd9cb6206645a4) | Current `IntentResolutionState` machine plus an older machine under `prompt/old/`. | Current extension included; `/old/` machine classified as legacy. |
| [`ontobdc-dev@9b0a0b2`](https://github.com/EliasMPJunior/ontobdc-dev/tree/9b0a0b268b90c5578ace9204ce5751d00f518be0) | No explicit state-machine files or state enums. | No machine page. |
| [`ontobdc-mobile@ae9a343`](https://github.com/EliasMPJunior/ontobdc-mobile/tree/ae9a3439e056c68bb6be3f43d6b4af0c344f69fd) | No explicit state-machine files or state enums. | No machine page. |
| [`ontobdc-remote@88c2a7b`](https://github.com/EliasMPJunior/ontobdc-remote/tree/88c2a7b1ccf26d24c67db509622b9b31e6fd5e02) | No explicit state-machine files or state enums. | No machine page. |
| [`infobim-wip@f476f12`](https://github.com/EliasMPJunior/infobim-wip/tree/f476f12d4347afa11b3f7ba7eaf8000283339486) | `ProjectCreateProcessState` and `A3LlmSuggestionProcessState` are application-owned InfoBIM machines. | Explicitly out of scope for OntoBDC reference; they belong in InfoBIM documentation. |
| [`brasidatacenter`](https://github.com/EliasMPJunior/brasidatacenter) | RDF policy/data, including Presentation Event promotion policy; no executor state machine. | Linked as policy authority, not counted as a machine owner. |

## Classification

### Current and end-to-end executable

- CLI Initialization and CLI Health.
- Container Create, Dataset Create, Container Update, and Container Attach.
- Surface Generation, Gantt Script Generation, WorkStream Script Generation, and Global Event Processing.
- Integrated Component Event Promotion in `ontobdc-view`.
- A3 Intent Resolution.

### Current definitions with execution gaps

| Machine | What exists | Gap in the audited source |
| --- | --- | --- |
| Entity Learning | Enum, YAML, handler, repository-backed state observation. | The dynamically resolved Context target capabilities are absent. |
| Entity Analysis | Enum, YAML, handler, repository-backed state observation. | The dynamically resolved Context target capabilities are absent. |
| Document Import | Enum, rich YAML lifecycle, direct bootstrap handler. | The handler does not load the YAML, has no state-specific capabilities, only materializes the main path, is not referenced elsewhere by class name, and the enum's `get_state()` names an undefined class. |

### Absorbed

| Former machine | Evidence of removal | Current owner of the work |
| --- | --- | --- |
| WorkStream Page-data | No enum, YAML, handler, or former capability names on audited `master`. | Surface `DATA_GATHERED` + `ENTITY_VIEWS_PUBLISHED` + WorkStream script generation. |
| IfcWorkSchedule Page-data | No enum, YAML, handler, or former capability names on audited `master`. | Surface `DATA_GATHERED` + `ENTITY_VIEWS_PUBLISHED` + Gantt script generation. |
| `VIEW_ARTIFACTS_CLEANED` and `ENTITY_DATA_GATHERED` Surface states | Present in `r008/v0.9`, absent from current `SurfaceGenerationProcessState`. | Responsibilities folded into current Surface capabilities; they are not current states. |

### Truly legacy

| Machine | Why it is legacy |
| --- | --- |
| `ContainerViewProcessState` / `StandardContainerView` | Source docstrings and handlers call it legacy; current publishing uses Surface; four of five mapped capability modules are absent and the remaining ID now resolves to a Surface capability. |
| `RunIntentResolutionState` under `ontobdc_a3/prompt/old/` | It is physically under `/old/`; the active package has a different state enum, YAML, handler, capability IDs, and branch semantics. |

### Parallel, not absorbed and not the integrated owner

`ontobdc-web-dock` still contains a complete direct Event Promotion machine. It is not called by the current `ontobdc-view` packager, which bundles `ontobdc_view.dock` from its own source tree. The two implementations currently share the same six enum states, but they are separate code copies and should not be silently described as one implementation.
