# Page asset and output layout

The on-disk conventions the Page subsystem depends on. Path mismatches here fail loudly
(`ValueError` / `Shared Entity Page asset was not found`) rather than silently, but they are
easy to get wrong when adding an entity.

**Source of truth:** `EliasMPJunior/ontobdc-view@r008/v0.9`.

## Packaged assets (inside `ontobdc_view`)

```text
src/ontobdc_view/page/
├── adapter/
│   ├── context.py     PageDataContextAdapter, PageScriptGenerationContextAdapter
│   ├── facade.py      FacadeLookupAdapter
│   ├── script.py      PageScriptAssetAdapter, EntityPageScriptGeneratorLoader
│   └── template.py    EntityPageTemplateAdapter
├── plugin/
│   ├── builder/<entity>/
│   │   ├── <entity>.py                        page-data state type + handlers
│   │   ├── <entity>_page_data.yaml            page-data statechart
│   │   ├── <entity>_script_generation.py      script-gen state type + handlers
│   │   ├── <entity>_script_generation.yaml    script-gen statechart
│   │   └── <name>.js                          runtime scripts, copied verbatim
│   ├── capability/transformation/*.py         generic, entity-agnostic capabilities
│   └── asset/entity/
│       ├── common/
│       │   ├── entity_page_header.html.j2     shared, included by every entity template
│       │   └── entity_page.css                shared, concatenated before entity CSS
│       └── <entity>_view/
│           ├── <entity>_view.html.j2          entity-specific template
│           └── <entity>_view.css              entity-specific styles
```

| Adapter method | Resolves to |
| --- | --- |
| `EntityPageTemplateAdapter._read_shared(name)` | `page/plugin/asset/entity/common/<name>` |
| `EntityPageTemplateAdapter._read_entity(dir, name)` | `page/plugin/asset/entity/<dir>/<name>` |
| `PageScriptAssetAdapter.source(context, name)` | `<builder_package>/<name>.js` |

`view_directory` (`<entity>`) resolves to the asset directory `<entity>_view`; the template
and CSS filenames are `<entity>_view.html.j2` / `<entity>_view.css`.

## Generated output (inside a container)

```text
<container>/.__ontobdc__/
├── view/
│   └── <entity>/                              <entity> = snake_case of the entity type local name
│       ├── <identifier>.jsonld                Page-data payload
│       ├── <identifier>.html                  published standalone Page
│       └── <name>.js                          runtime scripts copied by script generation
└── ...
<dataset>/.__ontobdc__/linkset/facade.ttl      materialized Facade, read by FacadesLocatedCapability
```

`<identifier>` is the element's `dcterms:identifier` (slugified), falling back to the element
URI's last segment. It is chosen so the published `<identifier>.html` matches the URL the
entity Tile builds for its detail-page link.

`PageScriptAssetAdapter.target_path` writes runtime scripts to
`<container>/.__ontobdc__/view/<view_directory>/<name>.js`, and validates `view_directory`
against `^[a-z][a-z0-9_]*$`.

## See also

- [Adding an Entity Page](../../04-guides/adding-an-entity-page.md)
- [Facade](../../02-concepts/facade.md)
- [Page transformation capabilities](../02-capabilities/page/transformation/index.md)
- [WorkStream Entity Page](work-stream-entity-page.md)
