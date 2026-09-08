[↑ Back to Reference](../index.md)

# State machine reference

This inventory was rebuilt from current code, not from the previous documentation. The audited snapshots are:

- [`ontobdc-wip@fe6d756`](https://github.com/EliasMPJunior/ontobdc-wip/tree/fe6d756c44141cdc14234937ce1e659384950b26)
- [`ontobdc-view@9b1dace`](https://github.com/EliasMPJunior/ontobdc-view/tree/9b1daceb0af79258f641409943c9b2a3b4ccbe86)
- [`ontobdc-web-dock@1164268`](https://github.com/EliasMPJunior/ontobdc-web-dock/tree/1164268618c6877d65ddd377d0d49d772d4f8982)
- [`ontobdc-a3@acb815b`](https://github.com/EliasMPJunior/ontobdc-a3/tree/acb815bf7b39a5f2c429481fb6bd9cb6206645a4)

The strict scan found **15 unique `*ProcessState` contracts with 138 enum members**. Event Promotion is declared twice with an identical six-state enum, so the repositories contain 16 concrete `*ProcessState` class declarations. A3 Intent Resolution is also an explicit current machine, but its enum is named `IntentResolutionState`; including it yields **16 current/retained OntoBDC machine contracts and 146 enum members**.

See [Lifecycle and repository status](lifecycle-status.md) for the complete scan, execution gaps, absorbed machines, true legacy code, application-owned exclusions, and the Event Promotion duplication.

## Current and retained machine inventory

| Domain | Machine | Status | Runtime form |
| --- | --- | --- | --- |
| CLI | [CLI initialization](cli-initialization.md) | Current, executable | Enum + YAML + evaluator/handler + capabilities |
| CLI | [CLI health](cli-health.md) | Current, executable | Enum + YAML + evaluator/handler + capabilities |
| Context | [Entity learning](entity-learning.md) | Current contract; incomplete runtime | Enum + YAML + handler; target capabilities absent |
| Context | [Entity analysis](entity-analysis.md) | Current contract; incomplete runtime | Enum + YAML + handler; target capabilities absent |
| Context | [Document import](document-import.md) | Partial | Enum + YAML, but direct handler does not execute YAML |
| Storage | [Container creation](container-create.md) | Current, executable | Enum + YAML + evaluator/handler + capabilities |
| Storage | [Dataset creation](dataset-create.md) | Current, executable | Enum + YAML + evaluator/handler + capabilities |
| Storage | [Container update](container-update.md) | Current, executable | Enum + YAML + evaluator/handler + capabilities |
| Storage | [Container attachment](container-attach.md) | Current, executable | Enum + YAML + evaluator/handler + capabilities/error classifier |
| View | [Surface generation](surface-generation.md) | Current, executable | Enum + YAML + evaluator/handler + capabilities |
| View | [Gantt script generation](gantt-script-generation.md) | Current, executable | Enum + YAML + evaluator/handler + capabilities |
| View | [WorkStream script generation](work-stream-script-generation.md) | Current, executable | Enum + YAML + evaluator/handler + capabilities |
| View | [Global Event processing](global-event-processing.md) | Current, executable | Enum + direct Python transition table/listener |
| dDock | [Component Event promotion](event-promotion.md) | Current integrated + parallel copy | Enum + direct listener/machine; RDF policy |
| View | [Legacy container view](container-view.md) | Truly legacy | Preserved enum/YAML/adapter; capability set no longer viable |
| A3 | [Intent resolution](intent-resolution.md) | Current extension, executable | Enum + YAML + evaluator/handler + capabilities |

## Absorbed machines and removed states

These pages remain only to preserve architectural traceability and prevent old links from pretending to describe current code:

- [WorkStream Page-data](work-stream-page-data.md) — absorbed into Surface data gathering/publication and WorkStream script generation.
- [IfcWorkSchedule Page-data](ifc-work-schedule-page-data.md) — absorbed into Surface data gathering/publication and Gantt script generation.
- The old Surface states `VIEW_ARTIFACTS_CLEANED` and `ENTITY_DATA_GATHERED` were removed from the current enum.

## Source-of-truth rule

For each current machine, the enum is authoritative for the state set and raw values. YAML is authoritative for the transition graph only when the listed executor actually loads it. The adapter/handler is authoritative for runtime execution, capability resolution, state observation, and any direct branching outside YAML.

Released historical branches such as `ontobdc-view@r008/v0.9` are evidence of prior behavior, not authority over the audited `master` code.
