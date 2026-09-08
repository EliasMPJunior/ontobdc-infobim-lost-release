from pathlib import Path
from typing import Any, Dict, List

from test.e2e.cli_process_runner import CliInvocationResult, OntobdcCliProcessRunner
from test.e2e.storage.container_fixture import StorageContainerFixture


class TestOntobdcStorageContainerDeleteCommand:
    """
    E2E coverage for `ontobdc storage --delete <container-id> --json`.
    """

    def test_delete_removes_a_registered_container_from_the_index(
        self, cli_runner: OntobdcCliProcessRunner, tmp_path: Path
    ) -> None:
        cli_runner.run("init")
        container_id, _container_path = StorageContainerFixture(cli_runner, tmp_path).create()

        result: CliInvocationResult = cli_runner.run("storage", "--delete", container_id)

        assert result.exit_code == 0

        payload: Dict[str, Any] = result.json
        assert payload["title"] == "Container Deleted"
        assert payload["content"]["container_id"] == container_id

        list_result: CliInvocationResult = cli_runner.run("storage")
        containers: List[Dict[str, Any]] = list_result.json["content"]["containers"]
        assert containers == []

    def test_delete_leaves_the_container_directory_on_disk(
        self, cli_runner: OntobdcCliProcessRunner, tmp_path: Path
    ) -> None:
        cli_runner.run("init")
        container_id, container_path = StorageContainerFixture(cli_runner, tmp_path).create()

        cli_runner.run("storage", "--delete", container_id)

        assert container_path.is_dir()
        assert (container_path / ".__ontobdc__" / "container.ttl").is_file()

    def test_delete_unregistered_container_fails_with_exit_zero(
        self, cli_runner: OntobdcCliProcessRunner
    ) -> None:
        cli_runner.run("init")
        result: CliInvocationResult = cli_runner.run("storage", "--delete", "bogus-id")

        assert result.exit_code == 0

        payload: Dict[str, Any] = result.json
        assert payload["title"] == "Failed to Delete Container"
        assert "is not registered" in payload["content"]["error"]

    def test_delete_without_a_container_id_is_rejected(self, cli_runner: OntobdcCliProcessRunner) -> None:
        cli_runner.run("init")
        result: CliInvocationResult = cli_runner.run("storage", "--delete")

        assert result.exit_code == 1
        assert "Invalid command arguments" in result.json["content"]["error"]
