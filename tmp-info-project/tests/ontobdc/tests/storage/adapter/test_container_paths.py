from ontobdc.storage.adapter.manifest import ContainerDataPackageSynchronizer


def test_list_container_file_paths_includes_every_format(tmp_path):
    # Regression: data_gathered.py's RO-Crate/Surface file inventory used to
    # reuse list_resource_paths() (frictionless-gated), so any file whose
    # extension frictionless has no registered parser for (images, PDFs,
    # plain text, ...) silently vanished from the generated Surface's file
    # tree and size totals, even though dedicated Tiles exist for exactly
    # those types (onto-image-file-tile, onto-pdf-file-tile, ...).
    (tmp_path / "data").mkdir()
    (tmp_path / "data" / "table.csv").write_text("a,b\n1,2\n", encoding="utf-8")
    (tmp_path / "docs").mkdir()
    (tmp_path / "docs" / "note.txt").write_text("hello", encoding="utf-8")
    (tmp_path / "docs" / "report.pdf").write_bytes(b"%PDF-1.4 fake")
    (tmp_path / "docs" / "photo.jpg").write_bytes(b"\xff\xd8\xff\xe0fake")

    paths = set(ContainerDataPackageSynchronizer.list_container_file_paths(tmp_path))

    assert paths == {
        "data/table.csv",
        "docs/note.txt",
        "docs/report.pdf",
        "docs/photo.jpg",
    }


def test_list_resource_paths_stays_narrowed_to_frictionless_formats(tmp_path):
    # list_resource_paths() backs the frictionless Data Package descriptor
    # sync and container_healthy's pruning — it must keep excluding formats
    # frictionless can't parse, unlike list_container_file_paths() above.
    (tmp_path / "table.csv").write_text("a,b\n1,2\n", encoding="utf-8")
    (tmp_path / "note.txt").write_text("hello", encoding="utf-8")
    (tmp_path / "photo.jpg").write_bytes(b"\xff\xd8\xff\xe0fake")

    paths = set(ContainerDataPackageSynchronizer.list_resource_paths(tmp_path))

    assert paths == {"table.csv"}


def test_list_container_file_paths_excludes_ontobdc_internals(tmp_path):
    (tmp_path / "table.csv").write_text("a,b\n1,2\n", encoding="utf-8")
    internal_dir = tmp_path / ".__ontobdc__"
    internal_dir.mkdir()
    (internal_dir / "datapackage.json").write_text("{}", encoding="utf-8")

    paths = set(ContainerDataPackageSynchronizer.list_container_file_paths(tmp_path))

    assert paths == {"table.csv"}
