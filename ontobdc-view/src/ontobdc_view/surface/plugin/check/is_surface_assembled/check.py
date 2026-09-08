import json
import re
from pathlib import Path
from typing import Optional
from ontobdc_view.surface.adapter.assembly import SurfaceAssemblyAdapter
from ontobdc_view.surface.adapter.document import (
    CONFIG_ID,
    DEFAULT_LAYOUTS_ID,
    JSONLD_ID,
    MATCHES_ID,
    SURFACE_TAG,
    SurfaceDocumentAdapter,
)


def main(surface_path: Optional[str] = None) -> int:
    try:
        _, document = resolve_document(surface_path)
    except Exception:
        return 1
    return 0 if is_assembled_surface(document) else 1


def is_assembled_surface(document: str) -> bool:
    return is_operational_matched_surface(document) and SurfaceAssemblyAdapter.has_assembled_tiles(document)


def is_operational_matched_surface(document: str) -> bool:
    return is_matched_surface(document) and has_valid_default_layouts(document)


def is_matched_surface(document: str) -> bool:
    return is_set_surface(document) and has_surface_matches(document)


def is_set_surface(document: str) -> bool:
    return is_enriched_surface(document) and has_surface_config(document)


def is_enriched_surface(document: str) -> bool:
    return has_initialized_surface(document) and has_jsonld(document)


def has_initialized_surface(document: str) -> bool:
    return (
        "<!doctype html" in document.lower()
        and re.search(r"<html\b", document, re.IGNORECASE) is not None
        and re.search(r"<head\b", document, re.IGNORECASE) is not None
        and re.search(r"<body\b", document, re.IGNORECASE) is not None
        and re.search(rf"<{SURFACE_TAG}\b", document, re.IGNORECASE) is not None
    )


def has_jsonld(document: str) -> bool:
    try:
        payload = SurfaceDocumentAdapter.extract_json_script(document, JSONLD_ID)
    except (ValueError, json.JSONDecodeError):
        return False
    return isinstance(payload, (dict, list))


def has_surface_config(document: str) -> bool:
    try:
        config = SurfaceDocumentAdapter.extract_json_script(document, CONFIG_ID)
    except (ValueError, json.JSONDecodeError):
        return False
    if not isinstance(config, dict):
        return False
    content = config.get("content")
    if not isinstance(content, dict) or content.get("mode") not in {"fixed", "scroll"}:
        return False
    return all(
        key in config
        for key in ("operation", "pinned", "slotTarget", "gap", "padding", "tileMargin")
    )


def has_surface_matches(document: str) -> bool:
    try:
        matches = SurfaceDocumentAdapter.extract_json_script(document, MATCHES_ID)
    except (ValueError, json.JSONDecodeError):
        return False
    if not isinstance(matches, list):
        return False

    required = {
        "tile",
        "region",
        "minColumns",
        "preferredColumns",
        "maxColumns",
        "minRows",
        "preferredRows",
        "maxRows",
    }
    for item in matches:
        if not isinstance(item, dict) or not required.issubset(item):
            return False
    return True


def has_valid_default_layouts(document: str) -> bool:
    try:
        payload = SurfaceDocumentAdapter.extract_json_script(document, DEFAULT_LAYOUTS_ID)
    except (ValueError, json.JSONDecodeError):
        # Absence is fine -- SURFACE_OPERATIONAL_MATCHED is a legal no-op
        # when no DefaultSurfaceLayout/PresentationSurface RDF is configured.
        return True
    return isinstance(payload, list) and all(
        isinstance(item, dict) and "iri" in item for item in payload
    )


def resolve_document(surface_path: Optional[str]) -> tuple[Path, str]:
    path = SurfaceDocumentAdapter.resolve_surface_path(surface_path)
    if not path.is_file():
        raise FileNotFoundError(path)
    return path, SurfaceDocumentAdapter.read_surface(path)
