import html
import json
import re
from pathlib import Path
from typing import Any, Dict, Iterable, List, Mapping, Optional

from ontobdc_view.surface.domain.machine.standard_surface_html.state import SurfaceGenerationProcessState


STATE_META_NAME = "ontobdc:surface-state"
JSONLD_ID = "ontobdc-surface-jsonld"
CONFIG_ID = "ontobdc-surface-config"
MATCHES_ID = "ontobdc-surface-matches"
DEFAULT_LAYOUTS_ID = "ontobdc-surface-default-layouts"
DEFAULT_LAYOUTS_BOOTSTRAP_ID = "ontobdc-surface-default-layouts-bootstrap"
URL_STATE_BOOTSTRAP_ID = "ontobdc-surface-url-state"
COMPONENT_SCRIPT_ATTR = "data-ontobdc-surface-component"

# Canonical URL-controlled presentation parameters. The address bar is the
# only store for these — no cookie, no localStorage, no second in-page state
# — so they have to be named in exactly one place and read from there by
# every producer and consumer.
LANGUAGE_PARAM = "lang"
THEME_PARAM = "theme"
PRESENTATION_PARAMS = (LANGUAGE_PARAM, THEME_PARAM)
SURFACE_TAG = "onto-presentation-surface"
_CUSTOM_ELEMENT_RE = re.compile(r"^[a-z][a-z0-9._-]*-[a-z0-9._-]+$")


