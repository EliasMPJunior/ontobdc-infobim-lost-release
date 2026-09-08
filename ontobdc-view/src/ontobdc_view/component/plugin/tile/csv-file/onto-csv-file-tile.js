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

class OntoCsvFileTile extends HTMLElement {
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
            color-mix(in srgb, var(--onto-theme-accent, #0ea5e9) 45%, transparent);
          background: color-mix(in srgb, var(--onto-theme-foreground, #0f172a) 5%, var(--onto-theme-background, #ffffff));
          color: var(--onto-theme-foreground, #0f172a);
          cursor: pointer;
        }
        :host(:fullscreen) .tile {
          border-radius: 0;
        }
        .scroll {
          min-inline-size: 0;
          min-block-size: 0;
          overflow: auto;
          border-radius: 8px;
        }
        table {
          border-collapse: collapse;
          font-size: clamp(10px, 2.4cqw, 12px);
          inline-size: 100%;
        }
        th, td {
          padding: 3px 8px;
          text-align: start;
          white-space: nowrap;
          border-bottom: 1px solid color-mix(in srgb, var(--onto-theme-foreground, #0f172a) 12%, transparent);
        }
        th {
          position: sticky;
          inset-block-start: 0;
          font-weight: 700;
          background: color-mix(in srgb, var(--onto-theme-foreground, #0f172a) 10%, var(--onto-theme-background, #ffffff));
        }
        .fallback {
          display: grid;
          place-items: center;
          gap: 6px;
          inline-size: 100%;
          block-size: 100%;
          font-size: clamp(10px, 2.6cqw, 12px);
          opacity: .7;
          text-align: center;
        }
        .fallback a {
          color: var(--onto-theme-accent, #0ea5e9);
          font-weight: 600;
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
          display: flex;
          align-items: baseline;
          gap: .5em;
        }
        .label {
          flex: none;
          font-size: clamp(9px, 2.2cqw, 11px);
          font-weight: 700;
          letter-spacing: .12em;
          text-transform: uppercase;
          color: color-mix(in srgb, var(--onto-theme-foreground, #0f172a) 60%, transparent);
        }
        .name {
          font-size: clamp(11px, 2.6cqw, 13px);
          font-weight: 700;
          overflow: hidden;
          text-overflow: ellipsis;
          white-space: nowrap;
        }
        .count {
          flex: none;
          font-size: clamp(9px, 2.2cqw, 11px);
          opacity: .6;
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
    `;
    this.#root.appendChild(this.#buildTileElement());
    this.#applyStaticLabels();
  }

  // The .tile markup as its own template, separate from the shadow root's
  // static <style> block: #render() replaces the whole .tile subtree with
  // a plain .empty message when there is no file, so it must be able to
  // rebuild .tile from scratch (with its listeners re-wired) the moment
  // data shows up again -- not assume .tile is still there once it never
  // was, or was previously torn down.
  static #TILE_MARKUP = `
    <div class="tile">
      <div class="scroll"></div>
      <div class="caption">
        <div class="info">
          <span class="label">CSV</span>
          <span class="name"></span>
        </div>
        <span class="count"></span>
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

  #buildTileElement() {
    const template = document.createElement("template");
    template.innerHTML = OntoCsvFileTile.#TILE_MARKUP;
    const tileElement = template.content.firstElementChild;
    tileElement.addEventListener("dblclick", () => this.#activate());
    tileElement.querySelector(".open-link").addEventListener("click", (event) => event.stopPropagation());
    tileElement.querySelector(".close-btn").addEventListener("click", (event) => {
      event.stopPropagation();
      this.#close();
    });
    return tileElement;
  }

  // Restores .tile after a previous #render() replaced it with .empty --
  // a no-op (returns the existing element) when .tile is already there.
  #ensureTileElement() {
    const existingTile = this.#root.querySelector(".tile");
    if (existingTile) return existingTile;

    const tileElement = this.#buildTileElement();
    const emptyElement = this.#root.querySelector(".empty");
    if (emptyElement) emptyElement.replaceWith(tileElement);
    else this.#root.appendChild(tileElement);
    return tileElement;
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
    document.removeEventListener("language-changed", this.#onLanguageChanged);
    document.removeEventListener("fullscreenchange", this.#onFullscreenChange);
    this.closest("onto-presentation-surface")?.removeEventListener(SHARED_EVENT_TYPE, this.#sharedEventListener);
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

  // Minimal RFC4180-ish parser: handles quoted fields, escaped "" and commas inside quotes.
  #parseCsv(text) {
    const rows = [];
    let row = [];
    let field = "";
    let inQuotes = false;

    for (let index = 0; index < text.length; index += 1) {
      const char = text[index];
      if (inQuotes) {
        if (char === '"' && text[index + 1] === '"') {
          field += '"';
          index += 1;
        } else if (char === '"') {
          inQuotes = false;
        } else {
          field += char;
        }
        continue;
      }

      if (char === '"') {
        inQuotes = true;
      } else if (char === ",") {
        row.push(field);
        field = "";
      } else if (char === "\n" || char === "\r") {
        if (char === "\r" && text[index + 1] === "\n") index += 1;
        row.push(field);
        field = "";
        rows.push(row);
        row = [];
      } else {
        field += char;
      }
    }
    if (field.length || row.length) {
      row.push(field);
      rows.push(row);
    }
    return rows.filter((cells) => cells.some((cell) => cell.trim() !== ""));
  }

  #renderTable(rows) {
    const [header, ...body] = rows;
    const table = document.createElement("table");
    const thead = document.createElement("thead");
    const headRow = document.createElement("tr");
    for (const cell of header) {
      const th = document.createElement("th");
      th.textContent = cell;
      headRow.appendChild(th);
    }
    thead.appendChild(headRow);
    table.appendChild(thead);

    const tbody = document.createElement("tbody");
    for (const cells of body) {
      const tr = document.createElement("tr");
      for (const cell of cells) {
        const td = document.createElement("td");
        td.textContent = cell;
        tr.appendChild(td);
      }
      tbody.appendChild(tr);
    }
    table.appendChild(tbody);
    return table;
  }

  #renderFallback(scroll, href) {
    const fallback = document.createElement("div");
    fallback.className = "fallback";
    fallback.innerHTML = `<span></span>`;
    fallback.querySelector("span").textContent = t("previewUnavailable");
    const link = document.createElement("a");
    link.href = href;
    link.target = "_blank";
    link.rel = "noopener";
    link.textContent = t("openFile");
    link.addEventListener("click", (event) => event.stopPropagation());
    fallback.appendChild(link);
    scroll.replaceChildren(fallback);
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
    this.#render();
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

  async #render() {
    const entity = this.#entity();
    this.#path = entity ? this.#literal(entity, "http://ontobdc.org/ontology/domain/ontobdc/ns.ttl#filePath") : "";
    const title = (entity ? this.#literal(entity, "http://purl.org/dc/terms/title") : "") || this.#path;

    if (!this.#path) {
      const existingTile = this.#root.querySelector(".tile");
      if (existingTile) {
        existingTile.replaceWith(
          Object.assign(document.createElement("div"), { className: "empty", textContent: t("noFile") }),
        );
      } else {
        const emptyElement = this.#root.querySelector(".empty");
        if (emptyElement) emptyElement.textContent = t("noFile");
      }
      return;
    }

    const tileElement = this.#ensureTileElement();
    const href = encodeURI(this.#path);
    tileElement.querySelector(".name").textContent = title;
    tileElement.querySelector(".name").title = title;
    tileElement.querySelector(".open-link").href = href;
    const scroll = tileElement.querySelector(".scroll");
    const count = tileElement.querySelector(".count");

    // `data-tile-closed` only hides a default-closed Tile visually — it
    // stays connected, so fetching unconditionally here would eagerly read
    // every CSV file's full content on initial page load regardless of
    // visibility (e.g. forcing OneDrive Files On-Demand to hydrate every
    // file up front). Deferred until `#handleShowDetailsRequested` clears
    // the flag and re-renders.
    if (this.dataset.tileClosed === "true") {
      return;
    }

    try {
      const response = await fetch(href);
      if (!response.ok) throw new Error(`HTTP ${response.status}`);
      const text = await response.text();
      const rows = this.#parseCsv(text);
      if (!rows.length) throw new Error("empty CSV");
      scroll.replaceChildren(this.#renderTable(rows));
      count.textContent = t("rows", { count: Math.max(0, rows.length - 1) });
    } catch {
      this.#renderFallback(scroll, href);
    }
  }
}

if (!customElements.get("onto-csv-file-tile")) {
  customElements.define("onto-csv-file-tile", OntoCsvFileTile);
}

export { OntoCsvFileTile };
