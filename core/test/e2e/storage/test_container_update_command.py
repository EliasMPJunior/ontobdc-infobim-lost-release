from pathlib import Path
from typing import Any, Dict

from test.e2e.cli_process_runner import CliInvocationResult, OntobdcCliProcessRunner
from test.e2e.storage.container_fixture import StorageContainerFixture


class TestOntobdcStorageContainerUpdateCommand:
    """
    E2E coverage for `ontobdc storage --update --json` and
    `ontobdc storage --container-id <id> --update --json`.
    """

    def test_update_by_container_id_cleans_and_updates_the_container(
        self, cli_runner: OntobdcCliProcessRunner, tmp_path: Path
    ) -> None:
        cli_runner.run("init")
        container_id, _container_path = StorageContainerFixture(cli_runner, tmp_path).create()

        result: CliInvocationResult = cli_runner.run(
            "storage", "--container-id", container_id, "--update"
        )

        assert result.exit_code == 0

        payload: Dict[str, Any] = result.json
        assert payload["title"] == "Storage Container Updated"

        content: Dict[str, Any] = payload["content"]
        assert content["container_id"] == container_id
        assert content["current_state"] == "__container_ro_crate_updated__"

    def test_update_without_a_resolvable_container_is_rejected(
        self, cli_runner: OntobdcCliProcessRunner
    ) -> None:
        cli_runner.run("init")
        result: CliInvocationResult = cli_runner.run("storage", "--update")

        assert result.exit_code == 1

        payload: Dict[str, Any] = result.json
        assert payload["title"] == "Run"
        assert "Unable to resolve the current container" in payload["content"]["error"]

    def test_update_with_unregistered_container_id_is_rejected(
        self, cli_runner: OntobdcCliProcessRunner
    ) -> None:
        cli_runner.run("init")
        result: CliInvocationResult = cli_runner.run(
            "storage", "--container-id", "bogus-id", "--update"
        )

        assert result.exit_code == 1
        assert "Container is not registered: bogus-id" in result.json["content"]["error"]
