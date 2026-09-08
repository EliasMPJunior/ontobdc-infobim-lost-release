import sys
from typing import Any, Dict, List, Optional, Sequence

from ontobdc.cli import (
    CliGlobalArgumentParser,
    CliParameterValidationOrchestrator,
    CommandResponseRenderer,
)
from ontobdc.cli.adapter.command import CliCommandRunAdapter
from ontobdc.cli.adapter.logger import InLineLogger, NullLogRepository
from ontobdc.cli.adapter.terminal import prompt_choice
from ontobdc.cli.domain.model.logger import LogLevel, LogStrategyConfig
from ontobdc.cli.domain.port.command import CliCommandPort
from ontobdc.cli.domain.port.context import CliContextPort, PromptChoiceAwarePort
from ontobdc.cli.domain.port.logger import LoggerAwarePort, LogRepositoryPort
from ontobdc.cli.domain.response.command import (
    CommandResponse,
    ExceptionCommandResponse,
    InteractiveCommandResponse,
)
from ontobdc.shared.adapter.loader import ParameterLoader
from ontobdc.shared.facade.adapter.logger import ActiveLogRepositoryBroker
from ontobdc_view.cli.adapter.loader import ViewCommandLoader


class OntoBDCViewCli:
    """Run ontobdc-view commands through OntoBDC's shared CLI pipeline."""

    def __init__(self) -> None:
        self._global_arguments: CliGlobalArgumentParser = CliGlobalArgumentParser()
        self._parameter_validator: CliParameterValidationOrchestrator = (
            CliParameterValidationOrchestrator()
        )
        self._response_renderer: CommandResponseRenderer = CommandResponseRenderer()

    def run(self, argv: Optional[Sequence[str]] = None) -> int:
        raw_args: List[str] = list(sys.argv[1:] if argv is None else argv)
        render_type: str = self._render_type(raw_args)
        silent: bool = self._is_silent(raw_args)
        logger: LogRepositoryPort = (
            NullLogRepository() if render_type == "json" else InLineLogger()
        )

        try:
            incoming_args: List[str] = self._global_arguments.strip_output_flags(
                raw_args
            )
            resolved_log_level: Optional[LogLevel]
            sanitized_args: List[str]
            resolved_log_level, sanitized_args = (
                self._global_arguments.consume_log_level(incoming_args)
            )
            command_args: List[str] = self._normalize_command_args(
                sanitized_args
            )

            if resolved_log_level is not None:
                LogStrategyConfig(
                    log_level=resolved_log_level,
                    log_repository=logger,
                )

            ActiveLogRepositoryBroker.instance().set(logger)

            command: CliCommandPort = CliCommandRunAdapter.make(
                command_args,
                logger,
                loader_class=ViewCommandLoader,
                defer_check=True,
            )

            if resolved_log_level is not None:
                request: Optional[Any] = getattr(command, "_request", None)
                context: Optional[CliContextPort] = getattr(
                    request,
                    "context",
                    None,
                )
                if context is not None:
                    context.set_parameter_value(
                        "log_level",
                        resolved_log_level,
                    )

            parameter_loader: ParameterLoader = ParameterLoader(
                logger=logger,
                root_packages=("ontobdc", "ontobdc_view"),
            )
            self._parameter_validator.check(
                command,
                command_args,
                logger,
                parameter_loader,
            )

            if isinstance(command, LoggerAwarePort):
                log_strategy_kwargs: Dict[str, Any] = {
                    "log_repository": logger,
                }
                if resolved_log_level is not None:
                    log_strategy_kwargs["log_level"] = resolved_log_level
                command.set_log_strategy(
                    LogStrategyConfig(**log_strategy_kwargs)
                )

            if isinstance(command, PromptChoiceAwarePort):
                command.set_prompt_choice(prompt_choice)

            response: CommandResponse = command.run()
            if not silent and not isinstance(
                response,
                InteractiveCommandResponse,
            ):
                self._response_renderer.render(
                    response,
                    logger,
                    render_type,
                )
            return 0
        except Exception as error:
            response: CommandResponse = ExceptionCommandResponse(
                title="View",
                description="View command execution failed.",
                content={"error": str(error)},
            )
            if not silent:
                self._response_renderer.render(
                    response,
                    logger,
                    render_type,
                )
            return 1
        finally:
            ActiveLogRepositoryBroker.instance().clear()

    @staticmethod
    def _normalize_command_args(args: List[str]) -> List[str]:
        if args and args[0] == "view":
            return list(args)
        return ["view", *args]

    @staticmethod
    def _render_type(args: List[str]) -> str:
        if "--json" in args:
            return "json"
        if "--html" in args:
            return "html"
        return "rich"

    @staticmethod
    def _is_silent(args: List[str]) -> bool:
        return "--silent" in args or "-s" in args


def main(argv: Optional[Sequence[str]] = None) -> int:
    return OntoBDCViewCli().run(argv)
