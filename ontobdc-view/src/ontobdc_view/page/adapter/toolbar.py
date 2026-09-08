from __future__ import annotations

import json
from typing import Any, Dict, List, Mapping, Optional

from rdflib import Graph, Literal, Namespace
from rdflib.namespace import RDF, RDFS


VIEW = Namespace("http://datacenter.app.br/ontology/ontobdc/domain/view.ttl#")

_ICONS = {
    "refresh": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" aria-hidden="true"><path d="M20 6v5h-5"/><path d="M4 18v-5h5"/><path d="M18 9a7 7 0 0 0-12-2M6 15a7 7 0 0 0 12 2"/></svg>',
    "excel": '<svg viewBox="0 0 24 24" aria-hidden="true"><rect x="3" y="3" width="18" height="18" rx="2.5" fill="#1D6F42"/><path d="M8.7 8h2.1l1.2 2.15L13.2 8h2.1l-2.35 4 2.35 4h-2.1l-1.2-2.15L10.8 16H8.7l2.35-4z" fill="#fff"/></svg>',
    "workspace": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" aria-hidden="true"><circle cx="12" cy="8" r="4"/><path d="M4 21c0-4.4 3.6-8 8-8s8 3.6 8 8"/></svg>',
    "subjects": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" aria-hidden="true"><rect x="3" y="3" width="7" height="7"/><rect x="14" y="3" width="7" height="7"/><rect x="14" y="14" width="7" height="7"/><rect x="3" y="14" width="7" height="7"/></svg>',
    "filter": '<svg viewBox="0 0 24 24" fill="currentColor" aria-hidden="true"><path d="M6 2v6l4 4-4 4v6h12v-6l-4-4 4-4V2H6z"/></svg>',
    "add": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" aria-hidden="true"><path d="M12 5v14M5 12h14"/></svg>',
    "print": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" aria-hidden="true"><path d="M6 9V2h12v7M6 18H4a2 2 0 0 1-2-2v-5a2 2 0 0 1 2-2h16a2 2 0 0 1 2 2v5a2 2 0 0 1-2 2h-2"/><path d="M6 14h12v8H6z"/></svg>',
    "fullscreen": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" aria-hidden="true"><path d="M8 3H3v5M16 3h5v5M3 16v5h5M21 16v5h-5"/></svg>',
}


class EntityPageToolbarAdapter:
    """Convert an ontology-backed toolbar subgraph into template data."""

    def render_data(self, payload: Any) -> Dict[str, Any]:
        configuration = (
            payload.get("toolbar_configuration")
            if isinstance(payload, Mapping)
            else None
        )
        if not isinstance(configuration, Mapping):
            return {"id": "", "label": "", "alignment": "right", "actions": []}

        graph = Graph().parse(
            data=json.dumps(configuration, ensure_ascii=False),
            format="json-ld",
        )
        toolbars = sorted(
            set(graph.subjects(RDF.type, VIEW.EntityPageToolbar)),
            key=str,
        )
        if len(toolbars) != 1:
            return {"id": "", "label": "", "alignment": "right", "actions": []}

        toolbar = toolbars[0]
        alignment = self._alignment(graph, toolbar)
        placements = sorted(
            graph.objects(toolbar, VIEW.hasToolbarItemPlacement),
            key=lambda placement: (
                self._integer(graph.value(placement, VIEW.placementOrder)),
                str(placement),
            ),
        )
        actions = []
        for placement in placements:
            components = list(graph.objects(placement, VIEW.placesComponent))
            if len(components) == 1:
                actions.append(self._action(graph, components[0]))

        return {
            "id": str(toolbar),
            "label": self._text(graph.value(toolbar, RDFS.label)),
            "alignment": alignment,
            "actions": actions,
        }

    def _action(self, graph: Graph, component: Any) -> Dict[str, Any]:
        attributes: Dict[str, Optional[str]] = {
            "type": "button",
            "class": self._text(graph.value(component, VIEW.cssClass)),
            "data-toolbar-action": str(component),
        }
        keys = {
            "data-i18n": VIEW.i18nContentKey,
            "data-i18n-title": VIEW.i18nTitleKey,
            "data-i18n-aria-label": VIEW.i18nAriaLabelKey,
        }
        for attribute, predicate in keys.items():
            value = self._text(graph.value(component, predicate))
            if value:
                attributes[attribute] = value
        if self._boolean(graph.value(component, VIEW.initiallyDisabled)):
            attributes["disabled"] = None
        if self._boolean(graph.value(component, VIEW.initiallyHidden)):
            attributes["hidden"] = None
        icon = self._text(graph.value(component, VIEW.iconName))
        return {
            "tag": "button",
            "attributes": attributes,
            "content": _ICONS.get(icon, ""),
        }

    @staticmethod
    def _alignment(graph: Graph, toolbar: Any) -> str:
        value = graph.value(toolbar, VIEW.hasToolbarAlignment)
        name = str(value or "").rsplit("#", 1)[-1].lower()
        for alignment in ("left", "center", "right"):
            if name.startswith(alignment):
                return alignment
        return "right"

    @staticmethod
    def _text(value: Any) -> str:
        return str(value).strip() if value is not None else ""

    @staticmethod
    def _integer(value: Any) -> int:
        try:
            return int(str(value))
        except (TypeError, ValueError):
            return 0

    @staticmethod
    def _boolean(value: Any) -> bool:
        return isinstance(value, Literal) and bool(value.toPython())
