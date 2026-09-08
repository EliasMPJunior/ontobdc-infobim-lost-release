"""The Global Event journal: appending, sequencing and compacting.

A generated Surface carries a build-time JSON-LD snapshot. Every change to
the underlying data made after that generation is persisted as one more
`<script>` block appended to the end of the same document, and the browser
replays those blocks over the snapshot before any Tile reads it.

Three properties shape this module, and each one is the reason for code
that would otherwise look excessive:

**An append never deserializes the snapshot.** The snapshot is the whole
container's graph and can be large; an edit to one spreadsheet cell must not
cost a parse and a re-serialization of it. So a normal append opens the file
in binary append mode and writes one block. The bytes already in the file are
never read, never rewritten, and are byte-for-byte identical afterwards.

**The document has to stay parseable while staying appendable.** HTML's
`</body>` and `</html>` end tags are optional; omitting them is what lets
content be appended at the end of the file and still be parsed as children
of `<body>`. Appending *after* `</html>` also happens to work in browsers,
but only through error recovery, so the generator omits the end tags
instead — `prepare_document_for_journal` does that, and
`document_accepts_journal` is what the tests assert against.

**A value in the journal is user data.** The HTML parser closes a
`<script>` at the first `</script>` in its text, whatever the `type`. A
spreadsheet cell containing `</script>` would end the block and let the rest
of the cell parse as markup. Every `<` is therefore escaped as `\\u003c`,
which JSON reads back as the same character.
"""

from __future__ import annotations

import json
import os
import re
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from ontobdc.shared.adapter.atomic_file import AtomicFileWriter

JOURNAL_ATTR = "data-ontobdc-global-event"
SNAPSHOT_THROUGH_ATTR = "data-snapshot-through"
JSONLD_ID = "ontobdc-surface-jsonld"

# Written by hand rather than composed, because the recovery scan below has to
# recognize exactly this shape at the end of a possibly truncated file.
_BLOCK_OPEN = '<script type="application/ld+json" ' + JOURNAL_ATTR + '="true"'
_BLOCK_CLOSE = "</script>"

# Where the journal starts. Everything after this marker is appended blocks
# and nothing else, so reading the journal never has to reason about the rest
# of the document.
#
# The marker is not decoration. Without it, finding "the highest sequence in
# this file" means scanning the whole text for `data-sequence="N"` — and the
# document has component scripts inlined in it, one of which documents this
# very format in a comment containing `data-sequence="42"`. That scan read 43
# as the last sequence of an empty journal. A delimited region cannot be
# fooled by anything a script's source happens to contain.
JOURNAL_MARKER = "<!-- ontobdc:global-event-journal -->"

_BLOCK_RE = re.compile(
    rf'<script\b[^>]*\b{re.escape(JOURNAL_ATTR)}\s*=\s*"true"[^>]*>(.*?)</script>',
    re.IGNORECASE | re.DOTALL,
)
_BLOCK_TAG_RE = re.compile(
    rf'<script\b([^>]*\b{re.escape(JOURNAL_ATTR)}\s*=\s*"true"[^>]*)>',
    re.IGNORECASE,
)
_SEQUENCE_RE = re.compile(r'\bdata-sequence\s*=\s*"(-?\d+)"')
_EVENT_ID_RE = re.compile(r'\bdata-event-id\s*=\s*"([^"]*)"')
# An embedded component script has its own `</script>` escaped by the
# generator, so this really does step over whole script bodies rather than
# stopping inside one.
_SCRIPT_RE = re.compile(r"<script\b([^>]*)>(.*?)</script>", re.IGNORECASE | re.DOTALL)


def journal_region(document: str) -> str:
    """The part of the document that holds appended events.

    A document with no marker has no journal region yet; treating the whole
    file as one is what produced the false readings described above, so this
    returns nothing instead.
    """
    index = document.find(JOURNAL_MARKER)
    return "" if index == -1 else document[index + len(JOURNAL_MARKER) :]


