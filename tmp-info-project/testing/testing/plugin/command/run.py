from pathlib import Path
from typing import Any, Dict, List, Optional

from ontobdc.cli.domain.exception.command import CliCommandArgumentException
from ontobdc.cli.domain.model.command import CliCommandMetadata
from ontobdc.cli.domain.port.command import CliCommandPort
from ontobdc.cli.domain.request.command import CliCommandRequest
from ontobdc.cli.domain.response.command import CommandResponse

from ontobdc_dev.testing.application.catalog import TestCatalog, TestCatalogLoader
from ontobdc_dev.testing.application.runner import SemanticTestRunner
from ontobdc_dev.testing.domain.model.context import ExecutionContext
from ontobdc_dev.testing.domain.model.result import ActionResult, StateSnapshot, TestRunResult
from ontobdc_dev.testing.plugin.command.args import collect_params, flag_value


class DevTestRunCommand(CliCommandPort):
    """Run a state observation, or a check -> hotfix -> recheck cycle for an action.

    This is the command that actually delivers "execução dos check e
    hotfix": `--state <id>` runs a bare check; `--action <id>` executes the
    action's `python-call` hotfix and reobserves its declared states
    afterwards, deriving the verdict from that reobservation, never from
    the hotfix's own return value (semantic-test-orchestrator.md, 6.1).
    """

    METADATA: CliCommandMetadata = CliCommandMetadata(
        id="test-run",
        logical_component="dev",
        description="Run a state check, or execute an action and reobserve its declared states.",
        arguments=[
            {
                "accepts": ["test"],
                "description": "Run a state check or a check-hotfix-recheck cycle for an action.",
                "usage": (
                    "ontobdc dev test run --state <id> | --action <id> "
                    "--manifest <path> [--param key=value ...]"
                ),
            },
            {
                "accepts": ["--manifest"],
                "valued": True,
                "description": "Path to a manifest file or a directory of *.yaml manifests.",
                "usage": "ontobdc dev test run --manifest tests/semantic --state <id>",
            },
            {
                "accepts": ["--state"],
                "valued": True,
                "description": "Observe a single StateDefinition and derive a verdict from it.",
                "usage": "ontobdc dev test run --manifest tests/semantic --state storage.container.metadata.ready --param root_path=<path> --param container_path=<path>",
            },
            {
                "accepts": ["--action"],
                "valued": True,
                "description": "Execute a TestAction and reobserve its declared states afterwards.",
                "usage": "ontobdc dev test run --manifest tests/semantic --action storage.container.metadata.repair --param root_path=<path> --param container_path=<path>",
            },
            {
                "accepts": ["--param"],
                "description": (
                    "Provide 'key=value', substituted into '${context.key}' "
                    "placeholders. Repeatable."
                ),
                "usage": "ontobdc dev test run ... --param root_path=<path> --param container_path=<path>",
            },
        ],
    )

    def __init__(self, request: CliCommandRequest) -> None:
        self._request: CliCommandRequest = request
        self._manifest_path: Optional[Path] = None
        self._state_name: Optional[str] = None
        self._action_name: Optional[str] = None
        self._context_values: Dict[str, str] = {}

    @staticmethod
    def accepts(args: List[str]) -> bool:
        return (
            len(args) >= 3
            and args[0] == "dev"
            and args[1] == "test"
            and args[2] == "run"
        )

    def check(self) -> bool:
        command_args: List[str] = self._request.command_args
        if len(command_args) < 2 or command_args[0] != "test" or command_args[1] != "run":
            return False

        tokens: List[str] = command_args[2:]

        manifest_value: Optional[str] = flag_value(tokens, "--manifest")
        if not manifest_value:
            return False
        self._manifest_path = Path(manifest_value).expanduser()

        state_value: Optional[str] = flag_value(tokens, "--state")
        action_value: Optional[str] = flag_value(tokens, "--action")
        if bool(state_value) == bool(action_value):
            raise CliCommandArgumentException(
                "Exactly one of --state or --action is required."
            )
        self._state_name = state_value
        self._action_name = action_value

        try:
            self._context_values = collect_params(tokens)
        except ValueError as exception:
            raise CliCommandArgumentException(str(exception)) from exception

        return True

    def run(self) -> CommandResponse:
        catalog: TestCatalog = TestCatalogLoader().load(self._manifest_path)
        runner: SemanticTestRunner = SemanticTestRunner(catalog)
        context: ExecutionContext = ExecutionContext(values=self._context_values)

        result: TestRunResult
        if self._state_name:
            result = runner.run_state(self._state_name, context)
        else:
            result = runner.run_action(self._action_name, context)

        return CommandResponse(
            title="Semantic Test Run",
            description=f"Verdict: {result.verdict.value}",
            content=_serialize_result(result),
        )


def _serialize_result(result: TestRunResult) -> Dict[str, Any]:
    return {
        "mode": result.mode,
        "target": result.target,
        "verdict": result.verdict.value,
        "before": {name: _serialize_snapshot(snapshot) for name, snapshot in result.before.items()},
        "action_result": _serialize_action_result(result.action_result),
        "after": {name: _serialize_snapshot(snapshot) for name, snapshot in result.after.items()},
        "detail": result.detail,
    }


def _serialize_snapshot(snapshot: StateSnapshot) -> Dict[str, Any]:
    return {
        "status": snapshot.status.value,
        "observed_at": snapshot.observed_at,
        "detail": snapshot.detail,
        "evidence": snapshot.evidence,
    }


def _serialize_action_result(action_result: Optional[ActionResult]) -> Optional[Dict[str, Any]]:
    if action_result is None:
        return None

    return {
        "action": action_result.action,
        "status": action_result.status.value,
        "executed_at": action_result.executed_at,
        "detail": action_result.detail,
    }
