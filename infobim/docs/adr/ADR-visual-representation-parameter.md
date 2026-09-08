# Visual representation parameter

InfoBIM project views use `representation` as the canonical parameter for the generated visual artifact.

Examples:

```bash
infobim view --project <project_id> --representation html
infobim view --project <project_id> --representation pdf
infobim view --project <project_id> --representation html --language pt-BR
```

`representation` is preferred over `format` because it describes the visual manifestation of the same semantic view, rather than a generic data serialization format.

The language parameter is optional. When omitted, the view preserves the language already resolved by the OntoBDC context/configuration chain. An explicit `--language` value overrides that resolved language for the generated view.

HTML remains the default representation for backward compatibility. PDF is recognized by the parameter strategy, but its renderer is intentionally not implemented in this change.
