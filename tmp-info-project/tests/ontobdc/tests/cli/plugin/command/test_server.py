from contextlib import contextmanager
from typing import Any, Iterator, List
from unittest.mock import MagicMock, patch

import pytest

from ontobdc.cli.adapter.context import CliContextAdapter
from ontobdc.cli.domain.request.command import CliCommandRequest
from ontobdc.cli.domain.response.command import CommandResponse
from ontobdc.cli.plugin.command.server import CliServerCommand
from ontobdc.shared.adapter.loader import CommandLoader

_STRATEGY = "ontobdc.cli.plugin.command.server.ContainerIdStrategy"


@contextmanager
def _registered_container(
    path: Any, container_id: str = "urn:test:c"
) -> Iterator[None]:
    """Stub the ContainerIdStrategy so ``path`` resolves as registered."""

    def _execute(context: Any) -> Any:
        context.set_parameter_value("container_id", container_id)
        context.set_parameter_value("container_path", str(path))
        return context

    strategy = MagicMock()
    strategy.execute.side_effect = _execute
    with patch(_STRATEGY, return_value=strategy):
        yield


@contextmanager
def _registered_container_unresolved() -> Iterator[None]:
    """Stub the strategy to resolve nothing (unknown selector / bare CWD)."""

    strategy = MagicMock()
    strategy.execute.side_effect = lambda context: context
    with patch(_STRATEGY, return_value=strategy):
        yield


def _command(args: List[str]) -> CliServerCommand:
    return CliServerCommand(
        CliCommandRequest(
            logical_component="cli",
            component_action="server",
            command_args=args,
            context=CliContextAdapter(args),
        )
    )


def test_accepts_server_with_optional_valued_flags() -> None:
    assert CliServerCommand.accepts(["server"])
    assert CliServerCommand.accepts(["server", "--port", "8080"])
    assert CliServerCommand.accepts(
        ["server", "--container", "c-1", "--host", "0.0.0.0"]
    )
    assert CliServerCommand.accepts(["server", "--container-id", "urn:x"])
    assert not CliServerCommand.accepts(["server", "--port"])
    assert not CliServerCommand.accepts(["server", "--unknown", "x"])
    assert not CliServerCommand.accepts(["server", "--port", "--host"])
    assert not CliServerCommand.accepts(["server", "--port", "1", "--port", "2"])
    assert not CliServerCommand.accepts(
        ["server", "--container", "c", "--container-id", "urn:x"]
    )
    assert not CliServerCommand.accepts(["--version"])


def test_server_is_discoverable_as_a_cli_command() -> None:
    from ontobdc.cli.adapter.logger import NullLogRepository

    ids = {
        cls.METADATA.id
        for cls in CommandLoader("cli", NullLogRepository()).get_all()
        if isinstance(cls, type)
    }
    assert "server" in ids


def test_check_resolves_the_container_through_the_strategy(tmp_path) -> None:
    command = _command(
        [
            "server",
            "--container",
            "my-container",
            "--host",
            "0.0.0.0",
            "--port",
            "9000",
        ]
    )
    with _registered_container(tmp_path, container_id="urn:test:my"):
        assert command.check() is True

    context = command._request.context
    assert context.get_parameter_value("container_id") == "urn:test:my"
    assert context.get_parameter_value("container_path") == str(
        tmp_path.resolve()
    )
    assert context.get_parameter_value("server_host") == "0.0.0.0"
    assert context.get_parameter_value("server_bind_host") == "0.0.0.0"
    assert context.get_parameter_value("server_port") == 9000
    assert context.get_parameter_value("server_bind_port") == 9000


def test_check_leaves_port_for_launcher_state_when_not_supplied(tmp_path) -> None:
    command = _command(["server", "--container", "c"])
    with _registered_container(tmp_path):
        assert command.check() is True

    context = command._request.context
    assert context.get_parameter_value("server_port") is None
    assert context.get_parameter_value("server_bind_port") is None


def test_check_requires_an_explicit_container_selector() -> None:
    with pytest.raises(ValueError, match="requires an explicit container"):
        _command(["server"]).check()


