from pathlib import Path

import pytest


def _policy_turtle() -> str:
    """The real presentation-event policy document, read through the same
    brasidatacenter resource mechanism the packaging step uses. No mocks."""
    try:
        from brasidatacenter.resources import ontology_path
    except ImportError:  # pragma: no cover - environment guard
        return ""

    abox = ontology_path("tool", "ontobdc", "abox", "presentation_event.ttl")
    if not Path(str(abox)).is_file():
        return ""
    return Path(str(abox)).read_text(encoding="utf-8")


@pytest.fixture(scope="session")
def policy_turtle() -> str:
    turtle = _policy_turtle()
    if not turtle:
        pytest.skip("presentation_event.ttl is not resolvable in this env")
    return turtle
