import asyncio
from pathlib import Path
from typing import Any, Dict, List, Optional

import pytest
from rdflib import URIRef
from textual.widgets import Footer, Header, Markdown, MarkdownViewer, Tree

from ontobdc.cli.adapter.logger import NullLogRepository
from ontobdc.cli.domain.port.context import CliContextPort
from ontobdc.cli.domain.response.command import InteractiveCommandResponse
from ontobdc.context.adapter.dataset_instance import (
    DatasetEntityInstanceRepository,
)
from ontobdc.shared.adapter.loader import CommandLoader, ComponentLoader
from ontobdc.shared.domain.model.component import ComponentMetadata
from ontobdc.shared.domain.port.component import (
    ComponentPort,
    TerminalTileRenderable,
)
from ontobdc.shared.facade.request.command import CliCommandRequest
from ontobdc.storage.adapter.explorer import (
    StorageElementContentAdapter,
    StorageElementExplorerAdapter,
    StorageElementExplorerApp,
    StorageElementFacadeContent,
    StorageElementLazyExplorerApp,
    StorageElementMarkdownAdapter,
)
from ontobdc.storage.plugin.command.explore import (
    StorageElementExploreOneCommand,
    StorageExploreCommand,
)
from ontobdc.storage.plugin.parameter.container import ContainerIdStrategy


class ExploreContext(CliContextPort):
    def __init__(self, root_path: Path, **parameters: Any) -> None:
        self._root_path: Path = root_path
        self._parameters: Dict[str, Any] = dict(parameters)

    @property
    def raw_args(self) -> List[str]:
        return []

    @property
    def unprocessed_args(self) -> List[str]:
        return []

    @property
    def is_capability_targeted(self) -> bool:
        return False

    @property
    def target_capability_id(self) -> Optional[str]:
        return None

    @property
    def root_path(self) -> str:
        return str(self._root_path)

    @property
    def language(self) -> Optional[str]:
        return None

    def has_parameter(self, name: str) -> bool:
        return name in self._parameters

    def get_parameter_value(self, name: str) -> Any:
        return self._parameters.get(name)

    def set_parameter_value(self, name: str, value: Any) -> None:
        self._parameters[name] = value

    def delete_parameter(self, name: str) -> None:
        self._parameters.pop(name, None)

    def clear_parameters(self, names: List[str]) -> None:
        for name in names:
            self.delete_parameter(name)

    def reload(self) -> None:
        return None


class StaticElementContentAdapter(StorageElementContentAdapter):
    def load(
        self,
        element: Dict[str, Any],
    ) -> StorageElementFacadeContent:
        return StorageElementFacadeContent(
            entity_name="WorkStream",
            facade_name="WorkStream Facade",
            field_names=("GlobalId", "Name", "What", "Why"),
            records=[
                {
                    "GlobalId": element["id"],
                    "Name": element["title"],
                    "What": "Build the foundation",
                    "Why": "Support the new room",
                }
            ],
        )


class FakeStandaloneTile(ComponentPort, TerminalTileRenderable):
    """Terminal-renderable test double, matched by ``tile_class``."""

    METADATA = ComponentMetadata(
        id="test.fake.standalone.tile",
        tag="fake-standalone-tile",
        version="1.0.0",
        name="Fake Standalone Tile",
        description="Test double for the facade-declared standalone tile.",
        author=["urn:test:author"],
        tile_class="urn:test:tile:FakeStandaloneTile",
    )

    def render(
        self,
        *,
        columns: int,
        rows: int,
        context: Optional[Dict[str, Any]] = None,
    ) -> str:
        element: Dict[str, Any] = (context or {}).get("element") or {}
        return f"FAKE TILE for {element.get('title')}"


class RecordingElementExplorerAdapter(StorageElementExplorerAdapter):
    def __init__(self) -> None:
        self.markdown: str = ""
        self.lazy_elements: List[Dict[str, Any]] = []

    def open(self, markdown: str) -> None:
        self.markdown = markdown

    def open_lazy(
        self,
        elements: List[Dict[str, Any]],
        *,
        markdown_adapter: StorageElementMarkdownAdapter | None = None,
    ) -> None:
        self.lazy_elements = elements


