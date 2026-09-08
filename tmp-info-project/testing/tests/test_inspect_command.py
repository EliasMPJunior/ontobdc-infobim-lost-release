from types import SimpleNamespace
from typing import Any

from ontobdc.cli.domain.response.command import CommandResponse

from ontobdc_dev.inspect.plugin.command import base
from ontobdc_dev.inspect.plugin.command.base import DevInspectCommand


class TestDevInspectCommand:
    def test_accepts_only_bare_inspect(self) -> None:
        assert DevInspectCommand.accepts(["dev", "inspect"])
        assert not DevInspectCommand.accepts(
            ["dev", "inspect", "--free-functions"]
        )

    def test_consolidates_only_free_function_statistics(
        self,
        monkeypatch: Any,
    ) -> None:
        detailed_response: CommandResponse = CommandResponse(
            title="Architecture Free Functions",
            description="Detailed findings.",
            content={
                "count": 3,
                "path": "/installed/ontobdc",
                "functions": [
                    {
                        "file": "/installed/ontobdc/cli/first.py",
                        "name": "first",
                    },
                    {
                        "file": "/installed/ontobdc/cli/second.py",
                        "name": "second",
                    },
                    {
                        "file": "/installed/ontobdc/storage/third.py",
                        "name": "third",
                    },
                ],
            },
        )

        class DetailedCommandStub:
            def __init__(self, request: Any) -> None:
                self.request: Any = request

            def run(self) -> CommandResponse:
                return detailed_response

        monkeypatch.setattr(
            base,
            "DevArchitectureFreeFunctionsCommand",
            DetailedCommandStub,
        )
        request: Any = SimpleNamespace(command_args=["inspect"])

        response: CommandResponse = DevInspectCommand(request).run()

        assert response.content == {
            "free": {
                "cli": 2,
                "storage": 1,
            }
        }

    def test_groups_root_package_files_as_ontobdc(self) -> None:
        response: CommandResponse = CommandResponse(
            title="Architecture Free Functions",
            description="Detailed findings.",
            content={
                "count": 1,
                "path": "/installed/ontobdc",
                "functions": [
                    {
                        "file": "/installed/ontobdc/__init__.py",
                        "name": "main",
                    },
                ],
            },
        )

        statistics = DevInspectCommand._free_statistics(response)

        assert statistics == {"ontobdc": 1}
