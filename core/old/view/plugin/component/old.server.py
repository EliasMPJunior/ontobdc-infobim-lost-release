import threading
import webbrowser
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any, Dict, List, Optional
from urllib.parse import urlencode

from ontobdc.cli.adapter.logger import NullLogRepository
from ontobdc.cli.domain.model.command import CliCommandMetadata
from ontobdc.cli.domain.model.logger import LogStrategyConfig
from ontobdc.cli.domain.port.command import CliCommandPort
from ontobdc.cli.domain.port.logger import LogRepositoryPort
from ontobdc.cli.domain.request.command import CliCommandRequest
from ontobdc.cli.domain.response.command import CommandResponse
from ontobdc.shared.adapter.filesystem import remove_directory_tree, remove_file
from ontobdc.storage.plugin.parameter.container import ContainerIdStrategy
from ontobdc.view.adapter.surface.context import SurfaceContextAdapter
from ontobdc.view.adapter.surface.machine import SurfaceGenerationStateTransitionHandler
from ontobdc.view.plugin.capability.transformation.data_gathered import DataGatheredCapability
from ontobdc.view.plugin.check.is_server_launcher_generated.check import (
    DEFAULT_SERVER_HOST,
    DEFAULT_SERVER_PORT,
)


class CliServerCommand(CliCommandPort):
    """Generate the standard container view, serve it over HTTP, and open it."""

    METADATA = CliCommandMetadata(
        id="server",
        logical_component="cli",
        description=(
            "Generate the standard container view and serve the same generated "
            "HTML over local HTTP."
        ),
        depends_on=None,
        arguments=[
            {
                "accepts": ["server"],
                "description": (
                    "Generate the container's standard view, start the HTTP "
                    "server, then open its index.html in the browser."
                ),
                "usage": (
                    "ontobdc server --container <id-or-path> "
                    "[--host <host>] [--port <port>]"
                ),
            },
            {
                "accepts": ["--container-id", "--container"],
                "valued": True,
                "description": (
                    "Required. Select the registered container to serve by "
                    "id, or use --container with either an id or a "
                    "filesystem path."
                ),
                "usage": "ontobdc server --container <id-or-path>",
            },
            {
                "accepts": ["--host"],
                "valued": True,
                "description": "Interface to bind (default: 127.0.0.1).",
                "usage": "ontobdc server --host 0.0.0.0",
            },
            {
                "accepts": ["--port"],
                "valued": True,
                "description": (
                    "Port to bind. When omitted, the Surface launcher state "
                    "generates and persists a random high port."
                ),
                "usage": "ontobdc server --port 8080",
            },
        ],
    )

    _VALUED_FLAGS = {"--container-id", "--container", "--host", "--port"}
    _DEFAULT_HOST: str = DEFAULT_SERVER_HOST
    _DEFAULT_PORT: int = DEFAULT_SERVER_PORT

    def __init__(self, request: CliCommandRequest):
        self._request: CliCommandRequest = request
        self._logger: LogRepositoryPort = NullLogRepository()
        self._log_strategy: Any = None

    @property
    def log_strategy(self) -> Any:
        return self._log_strategy

    @staticmethod
    def accepts(args: List[str]) -> bool:
        if not args or args[0] != "server":
            return False

        remaining: List[str] = args[1:]
        index: int = 0
        seen: set = set()
        while index < len(remaining):
            flag: str = remaining[index]
            if flag not in CliServerCommand._VALUED_FLAGS or flag in seen:
                return False
            if (
                index + 1 >= len(remaining)
                or remaining[index + 1].startswith("--")
            ):
                return False
            seen.add(flag)
            index += 2

        return not ({"--container-id", "--container"} <= seen)

    def set_log_strategy(self, log_strategy: LogStrategyConfig) -> None:
        self._log_strategy = log_strategy
        self._logger = log_strategy.log_repository

    def check(self) -> bool:
        args: List[str] = list(self._request.command_args)
        if not args or args[0] != "server":
            return False

        context = self._request.context

        # A per-project context.ttl can carry stale invocation values. The
        # command selector and the launcher state are authoritative for this
        # run, so do not let an old server reference leak into it.
        if getattr(context, "delete_parameter", None) is not None:
            for stale in (
                "container_id",
                "container",
                "container_path",
                "surface_path",
                "server_host",
                "server_port",
                "server_bind_host",
                "server_bind_port",
            ):
                context.delete_parameter(stale)

        explicit_id: Optional[str] = self._argument_value("--container-id")
        selector: Optional[str] = self._argument_value("--container")
        if explicit_id is None and selector is None:
            raise ValueError(
                "ontobdc server requires an explicit container: pass "
                "--container <id-or-path> or --container-id <id>."
            )
        if explicit_id is not None:
            context.set_parameter_value("container_id", explicit_id)
        else:
            context.set_parameter_value("container", selector)
        ContainerIdStrategy().execute(context)

        container_id: str = str(
            context.get_parameter_value("container_id") or ""
        ).strip()
        container_path_value: str = str(
            context.get_parameter_value("container_path") or ""
        ).strip()
        if not container_id or not container_path_value:
            raise ValueError(
                "No registered container matches "
                f"'{explicit_id or selector}'. Run 'ontobdc storage --list' "
                "to see the registered containers."
            )
        container_path: Path = (
            Path(container_path_value).expanduser().resolve()
        )
        if not container_path.is_dir():
            raise ValueError(
                "The registered container path does not exist: "
                f"{container_path}."
            )

        host: str = self._argument_value("--host") or self._DEFAULT_HOST
        raw_port: Optional[str] = self._argument_value("--port")
        explicit_port: Optional[int] = None
        if raw_port is not None:
            try:
                explicit_port = int(raw_port)
            except ValueError:
                raise ValueError(
                    f"--port must be an integer, got '{raw_port}'."
                )
            if not 1 <= explicit_port <= 65535:
                raise ValueError(
                    f"--port must be between 1 and 65535, got {explicit_port}."
                )

        context.set_parameter_value("container_path", str(container_path))
        context.set_parameter_value("server_bind_host", host)
        context.set_parameter_value("server_host", host)
        if explicit_port is not None:
            context.set_parameter_value("server_bind_port", explicit_port)
            context.set_parameter_value("server_port", explicit_port)
        return True

    def run(self) -> CommandResponse:
        context = self._request.context

        # Run exactly the same Surface-generation process as ``ontobdc view``.
        # Remove every generated presentation artefact first so this invocation
        # can never reuse stale entity HTML from a previous generation.
        existing_surface_path = SurfaceContextAdapter().surface_path(context)
        if existing_surface_path.is_file():
            remove_file(existing_surface_path)

        existing_file_viewer_path = (
            existing_surface_path.parent / "onto-file-viewer.html"
        )
        if existing_file_viewer_path.is_file():
            remove_file(existing_file_viewer_path)
        legacy_marker_viewer_path = (
            existing_surface_path.parent
            / ".__ontobdc__"
            / "onto-file-viewer.html"
        )
        if legacy_marker_viewer_path.is_file():
            remove_file(legacy_marker_viewer_path)

        generated_views_directory = (
            existing_surface_path.parent / ".__ontobdc__" / "view"
        )
        if generated_views_directory.is_dir():
            remove_directory_tree(generated_views_directory)

        etl_state_directory = DataGatheredCapability.state_directory(context)
        if etl_state_directory.is_dir():
            remove_directory_tree(etl_state_directory)

        # The final SERVER_LAUNCHER_GENERATED state owns the generated
        # host/port reference. If --port was omitted it chooses a random high
        # port, writes it to server.cmd and every generated HTML, and leaves
        # the chosen value on the shared context for this command to bind.
        response: CommandResponse = SurfaceGenerationStateTransitionHandler(
            context=context,
        ).execute()

        directory: Path = Path(
            str(context.get_parameter_value("container_path"))
        ).resolve()
        index_path: Path = directory / "index.html"
        if not index_path.is_file():
            raise FileNotFoundError(
                f"The container at '{directory}' has no index.html even "
                "after standard view generation."
            )

        generated_host: str = str(
            context.get_parameter_value("server_host") or self._DEFAULT_HOST
        )
        bind_host: str = str(
            context.get_parameter_value("server_bind_host") or generated_host
        )
        explicit_bind_port = context.get_parameter_value("server_bind_port")
        generated_port_value = context.get_parameter_value("server_port")
        bind_port: int = int(
            explicit_bind_port
            if explicit_bind_port is not None
            else (
                generated_port_value
                if generated_port_value is not None
                else self._DEFAULT_PORT
            )
        )

        handler_class: Any = partial(
            SimpleHTTPRequestHandler,
            directory=str(directory),
        )
        try:
            http_server: ThreadingHTTPServer = ThreadingHTTPServer(
                (bind_host, bind_port), handler_class
            )
        except OSError as error:
            raise RuntimeError(
                f"Cannot bind {bind_host}:{bind_port} "
                f"({error.strerror or error})."
            ) from error

        bound_host, bound_port = http_server.server_address[:2]
        display_host: str = (
            generated_host
            if str(bound_host) in ("0.0.0.0", "::")
            else str(bound_host)
        )
        query = urlencode(
            {
                "host": display_host,
                "port": int(bound_port),
            }
        )
        url: str = f"http://{display_host}:{int(bound_port)}/?{query}"

        print(f"serving {directory}", flush=True)
        print(f"        {url}   (Ctrl+C to stop)", flush=True)

        # The server must be listening before the browser is opened.
        server_thread: threading.Thread = threading.Thread(
            target=http_server.serve_forever,
            name="ontobdc-server",
            daemon=True,
        )
        server_thread.start()

        browser_opened = False
        runtime_error: Optional[str] = None
        try:
            browser_opened = bool(webbrowser.open(url, new=2))
            if not browser_opened:
                runtime_error = (
                    "The standard view was generated and the HTTP server "
                    f"started, but the default browser did not open {url}."
                )
        except Exception as error:
            runtime_error = str(error)

        try:
            while server_thread.is_alive():
                server_thread.join(0.5)
        except KeyboardInterrupt:
            pass
        finally:
            http_server.shutdown()
            http_server.server_close()

        content: Dict[str, Any] = dict(response.content)
        content.update(
            {
                "directory": str(directory),
                "host": display_host,
                "bind_host": str(bound_host),
                "port": int(bound_port),
                "url": url,
                "browser_opened": browser_opened,
                "runtime_error": runtime_error,
                "stopped": True,
            }
        )
        response.title = "Server"
        response.content = content
        response.description = f"Stopped serving {directory}."
        return response

    def _argument_value(self, flag: str) -> Optional[str]:
        arguments: List[str] = list(self._request.command_args)
        if flag not in arguments:
            return None
        index: int = arguments.index(flag) + 1
        if index >= len(arguments):
            return None
        value: str = str(arguments[index] or "").strip()
        return value or None
