from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any, Dict, List

from ontobdc_view.surface.adapter.machine import (
    SurfaceGenerationStateTransitionHandler,
)
from ontobdc_view.surface.domain.machine.standard_surface_html.state import (
    SurfaceGenerationProcessState,
)
from ontobdc_view.surface.plugin.capability.transformation.entity_views_published import (
    EntityViewsPublishedCapability,
)


class FakeCliContext:
    raw_args: List[str] = []
    unprocessed_args: List[str] = []
    is_capability_targeted = False
    target_capability_id = None
    root_path = ""
    language = "en"

    def __init__(self, values: Dict[str, Any]) -> None:
        self._values = values

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


class EntityDataGatheredEvaluator:
    process_state_class = SurfaceGenerationProcessState
    state_sequence = list(SurfaceGenerationProcessState)

    def evaluate(self, context: FakeCliContext) -> SurfaceGenerationProcessState:
        return SurfaceGenerationProcessState.ENTITY_DATA_GATHERED


def test_publishes_each_generated_jsonld_with_localized_breadcrumb(
    tmp_path: Path,
) -> None:
    source_path = (
        tmp_path
        / ".__ontobdc__"
        / "view"
        / "ifc_work_schedule"
        / "schedule.jsonld"
    )
    source_path.parent.mkdir(parents=True)
    payload = {
        "fields": {"Name": "Cronograma", "unsafe": "</script><p>bad</p>"},
        "related_entities": [],
    }
    source_path.write_text(json.dumps(payload), encoding="utf-8")
    context = FakeCliContext(
        {"container_path": str(tmp_path), "language": "pt-br"}
    )

    result = EntityViewsPublishedCapability().execute(context)

    target_path = source_path.with_suffix(".html")
    document = target_path.read_text(encoding="utf-8")
    embedded = re.search(
        r'<script type="application/ld\+json" id="ontobdc-page-jsonld">(.*?)</script>',
        document,
        re.DOTALL,
    )
    i18n = re.search(
        r'<script type="application/json" id="ontobdc-i18n">(.*?)</script>',
        document,
        re.DOTALL,
    )
    assert result["published_view_count"] == 1
    assert (
        result["resulting_state"]
        is SurfaceGenerationProcessState.ENTITY_VIEWS_PUBLISHED
    )
    assert result["published_view_paths"] == [str(target_path)]
    assert result["generated_script_paths"] == [
        str(source_path.parent / "xlsx-0.18.5.full.min.js"),
        str(source_path.parent / "i18n_apply.js"),
    ]
    assert '<html lang="pt-br">' in document
    assert '<script defer src="./i18n_apply.js"></script>' in document
    assert 'data-i18n="breadcrumbHome">Home</span>' in document
    assert (
        'data-i18n="breadcrumbEntity">Cronograma</span>' in document
    )
    assert embedded is not None
    assert json.loads(embedded.group(1)) == payload
    assert "</script><p>bad</p>" not in embedded.group(1)
    assert i18n is not None
    catalog = json.loads(i18n.group(1))
    assert catalog["en"]["breadcrumbEntity"] == "IFC Work Schedule"
    assert catalog["pt-BR"]["breadcrumbEntity"] == "Cronograma"
    assert catalog["pt-BR"]["breadcrumbHome"] == "Início"
    assert EntityViewsPublishedCapability().check(context)


def test_check_is_false_when_previous_stage_generated_no_jsonld(
    tmp_path: Path,
) -> None:
    context = FakeCliContext({"container_path": str(tmp_path)})

    assert not EntityViewsPublishedCapability().check(context)


def test_work_stream_html_is_fully_materialized_from_page_data_jsonld(
    tmp_path: Path,
) -> None:
    source_path = (
        tmp_path / ".__ontobdc__" / "view" / "work_stream" / "stream.jsonld"
    )
    source_path.parent.mkdir(parents=True)
    payload = {
        "@id": "urn:work-stream:1",
        "http://purl.org/dc/terms/title": [{"@value": "Mobilization"}],
        "http://purl.org/dc/terms/identifier": [{"@value": "WS-01"}],
        "http://purl.org/dc/terms/description": [{"@value": "Site setup"}],
        "dimensions": [
            {
                "kind": "What",
                "label": "What",
                "value": "Mobilize the site",
                "related_resources": [
                    {
                        "id": "urn:file:1",
                        "title": "plan.pdf",
                        "path": "docs/plan.pdf",
                        "href": "../../../docs/plan.pdf",
                        "kind": "pdf",
                        "category": "documents",
                        "annotations": [{"type": "#NoteAnnotation", "body": "Review"}],
                    }
                ],
                "suggested_resources": [],
                "found_resources": [],
            }
        ],
        "toolbar_configuration": {"@graph": []},
    }
    source_path.write_text(json.dumps(payload), encoding="utf-8")

    EntityViewsPublishedCapability().execute(
        FakeCliContext({"container_path": str(tmp_path), "language": "en"})
    )

    document = source_path.with_suffix(".html").read_text(encoding="utf-8")
    assert '<div class="name">Mobilization</div>' in document
    assert '<div class="identifier">WS-01</div>' in document
    assert "Site setup" in document
    assert "Mobilize the site" in document
    assert "plan.pdf" in document
    assert "Review" in document
    assert 'class="icon-btn create-annotation-btn" disabled' in document
    assert '<button type="button" class="connect-btn"' not in document


def test_surface_statechart_publishes_entity_views_after_data_gathering(
    tmp_path: Path,
) -> None:
    source_path = (
        tmp_path
        / ".__ontobdc__"
        / "view"
        / "work_stream"
        / "entity.jsonld"
    )
    source_path.parent.mkdir(parents=True)
    source_path.write_text('{"@id": "urn:test"}', encoding="utf-8")
    context = FakeCliContext({"container_path": str(tmp_path)})
    handler = SurfaceGenerationStateTransitionHandler(
        context,
        state_evaluator=EntityDataGatheredEvaluator(),
    )

    visited_states = handler.execute_until(
        SurfaceGenerationProcessState.ENTITY_VIEWS_PUBLISHED
    )

    assert visited_states == [
        "__entity_data_gathered__",
        "__entity_views_published__",
    ]
    assert source_path.with_suffix(".html").is_file()
