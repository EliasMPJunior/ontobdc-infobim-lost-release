from pathlib import Path
from typing import Any, Dict, List

from test.e2e.cli_process_runner import CliInvocationResult, OntobdcCliProcessRunner
from test.e2e.storage.container_fixture import StorageContainerFixture


class TestOntobdcStorageContainerEntityCommand:
    """
    E2E coverage for `ontobdc storage --entity ... --json` (`entity.py`):
    the catalog listing, the URI-lookup echo, and the per-container
    instance listing. `--create <name> --entity <type>` (materializing a
    new entity instance) is out of scope -- it needs a resolvable entity
    facade, a generated workbook and a related dataset.ttl entry.
    """

    def test_entity_all_lists_the_brasidata_entity_catalog(
        self, cli_runner: OntobdcCliProcessRunner
    ) -> None:
        cli_runner.run("init")
        result: CliInvocationResult = cli_runner.run("storage", "--entity", "--all")

        assert result.exit_code == 0

        payload: Dict[str, Any] = result.json
        assert payload["title"] == "Brasidata Entity Catalog"

        content: Dict[str, Any] = payload["content"]
        assert content["entity_count"] > 0
        entities: List[Dict[str, Any]] = content["entities"]
        assert len(entities) == content["entity_count"]
        assert all("entity_uri" in entity for entity in entities)

    def test_entity_lookup_by_uri_echoes_the_requested_uri(
        self, cli_runner: OntobdcCliProcessRunner
    ) -> None:
        cli_runner.run("init")
        result: CliInvocationResult = cli_runner.run("storage", "--entity", "obdc:SomeType")

        assert result.exit_code == 0

        payload: Dict[str, Any] = result.json
        assert payload["title"] == "Storage Entity"
        assert payload["content"]["entity_uri"] == "obdc:SomeType"

    def test_entity_list_without_a_resolvable_container_is_rejected(
        self, cli_runner: OntobdcCliProcessRunner
    ) -> None:
        cli_runner.run("init")
        result: CliInvocationResult = cli_runner.run("storage", "--entity", "WorkStream")

        assert result.exit_code == 1

        payload: Dict[str, Any] = result.json
        assert payload["title"] == "Run"
        assert "Could not resolve a container" in payload["content"]["error"]

    def test_entity_list_in_a_registered_container_returns_zero_instances(
        self, cli_runner: OntobdcCliProcessRunner, tmp_path: Path
    ) -> None:
        cli_runner.run("init")
        container_id, _container_path = StorageContainerFixture(cli_runner, tmp_path).create()

        result: CliInvocationResult = cli_runner.run(
            "storage", "--container", container_id, "--entity", "WorkStream"
        )

        assert result.exit_code == 0

        payload: Dict[str, Any] = result.json
        assert payload["title"] == "Storage Entity Instances"

        content: Dict[str, Any] = payload["content"]
        assert content["container_id"] == container_id
        assert content["entity"] == "WorkStream"
        assert content["instance_count"] == 0
        assert content["instances"] == []
