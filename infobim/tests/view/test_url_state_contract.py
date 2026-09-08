"""What `infobim view` must be able to produce, expressed against the
*installed* ontobdc / ontobdc-view rather than the checked-out sources.

Every failure here means the environment is running a build of those
packages that predates URL-owned presentation state — which at runtime looks
exactly like "the language/theme fix does not work": the control changes the
page, the address bar never changes, and a reload reverts it. Catching it as
a failing test names the real cause instead.
"""
import re

import pytest

ontobdc_view = pytest.importorskip("ontobdc_view")

from ontobdc.view.domain.machine.surface_state import SurfaceGenerationProcessState
from ontobdc.view.adapter.surface.machine import _capability_type_for_state

from infobim.view.adapter.component import InfoBIMComponentSourceAdapter


def test_surface_pipeline_has_the_default_parameter_step():
    assert hasattr(SurfaceGenerationProcessState, "SURFACE_PARAMETERS_ENSURED"), (
        "the installed ontobdc has no SURFACE_PARAMETERS_ENSURED state, so a "
        "generated Surface never normalizes its own URL"
    )


def test_the_default_parameter_step_resolves_to_a_capability():
    capability = _capability_type_for_state(
        SurfaceGenerationProcessState.SURFACE_PARAMETERS_ENSURED
    )
    assert capability is not None


def test_the_pipeline_can_embed_the_url_state_runtime():
    from ontobdc.view.adapter.surface.document import build_url_state_bootstrap

    bootstrap = build_url_state_bootstrap({"lang": "pt-BR", "theme": "light"})
    # The three things every generated page relies on: normalize the address
    # bar, change a parameter, carry it onto an internal link.
    for helper in ("ensureDefaults", "select", "decorate"):
        assert helper in bootstrap, helper
    assert '"lang":"pt-BR"' in bootstrap


@pytest.mark.parametrize(
    ("tag", "parameter"),
    [("onto-language-tile", '"lang"'), ("onto-theme-tile", '"theme"')],
)
def test_operation_tiles_persist_their_selection_in_the_url(tag, parameter):
    source = ontobdc_view.component_source(tag)
    assert source, f"ontobdc-view served no source for {tag}"
    assert parameter in source
    # Prefers the page's URL-state runtime rather than only repainting the
    # live document...
    assert "ontobdcUrlState" in source
    assert "state.select(" in source
    # ...but never *only* through it. An optional call on a runtime this
    # package does not ship is how the persistence silently vanished once
    # already: the control repaints, the URL never changes, the reload
    # reverts. The Tile has to be able to write the parameter on its own.
    assert not re.search(r"\?\.\s*select\s*\(", source), (
        f"{tag} routes its only persist path through an optional call"
    )
    assert "location.assign(" in source
    assert "searchParams.set(" in source


def test_theme_catalog_is_public_so_the_pipeline_can_declare_its_default():
    catalog = ontobdc_view.theme_catalog()
    assert catalog and catalog[0].get("name")


def test_infobim_tiles_do_not_hand_roll_url_state():
    """InfoBIM's own Tiles must read the language the runtime already applied
    and leave query-string handling to the central helper."""
    for source in InfoBIMComponentSourceAdapter().scripts():
        if "__ONTOBDC_BUILD_" in source:
            continue
        assert "location.search" not in source or "ontobdcUrlState" in source
