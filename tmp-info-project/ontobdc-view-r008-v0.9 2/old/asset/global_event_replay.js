// Global Event replay — materializes the Surface graph before any Tile reads it.
//
// The `#ontobdc-surface-jsonld` block is a build-time snapshot. Everything
// that happened to the underlying data since it was generated is persisted
// after it, as an append-only journal of Global Events:
//
//   <script id="ontobdc-surface-jsonld" data-snapshot-through="41"> … </script>
//   …component modules…
//   <script data-ontobdc-global-event="true" data-sequence="42"> … </script>
//   <script data-ontobdc-global-event="true" data-sequence="43"> … </script>
//
// This module reads both, applies the journal to the snapshot and writes the
// materialized graph back into that same block — once. Tiles keep reading
// `#ontobdc-surface-jsonld` exactly as they always did and simply find the
// current state there.
//
// Why the Surface does not just re-read the source: it cannot. The canonical
// .xlsx lives behind a `FileSystemDirectoryHandle` the Page holds in
// IndexedDB, and on `file://` the Page and the Surface are separate opaque
// origins — the Surface looks in a different database, finds nothing, and
// silently renders stale data. The journal removes that dependency entirely:
// nothing here opens a workbook, asks for a directory, or touches IndexedDB.
//
// Ordering matters and is not incidental. This is a deferred module emitted
// *before* the component modules, so it runs before `customElements.define`
// upgrades any Tile — a Tile's `connectedCallback` therefore never sees the
// pre-replay snapshot, and nothing has to be re-rendered after the fact.
// Deferred modules also run after parsing, so the journal blocks appended at
// the very end of the document are already in the DOM when this executes.
//
// It must be embedded *inline*, as `<script type="module">…</script>`, the
// same way every component script already is. A module referenced with `src=`
// is fetched, and on `file://` that fetch is a cross-origin request from an
// opaque origin: Chromium blocks it and the module never runs at all. Inline
// modules have nothing to fetch and are unaffected.

const SNAPSHOT_ID = "ontobdc-surface-jsonld";
const SNAPSHOT_THROUGH_ATTR = "data-snapshot-through";
const JOURNAL_SELECTOR = "[data-ontobdc-global-event]";
const COMPONENT_EVENT_TYPE = "ontobdc:component-event";

// The Global Event IRIs, read from the ontology at build time
// (`ontology/tool/ontobdc/abox/presentation_event.ttl`). This runtime accepts
// an event only if the graph declares it a `view:GlobalEvent` — it does not
// keep a vocabulary of its own, and a persisted event naming anything else is
// a diagnostic, not something to guess about.
const GLOBAL_EVENT_IRIS = __ONTOBDC_BUILD_GLOBAL_EVENT_IRIS__;

// Which reducer operation each declared event is allowed to carry. Also from
// the ontology: the key is the event's IRI, so adding an event to the graph
// is what makes it replayable, not editing a table here.
const OPERATIONS_BY_EVENT = __ONTOBDC_BUILD_GLOBAL_EVENT_OPERATIONS__;

const SET = "set";
const UNSET = "unset";
const ADD = "add";
const REMOVE = "remove";

// --------------------------------------------------------------------------
// Reading the document
// --------------------------------------------------------------------------

function snapshotElement() {
  return document.getElementById(SNAPSHOT_ID);
}

function readSnapshot(element) {
  const parsed = JSON.parse(element.textContent);
  // Both shapes occur: a flattened JSON-LD array, or a single node object.
  // Keep track of which one came in so the same shape is written back.
  return Array.isArray(parsed)
    ? { nodes: parsed, wasArray: true }
    : { nodes: [parsed], wasArray: false };
}

function snapshotThrough(element) {
  const raw = element.getAttribute(SNAPSHOT_THROUGH_ATTR);
  const parsed = Number.parseInt(String(raw ?? ""), 10);
  // No attribute means the snapshot incorporates nothing: replay everything.
  return Number.isFinite(parsed) ? parsed : -1;
}

function readJournal(errors) {
  const events = [];
  for (const element of document.querySelectorAll(JOURNAL_SELECTOR)) {
    const sequenceAttr = element.getAttribute("data-sequence");
    let payload;
    try {
      payload = JSON.parse(element.textContent);
    } catch (error) {
      // One unreadable block must not cost the readable ones. Journal order
      // is the sequence, not DOM order, so a hole is survivable.
      errors.push({
        reason: "unparsable",
        sequence: sequenceAttr,
        message: String(error && error.message ? error.message : error),
      });
      continue;
    }
    events.push(payload);
  }
  return events;
}

