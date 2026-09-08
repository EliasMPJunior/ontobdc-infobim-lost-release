import json
from pathlib import Path

from rdflib import Graph, URIRef
from rdflib.namespace import DCTERMS, RDF

from infobim.project.domain.model.contract import IFC_PROJECT_CLASS_URI
from infobim.view.adapter.presentation import (
    IFC_MODEL_MEDIA_TYPE,
    SCHEMA,
    InfoBIMPresentationContextAdapter,
)
from infobim.view.domain.model import (
    IfcClassPresentation,
    InfoBIMProjectPresentation,
)


def _presentation(tmp_path: Path) -> InfoBIMProjectPresentation:
    return InfoBIMProjectPresentation(
        project_id="3t3TDZl_D9NOIWB0BSjzJI",
        project_path=str(tmp_path),
        project_subject="urn:test:project",
        project={
            "GlobalId": "3t3TDZl_D9NOIWB0BSjzJI",
            "Name": "Hospital BIM",
            "Description": "OpenBIM test Project",
            "Phase": "Construction",
        },
        classes=(
            IfcClassPresentation(
                class_uri="urn:ifc:IfcWall",
                class_name="IfcWall",
                element_count=1,
                dataset_count=1,
                datasets=(str(tmp_path / "architecture"),),
                elements=(
                    {
                        "GlobalId": "wall-001",
                        "Name": "Wall A",
                        "datasets": [str(tmp_path / "architecture")],
                    },
                ),
            ),
        ),
    )


def test_presentation_context_augments_only_gathered_jsonld(
    tmp_path: Path,
) -> None:
    gathered_path = tmp_path / "data_gathered.jsonld"
    graph = Graph()
    graph.add(
        (
            URIRef("urn:test:project"),
            RDF.type,
            URIRef(IFC_PROJECT_CLASS_URI),
        )
    )
    graph.serialize(destination=str(gathered_path), format="json-ld")

    model_resource = InfoBIMPresentationContextAdapter().augment(
        gathered_path,
        _presentation(tmp_path),
    )

    result = Graph().parse(str(gathered_path), format="json-ld")
    project = URIRef("urn:test:project")
    model = URIRef(model_resource)
    assert str(result.value(project, DCTERMS.identifier)) == (
        "3t3TDZl_D9NOIWB0BSjzJI"
    )
    assert str(result.value(project, DCTERMS.title)) == "Hospital BIM"
    assert str(result.value(model, URIRef(f"{SCHEMA}encodingFormat"))) == (
        IFC_MODEL_MEDIA_TYPE
    )

    payload = json.loads(str(result.value(model, RDF.value)))
    assert payload["class_count"] == 1
    assert payload["element_count"] == 1
    assert payload["classes"][0]["class_name"] == "IfcWall"
    assert payload["classes"][0]["elements"][0]["GlobalId"] == "wall-001"


def test_empty_ifc_catalog_keeps_a_valid_model_projection(
    tmp_path: Path,
) -> None:
    gathered_path = tmp_path / "data_gathered.jsonld"
    Graph().serialize(destination=str(gathered_path), format="json-ld")
    presentation = InfoBIMProjectPresentation(
        project_id="project-empty",
        project_path=str(tmp_path),
        project_subject="urn:test:empty-project",
        project={"GlobalId": "project-empty", "Name": "Empty"},
        classes=(),
    )

    model_resource = InfoBIMPresentationContextAdapter().augment(
        gathered_path,
        presentation,
    )
    result = Graph().parse(str(gathered_path), format="json-ld")
    payload = json.loads(str(result.value(URIRef(model_resource), RDF.value)))
    assert payload["classes"] == []
    assert payload["element_count"] == 0

