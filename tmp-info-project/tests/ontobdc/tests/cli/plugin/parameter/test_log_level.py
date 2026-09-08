from unittest.mock import Mock

import pytest

from ontobdc.cli.adapter.logger import InLineLogger
from ontobdc.cli.domain.model.logger import LogLevel, LogStrategyConfig
from ontobdc.cli.domain.port.context import CliContextPort
from ontobdc.cli.plugin.parameter.log_level import LogLevelStrategy


def _strategy(args: list[str]) -> tuple[LogLevelStrategy, InLineLogger]:
    logger = InLineLogger()
    strategy = LogLevelStrategy()
    strategy.set_log_strategy(LogStrategyConfig(log_repository=logger))
    context = Mock(spec=CliContextPort)
    context.raw_args = args
    context.get_parameter_value.return_value = None
    strategy.execute(context)
    return strategy, logger


def test_log_level_strategy_injects_debug_for_one_execution() -> None:
    strategy, logger = _strategy(["--log-level", "DEBUG", "--version"])

    assert logger.log_level is LogLevel.DEBUG
    assert strategy.log_strategy is not None
    assert strategy.log_strategy.log_level is LogLevel.DEBUG
    assert strategy.remaining_args == ["--version"]


def test_log_level_strategy_keeps_default_when_option_is_absent() -> None:
    strategy, logger = _strategy(["--version"])

    assert logger.log_level is LogLevel.NOTICE
    assert strategy.remaining_args == ["--version"]


@pytest.mark.parametrize(
    "args",
    [
        ["--log-level"],
        ["--log-level", "INVALID", "--version"],
        ["--log-level", "DEBUG", "--log-level", "ERROR", "--version"],
    ],
)
def test_log_level_strategy_rejects_invalid_input(args: list[str]) -> None:
    with pytest.raises(ValueError):
        _strategy(args)


def test_log_level_strategy_accepts_case_insensitive_level_and_equals_form() -> None:
    strategy, logger = _strategy(["--version", "--log-level=debug"])

    assert logger.log_level is LogLevel.DEBUG
    assert strategy.remaining_args == ["--version"]


@pytest.mark.parametrize(
    "args",
    [
        ["--log-level", "reset", "--version"],
        ["--version", "--log-level=RESET"],
    ],
)
def test_log_level_strategy_resets_to_default(args: list[str]) -> None:
    strategy, logger = _strategy(args)

    assert logger.log_level is LogLevel.NOTICE
    assert strategy.log_strategy is not None
    assert strategy.log_strategy.log_level is LogLevel.NOTICE
    assert strategy.remaining_args == ["--version"]
