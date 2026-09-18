# WorkStream Related Entities Resolved

`WorkStreamRelatedEntitiesResolvedCapability` materializes the read model needed by the static WorkStream Entity Page. It is entity-specific: the WorkStream state adapter maps `RELATED_ENTITIES_RESOLVED` to this capability instead of the generic relation stub.

| Property | Value |
| --- | --- |
| Capability ID | `org.ontobdc.view.plugin.capability.transformation.target.work_stream_related_entities_resolved` |
| Capability type | `TransformationCapability` |
| Resulting state | `__related_entities_resolved__` |
| Implementation | `page/plugin/capability/transformation/work_stream_related_entities_resolved.py` |

## Inputs

The capability reads generated and semantic artifacts during `ontobdc view`:

- the `DATA_GATHERED` JSON-LD graph, from which it selects supported file-resource nodes;
- `WorkStreamResource.ttl` linksets for explicit dimension-to-resource relations;
- `WorkStreamSuggested.ttl` linksets for suggested relations;
- `EnrichmentAnnotation.ttl` files for annotations associated with the current WorkStream dimensions;
- the current element URI, source node, dimension model, and mutable payload from `PageDataContextAdapter`.

Malformed or unrelated linkset and annotation files are ignored. Relations are accepted only when their dimension URI belongs to the current WorkStream element.

## Payload mutations

The capability writes:

| Field | Meaning |
| --- | --- |
| `@graph` | Current WorkStream source node followed by the file-resource nodes needed by the page. |
| `related_entities` | Deterministic per-dimension lists of related and suggested resource identifiers. |
| `annotations` | Persisted annotations belonging to the current WorkStream dimensions. |
| `dimensions[*].related_resources` | Render-ready models for explicitly related resources. |
| `dimensions[*].suggested_resources` | Render-ready models for suggestions not already related. |
| `dimensions[*].found_resources` | All discovered resource models available to that dimension's Found tab. |

Each render-ready resource includes its identifier, title, container-relative path and link, preview kind, category, and associated annotations. Images and PDFs receive inline preview kinds; other formats use a direct-open fallback.

## Runtime boundary

Resolution happens before HTML publication. The completed payload is written to `.__ontobdc__/view/work_stream/<identifier>.jsonld`, and Jinja materializes it into the sibling HTML file. Opening the page does not connect to a folder, query linksets, or mutate relations.

The generic [Related Entities Resolved](related-entities-resolved.md) capability remains a placeholder for entity builders without concrete relation semantics.

See [WorkStream Page data](../../../04-state-machines/work-stream-page-data.md) and [WorkStream Entity Page](../../../05-layout/work-stream-entity-page.md).
