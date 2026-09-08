"""Container connection is shared between Pages, not copied per Page.

Acquiring a container handle — picker, IndexedDB persistence, permission,
descending into the dataset folder — is identical whichever entity a Page
shows. Copying it for a second Page guarantees the two drift the first time
one is fixed, so both render the same template with their own options.
"""
import re
from pathlib import Path

import pytest
import yaml

from ontobdc_view.page.adapter.container import (
    IFC_WORK_SCHEDULE_RUNTIME,
    WORK_STREAM_RUNTIME,
    connection_state_source,
    container_connection_source,
)
from ontobdc_view.page.adapter.work_stream import WorkStreamScriptAdapter

RUNTIMES = [WORK_STREAM_RUNTIME, IFC_WORK_SCHEDULE_RUNTIME]
SOURCES = [container_connection_source, connection_state_source]


@pytest.mark.parametrize("options", RUNTIMES, ids=lambda o: o.resource_name)
@pytest.mark.parametrize("source", SOURCES, ids=lambda s: s.__name__)
def test_every_placeholder_is_resolved(source, options):
    assert not re.findall(r"__[A-Z_]+__", source(options))


@pytest.mark.parametrize("source", SOURCES, ids=lambda s: s.__name__)
def test_the_two_pages_differ_only_by_their_declared_options(source):
    work_stream, schedule = source(WORK_STREAM_RUNTIME), source(IFC_WORK_SCHEDULE_RUNTIME)
    assert work_stream != schedule

    normalized = schedule
    # Read the options off the object rather than listing them here: a new
    # per-Page option added upstream must widen what this test tolerates
    # automatically, not fail as if the Pages had diverged.
    for attribute in vars(WORK_STREAM_RUNTIME):
        normalized = normalized.replace(
            getattr(IFC_WORK_SCHEDULE_RUNTIME, attribute),
            getattr(WORK_STREAM_RUNTIME, attribute),
        )
    assert normalized == work_stream, "the two Pages have diverged beyond their options"


def test_the_work_stream_page_still_emits_what_it_always_did():
    """The extraction must be a move, not a rewrite: the WorkStream Page's
    own scripts are the regression surface here."""
    adapter = WorkStreamScriptAdapter()
    connection = adapter.script_source("container_connection")

    assert "OntoBDCWorkStreamViewRuntime" in connection
    assert '"ontobdc-workstream-view"' in connection
    assert 'const WORK_STREAM_RESOURCE_NAME = "work_stream";' in connection
    assert connection == container_connection_source(WORK_STREAM_RUNTIME)


@pytest.mark.parametrize("options", RUNTIMES, ids=lambda o: o.resource_name)
def test_folder_resolution_requires_the_page_dataset(options):
    source = container_connection_source(options)

    assert "return hasExactNamedResource;" in source
    assert "if (hasExactNamedResource)" not in source


@pytest.mark.parametrize("options", RUNTIMES, ids=lambda o: o.resource_name)
def test_transient_error_label_returns_to_the_connected_state(options):
    source = connection_state_source(options)

    assert 'runtime.state.rawContainerHandle ? t("connectedFolder") : fallbackLabel' in source


@pytest.mark.parametrize("options", RUNTIMES, ids=lambda o: o.resource_name)
def test_every_page_action_is_gated_until_its_folder_is_loaded(options):
    source = connection_state_source(options)

    assert 'querySelectorAll("button:not(.connect-btn)")' in source
    assert "new MutationObserver" in source
    assert "node.disabled = true;" in source
    assert "setProjectActionsDisabled(!runtime.state.rawContainerHandle);" in source
    assert "setProjectActionsDisabled(false);" in source
    assert 'querySelector(".gantt-container")' not in source


def test_workstream_connection_and_refresh_have_single_event_owners():
    adapter = WorkStreamScriptAdapter()
    chrome = adapter.script_source("chrome_controls")
    annotations = adapter.script_source("annotation_bridge")

    assert "connectFolderClickHandler" in chrome
    assert "refreshBtn.addEventListener" in chrome
    assert "connectFolderClickHandler" not in annotations
    assert 'querySelector(".connect-btn").addEventListener' not in annotations
    assert "refreshBtn.addEventListener" not in annotations
    assert "wireConnectionStatusIndicator" not in annotations


@pytest.mark.parametrize(
    "attribute",
    ["runtime_global", "handle_db_name", "resource_name", "no_context_key", "connection_event"],
)
def test_the_pages_share_no_runtime_identity(attribute):
    """Two Pages open in the same browser must not fight over one global,
    one IndexedDB store or one connection event."""
    assert getattr(WORK_STREAM_RUNTIME, attribute) != getattr(IFC_WORK_SCHEDULE_RUNTIME, attribute)


LOCALES = Path(__file__).resolve().parents[1] / "src/ontobdc_view/component/adapter/i18n/locale"
LOCALE_NAMES = ["en", "pt-BR", "pt-PT", "es"]
NAMESPACES = ["work_stream_view", "ifc_work_schedule_view"]


def catalog(locale: str, namespace: str) -> dict:
    data = yaml.safe_load((LOCALES / f"{locale}.yaml").read_text(encoding="utf-8"))
    return data[namespace]


@pytest.mark.parametrize("options", RUNTIMES, ids=lambda o: o.resource_name)
def test_the_page_dataset_folder_settles_a_folder_holding_several_datasets(options):
    """A container with more than one dataset used to be a dead end, even
    though the Page is generated for exactly one of them and carries that
    folder's name in its payload. Reading the name is what makes a shared
    OneDrive container connectable at all."""
    source = container_connection_source(options)

    assert "function pageDatasetFolderName()" in source
    assert "String(payload.datasetFolder || \"\")" in source
    assert "const wantedName = pageDatasetFolderName();" in source
    assert "if (wantedName && name === wantedName) {" in source


@pytest.mark.parametrize("options", RUNTIMES, ids=lambda o: o.resource_name)
def test_the_dataset_walk_is_not_truncated_before_the_page_own_folder(options):
    """The walk stopped after three datasets, so the Page's own folder was
    unreachable the moment it was the fourth one visited — and the message
    could not name what had been found either."""
    source = container_connection_source(options)

    assert "matches.length <= 2" not in source
    assert "matches.length > 2" not in source
    assert "while (queue.length > 0 && visited.size < maxVisits) {" in source


@pytest.mark.parametrize("options", RUNTIMES, ids=lambda o: o.resource_name)
def test_the_ambiguous_folder_message_names_the_datasets_it_found(options):
    source = container_connection_source(options)

    assert 't("multipleDatasetsSelectedFolderCandidates", {' in source
    assert "folders: matches.slice(0, 8).map(function (match) {" in source


@pytest.mark.parametrize("locale", LOCALE_NAMES)
@pytest.mark.parametrize("namespace", NAMESPACES)
def test_the_candidate_message_is_translated_and_interpolates(namespace, locale):
    """Both Pages render the same shared template, so a key only one locale
    or one namespace carries shows up as a raw key for the rest."""
    message = catalog(locale, namespace)["multipleDatasetsSelectedFolderCandidates"]

    assert "{folders}" in message