class SurfaceDocumentAdapter:
    """Read, normalize, assemble, and validate Presentation Surface HTML."""

    @classmethod
    def resolve_surface_path(cls, raw_path: Any) -> Path:
        if not isinstance(raw_path, (str, Path)) or not str(raw_path).strip():
            raise ValueError("surface_path is required")
        return Path(raw_path).expanduser().resolve()

    @classmethod
    def read_surface(cls, path: Path) -> str:
        return path.read_text(encoding="utf-8")

    @classmethod
    def write_surface(cls, path: Path, content: str) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")

    @classmethod
    def make_initial_html(cls, lang: str = "en") -> str:
        safe_lang = html.escape(lang or "en", quote=True)
        return f'''<!doctype html>
<html lang="{safe_lang}">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <meta name="{STATE_META_NAME}" content="surface_initialized">
  <title>OntoBDC Presentation Surface</title>
  <style>
    /* Without this, the default UA body margin shows through as a light
       border around a dark-themed Surface (the theme tile sets
       --onto-theme-background on documentElement, which onto-presentation-
       surface's :host already reads, but nothing before this covered the
       page canvas itself). Invisible in a light theme, hence unnoticed
       until dark mode. */
    html, body {{
      margin: 0;
      padding: 0;
      block-size: 100%;
      background: var(--onto-theme-background, #ffffff);
    }}
    {SURFACE_TAG} {{
      display: block;
      inline-size: 100%;
      block-size: 100dvh;
    }}
  </style>
</head>
<body>
  <{SURFACE_TAG}></{SURFACE_TAG}>
</body>
</html>
'''

    @classmethod
    def _insert_before_closing_tag(
        cls,
        document: str,
        tag: str,
        insertion: str,
    ) -> str:
        closing = f"</{tag}>"
        if closing not in document:
            raise ValueError(
                f"Surface document is missing a closing <{tag}> tag; "
                "refusing to insert content into a malformed document."
            )
        return document.replace(closing, f"  {insertion}\n{closing}", 1)

    @classmethod
    def set_state_marker(cls, document: str, state_name: str) -> str:
        marker = (
            f'<meta name="{STATE_META_NAME}" '
            f'content="{html.escape(state_name, quote=True)}">'
        )
        pattern = re.compile(
            rf"<meta\s+name=[\"']{re.escape(STATE_META_NAME)}[\"']"
            rf"\s+content=[\"'][^\"']*[\"']\s*/?>",
            re.IGNORECASE,
        )
        if pattern.search(document):
            return pattern.sub(marker, document, count=1)
        return cls._insert_before_closing_tag(document, "head", marker)

    @classmethod
    def get_state_marker(cls, document: str) -> Optional[str]:
        pattern = re.compile(
            rf"<meta\s+name=[\"']{re.escape(STATE_META_NAME)}[\"']"
            rf"\s+content=[\"']([^\"']+)[\"']\s*/?>",
            re.IGNORECASE,
        )
        match = pattern.search(document)
        return match.group(1).strip() if match else None

    @classmethod
    def state_reached(
        cls,
        document: str,
        target: SurfaceGenerationProcessState,
    ) -> bool:
        """Whether ``document``'s state marker is at or past ``target``."""
        marker = cls.get_state_marker(document)
        if not marker:
            return False

        states = list(SurfaceGenerationProcessState)
        try:
            current = next(
                state for state in states if state.value.strip("_") == marker
            )
        except StopIteration:
            return False
        return states.index(current) >= states.index(target)

    @classmethod
    def _json_script(
        cls,
        script_id: str,
        payload: Any,
        script_type: str = "application/json",
    ) -> str:
        body = json.dumps(
            payload,
            ensure_ascii=False,
            indent=2,
        ).replace("</", "<\\/")
        return (
            f'<script type="{script_type}" id="{script_id}">\n'
            f"{body}\n</script>"
        )

    @classmethod
    def upsert_json_script(
        cls,
        document: str,
        script_id: str,
        payload: Any,
        script_type: str = "application/json",
    ) -> str:
        replacement = cls._json_script(script_id, payload, script_type)
        pattern = re.compile(
            rf"<script\b[^>]*\bid=[\"']{re.escape(script_id)}[\"'][^>]*>"
            rf".*?</script>",
            re.IGNORECASE | re.DOTALL,
        )
        if pattern.search(document):
            return pattern.sub(replacement, document, count=1)
        return cls._insert_before_closing_tag(document, "head", replacement)

    @classmethod
    def upsert_raw_script(
        cls,
        document: str,
        script_id: str,
        script_type: str,
        body: str,
    ) -> str:
        safe_body = body.replace("</script>", "<\\/script>")
        replacement = (
            f'<script type="{script_type}" id="{script_id}">\n'
            f"{safe_body}\n</script>"
        )
        pattern = re.compile(
            rf"<script\b[^>]*\bid=[\"']{re.escape(script_id)}[\"'][^>]*>"
            rf".*?</script>",
            re.IGNORECASE | re.DOTALL,
        )
        if pattern.search(document):
            return pattern.sub(replacement, document, count=1)
        return cls._insert_before_closing_tag(document, "head", replacement)

    @classmethod
    def extract_json_script(cls, document: str, script_id: str) -> Any:
        pattern = re.compile(
            rf"<script\b[^>]*\bid=[\"']{re.escape(script_id)}[\"'][^>]*>"
            rf"(.*?)</script>",
            re.IGNORECASE | re.DOTALL,
        )
        match = pattern.search(document)
        if not match:
            raise ValueError(f"Missing script: {script_id}")
        return json.loads(match.group(1).replace("<\\/", "</"))

    @classmethod
    def normalize_surface_config(cls, raw: Any) -> Dict[str, Any]:
        source: Dict[str, Any] = dict(raw) if isinstance(raw, Mapping) else {}
        content = (
            source.get("content")
            if isinstance(source.get("content"), Mapping)
            else {}
        )
        operation = (
            source.get("operation")
            if isinstance(source.get("operation"), Mapping)
            else {}
        )
        pinned = (
            source.get("pinned")
            if isinstance(source.get("pinned"), Mapping)
            else {}
        )

        mode = str(content.get("mode", "scroll")).strip().lower()
        if mode not in {"scroll", "fixed"}:
            raise ValueError("surface content mode must be 'scroll' or 'fixed'")

        return {
            "operation": {"enabled": bool(operation.get("enabled", True))},
            "content": {"mode": mode},
            "pinned": {"enabled": bool(pinned.get("enabled", True))},
            "slotTarget": cls._positive_number(source.get("slotTarget"), 72),
            "gap": cls._non_negative_number(source.get("gap"), 12),
            "padding": cls._non_negative_number(source.get("padding"), 16),
            "tileMargin": cls._non_negative_number(
                source.get("tileMargin"),
                0,
            ),
        }

    @classmethod
    def normalize_matches(cls, raw: Any) -> List[Dict[str, Any]]:
        if raw is None:
            return []
        if not isinstance(raw, list):
            raise ValueError("surface_matches must be a list")

        normalized: List[Dict[str, Any]] = []
        for index, item in enumerate(raw):
            if not isinstance(item, Mapping):
                raise ValueError(f"surface_matches[{index}] must be an object")

            tile = str(item.get("tile", "")).strip().lower()
            if not _CUSTOM_ELEMENT_RE.fullmatch(tile):
                raise ValueError(
                    f"surface_matches[{index}].tile must be a valid "
                    "custom-element tag"
                )

            region = str(item.get("region", "content")).strip().lower()
            if region not in {"operation", "content", "pinned"}:
                raise ValueError(f"surface_matches[{index}].region is invalid")

            data_id = str(
                item.get("data", item.get("data_id", ""))
            ).strip()

            min_columns = cls._positive_int(item.get("minColumns"), 1)
            preferred_columns = cls._positive_int(
                item.get("preferredColumns"),
                min_columns,
            )
            max_columns = cls._positive_int(
                item.get("maxColumns"),
                preferred_columns,
            )
            min_rows = cls._positive_int(item.get("minRows"), 1)
            preferred_rows = cls._positive_int(
                item.get("preferredRows"),
                min_rows,
            )
            max_rows = cls._positive_int(
                item.get("maxRows"),
                preferred_rows,
            )

            if not (min_columns <= preferred_columns <= max_columns):
                raise ValueError(
                    f"surface_matches[{index}] has invalid column envelope"
                )
            if not (min_rows <= preferred_rows <= max_rows):
                raise ValueError(
                    f"surface_matches[{index}] has invalid row envelope"
                )
            if region in {"operation", "pinned"} and (
                min_rows != 1 or preferred_rows != 1 or max_rows != 1
            ):
                raise ValueError(
                    f"surface_matches[{index}] fixed-region Tiles must be "
                    "one row high"
                )

            normalized_item: Dict[str, Any] = {
                **dict(item),
                "tile": tile,
                "region": region,
                "minColumns": min_columns,
                "preferredColumns": preferred_columns,
                "maxColumns": max_columns,
                "minRows": min_rows,
                "preferredRows": preferred_rows,
                "maxRows": max_rows,
            }
            if data_id:
                normalized_item["data"] = data_id
            else:
                normalized_item.pop("data", None)
                normalized_item.pop("data_id", None)
            normalized.append(normalized_item)

        return normalized

    @classmethod
    def assemble_surface_markup(
        cls,
        document: str,
        matches: Iterable[Mapping[str, Any]],
    ) -> str:
        surface_pattern = re.compile(
            rf"<{SURFACE_TAG}\b[^>]*>.*?</{SURFACE_TAG}>",
            re.IGNORECASE | re.DOTALL,
        )
        tiles: List[str] = []
        for match in matches:
            attrs: Dict[str, Any] = {
                "surface-region": match["region"],
                "min-columns": match["minColumns"],
                "columns": match["preferredColumns"],
                "max-columns": match["maxColumns"],
                "min-rows": match["minRows"],
                "rows": match["preferredRows"],
                "max-rows": match["maxRows"],
            }
            data_id = str(match.get("data", "")).strip()
            if data_id:
                attrs["data-ontobdc-resource"] = data_id
            if match.get("closed"):
                attrs["data-tile-closed"] = "true"

            attr_text = " ".join(
                f'{name}="{html.escape(str(value), quote=True)}"'
                for name, value in attrs.items()
            )
            tile_name = str(match["tile"])
            tiles.append(f"    <{tile_name} {attr_text}></{tile_name}>")

        surface = (
            f"<{SURFACE_TAG}>\n"
            + "\n".join(tiles)
            + f"\n  </{SURFACE_TAG}>"
        )
        if surface_pattern.search(document):
            # Replace ALL occurrences (not just count=1) so stale empty
            # <surface> tags from previous state runs don't remain behind and
            # confuse downstream checks like has_assembled_tiles which look
            # for tiles inside the first or last surface tag. Also run
            # surface_pattern.sub without count so multiple stale copies are
            # collapsed into one.
            return surface_pattern.sub(surface, document)
        return cls._insert_before_closing_tag(document, "body", surface)

    @classmethod
    def embed_component_scripts(
        cls,
        document: str,
        scripts: Iterable[str],
    ) -> str:
        without_existing = re.sub(
            rf"\s*<script\b[^>]*\b{COMPONENT_SCRIPT_ATTR}"
            rf"(?:=[\"'][^\"']*[\"'])?[^>]*>.*?</script>\s*",
            "\n",
            document,
            flags=re.IGNORECASE | re.DOTALL,
        )
        blocks: List[str] = []
        for index, script in enumerate(scripts):
            if not isinstance(script, str) or not script.strip():
                continue
            safe_script = script.replace("</script>", "<\\/script>")
            blocks.append(
                f'<script type="module" {COMPONENT_SCRIPT_ATTR}="{index}">\n'
                f"{safe_script}\n</script>"
            )
        insertion = "\n  ".join(blocks)
        if not insertion:
            return without_existing
        return cls._insert_before_closing_tag(
            without_existing,
            "body",
            insertion,
        )

    @classmethod
    def embed_default_layouts_bootstrap(cls, document: str) -> str:
        """Embed the runtime script that applies DefaultSurfaceLayout data."""
        script = (
            f'<script type="module" id="{DEFAULT_LAYOUTS_BOOTSTRAP_ID}">\n'
            'customElements.whenDefined("onto-presentation-surface").then(() => {\n'
            f'  const dataScript = document.getElementById("{DEFAULT_LAYOUTS_ID}");\n'
            f'  const surface = document.querySelector("{SURFACE_TAG}");\n'
            '  if (!dataScript || !surface) return;\n'
            '  surface.defaultSurfaceLayouts = JSON.parse(dataScript.textContent);\n'
            '});\n'
            '</script>'
        )
        pattern = re.compile(
            rf"<script\b[^>]*\bid=[\"']"
            rf"{re.escape(DEFAULT_LAYOUTS_BOOTSTRAP_ID)}[\"'][^>]*>"
            rf".*?</script>",
            re.IGNORECASE | re.DOTALL,
        )
        if pattern.search(document):
            return pattern.sub(script, document, count=1)
        return cls._insert_before_closing_tag(document, "body", script)

    _URL_STATE_DEFAULTS_PLACEHOLDER = "__ONTOBDC_URL_STATE_DEFAULTS__"
    _URL_STATE_NAMES_PLACEHOLDER = "__ONTOBDC_URL_STATE_NAMES__"

    # Runtime owner of URL presentation state, embedded once per generated
    # page. Components never parse or rewrite the query string themselves:
    # they read `window.ontobdcUrlState`, so the rules below live in a single
    # place instead of being re-derived — differently — in each Tile.
    _URL_STATE_BOOTSTRAP_JS = """(() => {
  const DEFAULTS = __ONTOBDC_URL_STATE_DEFAULTS__;
  const NAMES = __ONTOBDC_URL_STATE_NAMES__;

  const current = () => new URLSearchParams(location.search);

  // A control may already have painted a presentation choice before the URL
  // is normalized. Internal links must carry what the user is actually
  // seeing, even when that value is not present in the query string yet.
  function applied(name) {
    if (name === "lang") {
      return document.documentElement.lang
        || document.documentElement.dataset.language
        || null;
    }
    if (name === "theme") {
      return document.documentElement.dataset.theme || null;
    }
    return null;
  }

  // The address bar is the source of truth; DEFAULTS only answers for a
  // parameter the URL does not carry.
  const value = (name) => current().get(name) ?? DEFAULTS[name] ?? null;

  // Stamp every missing default into the address bar, so even the very first
  // open of a generated page is an explicit, shareable, reproducible URL
  // rather than one whose rendering depends on build-time knowledge.
  function ensureDefaults() {
    const url = new URL(location.href);
    let changed = false;
    for (const [name, defaultValue] of Object.entries(DEFAULTS)) {
      if (url.searchParams.has(name)) continue;
      url.searchParams.set(name, defaultValue);
      changed = true;
    }
    if (!changed) return;
    try {
      // Same-document rewrite: no reload, no extra history entry.
      history.replaceState(history.state, "", url.href);
    } catch {
      // Some browsers refuse replaceState with a URL on an opaque-origin
      // (file://) document. A replacing navigation reaches the same
      // normalized URL; the parameters are present on that load, so the
      // branch cannot run twice and cannot loop.
      location.replace(url.href);
    }
  }

  // Carry the live presentation state onto an internal link rather than
  // letting each component re-derive it. A parameter the link already
  // declares wins: inheriting must never overwrite an explicit choice, and
  // must never stamp a build-time default over the user's selection.
  function decorate(href) {
    try {
      const target = new URL(href, location.href);
      const params = current();
      for (const name of NAMES) {
        const carried = params.get(name) ?? applied(name);
        if (carried !== null && !target.searchParams.has(name)) {
          target.searchParams.set(name, carried);
        }
      }
      return target.href;
    } catch {
      return href;
    }
  }

  // The one place a presentation parameter is *changed*. Writing it into the
  // URL and navigating means page initialization re-derives the whole
  // rendering from the address bar, so a reload, a bookmark and a shared
  // link all reproduce it — and no Tile has to know how that is done.
  function withParam(name, value) {
    const url = new URL(location.href);
    url.searchParams.set(name, value);
    return url.href;
  }

  function select(name, value) {
    if (value === null || value === undefined || value === "") return false;
    let target;
    try {
      target = withParam(name, value);
    } catch {
      return false;
    }
    // Already the active URL: navigating would only cost a reload.
    if (target === location.href) return false;
    try {
      // assign(), not replace(): the change stays undoable with Back.
      location.assign(target);
      return true;
    } catch {
      // Navigation refused (sandboxed frame, exotic scheme). The caller has
      // already applied the change in-document, so the control still works
      // for this session — it just will not survive the next reload.
      return false;
    }
  }

  // Runs before the deferred component modules upgrade any Tile, so the
  // document is already in the URL's language at first paint instead of
  // flashing the language it was generated in.
  function applyLanguage() {
    const language = value("lang");
    if (!language) return;
    document.documentElement.lang = language;
    document.documentElement.dataset.language = language;
  }

  ensureDefaults();
  applyLanguage();

  window.ontobdcUrlState = {
    defaults: { ...DEFAULTS },
    names: [...NAMES],
    current,
    value,
    withParam,
    select,
    decorate,
    applyLanguage,
  };
})();"""

    @classmethod
    def build_url_state_bootstrap(
        cls,
        defaults: Mapping[str, str],
    ) -> str:
        """Return the URL-state bootstrap script tag for ``defaults``."""
        payload = json.dumps(
            {str(name): str(value) for name, value in defaults.items()},
            ensure_ascii=False,
            separators=(",", ":"),
            sort_keys=True,
        )
        script = cls._URL_STATE_BOOTSTRAP_JS.replace(
            cls._URL_STATE_DEFAULTS_PLACEHOLDER,
            payload,
        )
        script = script.replace(
            cls._URL_STATE_NAMES_PLACEHOLDER,
            json.dumps(PRESENTATION_PARAMS, separators=(",", ":")),
        )
        safe_script = script.replace("</script>", "<\\/script>")
        return (
            f'<script id="{URL_STATE_BOOTSTRAP_ID}">\n'
            f"{safe_script}\n"
            "</script>"
        )

    @classmethod
    def embed_url_state_bootstrap(
        cls,
        document: str,
        defaults: Mapping[str, str],
    ) -> str:
        """Idempotently embed the URL-state bootstrap in ``<head>``."""
        script = cls.build_url_state_bootstrap(defaults)
        pattern = re.compile(
            rf"<script\b[^>]*\bid=[\"']"
            rf"{re.escape(URL_STATE_BOOTSTRAP_ID)}[\"'][^>]*>"
            rf".*?</script>",
            re.IGNORECASE | re.DOTALL,
        )
        if pattern.search(document):
            return pattern.sub(lambda _: script, document, count=1)
        return cls._insert_before_closing_tag(document, "head", script)

    @classmethod
    def contains_external_runtime_reference(cls, document: str) -> bool:
        patterns = [
            r"<script\b[^>]*\bsrc=[\"']\s*https?://",
            r"<link\b[^>]*\bhref=[\"']\s*https?://",
            r"@import\s+(?:url\()?\s*[\"']?https?://",
        ]
        return any(
            re.search(pattern, document, re.IGNORECASE)
            for pattern in patterns
        )

    @classmethod
    def _positive_int(cls, value: Any, fallback: int) -> int:
        try:
            parsed = int(value)
        except (TypeError, ValueError):
            return fallback
        return parsed if parsed > 0 else fallback

    @classmethod
    def _positive_number(cls, value: Any, fallback: float) -> float:
        try:
            parsed = float(value)
        except (TypeError, ValueError):
            return fallback
        return parsed if parsed > 0 else fallback

    @classmethod
    def _non_negative_number(cls, value: Any, fallback: float) -> float:
        try:
            parsed = float(value)
        except (TypeError, ValueError):
            return fallback
        return parsed if parsed >= 0 else fallback
