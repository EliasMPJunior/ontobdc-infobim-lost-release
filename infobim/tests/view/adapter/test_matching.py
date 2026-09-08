from rdflib import Graph, Literal, URIRef
from rdflib.namespace import DCTERMS, RDF

from infobim.project.domain.model.contract import IFC_PROJECT_CLASS_URI
from infobim.view.adapter.component import InfoBIMComponentLoader
from infobim.view.adapter.machine import (
    InfoBIMSurfaceGenerationStateTransitionHandler,
)
from infobim.view.adapter.presentation import SCHEMA
from infobim.view.plugin.capability.surface_matched import (
    InfoBIMSurfaceMatchedCapability,
)
from ontobdc.cli.adapter.context import CliContextAdapter
from ontobdc.storage.adapter.bootstrap import StorageNamespaceBootstrap
from ontobdc.view.adapter.surface.machine import (
    SurfaceGenerationStateTransitionHandler,
)


StorageNamespaceBootstrap.initialize()
_OBDC = StorageNamespaceBootstrap.OBDC


WORK_STREAM = URIRef(
    "http://datacenter.app.br/ontology/productivity/entity/"
    "work_stream/type.ttl#WorkStream"
)


def test_infobim_handler_specializes_the_ontobdc_surface_state_machine() -> None:
    assert issubclass(
        InfoBIMSurfaceGenerationStateTransitionHandler,
        SurfaceGenerationStateTransitionHandler,
    )


def test_components_match_project_and_single_ifc_model_projection() -> None:
    graph = Graph()
    project = URIRef("urn:test:project")
    model = URIRef("urn:test:model")
    graph.add((project, RDF.type, URIRef(IFC_PROJECT_CLASS_URI)))
    graph.add((project, DCTERMS.identifier, Literal("project-id")))
    graph.add((model, RDF.type, _OBDC.DataEntity))
    graph.add((model, RDF.value, Literal("{}")))
    graph.add((model, URIRef(f"{SCHEMA}encodingFormat"), Literal("json")))

    loader = InfoBIMComponentLoader()
    assert [
        item.METADATA.tag
        for item in loader.match(graph, project)
        if item.METADATA.id.startswith("org.infobim")
    ] == ["onto-infobim-project-tile"]
    assert [
        item.METADATA.tag
        for item in loader.match(graph, model)
        if item.METADATA.id.startswith("org.infobim")
    ] == ["onto-infobim-ifc-model-tile"]


def test_default_project_requests_hide_distributed_ifc_and_container() -> None:
    graph = Graph()
    project = URIRef("urn:test:project")
    model = URIRef("urn:test:model")
    container = URIRef("urn:test:container")
    workstream = URIRef("urn:test:workstream")

    graph.add((project, RDF.type, URIRef(IFC_PROJECT_CLASS_URI)))
    graph.add((project, DCTERMS.identifier, Literal("project-id")))
    graph.add((model, RDF.type, _OBDC.DataEntity))
    graph.add((model, RDF.value, Literal("{}")))
    graph.add((model, URIRef(f"{SCHEMA}encodingFormat"), Literal("json")))
    graph.add((container, RDF.type, _OBDC.DataContainer))
    graph.add((_OBDC.DataContainer, RDF.type, _OBDC.SurfaceableEntity))
    graph.add((workstream, RDF.type, WORK_STREAM))
    graph.add((WORK_STREAM, RDF.type, _OBDC.SurfaceableEntity))

    context = CliContextAdapter([])
    context.set_parameter_value("infobim_project_resource", str(project))
    context.set_parameter_value("infobim_ifc_model_resource", str(model))
    requests = InfoBIMSurfaceMatchedCapability()._project_requests(
        graph,
        context,
    )
    resources = [request["data"] for request in requests if "data" in request]
    assert resources[0] == str(project)
    assert str(model) not in resources
    assert str(container) not in resources
    assert str(workstream) in resources
