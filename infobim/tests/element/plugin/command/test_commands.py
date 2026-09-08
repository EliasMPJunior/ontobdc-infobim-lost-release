from ontobdc.cli.adapter.logger import NullLogRepository
from ontobdc.shared.adapter.loader import CommandLoader

from infobim.element.plugin.command.fill import ElementFillCommand
from infobim.element.plugin.command.set_parameter import ElementParameterSetCommand
from infobim.element.plugin.command.set_parameter_all import (
    ElementParameterSetAllCommand,
)
from infobim.element.plugin.command.unset_all_parameters import (
    ElementParametersUnsetAllCommand,
)
from infobim.element.plugin.command.unset_parameter import (
    ElementParameterUnsetCommand,
)

COMMANDS = (
    ElementParameterSetCommand,
    ElementParameterSetAllCommand,
    ElementParameterUnsetCommand,
    ElementParametersUnsetAllCommand,
    ElementFillCommand,
)


def _matches(args):
    return [command for command in COMMANDS if command.accepts(args)]


def test_each_requested_contract_resolves_to_exactly_one_command():
    contracts = [
        [
            "element",
            "--project",
            "PROJECT-ID",
            "--global-id",
            "ELEMENT-ID",
            "--parameter",
            "https://example.test/name",
            "--set",
            "Wall A",
        ],
        [
            "element",
            "--project",
            "PROJECT-ID",
            "--global-id",
            "ELEMENT-ID",
            "--parameter",
            "https://example.test/name",
            "--set",
            "Wall A",
            "--all",
        ],
        [
            "element",
            "--project",
            "PROJECT-ID",
            "--global-id",
            "ELEMENT-ID",
            "--parameter",
            "https://example.test/name",
            "--unset",
        ],
        [
            "element",
            "--project",
            "PROJECT-ID",
            "--global-id",
            "ELEMENT-ID",
            "--all",
            "--unset",
        ],
        [
            "element",
            "--project",
            "PROJECT-ID",
            "--dataset",
            "DATASET-ID",
            "--entity",
            "https://example.test/Entity",
            "--fill",
        ],
        [
            "element",
            "--project",
            "PROJECT-ID",
            "--dataset",
            "DATASET-ID",
            "--entity",
            "https://example.test/Entity",
            "--fill",
            "--schema",
            "IFC2X3",
        ],
    ]

    assert [len(_matches(contract)) for contract in contracts] == [1, 1, 1, 1, 1, 1]


def test_read_and_list_contracts_invented_by_previous_implementation_are_rejected():
    assert not _matches(
        [
            "element",
            "--project",
            "PROJECT-ID",
            "--global-id",
            "ELEMENT-ID",
            "--parameter",
            "https://example.test/name",
        ]
    )
    assert not _matches(
        [
            "element",
            "--project",
            "PROJECT-ID",
            "--global-id",
            "ELEMENT-ID",
            "--parameter",
            "--all",
        ]
    )


def test_project_is_required_on_all_four_commands():
    assert not _matches(
        [
            "element",
            "--global-id",
            "ELEMENT-ID",
            "--parameter",
            "https://example.test/name",
            "--set",
            "Wall A",
        ]
    )


def test_command_loader_discovers_exactly_the_four_element_commands():
    discovered = CommandLoader(
        "element",
        NullLogRepository(),
        root_package="infobim",
    ).get_all()

    assert {command.METADATA.id for command in discovered} == {
        "element_parameter_set",
        "element_parameter_set_all",
        "element_parameter_unset",
        "element_parameters_unset_all",
        "element_fill",
    }
