
import webbrowser
from pathlib import Path
from typing import Any, Dict, List, Optional
from ontobdc.cli.domain.exception.command import CliCommandArgumentException
from ontobdc.cli.domain.port.command import CliCommandPort
from ontobdc.cli.domain.response.command import CommandResponse
from ontobdc.cli.domain.model.command import CliCommandMetadata
from ontobdc.cli.domain.request.command import CliCommandRequest
from ontobdc.storage.plugin.parameter.container import ContainerIdStrategy
from ontobdc_view.surface.adapter.machine import SurfaceGenerationStateTransitionHandler


class ContainerViewCommand(CliCommandPort):
    """Generate and open a portable view for an OntoBDC container."""

    METADATA = CliCommandMetadata(
        id="view_generate",
        logical_component="view",
        description=(
            "Generate a standalone container view at index.html and open it."
        ),
        arguments=[
            {
                "accepts": ["--container-id", "--container"],
                "valued": True,
                "description": (
                    "Select a registered container by ID, or use --container "
                    "with either an ID or filesystem path."
                ),
                "usage": (
                    "ontobdc view [--container <id-or-path>] [options]"
                ),
            },
            {
                "accepts": ["--type"],
                "valued": True,
                "description": (
                    "Select the view type. The supported value is standard."
                ),
                "usage": "ontobdc view --type standard",
            },
            {
                "accepts": ["--representation"],
                "valued": True,
                "description": (
                    "Select the representation. The supported value is html."
                ),
                "usage": "ontobdc view --representation html",
            },
            {
                "accepts": ["--language"],
                "valued": True,
                "description": "Select the language declared by the view.",
                "usage": "ontobdc view --language pt-br",
            },
        ],
    )

    _VALUED_FLAGS = {
        "--container-id",
        "--container",
        "--type",
        "--representation",
        "--language",
    }

    @staticmethod
    def accepts(args: List[str]) -> bool:
        if not args or args[0] != "view":
            return False

        remaining = args[1:]
        index = 0
        seen = set()
        while index < len(remaining):
            flag = remaining[index]
            if flag not in ContainerViewCommand._VALUED_FLAGS:
                return False
            if flag in seen:
                return False
            if (
                index + 1 >= len(remaining)
                or remaining[index + 1].startswith("--")
            ):
                return False
            seen.add(flag)
            index += 2

        return not ({"--container-id", "--container"} <= seen)

    def __init__(self, request: CliCommandRequest):
        self._request = request

    def check(self) -> bool:
        context = self._request.context
        # The per-project root ``.__ontobdc__/context.ttl`` may carry a stale
        # ``container_path`` left by a different container (or a previous
        # invocation of the view command against a sibling container).  The
        # ContainerIdStrategy is only authoritative for the *current* CWD, so
        # drop any inherited value before we let it decide which container
        # the run actually targets -- otherwise ``context.ttl`` wins and the
        # command silently opens a sibling's view (e.g. ``data/``) instead of
        # the directory the user actually ``cd``'d into.
        if getattr(context, "delete_parameter", None) is not None:
            context.delete_parameter("container_id")
            context.delete_parameter("container_path")
        ContainerIdStrategy().execute(context)
        container_path = self._resolved_container_path()
        if container_path is None or not container_path.is_dir():
            raise CliCommandArgumentException(
                "Could not resolve a container. Run 'ontobdc view' inside a "
                "registered container, or pass --container <id-or-path>."
            )

        representation = (
            self._argument_value("--representation") or "html"
        ).lower()
        if representation != "html":
            raise ValueError(
                "The ontobdc view command currently supports "
                "--representation html only."
            )

        view_type = (
            self._argument_value("--type") or "standard"
        ).lower()
        if view_type != "standard":
            raise ValueError(
                "The ontobdc view command currently supports "
                "--type standard only."
            )

        language = (
            self._argument_value("--language") or "en"
        ).lower()

        context.set_parameter_value("container_path", str(container_path))
        context.set_parameter_value("view_type", view_type)
        context.set_parameter_value("representation", representation)
        context.set_parameter_value("language", language)
        return True

    def run(self) -> CommandResponse:
        context = self._request.context

        # Removing a stale prior run's HTML artifacts (index.html, the
        # standalone file viewer, published entity pages) is now the
        # VIEW_ARTIFACTS_CLEANED state's own job, run by the state machine
        # right before SURFACE_INITIALIZED -- see
        # ViewArtifactsCleanedCapability. The command no longer does this
        # itself.
        handler = SurfaceGenerationStateTransitionHandler(
            context=context,
        )
        response = handler.execute()

        index_path = (
            Path(
                str(
                    context.get_parameter_value(
                        "container_path"
                    )
                    or ""
                )
            )
            .expanduser()
            .resolve()
            / "index.html"
        )
        if not index_path.is_file():
            raise FileNotFoundError(
                "The Surface generation process finished without generating "
                f"{index_path}."
            )

        index_uri = index_path.as_uri()
        browser_opened = False
        runtime_error: Optional[str] = None
        try:
            browser_opened = bool(webbrowser.open(index_uri, new=2))
            if not browser_opened:
                runtime_error = (
                    "The Surface was generated, but the default browser did "
                    f"not open {index_uri}."
                )
        except Exception as error:
            runtime_error = str(error)

        content: Dict[str, Any]
        if isinstance(response.content, dict):
            content = response.content
        else:
            content = {"result": response.content}
            response.content = content

        content.update(
            {
                "container_id": (
                    context.get_parameter_value(
                        "container_id"
                    )
                ),
                "view_type": (
                    context.get_parameter_value("view_type")
                ),
                "representation": (
                    context.get_parameter_value(
                        "representation"
                    )
                ),
                "language": (
                    context.get_parameter_value("language")
                ),
                "index_path": str(index_path),
                "index_uri": index_uri,
                "browser_opened": browser_opened,
                "runtime_error": runtime_error,
            }
        )
        return response

    def _resolved_container_path(self) -> Optional[Path]:
        value = self._request.context.get_parameter_value("container_path")
        normalized = str(value or "").strip()
        if not normalized:
            return None
        try:
            return Path(normalized).expanduser().resolve()
        except (OSError, RuntimeError, TypeError, ValueError):
            return None

    def _argument_value(self, flag: str) -> Optional[str]:
        arguments = list(self._request.command_args)
        if flag not in arguments:
            return None
        index = arguments.index(flag) + 1
        if index >= len(arguments):
            return None
        normalized = str(arguments[index] or "").strip()
        return normalized or None
