from __future__ import annotations

import json
from typing import Dict, List, Optional

from ontobdc_view.shared.domain.port.entity_view_render import EntityViewRenderPort

from .asset import PageAssetAdapter
from .descriptor import PageDescriptorAdapter
from .entity_view import _short_title_from_page_name, _url_state_bootstrap


_DCTERMS_IDENTIFIER = "http://purl.org/dc/terms/identifier"


class ClientServerEntityViewRenderAdapter(EntityViewRenderPort):
    """Render entity detail Pages for the local client-server runtime.

    This renderer uses the same Page descriptors, visual assets, theme catalog,
    i18n catalog, output path segments and identifiers as the offline renderer,
    but selects a dedicated ``*_client_server.html.j2`` template. Those
    templates do not embed the browser-side Python runtime or directory-picker
    machinery; live data is requested from the OntoBDC HTTP API on 127.0.0.1.
    """

    def __init__(
        self,
        *,
        page_descriptor: Optional[PageDescriptorAdapter] = None,
        page_asset: Optional[PageAssetAdapter] = None,
    ) -> None:
        self._page_descriptor = page_descriptor or PageDescriptorAdapter()
        self._page_asset = page_asset or PageAssetAdapter()

    def render_entity_view(
        self,
        entity_type_uris: List[str],
        entity_data: dict,
        *,
        graph_nodes: Optional[List[dict]] = None,
        language: str = "en",
    ) -> Optional[Dict[str, str]]:
        _ = graph_nodes
        descriptor = self._page_descriptor.matching_descriptor(entity_type_uris)
        if descriptor is None:
            return None

        from jinja2 import Template
        from ontobdc_view.component.adapter.i18n import catalog_for_namespace
        from ontobdc_view.component.adapter.source import theme_catalog

        metadata = descriptor.METADATA
        base_name = metadata.template.removesuffix(".html.j2")
        template_name = f"{base_name}_client_server.html.j2"
        template_text = self._page_asset.read_page_asset(template_name)
        css_content = "\n".join(
            (
                self._page_asset.read_page_asset("page_chrome.css"),
                self._page_asset.read_page_asset(f"{base_name}.css"),
            )
        )

        entity_id = str(entity_data.get("@id", ""))
        identifier = self._resolve_identifier(entity_data)
        themes = theme_catalog()
        theme_catalog_json = self._escape_for_script_embedding(
            json.dumps(themes, ensure_ascii=False)
        )
        i18n_json = self._escape_for_script_embedding(
            json.dumps(
                catalog_for_namespace(f"{metadata.path_segment}_view"),
                ensure_ascii=False,
            )
        )
        url_state_bootstrap = _url_state_bootstrap(
            {
                "lang": language,
                **(
                    {"theme": str(themes[0].get("name") or "")}
                    if themes
                    and isinstance(themes[0], dict)
                    and themes[0].get("name")
                    else {}
                ),
            }
        )

        html = Template(template_text).render(
            language=language,
            url_state_bootstrap=url_state_bootstrap,
            page_title=metadata.name,
            breadcrumb_current_title=_short_title_from_page_name(metadata.name),
            entity_id=entity_id,
            identifier=identifier,
            css_content=css_content,
            theme_catalog_json=theme_catalog_json,
            i18n_json=i18n_json,
        )
        return {
            "html": html,
            "path_segment": metadata.path_segment,
            "identifier": identifier,
        }

    def _literal(self, entity_data: dict, property_uri: str) -> str:
        values = entity_data.get(property_uri)
        if not isinstance(values, list) or not values:
            return ""
        picked = values[0]
        if isinstance(picked, dict):
            return str(picked.get("@value") or picked.get("@id") or "").strip()
        return str(picked).strip()

    def _resolve_identifier(self, entity_data: dict) -> str:
        return self._literal(entity_data, _DCTERMS_IDENTIFIER) or str(
            entity_data.get("@id", "")
        )

    @staticmethod
    def _escape_for_script_embedding(json_text: str) -> str:
        return json_text.replace("</", "<\\/")
