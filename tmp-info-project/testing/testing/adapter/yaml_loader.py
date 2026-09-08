from pathlib import Path
from typing import Any, Dict, List

import yaml

from ontobdc_dev.testing.domain.exception import TestManifestError


def load_documents(path: Path) -> List[Dict[str, Any]]:
    """Load every YAML document under `path` as a plain dict.

    `path` may be a single file or a directory, searched recursively for
    `*.yaml` files (semantic-test-orchestrator.md, 18: `tests/semantic/`).
    A file may contain multiple `---`-separated documents (7.1: "documentos
    podem ser separados por `---`"). Each returned dict carries its source
    path under `_source_path` for error messages.
    """

    documents: List[Dict[str, Any]] = []
    for manifest_path in _iter_manifest_paths(path):
        with open(manifest_path, "r", encoding="utf-8") as file_handle:
            try:
                raw_documents: List[Any] = list(yaml.safe_load_all(file_handle))
            except yaml.YAMLError as exception:
                raise TestManifestError(
                    f"Invalid YAML in '{manifest_path}': {exception}"
                ) from exception

        for raw_document in raw_documents:
            if raw_document is None:
                continue
            if not isinstance(raw_document, dict):
                raise TestManifestError(
                    f"Manifest document in '{manifest_path}' is not a mapping."
                )
            raw_document["_source_path"] = str(manifest_path)
            documents.append(raw_document)

    return documents


def _iter_manifest_paths(path: Path) -> List[Path]:
    if path.is_file():
        return [path]

    if path.is_dir():
        return sorted(
            candidate
            for candidate in path.rglob("*.yaml")
            if candidate.is_file()
        )

    raise TestManifestError(f"Manifest path does not exist: {path}")
