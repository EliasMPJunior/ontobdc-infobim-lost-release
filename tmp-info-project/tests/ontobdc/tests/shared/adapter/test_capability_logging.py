from io import StringIO
from typing import Callable, Optional

from ontobdc.cli.adapter.logger import InLineLogger
from ontobdc.cli.domain.model.logger import LogLevel
from ontobdc.shared.adapter.capability import CapabilityLoggingSupport


def test_capability_emitters_preserve_notice_threshold() -> None:
    stream: StringIO = StringIO()
    logger: InLineLogger = InLineLogger(
        stream=stream,
        log_level=LogLevel.NOTICE,
    )

    debug_emitter: Optional[Callable[[str], None]] = (
        CapabilityLoggingSupport._extract_debug_logger(logger)
    )
    info_emitter: Optional[Callable[[str], None]] = (
        CapabilityLoggingSupport._extract_info_logger(logger)
    )

    assert debug_emitter is not None
    assert info_emitter is not None
    debug_emitter("Hidden debug")
    info_emitter("Hidden info")
    assert stream.getvalue() == ""
    assert logger.log_level is LogLevel.NOTICE


def test_capability_emitters_preserve_info_threshold() -> None:
    stream: StringIO = StringIO()
    logger: InLineLogger = InLineLogger(
        stream=stream,
        log_level=LogLevel.INFORMATIONAL,
    )

    debug_emitter: Optional[Callable[[str], None]] = (
        CapabilityLoggingSupport._extract_debug_logger(logger)
    )
    info_emitter: Optional[Callable[[str], None]] = (
        CapabilityLoggingSupport._extract_info_logger(logger)
    )

    assert debug_emitter is not None
    assert info_emitter is not None
    debug_emitter("Hidden debug")
    info_emitter("Visible info")
    output: str = stream.getvalue()
    assert "Hidden debug" not in output
    assert "Visible info" in output
    assert logger.log_level is LogLevel.INFORMATIONAL


def test_capability_emitters_preserve_debug_threshold() -> None:
    stream: StringIO = StringIO()
    logger: InLineLogger = InLineLogger(
        stream=stream,
        log_level=LogLevel.DEBUG,
    )

    debug_emitter: Optional[Callable[[str], None]] = (
        CapabilityLoggingSupport._extract_debug_logger(logger)
    )
    info_emitter: Optional[Callable[[str], None]] = (
        CapabilityLoggingSupport._extract_info_logger(logger)
    )

    assert debug_emitter is not None
    assert info_emitter is not None
    debug_emitter("Visible debug")
    info_emitter("Visible info")
    output: str = stream.getvalue()
    assert "Visible debug" in output
    assert "Visible info" in output
    assert logger.log_level is LogLevel.DEBUG
