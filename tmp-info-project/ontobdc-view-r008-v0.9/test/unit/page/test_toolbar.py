import json

from rdflib import Graph, Literal, Namespace
from rdflib.namespace import RDF

from ontobdc_view.page.adapter.toolbar import EntityPageToolbarAdapter


VIEW = Namespace("http://datacenter.app.br/ontology/ontobdc/domain/view.ttl#")
PAGE = Namespace("urn:test:page:")


def test_renders_toolbar_actions_in_ontology_placement_order() -> None:
    graph = Graph()
    graph.add((PAGE.Toolbar, RDF.type, VIEW.EntityPageToolbar))
    graph.add((PAGE.Toolbar, VIEW.hasToolbarAlignment, VIEW.RightToolbarAlignment))
    graph.add((PAGE.Toolbar, VIEW.hasToolbarItemPlacement, PAGE.SecondPlacement))
    graph.add((PAGE.Toolbar, VIEW.hasToolbarItemPlacement, PAGE.FirstPlacement))
    graph.add((PAGE.FirstPlacement, VIEW.placementOrder, Literal(1)))
    graph.add((PAGE.FirstPlacement, VIEW.placesComponent, PAGE.Connect))
    graph.add((PAGE.SecondPlacement, VIEW.placementOrder, Literal(2)))
    graph.add((PAGE.SecondPlacement, VIEW.placesComponent, PAGE.Refresh))
    graph.add((PAGE.Connect, VIEW.cssClass, Literal("connect-btn")))
    graph.add((PAGE.Connect, VIEW.i18nContentKey, Literal("connectFolder")))
    graph.add((PAGE.Refresh, VIEW.cssClass, Literal("icon-btn refresh-btn")))
    graph.add((PAGE.Refresh, VIEW.iconName, Literal("refresh")))
    graph.add((PAGE.Refresh, VIEW.initiallyDisabled, Literal(True)))

    configuration = json.loads(graph.serialize(format="json-ld"))
    toolbar = EntityPageToolbarAdapter().render_data(
        {"toolbar_configuration": {"@graph": configuration}}
    )

    assert toolbar["alignment"] == "right"
    assert [action["attributes"]["class"] for action in toolbar["actions"]] == [
        "connect-btn",
        "icon-btn refresh-btn",
    ]
    assert toolbar["actions"][0]["attributes"]["data-i18n"] == "connectFolder"
    assert toolbar["actions"][1]["attributes"]["disabled"] is None
    assert "<svg" in toolbar["actions"][1]["content"]
