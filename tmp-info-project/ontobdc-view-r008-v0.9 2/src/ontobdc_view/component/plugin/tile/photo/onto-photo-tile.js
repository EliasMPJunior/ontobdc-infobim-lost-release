const I18N = __ONTOBDC_BUILD_I18N__;

// This Tile's own namespace for properties no shared ontology term already
// covers -- everything else below reuses dcterms/prov, same as every
// other Tile that reads a JSON-LD entity (see e.g. onto-data-container-tile,
// onto-workstream-tile).
const ONTOBDC_NS = "http://ontobdc.org/ontology/domain/ontobdc/ns.ttl#";
const FILE_PATH_PROPERTY = `${ONTOBDC_NS}filePath`;
const ALT_TEXT_PROPERTY = `${ONTOBDC_NS}altText`;
const PHOTO_MODE_PROPERTY = `${ONTOBDC_NS}photoMode`;
const PHOTO_FIT_PROPERTY = `${ONTOBDC_NS}photoFit`;
const FOCAL_X_PROPERTY = `${ONTOBDC_NS}focalX`;
const FOCAL_Y_PROPERTY = `${ONTOBDC_NS}focalY`;
const TITLE_PROPERTY = "http://purl.org/dc/terms/title";
const CREATOR_PROPERTY = "http://purl.org/dc/terms/creator";
const DATE_PROPERTY = "http://purl.org/dc/terms/date";
const LOCATION_PROPERTY = "http://www.w3.org/ns/prov#atLocation";

function t(key, vars) {
  const locale = document.documentElement.lang || document.documentElement.dataset.language || "en";
  const table = I18N[locale] || I18N.en || {};
  let text = table[key] ?? key;
  if (vars) {
    for (const [name, value] of Object.entries(vars)) text = text.replaceAll(`{${name}}`, value);
  }
  return text;
}

// The canonical Component Event envelope. This Tile reports what happened
// to it locally; it dispatches no Shared Event and holds no promotion rule.
const COMPONENT_EVENT_TYPE = "ontobdc:component-event";

class OntoPhotoTile extends HTMLElement {
  #root;
  #lastCaption = "";
  #lastMode = "photo";
  #lastFocalPoint = { x: 0.5, y: 0.5 };

  static get observedAttributes() {
    return ["columns", "rows", "data-ontobdc-resource"];
  }

