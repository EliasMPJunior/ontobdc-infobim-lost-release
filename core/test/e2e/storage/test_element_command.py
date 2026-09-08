from typing import Any, Dict

from test.e2e.cli_process_runner import CliInvocationResult, OntobdcCliProcessRunner


class TestOntobdcStorageElementCommand:
    """
    E2E coverage for `ontobdc storage --container <id-or-path> --element
    [--entity <entity-uri-or-identifier>] --json`.

    Exercising the happy path (listing real obdc:DataEntity instances) would
    require a fully attached storage container -- container.ttl, a synced
    Data Package and `frictionless` installed -- which is out of scope here.
    These tests cover the argument-validation and unregistered-container
    error paths, which are fully deterministic without any container setup.
    """

    def test_element_rejects_unregistered_container(self, cli_runner: OntobdcCliProcessRunner) -> None:
        cli_runner.run("init")
        result: CliInvocationResult = cli_runner.run(
            "storage", "--container", "bogus-container", "--element"
        )

        assert result.exit_code == 1

        payload: Dict[str, Any] = result.json
        assert payload["title"] == "Run"
        assert "Invalid container selector: bogus-container" in payload["content"]["error"]

    def test_element_with_entity_filter_rejects_unregistered_container(
        self, cli_runner: OntobdcCliProcessRunner
    ) -> None:
        cli_runner.run("init")
        result: CliInvocationResult = cli_runner.run(
            "storage", "--container", "bogus-container", "--element", "--entity", "SomeEntity"
        )

        assert result.exit_code == 1
        assert "Invalid container selector: bogus-container" in result.json["content"]["error"]

    def test_element_without_container_flag_is_rejected(self, cli_runner: OntobdcCliProcessRunner) -> None:
        cli_runner.run("init")
        result: CliInvocationResult = cli_runner.run("storage", "--element")

        assert result.exit_code == 1

        payload: Dict[str, Any] = result.json
        assert payload["title"] == "Run"
        assert "Invalid command arguments" in payload["content"]["error"]

    def test_element_with_empty_container_value_is_rejected(self, cli_runner: OntobdcCliProcessRunner) -> None:
        cli_runner.run("init")
        result: CliInvocationResult = cli_runner.run(
            "storage", "--container", "", "--element"
        )

        assert result.exit_code == 1
        assert "Invalid command arguments" in result.json["content"]["error"]

    def test_element_with_entity_flag_missing_value_is_rejected(
        self, cli_runner: OntobdcCliProcessRunner
    ) -> None:
        # This 5-token shape doesn't match element.py's own `accepts()`
        # (valid shapes are exactly 4 or exactly 6 tokens), so it falls
        # through to the sibling `container/entity.py` command instead --
        # still a clean rejection, just with that command's own message.
        cli_runner.run("init")
        result: CliInvocationResult = cli_runner.run(
            "storage", "--container", "foo", "--element", "--entity"
        )

        assert result.exit_code == 1
        assert "Could not resolve a container" in result.json["content"]["error"]

    def test_element_explore_rejects_json_output_before_opening_tui(
        self, cli_runner: OntobdcCliProcessRunner
    ) -> None:
        cli_runner.run("init")
        result: CliInvocationResult = cli_runner.run(
            "storage", "--container", "bogus-container", "--element", "--explore"
        )

        assert result.exit_code == 1
        payload: Dict[str, Any] = result.json
        assert payload["title"] == "Run"
        assert (
            "Interactive command 'explore' does not support json output."
            in payload["content"]["error"]
        )
