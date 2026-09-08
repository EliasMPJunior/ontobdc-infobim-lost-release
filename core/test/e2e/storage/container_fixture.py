from pathlib import Path
from typing import Any, Dict, List, Tuple

from test.e2e.cli_process_runner import CliInvocationResult, OntobdcCliProcessRunner


class StorageContainerFixture:
    """
    Creates a real, registered storage container inside an isolated project
    root via `ontobdc storage --create`, for tests that need one already in
    place (the delete/rename/update/attach happy paths). The caller must
    have already run `cli_runner.run("init")`.
    """

    def __init__(self, cli_runner: OntobdcCliProcessRunner, project_root: Path) -> None:
        self._cli_runner: OntobdcCliProcessRunner = cli_runner
        self._project_root: Path = project_root

    def create(self, directory_name: str = "container") -> Tuple[str, Path]:
        container_path: Path = self._project_root / directory_name

        create_result: CliInvocationResult = self._cli_runner.run(
            "storage", "--create", directory_name
        )
        if create_result.exit_code != 0:
            raise AssertionError(
                f"Test setup failed: could not create container "
                f"'{directory_name}': {create_result.stdout}"
            )

        list_result: CliInvocationResult = self._cli_runner.run("storage")
        containers: List[Dict[str, Any]] = list_result.json["content"]["containers"]
        matching_containers: List[Dict[str, Any]] = [
            container
            for container in containers
            if container["location"] == str(container_path.resolve())
        ]
        if not matching_containers:
            raise AssertionError(
                f"Test setup failed: created container was not found in the "
                f"storage index: {list_result.stdout}"
            )

        container_id: str = str(matching_containers[0]["id"])
        return container_id, container_path
