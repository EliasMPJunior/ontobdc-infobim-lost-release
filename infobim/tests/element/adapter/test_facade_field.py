from pathlib import Path

from infobim.element.adapter.facade_field import (
    ElementFacadeFieldResolver,
    FacadeFieldSource,
)


def _write_facade(path: Path, content: str) -> None:
    facade_directory = path / ".__ontobdc__" / "linkset"
    facade_directory.mkdir(parents=True)
    (facade_directory / "facade.ttl").write_text(content.strip(), encoding="utf-8")


def test_resolves_fields_from_canonical_has_data_entity_facade_direction(
    tmp_path: Path,
) -> None:
    _write_facade(
        tmp_path,
        """
@prefix facade: <urn:test:facade#> .
@prefix entity: <urn:test:entity#> .

entity:WorkStream facade:hasDataEntityFacade facade:WorkStreamFacade .

facade:WorkStreamFacade
    facade:hasFacadeField facade:NameField , facade:GlobalIdField .

facade:GlobalIdField
    facade:identifier "GlobalId" ;
    facade:name "GlobalId" ;
    facade:fieldDatatype <http://www.w3.org/2001/XMLSchema#string> ;
    facade:isRequired true .

facade:NameField
    facade:identifier "Name" ;
    facade:name "Name" ;
    facade:fieldDatatype <http://www.w3.org/2001/XMLSchema#string> .
""",
    )

    resolution = ElementFacadeFieldResolver().resolve(
        dataset_path=tmp_path,
        entity_uri="urn:test:entity#WorkStream",
        ifc_schema="IFC4",
    )

    assert resolution.source is FacadeFieldSource.FACADE
    assert [field.identifier for field in resolution.fields] == [
        "GlobalId",
        "Name",
    ]
    global_id_field = resolution.fields[0]
    assert global_id_field.datatype == "string"
    assert global_id_field.required is True
    assert resolution.fields[1].required is False


def test_resolves_fields_from_materialized_targets_class_direction(
    tmp_path: Path,
) -> None:
    # The materialized per-dataset facade.ttl snapshot uses the *reverse*
    # direction (facade -> entity via targetsClass) and no
    # hasDataEntityFacade triple at all — see ibim:DefaultIfcWorkScheduleFacade
    # in a real dataset's linkset/facade.ttl.
    _write_facade(
        tmp_path,
        """
@prefix ibim: <https://infobim.org/ontology/ns#> .

ibim:DefaultIfcWorkScheduleFacade
    ibim:targetsClass ibim:IfcWorkSchedule ;
    ibim:hasFacadeField ibim:NameField .

ibim:NameField ibim:identifier "Name" .
""",
    )

    resolution = ElementFacadeFieldResolver().resolve(
        dataset_path=tmp_path,
        entity_uri="https://infobim.org/ontology/ns#IfcWorkSchedule",
        ifc_schema="IFC4",
    )

    assert resolution.source is FacadeFieldSource.FACADE
    assert [field.identifier for field in resolution.fields] == ["Name"]


def test_resolves_fields_from_canonical_ontology_tree_when_dataset_has_no_facade(
    tmp_path: Path,
) -> None:
    # Regression: the dataset itself has no materialized linkset/facade.ttl
    # (a brand new dataset), but the entity's own canonical facade file is
    # tracked in the ontology tree under a name like
    # ``<entity>_facade.ttl`` — not literally ``facade.ttl`` — so it must
    # still be found by directory walk, not skipped in favor of the
    # IfcOpenShell fallback.
    dataset_path = tmp_path / "dataset"
    dataset_path.mkdir()
    ontology_root = tmp_path / "ontology_root"
    entity_directory = ontology_root / "brasidatacenter" / "ontology" / "tool" / "widget" / "entity"
    entity_directory.mkdir(parents=True)
    (entity_directory / "widget_facade.ttl").write_text(
        """
@prefix : <urn:test:widget:facade#> .
@prefix facade: <http://ontobdc.org/ontology/domain/facade.ttl#> .
@prefix entity: <urn:test:widget:type#> .

entity:Widget facade:hasDataEntityFacade :WidgetFacade .

:WidgetFacade facade:hasFacadeField :GlobalIdField .

:GlobalIdField
    facade:identifier "GlobalId" ;
    facade:name "GlobalId" ;
    facade:isRequired true .
""".strip(),
        encoding="utf-8",
    )

    resolution = ElementFacadeFieldResolver().resolve(
        dataset_path=dataset_path,
        entity_uri="urn:test:widget:type#Widget",
        ifc_schema="IFC4",
        ontology_root=ontology_root,
    )

    assert resolution.source is FacadeFieldSource.FACADE
    assert [field.identifier for field in resolution.fields] == ["GlobalId"]
    assert resolution.fields[0].required is True


