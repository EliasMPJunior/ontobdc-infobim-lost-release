from pathlib import Path

from ontobdc.context.adapter.graph import ContextGraphAdapter


class TestContextGraphAdapter:
    def test_loads_turtle_as_nodes_and_edges(self, tmp_path: Path) -> None:
        context_file_path: Path = tmp_path / "context.ttl"
        context_file_path.write_text(
            "@prefix ex: <https://example.org/> .\n"
            "ex:context ex:hasProject ex:project ; ex:label \"Demo\" .\n",
            encoding="utf-8",
        )

        graph_data = ContextGraphAdapter().load(context_file_path)

        assert len(graph_data["edges"]) == 2
        assert {edge["label"] for edge in graph_data["edges"]} == {
            "ex:hasProject",
            "ex:label",
        }
        assert {node["label"] for node in graph_data["nodes"]} >= {
            "ex:context",
            "ex:project",
            '"Demo"',
        }
