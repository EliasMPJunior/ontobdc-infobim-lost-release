from __future__ import annotations

import html
import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import ClassVar, Dict, List, Optional, Tuple

import yaml


@dataclass(frozen=True)
class TilePreviewCase:
    tag: str
    columns: int
    rows: int


class TileStandaloneHtmlBuilder:
    """Build a temporary page containing exactly one shipped Tile.

    Shared between the automated Playwright regression suite
    (``ontobdc_view``'s own ``test/view/test_tile_preview.py``) and
    ``ontobdc dev test --tile <slug> --view``, so both ways of exercising a
    Tile always render it exactly the same way.
    """

    SLOT_SIZE: ClassVar[int] = 96
    GAP: ClassVar[int] = 12
    THEME_TOKENS: ClassVar[Dict[str, Dict[str, str]]] = {
        "light": {
            "background": "#ffffff",
            "foreground": "#0f172a",
            "accent": "#0284c7",
            "borderColor": "rgba(2,132,199,.35)",
        },
        "dark": {
            "background": "#000000",
            "foreground": "#f8fafc",
            "accent": "#38bdf8",
            "borderColor": "rgba(56,189,248,.55)",
        },
    }
    LANGUAGES: ClassVar[List[Dict[str, str]]] = [
        {
            "code": "en",
            "label": "English",
            "short_label": "EN",
            "flag": "🇺🇸",
        },
        {
            "code": "pt-BR",
            "label": "Portugues (Brasil)",
            "short_label": "PT-BR",
            "flag": "🇧🇷",
        },
        {
            "code": "pt-PT",
            "label": "Portugues (Portugal)",
            "short_label": "PT-PT",
            "flag": "🇵🇹",
        },
        {
            "code": "es",
            "label": "Espanol",
            "short_label": "ES",
            "flag": "🇪🇸",
        },
    ]
    BRAND: ClassVar[Dict[str, str]] = {
        "name": "OntoBDC",
        "mark_svg": (
            '<svg viewBox="0 0 64 64" aria-hidden="true">'
            '<circle cx="32" cy="32" r="25" fill="none" '
            'stroke="currentColor" stroke-width="8"/>'
            '<circle cx="32" cy="32" r="7" fill="currentColor"/></svg>'
        ),
        "logotype_svg": (
            '<svg viewBox="0 0 260 64" aria-hidden="true">'
            '<circle cx="32" cy="32" r="23" fill="none" '
            'stroke="var(--onto-theme-accent, currentColor)" stroke-width="7"/>'
            '<circle cx="32" cy="32" r="6" '
            'fill="var(--onto-theme-accent, currentColor)"/>'
            '<text x="68" y="42" fill="currentColor" '
            'font-family="system-ui, sans-serif" font-size="31" '
            'font-weight="700">OntoBDC</text></svg>'
        ),
        "slogan": "Data with Brains",
    }
    I18N_NAMESPACE_BY_TAG: ClassVar[Dict[str, str]] = {
        "onto-language-tile": "language_tile",
        "onto-theme-tile": "theme_tile",
        "onto-logo-tile": "logo_tile",
        "onto-file-tree-tile": "file_tree_tile",
        "onto-workstream-tile": "workstream_tile",
        "onto-csv-file-tile": "csv_file_tile",
        "onto-photo-tile": "photo_tile",
        "onto-data-container-tile": "data_container_tile",
        "onto-file-size-tile": "file_size_tile",
        "onto-pdf-file-tile": "common",
        "onto-generic-file-tile": "common",
        "onto-image-file-tile": "common",
        "onto-file-viewer-tile": "file_tree_tile",
    }

    _MIGRATED_TILE_ROOT_PARTS: Tuple[str, ...] = (
        "src",
        "ontobdc_view",
        "component",
        "plugin",
        "tile",
    )

    _MOCK_RESOURCE_ID: ClassVar[str] = "urn:ontobdc:test:tile-resource"
    _MOCK_ENTITY_FILE_NAME: ClassVar[str] = "mock.json"

    # mock.json's "kind" field selects how the Tile gets mocked -- most
    # Tiles read a JSON-LD node from #ontobdc-surface-jsonld (the default,
    # "entity"), but some (onto-file-viewer-tile) are only ever driven by a
    # public method call (openFile(path)) and have no notion of
    # data-ontobdc-resource/JSON-LD at all.
    _MOCK_ENTITY_KIND: ClassVar[str] = "entity"
    _MOCK_METHOD_CALL_KIND: ClassVar[str] = "method_call"
    _JS_IDENTIFIER_PATTERN: ClassVar[re.Pattern[str]] = re.compile(
        r"^[A-Za-z_$][A-Za-z0-9_$]*$"
    )

    def __init__(self, repository_root: Path) -> None:
        self._repository_root: Path = repository_root
        # Only tiles actually migrated out of old/ into the real package
        # are ever read from here -- old/ itself is never touched. Callers
        # for tags not yet migrated should check is_migrated() first.
        self._locale_directory: Path = (
            repository_root
            / "src"
            / "ontobdc_view"
            / "component"
            / "adapter"
            / "i18n"
            / "locale"
        )

    def write(
        self,
        *,
        case: TilePreviewCase,
        theme: str,
        output_path: Path,
    ) -> Path:
        output_path.write_text(
            self.build(case=case, theme=theme),
            encoding="utf-8",
        )
        return output_path

    def build(self, *, case: TilePreviewCase, theme: str) -> str:
        javascript: str = self._resolved_javascript(case.tag)
        tokens: Dict[str, str] = self.THEME_TOKENS[theme]
        width: int = (
            case.columns * self.SLOT_SIZE
            + max(0, case.columns - 1) * self.GAP
        )
        height: int = (
            case.rows * self.SLOT_SIZE
            + max(0, case.rows - 1) * self.GAP
        )
        safe_tag: str = html.escape(case.tag)
        safe_title: str = html.escape(f"Standalone {case.tag}")
        script_source: str = javascript.replace("</script>", "<\\/script>")
        mock_button_html: str
        mock_script: str
        mock_button_html, mock_script = self._mock_injection(case.tag, safe_tag)

        return f"""<!doctype html>
<html lang="en" data-language="en" data-theme="{theme}">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{safe_title}</title>
  <style>
    :root {{
      color-scheme: {theme};
      --onto-theme-background: {tokens['background']};
      --onto-theme-foreground: {tokens['foreground']};
      --onto-theme-accent: {tokens['accent']};
      --onto-theme-border-color: {tokens['borderColor']};
      --onto-surface-slot-size: {self.SLOT_SIZE}px;
    }}
    html, body {{
      margin: 0;
      min-height: 100%;
      background: var(--onto-theme-background);
      color: var(--onto-theme-foreground);
      font-family: system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
    }}
    body {{
      min-height: 100vh;
      display: grid;
      place-items: center;
      padding-bottom: 48px;
    }}
    #tile-preview {{
      width: {width}px;
      height: {height}px;
      display: grid;
      place-items: stretch;
    }}
    #tile-preview > {safe_tag} {{
      display: block;
      width: 100%;
      height: 100%;
      min-width: 0;
      min-height: 0;
    }}
    #preview-toolbar {{
      position: fixed;
      inset: 12px 12px auto auto;
      z-index: 1000;
    }}
    #mock-data-btn {{
      all: unset;
      cursor: pointer;
      padding: 6px 14px;
      border-radius: 8px;
      border: 1px solid var(--onto-theme-border-color);
      background: var(--onto-theme-accent);
      color: var(--onto-theme-background);
      font: 700 12px/1 system-ui, -apple-system, sans-serif;
      letter-spacing: .04em;
      text-transform: uppercase;
    }}
    #mock-data-btn:hover {{
      filter: brightness(1.08);
    }}
    #event-monitor {{
      position: fixed;
      inset: auto 0 0 0;
      min-height: 48px;
      display: flex;
      align-items: center;
      gap: 10px;
      padding: 8px 14px;
      border-top: 1px solid var(--onto-theme-border-color);
      background: var(--onto-theme-background);
      color: var(--onto-theme-foreground);
      font: 12px/1.35 ui-monospace, SFMono-Regular, Menlo, Consolas, monospace;
      z-index: 1000;
    }}
    #event-monitor-label {{
      color: var(--onto-theme-accent);
      font-weight: 800;
      text-transform: uppercase;
      letter-spacing: .08em;
    }}
    #event-monitor-name {{
      font-weight: 800;
    }}
    #event-monitor-detail {{
      min-width: 0;
      overflow: hidden;
      text-overflow: ellipsis;
      white-space: nowrap;
      opacity: .8;
    }}
  </style>
</head>
<body>
  {mock_button_html}
  <main id="tile-preview">
    <{safe_tag}
      columns="{case.columns}"
      rows="{case.rows}"
      data-ontobdc-resource="{self._MOCK_RESOURCE_ID}"
    ></{safe_tag}>
  </main>
  <footer id="event-monitor" aria-live="polite">
    <span id="event-monitor-label">Event</span>
    <span id="event-monitor-name">—</span>
    <span id="event-monitor-detail">No event dispatched.</span>
  </footer>
  <script type="module">
const eventMonitorName = document.getElementById("event-monitor-name");
const eventMonitorDetail = document.getElementById("event-monitor-detail");
const originalDispatchEvent = EventTarget.prototype.dispatchEvent;
window.__ONTOBDC_PREVIEW_EVENTS__ = [];
EventTarget.prototype.dispatchEvent = function(event) {{
  let detail;
  if (event instanceof CustomEvent) detail = event.detail;

  let serializedDetail = "";
  if (detail !== undefined) {{
    try {{
      serializedDetail = JSON.stringify(detail);
    }} catch {{
      serializedDetail = String(detail);
    }}
  }}

  const target = this instanceof Element
    ? this.tagName.toLowerCase()
    : this === document
      ? "document"
      : this === window
        ? "window"
        : this.constructor?.name ?? "EventTarget";

  window.__ONTOBDC_PREVIEW_EVENTS__.push({{
    type: event.type,
    detail,
    target,
  }});
  eventMonitorName.textContent = event.type;
  eventMonitorDetail.textContent = serializedDetail || `(target: ${{target}})`;

  return originalDispatchEvent.call(this, event);
}};
{mock_script}
{script_source}
  </script>
</body>
</html>
"""

    def _mock_directive_path(self, tag: str) -> Path:
        return self._tile_directory(tag) / self._MOCK_ENTITY_FILE_NAME

    def _mock_directive(self, tag: str) -> Optional[Dict[str, object]]:
        """The tile's own mock.json, if it shipped one, else None."""
        mock_directive_path: Path = self._mock_directive_path(tag)
        if not mock_directive_path.is_file():
            return None
        loaded: object = json.loads(
            mock_directive_path.read_text(encoding="utf-8")
        )
        if not isinstance(loaded, dict):
            raise AssertionError(f"Invalid mock.json: {mock_directive_path}")
        return loaded

    def _mock_injection(self, tag: str, safe_tag: str) -> Tuple[str, str]:
        """HTML for the "Mock" button and its click-handler script for *tag*.

        Returns two empty strings when the tile ships no mock.json in its
        own directory -- the page must still open truly empty by default,
        this is opt-in per click, never automatic.
        """
        directive: Optional[Dict[str, object]] = self._mock_directive(tag)
        if directive is None:
            return "", ""

        button_html: str = (
            '<div id="preview-toolbar">'
            '<button type="button" id="mock-data-btn">Mock</button>'
            "</div>"
        )

        kind: str = str(directive.get("kind", self._MOCK_ENTITY_KIND))
        if kind == self._MOCK_METHOD_CALL_KIND:
            return button_html, self._mock_method_call_script(directive, safe_tag)
        if kind != self._MOCK_ENTITY_KIND:
            raise AssertionError(
                f"Unknown mock.json \"kind\" for {tag}: {kind!r}"
            )
        return button_html, self._mock_entity_script(directive, safe_tag)

    def _mock_entity_script(
        self,
        mock_entity: Dict[str, object],
        safe_tag: str,
    ) -> str:
        """Click handler that injects *mock_entity* as the Tile's whole
        #ontobdc-surface-jsonld graph -- for Tiles that read their data from
        a JSON-LD node keyed by data-ontobdc-resource (the common case)."""
        mock_payload_json: str = json.dumps(
            [mock_entity],
            ensure_ascii=False,
            separators=(",", ":"),
        ).replace("</script>", "<\\/script>")

        return f"""
document.getElementById("mock-data-btn")?.addEventListener("click", () => {{
  const payload = {mock_payload_json};
  let jsonldScript = document.getElementById("ontobdc-surface-jsonld");
  if (!jsonldScript) {{
    jsonldScript = document.createElement("script");
    jsonldScript.type = "application/ld+json";
    jsonldScript.id = "ontobdc-surface-jsonld";
    document.body.appendChild(jsonldScript);
  }}
  jsonldScript.textContent = JSON.stringify(payload);

  // Re-rendering by toggling an attribute only works for Tiles that
  // observe it -- not every Tile does (e.g. onto-file-size-tile reads the
  // whole graph and observes nothing). Replacing the element with a fresh
  // instance of the same tag/attributes forces connectedCallback -> the
  // Tile's own initial #render() -- universal, regardless of what (if
  // anything) that Tile observes.
  const oldTile = document.querySelector("{safe_tag}");
  const freshTile = document.createElement(oldTile.tagName);
  for (const attribute of oldTile.attributes) {{
    freshTile.setAttribute(attribute.name, attribute.value);
  }}
  oldTile.replaceWith(freshTile);
}});
"""

    def _mock_method_call_script(
        self,
        directive: Dict[str, object],
        safe_tag: str,
    ) -> str:
        """Click handler that calls a public method directly on the Tile --
        for Tiles like onto-file-viewer-tile that are only ever driven by a
        method call (openFile(path)) and have no JSON-LD entity of their
        own to inject."""
        method_name: str = str(directive.get("method", ""))
        if not self._JS_IDENTIFIER_PATTERN.match(method_name):
            raise AssertionError(
                f"Invalid mock.json \"method\": {method_name!r}"
            )
        arguments_json: str = json.dumps(
            list(directive.get("arguments", [])),
            ensure_ascii=False,
            separators=(",", ":"),
        ).replace("</script>", "<\\/script>")

        return f"""
document.getElementById("mock-data-btn")?.addEventListener("click", () => {{
  const tile = document.querySelector("{safe_tag}");
  tile.{method_name}(...{arguments_json});
}});
"""

    def _tile_directory(self, tag: str) -> Path:
        # onto-language-tile -> language, onto-csv-file-tile -> csv-file, ...
        slug: str = tag.removeprefix("onto-").removesuffix("-tile")
        tile_root: Path = self._repository_root.joinpath(
            *self._MIGRATED_TILE_ROOT_PARTS
        )
        return tile_root / slug

    def _migrated_asset_path(self, tag: str) -> Path:
        return self._tile_directory(tag) / f"{tag}.js"

    def is_migrated(self, tag: str) -> bool:
        """Whether *tag* has been moved out of old/ into the real package."""
        return self._migrated_asset_path(tag).is_file()

    def _resolved_javascript(self, tag: str) -> str:
        asset_path: Path = self._migrated_asset_path(tag)
        if not asset_path.is_file():
            raise AssertionError(
                f"{tag} has not been migrated out of old/ yet -- "
                "call is_migrated() and skip before resolving its JS."
            )
        source: str = asset_path.read_text(encoding="utf-8")
        replacements: Dict[str, object] = {
            "__ONTOBDC_BUILD_THEMES__": [
                {
                    "name": name,
                    "label": name.title(),
                    "tokens": dict(tokens),
                    "options": {"transparentBackground": False},
                }
                for name, tokens in self.THEME_TOKENS.items()
            ],
            "__ONTOBDC_BUILD_LANGUAGES__": self.LANGUAGES,
            "__ONTOBDC_BUILD_BRAND__": self.BRAND,
            "__ONTOBDC_BUILD_I18N__": self._i18n_catalog(tag),
        }
        for placeholder, payload in replacements.items():
            if placeholder not in source:
                continue
            source = source.replace(
                placeholder,
                json.dumps(
                    payload,
                    ensure_ascii=False,
                    separators=(",", ":"),
                ),
            )

        if "__ONTOBDC_BUILD_" in source:
            raise AssertionError(
                f"Unresolved build placeholder in {asset_path.name}"
            )
        if tag not in source or "customElements.define" not in source:
            raise AssertionError(
                f"{asset_path.name} does not register the expected Tile {tag}"
            )
        return source

    def _i18n_catalog(self, tag: str) -> Dict[str, Dict[str, str]]:
        namespace: str = self.I18N_NAMESPACE_BY_TAG.get(tag, "common")
        catalog: Dict[str, Dict[str, str]] = {}
        for locale_path in sorted(self._locale_directory.glob("*.yaml")):
            loaded: object = yaml.safe_load(
                locale_path.read_text(encoding="utf-8")
            )
            if not isinstance(loaded, dict):
                raise AssertionError(f"Invalid locale catalog: {locale_path}")

            common: object = loaded.get("common", {})
            selected: object = loaded.get(namespace, {})
            values: Dict[str, str] = {}
            if isinstance(common, dict):
                values.update(
                    {
                        str(key): str(value)
                        for key, value in common.items()
                    }
                )
            if namespace != "common" and isinstance(selected, dict):
                values.update(
                    {
                        str(key): str(value)
                        for key, value in selected.items()
                    }
                )
            catalog[locale_path.stem] = values
        return catalog