def test_dataset_facade_wins_over_ontology_tree_when_both_exist(
    tmp_path: Path,
) -> None:
    dataset_path = tmp_path / "dataset"
    _write_facade(
        dataset_path,
        """
@prefix facade: <urn:test:facade#> .
@prefix entity: <urn:test:entity#> .

entity:Widget facade:hasDataEntityFacade facade:DatasetWidgetFacade .
facade:DatasetWidgetFacade facade:hasFacadeField facade:OnlyField .
facade:OnlyField facade:identifier "FromDataset" .
""",
    )
    ontology_root = tmp_path / "ontology_root"
    entity_directory = ontology_root / "tool" / "entity"
    entity_directory.mkdir(parents=True)
    (entity_directory / "widget_facade.ttl").write_text(
        """
@prefix facade: <urn:test:facade#> .
@prefix entity: <urn:test:entity#> .

entity:Widget facade:hasDataEntityFacade facade:CanonicalWidgetFacade .
facade:CanonicalWidgetFacade facade:hasFacadeField facade:OtherField .
facade:OtherField facade:identifier "FromOntologyTree" .
""".strip(),
        encoding="utf-8",
    )

    resolution = ElementFacadeFieldResolver().resolve(
        dataset_path=dataset_path,
        entity_uri="urn:test:entity#Widget",
        ifc_schema="IFC4",
        ontology_root=ontology_root,
    )

    assert [field.identifier for field in resolution.fields] == ["FromDataset"]


def test_matches_facade_by_short_snake_case_entity_identifier(
    tmp_path: Path,
) -> None:
    # Regression: --entity is often the short "entity_identifier" form
    # (e.g. "ifc_work_schedule", the value the --element list's ENTITY
    # IDENTIFIER column shows) rather than a full URI or the PascalCase
    # class name (IfcWorkSchedule) the facade actually declares.
    _write_facade(
        tmp_path,
        """
@prefix ibim: <https://infobim.org/ontology/ns#> .

ibim:DefaultIfcWorkScheduleFacade
    ibim:targetsClass ibim:IfcWorkSchedule ;
    ibim:hasFacadeField ibim:NameField .

ibim:NameField ibim:identifier "Name" .
""",
    )

    resolution = ElementFacadeFieldResolver().resolve(
        dataset_path=tmp_path,
        entity_uri="ifc_work_schedule",
        ifc_schema="IFC4",
    )

    assert resolution.source is FacadeFieldSource.FACADE
    assert [field.identifier for field in resolution.fields] == ["Name"]


def test_ifc_schema_fallback_accepts_short_snake_case_entity_identifier(
    tmp_path: Path,
) -> None:
    resolution = ElementFacadeFieldResolver().resolve(
        dataset_path=tmp_path,
        entity_uri="ifc_task",
        ifc_schema="IFC4",
    )

    assert resolution.source is FacadeFieldSource.IFC_SCHEMA
    assert any(field.identifier == "IsMilestone" for field in resolution.fields)


def test_falls_back_to_ifc_schema_when_no_facade_declared(tmp_path: Path) -> None:
    resolution = ElementFacadeFieldResolver().resolve(
        dataset_path=tmp_path,
        entity_uri="https://standards.buildingsmart.org/IFC/DEV/IFC4/FINAL/OWL#IfcTask",
        ifc_schema="IFC4",
    )

    assert resolution.source is FacadeFieldSource.IFC_SCHEMA
    identifiers = {field.identifier for field in resolution.fields}
    assert "GlobalId" in identifiers
    assert "IsMilestone" in identifiers
    global_id_field = next(
        field for field in resolution.fields if field.identifier == "GlobalId"
    )
    assert global_id_field.required is True


def test_returns_none_source_for_non_ifc_entity_without_facade(
    tmp_path: Path,
) -> None:
    resolution = ElementFacadeFieldResolver().resolve(
        dataset_path=tmp_path,
        entity_uri="https://example.org/ns#NotAnEntity",
        ifc_schema="IFC4",
    )

    assert resolution.source is FacadeFieldSource.NONE
    assert resolution.fields == []
    assert resolution.field_count == 0


def test_missing_facade_file_falls_through_without_error(tmp_path: Path) -> None:
    resolution = ElementFacadeFieldResolver().resolve(
        dataset_path=tmp_path,
        entity_uri="https://standards.buildingsmart.org/IFC/DEV/IFC4/FINAL/OWL#IfcWall",
        ifc_schema="IFC4",
    )

    assert resolution.source is FacadeFieldSource.IFC_SCHEMA
    assert resolution.field_count > 0
