import json
import re
from pathlib import Path
from typing import Optional
from ontobdc_view.surface.adapter.document import CONFIG_ID, JSONLD_ID, SURFACE_TAG, SurfaceDocumentAdapter


def main(surface_path: Optional[str] = None) -> int:
    try:
        _, document = resolve_document(surface_path)
    except Exception:
        return 1
    return 0 if is_set_surface(document) else 1


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


def resolve_document(surface_path: Optional[str]) -> tuple[Path, str]:
    path = SurfaceDocumentAdapter.resolve_surface_path(surface_path)
    if not path.is_file():
        raise FileNotFoundError(path)
    return path, SurfaceDocumentAdapter.read_surface(path)
