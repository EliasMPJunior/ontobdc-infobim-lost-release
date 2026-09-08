const PHOTO = __ONTOBDC_BUILD_PHOTO__;
const I18N = __ONTOBDC_BUILD_I18N__;

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

  static get observedAttributes() {
    return ["columns", "rows"];
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
        <div class="media"><img></div>
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

  get photo() {
    return { ...PHOTO };
  }

  #render() {
    const columns = Math.max(1, Number.parseInt(this.getAttribute("columns") || "1", 10));
    const rows = Math.max(1, Number.parseInt(this.getAttribute("rows") || "1", 10));
    const area = columns * rows;
    const mode = PHOTO.mode || "photo";
    const requestedFit = PHOTO.fit || "cover";
    const fit = mode === "evidence" ? "contain" : requestedFit;
    const x = Math.max(0, Math.min(1, Number(PHOTO.focal_x ?? 0.5))) * 100;
    const y = Math.max(0, Math.min(1, Number(PHOTO.focal_y ?? 0.5))) * 100;

    const tile = this.#root.querySelector(".tile");
    const image = this.#root.querySelector("img");
    const caption = this.#root.querySelector(".caption");

    image.src = PHOTO.data_uri;
    image.alt = PHOTO.alt || "";
    image.style.setProperty("--photo-fit", fit);
    image.style.setProperty("--photo-position", `${x}% ${y}%`);
    caption.textContent = PHOTO.caption || PHOTO.alt || "";

    this.#root.querySelector('[data-meta="date"]').textContent = PHOTO.date || "";
    this.#root.querySelector('[data-meta="location"]').textContent = PHOTO.location || "";
    this.#root.querySelector('[data-meta="author"]').textContent = PHOTO.author || "";

    tile.dataset.mode = mode;
    tile.dataset.level = area === 1 ? "image" : area < 4 ? "caption" : "detail";
    tile.dataset.layout = area === 1 ? "image" : (columns > rows && area >= 4 ? "horizontal" : "vertical");
    tile.setAttribute("aria-label", PHOTO.caption || PHOTO.alt || t("fallbackCaption"));
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
        photoId: PHOTO.id,
        caption: PHOTO.caption,
        mode: PHOTO.mode,
        focalPoint: { x: PHOTO.focal_x, y: PHOTO.focal_y }
      }
    }));
  }
}

if (!customElements.get("onto-photo-tile")) {
  customElements.define("onto-photo-tile", OntoPhotoTile);
}

export { OntoPhotoTile };