# Every Tile known to the preview/regression tooling, keyed by its slug
# (the tag with the "onto-"/"-tile" wrapping stripped, e.g. "language" for
# "onto-language-tile") -- the same slug `ontobdc dev test --tile <slug>`
# takes on the command line.
CASES: Tuple[TilePreviewCase, ...] = (
    TilePreviewCase("onto-csv-file-tile", 6, 5),
    TilePreviewCase("onto-data-container-tile", 4, 2),
    TilePreviewCase("onto-date-time-tile", 2, 1),
    TilePreviewCase("onto-file-size-tile", 1, 1),
    TilePreviewCase("onto-file-tree-tile", 6, 4),
    TilePreviewCase("onto-file-viewer-tile", 6, 5),
    TilePreviewCase("onto-generic-file-tile", 6, 5),
    TilePreviewCase("onto-image-file-tile", 6, 5),
    TilePreviewCase("onto-language-tile", 1, 1),
    TilePreviewCase("onto-logo-tile", 3, 1),
    TilePreviewCase("onto-pdf-file-tile", 6, 5),
    TilePreviewCase("onto-photo-tile", 4, 3),
    TilePreviewCase("onto-theme-tile", 1, 1),
    TilePreviewCase("onto-wind-speed-tile", 1, 1),
    TilePreviewCase("onto-workstream-tile", 6, 3),
)

CASE_BY_SLUG: Dict[str, TilePreviewCase] = {
    case.tag.removeprefix("onto-").removesuffix("-tile"): case
    for case in CASES
}
