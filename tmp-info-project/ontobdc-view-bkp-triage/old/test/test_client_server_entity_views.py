from unittest.mock import MagicMock

from ontobdc_view.page.adapter.client_server_entity_view import (
    ClientServerEntityViewRenderAdapter,
)
from ontobdc_view.page.plugin.ifc_work_schedule_view import IfcWorkScheduleViewPage
from ontobdc_view.page.plugin.work_stream_view import WorkStreamViewPage


DCTERMS_IDENTIFIER = "http://purl.org/dc/terms/identifier"


def _renderer(descriptor):
    page_descriptor = MagicMock()
    page_descriptor.matching_descriptor.return_value = descriptor
    return ClientServerEntityViewRenderAdapter(page_descriptor=page_descriptor)


def _entity(identifier: str) -> dict:
    return {
        "@id": f"urn:test:{identifier}",
        DCTERMS_IDENTIFIER: [{"@value": identifier}],
    }


def test_work_stream_client_server_template_declares_local_api_origin_without_browser_python() -> None:
    result = _renderer(WorkStreamViewPage).render_entity_view(
        list(WorkStreamViewPage.METADATA.required_uris),
        _entity("ws-1"),
        language="en",
    )

    assert result is not None
    html = result["html"]
    assert '<meta name="ontobdc:view-runtime" content="client-server">' in html
    assert '<meta name="ontobdc:api-origin" content="http://127.0.0.1">' in html
    assert "/api/" not in html
    assert "pyodide" not in html.lower()


def test_schedule_client_server_template_declares_local_api_origin_without_browser_python() -> None:
    result = _renderer(IfcWorkScheduleViewPage).render_entity_view(
        list(IfcWorkScheduleViewPage.METADATA.required_uris),
        _entity("schedule-1"),
        language="en",
    )

    assert result is not None
    html = result["html"]
    assert '<meta name="ontobdc:view-runtime" content="client-server">' in html
    assert '<meta name="ontobdc:api-origin" content="http://127.0.0.1">' in html
    assert "/api/" not in html
    assert "pyodide" not in html.lower()
