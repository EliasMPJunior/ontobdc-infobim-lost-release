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

// The canonical presentation-event envelopes. This Tile announces what
// happened to it locally as a Component Event and listens for the Shared
// Events the dDock promoted; it holds no rule about which of its own
// occurrences promote to what, and it never dispatches a Shared Event.
const COMPONENT_EVENT_TYPE = "ontobdc:component-event";
const SHARED_EVENT_TYPE = "ontobdc:shared-event";

class OntoGenericFileTile extends HTMLElement {
  #root;
  #path = "";
  #sharedEventListener;
  #wasFullscreen = false;

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
          font-family: system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
        }
        *, *::before, *::after { box-sizing: border-box; }
        :host(:fullscreen) {
          inline-size: 100vw;
          block-size: 100vh;
          background: var(--onto-theme-background, #ffffff);
        }
        .tile {
          display: grid;
          grid-template-rows: minmax(0, 1fr) var(--onto-surface-slot-size, 72px);
          row-gap: 6px;
          inline-size: 100%;
          block-size: 100%;
          min-inline-size: 0;
          min-block-size: 0;
          overflow: hidden;
          padding: clamp(8px, 2.4cqw, 14px);
          border-radius: var(--onto-theme-tile-border-radius, 16px);
          border: var(--onto-theme-tile-border-width, 1px) solid
            color-mix(in srgb, var(--onto-theme-foreground, #0f172a) 22%, transparent);
          background: color-mix(in srgb, var(--onto-theme-foreground, #0f172a) 5%, var(--onto-theme-background, #ffffff));
          color: var(--onto-theme-foreground, #0f172a);
          cursor: pointer;
        }
        :host(:fullscreen) .tile {
          border-radius: 0;
        }
        .glyph {
          display: grid;
          place-items: center;
          min-inline-size: 0;
          min-block-size: 0;
          border-radius: 10px;
          background: color-mix(in srgb, var(--onto-theme-foreground, #0f172a) 8%, transparent);
          font-size: clamp(20px, 12cqh, 56px);
          font-weight: 800;
          letter-spacing: .04em;
          color: color-mix(in srgb, var(--onto-theme-foreground, #0f172a) 55%, transparent);
        }
        .caption {
          display: flex;
          align-items: center;
          justify-content: space-between;
          gap: 8px;
          min-inline-size: 0;
        }
        .info {
          min-inline-size: 0;
        }
        .name {
          font-size: clamp(11px, 2.6cqw, 13px);
          font-weight: 700;
          overflow: hidden;
          text-overflow: ellipsis;
          white-space: nowrap;
        }
        .meta {
          font-size: clamp(9px, 2.2cqw, 11px);
          color: color-mix(in srgb, var(--onto-theme-foreground, #0f172a) 60%, transparent);
        }
        .actions {
          display: flex;
          align-items: center;
          gap: 4px;
          flex: none;
        }
        .icon-btn {
          display: inline-flex;
          align-items: center;
          justify-content: center;
          inline-size: 24px;
          block-size: 24px;
          padding: 0;
          border: 0;
          border-radius: 6px;
          background: transparent;
          color: var(--onto-theme-accent, #0ea5e9);
          cursor: pointer;
        }
        .icon-btn:hover {
          background: color-mix(in srgb, var(--onto-theme-foreground, #0f172a) 10%, transparent);
        }
        .icon-btn.close-btn {
          color: color-mix(in srgb, var(--onto-theme-foreground, #0f172a) 55%, transparent);
        }
        .icon-btn svg {
          inline-size: 14px;
          block-size: 14px;
        }
        .empty {
          font-size: clamp(11px, 2.6cqw, 13px);
          opacity: .6;
        }
      </style>
      <div class="tile">
        <div class="glyph"></div>
        <div class="caption">
          <div class="info">
            <div class="name"></div>
            <div class="meta"></div>
          </div>
          <div class="actions">
            <a class="icon-btn open-link" target="_blank" rel="noopener">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6"/><polyline points="15 3 21 3 21 9"/><line x1="10" y1="14" x2="21" y2="3"/></svg>
            </a>
            <button type="button" class="icon-btn close-btn">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg>
            </button>
          </div>
        </div>
      </div>
    `;

    this.#root.querySelector(".tile").addEventListener("dblclick", () => this.#activate());
    this.#root.querySelector(".open-link").addEventListener("click", (event) => event.stopPropagation());
    this.#root.querySelector(".close-btn").addEventListener("click", (event) => {
      event.stopPropagation();
      this.#close();
    });
    this.#applyStaticLabels();
  }

  #applyStaticLabels() {
    const openLink = this.#root.querySelector(".open-link");
    const closeBtn = this.#root.querySelector(".close-btn");
    if (openLink) {
      openLink.title = t("open");
      openLink.setAttribute("aria-label", t("openFile"));
    }
    if (closeBtn) {
      closeBtn.title = t("close");
      closeBtn.setAttribute("aria-label", t("closeTile"));
    }
  }

  #onLanguageChanged = () => {
    this.#applyStaticLabels();
    this.#render();
  };

  connectedCallback() {
    this.#render();
    this.#sharedEventListener = (event) => this.#handleSharedEvent(event);
    this.closest("onto-presentation-surface")?.addEventListener(SHARED_EVENT_TYPE, this.#sharedEventListener);
    document.addEventListener("fullscreenchange", this.#onFullscreenChange);
    document.addEventListener("language-changed", this.#onLanguageChanged);
  }

  disconnectedCallback() {
    this.closest("onto-presentation-surface")?.removeEventListener(SHARED_EVENT_TYPE, this.#sharedEventListener);
    document.removeEventListener("fullscreenchange", this.#onFullscreenChange);
    document.removeEventListener("language-changed", this.#onLanguageChanged);
  }

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

  #literal(entity, property) {
    const values = entity?.[property];
    if (!Array.isArray(values) || values.length === 0) return "";
    return String(values[0]?.["@value"] ?? values[0]?.["@id"] ?? "").trim();
  }

  #formatBytes(bytesText) {
    const bytes = Number.parseInt(bytesText, 10);
    if (!Number.isFinite(bytes)) return "";
    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
    return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
  }

  // Double-clicking this Tile directly opens fullscreen, without repositioning it.
  #activate() {
    this.#toggleFullscreen(true);
  }

  // Reacts to the `EntityPageRequested` Shared Event the dDock promoted
  // from another component's `EntityPageOpenRequested`. The requester never
  // reaches in here: opening this Tile is this Tile's own responsibility.
  #handleSharedEvent(event) {
    if (event.detail?.event !== "EntityPageRequested") return;
    if (!this.#path || event.detail?.path !== this.#path) return;
    delete this.dataset.tileClosed;
    this.closest("onto-presentation-surface")?.sendToEnd(this);
    requestAnimationFrame(() => this.scrollIntoView({ behavior: "smooth", block: "end" }));
    this.#emitComponentEvent("TileOpened", { path: this.#path });
  }

  // Native Fullscreen API — immune to container-type/position:fixed containment quirks, and Escape closes it for free.
  #toggleFullscreen(force) {
    const shouldOpen = typeof force === "boolean" ? force : document.fullscreenElement !== this;
    if (shouldOpen) {
      this.requestFullscreen?.().catch(() => {});
    } else if (document.fullscreenElement === this) {
      document.exitFullscreen?.();
    }
  }

  // Hides this Tile again (not a removal) — double-clicking the file in
  // onto-file-tree-tile reveals it again later.
  #close() {
    this.#toggleFullscreen(false);
    this.closest("onto-presentation-surface")?.close(this);
    this.#emitComponentEvent("TileClosed", { path: this.#path });
  }

  // Local occurrence -> Component Event, bubbled and composed so it
  // reaches the dDock bridge listening on the document. Whether it
  // promotes, and into what, is decided by the Python Listener against
  // `view:promotesTo` — not here.
  #emitComponentEvent(name, detail) {
    this.dispatchEvent(
      new CustomEvent(COMPONENT_EVENT_TYPE, {
        bubbles: true,
        composed: true,
        detail: {
          event: name,
          tile: this.localName,
          resource: this.getAttribute("data-ontobdc-resource") || "",
          ...detail,
        },
      }),
    );
  }

  // Fullscreen is entered and left by the browser, not by the click: the
  // user can leave it with Escape, the system UI or a browser gesture. The
  // occurrence must describe the state actually reached, so it is reported
  // from `fullscreenchange` rather than from the button handler.
  #onFullscreenChange = () => {
    const isFullscreen = document.fullscreenElement === this;
    if (isFullscreen === this.#wasFullscreen) return;
    this.#wasFullscreen = isFullscreen;
    this.#emitComponentEvent(isFullscreen ? "TileFullSized" : "TileRestored", { path: this.#path });
  };

  #render() {
    const entity = this.#entity();
    this.#path = entity ? this.#literal(entity, "http://ontobdc.org/ontology/domain/ontobdc/ns.ttl#filePath") : "";
    const title = (entity ? this.#literal(entity, "http://purl.org/dc/terms/title") : "") || this.#path;
    const format = entity ? this.#literal(entity, "http://purl.org/dc/terms/format") : "";
    const size = entity ? this.#literal(entity, "http://ontobdc.org/ontology/domain/ontobdc/ns.ttl#fileSize") : "";

    if (!this.#path) {
      this.#root.querySelector(".tile").replaceWith(
        Object.assign(document.createElement("div"), { className: "empty", textContent: t("noFile") }),
      );
      return;
    }

    const href = encodeURI(this.#path);
    this.#root.querySelector(".glyph").textContent = format ? `.${format}` : t("fileBadge");
    this.#root.querySelector(".name").textContent = title;
    this.#root.querySelector(".name").title = title;
    this.#root.querySelector(".meta").textContent = this.#formatBytes(size);
    this.#root.querySelector(".open-link").href = href;
  }
}

if (!customElements.get("onto-generic-file-tile")) {
  customElements.define("onto-generic-file-tile", OntoGenericFileTile);
}

export { OntoGenericFileTile };
