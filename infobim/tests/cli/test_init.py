from pathlib import Path

from infobim import cli
from infobim.cli.plugin.command.init import CliInitCommand
from ontobdc.cli.domain.response.command import CommandResponse


def test_infobim_init_delegates_to_ontobdc_command(
    tmp_path: Path,
    monkeypatch,
    capsys,
) -> None:
    observed = {}

    def check(command) -> bool:
        observed["args"] = list(command._request.command_args)
        observed["component"] = command._request.logical_component
        return True

    def run(command) -> CommandResponse:
        observed["type"] = type(command).__name__
        return CommandResponse(
            title="Init",
            description="delegated",
            content={"root_path": str(tmp_path)},
        )

    monkeypatch.setattr(CliInitCommand, "check", check)
    monkeypatch.setattr(CliInitCommand, "run", run)

    cli.main(["init"])

    # "init" has no dedicated logical_component of its own to scope into
    # (matching ontobdc's own native `ontobdc init`, driven by this exact
    # same CliCommandRunAdapter.make() code path) -- it's discovered as
    # part of the "cli" domain's command list, and since scoping by "init"
    # itself finds nothing, command_args stays the full, unstripped argv.
    assert observed == {
        "args": ["init"],
        "component": "cli",
        "type": "CliInitCommand",
    }
    assert "delegated" in capsys.readouterr().out


def test_infobim_init_rejects_extra_arguments() -> None:
    assert CliInitCommand.accepts(["init"])
    assert not CliInitCommand.accepts(["init", "--project"])
