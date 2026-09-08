import sys
import types
from unittest.mock import MagicMock, patch

from ontobdc.shared.adapter.config import (
    ConfigDataAdapter,
    UnsetProjectRootConfigDataAdapter,
)


def test_is_a3_installed_reflects_find_spec() -> None:
    with patch(
        "ontobdc.shared.adapter.config.find_spec", return_value=object()
    ):
        assert ConfigDataAdapter.is_a3_installed() is True

    with patch(
        "ontobdc.shared.adapter.config.find_spec", return_value=None
    ):
        assert ConfigDataAdapter.is_a3_installed() is False


def test_is_a3_installed_swallows_import_machinery_errors() -> None:
    with patch(
        "ontobdc.shared.adapter.config.find_spec", side_effect=ValueError
    ):
        assert ConfigDataAdapter.is_a3_installed() is False


def test_is_a3_installed_available_without_a_project_root() -> None:
    # Inherited as a staticmethod, so it works even when the root-less
    # adapter would raise for every project-scoped property.
    assert isinstance(
        UnsetProjectRootConfigDataAdapter.is_a3_installed(), bool
    )


def test_entity_strategy_skips_lemmatization_without_a3() -> None:
    from ontobdc.context.plugin.parameter.entity import EntityUriStrategy

    with patch.object(
        ConfigDataAdapter, "is_a3_installed", return_value=False
    ):
        assert (
            EntityUriStrategy._lemmatize("running dogs", "en")
            == "running dogs"
        )


def test_entity_strategy_lemmatizes_through_ontobdc_a3_when_installed() -> None:
    from ontobdc.context.plugin.parameter.entity import EntityUriStrategy

    fake_lemma = MagicMock(return_value="run dog")
    fake_module = types.ModuleType("ontobdc_a3.prompt.adapter.lemmatization")
    fake_module.to_lemma = fake_lemma

    modules = {
        "ontobdc_a3": types.ModuleType("ontobdc_a3"),
        "ontobdc_a3.prompt": types.ModuleType("ontobdc_a3.prompt"),
        "ontobdc_a3.prompt.adapter": types.ModuleType(
            "ontobdc_a3.prompt.adapter"
        ),
        "ontobdc_a3.prompt.adapter.lemmatization": fake_module,
    }

    with patch.object(
        ConfigDataAdapter, "is_a3_installed", return_value=True
    ), patch.dict(sys.modules, modules):
        assert EntityUriStrategy._lemmatize("running dogs", "en") == "run dog"

    fake_lemma.assert_called_once_with("running dogs", language="en")