// --------------------------------------------------------------------------
// Validation
// --------------------------------------------------------------------------

function validate(event, errors) {
  const eventId = typeof event?.eventId === "string" ? event.eventId.trim() : "";
  if (!eventId) {
    errors.push({ reason: "missing-event-id", event });
    return null;
  }

  const sequence = Number.parseInt(String(event?.sequence ?? ""), 10);
  if (!Number.isFinite(sequence)) {
    errors.push({ reason: "missing-sequence", eventId });
    return null;
  }

  const type = typeof event?.event === "string" ? event.event.trim() : "";
  if (!GLOBAL_EVENT_IRIS.includes(type)) {
    errors.push({ reason: "unknown-event-type", eventId, type });
    return null;
  }

  const entity = typeof event?.entity === "string" ? event.entity.trim() : "";
  if (!entity) {
    errors.push({ reason: "missing-entity", eventId });
    return null;
  }

  const operations = Array.isArray(event?.operations) ? event.operations : [];
  if (!operations.length) {
    errors.push({ reason: "no-operations", eventId });
    return null;
  }

  const allowed = OPERATIONS_BY_EVENT[type] ?? [];
  const valid = [];
  for (const operation of operations) {
    const name = typeof operation?.operation === "string" ? operation.operation : "";
    const predicate = typeof operation?.predicate === "string" ? operation.predicate.trim() : "";
    if (!allowed.includes(name)) {
      errors.push({ reason: "operation-not-allowed", eventId, operation: name, type });
      continue;
    }
    if (!predicate) {
      errors.push({ reason: "missing-predicate", eventId, operation: name });
      continue;
    }
    valid.push({ operation: name, predicate, value: operation.value });
  }
  if (!valid.length) return null;

  return { eventId, sequence, type, entity, operations: valid };
}

// --------------------------------------------------------------------------
// The reducer
// --------------------------------------------------------------------------

function findNode(nodes, id) {
  return nodes.find((node) => node && node["@id"] === id) ?? null;
}

// A JSON-LD value object, carrying over whatever the existing value declared
// unless the event replaced it. An edit that changes a label's text must not
// silently drop that label's `@language`.
function valueObject(incoming, existing) {
  if (incoming && typeof incoming === "object" && "@id" in incoming) {
    return { "@id": incoming["@id"] };
  }
  const next = {};
  const raw =
    incoming && typeof incoming === "object" ? incoming : { "@value": incoming };
  next["@value"] = raw["@value"];
  const language = raw["@language"] ?? existing?.["@language"];
  const datatype = raw["@type"] ?? existing?.["@type"];
  if (language != null) next["@language"] = language;
  // `@language` and `@type` are mutually exclusive on a literal.
  else if (datatype != null) next["@type"] = datatype;
  return next;
}

function sameValue(a, b) {
  if (a == null || b == null) return a === b;
  if (typeof a !== "object" || typeof b !== "object") return a === b;
  if ("@id" in a || "@id" in b) return a["@id"] === b["@id"];
  return (
    a["@value"] === b["@value"] &&
    (a["@language"] ?? null) === (b["@language"] ?? null) &&
    (a["@type"] ?? null) === (b["@type"] ?? null)
  );
}

function applyOperation(node, operation) {
  const { predicate, value } = operation;
  const existing = Array.isArray(node[predicate]) ? node[predicate] : undefined;

  if (operation.operation === SET) {
    // Replaces the property. Idempotent: applying the same event twice
    // leaves the same single value.
    node[predicate] = [valueObject(value, existing?.[0])];
    return true;
  }

  if (operation.operation === UNSET) {
    if (existing === undefined) return true; // already absent — idempotent
    if (value === undefined || value === null) {
      delete node[predicate];
      return true;
    }
    const target = valueObject(value, existing[0]);
    const kept = existing.filter((entry) => !sameValue(entry, target));
    if (kept.length) node[predicate] = kept;
    else delete node[predicate];
    return true;
  }

  if (operation.operation === ADD) {
    const target = valueObject(value, existing?.[0]);
    const current = existing ?? [];
    if (current.some((entry) => sameValue(entry, target))) return true;
    node[predicate] = [...current, target];
    return true;
  }

  if (operation.operation === REMOVE) {
    if (existing === undefined) return true;
    const target = valueObject(value, existing[0]);
    const kept = existing.filter((entry) => !sameValue(entry, target));
    if (kept.length) node[predicate] = kept;
    else delete node[predicate];
    return true;
  }

  return false;
}

