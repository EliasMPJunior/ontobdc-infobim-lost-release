from pathlib import Path
from typing import Any, Dict, List

from test.e2e.cli_process_runner import CliInvocationResult, OntobdcCliProcessRunner
from test.e2e.storage.container_fixture import StorageContainerFixture


class TestOntobdcStorageContainerRenameCommand:
    """
    E2E coverage for `ontobdc storage --container <container-id> --rename
    <name> --json`.
    """

    def test_rename_updates_the_registered_container_title(
        self, cli_runner: OntobdcCliProcessRunner, tmp_path: Path
    ) -> None:
        cli_runner.run("init")
        container_id, _container_path = StorageContainerFixture(cli_runner, tmp_path).create()

        result: CliInvocationResult = cli_runner.run(
            "storage", "--container", container_id, "--rename", "New Name"
        )

        assert result.exit_code == 0

        payload: Dict[str, Any] = result.json
        assert payload["title"] == "Storage Container Renamed"

        content: Dict[str, Any] = payload["content"]
        assert content["container_id"] == container_id
        assert content["name"] == "New Name"

        list_result: CliInvocationResult = cli_runner.run("storage")
        containers: List[Dict[str, Any]] = list_result.json["content"]["containers"]
        assert containers[0]["title"] == "New Name"

    def test_rename_unregistered_container_is_rejected(self, cli_runner: OntobdcCliProcessRunner) -> None:
        cli_runner.run("init")
        result: CliInvocationResult = cli_runner.run(
            "storage", "--container", "bogus-id", "--rename", "New Name"
        )

        assert result.exit_code == 1

        payload: Dict[str, Any] = result.json
        assert payload["title"] == "Run"
        assert "Container is not registered: bogus-id" in payload["content"]["error"]

    def test_rename_without_a_new_name_is_rejected(
        self, cli_runner: OntobdcCliProcessRunner, tmp_path: Path
    ) -> None:
        cli_runner.run("init")
        container_id, _container_path = StorageContainerFixture(cli_runner, tmp_path).create()

        result: CliInvocationResult = cli_runner.run("storage", "--container", container_id, "--rename")

        assert result.exit_code == 1
        assert "Invalid command arguments" in result.json["content"]["error"]
