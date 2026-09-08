from pathlib import Path
from typing import Any, Dict, List

from test.e2e.cli_process_runner import CliInvocationResult, OntobdcCliProcessRunner

_EXPECTED_CHECK_NAMES: List[str] = [
    "OntoBDC Directory Ready",
    "Engine Ready",
    "Storage Index Healthy",
    "Execution Context Healthy",
    "Config Adapter Ready",
]


class TestOntobdcHealthCommand:
    """
    E2E coverage for `ontobdc health --json`.

    `health` only reads `.__ontobdc__/*`, it never writes, but every
    invocation still runs through `cli_runner`, which scopes the process's
    cwd to a fresh pytest `tmp_path` -- never the developer's real project
    directories.
    """

    def test_health_fails_without_init(self, cli_runner: OntobdcCliProcessRunner) -> None:
        result: CliInvocationResult = cli_runner.run("health")

        assert result.exit_code == 1

        payload: Dict[str, Any] = result.json
        assert payload["title"] == "Run"
        assert "ontobdc init" in payload["content"]["error"]

    def test_health_passes_after_init(self, cli_runner: OntobdcCliProcessRunner) -> None:
        cli_runner.run("init")
        result: CliInvocationResult = cli_runner.run("health")

        assert result.exit_code == 0

        payload: Dict[str, Any] = result.json
        assert payload["title"] == "Health"
        assert payload["severity"] == "SUCCESS"

        content: Dict[str, Any] = payload["content"]
        assert content["healthy"] is True

        checks: List[Dict[str, Any]] = content["checks"]
        checked_names: List[str] = [check["name"] for check in checks]
        for expected_check_name in _EXPECTED_CHECK_NAMES:
            assert expected_check_name in checked_names

        for check in checks:
            assert check["status"] == "pass"

    def test_health_does_not_modify_the_ontobdc_directory(
        self, cli_runner: OntobdcCliProcessRunner, tmp_path: Path
    ) -> None:
        cli_runner.run("init")

        ontobdc_directory: Path = tmp_path / ".__ontobdc__"
        snapshot_before: Dict[str, bytes] = self._snapshot(ontobdc_directory)

        result: CliInvocationResult = cli_runner.run("health")

        assert result.exit_code == 0
        assert self._snapshot(ontobdc_directory) == snapshot_before

    def _snapshot(self, directory: Path) -> Dict[str, bytes]:
        return {
            str(file_path.relative_to(directory)): file_path.read_bytes()
            for file_path in sorted(directory.rglob("*"))
            if file_path.is_file()
        }
