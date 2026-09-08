from typing import Any, Dict, List

from test.e2e.cli_process_runner import CliInvocationResult, OntobdcCliProcessRunner


class TestOntobdcStorageBaseCommand:
    """
    E2E coverage for `ontobdc storage --json`, `ontobdc storage --list --json`
    and `ontobdc storage -l --json` -- the container-listing base command.
    """

    def test_storage_without_flags_lists_containers(self, cli_runner: OntobdcCliProcessRunner) -> None:
        cli_runner.run("init")
        result: CliInvocationResult = cli_runner.run("storage")

        assert result.exit_code == 0

        payload: Dict[str, Any] = result.json
        assert payload["title"] == "Storage Containers"
        assert payload["severity"] is None

        containers: List[Dict[str, Any]] = payload["content"]["containers"]
        assert containers == []

    def test_storage_list_flag_lists_containers(self, cli_runner: OntobdcCliProcessRunner) -> None:
        cli_runner.run("init")
        result: CliInvocationResult = cli_runner.run("storage", "--list")

        assert result.exit_code == 0
        assert result.json["title"] == "Storage Containers"
        assert result.json["content"]["containers"] == []

    def test_storage_short_list_flag_lists_containers(self, cli_runner: OntobdcCliProcessRunner) -> None:
        cli_runner.run("init")
        result: CliInvocationResult = cli_runner.run("storage", "-l")

        assert result.exit_code == 0
        assert result.json["title"] == "Storage Containers"
        assert result.json["content"]["containers"] == []

    def test_storage_without_init_reports_missing_project_root(
        self, cli_runner: OntobdcCliProcessRunner
    ) -> None:
        result: CliInvocationResult = cli_runner.run("storage")

        assert result.exit_code == 0

        payload: Dict[str, Any] = result.json
        assert payload["title"] == "Failed to List Containers"
        assert "Project root directory not set" in payload["content"]["error"]
