from datetime import datetime
from io import StringIO

import pytest

from ontobdc.cli.adapter.logger import InLineLogger, StandardConsoleLogger
from ontobdc.cli.domain.model.logger import (
    LogLevel,
    LogLevelPolicy,
    LogStrategyConfig,
)


@pytest.mark.parametrize(
    ("level", "expected_style"),
    [
        (LogLevel.INFORMATIONAL, "\033[34m▶ INFO\033[0m"),
        (LogLevel.WARNING, "\033[33m⚠️  WARNING\033[0m"),
        (LogLevel.ERROR, "\033[31m❌ ERROR\033[0m"),
        (LogLevel.DEBUG, "\033[36m▶ DEBUG\033[0m"),
        (LogLevel.NOTICE, "\033[36m▶ NOTICE\033[0m"),
        (LogLevel.SUCCESS, "\033[32m✔ SUCCESS\033[0m"),
        (LogLevel.CRITICAL, "\033[37m• CRITICAL\033[0m"),
    ],
)
def test_inline_logger_preserves_level_styles(
    level: LogLevel,
    expected_style: str,
) -> None:
    stream = StringIO()
    logger = InLineLogger(
        stream=stream,
        clock=lambda: datetime(2026, 8, 15, 18, 55, 5),
        log_level=LogLevel.DEBUG,
    )

    logger.log(level, "Message")

    assert stream.getvalue() == (
        "\033[90m[18:55:05]\033[0m "
        f"{expected_style} "
        "\033[37mMessage\033[0m\n"
    )


def test_inline_logger_formats_arguments_in_one_line() -> None:
    stream = StringIO()
    logger = InLineLogger(
        stream=stream,
        clock=lambda: datetime(2026, 8, 15, 18, 55, 5),
    )

    logger.log_warning("Example warning", "container=demo", "step 3")

    assert stream.getvalue() == (
        "\033[90m[18:55:05]\033[0m "
        "\033[33m⚠️  WARNING\033[0m "
        "\033[37mExample warning\033[0m "
        "\033[34mcontainer\033[0m=\033[90mdemo\033[0m "
        "\033[90mstep 3\033[0m\n"
    )
    assert stream.getvalue().count("\n") == 1


class _FlushTrackingStream(StringIO):
    def __init__(self) -> None:
        super().__init__()
        self.flushed = False

    def flush(self) -> None:
        self.flushed = True
        super().flush()


def test_inline_logger_flushes_each_complete_line() -> None:
    stream = _FlushTrackingStream()
    logger = InLineLogger(
        stream=stream,
        clock=lambda: datetime(2026, 8, 15, 18, 55, 5),
    )

    logger.log_notice("Ready")

    assert stream.flushed is True


def test_default_notice_threshold_suppresses_info_and_debug() -> None:
    assert LogLevelPolicy.DEFAULT is LogLevel.NOTICE

    stream = StringIO()
    logger = InLineLogger(
        stream=stream,
        clock=lambda: datetime(2026, 8, 15, 18, 55, 5),
    )

    logger.log_debug("Hidden")
    logger.log_info("Also hidden")
    logger.log_notice("Visible")

    assert "Hidden" not in stream.getvalue()
    assert "Also hidden" not in stream.getvalue()
    assert "Visible" in stream.getvalue()


def test_success_is_distinct_but_notice_equivalent_for_filtering() -> None:
    assert LogLevel.SUCCESS.value == "SUCCESS"
    assert LogLevelPolicy.priority(LogLevel.SUCCESS) == LogLevelPolicy.priority(
        LogLevel.NOTICE
    )

    stream = StringIO()
    logger = InLineLogger(
        stream=stream,
        clock=lambda: datetime(2026, 8, 15, 18, 55, 5),
        log_level=LogLevel.NOTICE,
    )

    logger.log_success("Saved")
    logger.log_info("Hidden")

    assert "✔ SUCCESS" in stream.getvalue()
    assert "Saved" in stream.getvalue()
    assert "Hidden" not in stream.getvalue()


def test_log_strategy_config_applies_threshold_to_repository() -> None:
    stream = StringIO()
    logger = InLineLogger(
        stream=stream,
        clock=lambda: datetime(2026, 8, 15, 18, 55, 5),
    )
    LogStrategyConfig(
        log_level=LogLevel.ERROR,
        log_repository=logger,
    )

    logger.log_warning("Hidden")
    logger.log_error("Visible")

    assert "Hidden" not in stream.getvalue()
    assert "Visible" in stream.getvalue()


def test_standard_console_logger_applies_threshold(capsys) -> None:
    logger = StandardConsoleLogger(log_level=LogLevel.WARNING)

    logger.log_notice("Hidden")
    logger.log_warning("Visible")

    captured = capsys.readouterr()
    assert "Hidden" not in captured.out
    assert "[WARNING] Visible" in captured.out
