from pathlib import Path

from ontobdc.storage.plugin.check.is_container_manifest_synced.check import (
    _expected_file_properties,
    _metadata_matches,
)
from ontobdc.storage.plugin.check.is_container_manifest_synced.hotfix import (
    _file_properties,
)


def test_file_properties_include_logical_size_and_basic_ro_crate_metadata(tmp_path: Path) -> None:
    file_path = tmp_path / "report.txt"
    file_path.write_text("abc", encoding="utf-8")

    properties = _file_properties(file_path)

    assert properties["name"] == "report.txt"
    assert properties["contentSize"] == "3"
    assert properties["encodingFormat"] == "text/plain"
    assert properties["dateModified"].endswith("Z")


def test_check_uses_same_filesystem_metadata_contract(tmp_path: Path) -> None:
    file_path = tmp_path / "report.txt"
    file_path.write_text("abc", encoding="utf-8")

    assert _expected_file_properties(file_path) == _file_properties(file_path)


def test_metadata_match_detects_file_size_change(tmp_path: Path) -> None:
    file_path = tmp_path / "report.txt"
    file_path.write_text("abc", encoding="utf-8")
    properties = _file_properties(file_path)
    crate_data = {
        "@graph": [
            {
                "@id": "report.txt",
                "@type": "File",
                **properties,
            }
        ]
    }

    assert _metadata_matches(tmp_path, {"report.txt"}, crate_data)

    file_path.write_text("abcdef", encoding="utf-8")

    assert not _metadata_matches(tmp_path, {"report.txt"}, crate_data)