def _durable_write(path: Path, text: str) -> None:
    """Write and fsync, so `os.replace` swaps in content that is on the disk
    rather than only in the page cache."""
    with open(path, "w", encoding="utf-8") as handle:
        handle.write(text)
        handle.flush()
        os.fsync(handle.fileno())


class GlobalEventError(Exception):
    """A Global Event request could not be accepted."""


@dataclass(frozen=True)
class GlobalEventOperation:
    operation: str
    predicate: str
    value: Optional[Dict[str, Any]] = None

    def as_payload(self) -> Dict[str, Any]:
        payload: Dict[str, Any] = {"operation": self.operation, "predicate": self.predicate}
        if self.value is not None:
            payload["value"] = self.value
        return payload


# --------------------------------------------------------------------------
# Escaping
# --------------------------------------------------------------------------


def escape_for_script(payload: Any) -> str:
    """Serialize a payload so nothing inside it can end its `<script>` block.

    Escaping every `<` (rather than only the literal `</script>`) also covers
    the variants an HTML parser accepts — `</script >`, `</SCRIPT`, a
    `<!--` that would open a comment — with one rule instead of a list of
    special cases to keep in sync with a parser.

    `\\u003c` is a JSON escape for `<`, so the browser reads the original
    character back.
    """
    return json.dumps(payload, ensure_ascii=False).replace("<", "\\u003c")


# --------------------------------------------------------------------------
# Reading the journal
# --------------------------------------------------------------------------


def journal_entries(document: str) -> List[Dict[str, Any]]:
    """Every complete Global Event block already in the document."""
    entries: List[Dict[str, Any]] = []
    for match in _BLOCK_RE.finditer(journal_region(document)):
        try:
            entries.append(json.loads(match.group(1)))
        except json.JSONDecodeError:
            continue
    return entries


def journal_event_ids(document: str) -> List[str]:
    """The `eventId`s the document already carries.

    Read from the block attributes, not the JSON bodies: a duplicate has to
    be detectable without parsing every payload, and the attribute is what an
    interrupted write would have flushed first anyway.
    """
    ids: List[str] = []
    for tag in _BLOCK_TAG_RE.finditer(journal_region(document)):
        found = _EVENT_ID_RE.search(tag.group(1))
        if found:
            ids.append(found.group(1))
    return ids


def last_sequence(document: str) -> int:
    """The highest sequence in the document — journal blocks and the
    snapshot's own `data-snapshot-through`, so a compacted document still
    reports where the numbering got to."""
    sequences = [
        int(found.group(1))
        for tag in _BLOCK_TAG_RE.finditer(journal_region(document))
        for found in [_SEQUENCE_RE.search(tag.group(1))]
        if found
    ]
    sequences.append(snapshot_through(document))
    return max(sequences)


def snapshot_through(document: str) -> int:
    """The highest sequence the snapshot already incorporates, or -1."""
    for script in _SCRIPT_RE.finditer(document):
        attributes = script.group(1)
        if f'id="{JSONLD_ID}"' not in attributes:
            continue
        found = re.search(
            rf'\b{re.escape(SNAPSHOT_THROUGH_ATTR)}\s*=\s*"(-?\d+)"', attributes
        )
        return int(found.group(1)) if found else -1
    return -1


# --------------------------------------------------------------------------
# Preparing a generated document
# --------------------------------------------------------------------------


def document_accepts_journal(document: str) -> bool:
    """True when a block appended to the end of this file will parse as a
    child of `<body>` rather than through HTML error recovery."""
    tail = document.rstrip().lower()
    if tail.endswith("</html>") or tail.endswith("</body>"):
        return False
    return JOURNAL_MARKER in document


def prepare_document_for_journal(document: str) -> str:
    """Drop the optional `</body>`/`</html>` end tags from a generated
    document so events can be appended to the end of the file.

    Both tags are optional in the HTML syntax; a parser closes the elements
    at end of file. Anything appended after this point is therefore parsed as
    ordinary trailing content of `<body>` — which is what the replay runtime
    walks — instead of relying on a browser's tolerance for content that
    follows `</html>`.
    """
    trimmed = document.rstrip()
    if trimmed.endswith(JOURNAL_MARKER):
        return trimmed + "\n"
    for closing in ("</html>", "</body>"):
        while trimmed.lower().endswith(closing):
            trimmed = trimmed[: -len(closing)].rstrip()
    return f"{trimmed}\n{JOURNAL_MARKER}\n"


