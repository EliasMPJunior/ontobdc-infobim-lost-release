"""The small, stable in-process interface the JavaScript/Pyodide bridge
calls.

This module sits at the package root -- above the ``dock/`` clean
architecture layers, the same place ontobdc-a3 keeps ``cli.py`` -- as the
composition root: it wires the outside caller (the JS bridge) to the
Listener dispatch and does no domain work of its own.

The bridge exchanges JSON:

    bootstrap(policy_turtle)                  -> {"ready": true, ...}
    promote('{"event": "TileExpanded", ...}') -> '{"status": "...",
                                                   "targets": [...], ...}'

Python decides *what the event means*; JavaScript emits every event in
``targets``. Not coupled to the DOM.
"""

import json
from typing import Any, Dict, Optional

from ontobdc_web_dock.dock.adapter.listener import (
    DockNotReadyError,
    PresentationEventDock,
)
from ontobdc_web_dock.dock.adapter.policy import PromotionPolicy

_DOCK: Optional[PresentationEventDock] = None


def bootstrap(policy_turtle: str) -> Dict[str, Any]:
    """Parse and index the promotion policy once for the page's lifetime.

    ``policy_turtle`` is the ``presentation_event.ttl`` document itself,
    handed over by the bridge -- the browser cannot reach the
    brasidatacenter package the document is published in, so the document
    travels with the page instead of the policy being restated in code.
    """
    global _DOCK
    policy = PromotionPolicy.from_turtle(policy_turtle)
    _DOCK = PresentationEventDock(policy)
    return {
        "ready": True,
        "listeners": _DOCK.listener_ids(),
        "componentEvents": policy.component_event_names(),
        "sharedEvents": policy.shared_event_names(),
    }


def is_ready() -> bool:
    return _DOCK is not None


def promote(envelope_json: Any) -> str:
    """JSON in, JSON out -- the shape the Pyodide bridge exchanges.

    Returns every Shared Event the policy promotes the occurrence to:
    ``[]``, one target, or many.
    """
    if _DOCK is None:
        raise DockNotReadyError(
            "the presentation event dock has not been bootstrapped with a "
            "policy graph"
        )
    try:
        envelope = (
            json.loads(envelope_json)
            if isinstance(envelope_json, str)
            else dict(envelope_json or {})
        )
    except (TypeError, ValueError) as error:
        raise DockNotReadyError(
            f"unreadable Component Event envelope: {error}"
        ) from error
    return json.dumps(_DOCK.promote(envelope), ensure_ascii=False)


class WebDock:
    """Object-style facade over ``bootstrap`` / ``promote`` for callers
    that hold their own policy (tests, embedders).

    The browser bridge uses the module-level ``bootstrap`` / ``promote``
    functions directly; this class is the ergonomic equivalent for
    in-process Python callers.
    """

    def __init__(self, policy_turtle: Optional[str] = None) -> None:
        self._dock: Optional[PresentationEventDock] = None
        if policy_turtle is not None:
            self.bootstrap(policy_turtle)

    def bootstrap(self, policy_turtle: str) -> Dict[str, Any]:
        policy = PromotionPolicy.from_turtle(policy_turtle)
        self._dock = PresentationEventDock(policy)
        return {
            "ready": True,
            "listeners": self._dock.listener_ids(),
            "componentEvents": policy.component_event_names(),
            "sharedEvents": policy.shared_event_names(),
        }

    def promote(self, event: Any) -> Dict[str, Any]:
        if self._dock is None:
            raise DockNotReadyError("WebDock was not bootstrapped with a policy")
        envelope = (
            event
            if isinstance(event, dict)
            else {"event": str(event)}
        )
        return self._dock.promote(envelope)
