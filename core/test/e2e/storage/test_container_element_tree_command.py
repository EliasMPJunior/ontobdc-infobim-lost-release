from pathlib import Path
from typing import Any, Dict

from test.e2e.cli_process_runner import CliInvocationResult, OntobdcCliProcessRunner
from test.e2e.storage.container_fixture import StorageContainerFixture


class TestOntobdcStorageContainerElementTreeCommand:
    """
    E2E coverage for `ontobdc storage --container <id-or-path> --element
    <element_id> --json`.

    Exercising the happy path (a real obdc:DataEntity element with actual
    RDF properties) would require a fully materialized entity instance --
    an entity facade resolved from the Brasidata entity catalog, a
    generated workbook, and a related dataset.ttl entry (see
    `StorageEntityCommand._run_create_instance`). That is out of scope
    here; these tests cover the two deterministic rejection paths.
    """

    def test_element_tree_of_unregistered_container_is_rejected(
        self, cli_runner: OntobdcCliProcessRunner
    ) -> None:
        cli_runner.run("init")
        result: CliInvocationResult = cli_runner.run(
            "storage", "--container", "bogus-container", "--element", "some-id"
        )

        assert result.exit_code == 1

        payload: Dict[str, Any] = result.json
        assert payload["title"] == "Run"
        assert "Container is not registered: bogus-container" in payload["content"]["error"]

    def test_element_tree_of_missing_element_is_rejected(
        self, cli_runner: OntobdcCliProcessRunner, tmp_path: Path
    ) -> None:
        cli_runner.run("init")
        container_id, _container_path = StorageContainerFixture(cli_runner, tmp_path).create()

        result: CliInvocationResult = cli_runner.run(
            "storage", "--container", container_id, "--element", "some-id"
        )

        assert result.exit_code == 1

        payload: Dict[str, Any] = result.json
        assert payload["title"] == "Run"
        assert "Element is not registered in this container: some-id" in payload["content"]["error"]
