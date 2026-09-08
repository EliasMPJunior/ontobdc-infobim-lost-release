from __future__ import annotations

from _pytest.config.argparsing import Parser


def pytest_addoption(parser: Parser) -> None:
    parser.addoption(
        "--theme",
        action="store",
        choices=("light", "dark"),
        default="light",
        help="Theme used by standalone Tile browser tests.",
    )
