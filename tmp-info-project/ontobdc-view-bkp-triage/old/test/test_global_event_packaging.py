"""The listener bundle is self-contained, or it does not run in the browser.

Pyodide has the standard library and whatever wheels were loaded into it. It
does not have `ontobdc`, it does not have `ontobdc_view`, and it has none of
rdflib, pydantic, sismic, Jinja2 or frictionless. So the four modules the
Page ships have to import each other and nothing else.

That property is easy to lose by accident — one convenience import in a
module that already works everywhere else — and impossible to notice in a
development checkout, where every package is on the path. The test below
therefore runs the generated installer in an interpreter with nothing
installed at all, which is the closest thing to Pyodide that exists off the
browser.
"""

import json
import subprocess
import sys
import venv
from pathlib import Path

import pytest

from ontobdc_view.component.adapter.global_event_listener import (
    _FORBIDDEN_IMPORTS,
    _PYODIDE_ROOT,
    global_event_listener_source,
    listener_module_names,
    listener_module_sources,
)

EVENT_NS = "http://datacenter.app.br/ontology/ontobdc/abox/presentation_event.ttl#"


def test_the_bundle_carries_the_journal_the_statechart_and_the_listener():
    assert listener_module_names() == [
        "ontobdc_view/shared/adapter/atomic_file.py",
        "ontobdc_view/surface/domain/machine/global_event_state.py",
        "ontobdc_view/surface/adapter/global_event.py",
        "ontobdc_view/surface/adapter/global_event_listener.py",
    ]


def test_the_bundle_is_the_shipped_code_not_a_copy_of_it():
    """Same files, same import paths. A rewritten copy is a second
    implementation that no test exercises."""
    import ontobdc_view.surface.adapter.global_event_listener as listener

    sources = listener_module_sources()
    assert (
        sources["ontobdc_view/surface/adapter/global_event_listener.py"]
        == Path(listener.__file__).read_text(encoding="utf-8")
    )


def test_no_shipped_module_reaches_for_the_application_package():
    """`ontobdc` depends on `ontobdc-view`. A module here importing it back
    would be a cycle that resolves only where both checkouts sit side by
    side — and not at all in a browser."""
    for name, source in listener_module_sources().items():
        for line in source.splitlines():
            stripped = line.strip()
            if stripped.startswith(("import ontobdc", "from ontobdc")):
                assert stripped.split()[1].startswith("ontobdc_view"), f"{name}: {stripped}"


def test_no_shipped_module_imports_something_the_browser_lacks():
    for name, source in listener_module_sources().items():
        imports = [
            line for line in source.splitlines()
            if line.strip().startswith(("import ", "from "))
        ]
        for forbidden in _FORBIDDEN_IMPORTS:
            assert not any(forbidden in line for line in imports), f"{name}: {forbidden}"


def test_the_install_root_is_a_parameter_rather_than_text_to_edit_out():
    """A caller that has to patch the returned script to move the root can
    miss — a quoting style away — and install the bundle somewhere else
    entirely, leaving the import to whatever else is on the machine."""
    assert _PYODIDE_ROOT in global_event_listener_source()
    assert "/elsewhere" in global_event_listener_source("/elsewhere")
    assert _PYODIDE_ROOT not in global_event_listener_source("/elsewhere")


# --------------------------------------------------------------------------
# The real thing: nothing installed
# --------------------------------------------------------------------------

RUN = r'''
import json, sys

root = sys.argv[1]
# Nothing but the standard library and the tree the installer just wrote.
sys.path = [root] + [entry for entry in sys.path if "ontobdc" not in entry]
import ontobdc_view.surface.adapter.global_event_listener as listener

if not listener.__file__.startswith(root):
    raise SystemExit("the bundle was shadowed by " + listener.__file__)
print(json.dumps({
    "listener": listener.__file__,
    "answer": json.loads(listener.handle_global_event_json(sys.argv[2], sys.argv[3])),
}))
'''


@pytest.fixture(scope="module")
def bare_python(tmp_path_factory):
    """An interpreter with no site-packages of ours — no `ontobdc`, no
    `ontobdc_view`, no third-party wheels."""
    root = tmp_path_factory.mktemp("bare")
    venv.EnvBuilder(with_pip=False).create(root)
    python = root / "bin" / "python"
    if not python.exists():  # pragma: no cover - Windows layout
        python = root / "Scripts" / "python.exe"
    probe = subprocess.run(
        [str(python), "-c", "import ontobdc_view"], capture_output=True, text=True
    )
    assert probe.returncode != 0, "the bare interpreter can see ontobdc_view"
    return python


def test_the_shipped_bundle_installs_and_answers_with_nothing_else_present(
    bare_python, tmp_path
):
    install_root = tmp_path / "pylib"
    installer = tmp_path / "install.py"
    installer.write_text(global_event_listener_source(str(install_root)), encoding="utf-8")
    subprocess.run([str(bare_python), str(installer)], check=True, capture_output=True)

    assert sorted(
        str(path.relative_to(install_root)) for path in install_root.rglob("*.py")
    ) == sorted(listener_module_names())

    dataset = tmp_path / "dataset"
    dataset.mkdir()
    (dataset / "index.html").write_text(
        '<script type="application/ld+json" id="ontobdc-surface-jsonld">[]</script>\n'
        "<!-- ontobdc:global-event-journal -->",
        encoding="utf-8",
    )
    envelope = json.dumps(
        {
            "eventId": "urn:uuid:packaged-1",
            "event": f"{EVENT_NS}EntityPropertySet",
            "entity": "urn:ontobdc:x",
            "operations": [
                {
                    "operation": "set",
                    "predicate": "http://purl.org/dc/terms/title",
                    "value": {"@value": "ok"},
                }
            ],
        }
    )
    runner = tmp_path / "run.py"
    runner.write_text(RUN, encoding="utf-8")
    completed = subprocess.run(
        [str(bare_python), str(runner), str(install_root), str(dataset), envelope],
        capture_output=True,
        text=True,
    )
    assert completed.returncode == 0, completed.stderr
    reported = json.loads(completed.stdout)

    assert reported["listener"].startswith(str(install_root))
    assert reported["answer"]["status"] == "completed"
    assert reported["answer"]["trace"] == [
        "EVENT_RECEIVED",
        "EVENT_STORED",
        "SURFACE_JOURNAL_UPDATED",
        "COMPLETED",
    ]
    assert (dataset / ".__ontobdc__" / "event" / "urn-uuid-packaged-1.json").is_file()
    assert (dataset / "index.html").read_text(encoding="utf-8").count(
        "data-ontobdc-global-event"
    ) == 1
