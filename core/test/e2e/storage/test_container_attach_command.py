from typing import Any, Dict

from test.e2e.cli_process_runner import CliInvocationResult, OntobdcCliProcessRunner


class TestOntobdcStorageContainerAttachCommand:
    """
    E2E coverage for `ontobdc storage --attach --json` and its
    `--container-path`/`--container` path variants.

    A container that `ontobdc storage --create` already fully wires into
    the current project cannot be cleanly re-attached in this codebase --
    the attachment statechart partially mutates the storage index before
    failing with a `PostconditionError` at its `CONTEXT_ATTACHED`
    transition. That is a separate, deeper bug in
    `storage/adapter/attachment/machine.py`, out of scope for testing this
    command's own argument handling, so it is not asserted here. These
    tests cover `attach.py`'s own argument validation and the deterministic
    first-state failure when no container metadata exists yet.
    """

    def test_attach_without_container_metadata_fails_cleanly(
        self, cli_runner: OntobdcCliProcessRunner
    ) -> None:
        cli_runner.run("init")
        result: CliInvocationResult = cli_runner.run("storage", "--attach")

        assert result.exit_code == 0

        payload: Dict[str, Any] = result.json
        assert payload["title"] == "Invalid Container Graph"
        assert "Container metadata file was not found" in payload["content"]["error"]

    def test_attach_with_container_path_alias_behaves_like_bare_attach(
        self, cli_runner: OntobdcCliProcessRunner
    ) -> None:
        cli_runner.run("init")
        result: CliInvocationResult = cli_runner.run(
            "storage", "--container-path", ".", "--attach"
        )

        assert result.exit_code == 0
        assert result.json["title"] == "Invalid Container Graph"

    def test_attach_with_container_alias_behaves_like_bare_attach(
        self, cli_runner: OntobdcCliProcessRunner
    ) -> None:
        cli_runner.run("init")
        result: CliInvocationResult = cli_runner.run("storage", "--container", ".", "--attach")

        assert result.exit_code == 0
        assert result.json["title"] == "Invalid Container Graph"

    def test_attach_with_nonexistent_container_path_is_rejected(
        self, cli_runner: OntobdcCliProcessRunner
    ) -> None:
        cli_runner.run("init")
        result: CliInvocationResult = cli_runner.run(
            "storage", "--container-path", "does-not-exist", "--attach"
        )

        assert result.exit_code == 1

        payload: Dict[str, Any] = result.json
        assert payload["title"] == "Run"
        assert "Invalid command arguments" in payload["content"]["error"]
