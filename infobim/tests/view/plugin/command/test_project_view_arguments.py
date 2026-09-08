from infobim.view.plugin.command.project import ViewProjectCommand


def test_project_view_accepts_representation_and_language() -> None:
    assert ViewProjectCommand.accepts(
        [
            "view",
            "--project",
            "project-123",
            "--representation",
            "html",
            "--language",
            "pt-BR",
        ]
    )


def test_project_view_keeps_html_default_compatibility() -> None:
    assert ViewProjectCommand.accepts(
        ["view", "--project", "project-123"]
    )
