import json
import logging
import re
import time
from typing import Any, Dict, Optional, Set

from ontobdc_view.surface.adapter.document import MATCHES_ID, SURFACE_TAG, SurfaceDocumentAdapter

_LOGGER: logging.Logger = logging.getLogger(__name__)


class SurfaceAssemblyAdapter:
    """Whether an assembled Surface document actually carries its matched Tiles.

    Ported as a single centralized adapter -- rather than duplicated per
    `check.py`, like every other small state predicate in this package --
    because `has_assembled_tiles` is the one non-trivial piece of this
    cascade: a single O(document_chars) scan replacing a legacy
    O(matches x document_chars) regex cascade that used to read 40+ GB of
    string bytes per call (2000 tiles x 2 regex searches x 10 MB document),
    causing 5+ minute hangs. Duplicating that algorithm per caller would
    risk silently reintroducing the bug it was written to fix. Its debug
    metrics (`_DBG_METRICS`) are read by more than one Surface capability,
    which also argues for one shared owner instead of N copies.
    """

    _DBG_METRICS: Dict[str, Any] = {}

    _SURFACE_OPEN_RE: Any = re.compile(
        rf"<{SURFACE_TAG}\b[^>]*>",
        re.IGNORECASE | re.DOTALL,
    )
    _SURFACE_CLOSE_RE: Any = re.compile(
        rf"</{SURFACE_TAG}\s*>",
        re.IGNORECASE,
    )
    _TILE_ATTRS_RE: Any = re.compile(
        r"<(?P<tag>[A-Za-z][A-Za-z0-9._:-]*)"
        r"(?P<attrs>\s[^<>]*?)>",
        re.DOTALL,
    )
    _ATTR_RE: Any = re.compile(
        r"""
        (?P<name>[a-z_:][\w:.-]*)\s*=\s*
        (?:
            "(?P<dq>[^"\\]*(?:\\.[^"\\]*)*)"
          | '(?P<sq>[^'\\]*(?:\\.[^'\\]*)*)'
        )
        """,
        re.IGNORECASE | re.VERBOSE,
    )

    @classmethod
    def has_assembled_tiles(cls, document: str) -> bool:
        #region debug-point (infobim-view-slow-crash): H2/H3 instrumentation for O(T·html_bytes)
        _dbg_t0: float = time.perf_counter()
        #endregion
        if re.search(
            rf"<{SURFACE_TAG}\b[^>]*\bdata-ontobdc-assembled=[\"']true[\"']",
            document,
            re.IGNORECASE,
        ) is None:
            #region debug-point (infobim-view-slow-crash): persist short-circuit metric
            cls._DBG_METRICS["has_assembled_tiles"] = {
                "seconds": round(time.perf_counter() - _dbg_t0, 4),
                "matches": 0,
                "document_chars": len(document),
                "short_circuit_assembled_attr": True,
                "per_tile_regex_searches": 0,
            }
            #endregion
            return False

        try:
            matches = SurfaceDocumentAdapter.extract_json_script(document, MATCHES_ID)
        except (ValueError, json.JSONDecodeError):
            #region debug-point (infobim-view-slow-crash): persist error metric
            cls._DBG_METRICS["has_assembled_tiles"] = {
                "seconds": round(time.perf_counter() - _dbg_t0, 4),
                "matches": 0,
                "document_chars": len(document),
                "matches_invalid": True,
                "per_tile_regex_searches": 0,
            }
            #endregion
            return False
        if not isinstance(matches, list):
            #region debug-point (infobim-view-slow-crash): persist invalid metric
            cls._DBG_METRICS["has_assembled_tiles"] = {
                "seconds": round(time.perf_counter() - _dbg_t0, 4),
                "matches": 0,
                "document_chars": len(document),
                "matches_not_a_list": True,
                "per_tile_regex_searches": 0,
            }
            #endregion
            return False

        #region debug-point (infobim-view-slow-crash): H2/H3 instrumentation
        _dbg_regex_searches: int = 0
        #endregion

        # Build the expected tile tag attribute lookup ONCE (single pass O(chars))
        # either over the extracted surface inner markup (~50-200 KB) or the full
        # document (~10 MB). Either way it's a SINGLE constant-factor string scan
        # that replaces the previous O(T · len(document)) regex cascade that was
        # reading 40+ GB of string bytes (2 per tile × 2000 tiles × 10 MB) on
        # every check/validate call, causing 5+ minute hangs when the document
        # wasn't freshly assembled or had an unusual surface-open tag ordering.
        #
        # CRITICAL: we MUST NOT fall back to O(T · N_bytes) per-tile regex. That
        # legacy path is the root cause of the 5-minute SurfaceAssembled stall
        # (10 require_check retries × 30s each). A single 10 MB regex scan is
        # always preferable and stays under 1 second even on slow systems.
        surface_body: Optional[str] = cls._extract_surface_inner_markup(document)
        lut_source: str = surface_body if surface_body is not None else document
        present_tiles: Dict[tuple[str, str], Set[str]] = cls._build_tile_lut(lut_source) or {}
        _lut_from_full_doc: bool = surface_body is None

        for item in matches:
            if not isinstance(item, dict):
                cls._DBG_METRICS["has_assembled_tiles"] = {
                    "seconds": round(time.perf_counter() - _dbg_t0, 4),
                    "matches": len(matches),
                    "document_chars": len(document),
                    "item_invalid": True,
                    "per_tile_regex_searches": _dbg_regex_searches,
                    "fast_lut": True,
                    "lut_from_full_document": _lut_from_full_doc,
                }
                return False
            tile_name = str(item.get("tile", "")).strip()
            region = str(item.get("region", "")).strip()
            if not tile_name or not region:
                cls._DBG_METRICS["has_assembled_tiles"] = {
                    "seconds": round(time.perf_counter() - _dbg_t0, 4),
                    "matches": len(matches),
                    "document_chars": len(document),
                    "item_missing_fields": True,
                    "per_tile_regex_searches": _dbg_regex_searches,
                    "fast_lut": True,
                    "lut_from_full_document": _lut_from_full_doc,
                }
                return False

            bucket: Optional[Set[str]] = present_tiles.get((tile_name.lower(), region.lower()))
            if bucket is None:
                lut_keys: list[tuple[str, str]] = list(present_tiles.keys())[:20]
                _LOGGER.error(
                    "has_assembled_tiles FAIL: tile %r region %r (key=%r) not in LUT "
                    "(lut_size=%d sample_keys=%s lut_from_full_doc=%s)",
                    tile_name, region, (tile_name.lower(), region.lower()),
                    len(present_tiles), lut_keys, _lut_from_full_doc,
                )
                cls._DBG_METRICS["has_assembled_tiles"] = {
                    "seconds": round(time.perf_counter() - _dbg_t0, 4),
                    "matches": len(matches),
                    "document_chars": len(document),
                    "tile_not_found": tile_name,
                    "tile_region": region,
                    "per_tile_regex_searches": _dbg_regex_searches,
                    "fast_lut": True,
                    "lut_from_full_document": _lut_from_full_doc,
                    "lut_size": len(present_tiles),
                    "lut_sample_keys": lut_keys,
                }
                return False
            _dbg_regex_searches += 1

            expected_data: str = str(item.get("data", "")).strip()
            if expected_data and expected_data not in bucket:
                sample_bucket: list[str] = sorted(bucket)[:10]
                _LOGGER.error(
                    "has_assembled_tiles FAIL: tile %r region %r resource MISMATCH "
                    "expected=%r bucket_size=%d bucket_sample=%s lut_from_full_doc=%s",
                    tile_name, region, expected_data[:120],
                    len(bucket), sample_bucket, _lut_from_full_doc,
                )
                cls._DBG_METRICS["has_assembled_tiles"] = {
                    "seconds": round(time.perf_counter() - _dbg_t0, 4),
                    "matches": len(matches),
                    "document_chars": len(document),
                    "data_not_found": expected_data,
                    "tile": tile_name,
                    "per_tile_regex_searches": _dbg_regex_searches + 1,
                    "fast_lut": True,
                    "lut_from_full_document": _lut_from_full_doc,
                    "bucket_size": len(bucket),
                    "bucket_sample": sample_bucket,
                }
                return False
            if expected_data:
                _dbg_regex_searches += 1

        #region debug-point (infobim-view-slow-crash): persist full success metric
        cls._DBG_METRICS["has_assembled_tiles"] = {
            "seconds": round(time.perf_counter() - _dbg_t0, 4),
            "matches": len(matches),
            "document_chars": len(document),
            "ok": True,
            "per_tile_regex_searches": _dbg_regex_searches,
            "fast_lut": True,
            "lut_from_full_document": _lut_from_full_doc,
        }
        #endregion
        return True

    @classmethod
    def _extract_surface_inner_markup(cls, document: str) -> Optional[str]:
        # Always take the LAST occurrence to avoid matching commented-out stubs
        # or stale pre-assembly tag copies that some HTML builders leave in the
        # head. Using max() on match.span() gives us the rightmost real tag.
        open_matches = list(cls._SURFACE_OPEN_RE.finditer(document))
        if not open_matches:
            return None
        open_match = open_matches[-1]
        close_matches = list(cls._SURFACE_CLOSE_RE.finditer(document, open_match.end()))
        if not close_matches:
            # Fallback: accept any close-match later in the doc (could be wrong,
            # but it's strictly better than returning None which triggers the
            # O(matches · document_chars) legacy scan that costs 5+ minutes).
            any_close = list(cls._SURFACE_CLOSE_RE.finditer(document))
            if not any_close or any_close[-1].start() <= open_match.end():
                return None
            close_match = any_close[-1]
        else:
            close_match = close_matches[0]
        return document[open_match.end():close_match.start()]

    @classmethod
    def _build_tile_lut(
        cls,
        surface_inner: str,
    ) -> Optional[Dict[tuple[str, str], Set[str]]]:
        """Return a dict of (tag, region) → {resourceId1, resourceId2, ...} from
        the tile tags inside the surface element's light DOM.

        Multiple tiles with the same (tag, region) pair are perfectly valid --
        for example 1000+ <onto-image-file-tile surface-region=content> tiles
        all in the content region, each pointing to a different photo
        resource. The LUT therefore accumulates a set of all resource ids
        observed for each key instead of only the last one (a prior bug that
        caused 100% reproducible MISMATCH failures for any real project with
        multiple tiles of the same type in the same region).
        """
        lut: Dict[tuple[str, str], Set[str]] = {}
        for match in cls._TILE_ATTRS_RE.finditer(surface_inner):
            tag: str = match.group("tag").lower()
            attrs_str: str = match.group("attrs")
            region: Optional[str] = None
            resource: str = ""
            if tag == SURFACE_TAG.lower():
                continue
            for attr in cls._ATTR_RE.finditer(attrs_str):
                name: str = attr.group("name").lower()
                value: Optional[str] = attr.group("dq") if attr.group("dq") is not None else attr.group("sq")
                if value is None:
                    continue
                if name == "surface-region":
                    region = value
                elif name == "data-ontobdc-resource":
                    resource = value
            if region is None:
                continue
            key: tuple[str, str] = (tag, region.lower())
            bucket: Optional[Set[str]] = lut.get(key)
            if bucket is None:
                bucket = set()
                lut[key] = bucket
            bucket.add(resource)
        return lut
