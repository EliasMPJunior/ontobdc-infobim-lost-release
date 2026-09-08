import json

from rdflib import Graph, Literal, Namespace
from rdflib.namespace import DCTERMS, RDF, RDFS, SDO

from ontobdc_view.page.adapter.entity_page import EntityPageOntologyAdapter


VIEW = Namespace("http://datacenter.app.br/ontology/ontobdc/domain/view.ttl#")
PAGE = Namespace("urn:test:page:")
ENTITY = Namespace("urn:test:entity:")


def test_resolves_entity_title_in_the_requested_language() -> None:
    graph = Graph()
    graph.add((PAGE.WorkStream, SDO.identifier, Literal("work_stream")))
    graph.add((PAGE.WorkStream, VIEW.presentsEntityType, ENTITY.WorkStream))
    graph.add((ENTITY.WorkStream, RDFS.label, Literal("Work Stream", lang="en")))
    graph.add(
        (
            ENTITY.WorkStream,
            RDFS.label,
            Literal("Frente de trabalho", lang="pt-BR"),
        )
    )
    adapter = EntityPageOntologyAdapter(graph)

    assert adapter.entity_title("work_stream", "en") == "Work Stream"
    assert adapter.entity_title("work_stream", "pt-BR") == (
        "Frente de trabalho"
    )
    assert adapter.entity_title("work_stream", "pt-PT") == (
        "Frente de trabalho"
    )
    assert adapter.entity_title("work_stream", "es") == "Work Stream"


def test_resolves_entity_page_toolbar_as_jsonld() -> None:
    graph = Graph()
    graph.add((PAGE.WorkStream, VIEW.presentsEntityType, ENTITY.WorkStream))
    graph.add((PAGE.Toolbar, RDF.type, VIEW.EntityPageToolbar))
    graph.add((PAGE.Toolbar, DCTERMS.isPartOf, PAGE.WorkStream))
    graph.add((PAGE.Toolbar, VIEW.hasToolbarAlignment, VIEW.RightToolbarAlignment))
    graph.add((PAGE.Toolbar, VIEW.hasToolbarItemPlacement, PAGE.OpenPlacement))
    graph.add((PAGE.OpenPlacement, RDF.type, VIEW.ToolbarItemPlacement))
    graph.add((PAGE.OpenPlacement, VIEW.placementOrder, Literal(1)))
    graph.add((PAGE.OpenPlacement, VIEW.placesComponent, PAGE.OpenButton))
    graph.add((PAGE.OpenButton, RDF.type, VIEW.EntityPageActionButton))
    graph.add((PAGE.OpenButton, RDFS.label, Literal("Open", lang="en")))

    configuration = EntityPageOntologyAdapter(graph).toolbar_configuration(
        str(ENTITY.WorkStream)
    )
    resolved = Graph().parse(
        data=json.dumps(configuration),
        format="json-ld",
    )

    assert (PAGE.Toolbar, RDF.type, VIEW.EntityPageToolbar) in resolved
    assert (PAGE.Toolbar, DCTERMS.isPartOf, PAGE.WorkStream) in resolved
    assert (
        PAGE.Toolbar,
        VIEW.hasToolbarAlignment,
        VIEW.RightToolbarAlignment,
    ) in resolved
    assert (
        PAGE.OpenPlacement,
        VIEW.placesComponent,
        PAGE.OpenButton,
    ) in resolved
    assert (PAGE.OpenButton, RDFS.label, Literal("Open", lang="en")) in resolved
