
from pathlib import Path
from typing import Any, Dict, List, Optional, Type

from ontobdc.cli.domain.port.command import CliCommandPort
from ontobdc.cli.domain.response.command import CommandResponse
from ontobdc.cli.domain.model.command import CliCommandMetadata
from ontobdc.cli.domain.request.command import CliCommandRequest
from ontobdc.context.plugin.parameter.element import ElementIdStrategy
from ontobdc.storage.plugin.parameter.container import ContainerIdStrategy
from ontobdc_view.page.domain.machine.loader import (
    EntityPageGenerationDataTransitionHandlerLoader,
)
from ontobdc_view.page.domain.port.machine import (
    EntityPageGenerationDataTransitionHandlerPort,
)


class EntityPageViewCommand(CliCommandPort):
    """Generate and open a portable view for an OntoBDC container."""

    METADATA = CliCommandMetadata(
        id="entity_page_generate",
        logical_component="view",
        description=(
            "Generate a standalone container view at index.html and open it."
        ),
        arguments=[
            {
                "accepts": [
                    "--container-id",
                    "--container-path",
                    "--container",
                ],
                "valued": True,
                "description": (
                    "Select a registered container by ID, use "
                    "--container-path with a filesystem path, or use "
                    "--container with either selector."
                ),
                "usage": (
                    "ontobdc view [--container-id <id> | "
                    "--container-path <path> | "
                    "--container <id-or-path>] [options]"
                ),
            },
            {
                "accepts": ["--element"],
                "valued": True,
                "description": (
                    "Select one element by its identifier (the GLOBAL ID "
                    "shown by the bare --element list) and show its tree."
                ),
                "usage": "ontobdc view --element <element_id>",
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
            {
                "accepts": ["--theme"],
                "valued": True,
                "description": "Select the theme supported by the view.",
                "usage": "ontobdc view --language dark",
            },
        ],
    )

    @staticmethod
    def accepts(args: List[str]) -> bool:
        if not args or args[0] != "view":
            return False

        if '--element' not in args:
            return False

        return True

    def __init__(self, request: CliCommandRequest):
        self._request = request

    def check(self) -> bool:
        context = self._request.context

        ContainerIdStrategy().execute(context)
        ElementIdStrategy().execute(context)

        representation = (
            self._argument_value("--representation") or "html"
        ).lower()
        if representation != "html":
            raise ValueError(
                "The ontobdc view command currently supports "
                "--representation html only."
            )

        theme = (
            self._argument_value("--theme") or "light"
        ).lower()

        language = (
            self._argument_value("--language") or "en"
        ).lower()

        context.set_parameter_value("theme", theme)
        context.set_parameter_value("representation", representation)
        context.set_parameter_value("language", language)

        return True

    def run(self) -> CommandResponse:
        context = self._request.context

        entity_uri: str = str(
            context.get_parameter_value("entity_uri") or ""
        ).strip()
        if not entity_uri:
            raise ValueError(
                "Element resolution did not provide an entity URI."
            )

        loader: EntityPageGenerationDataTransitionHandlerLoader = (
            EntityPageGenerationDataTransitionHandlerLoader()
        )

        handler_type: Type[
            EntityPageGenerationDataTransitionHandlerPort
        ] = loader.get(entity_uri)

        handler: EntityPageGenerationDataTransitionHandlerPort = (
            handler_type(context=context)
        )

        response = handler.execute()

        return response

    def _argument_value(self, flag: str) -> Optional[str]:
        arguments = list(self._request.command_args)
        if flag not in arguments:
            return None
        index = arguments.index(flag) + 1
        if index >= len(arguments):
            return None
        normalized = str(arguments[index] or "").strip()
        return normalized or None
