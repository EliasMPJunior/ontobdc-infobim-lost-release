from typing import Any, List
from unittest.mock import patch

import pytest
import yaml

from ontobdc.cli.adapter.context import CliContextAdapter
from ontobdc.cli.adapter.machine import (
    _HEALTH_CAPABILITY_IDS,
    CliHealthStateTransitionHandler,
)
from ontobdc.cli.domain.machine.health_state import CliHealthProcessState
from ontobdc.cli.domain.request.command import CliCommandRequest
from ontobdc.cli.domain.response.command import CommandResponse
from ontobdc.cli.plugin.command.health import CliHealthCommand
from ontobdc.shared.adapter.loader import CommandLoader
from ontobdc.shared.adapter.statechart import StatechartLocator

_EXECUTOR = "ontobdc.cli.adapter.machine.CapabilityExecutor.execute"

_ORDER: List[CliHealthProcessState] = [
    CliHealthProcessState.UNDEFINED,
    CliHealthProcessState.ONTOBDC_DIRECTORY_READY,
    CliHealthProcessState.ENGINE_READY,
    CliHealthProcessState.STORAGE_INDEX_HEALTHY,
    CliHealthProcessState.EXECUTION_CONTEXT_HEALTHY,
    CliHealthProcessState.CONFIG_ADAPTER_READY,
    CliHealthProcessState.BOOTSTRAP_HEALTHY,
]


def _command(args: List[str]) -> CliHealthCommand:
    return CliHealthCommand(
        CliCommandRequest(
            logical_component="cli",
            component_action="health",
            command_args=args,
            context=CliContextAdapter(args),
        )
    )


def _run(args: List[str] = ["health"]) -> CommandResponse:
    # The capabilities repair + validate a real project; never let the
    # suite mutate the checkout it runs from.
    with patch(_EXECUTOR, return_value={}):
        return _command(args).run()


def test_accepts_only_the_bare_health_token() -> None:
    assert CliHealthCommand.accepts(["health"])
    assert not CliHealthCommand.accepts(["health", "--fix"])
    assert not CliHealthCommand.accepts(["--version"])
    assert not CliHealthCommand.accepts([])


def test_health_is_discoverable_as_a_cli_command() -> None:
    from ontobdc.cli.adapter.logger import NullLogRepository

    ids = {
        cls.METADATA.id
        for cls in CommandLoader("cli", NullLogRepository()).get_all()
        if isinstance(cls, type)
    }
    assert "health" in ids


def test_the_statechart_is_the_linear_bootstrap_pipeline() -> None:
    path = StatechartLocator.locate_via_package(
        "ontobdc.cli.domain.machine", "standard_health.yaml",
    )
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    names = [
        state["name"]
        for state in data["statechart"]["root state"]["states"]
    ]

    assert names == [state.value.strip("_") for state in _ORDER]
    assert data["statechart"]["root state"]["states"][-1]["type"] == "final"
    assert list(CliHealthProcessState) == _ORDER


def test_every_intermediate_state_maps_to_a_bootstrap_capability() -> None:
    intermediate = _ORDER[1:-1]
    assert set(_HEALTH_CAPABILITY_IDS) == set(intermediate)
    for state, capability_id in _HEALTH_CAPABILITY_IDS.items():
        assert capability_id.endswith(state.value.strip("_"))


def test_run_records_one_check_per_capability_with_its_metadata() -> None:
    response = _run()

    checks = response.content["checks"]
    assert response.title == "Health"
    assert response.content["healthy"] is True
    assert response.severity == "SUCCESS"
    assert [check["name"] for check in checks] == [
        "OntoBDC Directory Ready",
        "Engine Ready",
        "Storage Index Healthy",
        "Execution Context Healthy",
        "Config Adapter Ready",
    ]
    for check in checks:
        assert check["status"] == "pass"
        assert check["uri"].startswith(
            "org.ontobdc.cli.plugin.capability.transformation.target."
        )
        assert check["description"]
        # ``detail`` is dropped when every check passed.
        assert set(check) == {"name", "status", "uri", "description"}


def test_a_failing_capability_is_reported_and_the_pipeline_continues() -> None:
    def _fake_execute(capability: Any, context: Any) -> dict:
        if capability.METADATA.name == "Storage Index Healthy":
            raise ValueError("storage.ttl is beyond repair")
        return {}

    with patch(_EXECUTOR, side_effect=_fake_execute):
        response = _command(["health"]).run()

    checks = response.content["checks"]
    assert len(checks) == 5  # every capability was still attempted
    assert response.content["healthy"] is False
    assert response.severity == "ERROR"

    failed = [check for check in checks if check["status"] == "fail"]
    assert [check["name"] for check in failed] == ["Storage Index Healthy"]
    assert "beyond repair" in failed[0]["detail"]


def test_health_refuses_to_bootstrap_a_directory_that_is_not_a_project(
    tmp_path,
) -> None:
    handler = CliHealthStateTransitionHandler(
        context=CliContextAdapter([]),
    )
    with patch(
        "ontobdc.cli.adapter.machine.StorageBootstrap.get_init_root_path",
        return_value=tmp_path,
    ):
        with pytest.raises(RuntimeError, match="Run 'ontobdc init' first"):
            handler.execute()

    assert not (tmp_path / ".__ontobdc__").exists()


def test_handler_state_sequence_is_the_full_pipeline() -> None:
    handler = CliHealthStateTransitionHandler(context=CliContextAdapter([]))
    assert handler.state_sequence == _ORDER


def _render(response: CommandResponse) -> str:
    from ontobdc.cli import CommandResponseRenderer
    from ontobdc.cli.adapter.loader import ResponseWidgetAdapterLoader
    from ontobdc.view.adapter.terminal.surface_renderer import (
        TerminalSurfaceRenderer,
    )
    from ontobdc.view.component.widget.python import TextWidget

    markdown = CommandResponseRenderer().response_to_markdown(
        response,
        response_loader_cls=ResponseWidgetAdapterLoader,
        text_widget_cls=TextWidget,
        widget_protocol=None,
    )
    return TerminalSurfaceRenderer.select_and_render(
        body_markdown=markdown,
        renderer=TerminalSurfaceRenderer(theme="error"),
    )


def test_rich_output_tints_pass_green_and_fail_red() -> None:
    from ontobdc.shared.adapter.terminal_color import GREEN, RED

    def _fake_execute(capability: Any, context: Any) -> dict:
        if capability.METADATA.name == "Engine Ready":
            raise ValueError("engine is unrepairable")
        return {}

    with patch(_EXECUTOR, side_effect=_fake_execute):
        rendered = _render(_command(["health"]).run())

    assert f"{GREEN}pass" in rendered
    assert f"{RED}fail" in rendered


def test_detail_cards_dim_the_uri_and_do_not_repeat_the_name() -> None:
    from ontobdc.shared.adapter.terminal_color import (
        ANSI_ESCAPE_REGEX,
        GRAY,
    )

    rendered = _render(_run())
    plain = ANSI_ESCAPE_REGEX.sub("", rendered)

    # The card is titled by the check name; a "NAME:" bullet under it is
    # removed as pure repetition.
    assert "OntoBDC Directory Ready" in plain
    assert "NAME: " not in plain
    assert "STATUS: " in plain and "DESCRIPTION: " in plain
    # The uri value is dimmed.
    assert f"{GRAY}org.ontobdc.cli.plugin.capability" in rendered