def set_snapshot_through(document: str, sequence: int) -> str:
    """Record on the snapshot block which sequences it already contains."""
    pattern = re.compile(
        rf'(<script\b[^>]*\bid="{re.escape(JSONLD_ID)}")([^>]*)>'
    )
    match = pattern.search(document)
    if not match:
        raise GlobalEventError(
            f"the document has no <script id=\"{JSONLD_ID}\"> to mark"
        )
    attributes = re.sub(
        rf'\s*{re.escape(SNAPSHOT_THROUGH_ATTR)}\s*=\s*"[^"]*"', "", match.group(2)
    )
    return (
        document[: match.start()]
        + f'{match.group(1)}{attributes} {SNAPSHOT_THROUGH_ATTR}="{sequence}">'
        + document[match.end() :]
    )


# --------------------------------------------------------------------------
# Appending
# --------------------------------------------------------------------------


def render_block(payload: Dict[str, Any]) -> str:
    """One journal block, ready to append."""
    return (
        f'\n{_BLOCK_OPEN}'
        f' data-event-id="{payload["eventId"]}"'
        f' data-sequence="{payload["sequence"]}">\n'
        f"{escape_for_script(payload)}\n"
        f"{_BLOCK_CLOSE}\n"
    )


def truncate_incomplete_block(path: Path) -> bool:
    """Cut a partially written block off the end of the file.

    A crash between the `write` and the `fsync` of an append can leave a
    block that has an opening tag and no `</script>`. Left there, the HTML
    parser swallows everything after it — including the next event appended.
    Every complete block ends with `</script>`, so the last one is the safe
    truncation point.

    Returns True when the file was truncated.
    """
    data = path.read_bytes()
    text = data.decode("utf-8", errors="replace")
    opens = text.rfind(_BLOCK_OPEN)
    if opens == -1:
        return False
    closes = text.rfind(_BLOCK_CLOSE)
    if closes > opens:
        return False  # the last block is complete

    # Everything from the dangling opening tag onward is unusable.
    keep = text[:opens].rstrip() + "\n"
    with open(path, "r+b") as handle:
        encoded = keep.encode("utf-8")
        handle.seek(0)
        handle.write(encoded)
        handle.truncate(len(encoded))
        handle.flush()
        os.fsync(handle.fileno())
    return True


def append_event(path: Path, payload: Dict[str, Any]) -> None:
    """Append one rendered block to the document and get it onto the disk.

    Binary append mode, one `write`, then `flush` + `fsync`. The rest of the
    file is never read: appending an event costs the size of the event, not
    the size of the snapshot.
    """
    block = render_block(payload).encode("utf-8")
    with open(path, "ab") as handle:
        handle.write(block)
        handle.flush()
        os.fsync(handle.fileno())


# --------------------------------------------------------------------------
# The writer
# --------------------------------------------------------------------------


