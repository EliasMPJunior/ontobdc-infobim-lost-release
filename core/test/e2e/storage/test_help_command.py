from typing import Any, Dict

from test.e2e.cli_process_runner import CliInvocationResult, OntobdcCliProcessRunner


class TestOntobdcStorageHelpCommand:
    """
    E2E coverage for `ontobdc storage --help --json` / `ontobdc storage -h --json`.
    """

    def test_help_flag_returns_storage_command_reference(self, cli_runner: OntobdcCliProcessRunner) -> None:
        result: CliInvocationResult = cli_runner.run("storage", "--help")

        assert result.exit_code == 0

        payload: Dict[str, Any] = result.json
        assert payload["title"] == "Storage CLI Help"
        assert payload["severity"] is None

        usage: Dict[str, str] = payload["content"]["Usage"]
        assert usage["base"] == "ontobdc storage <argument> [flags/parameters]"
        assert "element" in usage

        options: Dict[str, str] = payload["content"]["Options"]
        assert "--help | -h" in options

    def test_short_help_flag_returns_storage_command_reference(self, cli_runner: OntobdcCliProcessRunner) -> None:
        result: CliInvocationResult = cli_runner.run("storage", "-h")

        assert result.exit_code == 0
        assert result.json["title"] == "Storage CLI Help"

    def test_help_flag_matches_short_help_flag(self, cli_runner: OntobdcCliProcessRunner) -> None:
        long_flag_result: CliInvocationResult = cli_runner.run("storage", "--help")
        short_flag_result: CliInvocationResult = cli_runner.run("storage", "-h")

        assert long_flag_result.json["content"] == short_flag_result.json["content"]
