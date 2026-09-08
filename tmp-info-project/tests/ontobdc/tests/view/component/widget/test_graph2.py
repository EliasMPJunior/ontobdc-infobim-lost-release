from ontobdc.view.component.widget.graph import GraphWidget


class TestLayeredGraphWidget:
    def test_renders_layered_graph_through_netext(self) -> None:
        widget = GraphWidget(
            layout="layered",
            nodes=[
                {"id": "root", "label": "Root"},
                {"id": "child-a", "label": "Child A"},
                {"id": "child-b", "label": "Child B"},
                {"id": "leaf", "label": "Leaf"},
            ],
            edges=[
                {"source": "root", "target": "child-a", "label": "hasA"},
                {"source": "root", "target": "child-b", "label": "hasB"},
                {"source": "child-a", "target": "leaf", "label": "hasLeaf"},
            ],
        )

        rendered = "\n".join(widget.render(available_columns=80))

        assert "Root" in rendered
        assert "Child A" in rendered
        assert "Child B" in rendered
        assert "Leaf" in rendered
        assert "hasLeaf" in rendered

    def test_renders_vertical_variant_through_netext(self) -> None:
        widget = GraphWidget(
            layout="layered",
            orientation="vertical",
            nodes=[
                {"id": "root", "label": "Root"},
                {"id": "child-a", "label": "Child A"},
                {"id": "child-b", "label": "Child B"},
            ],
            edges=[
                {"source": "root", "target": "child-a", "label": "hasA"},
                {"source": "root", "target": "child-b", "label": "hasB"},
            ],
        )

        rendered = "\n".join(widget.render(available_columns=60))

        assert "Root" in rendered
        assert "Child A" in rendered
        assert "Child B" in rendered
        assert "hasA" in rendered
        assert "hasB" in rendered