class GlobalEventJournalWriter:
    """Assigns sequences and appends events to one Surface document.

    Callers hold the journal lock; this class is the part that has to be
    right about ordering, duplicates and durability.
    """

    def __init__(self, surface_path: Path, state_path: Path) -> None:
        self._surface_path = Path(surface_path)
        self._state_path = Path(state_path)

    # -- sequence state ----------------------------------------------------

    def _read_state(self) -> Dict[str, Any]:
        try:
            return json.loads(self._state_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return {}

    def _write_state(self, state: Dict[str, Any]) -> None:
        self._state_path.parent.mkdir(parents=True, exist_ok=True)
        body = json.dumps(state, ensure_ascii=False, indent=2) + "\n"
        AtomicFileWriter.write(
            self._state_path, lambda temp: _durable_write(temp, body)
        )

    def next_sequence(self, document: str) -> int:
        """The sequence to assign next.

        Taken as the higher of the persisted counter and what the document
        itself already shows, so a lost or rolled-back state file can never
        hand out a number already in the journal — which would make two
        different events indistinguishable to the replay's ordering.
        """
        persisted = int(self._read_state().get("lastSequence", -1))
        return max(persisted, last_sequence(document)) + 1

    # -- appending ---------------------------------------------------------

    def append(
        self,
        *,
        event: str,
        entity: str,
        operations: List[GlobalEventOperation],
        source: Optional[Dict[str, Any]] = None,
        event_id: Optional[str] = None,
        occurred_at: Optional[str] = None,
    ) -> Tuple[Dict[str, Any], bool]:
        """Append one Global Event. Returns the payload and whether it was new.

        Re-appending an `eventId` the document already carries is a no-op that
        reports the existing state instead of raising: a request that was
        persisted but whose acknowledgement never got written will be retried,
        and the retry must converge rather than duplicate the event.
        """
        if not str(event or "").strip():
            raise GlobalEventError("a Global Event needs an event type IRI")
        if not str(entity or "").strip():
            raise GlobalEventError("a Global Event needs the entity's exact @id")
        if not operations:
            raise GlobalEventError("a Global Event needs at least one operation")
        for operation in operations:
            if not str(operation.predicate or "").strip():
                raise GlobalEventError("every operation needs a predicate IRI")
            if not str(operation.predicate).startswith(("http://", "https://", "urn:")):
                raise GlobalEventError(
                    f"predicate {operation.predicate!r} is not an IRI — a column "
                    "label is not a predicate"
                )

        resolved_id = str(event_id or f"urn:uuid:{uuid.uuid4()}")

        # A truncated tail would swallow whatever is appended after it.
        truncate_incomplete_block(self._surface_path)
        document = self._surface_path.read_text(encoding="utf-8")

        if resolved_id in journal_event_ids(document):
            existing = next(
                (
                    entry
                    for entry in journal_entries(document)
                    if entry.get("eventId") == resolved_id
                ),
                {"eventId": resolved_id},
            )
            return existing, False

        payload = {
            "event": str(event).strip(),
            "eventId": resolved_id,
            "sequence": self.next_sequence(document),
            "occurredAt": occurred_at or datetime.now(timezone.utc).isoformat(),
            "source": source or {},
            "entity": str(entity).strip(),
            "operations": [operation.as_payload() for operation in operations],
        }

        append_event(self._surface_path, payload)
        # Only after the append is on the disk: a state file ahead of the
        # journal would skip a sequence, which is survivable, but one written
        # before a failed append would claim a number the journal never got.
        self._write_state({"lastSequence": payload["sequence"]})
        return payload, True

    # -- compaction --------------------------------------------------------

    def compact(self, materialized_document: str) -> str:
        """Fold the journal into a freshly generated document.

        `materialized_document` is a full regeneration — the sources were
        re-read, so the snapshot in it already contains everything the
        journal was carrying. Mark how far it goes and drop the blocks it
        absorbed; anything that arrived after the cutoff is preserved.

        This is the one path that rewrites the document, and it is also the
        only one that is allowed to: it runs while the journal lock is held
        and writes through an atomic replace, so a reader never sees a
        document with the events removed but the new snapshot not yet in.
        """
        cutoff = last_sequence(self._surface_path.read_text(encoding="utf-8"))
        prepared = prepare_document_for_journal(
            set_snapshot_through(materialized_document, cutoff)
        )
        # Nothing to carry over: the regeneration read the same sources the
        # journal described, so every event at or below the cutoff is in the
        # new snapshot by construction.
        return prepared

    def write_compacted(self, materialized_document: str) -> int:
        """Compact and replace the document atomically. Returns the cutoff."""
        document = self.compact(materialized_document)
        cutoff = snapshot_through(document)
        AtomicFileWriter.write(
            self._surface_path, lambda temp: _durable_write(temp, document)
        )
        self._write_state({"lastSequence": max(cutoff, self._read_state().get("lastSequence", -1))})
        return cutoff
