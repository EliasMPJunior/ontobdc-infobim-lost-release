from typing import Any, Dict

from test.e2e.cli_process_runner import CliInvocationResult, OntobdcCliProcessRunner


class TestOntobdcBaseCommand:
    """
    E2E coverage for the bare `ontobdc` entrypoint: no subcommand, help and
    unknown-argument handling. Every invocation runs the real installed
    executable through a subprocess, always with `--json`. `--version`/`-v`
    have their own dedicated coverage in `test_version_command.py`.
    """

    def test_no_arguments_lists_available_commands(self, cli_runner: OntobdcCliProcessRunner) -> None:
        result: CliInvocationResult = cli_runner.run()

        assert result.exit_code == 0
        assert result.stderr.strip() == "" or "Traceback" not in result.stderr

        payload: Dict[str, Any] = result.json
        assert payload["title"] == "OntoBDC Commands"
        assert payload["severity"] is None

        commands_tree: str = payload["content"]["Commands"]
        for expected_command in ("storage", "context", "health", "init"):
            assert expected_command in commands_tree

    def test_help_flag_returns_command_reference(self, cli_runner: OntobdcCliProcessRunner) -> None:
        result: CliInvocationResult = cli_runner.run("--help")

        assert result.exit_code == 0

        payload: Dict[str, Any] = result.json
        assert payload["title"] == "OntoBDC Help"

        documented_commands: Dict[str, str] = payload["content"]["Commands"]
        assert "storage" in documented_commands
        assert "context" in documented_commands

    def test_short_help_flag_returns_command_reference(self, cli_runner: OntobdcCliProcessRunner) -> None:
        result: CliInvocationResult = cli_runner.run("-h")

        assert result.exit_code == 0

        payload: Dict[str, Any] = result.json
        assert payload["title"] == "OntoBDC Help"

    def test_unknown_command_fails_with_exit_code_one(self, cli_runner: OntobdcCliProcessRunner) -> None:
        result: CliInvocationResult = cli_runner.run("foobar")

        assert result.exit_code == 1

        payload: Dict[str, Any] = result.json
        assert payload["title"] == "Run"
        assert "foobar" in payload["content"]["error"]

    def test_unknown_flag_fails_with_exit_code_one(self, cli_runner: OntobdcCliProcessRunner) -> None:
        result: CliInvocationResult = cli_runner.run("--bogus-flag")

        assert result.exit_code == 1

        payload: Dict[str, Any] = result.json
        assert payload["title"] == "Run"
        assert "--bogus-flag" in payload["content"]["error"]
