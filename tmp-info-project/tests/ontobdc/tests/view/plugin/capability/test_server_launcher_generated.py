from ontobdc.cli.adapter.context import CliContextAdapter
from ontobdc.view.adapter.surface.document import make_initial_html, set_state_marker
from ontobdc.view.domain.machine.surface_state import SurfaceGenerationProcessState
from ontobdc.view.plugin.capability.transformation.server_launcher_generated import (
    ServerLauncherGeneratedCapability,
)
from ontobdc.view.plugin.check.is_server_launcher_generated.check import (
    DEFAULT_SERVER_HOST,
    DEFAULT_SERVER_PORT,
    DYNAMIC_PORT_MAX,
    DYNAMIC_PORT_MIN,
    SERVER_LAUNCHER_FILENAME,
    extract_server_reference,
    launcher_lines,
    main as check_server_launcher_generated,
    read_launcher_reference,
)


def _context(container_path):
    context = CliContextAdapter([])
    context.set_parameter_value("container_path", str(container_path))
    return context


def test_server_launcher_generates_random_port_and_writes_every_html(
    tmp_path,
) -> None:
    index_path = tmp_path / "index.html"
    index_path.write_text(
        set_state_marker(
            make_initial_html(),
            "entity_views_published",
        ),
        encoding="utf-8",
    )
    detail_path = (
        tmp_path
        / ".__ontobdc__"
        / "view"
        / "work_stream"
        / "ws-1.html"
    )
    detail_path.parent.mkdir(parents=True)
    detail_path.write_text(make_initial_html(), encoding="utf-8")
    context = _context(tmp_path)

    result = ServerLauncherGeneratedCapability().execute(context)

    launcher_path = tmp_path / SERVER_LAUNCHER_FILENAME
    assert launcher_path.is_file()
    reference = read_launcher_reference(launcher_path)
    assert reference is not None
    host, port = reference
    assert host == DEFAULT_SERVER_HOST
    assert DYNAMIC_PORT_MIN <= port <= DYNAMIC_PORT_MAX
    assert tuple(launcher_path.read_text(encoding="utf-8").splitlines()) == (
        launcher_lines(host, port)
    )

    for html_path in (index_path, detail_path):
        embedded = extract_server_reference(
            html_path.read_text(encoding="utf-8")
        )
        assert embedded == {"host": host, "port": port}
        html = html_path.read_text(encoding="utf-8")
        assert f'"host":"{DEFAULT_SERVER_HOST}"' in html
        assert f'"port":{DEFAULT_SERVER_PORT}' in html
        assert "ontobdcServerReference" in html

    assert result["resulting_state"] == (
        SurfaceGenerationProcessState.SERVER_LAUNCHER_GENERATED
    )
    assert result["launcher_path"] == str(launcher_path)
    assert result["host"] == host
    assert result["port"] == port
    assert context.get_parameter_value("server_host") == host
    assert context.get_parameter_value("server_port") == port
    assert check_server_launcher_generated(str(index_path)) == 0


def test_server_launcher_reuses_existing_generated_port(tmp_path) -> None:
    index_path = tmp_path / "index.html"
    index_path.write_text(
        set_state_marker(make_initial_html(), "entity_views_published"),
        encoding="utf-8",
    )
    context = _context(tmp_path)

    first = ServerLauncherGeneratedCapability().execute(context)
    first_port = first["port"]

    # Simulate a fresh invocation context against the same portable container.
    index_path.write_text(
        set_state_marker(make_initial_html(), "entity_views_published"),
        encoding="utf-8",
    )
    second_context = _context(tmp_path)
    second = ServerLauncherGeneratedCapability().execute(second_context)

    assert second["port"] == first_port
    assert check_server_launcher_generated(str(index_path)) == 0


def test_explicit_server_port_overrides_persisted_generated_port(tmp_path) -> None:
    index_path = tmp_path / "index.html"
    index_path.write_text(
        set_state_marker(make_initial_html(), "entity_views_published"),
        encoding="utf-8",
    )
    first_context = _context(tmp_path)
    ServerLauncherGeneratedCapability().execute(first_context)

    index_path.write_text(
        set_state_marker(make_initial_html(), "entity_views_published"),
        encoding="utf-8",
    )
    context = _context(tmp_path)
    context.set_parameter_value("server_port", 55001)
    result = ServerLauncherGeneratedCapability().execute(context)

    assert result["port"] == 55001
    assert read_launcher_reference(tmp_path / SERVER_LAUNCHER_FILENAME) == (
        DEFAULT_SERVER_HOST,
        55001,
    )
    assert check_server_launcher_generated(str(index_path)) == 0


def test_server_launcher_check_rejects_missing_or_modified_launcher(
    tmp_path,
) -> None:
    index_path = tmp_path / "index.html"
    index_path.write_text(
        set_state_marker(
            make_initial_html(),
            "server_launcher_generated",
        ),
        encoding="utf-8",
    )

    assert check_server_launcher_generated(str(index_path)) != 0

    launcher_path = tmp_path / SERVER_LAUNCHER_FILENAME
    launcher_path.write_text("@echo off\nwrong command\n", encoding="utf-8")
    assert check_server_launcher_generated(str(index_path)) != 0