def test_check_requires_a_registered_container() -> None:
    with _registered_container_unresolved():
        with pytest.raises(ValueError, match="registered container"):
            _command(["server", "--container", "nope"]).check()


def test_check_rejects_a_non_integer_port(tmp_path) -> None:
    with _registered_container(tmp_path):
        with pytest.raises(ValueError, match="--port must be an integer"):
            _command(
                ["server", "--container", "c", "--port", "abcd"]
            ).check()


def test_check_rejects_a_port_outside_the_valid_range(tmp_path) -> None:
    with _registered_container(tmp_path):
        with pytest.raises(ValueError, match="between 1 and 65535"):
            _command(
                ["server", "--container", "c", "--port", "70000"]
            ).check()
    with _registered_container(tmp_path):
        with pytest.raises(ValueError, match="between 1 and 65535"):
            _command(
                ["server", "--container", "c", "--port", "0"]
            ).check()


def test_run_uses_generated_reference_then_serves_and_opens_http(
    tmp_path,
) -> None:
    command = _command(["server", "--container", "c"])
    with _registered_container(tmp_path):
        command.check()

    stale_views = tmp_path / ".__ontobdc__" / "view"
    stale_views.mkdir(parents=True)
    (stale_views / "stale.html").write_text("stale", encoding="utf-8")

    prepared = CommandResponse(
        title="Presentation Surface Generated",
        description="generated",
        content={"current_state": "__server_launcher_generated__"},
    )
    fake_handler = MagicMock()

    def _generate() -> CommandResponse:
        assert not stale_views.exists()
        (tmp_path / "index.html").write_text("<h1>ok</h1>", encoding="utf-8")
        command._request.context.set_parameter_value("server_host", "127.0.0.1")
        command._request.context.set_parameter_value("server_port", 54321)
        return prepared

    fake_handler.execute.side_effect = _generate

    fake_server = MagicMock()
    fake_server.server_address = ("127.0.0.1", 54321)
    fake_server.serve_forever.side_effect = lambda: None

    with patch(
        "ontobdc.cli.plugin.command.server.SurfaceGenerationStateTransitionHandler",
        return_value=fake_handler,
    ) as surface_handler_type, patch(
        "ontobdc.cli.plugin.command.server.ThreadingHTTPServer",
        return_value=fake_server,
    ) as http_server_type, patch(
        "ontobdc.cli.plugin.command.server.webbrowser.open",
        return_value=True,
    ) as browser_open:
        response = command.run()

    surface_handler_type.assert_called_once_with(context=command._request.context)
    fake_handler.execute.assert_called_once_with()
    http_server_type.assert_called_once()
    assert http_server_type.call_args.args[0] == ("127.0.0.1", 54321)
    expected_url = "http://127.0.0.1:54321/?host=127.0.0.1&port=54321"
    browser_open.assert_called_once_with(expected_url, new=2)
    assert response.title == "Server"
    assert response.content["current_state"] == "__server_launcher_generated__"
    assert response.content["browser_opened"] is True
    assert response.content["stopped"] is True
    assert response.content["url"] == expected_url
    assert response.content["host"] == "127.0.0.1"
    assert response.content["port"] == 54321
    assert response.content["directory"] == str(tmp_path.resolve())
    assert "Stopped serving" in response.description
    fake_server.shutdown.assert_called_once()
    fake_server.server_close.assert_called_once()


def test_run_refuses_when_standard_view_generation_produces_no_index(
    tmp_path,
) -> None:
    command = _command(["server", "--container", "c"])
    with _registered_container(tmp_path):
        command.check()

    fake_handler = MagicMock()
    fake_handler.execute.return_value = CommandResponse(
        title="Presentation Surface Generated",
        description="",
        content={},
    )

    with patch(
        "ontobdc.cli.plugin.command.server.SurfaceGenerationStateTransitionHandler",
        return_value=fake_handler,
    ):
        with pytest.raises(FileNotFoundError, match="no index.html"):
            command.run()
