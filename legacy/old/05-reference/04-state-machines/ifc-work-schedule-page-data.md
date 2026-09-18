[↑ Back to state-machine inventory](index.md)

# IfcWorkSchedule Page-data machine

> **Status:** Absorbed; not present in the current code.

The `IfcWorkSchedulePageData` machine from `ontobdc-view@r008/v0.9` has no enum, YAML statechart, evaluator, or transition handler in the audited `master` trees.

## Former states

The historical machine used `UNDEFINED`, `FACADES_LOCATED`, `FACADE_DATA_GATHERED`, `MISSING_DATA_FILLED`, `RELATED_ENTITIES_RESOLVED`, and `TOOLBAR_CONFIGURATION_GATHERED`. They are not current enum members.

## Where the work moved

Current code distributes this responsibility across:

- [`DataGatheredCapability`](https://github.com/EliasMPJunior/ontobdc-wip/blob/fe6d756c44141cdc14234937ce1e659384950b26/src/ontobdc/view/plugin/capability/transformation/data_gathered.py), which merges dataset and entity information into the Surface JSON-LD state;
- [`EntityViewsPublishedCapability`](https://github.com/EliasMPJunior/ontobdc-wip/blob/fe6d756c44141cdc14234937ce1e659384950b26/src/ontobdc/view/plugin/capability/transformation/entity_views_published.py), which renders supported entity views;
- [`GanttScriptGenerationProcessState`](gantt-script-generation.md), which builds the IfcWorkSchedule browser runtime.

The old Page-data lifecycle was absorbed into capabilities owned by the Surface and script-generation pipelines; it was not preserved under a new enum name.

## Historical source

- [Former builder, handler, and enum](https://github.com/EliasMPJunior/ontobdc-view/blob/r008/v0.9/src/ontobdc_view/page/plugin/builder/ifc_work_schedule/ifc_work_schedule.py)
- [Former YAML](https://github.com/EliasMPJunior/ontobdc-view/blob/r008/v0.9/src/ontobdc_view/page/plugin/builder/ifc_work_schedule/ifc_work_schedule_page_data.yaml)