// --------------------------------------------------------------------------
// The replay itself
// --------------------------------------------------------------------------

function replay(nodes, events, through, errors) {
  const replayedEventIds = [];
  const seen = new Set();
  let lastSequence = through;

  // Sequence order, not document order: the writer assigns the sequence, and
  // it is the only thing that says which of two edits to the same field won.
  const ordered = [...events].sort((a, b) => a.sequence - b.sequence);

  for (const event of ordered) {
    if (event.sequence <= through) continue; // already in the snapshot
    if (seen.has(event.eventId)) continue; // a redelivered append
    seen.add(event.eventId);

    const node = findNode(nodes, event.entity);
    if (!node) {
      // The entity is not on this Surface (another dataset's event, or one
      // whose entity the last generation dropped). Report it and carry on —
      // the following events are unaffected.
      errors.push({ reason: "unknown-entity", eventId: event.eventId, entity: event.entity });
      lastSequence = Math.max(lastSequence, event.sequence);
      continue;
    }

    for (const operation of event.operations) applyOperation(node, operation);
    replayedEventIds.push(event.eventId);
    lastSequence = Math.max(lastSequence, event.sequence);
  }

  return { replayedEventIds, lastSequence };
}

function run() {
  const element = snapshotElement();
  const errors = [];
  if (!element) {
    // A Page with no Surface graph. Nothing to replay, nothing wrong.
    return { snapshotThrough: -1, replayedEventIds: [], lastSequence: -1, errors };
  }

  let snapshot;
  try {
    snapshot = readSnapshot(element);
  } catch (error) {
    errors.push({ reason: "unparsable-snapshot", message: String(error?.message ?? error) });
    console.error("[OntoBDC GlobalEvent] the Surface snapshot is not readable", error);
    return { snapshotThrough: -1, replayedEventIds: [], lastSequence: -1, errors };
  }

  const through = snapshotThrough(element);
  const events = readJournal(errors)
    .map((event) => validate(event, errors))
    .filter((event) => event !== null);

  const { replayedEventIds, lastSequence } = replay(snapshot.nodes, events, through, errors);

  if (replayedEventIds.length) {
    // One write, after the whole journal is applied — so no Tile can observe
    // a half-materialized graph, and the DOM is touched once regardless of
    // how long the journal is.
    element.textContent = JSON.stringify(
      snapshot.wasArray ? snapshot.nodes : snapshot.nodes[0],
    );
  }

  return { snapshotThrough: through, replayedEventIds, lastSequence, errors };
}

const state = run();

// Diagnostics only. Deliberately small: this is not an API for Tiles to build
// on, it is what you read in a console when a value on screen is not the value
// you just saved.
window.OntoBDCGlobalEventRuntime = state;

// Back-forward cache. Restoring the Surface from the BFCache does not re-parse
// the document, so a journal the worker appended while the user was away is
// simply not there — no `connectedCallback`, no replay, and the page shows
// pre-edit values with no indication that it is stale. A real reload is the
// only way to pick the file up again, and it is cheap: this is a local
// document, and the reload is what re-runs the replay above.
//
// This is deliberately *not* the old "go and read the workbook again" path in
// disguise. Nothing here recovers a directory handle or opens a data source;
// it re-reads this same HTML file.
window.addEventListener("pageshow", (event) => {
  if (!event.persisted) return;
  location.reload();
});

// Announced as an ordinary Component Event, so it appears wherever
// occurrences appear. The ontology gives it no `view:promotesTo`, so the dock
// promotes it to nothing: replaying persisted history never re-enters the
// promotion chain as if the user had just acted.
document.dispatchEvent(
  new CustomEvent(COMPONENT_EVENT_TYPE, {
    bubbles: true,
    composed: true,
    detail: {
      event: "GlobalEventsReplayed",
      tile: "global-event-replay",
      replayed: state.replayedEventIds.length,
      snapshotThrough: state.snapshotThrough,
      lastSequence: state.lastSequence,
    },
  }),
);

export { applyOperation, replay, validate, valueObject, state };
