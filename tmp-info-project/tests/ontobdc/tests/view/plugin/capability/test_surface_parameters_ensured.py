import json
import re

import pytest

from ontobdc.view.adapter.surface.document import (
    contains_external_runtime_reference,
    make_initial_html,
    set_state_marker,
)
from ontobdc.view.domain.machine.surface_state import SurfaceGenerationProcessState
from ontobdc.view.plugin.capability.transformation.surface_parameters_ensured import (
    SurfaceParametersEnsuredCapability,
)


class StubContext:
    def __init__(self, **parameters):
        self._parameters = dict(parameters)

    def get_parameter_value(self, name):
        return self._parameters.get(name)

    def set_parameter_value(self, name, value):
        self._parameters[name] = value

    def has_parameter(self, name):
        return name in self._parameters


def embedded_defaults(document):
    match = re.search(r"const DEFAULTS = (\{.*?\});", document, re.DOTALL)
    assert match, "the url-state bootstrap is missing from the document"
    return json.loads(match.group(1))


@pytest.fixture
def assembled_surface(tmp_path):
    path = tmp_path / "index.html"
    path.write_text(
        set_state_marker(make_initial_html("pt-BR"), "surface_assembled"),
        encoding="utf-8",
    )
    return path


def test_check_is_false_before_the_step_and_true_after(assembled_surface):
    capability = SurfaceParametersEnsuredCapability()
    context = StubContext(surface_path=str(assembled_surface), language="pt-BR")

    assert capability.check(context) is False
    capability.execute(context)
    assert capability.check(context) is True


def test_embeds_the_bootstrap_in_head_as_a_parser_blocking_script(assembled_surface):
    context = StubContext(surface_path=str(assembled_surface), language="pt-BR")
    SurfaceParametersEnsuredCapability().execute(context)

    document = assembled_surface.read_text(encoding="utf-8")
    assert '<script id="ontobdc-surface-url-state">' in document
    # Before </head>, so the URL language is applied before first paint and
    # before the deferred component modules upgrade any Tile.
    assert document.index("ontobdc-surface-url-state") < document.index("</head>")


def test_declares_the_requested_language_and_the_shipped_theme_default(assembled_surface):
    context = StubContext(surface_path=str(assembled_surface), language="pt-BR")
    result = SurfaceParametersEnsuredCapability().execute(context)

    defaults = embedded_defaults(assembled_surface.read_text(encoding="utf-8"))
    assert defaults["lang"] == "pt-BR"
    # The same catalog onto-theme-tile cycles through, not a second copy.
    import ontobdc_view

    assert defaults["theme"] == ontobdc_view.theme_catalog()[0]["name"]
    assert result["url_state_defaults"] == defaults
    assert (
        result["resulting_state"]
        is SurfaceGenerationProcessState.SURFACE_PARAMETERS_ENSURED
    )


def test_language_default_falls_back_to_the_document_lang(tmp_path):
    path = tmp_path / "index.html"
    path.write_text(
        set_state_marker(make_initial_html("es"), "surface_assembled"),
        encoding="utf-8",
    )
    SurfaceParametersEnsuredCapability().execute(StubContext(surface_path=str(path)))

    assert embedded_defaults(path.read_text(encoding="utf-8"))["lang"] == "es"


def test_re_running_replaces_the_bootstrap_instead_of_stacking(assembled_surface):
    capability = SurfaceParametersEnsuredCapability()
    context = StubContext(surface_path=str(assembled_surface), language="pt-BR")

    capability.execute(context)
    context.set_parameter_value("language", "en")
    capability.execute(context)

    document = assembled_surface.read_text(encoding="utf-8")
    assert document.count('id="ontobdc-surface-url-state"') == 1
    assert embedded_defaults(document)["lang"] == "en"


def test_bootstrap_stays_offline(assembled_surface):
    context = StubContext(surface_path=str(assembled_surface), language="pt-BR")
    SurfaceParametersEnsuredCapability().execute(context)

    # surface_validated rejects any external runtime reference outright.
    assert (
        contains_external_runtime_reference(
            assembled_surface.read_text(encoding="utf-8")
        )
        is False
    )
