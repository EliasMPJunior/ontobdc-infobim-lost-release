"""A standalone Page is published in the language the Surface was generated in.

`render_entity_view` defaults to `language="en"`, and the publishing
capability was the only production call site — and never passed one. So a
pt-BR Surface published English detail pages: the first click landed on the
wrong language, and a Page opened directly, with no link and no query
parameter to recover from, had no way back to the right one.
"""
import json
import re
import tempfile
from pathlib import Path

import pytest

from ontobdc.view.adapter.surface.document import (
    JSONLD_ID,
    make_initial_html,
    set_state_marker,
    upsert_json_script,
)
from ontobdc.view.plugin.capability.transformation.entity_views_published import (
    EntityViewsPublishedCapability,
)

WORK_STREAM_TYPE = (
    "http://datacenter.app.br/ontology/productivity/entity/work_stream/type.ttl#WorkStream"
)
DCTERMS = "http://purl.org/dc/terms/"

NODE = {
    "@id": "urn:ontobdc:work_stream:WS-1",
    "@type": [WORK_STREAM_TYPE],
    f"{DCTERMS}identifier": [{"@value": "WS-1"}],
    f"{DCTERMS}title": [{"@value": "Execução de fundação"}],
}


class StubContext:
    def __init__(self, **parameters):
        self._parameters = dict(parameters)

    def get_parameter_value(self, name):
        return self._parameters.get(name)

    def set_parameter_value(self, name, value):
        self._parameters[name] = value

    def has_parameter(self, name):
        return name in self._parameters


@pytest.fixture
def publish():
    def _publish(language):
        root = Path(tempfile.mkdtemp())
        surface = root / "index.html"
        document = set_state_marker(make_initial_html(language), "surface_validated")
        document = upsert_json_script(document, JSONLD_ID, [NODE], "application/ld+json")
        surface.write_text(document, encoding="utf-8")

        context = StubContext(surface_path=str(surface), language=language)
        result = EntityViewsPublishedCapability().execute(context)
        page = root / ".__ontobdc__/view/work_stream/WS-1.html"
        return result, (page.read_text(encoding="utf-8") if page.is_file() else "")

    return _publish


@pytest.mark.parametrize("language", ["pt-BR", "pt-PT", "es", "en"])
def test_the_page_is_written_in_the_surface_language(publish, language):
    result, html = publish(language)

    assert result["published_view_count"] == 1
    assert re.search(r'<html lang="([^"]+)"', html).group(1) == language


@pytest.mark.parametrize("language", ["pt-BR", "es"])
def test_the_pages_own_url_default_is_that_language_too(publish, language):
    """Opened directly, with no parameter to inherit, the Page still has to
    normalize itself to the language it was generated in."""
    _, html = publish(language)

    defaults = re.search(r"const DEFAULTS = (\{.*?\});", html, re.DOTALL)
    assert defaults, "the url-state bootstrap is missing from the Page"
    assert json.loads(defaults.group(1))["lang"] == language


def test_a_missing_language_still_yields_a_usable_page(publish):
    root = Path(tempfile.mkdtemp())
    surface = root / "index.html"
    document = set_state_marker(make_initial_html("en"), "surface_validated")
    document = upsert_json_script(document, JSONLD_ID, [NODE], "application/ld+json")
    surface.write_text(document, encoding="utf-8")

    context = StubContext(surface_path=str(surface))
    EntityViewsPublishedCapability().execute(context)

    html = (root / ".__ontobdc__/view/work_stream/WS-1.html").read_text(encoding="utf-8")
    assert re.search(r'<html lang="([^"]+)"', html).group(1) == "en"
