// Standalone Page event display and opening occurrence producer.
//
// The dDock promoter owns Component -> Shared promotion. This adapter only
// gives a standalone Page the same visible promotion sink a Surface already
// has and emits the Page's own local loaded occurrence once the promoter has
// attached its document listener.
(() => {
  const COMPONENT_EVENT_TYPE = "ontobdc:component-event";
  const SHARED_EVENT_TYPE = "ontobdc:shared-event";
  const PROMOTER_READY_TYPE = "ontobdc:component-event-promoter-ready";
  const SURFACE_REFRESH_PARAM = "_ontobdc_refresh";
  const EVENT_BAR_VISIBLE_MS = 2600;

  class PageEventDisplay {
    #eventBar;
    #eventBarTimer = null;
    #loadedEmitted = false;

    constructor(eventBar) {
      this.#eventBar = eventBar;
    }

    announcePromotion({ sharedEvent, componentEvent, detail } = {}) {
      const name = String(sharedEvent || "").trim();
      if (!name) return false;
      const origin = String(componentEvent || "").trim();
      const hint =
        detail && typeof detail === "object"
          ? detail.path ?? detail.page ?? detail.entity ?? ""
          : "";
      const promotion = origin ? `${origin} → ${name}` : name;
      this.#write(hint ? `${promotion} · ${hint}` : promotion);
      return true;
    }

    announcePromotionFailure(error) {
      const reason = String(error?.message ?? error ?? "").trim();
      this.#write(
        reason
          ? `Promotion runtime unavailable · ${reason}`
          : "Promotion runtime unavailable",
      );
    }

    emitLoaded() {
      if (this.#loadedEmitted) return;
      this.#loadedEmitted = true;
      const page = document.querySelector("main.onto-page");
      document.dispatchEvent(
        new CustomEvent(COMPONENT_EVENT_TYPE, {
          bubbles: true,
          composed: true,
          detail: {
            event: "EntityPageLoaded",
            page: document.title,
            entity: page?.dataset.ontobdcResource ?? "",
            path: location.pathname,
          },
        }),
      );
    }

    #write(text) {
      this.#eventBar.textContent = text;
      this.#eventBar.dataset.visible = "true";
      clearTimeout(this.#eventBarTimer);
      this.#eventBarTimer = setTimeout(() => {
        this.#eventBar.dataset.visible = "false";
      }, EVENT_BAR_VISIBLE_MS);
    }
  }

  function armSurfaceRefresh(event) {
    const detail = event.detail || {};
    if (detail.event !== "PageLoaded" || detail.promotedFrom !== "EntityPageLoaded") return;

    const backLink = document.querySelector(".back-link");
    if (!backLink) return;

    try {
      const target = new URL(backLink.href || backLink.getAttribute("href"), location.href);
      target.searchParams.set(SURFACE_REFRESH_PARAM, String(Date.now()));
      backLink.href = target.href;
    } catch {
      // A malformed back-link must not interfere with normal page behavior.
    }
  }

  const eventBar = document.querySelector("[data-ontobdc-page-event-bar]");
  if (!eventBar) return;

  const display = new PageEventDisplay(eventBar);
  window.OntoBDCPageEventDisplay = display;
  document.addEventListener(SHARED_EVENT_TYPE, armSurfaceRefresh);
  document.addEventListener(
    PROMOTER_READY_TYPE,
    () => display.emitLoaded(),
    { once: true },
  );
  if (window.OntoBDCComponentEventPromoter) {
    queueMicrotask(() => display.emitLoaded());
  }
})();