class TestStorageElementMarkdownAdapter:
    def test_content_is_strictly_projected_by_facade(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        facade_directory: Path = tmp_path / ".__ontobdc__" / "linkset"
        facade_directory.mkdir(parents=True)
        (facade_directory / "facade.ttl").write_text(
            """
@prefix facade: <urn:test:facade#> .
@prefix obdc: <http://ontobdc.org/ontology/domain/ontobdc/ns.ttl#> .

facade:ExampleFacade
    obdc:hasFacadeField facade:NameField, facade:WhatField ;
    obdc:name "Example Facade" .

facade:NameField obdc:identifier "Name" ; obdc:fieldOrder 20 .
facade:WhatField obdc:identifier "What" ; obdc:fieldOrder 10 .
""".strip(),
            encoding="utf-8",
        )
        monkeypatch.setattr(
            DatasetEntityInstanceRepository,
            "list_instances",
            lambda _repository: {
                "instances": [
                    {
                        "Name": "Visible name",
                        "What": "Visible dimension",
                        "Secret": "Must not be rendered",
                    }
                ]
            },
        )

        facade_content: Optional[StorageElementFacadeContent] = (
            StorageElementContentAdapter().load(
                {
                    "dataset_path": str(tmp_path),
                    "entity_uri": "urn:test:entity#Entity",
                    "facade_uri": "urn:test:facade#ExampleFacade",
                }
            )
        )

        assert facade_content is not None
        assert facade_content.entity_name == "Entity"
        assert facade_content.facade_name == "Example Facade"
        assert facade_content.field_names == ("What", "Name")
        assert facade_content.records == [
            {
                "What": "Visible dimension",
                "Name": "Visible name",
            }
        ]

    def test_ignores_facade_declared_outside_canonical_facade_file(
        self,
        tmp_path: Path,
    ) -> None:
        facade_directory: Path = tmp_path / ".__ontobdc__" / "linkset"
        facade_directory.mkdir(parents=True)
        (facade_directory / "view.ttl").write_text(
            """
@prefix facade: <urn:test:facade#> .
@prefix obdc: <http://ontobdc.org/ontology/domain/ontobdc/ns.ttl#> .

facade:DefaultIfcWorkScheduleFacade
    obdc:hasFacadeField facade:GlobalIdField, facade:NameField .

facade:GlobalIdField obdc:identifier "GlobalId" ; obdc:fieldOrder 20 .
facade:NameField obdc:identifier "Name" ; obdc:fieldOrder 10 .
""".strip(),
            encoding="utf-8",
        )
        facade_content: Optional[StorageElementFacadeContent] = (
            StorageElementContentAdapter().load(
                {
                    "dataset_path": str(tmp_path),
                    "entity_uri": "urn:test:entity#Entity",
                    "facade_uri": (
                        "urn:test:facade#DefaultIfcWorkScheduleFacade"
                    ),
                }
            )
        )

        assert facade_content is None

    def test_builds_facade_dimensions_and_content(self) -> None:
        adapter: StorageElementMarkdownAdapter = StorageElementMarkdownAdapter(
            content_adapter=StaticElementContentAdapter(),
        )

        markdown: str = adapter.build(
            elements=[
                {
                    "id": "global-id",
                    "title": "Foundation execution",
                    "entity_identifier": "work_stream",
                    "entity_uri": "urn:entity#WorkStream",
                    "iri": "urn:instance:work-stream",
                    "source_dataset_title": "Work streams",
                    "source_dataset_id": "urn:dataset:work-stream",
                    "language": "en",
                }
            ],
        )

        assert "# Entity Element Explorer" in markdown
        assert "## 1. Foundation execution" in markdown
        assert "## 1. WorkStream Facade" not in markdown
        assert "### WorkStream" in markdown
        assert "| GlobalId | global-id |" in markdown
        assert "### Content" not in markdown
        assert "### Dimensions" in markdown
        assert "| What | Build the foundation |" in markdown
        assert markdown.index("### WorkStream") < markdown.index(
            "### Dimensions"
        )
        assert "Entity identifier" not in markdown

    def test_build_one_renders_single_element_without_outer_document(self) -> None:
        adapter: StorageElementMarkdownAdapter = StorageElementMarkdownAdapter(
            content_adapter=StaticElementContentAdapter(),
        )

        markdown: Optional[str] = adapter.build_one(
            {
                "id": "global-id",
                "title": "Foundation execution",
                "entity_identifier": "work_stream",
                "entity_uri": "urn:entity#WorkStream",
                "iri": "urn:instance:work-stream",
                "source_dataset_title": "Work streams",
                "source_dataset_id": "urn:dataset:work-stream",
                "language": "en",
            }
        )

        assert markdown is not None
        assert "# Entity Element Explorer" not in markdown
        assert "# Foundation execution" in markdown
        assert "## 1. Foundation execution" not in markdown
        assert "## WorkStream" in markdown
        assert "| GlobalId | global-id |" in markdown
        assert "## Dimensions" in markdown
        assert "| What | Build the foundation |" in markdown

    def test_build_one_returns_none_without_facade_content(self) -> None:
        adapter: StorageElementMarkdownAdapter = StorageElementMarkdownAdapter()

        assert adapter.build_one({"title": "No facade here"}) is None

    def test_resolve_standalone_tile_classes_orders_by_placement_order(
        self,
        tmp_path: Path,
    ) -> None:
        facade_directory: Path = tmp_path / ".__ontobdc__" / "linkset"
        facade_directory.mkdir(parents=True)
        (facade_directory / "facade.ttl").write_text(
            """
@prefix facade: <urn:test:facade#> .
@prefix obdc: <http://ontobdc.org/ontology/domain/ontobdc/ns.ttl#> .
@prefix rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#> .
@prefix view: <http://datacenter.app.br/ontology/ontobdc/domain/view.ttl#> .

facade:ExampleFacade
    obdc:hasStandaloneTile facade:SecondPlacement, facade:FirstPlacement .

facade:FirstPlacement
    rdf:type view:ComponentPlacement ;
    obdc:placesComponent facade:FirstTile ;
    obdc:placementOrder 10 .

facade:SecondPlacement
    rdf:type view:ComponentPlacement ;
    obdc:placesComponent facade:SecondTile ;
    obdc:placementOrder 20 .

facade:FirstTile rdf:type <urn:test:tile:First> .
facade:SecondTile rdf:type <urn:test:tile:Second> .
""".strip(),
            encoding="utf-8",
        )

        tile_classes: List[str] = (
            StorageElementContentAdapter().resolve_standalone_tile_classes(
                facade_path=facade_directory / "facade.ttl",
                facade_subject=URIRef(
                    "urn:test:facade#ExampleFacade"
                ),
            )
        )

        assert tile_classes == [
            "urn:test:tile:First",
            "urn:test:tile:Second",
        ]

    def test_resolve_standalone_tile_classes_empty_without_declaration(
        self,
        tmp_path: Path,
    ) -> None:
        facade_directory: Path = tmp_path / ".__ontobdc__" / "linkset"
        facade_directory.mkdir(parents=True)
        (facade_directory / "facade.ttl").write_text(
            """
@prefix facade: <urn:test:facade#> .
@prefix obdc: <http://ontobdc.org/ontology/domain/ontobdc/ns.ttl#> .

facade:ExampleFacade obdc:hasFacadeField facade:NameField .
facade:NameField obdc:identifier "Name" ; obdc:fieldOrder 10 .
""".strip(),
            encoding="utf-8",
        )

        tile_classes: List[str] = (
            StorageElementContentAdapter().resolve_standalone_tile_classes(
                facade_path=facade_directory / "facade.ttl",
                facade_subject=URIRef(
                    "urn:test:facade#ExampleFacade"
                ),
            )
        )

        assert tile_classes == []

    def test_build_standalone_renders_declared_tile_with_element_context(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        facade_directory: Path = tmp_path / ".__ontobdc__" / "linkset"
        facade_directory.mkdir(parents=True)
        (facade_directory / "facade.ttl").write_text(
            """
@prefix facade: <urn:test:facade#> .
@prefix obdc: <http://ontobdc.org/ontology/domain/ontobdc/ns.ttl#> .
@prefix rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#> .
@prefix view: <http://datacenter.app.br/ontology/ontobdc/domain/view.ttl#> .

facade:ExampleFacade obdc:hasStandaloneTile facade:OnlyPlacement .

facade:OnlyPlacement
    rdf:type view:ComponentPlacement ;
    obdc:placesComponent facade:OnlyTile ;
    obdc:placementOrder 10 .

facade:OnlyTile rdf:type <urn:test:tile:FakeStandaloneTile> .
""".strip(),
            encoding="utf-8",
        )
        monkeypatch.setattr(
            ComponentLoader,
            "get_all",
            lambda self, resource="component": [FakeStandaloneTile],
        )

        adapter: StorageElementMarkdownAdapter = StorageElementMarkdownAdapter()
        element: Dict[str, Any] = {
            "title": "Cronograma Final",
            "dataset_path": str(tmp_path),
            "facade_uri": "urn:test:facade#ExampleFacade",
        }

        rendered: str = adapter.build_standalone(element)

        assert "# Cronograma Final" in rendered
        assert "FAKE TILE for Cronograma Final" in rendered

    def test_build_standalone_falls_back_to_field_value_document(self) -> None:
        adapter: StorageElementMarkdownAdapter = StorageElementMarkdownAdapter(
            content_adapter=StaticElementContentAdapter(),
        )

        rendered: str = adapter.build_standalone(
            {
                "id": "global-id",
                "title": "Foundation execution",
                "entity_identifier": "work_stream",
                "entity_uri": "urn:entity#WorkStream",
            }
        )

        assert "| GlobalId | global-id |" in rendered

    def test_app_composes_markdown_viewer_with_brand_chrome(self) -> None:
        app: StorageElementExplorerApp = StorageElementExplorerApp("# Element")
        widgets: List[Any] = list(app.compose())

        assert isinstance(widgets[0], Header)
        assert isinstance(widgets[1], MarkdownViewer)
        assert widgets[1]._markdown == "# Element"
        assert widgets[1].show_table_of_contents is True
        assert isinstance(widgets[2], Footer)
        assert "#00b4d8" in app.CSS

    def test_lazy_app_composes_tree_and_markdown_pane_with_brand_chrome(
        self,
    ) -> None:
        app: StorageElementLazyExplorerApp = StorageElementLazyExplorerApp(
            [{"title": "Foundation execution"}],
        )
        widgets: List[Any] = list(app.compose())

        assert isinstance(widgets[0], Header)
        horizontal: Any = widgets[1]
        tree, content_pane = horizontal._pending_children
        assert isinstance(tree, Tree)
        assert tree.id == "element-tree"
        assert tree.show_root is False
        assert content_pane.id == "element-content-pane"
        (markdown_pane,) = content_pane._pending_children
        assert isinstance(markdown_pane, Markdown)
        assert markdown_pane.id == "element-markdown"
        assert isinstance(widgets[2], Footer)
        assert "#00b4d8" in app.CSS

    def test_lazy_app_groups_elements_by_entity_type_on_mount(self) -> None:
        app: StorageElementLazyExplorerApp = StorageElementLazyExplorerApp(
            [
                {
                    "title": "Cronograma Final",
                    "entity_identifier": "ifc_work_schedule",
                },
                {
                    "title": "Foundation execution",
                    "entity_identifier": "work_stream",
                },
                {"global_id": "no-title-id"},
            ],
        )

        async def _mount_and_inspect() -> List[Any]:
            async with app.run_test():
                tree: Tree[int] = app.query_one("#element-tree", Tree)
                return [
                    (str(group.label), [str(leaf.label) for leaf in group.children])
                    for group in tree.root.children
                ]

        groups: List[Any] = asyncio.run(_mount_and_inspect())
        assert groups == [
            ("IfcWorkSchedule", ["Cronograma Final"]),
            ("WorkStream", ["Foundation execution"]),
            ("Element", ["no-title-id"]),
        ]

    def test_lazy_app_loads_and_caches_selected_element_content(self) -> None:
        app: StorageElementLazyExplorerApp = StorageElementLazyExplorerApp(
            [
                {
                    "id": "global-id",
                    "title": "Foundation execution",
                    "entity_identifier": "work_stream",
                    "entity_uri": "urn:entity#WorkStream",
                },
            ],
            markdown_adapter=StorageElementMarkdownAdapter(
                content_adapter=StaticElementContentAdapter(),
            ),
        )

        async def _select_and_read(index: int) -> str:
            async with app.run_test():
                tree: Tree[int] = app.query_one("#element-tree", Tree)
                node = tree.root.children[0].children[index]
                await app.on_tree_node_selected(Tree.NodeSelected(node))
                markdown_pane: Markdown = app.query_one(
                    "#element-markdown", Markdown
                )
                return markdown_pane._markdown

        with_facade: str = asyncio.run(_select_and_read(0))
        assert "Foundation execution" in with_facade
        assert "| GlobalId |" in with_facade
        assert 0 in app._rendered_cache

    def test_lazy_app_shows_message_when_no_facade_content(self) -> None:
        # The default (real) content adapter returns None whenever an
        # element lacks a resolvable facade — this element has no
        # entity_uri/facade_uri at all.
        app: StorageElementLazyExplorerApp = StorageElementLazyExplorerApp(
            [{"title": "No facade element"}],
        )

        async def _select_and_read() -> str:
            async with app.run_test():
                tree: Tree[int] = app.query_one("#element-tree", Tree)
                node = tree.root.children[0].children[0]
                await app.on_tree_node_selected(Tree.NodeSelected(node))
                markdown_pane: Markdown = app.query_one(
                    "#element-markdown", Markdown
                )
                return markdown_pane._markdown

        rendered: str = asyncio.run(_select_and_read())
        assert "No facade content available" in rendered


class TestStorageExploreCommand:
    def test_accepts_and_is_discovered(self) -> None:
        assert StorageExploreCommand.accepts(
            [
                "storage",
                "--container",
                ".",
                "--element",
                "--explore",
            ]
        )
        assert not StorageExploreCommand.accepts(
            ["storage", "--container", ".", "--explore"]
        )
        assert StorageExploreCommand.accepts(
            [
                "storage",
                "--container",
                ".",
                "--element",
                "--explore",
                "--entity",
                "work_stream",
            ]
        )
        commands: List[type] = CommandLoader(
            "storage",
            NullLogRepository(),
        ).get_all()
        assert StorageExploreCommand in commands

    def test_opens_textual_explorer_without_terminal_response(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        context: ExploreContext = ExploreContext(root_path=tmp_path)

        def resolve_container(
            _strategy: ContainerIdStrategy,
            target_context: CliContextPort,
        ) -> CliContextPort:
            target_context.set_parameter_value("container_id", "container-id")
            target_context.set_parameter_value("container_path", str(tmp_path))
            return target_context

        monkeypatch.setattr(ContainerIdStrategy, "execute", resolve_container)
        monkeypatch.setattr(
            StorageExploreCommand,
            "_list_data_entity_instances",
            lambda _command, *, container_path: [
                {
                    "id": "global-id",
                    "title": "Foundation execution",
                    "entity_identifier": "work_stream",
                    "entity_uri": "urn:entity:work-stream",
                    "iri": "urn:instance:work-stream",
                    "source_dataset_title": "Work streams",
                    "source_dataset_id": "urn:dataset:work-stream",
                    "language": "en",
                }
            ],
        )
        explorer: RecordingElementExplorerAdapter = (
            RecordingElementExplorerAdapter()
        )
        request: CliCommandRequest = CliCommandRequest(
            logical_component="storage",
            component_action="explore",
            command_args=[
                "--container",
                ".",
                "--element",
                "--explore",
            ],
            context=context,
        )
        command: StorageExploreCommand = StorageExploreCommand(
            request,
            markdown_adapter=StorageElementMarkdownAdapter(
                content_adapter=StaticElementContentAdapter(),
            ),
            explorer_adapter=explorer,
        )

        assert command.check()
        response: InteractiveCommandResponse = command.run()

        assert response.description == "Explored 1 obdc:DataEntity instance(s)."
        assert len(explorer.lazy_elements) == 1
        assert explorer.lazy_elements[0]["title"] == "Foundation execution"


class TestStorageElementExploreOneCommand:
    def test_accepts_shape_with_element_id_between_flags(self) -> None:
        assert StorageElementExploreOneCommand.accepts(
            [
                "storage",
                "--container",
                ".",
                "--element",
                "global-id",
                "--explore",
            ]
        )
        # Must not swallow the bare (all-elements) --explore form, nor an
        # element id that is itself another flag (e.g. --explore itself,
        # which previously collided with StorageExploreCommand).
        assert not StorageElementExploreOneCommand.accepts(
            ["storage", "--container", ".", "--element", "--explore"]
        )
        assert not StorageElementExploreOneCommand.accepts(
            ["storage", "--container", ".", "--element", "global-id"]
        )
        commands: List[type] = CommandLoader(
            "storage",
            NullLogRepository(),
        ).get_all()
        assert StorageElementExploreOneCommand in commands

    def test_opens_single_document_viewer_for_the_selected_element(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        context: ExploreContext = ExploreContext(root_path=tmp_path)

        def resolve_container(
            _strategy: ContainerIdStrategy,
            target_context: CliContextPort,
        ) -> CliContextPort:
            target_context.set_parameter_value("container_id", "container-id")
            target_context.set_parameter_value("container_path", str(tmp_path))
            return target_context

        monkeypatch.setattr(ContainerIdStrategy, "execute", resolve_container)
        monkeypatch.setattr(
            StorageElementExploreOneCommand,
            "_list_data_entity_instances",
            lambda _command, *, container_path: [
                {
                    "id": "global-id",
                    "title": "Foundation execution",
                    "entity_identifier": "work_stream",
                    "entity_uri": "urn:entity:work-stream",
                },
                {
                    "id": "other-id",
                    "title": "Other element",
                    "entity_identifier": "ifc_project",
                    "entity_uri": "urn:entity:ifc-project",
                },
            ],
        )
        explorer: RecordingElementExplorerAdapter = (
            RecordingElementExplorerAdapter()
        )
        request: CliCommandRequest = CliCommandRequest(
            logical_component="storage",
            component_action="element_explore_one",
            command_args=[
                "--container",
                ".",
                "--element",
                "global-id",
                "--explore",
            ],
            context=context,
        )
        command: StorageElementExploreOneCommand = StorageElementExploreOneCommand(
            request,
            markdown_adapter=StorageElementMarkdownAdapter(
                content_adapter=StaticElementContentAdapter(),
            ),
            explorer_adapter=explorer,
        )

        assert command.check()
        response: InteractiveCommandResponse = command.run()

        assert response.description == "Explored element global-id."
        assert "# Foundation execution" in explorer.markdown
        assert "Other element" not in explorer.markdown
        assert "# Entity Element Explorer" not in explorer.markdown

    def test_raises_for_unknown_element_id(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        context: ExploreContext = ExploreContext(root_path=tmp_path)

        def resolve_container(
            _strategy: ContainerIdStrategy,
            target_context: CliContextPort,
        ) -> CliContextPort:
            target_context.set_parameter_value("container_id", "container-id")
            target_context.set_parameter_value("container_path", str(tmp_path))
            return target_context

        monkeypatch.setattr(ContainerIdStrategy, "execute", resolve_container)
        monkeypatch.setattr(
            StorageElementExploreOneCommand,
            "_list_data_entity_instances",
            lambda _command, *, container_path: [],
        )
        request: CliCommandRequest = CliCommandRequest(
            logical_component="storage",
            component_action="element_explore_one",
            command_args=[
                "--container",
                ".",
                "--element",
                "missing-id",
                "--explore",
            ],
            context=context,
        )
        command: StorageElementExploreOneCommand = StorageElementExploreOneCommand(
            request,
            explorer_adapter=RecordingElementExplorerAdapter(),
        )

        assert command.check()
        with pytest.raises(Exception, match="missing-id"):
            command.run()
