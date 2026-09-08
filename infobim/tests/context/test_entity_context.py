from infobim.context.ontology import InfoBIMOntologyAdapter


def test_work_schedule_context_is_ontology_driven() -> None:
    contract = InfoBIMOntologyAdapter().resolve_entity_context(
        "IfcWorkSchedule"
    )

    assert contract.root.entity_name == "IfcWorkSchedule"
    related_names = [entity.entity_name for entity in contract.related]
    assert "IfcTask" in related_names
    assert "IfcTaskTime" in related_names
    assert "IfcRelSequence" in related_names
    assert len(related_names) == 3
    assert [field.name for field in contract.root.fields][:2] == [
        "GlobalId",
        "Name",
    ]


def test_related_classes_do_not_encode_view_or_workbook_layout() -> None:
    source = InfoBIMOntologyAdapter.ontology_text("ns.ttl")

    assert "assignsRelatedClass" in source
    for representation_term in ("worksheet", "Tile", "PresentationRegion"):
        assert representation_term not in source
