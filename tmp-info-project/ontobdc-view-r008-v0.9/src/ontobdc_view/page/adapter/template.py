from __future__ import annotations

import json
import re
from importlib.resources import files
from typing import Any, Dict, List, Mapping, Optional, Sequence

from jinja2 import DictLoader, Environment

from ontobdc_view.page.adapter.entity_page import EntityPageOntologyAdapter
from ontobdc_view.page.adapter.toolbar import EntityPageToolbarAdapter


class EntityPageTemplateAdapter:
    """Render standalone Entity Pages from convention-based Jinja assets.

    A Page-data directory named ``<entity>`` resolves to the asset directory
    ``<entity>_view``. The adapter knows no concrete entity names. Every entity
    template includes the same ``entity_page_header.html.j2``; which actions
    appear in that header is supplied as render data and is not decided here.
    """

    _ASSET_PACKAGE = "ontobdc_view.page.plugin.asset"
    _VIEW_DIRECTORY_PATTERN = re.compile(r"^[a-z][a-z0-9_]*$")
    _HTML_NAME_PATTERN = re.compile(r"^[A-Za-z][A-Za-z0-9_:-]*$")
    _DCTERMS_TITLE = "http://purl.org/dc/terms/title"
    _DCTERMS_IDENTIFIER = "http://purl.org/dc/terms/identifier"

    def __init__(
        self,
        ontology: Optional[EntityPageOntologyAdapter] = None,
        toolbar: Optional[EntityPageToolbarAdapter] = None,
    ) -> None:
        self._ontology = ontology or EntityPageOntologyAdapter()
        self._toolbar = toolbar or EntityPageToolbarAdapter()

    def render(
        self,
        *,
        view_directory: str,
        payload: Any,
        language: str,
        header_actions: Optional[Sequence[Mapping[str, Any]]] = None,
    ) -> str:
        asset_directory = self._asset_directory(view_directory)
        template_name = f"{asset_directory}.html.j2"
        environment = Environment(
            loader=DictLoader(
                {
                    "entity_page_header.html.j2": self._read_shared(
                        "entity_page_header.html.j2"
                    ),
                    template_name: self._read_entity(
                        asset_directory,
                        template_name,
                    ),
                }
            ),
            autoescape=False,
        )
        return environment.get_template(template_name).render(
            **self._render_context(
                asset_directory=asset_directory,
                payload=payload,
                language=language,
                header_actions=header_actions or (),
            )
        )

    def _render_context(
        self,
        *,
        asset_directory: str,
        payload: Any,
        language: str,
        header_actions: Sequence[Mapping[str, Any]],
    ) -> Dict[str, Any]:
        primary_node = self._primary_node(payload)
        entity_id = str(primary_node.get("@id") or "").strip()
        title = (
            self._literal(primary_node, self._DCTERMS_TITLE)
            or self._literal(primary_node, self._DCTERMS_IDENTIFIER)
            or self._local_name(entity_id)
            or asset_directory.removesuffix("_view").replace("_", " ")
        )
        identifier = self._literal(primary_node, self._DCTERMS_IDENTIFIER)
        description = self._literal(
            primary_node, "http://purl.org/dc/terms/description"
        )

        from ontobdc_view.component.adapter.i18n import catalog_for_namespace
        from ontobdc_view.component.adapter.source import theme_catalog

        view_directory = asset_directory.removesuffix("_view")
        entity_titles = self._ontology.localized_entity_titles(view_directory)
        toolbar = self._toolbar.render_data(payload)
        resolved_header_actions = header_actions or toolbar["actions"]
        i18n_catalog = {
            locale: {
                **messages,
                "breadcrumbEntity": entity_titles[locale],
            }
            for locale, messages in catalog_for_namespace(
                asset_directory
            ).items()
        }
        shared_css = self._read_shared("entity_page.css")
        entity_css = self._read_entity(
            asset_directory,
            f"{asset_directory}.css",
        )
        payload_dict = payload if isinstance(payload, dict) else {}
        gantt_payload = payload_dict.get("gantt_payload")
        gantt_script_names = payload_dict.get("gantt_script_names")
        if not isinstance(gantt_script_names, list):
            gantt_script_names = []
        return {
            "language": str(language or "en").strip() or "en",
            "page_title": title,
            "breadcrumb_current_title": self._ontology.entity_title(
                view_directory,
                language,
            ),
            "entity_id": entity_id,
            "entity_name": title,
            "entity_identifier": identifier,
            "entity_description": description,
            "dimensions": payload_dict.get("dimensions") or [],
            "entity_json": self._json_for_script(payload),
            "i18n_json": self._json_for_script(i18n_catalog),
            "theme_catalog_json": self._json_for_script(theme_catalog()),
            "url_state_bootstrap": "",
            "css_content": f"{shared_css}\n{entity_css}",
            "annotation_runtime_css": "",
            "annotation_runtime_js": "",
            "workstream_context_js": "",
            "page_event_display_js": "",
            "js_content": "",
            "has_gantt_payload": isinstance(gantt_payload, dict) and bool(gantt_payload),
            "gantt_payload_json": self._json_for_script(gantt_payload or {}),
            "gantt_script_names": gantt_script_names,
            "toolbar": toolbar,
            "header_actions": self._normalize_header_actions(
                resolved_header_actions
            ),
        }

    @classmethod
    def _asset_directory(cls, view_directory: str) -> str:
        value = str(view_directory or "").strip()
        if not cls._VIEW_DIRECTORY_PATTERN.fullmatch(value):
            raise ValueError(f"Invalid Entity Page directory: {view_directory!r}.")
        return f"{value}_view"

    @classmethod
    def _read_shared(cls, name: str) -> str:
        try:
            return (
                files(cls._ASSET_PACKAGE)
                .joinpath("entity", "common", name)
                .read_text(encoding="utf-8")
            )
        except (FileNotFoundError, OSError) as error:
            raise ValueError(f"Shared Entity Page asset was not found: {name!r}.") from error

    @classmethod
    def _read_entity(cls, asset_directory: str, name: str) -> str:
        try:
            return (
                files(cls._ASSET_PACKAGE)
                .joinpath("entity", asset_directory, name)
                .read_text(encoding="utf-8")
            )
        except (FileNotFoundError, OSError) as error:
            raise ValueError(
                f"Entity Page asset was not found: {asset_directory}/{name}."
            ) from error

    @classmethod
    def _normalize_header_actions(
        cls,
        actions: Sequence[Mapping[str, Any]],
    ) -> List[Dict[str, Any]]:
        normalized: List[Dict[str, Any]] = []
        for action in actions:
            tag = str(action.get("tag") or "").strip()
            if not cls._HTML_NAME_PATTERN.fullmatch(tag):
                raise ValueError(f"Invalid Entity Page header action tag: {tag!r}.")
            raw_attributes = action.get("attributes") or {}
            if not isinstance(raw_attributes, Mapping):
                raise ValueError("Entity Page header action attributes must be a mapping.")
            attributes: Dict[str, Optional[str]] = {}
            for raw_name, raw_value in raw_attributes.items():
                name = str(raw_name or "").strip()
                if not cls._HTML_NAME_PATTERN.fullmatch(name):
                    raise ValueError(
                        f"Invalid Entity Page header action attribute: {name!r}."
                    )
                attributes[name] = None if raw_value is None else str(raw_value)
            normalized.append(
                {
                    "tag": tag,
                    "attributes": attributes,
                    "content": str(action.get("content") or ""),
                }
            )
        return normalized

    @classmethod
    def _primary_node(cls, payload: Any) -> Dict[str, Any]:
        if isinstance(payload, dict):
            graph = payload.get("@graph")
            if isinstance(graph, list):
                for node in graph:
                    if isinstance(node, dict):
                        return node
            return payload
        if isinstance(payload, list):
            for node in payload:
                if isinstance(node, dict):
                    return node
        return {}

    @staticmethod
    def _literal(node: Mapping[str, Any], property_uri: str) -> str:
        values = node.get(property_uri)
        picked = values[0] if isinstance(values, list) and values else values
        if isinstance(picked, dict):
            return str(picked.get("@value") or picked.get("@id") or "").strip()
        if picked is None:
            return ""
        return str(picked).strip()

    @staticmethod
    def _local_name(uri: str) -> str:
        value = str(uri or "").strip()
        if not value:
            return ""
        if "#" in value:
            return value.rsplit("#", 1)[-1].strip()
        trimmed = value.rstrip("/")
        if "/" in trimmed:
            return trimmed.rsplit("/", 1)[-1].strip()
        if ":" in trimmed:
            return trimmed.rsplit(":", 1)[-1].strip()
        return trimmed

    @staticmethod
    def _json_for_script(value: Any) -> str:
        return json.dumps(value, ensure_ascii=False).replace("</", "<\\/")
