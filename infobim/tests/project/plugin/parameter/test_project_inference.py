from pathlib import Path

from infobim.project.plugin.parameter.project import ProjectIdStrategy


class Context:
    def __init__(self, root: Path, raw_args=None, parameters=None) -> None:
        self.root_path = str(root)
        self.raw_args = raw_args
        self.parameters = dict(parameters or {})

    def set_parameter_value(self, name, value) -> None:
        self.parameters[name] = value

    def get_parameter_value(self, name):
        return self.parameters.get(name)

    def has_parameter(self, name) -> bool:
        return name in self.parameters

    def delete_parameter(self, name) -> None:
        self.parameters.pop(name, None)


def test_project_is_inferred_from_current_directory(tmp_path, monkeypatch) -> None:
    project = tmp_path / "project-alpha"
    nested = project / "payload" / "documents"
    nested.mkdir(parents=True)
    monkeypatch.chdir(nested)
    monkeypatch.setattr(
        ProjectIdStrategy,
        "_project_id_for_container",
        staticmethod(lambda path: "project-global-id"),
    )
    monkeypatch.setattr(
        "infobim.project.plugin.parameter.project.ContainerIdStrategy._registered_containers",
        lambda root: (("container-id", project),),
    )
    context = Context(tmp_path, raw_args=["view"])

    ProjectIdStrategy().execute(context)

    assert context.get_parameter_value("project_id") == "project-global-id"
    assert context.get_parameter_value("container_id") == "container-id"
    assert context.get_parameter_value("project_path") == str(project)


def test_explicit_project_selector_takes_precedence(tmp_path, monkeypatch) -> None:
    inferred = tmp_path / "project-alpha"
    explicit = tmp_path / "project-beta"
    inferred.mkdir()
    explicit.mkdir()
    monkeypatch.chdir(inferred)
    monkeypatch.setattr(
        ProjectIdStrategy,
        "_project_id_for_container",
        staticmethod(
            lambda path: "beta-id" if Path(path) == explicit else "alpha-id"
        ),
    )
    monkeypatch.setattr(
        "infobim.project.plugin.parameter.project.ContainerIdStrategy._registered_containers",
        lambda root: (("alpha", inferred), ("beta", explicit)),
    )
    context = Context(
        tmp_path,
        raw_args=["view", "--project", "beta"],
        parameters={"project": "beta"},
    )

    ProjectIdStrategy().execute(context)

    assert context.get_parameter_value("project_id") == "beta-id"
    assert context.get_parameter_value("container_id") == "beta"


def test_project_is_not_inferred_outside_a_project(tmp_path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(
        "infobim.project.plugin.parameter.project.ContainerIdStrategy._registered_containers",
        lambda root: (),
    )
    context = Context(tmp_path, raw_args=["view"])

    ProjectIdStrategy().execute(context)

    assert context.get_parameter_value("project_id") is None
