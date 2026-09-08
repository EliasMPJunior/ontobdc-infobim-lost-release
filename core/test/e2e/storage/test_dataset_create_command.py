from pathlib import Path
from typing import Any, Dict

from test.e2e.cli_process_runner import CliInvocationResult, OntobdcCliProcessRunner
from test.e2e.storage.container_fixture import StorageContainerFixture


class TestOntobdcStorageDatasetCreateCommand:
    """
    E2E coverage for `ontobdc storage --container <id-or-path> --create
    <dataset-name> --json`.
    """

    def test_create_builds_a_new_dataset_inside_the_container(
        self, cli_runner: OntobdcCliProcessRunner, tmp_path: Path
    ) -> None:
        cli_runner.run("init")
        container_id, container_path = StorageContainerFixture(cli_runner, tmp_path).create()

        result: CliInvocationResult = cli_runner.run(
            "storage", "--container", container_id, "--create", "my-dataset"
        )

        assert result.exit_code == 0

        payload: Dict[str, Any] = result.json
        assert payload["title"] == "Storage Dataset Created"

        content: Dict[str, Any] = payload["content"]
        assert content["container_id"] == container_id
        assert Path(content["path"]).resolve() == (container_path / "my-dataset").resolve()
        assert content["exists"] is True

        dataset_directory: Path = container_path / "my-dataset" / ".__ontobdc__"
        assert (dataset_directory / "dataset.ttl").is_file()

    def test_create_rejects_a_dataset_path_outside_the_container(
        self, cli_runner: OntobdcCliProcessRunner, tmp_path: Path
    ) -> None:
        cli_runner.run("init")
        container_id, _container_path = StorageContainerFixture(cli_runner, tmp_path).create()

        result: CliInvocationResult = cli_runner.run(
            "storage", "--container", container_id, "--create", "nested/dataset"
        )

        assert result.exit_code == 1

        payload: Dict[str, Any] = result.json
        assert payload["title"] == "Run"
        assert "Invalid dataset_path: nested/dataset" in payload["content"]["error"]

    def test_create_with_an_unregistered_container_is_rejected(
        self, cli_runner: OntobdcCliProcessRunner
    ) -> None:
        cli_runner.run("init")
        result: CliInvocationResult = cli_runner.run(
            "storage", "--container", "bogus-container", "--create", "my-dataset"
        )

        assert result.exit_code == 1

        payload: Dict[str, Any] = result.json
        assert payload["title"] == "Run"
        assert "Invalid container selector: bogus-container" in payload["content"]["error"]

    def test_create_without_a_dataset_name_is_rejected(
        self, cli_runner: OntobdcCliProcessRunner, tmp_path: Path
    ) -> None:
        cli_runner.run("init")
        container_id, _container_path = StorageContainerFixture(cli_runner, tmp_path).create()

        result: CliInvocationResult = cli_runner.run(
            "storage", "--container", container_id, "--create"
        )

        assert result.exit_code == 1
        assert "Invalid command arguments" in result.json["content"]["error"]