  constructor() {
    super();
    this.#root = this.attachShadow({ mode: "closed" });
    this.#root.innerHTML = `
      <style>
        :host {
          all: initial;
          display: block;
          inline-size: 100%;
          block-size: 100%;
          min-inline-size: 0;
          min-block-size: 0;
          box-sizing: border-box;
          container-type: size;
          color: var(--onto-theme-foreground, #0f172a);
          font-family: system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
        }
        *, *::before, *::after { box-sizing: border-box; }
        .tile {
          inline-size: 100%;
          block-size: 100%;
          min-inline-size: 0;
          min-block-size: 0;
          overflow: hidden;
          display: grid;
          border-radius: var(--onto-photo-radius, 16px);
          background: color-mix(in srgb, var(--onto-theme-foreground, #0f172a) 6%, transparent);
          cursor: pointer;
        }
        .media {
          position: relative;
          min-inline-size: 0;
          min-block-size: 0;
          overflow: hidden;
          background: #111827;
        }
        img {
          display: block;
          inline-size: 100%;
          block-size: 100%;
          object-fit: var(--photo-fit, cover);
          object-position: var(--photo-position, 50% 50%);
          user-select: none;
          -webkit-user-drag: none;
        }
        .empty-message {
          display: none;
          position: absolute;
          inset: 0;
          place-items: center;
          font-size: clamp(11px, 2.6cqw, 13px);
          opacity: .6;
          color: color-mix(in srgb, var(--onto-theme-foreground, #0f172a) 90%, transparent);
          background: color-mix(in srgb, var(--onto-theme-foreground, #0f172a) 6%, var(--onto-theme-background, #ffffff));
        }
        .tile[data-empty="true"] .empty-message {
          display: grid;
        }
        .tile[data-empty="true"] img {
          visibility: hidden;
        }
        .info {
          min-inline-size: 0;
          padding: clamp(8px, 4cqw, 16px);
          display: none;
          gap: 5px;
          align-content: center;
          background: color-mix(in srgb, var(--onto-theme-background, transparent) 88%, transparent);
          color: var(--onto-theme-foreground, inherit);
        }
        .caption {
          font-size: clamp(12px, 5cqw, 18px);
          line-height: 1.18;
          font-weight: 700;
        }
        .meta {
          display: none;
          gap: 3px;
          font-size: clamp(10px, 3.2cqw, 13px);
          line-height: 1.2;
          opacity: .68;
        }
        .tile[data-level="caption"] {
          grid-template-rows: minmax(0, 1fr) auto;
        }
        .tile[data-level="caption"] .info { display: grid; }
        .tile[data-level="detail"] .info { display: grid; }
        .tile[data-level="detail"] .meta { display: grid; }
        .tile[data-layout="vertical"] {
          grid-template-rows: minmax(0, 1fr) auto;
        }
        .tile[data-layout="horizontal"] {
          grid-template-columns: minmax(0, 1.6fr) minmax(120px, .9fr);
        }
        .tile[data-layout="image"] {
          grid-template: 1fr / 1fr;
        }
        :host([mode="avatar"]) .tile,
        .tile[data-mode="avatar"] {
          border-radius: 999px;
        }
      </style>
      <article class="tile" tabindex="0" role="button">
        <div class="media">
          <img>
          <div class="empty-message"></div>
        </div>
        <div class="info">
          <div class="caption"></div>
          <div class="meta">
            <span data-meta="date"></span>
            <span data-meta="location"></span>
            <span data-meta="author"></span>
          </div>
        </div>
      </article>
    `;

    const tile = this.#root.querySelector(".tile");
    // The ad-hoc `photo-selected` / `photo-open-requested` names these
    // interactions used to be announced under were a second, Tile-private
    // event vocabulary travelling the same bubbles/composed path as the
    // semantic one. They are the same two occurrences every other Tile
    // reports — a selection, and a request for the entity's page — so they
    // are announced under the presentation vocabulary instead.
    tile.addEventListener("click", () => this.#emitComponentEvent("EntitySelected"));
    tile.addEventListener("dblclick", () => this.#emitComponentEvent("EntityPageOpenRequested"));
    tile.addEventListener("keydown", (event) => {
      if (event.key === "Enter" || event.key === " ") {
        event.preventDefault();
        this.#emitComponentEvent("EntitySelected");
      }
    });
  }

  connectedCallback() {
    this.#render();
    document.addEventListener("language-changed", this.#onLanguageChanged);
  }

  disconnectedCallback() {
    document.removeEventListener("language-changed", this.#onLanguageChanged);
  }

  #onLanguageChanged = () => this.#render();

  attributeChangedCallback() {
    if (this.isConnected) this.#render();
  }

  #entity() {
    const resourceId = this.getAttribute("data-ontobdc-resource");
    if (!resourceId) return null;

    const script = document.getElementById("ontobdc-surface-jsonld");
    if (!script) return null;

    let graph;
    try {
      graph = JSON.parse(script.textContent);
    } catch {
      return null;
    }

    const nodes = Array.isArray(graph) ? graph : [graph];
    return nodes.find((node) => node && node["@id"] === resourceId) || null;
  }

  #literal(entity, property, lang) {
    const values = entity?.[property];
    if (!Array.isArray(values) || values.length === 0) return "";

    const localized = lang ? values.find((value) => value["@language"] === lang) : null;
    const picked = localized || values[0];
    return String(picked["@value"] ?? picked["@id"] ?? "").trim();
  }

  #render() {
    const columns = Math.max(1, Number.parseInt(this.getAttribute("columns") || "1", 10));
    const rows = Math.max(1, Number.parseInt(this.getAttribute("rows") || "1", 10));
    const area = columns * rows;
    const lang = (document.documentElement.lang || "en").toLowerCase();
    const entity = this.#entity();

    const dataUri = entity ? this.#literal(entity, FILE_PATH_PROPERTY) : "";
    const alt = entity ? this.#literal(entity, ALT_TEXT_PROPERTY) : "";
    const caption = entity
      ? this.#literal(entity, TITLE_PROPERTY, lang) || this.#literal(entity, TITLE_PROPERTY)
      : "";
    const author = entity ? this.#literal(entity, CREATOR_PROPERTY) : "";
    const date = entity ? this.#literal(entity, DATE_PROPERTY) : "";
    const location = entity ? this.#literal(entity, LOCATION_PROPERTY) : "";
    const mode = (entity ? this.#literal(entity, PHOTO_MODE_PROPERTY) : "") || "photo";
    const requestedFit = (entity ? this.#literal(entity, PHOTO_FIT_PROPERTY) : "") || "cover";
    const fit = mode === "evidence" ? "contain" : requestedFit;
    const focalXRaw = entity ? this.#literal(entity, FOCAL_X_PROPERTY) : "";
    const focalYRaw = entity ? this.#literal(entity, FOCAL_Y_PROPERTY) : "";
    const focalX = focalXRaw ? Number(focalXRaw) : 0.5;
    const focalY = focalYRaw ? Number(focalYRaw) : 0.5;
    const x = Math.max(0, Math.min(1, Number.isFinite(focalX) ? focalX : 0.5)) * 100;
    const y = Math.max(0, Math.min(1, Number.isFinite(focalY) ? focalY : 0.5)) * 100;

    const tile = this.#root.querySelector(".tile");
    const image = this.#root.querySelector("img");
    const captionEl = this.#root.querySelector(".caption");

    const hasPhoto = Boolean(dataUri);
    tile.dataset.empty = hasPhoto ? "false" : "true";
    this.#root.querySelector(".empty-message").textContent = t("noPhoto");

    image.src = dataUri;
    image.alt = alt;
    image.style.setProperty("--photo-fit", fit);
    image.style.setProperty("--photo-position", `${x}% ${y}%`);
    captionEl.textContent = caption || alt || "";

    this.#root.querySelector('[data-meta="date"]').textContent = date;
    this.#root.querySelector('[data-meta="location"]').textContent = location;
    this.#root.querySelector('[data-meta="author"]').textContent = author;

    tile.dataset.mode = mode;
    tile.dataset.level = area === 1 ? "image" : area < 4 ? "caption" : "detail";
    tile.dataset.layout = area === 1 ? "image" : (columns > rows && area >= 4 ? "horizontal" : "vertical");
    tile.setAttribute("aria-label", caption || alt || t("fallbackCaption"));

    // Cached for #emitComponentEvent, which fires from click/dblclick/
    // keydown listeners outside of #render()'s own call stack.
    this.#lastCaption = caption;
    this.#lastMode = mode;
    this.#lastFocalPoint = { x: focalX, y: focalY };
  }

  // Local occurrence -> Component Event, bubbled and composed so it
  // reaches the dDock bridge listening on the document. Whether it
  // promotes, and into what, is decided by the Python Listener against
  // `view:promotesTo` — not here.
  #emitComponentEvent(name) {
    this.dispatchEvent(new CustomEvent(COMPONENT_EVENT_TYPE, {
      bubbles: true,
      composed: true,
      detail: {
        event: name,
        tile: this.localName,
        resource: this.getAttribute("data-ontobdc-resource") || "",
        caption: this.#lastCaption,
        mode: this.#lastMode,
        focalPoint: this.#lastFocalPoint,
      }
    }));
  }
}

if (!customElements.get("onto-photo-tile")) {
  customElements.define("onto-photo-tile", OntoPhotoTile);
}

export { OntoPhotoTile };
