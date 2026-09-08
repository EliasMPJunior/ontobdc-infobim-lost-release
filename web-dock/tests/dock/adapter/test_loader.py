from __future__ import annotations

from ontobdc_web_dock.dock.adapter.loader import ListenerLoader
from ontobdc_web_dock.dock.plugin.listener.presentation_event import (
    PresentationEventPromotionListener,
)

# Real pkgutil discovery against the real ontobdc_web_dock.dock.plugin.listener
# package layout -- no mocking, per the architecture doc's testing guidelines
# ("ListenerLoader discovers PresentationEventPromotionListener through the
# real pkgutil package layout").


def test_get_all_discovers_the_presentation_event_promotion_listener() -> None:
    discovered = ListenerLoader().get_all()
    assert PresentationEventPromotionListener in discovered


def test_get_returns_the_listener_class_by_its_metadata_id() -> None:
    listener_class = ListenerLoader().get(
        PresentationEventPromotionListener.METADATA.id
    )
    assert listener_class is PresentationEventPromotionListener


def test_get_returns_none_for_an_unregistered_id() -> None:
    assert ListenerLoader().get("org.ontobdc.web_dock.dock.plugin.listener.nope") is None
