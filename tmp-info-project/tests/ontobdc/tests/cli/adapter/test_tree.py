"""``CommandTreeAdapter`` renders the ``├──``/``└──`` command tree shown
by ``ontobdc`` / ``infobim`` with no arguments.

These pin the two hooks a downstream CLI (ontobdc-dev) needs to get the
same tree without following ontobdc's ``<component>/plugin/command``
discovery convention: an explicit ``command_classes`` list, and
``executable_aliases`` for usage strings authored against an older
executable name.
"""
import re

from ontobdc.cli.adapter.tree import CommandTreeAdapter
from ontobdc.cli.domain.model.command import CliCommandMetadata
from ontobdc.cli.domain.port.command import CliCommandPort

_ANSI = re.compile(r"\x1b\[[0-9;]*m")


def _plain(text: str) -> str:
    return _ANSI.sub("", text)


class _StubCommand(CliCommandPort):
    @staticmethod
    def accepts(args):  # pragma: no cover - not exercised
        return False

    def check(self) -> bool:  # pragma: no cover - not exercised
        return True

    def run(self):  # pragma: no cover - not exercised
        return None


def _command(command_id: str, accepts, usage: str) -> type:
    metadata = CliCommandMetadata(
        id=command_id,
        logical_component="tool",
        description=f"{command_id} command",
        arguments=[{"accepts": accepts, "description": "", "usage": usage}],
    )
    return type(f"Cmd_{command_id}", (_StubCommand,), {"METADATA": metadata})


def test_explicit_command_classes_replace_filesystem_discovery() -> None:
    adapter = CommandTreeAdapter(
        executable="tool",
        command_classes=[
            (
                "build",
                _command("build", ["--target"], "tool build --target <name>"),
            ),
            (
                "build",
                _command(
                    "build-watch", ["--watch"], "tool build --watch"
                ),
            ),
            ("ship", _command("ship", ["--now"], "tool ship --now")),
        ],
    )

    tree = _plain(adapter.render())

    assert tree.startswith("tool\n")
    assert "├── build" in tree
    assert "│   ├── --target" in tree
    assert "│   └── --watch" in tree
    assert "└── ship" in tree
    assert "    └── --now" in tree


def test_executable_aliases_are_stripped_from_usage() -> None:
    adapter = CommandTreeAdapter(
        executable="tool-dev",
        executable_aliases=("tool dev",),
        command_classes=[
            (
                "branch",
                _command(
                    "branch-changelog",
                    ["--changelog"],
                    "tool dev branch --changelog [ref]",
                ),
            ),
        ],
    )

    tree = _plain(adapter.render())

    assert tree.startswith("tool-dev\n")
    assert "└── branch" in tree
    assert "    └── --changelog" in tree
    assert "tool dev" not in tree


def test_excluded_ids_still_apply_to_explicit_classes() -> None:
    adapter = CommandTreeAdapter(
        executable="tool",
        excluded_command_ids=("base",),
        command_classes=[
            ("tool", _command("base", ["--help"], "tool --help")),
            ("ship", _command("ship", ["--now"], "tool ship --now")),
        ],
    )

    tree = _plain(adapter.render())

    assert "--help" not in tree
    assert "ship" in tree


def test_explicit_classes_render_is_deterministic() -> None:
    pairs = [
        ("ship", _command("ship", ["--now"], "tool ship --now")),
    ]
    first = CommandTreeAdapter(executable="tool", command_classes=pairs)
    second = CommandTreeAdapter(executable="tool", command_classes=list(pairs))
    assert _plain(first.render()) == _plain(second.render())
