from pathlib import Path
from typing import Any, Dict, List

from test.e2e.cli_process_runner import CliInvocationResult, OntobdcCliProcessRunner
from test.e2e.storage.container_fixture import StorageContainerFixture


class TestOntobdcStorageContainerTreeCommand:
    """
    E2E coverage for `ontobdc storage --container <id-or-path> --json`.
    """

    def test_tree_of_an_empty_container_has_no_children(
        self, cli_runner: OntobdcCliProcessRunner, tmp_path: Path
    ) -> None:
        cli_runner.run("init")
        container_id, _container_path = StorageContainerFixture(cli_runner, tmp_path).create()

        result: CliInvocationResult = cli_runner.run("storage", "--container", container_id)

        assert result.exit_code == 0

        payload: Dict[str, Any] = result.json
        assert payload["title"] == "Storage Container"
        assert payload["description"] == f"Tree view of container {container_id}."

        tree: Dict[str, Any] = payload["content"]["tree"]
        assert tree["kind"] == "root"
        assert tree["children"] == []

    def test_tree_lists_datasets_after_a_dataset_is_created(
        self, cli_runner: OntobdcCliProcessRunner, tmp_path: Path
    ) -> None:
        cli_runner.run("init")
        container_id, _container_path = StorageContainerFixture(cli_runner, tmp_path).create()
        cli_runner.run("storage", "--container", container_id, "--create", "my-dataset")

        result: CliInvocationResult = cli_runner.run("storage", "--container", container_id)

        assert result.exit_code == 0
        children: List[Dict[str, Any]] = result.json["content"]["tree"]["children"]
        assert children[0]["name"] == "Datasets"
        assert children[0]["kind"] == "section"
        dataset_names: List[str] = [node["name"] for node in children[0]["children"]]
        assert any("my-dataset" in name for name in dataset_names)

    def test_tree_of_unregistered_container_is_rejected(self, cli_runner: OntobdcCliProcessRunner) -> None:
        cli_runner.run("init")
        result: CliInvocationResult = cli_runner.run("storage", "--container", "bogus-container")

        assert result.exit_code == 1

        payload: Dict[str, Any] = result.json
        assert payload["title"] == "Run"
        assert "Container is not registered: bogus-container" in payload["content"]["error"]
