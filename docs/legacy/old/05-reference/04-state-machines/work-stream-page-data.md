[↑ Back to state-machine inventory](index.md)

# WorkStream Page-data machine

> **Status:** Absorbed; not present in the current code.

The `WorkStreamPageData` machine documented from `ontobdc-view@r008/v0.9` is not a machine in any audited `master` tree. There is no current `WorkStreamPageData` enum, YAML statechart, evaluator, or transition handler.

## Former states

The released historical machine used `UNDEFINED`, `FACADES_LOCATED`, `FACADE_DATA_GATHERED`, `DIMENSION_CARDS_GENERATED`, `MISSING_DATA_FILLED`, `RELATED_ENTITIES_RESOLVED`, and `TOOLBAR_CONFIGURATION_GATHERED`. These are not members of a current enum and therefore are not part of the current machine inventory.

## Where the work moved

Current code performs the relevant work inside the outer Surface pipeline:

- [`DataGatheredCapability`](https://github.com/EliasMPJunior/ontobdc-wip/blob/fe6d756c44141cdc14234937ce1e659384950b26/src/ontobdc/view/plugin/capability/transformation/data_gathered.py) materializes container, dataset, entity, facade-field, and file data into the Surface JSON-LD state;
- [`EntityViewsPublishedCapability`](https://github.com/EliasMPJunior/ontobdc-wip/blob/fe6d756c44141cdc14234937ce1e659384950b26/src/ontobdc/view/plugin/capability/transformation/entity_views_published.py) renders supported standalone entity views;
- [`WorkStreamScriptGenerationProcessState`](work-stream-script-generation.md) builds the WorkStream browser runtime.

This is an architectural absorption, not a renamed state machine: the former per-entity Page-data state boundary no longer exists.

## Historical source

- [Former builder, handler, and enum](https://github.com/EliasMPJunior/ontobdc-view/blob/r008/v0.9/src/ontobdc_view/page/plugin/builder/work_stream/work_stream.py)
- [Former YAML](https://github.com/EliasMPJunior/ontobdc-view/blob/r008/v0.9/src/ontobdc_view/page/plugin/builder/work_stream/work_stream_page_data.yaml)
