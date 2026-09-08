"""Readers for the static Page assets packaged under this directory."""

from importlib.resources import files


def file_viewer_source() -> str:
    """The standalone file-viewer page's ready-to-write HTML.

    `onto-file-tree-tile` opens this page (written by
    `SurfacePackagedCapability` to
    `.__ontobdc__/view/onto-file-viewer.html`, relative to the container
    root) with the clicked file's path passed by reference in the query
    string -- the one place, and the only moment, a real container file is
    ever read. The asset is static; it carries no build placeholder, so it
    is returned verbatim.
    """
    source = (
        files(__package__)
        .joinpath("file_viewer.html")
        .read_text(encoding="utf-8")
    )
    if not source.strip():
        raise ValueError(
            "The packaged file-viewer asset "
            "(ontobdc_view/page/plugin/asset/file_viewer.html) is empty."
        )
    return source
