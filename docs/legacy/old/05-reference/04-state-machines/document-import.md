[↑ Back to state-machine inventory](index.md)

# Document import

> **Status:** Partially implemented; YAML is not the executed path.

Defines the semantic maturity lifecycle of an imported artifact, including review and terminal outcomes.

## Audited implementation

- Enum: [DocumentImportProcessState](https://github.com/EliasMPJunior/ontobdc-wip/blob/fe6d756c44141cdc14234937ce1e659384950b26/src/ontobdc/context/domain/machine/document_import_state.py)
- YAML: [standard_document_import.yaml](https://github.com/EliasMPJunior/ontobdc-wip/blob/fe6d756c44141cdc14234937ce1e659384950b26/src/ontobdc/context/domain/machine/standard_document_import.yaml) (declared statechart; not loaded by the current handler)
- Executor: [direct bootstrap handler](https://github.com/EliasMPJunior/ontobdc-wip/blob/fe6d756c44141cdc14234937ce1e659384950b26/src/ontobdc/context/adapter/document.py)

## States from the enum

| State | Raw value | Enum meaning | Capability or executing operation |
| --- | --- | --- | --- |
| `UNDEFINED` | `__undefined__` | Initial state assigned before the import process has materialized, classified, or otherwise processed any source artifact. | Source step loaded from `DocumentImportStepRepository` |
| `INGESTED` | `__ingested__` | The source artifact has entered the import process and has been preserved in its original form. Its identity, content hash, file name, media type, size, origin, and available provenance have been recorded. When applicable, the original artifact is already registered as an ICDD payload document, but its contents have not yet been interpreted. | Direct JSON step materialization by `DocumentImportStateTransitionHandler`; no capability |
| `PROFILED` | `__profiled__` | The source artifact has been technically and documentarily characterized so that suitable processing capabilities can be selected. Profiling may identify the document type, format, generating application, language, revision, page geometry, presence of native text, scanned content, tables, images, vector graphics, annotations, or other relevant structural features. No domain assertions are created solely from this characterization. | Direct JSON step materialization by `DocumentImportStateTransitionHandler`; no capability |
| `EXTRACTED` | `__extracted__` | Observable content has been recovered from the source without yet assigning domain meaning to it. Extracted material may include text, words, bounding boxes, blocks, tables, images, vector elements, metadata, bookmarks, annotations, or OCR results. Every extracted fragment should retain enough provenance to identify its source artifact, page or region, and extraction method. | Direct JSON step materialization by `DocumentImportStateTransitionHandler`; no capability |
| `STRUCTURED` | `__structured__` | Extracted fragments have been organized into a coherent intermediate representation that is independent of the target ontology. Examples include rows, columns, cells, sections, fields, records, candidate activities, dates, relationships, risks, controls, or other document-level structures. Each structured value remains traceable to the evidence from which it was derived. | Direct JSON step materialization by `DocumentImportStateTransitionHandler`; no capability |
| `INSTANTIATED` | `__instantiated__` | The intermediate records have been transformed into semantic instances and assertions according to the selected domain models. For example, schedule records may produce work schedules, tasks, task times, decompositions, and sequence relationships, while other documents may produce people, organizations, locations, requirements, risks, controls, inspections, or occurrences. References may still be unresolved at this stage. | Direct JSON step materialization by `DocumentImportStateTransitionHandler`; no capability |
| `RESOLVED` | `__resolved__` | References and candidate identities have been reconciled with known entities within the current import, the ICDD container, previous revisions, or authorized external datasets. Each attempted resolution should explicitly record whether it is resolved, ambiguous, unresolved, or conflicting, together with its supporting evidence, so that uncertain correspondences are not silently asserted. | Direct JSON step materialization by `DocumentImportStateTransitionHandler`; no capability |
| `VALIDATED` | `__validated__` | The semantic instances, values, and relationships have been checked for structural, referential, and domain consistency. Validation may include schema conformance, data types, cardinalities, SHACL shapes, temporal rules, referential integrity, document-specific constraints, completeness requirements, and cross-record consistency. The validation result and every warning or violation are recorded as auditable process outputs. | Direct JSON step materialization by `DocumentImportStateTransitionHandler`; no capability |
| `LINKED` | `__linked__` | Semantic instances have been connected to source documents, exact document fragments, other semantic entities, and relevant external artifacts. The resulting ICDD RDF linksets may relate an entity to a complete document, a page or bounding-box evidence fragment, another entity such as an IFC object, or operational records such as photographs, reports, permits, and risk assessments. | Direct JSON step materialization by `DocumentImportStateTransitionHandler`; no capability |
| `PACKAGED` | `__packaged__` | The original payloads and all selected process products have been assembled into an ICDD container. The package may include semantic models, human-editable representations, RDF linksets, validation reports, provenance, manifests, hashes, and capability versions. The container is complete enough for final verification but has not yet been declared an immutable published version. | Direct JSON step materialization by `DocumentImportStateTransitionHandler`; no capability |
| `PUBLISHED` | `__published__` | The ICDD container has passed final verification and has been closed as an identifiable, immutable, and distributable version. Final hashes, version identifiers, and signatures, when applicable, have been recorded. Any subsequent change must produce a new process execution or container revision rather than silently altering the published result. | Direct JSON step materialization by `DocumentImportStateTransitionHandler`; no capability |
| `REVIEW_REQUIRED` | `__review_required__` | Automated processing completed far enough to produce usable intermediate or semantic results, but one or more ambiguities, low-confidence interpretations, unresolved references, or validation findings require an explicit human decision before normal processing can continue. This is a controlled workflow state, not a technical failure. | Declared by enum/YAML; current handler never enters this state |
| `UNSUPPORTED` | `__unsupported__` | The artifact was ingested and profiled, but no available adapter or processing capability can reliably handle its format, structure, protection mechanism, or document type. The source and profiling evidence remain preserved so that processing may be retried when appropriate support becomes available. | Declared by enum/YAML; current handler never enters this state |
| `REJECTED` | `__rejected__` | Processing produced interpretable results, but the source or resulting semantic content does not satisfy the minimum acceptance criteria required for integration or publication. Rejection is a deliberate semantic or governance decision supported by recorded validation findings, not an unexpected execution error. | Declared by enum/YAML; current handler never enters this state |
| `FAILED` | `__failed__` | The process could not complete the current operation because of an unexpected technical error, unavailable dependency, corrupted intermediate artifact, or other execution failure. The failure context, completed states, and recoverable outputs should be retained to support diagnosis and safe retry. | Declared by enum/YAML; current handler never enters this state |
| `CANCELLED` | `__cancelled__` | The import process was deliberately stopped before publication by a user, an authorized workflow, or a controlling process. Already materialized artifacts and provenance are retained according to policy, but the execution is not considered a completed semantic import. | Declared by enum/YAML; current handler never enters this state |
| `SUPERSEDED` | `__superseded__` | The process result or published container version has been replaced by a newer accepted revision. The superseded result remains identifiable and auditable and may still be referenced for historical or provenance purposes, but it is no longer the current authoritative version. | Declared by enum/YAML; current handler never enters this state |

## Transition table

| From | To | Guard/condition | Action |
| --- | --- | --- | --- |
| `UNDEFINED` | `INGESTED` | handler.can_transit_to(to_state = DocumentImportProcessState.INGESTED) | handler.perform_state_transition(to_state = DocumentImportProcessState.INGESTED) |
| `INGESTED` | `PROFILED` | handler.can_transit_to(to_state = DocumentImportProcessState.PROFILED) | handler.perform_state_transition(to_state = DocumentImportProcessState.PROFILED) |
| `INGESTED` | `FAILED` | handler.can_transit_to(to_state = DocumentImportProcessState.FAILED) | handler.perform_state_transition(to_state = DocumentImportProcessState.FAILED) |
| `INGESTED` | `CANCELLED` | handler.can_transit_to(to_state = DocumentImportProcessState.CANCELLED) | handler.perform_state_transition(to_state = DocumentImportProcessState.CANCELLED) |
| `PROFILED` | `EXTRACTED` | handler.can_transit_to(to_state = DocumentImportProcessState.EXTRACTED) | handler.perform_state_transition(to_state = DocumentImportProcessState.EXTRACTED) |
| `PROFILED` | `UNSUPPORTED` | handler.can_transit_to(to_state = DocumentImportProcessState.UNSUPPORTED) | handler.perform_state_transition(to_state = DocumentImportProcessState.UNSUPPORTED) |
| `PROFILED` | `FAILED` | handler.can_transit_to(to_state = DocumentImportProcessState.FAILED) | handler.perform_state_transition(to_state = DocumentImportProcessState.FAILED) |
| `PROFILED` | `CANCELLED` | handler.can_transit_to(to_state = DocumentImportProcessState.CANCELLED) | handler.perform_state_transition(to_state = DocumentImportProcessState.CANCELLED) |
| `EXTRACTED` | `STRUCTURED` | handler.can_transit_to(to_state = DocumentImportProcessState.STRUCTURED) | handler.perform_state_transition(to_state = DocumentImportProcessState.STRUCTURED) |
| `EXTRACTED` | `REVIEW_REQUIRED` | handler.can_transit_to(to_state = DocumentImportProcessState.REVIEW_REQUIRED) | handler.perform_state_transition(to_state = DocumentImportProcessState.REVIEW_REQUIRED) |
| `EXTRACTED` | `FAILED` | handler.can_transit_to(to_state = DocumentImportProcessState.FAILED) | handler.perform_state_transition(to_state = DocumentImportProcessState.FAILED) |
| `EXTRACTED` | `CANCELLED` | handler.can_transit_to(to_state = DocumentImportProcessState.CANCELLED) | handler.perform_state_transition(to_state = DocumentImportProcessState.CANCELLED) |
| `STRUCTURED` | `INSTANTIATED` | handler.can_transit_to(to_state = DocumentImportProcessState.INSTANTIATED) | handler.perform_state_transition(to_state = DocumentImportProcessState.INSTANTIATED) |
| `STRUCTURED` | `REVIEW_REQUIRED` | handler.can_transit_to(to_state = DocumentImportProcessState.REVIEW_REQUIRED) | handler.perform_state_transition(to_state = DocumentImportProcessState.REVIEW_REQUIRED) |
| `STRUCTURED` | `FAILED` | handler.can_transit_to(to_state = DocumentImportProcessState.FAILED) | handler.perform_state_transition(to_state = DocumentImportProcessState.FAILED) |
| `STRUCTURED` | `CANCELLED` | handler.can_transit_to(to_state = DocumentImportProcessState.CANCELLED) | handler.perform_state_transition(to_state = DocumentImportProcessState.CANCELLED) |
| `INSTANTIATED` | `RESOLVED` | handler.can_transit_to(to_state = DocumentImportProcessState.RESOLVED) | handler.perform_state_transition(to_state = DocumentImportProcessState.RESOLVED) |
| `INSTANTIATED` | `REVIEW_REQUIRED` | handler.can_transit_to(to_state = DocumentImportProcessState.REVIEW_REQUIRED) | handler.perform_state_transition(to_state = DocumentImportProcessState.REVIEW_REQUIRED) |
| `INSTANTIATED` | `FAILED` | handler.can_transit_to(to_state = DocumentImportProcessState.FAILED) | handler.perform_state_transition(to_state = DocumentImportProcessState.FAILED) |
| `INSTANTIATED` | `CANCELLED` | handler.can_transit_to(to_state = DocumentImportProcessState.CANCELLED) | handler.perform_state_transition(to_state = DocumentImportProcessState.CANCELLED) |
| `RESOLVED` | `VALIDATED` | handler.can_transit_to(to_state = DocumentImportProcessState.VALIDATED) | handler.perform_state_transition(to_state = DocumentImportProcessState.VALIDATED) |
| `RESOLVED` | `REVIEW_REQUIRED` | handler.can_transit_to(to_state = DocumentImportProcessState.REVIEW_REQUIRED) | handler.perform_state_transition(to_state = DocumentImportProcessState.REVIEW_REQUIRED) |
| `RESOLVED` | `FAILED` | handler.can_transit_to(to_state = DocumentImportProcessState.FAILED) | handler.perform_state_transition(to_state = DocumentImportProcessState.FAILED) |
| `RESOLVED` | `CANCELLED` | handler.can_transit_to(to_state = DocumentImportProcessState.CANCELLED) | handler.perform_state_transition(to_state = DocumentImportProcessState.CANCELLED) |
| `VALIDATED` | `LINKED` | handler.can_transit_to(to_state = DocumentImportProcessState.LINKED) | handler.perform_state_transition(to_state = DocumentImportProcessState.LINKED) |
| `VALIDATED` | `REJECTED` | handler.can_transit_to(to_state = DocumentImportProcessState.REJECTED) | handler.perform_state_transition(to_state = DocumentImportProcessState.REJECTED) |
| `VALIDATED` | `REVIEW_REQUIRED` | handler.can_transit_to(to_state = DocumentImportProcessState.REVIEW_REQUIRED) | handler.perform_state_transition(to_state = DocumentImportProcessState.REVIEW_REQUIRED) |
| `VALIDATED` | `FAILED` | handler.can_transit_to(to_state = DocumentImportProcessState.FAILED) | handler.perform_state_transition(to_state = DocumentImportProcessState.FAILED) |
| `VALIDATED` | `CANCELLED` | handler.can_transit_to(to_state = DocumentImportProcessState.CANCELLED) | handler.perform_state_transition(to_state = DocumentImportProcessState.CANCELLED) |
| `LINKED` | `PACKAGED` | handler.can_transit_to(to_state = DocumentImportProcessState.PACKAGED) | handler.perform_state_transition(to_state = DocumentImportProcessState.PACKAGED) |
| `LINKED` | `FAILED` | handler.can_transit_to(to_state = DocumentImportProcessState.FAILED) | handler.perform_state_transition(to_state = DocumentImportProcessState.FAILED) |
| `LINKED` | `CANCELLED` | handler.can_transit_to(to_state = DocumentImportProcessState.CANCELLED) | handler.perform_state_transition(to_state = DocumentImportProcessState.CANCELLED) |
| `PACKAGED` | `PUBLISHED` | handler.can_transit_to(to_state = DocumentImportProcessState.PUBLISHED) | handler.perform_state_transition(to_state = DocumentImportProcessState.PUBLISHED) |
| `PACKAGED` | `REJECTED` | handler.can_transit_to(to_state = DocumentImportProcessState.REJECTED) | handler.perform_state_transition(to_state = DocumentImportProcessState.REJECTED) |
| `PACKAGED` | `FAILED` | handler.can_transit_to(to_state = DocumentImportProcessState.FAILED) | handler.perform_state_transition(to_state = DocumentImportProcessState.FAILED) |
| `PACKAGED` | `CANCELLED` | handler.can_transit_to(to_state = DocumentImportProcessState.CANCELLED) | handler.perform_state_transition(to_state = DocumentImportProcessState.CANCELLED) |
| `PUBLISHED` | `SUPERSEDED` | handler.can_transit_to(to_state = DocumentImportProcessState.SUPERSEDED) | handler.perform_state_transition(to_state = DocumentImportProcessState.SUPERSEDED) |
| `REVIEW_REQUIRED` | `STRUCTURED` | handler.can_transit_to(to_state = DocumentImportProcessState.STRUCTURED) | handler.perform_state_transition(to_state = DocumentImportProcessState.STRUCTURED) |
| `REVIEW_REQUIRED` | `INSTANTIATED` | handler.can_transit_to(to_state = DocumentImportProcessState.INSTANTIATED) | handler.perform_state_transition(to_state = DocumentImportProcessState.INSTANTIATED) |
| `REVIEW_REQUIRED` | `RESOLVED` | handler.can_transit_to(to_state = DocumentImportProcessState.RESOLVED) | handler.perform_state_transition(to_state = DocumentImportProcessState.RESOLVED) |
| `REVIEW_REQUIRED` | `VALIDATED` | handler.can_transit_to(to_state = DocumentImportProcessState.VALIDATED) | handler.perform_state_transition(to_state = DocumentImportProcessState.VALIDATED) |
| `REVIEW_REQUIRED` | `REJECTED` | handler.can_transit_to(to_state = DocumentImportProcessState.REJECTED) | handler.perform_state_transition(to_state = DocumentImportProcessState.REJECTED) |
| `REVIEW_REQUIRED` | `CANCELLED` | handler.can_transit_to(to_state = DocumentImportProcessState.CANCELLED) | handler.perform_state_transition(to_state = DocumentImportProcessState.CANCELLED) |

## Runtime findings

- `DocumentImportStateTransitionHandler.execute()` does not instantiate `StateWorkerAdapter` and does not load `standard_document_import.yaml`. It directly writes JSON artifacts for the ten-state main path from `INGESTED` through `PUBLISHED`.
- The YAML branches (`REVIEW_REQUIRED`, `UNSUPPORTED`, `REJECTED`, `FAILED`, `CANCELLED`, `SUPERSEDED`) are declarative only in the current handler.
- The enum's `get_state()` references undefined `ElementImportProcessState`; the direct handler avoids that method, but generic state lookup is broken in this snapshot.
