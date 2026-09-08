from pathlib import Path

from infobim.view.adapter import regeneration as module
from infobim.view.domain.model import InfoBIMProjectPresentation


def test_worker_executes_the_same_surface_generation_handler(
    tmp_path: Path,
    monkeypatch,
) -> None:
    presentation = InfoBIMProjectPresentation(
        project_id="project-123",
        project_path=str(tmp_path),
        project_subject="urn:test:project",
        project={"GlobalId": "project-123"},
        classes=(),
    )
    calls = []

    class FakeContext:
        def __init__(self, *_args, **_kwargs):
            self.values = {}

        def set_parameter_value(self, key, value):
            self.values[key] = value

        def get_parameter_value(self, key):
            return self.values.get(key)

    monkeypatch.setattr(module, "CliContextAdapter", FakeContext)

    monkeypatch.setattr(
        module.InfoBIMProjectPresentationRepository,
        "load",
        lambda _self, **_kwargs: presentation,
    )
    monkeypatch.setattr(
        module.InfoBIMComponentSourceAdapter,
        "scripts",
        lambda _self, **_kwargs: ["component"],
    )

    class FakeHandler:
        def __init__(self, *, context, presentation):
            self.context = context
            self.presentation = presentation

        def execute(self):
            calls.append((self.context, self.presentation))

    monkeypatch.setattr(
        module,
        "InfoBIMSurfaceGenerationStateTransitionHandler",
        FakeHandler,
    )

    worker = module.InfoBIMSurfaceRegenerationWorker(
        project_id="project-123",
        project_path=tmp_path,
        context_root=tmp_path,
        language="pt-BR",
    )
    worker.regenerate()

    assert len(calls) == 1
    context, received = calls[0]
    assert received is presentation
    assert context.get_parameter_value("project_id") == "project-123"
    assert context.get_parameter_value("container_path") == str(tmp_path)
    assert context.get_parameter_value("language") == "pt-BR"


def test_worker_discovers_requests_inside_nested_datasets(tmp_path: Path) -> None:
    request = (
        tmp_path
        / "work_stream"
        / ".__ontobdc__"
        / module.REQUEST_FILE_NAME
    )
    request.parent.mkdir(parents=True)
    request.write_text("{}", encoding="utf-8")

    worker = module.InfoBIMSurfaceRegenerationWorker(
        project_id="project-123",
        project_path=tmp_path,
        context_root=tmp_path,
        language="en",
    )

    assert worker.request_files() == [request]
    assert worker.latest_request_mtime_ns() == request.stat().st_mtime_ns


def test_launcher_reuses_a_live_project_worker(
    tmp_path: Path,
    monkeypatch,
) -> None:
    metadata = tmp_path / ".__ontobdc__"
    metadata.mkdir()
    (metadata / module.PID_FILE_NAME).write_text("2468", encoding="utf-8")
    monkeypatch.setattr(module, "_pid_is_running", lambda pid: pid == 2468)

    pid = module.InfoBIMSurfaceRegenerationWorkerLauncher().ensure_running(
        project_id="project-123",
        project_path=str(tmp_path),
        context_root=str(tmp_path),
        language="en",
    )

    assert pid == 2468
