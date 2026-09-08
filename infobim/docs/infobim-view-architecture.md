# InfoBIM View architecture

## Implemented flow

`infobim view` resolves the `IfcProject.GlobalId` through the existing
`ProjectIdStrategy`, reads the Project and distributed IFC catalog through the
same repositories used by `infobim ifc`, and enters the standard OntoBDC View
state machine.

The generic pipeline remains authoritative:

1. container validation and publishability;
2. RDF/JSON-LD data gathering;
3. Surface initialization, enrichment and selection;
4. semantic component matching and assembly;
5. packaging, validation and entity-view publication.

InfoBIM specializes two transitions only:

- after data gathering it adds an ephemeral Project/IFC-model presentation
  projection to the ETL artifact without mutating source datasets;
- during matching it requests the Project Tile, excludes the Distributed IFC
  Tile and the technical container from the default content, and retains
  generic OntoBDC matches for non-IFC entities.

The existing OntoBDC renderer and `ontobdc-view` Web Components package the
result into the offline `index.html`. The command does not construct HTML.

## BIM projection

The optional IFC Model Tile aggregates IFC classes discovered through each dataset's
`linkset/facade.ttl`. It reuses `IfcClassCatalogRepository` to deduplicate
classes and elements across datasets. Navigation is local:

```text
IFC Model -> classes -> elements -> element details
```

Element details use IFC `GlobalId`, the exposed facade fields and origin
datasets. IFC entities are not emitted as one Tile per instance or class.

## Generic entities and annotations

Non-IFC `SurfaceableEntity` resources continue through the generic OntoBDC
matcher. InfoBIM does not package a Subject workspace or annotation runtime;
`Thread` remains an ordinary persistent, navigable OntoBDC `DataEntity` when
it is present in gathered data.

## Entity context

The bundled InfoBIM RDF contract declares:

```text
IfcWorkSchedule assignsRelatedClass IfcTask, IfcTaskTime
```

The relation is representation-neutral. The XLSX adapter currently chooses to
materialize one worksheet per declared entity, while the View independently
presents the root `IfcWorkSchedule` through a semantic Tile. No worksheet name
or workbook structure is consulted by the presentation matcher.

## Deliberate limits

- Spatial hierarchy reconstruction from `IfcRelAggregates` and
  `IfcRelContainedInSpatialStructure` is the next BIM projection slice. The
  current class navigation remains valid when Site, Building or Storey levels
  are absent and does not invent placeholder nodes.
- The first schedule Tile presents the semantic root fields. Task/time drill
  down can be added from real relations after those instances are populated.
- Component scripts are embedded for offline use; no server or cloud runtime
  is needed after generation.
