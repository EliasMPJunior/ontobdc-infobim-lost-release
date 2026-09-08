"""Dispatch an occurrence to the discovered Listener.

The Listener counterpart of ``CliCommandRunAdapter``: discover the
plugins through the loader and hand the envelope to the one registered
for presentation-event promotion. Holds the indexed policy for the life
of the page so every interaction is a dictionary lookup.
"""

from typing import Any, Dict, List, Optional

from ontobdc_web_dock.dock.adapter.loader import ListenerLoader
from ontobdc_web_dock.dock.adapter.policy import PromotionPolicy
from ontobdc_web_dock.dock.domain.port.listener import ListenerPort


class DockNotReadyError(RuntimeError):
    """``promote()`` was called before the policy was loaded.

    The bridge queues occurrences until bootstrap completes rather than
    guessing an answer, so this is an explicit programming error, never a
    prompt to fall back to a JavaScript decision.
    """


class PresentationEventDock:
    """Holds the indexed policy and the discovered Listener plugins."""

    LISTENER_ID = (
        "org.ontobdc.web_dock.dock.plugin.listener.presentation_event_promotion"
    )

    def __init__(
        self,
        policy: PromotionPolicy,
        loader: Optional[ListenerLoader] = None,
    ) -> None:
        self._policy = policy
        self._loader = loader or ListenerLoader()
        self._listeners: Dict[str, ListenerPort] = {}
        for listener_class in self._loader.get_all():
            self._listeners[listener_class.METADATA.id] = listener_class(policy)

    @property
    def policy(self) -> PromotionPolicy:
        return self._policy

    def listener_ids(self) -> List[str]:
        return sorted(self._listeners)

    def listener(self, listener_id: Optional[str] = None) -> ListenerPort:
        resolved = listener_id or self.LISTENER_ID
        try:
            return self._listeners[resolved]
        except KeyError as error:
            raise DockNotReadyError(
                f"no dDock Listener plugin is registered under {resolved!r}; "
                f"discovered: {self.listener_ids()}"
            ) from error

    def promote(self, envelope: Dict[str, Any]) -> Dict[str, Any]:
        return self.listener().handle(envelope or {})
