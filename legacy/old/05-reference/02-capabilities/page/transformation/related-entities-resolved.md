# Related Entities Resolved

`RelatedEntitiesResolvedCapability` is the Page-data boundary for semantic relations associated with the current element.

| Property | Value |
| --- | --- |
| Capability ID | `org.ontobdc.view.plugin.capability.transformation.target.related_entities_resolved` |
| Capability type | `TransformationCapability` |
| Resulting state | `__related_entities_resolved__` |
| Implementation | [`related_entities_resolved.py`](https://github.com/EliasMPJunior/ontobdc-view/blob/r008/v0.9/src/ontobdc_view/page/plugin/capability/transformation/related_entities_resolved.py) |
| Current status | Placeholder with explicit empty-list materialization |

## Current behavior

```mermaid
flowchart LR
    A[Page-data payload] --> B{related_entities exists?}
    B -->|yes| C[Preserve current value]
    B -->|no| D[Set related_entities = []]
    C --> E[Return state]
    D --> E
```

The current capability does **not** execute relation rules or query linksets. It calls `setdefault("related_entities", [])`, so an existing value is preserved and an absent value becomes an empty list.

## Satisfaction check

`check()` returns `True` when `payload["related_entities"]` is a list. Because `execute()` establishes that invariant when the key is absent, `check()` is satisfied immediately after a normal execution.

IfcWorkSchedule and other builders without relation rules use this placeholder. WorkStream explicitly maps the same state to `WorkStreamRelatedEntitiesResolvedCapability`, which materializes its resources, linksets, and annotations.

Future relation resolution can be implemented behind this same state without changing the enclosing statecharts.
