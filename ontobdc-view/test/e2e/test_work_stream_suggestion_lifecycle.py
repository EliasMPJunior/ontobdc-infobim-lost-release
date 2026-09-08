from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any, Dict, List

from ontobdc.context.adapter.workstream_linkset import WorkStreamResourceLinkset
from ontobdc_view.page.adapter.context import PageDataContextAdapter
from ontobdc_view.page.plugin.capability.transformation.work_stream_related_entities_resolved import (
    WorkStreamRelatedEntitiesResolvedCapability,
)
from ontobdc_view.surface.plugin.capability.transformation.data_gathered import (
    DataGatheredCapability,
)
from ontobdc_view.surface.plugin.capability.transformation.entity_views_published import (
    EntityViewsPublishedCapability,
)


OBDC_NS = "http://ontobdc.org/ontology/domain/ontobdc/ns.ttl#"
DCTERMS_TITLE = "http://purl.org/dc/terms/title"
DCTERMS_IDENTIFIER = "http://purl.org/dc/terms/identifier"


class FakeCliContext:
    raw_args: List[str] = []
    unprocessed_args: List[str] = []
    is_capability_targeted = False
    target_capability_id = None
    root_path = ""
    language = "en"

    def __init__(self, values: Dict[str, Any]) -> None:
        self._values = dict(values)

    def has_parameter(self, key: str) -> bool:
        return key in self._values

    def get_parameter_value(self, key: str) -> Any:
        return self._values.get(key)

    def set_parameter_value(self, key: str, value: Any) -> None:
        self._values[key] = value

    def delete_parameter(self, key: str) -> None:
        self._values.pop(key, None)

    def clear_parameters(self, keys: List[str]) -> None:
        for key in keys:
            self.delete_parameter(key)

    def reload(self) -> None:
        pass


def _write_data_gathered(
    context: FakeCliContext,
    *,
    resource_uri: str,
    resource_title: str,
) -> None:
    state_path = DataGatheredCapability.state_path(context)
    state_path.parent.mkdir(parents=True, exist_ok=True)
    state_path.write_text(
        json.dumps(
            [
                {
                    "@id": resource_uri,
                    "@type": [f"{OBDC_NS}PdfFile"],
                    f"{OBDC_NS}filePath": [{"@value": "docs/method.pdf"}],
                    DCTERMS_TITLE: [{"@value": resource_title}],
                }
            ]
        ),
        encoding="utf-8",
    )


def _publish_work_stream_page(
    context: FakeCliContext,
    *,
    element_uri: str,
) -> tuple[Dict[str, Any], str]:
    source_node = {
        "@id": element_uri,
        DCTERMS_TITLE: [{"@value": "Mobilization"}],
        DCTERMS_IDENTIFIER: [{"@value": "WS-01"}],
    }
    payload: Dict[str, Any] = {
        **source_node,
        "dimensions": [
            {
                "kind": "What",
                "label": "What",
                "value": "Mobilize the site",
            }
        ],
        "toolbar_configuration": {"@graph": []},
    }
    page_context = PageDataContextAdapter(
        context,
        element_uri=element_uri,
        entity_uri=f"{OBDC_NS}WorkStream",
        source_node=source_node,
        payload=payload,
    )
    WorkStreamRelatedEntitiesResolvedCapability().execute(page_context)

    container_path = Path(str(context.get_parameter_value("container_path")))
    page_data_path = (
        container_path
        / ".__ontobdc__"
        / "view"
        / "work_stream"
        / "WS-01.jsonld"
    )
    page_data_path.parent.mkdir(parents=True, exist_ok=True)
    page_data_path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    EntityViewsPublishedCapability().execute(context)
    document = page_data_path.with_suffix(".html").read_text(encoding="utf-8")
    return payload, document


def _suggested_panel(document: str) -> str:
    match = re.search(
        r'<section class="resource-panel" data-resource-panel="suggested"[^>]*>(.*?)</section>',
        document,
        re.DOTALL,
    )
    assert match is not None
    return match.group(1)


def test_rejected_work_stream_suggestion_is_not_published(tmp_path: Path) -> None:
    """Suggested resource disappears from the generated WorkStream Page after rejection.

    This intentionally crosses the real persistence and publication boundary:
    ontobdc-core writes the WorkStreamSuggested.ttl lifecycle, ontobdc-view
    resolves the linkset into Page-data, then publishes the resulting HTML.
    """
    context = FakeCliContext(
        {"container_path": str(tmp_path), "language": "en"}
    )
    element_uri = "urn:work-stream:WS-01"
    dimension_uri = f"{element_uri}/dimension/what"
    resource_uri = "urn:resource:method-statement"
    resource_title = "method.pdf"

    _write_data_gathered(
        context,
        resource_uri=resource_uri,
        resource_title=resource_title,
    )

    suggestions = WorkStreamResourceLinkset(tmp_path, "suggested")
    suggestions.add(dimension_uri, resource_uri)

    payload_before, document_before = _publish_work_stream_page(
        context,
        element_uri=element_uri,
    )
    assert [
        resource["id"]
        for resource in payload_before["dimensions"][0]["suggested_resources"]
    ] == [resource_uri]
    assert resource_title in _suggested_panel(document_before)

    suggestions.reject(dimension_uri, resource_uri)

    payload_after, document_after = _publish_work_stream_page(
        context,
        element_uri=element_uri,
    )
    assert payload_after["dimensions"][0]["suggested_resources"] == []
    assert resource_title not in _suggested_panel(document_after)
