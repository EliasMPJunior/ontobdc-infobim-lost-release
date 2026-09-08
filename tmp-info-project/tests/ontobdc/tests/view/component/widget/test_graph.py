from ontobdc.view.component.widget.graph import GraphWidget


class TestGraphWidget:
    def test_renders_labeled_directed_edges_with_netext(self) -> None:
        widget = GraphWidget(
            nodes=[
                {"id": "a", "label": "ex:a", "kind": "uri"},
                {"id": "b", "label": "ex:b", "kind": "uri"},
            ],
            edges=[
                {"source": "a", "target": "b", "label": "ex:relatesTo"},
            ],
        )

        rendered = "\n".join(widget.render(available_columns=80))

        assert "ex:a" in rendered
        assert "ex:b" in rendered
        assert "ex:relatesTo" in rendered

    def test_returns_empty_output_for_empty_graph(self) -> None:
        widget = GraphWidget()

        assert widget.render(available_columns=80) == []
